"""
存算结构的完整系统模型
- 4-bit input输入
- 100个权重 (10串，每串10个)
- 动态范围ADC (6-bit)
"""

import numpy as np
from synapse import Synapse
from bitline import BitLine


class MemoryComputeUnit:
    """
    存算单元
    - 4-bit input (0-15)
    - 100个权重 (-7到+7)，组织为10串，每串10个
    - 动态范围6-bit ADC
    """
    
    def __init__(self, weights=None):
        """
        初始化存算单元
        Args:
            weights: 100个权重值列表 (-7到+7)，若为None则随机初始化
        """
        if weights is None:
            weights = np.random.randint(-7, 8, 100)
        else:
            weights = np.array(weights)
            assert len(weights) == 100, "Must have 100 weights"
            assert np.all((weights >= -7) & (weights <= 7)), "Weights must be -7 to +7"
        
        self.weights = weights
        
        # ====== 组织权重为10串，每串10个 ======
        self.num_strings = 10
        self.weights_per_string = 10
        
        # 为每一串创建Synapse对象
        self.strings = []
        for i in range(self.num_strings):
            start_idx = i * self.weights_per_string
            end_idx = start_idx + self.weights_per_string
            string_weights = weights[start_idx:end_idx]
            string_synapses = [Synapse(w) for w in string_weights]
            self.strings.append(string_synapses)
        
        # ====== 电流范围计算 ======
        # 单个Synapse的差分电流范围: [-190nA, +190nA]
        # 单串10个Synapse的范围: [-1.9uA, +1.9uA]
        # 10串的范围: [-19uA, +19uA]
        
        i_max_single_synapse = 190e-9  # 最大差分电流: 190nA
        i_min_single_synapse = -190e-9  # 最小差分电流: -190nA
        
        # 单串的范围
        self.i_max_per_string = self.weights_per_string * i_max_single_synapse  # 1.9 uA
        self.i_min_per_string = self.weights_per_string * i_min_single_synapse  # -1.9 uA
        
        # 所有串的总范围
        self.i_total_max = self.num_strings * self.i_max_per_string  # 19 uA
        self.i_total_min = self.num_strings * self.i_min_per_string  # -19 uA
        
        # 6-bit ADC (64个等级)
        self.adc_bits = 6
        self.adc_levels = 2 ** self.adc_bits  # 64
        
        # 初始化ADC (会根据运行时数据进行自适应)
        self.bitline = BitLine(adc_i_min=self.i_total_min, adc_i_max=self.i_total_max, adc_bits=self.adc_bits)
        
        # 用于跟踪全局最大/最小值
        self.global_i_min = self.i_total_max
        self.global_i_max = self.i_total_min
        
        print(f"[系统配置]")
        print(f"  - 权重组织: {self.num_strings}串 × {self.weights_per_string}个")
        print(f"  - 单串电流范围: {self.i_min_per_string*1e6:.2f} ~ {self.i_max_per_string*1e6:.2f} uA")
        print(f"  - 总电流范围: {self.i_total_min*1e6:.2f} ~ {self.i_total_max*1e6:.2f} uA")
        print(f"  - ADC: {self.adc_bits}-bit ({self.adc_levels}个等级)")
    
    def compute(self, input_code):
        """
        执行计算
        Args:
            input_code: 4-bit输入 (0-15)
        
        Returns:
            {
                'input': 输入码,
                'input_normalized': 归一化输入 [-1, +1],
                'string_currents': 10串的电流输出,
                'total_current': 总电流,
                'total_current_normalized': 归一化电流 [-1, +1],
                'adc_i_min': 当前ADC最小值,
                'adc_i_max': 当前ADC最大值,
                'adc_lsb': 当前LSB大小,
                'adc_code': ADC输出码 (0-63),
                'adc_code_normalized': 归一化ADC码 [-1, +1],
                'recovered_current': ADC恢复的电流,
                'synapse_currents': 各权重的电流列表
            }
        """
        assert 0 <= input_code <= 15, "Input must be 0-15 (4-bit)"
        
        # ====== 输入归一化 ======
        input_normalized = (input_code / 7.5) - 1.0
        
        # ====== 计算每一串的输出电流 ======
        string_currents = []
        synapse_currents = []
        total_current = 0
        
        for string_idx, synapses in enumerate(self.strings):
            string_current = 0
            for synapse in synapses:
                i_synapse = synapse.get_current()  # ±190nA
                # 加权: 乘以归一化输入
                i_weighted = i_synapse * input_normalized
                synapse_currents.append(i_weighted)
                string_current += i_weighted
            
            string_currents.append(string_current)
            total_current += string_current
        
        # ====== 动态ADC范围计算 ======
        # 找到当前总电流中的最小值和最大值
        # 这里简化处理：基于所有测试的历史最大/最小值
        # 实际应该在多次运行后建立动态范围
        
        # 更新全局最大/最小值
        if total_current > self.global_i_max:
            self.global_i_max = total_current
        if total_current < self.global_i_min:
            self.global_i_min = total_current
        
        # 使用全局范围作为ADC范围
        adc_i_min = self.global_i_min
        adc_i_max = self.global_i_max
        
        # 避免范围为零
        if adc_i_max == adc_i_min:
            adc_i_max = adc_i_min + 1e-9
        
        # 重新配置ADC范围
        adc_lsb = (adc_i_max - adc_i_min) / (self.adc_levels - 1)
        
        # ADC量化
        i_clipped = np.clip(total_current, adc_i_min, adc_i_max)
        adc_code = int(round((i_clipped - adc_i_min) / adc_lsb))
        adc_code = np.clip(adc_code, 0, self.adc_levels - 1)
        
        # 恢复电流
        i_recovered = adc_i_min + adc_code * adc_lsb
        
        # ====== 电流归一化 ======
        total_current_normalized = total_current / self.i_total_max
        
        # ====== ADC码归一化 ======
        # 将ADC码 (0-63) 归一化到 [-1, +1]
        # ADC_code=0  → -1.0
        # ADC_code=31.5 → 0.0
        # ADC_code=63 → +1.0
        adc_code_normalized = (adc_code / 31.5) - 1.0
        
        return {
            'input': input_code,
            'input_normalized': input_normalized,
            'string_currents': np.array(string_currents),
            'total_current': total_current,
            'total_current_normalized': total_current_normalized,
            'adc_i_min': adc_i_min,
            'adc_i_max': adc_i_max,
            'adc_lsb': adc_lsb,
            'adc_code': adc_code,
            'adc_code_normalized': adc_code_normalized,
            'recovered_current': i_recovered,
            'synapse_currents': np.array(synapse_currents)
        }
    
    def __repr__(self):
        return f"MemoryComputeUnit(10×10 weights, 6-bit dynamic ADC)\nWeights: {self.weights}"
