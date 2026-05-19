"""
存算结构的完整系统模型
- 4-bit input输入
- 100个权重 (差分对)
- 位线和ADC输出
"""

import numpy as np
from synapse import Synapse
from bitline import BitLine


class MemoryComputeUnit:
    """
    存算单元
    - 4-bit input (0-15)
    - 100个权重 (-7到+7)
    - 输出: 4-bit ADC码
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
        self.synapses = [Synapse(w) for w in weights]
        
        # ====== 电流范围计算 ======
        # 单个Synapse的差分电流范围: [-190nA, +190nA]
        # 100个Synapse的总电流范围: [-19uA, +19uA]
        
        i_max_single_synapse = 190e-9  # 最大差分电流: 190nA
        i_min_single_synapse = -190e-9  # 最小差分电流: -190nA
        
        # 100个权重的总电流范围（未加权）
        self.i_total_max = 100 * i_max_single_synapse  # 19 uA
        self.i_total_min = 100 * i_min_single_synapse  # -19 uA
        
        # 加权后（input_strength ∈ [-1, +1]），电流范围不变
        # 设置ADC范围为实际范围的110%，留出安全余量
        adc_i_min = self.i_total_min * 1.1  # -20.9 uA
        adc_i_max = self.i_total_max * 1.1  # +20.9 uA
        
        # 转换为nA级别
        adc_i_min = int(adc_i_min * 1e9) * 1e-9
        adc_i_max = int(adc_i_max * 1e9) * 1e-9
        
        print(f"[ADC自适应配置]")
        print(f"  - 单个Synapse电流范围: {i_min_single_synapse*1e9:.1f} ~ {i_max_single_synapse*1e9:.1f} nA")
        print(f"  - 100个权重总电流范围: {self.i_total_min*1e6:.2f} ~ {self.i_total_max*1e6:.2f} uA")
        print(f"  - ADC配置范围: {adc_i_min*1e6:.2f} ~ {adc_i_max*1e6:.2f} uA")
        
        self.bitline = BitLine(adc_i_min=adc_i_min, adc_i_max=adc_i_max, adc_bits=4)
    
    def compute(self, input_code):
        """
        执行计算
        Args:
            input_code: 4-bit输入 (0-15)
        
        Returns:
            {
                'input': 输入码,
                'input_normalized': 归一化输入 [-1, +1],
                'total_current': 总电流,
                'total_current_normalized': 归一化电流 [-1, +1],
                'adc_code': ADC输出码 (0-15),
                'adc_code_normalized': 归一化ADC码 [-1, +1],
                'recovered_current': ADC恢复的电流,
                'synapse_currents': 各权重的电流列表
            }
        """
        assert 0 <= input_code <= 15, "Input must be 0-15 (4-bit)"
        
        # ====== 输入归一化 ======
        # 将 input_code (0-15) 映射到 input_normalized (-1, +1)
        # input_code=0  → -1.0 (最小)
        # input_code=7  → 0.0  (中点)
        # input_code=15 → +1.0 (最大)
        input_normalized = (input_code / 7.5) - 1.0
        
        # 计算各权重的电流贡献
        synapse_currents = []
        total_current = 0
        
        for synapse in self.synapses:
            i_synapse = synapse.get_current()  # ±190nA
            # 加权: 乘以归一化输入
            i_weighted = i_synapse * input_normalized
            synapse_currents.append(i_weighted)
            total_current += i_weighted
        
        # ====== 电流归一化 ======
        # 将总电流归一化到 [-1, +1]
        total_current_normalized = total_current / self.i_total_max
        
        # ADC转换
        adc_code, i_recovered = self.bitline.adc_convert(total_current)
        
        # ====== ADC码归一化 ======
        # 将ADC码 (0-15) 归一化到 [-1, +1]
        # ADC_code=0  → -1.0
        # ADC_code=8  → 0.0
        # ADC_code=15 → +1.0
        adc_code_normalized = (adc_code / 7.5) - 1.0
        
        return {
            'input': input_code,
            'input_normalized': input_normalized,
            'total_current': total_current,
            'total_current_normalized': total_current_normalized,
            'adc_code': adc_code,
            'adc_code_normalized': adc_code_normalized,
            'recovered_current': i_recovered,
            'synapse_currents': np.array(synapse_currents)
        }
    
    def __repr__(self):
        return f"MemoryComputeUnit(100 weights, 4-bit ADC)\nWeights: {self.weights}"
