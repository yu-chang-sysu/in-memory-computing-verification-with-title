"""
存算结构的完整系统模型
- 4-bit input输入
- 20个权重 (差分对)
- 位线和ADC输出
"""

import numpy as np
from synapse import Synapse
from bitline import BitLine


class MemoryComputeUnit:
    """
    存算单元
    - 4-bit input (0-15)
    - 20个权重 (-7到+7)
    - 输出: 4-bit ADC码
    """
    
    def __init__(self, weights=None):
        """
        初始化存算单元
        Args:
            weights: 20个权重值列表 (-7到+7)，若为None则随机初始化
        """
        if weights is None:
            weights = np.random.randint(-7, 8, 20)
        else:
            weights = np.array(weights)
            assert len(weights) == 20, "Must have 20 weights"
            assert np.all((weights >= -7) & (weights <= 7)), "Weights must be -7 to +7"
        
        self.weights = weights
        self.synapses = [Synapse(w) for w in weights]
        
        # ====== 关键修复：正确计算ADC范围 ======
        # 单个Synapse的差分电流范围: [-190nA, +190nA]
        # 20个Synapse输出范围: [-3.8uA, +3.8uA]
        # 但实际电流还要乘以输入强度 input_strength ∈ [-1, +1]
        # 因此最终电流范围: [-3.8uA, +3.8uA]
        
        # ADC范围必须覆盖完整的电流范围
        # 设置为 ±4.0uA 以确保充分覆盖
        adc_i_min = -4.0e-6  # -4.0 uA
        adc_i_max = 4.0e-6   # +4.0 uA
        
        self.bitline = BitLine(adc_i_min=adc_i_min, adc_i_max=adc_i_max, adc_bits=4)
    
    def compute(self, input_code):
        """
        执行计算
        Args:
            input_code: 4-bit输入 (0-15)
        
        Returns:
            {
                'input': 输入码,
                'total_current': 总电流,
                'adc_code': ADC输出码 (0-15),
                'recovered_current': ADC恢复的电流,
                'synapse_currents': 各权重的电流列表
            }
        """
        assert 0 <= input_code <= 15, "Input must be 0-15 (4-bit)"
        
        # ====== 关键修复：正确的输入信号映射 ======
        # 将 input_code (0-15) 映射到 input_strength (-1, +1)
        # 
        # 原错误方案: input_strength = input_code / 15.0  (范围[0, 1])
        #   - 只能产生非负电流
        #   - 不能充分利用负权重
        #
        # 正确方案: 
        #   input_code=0  → -1.0 (最小/最负)
        #   input_code=7  → 0.0  (中点)
        #   input_code=15 → +1.0 (最大/最正)
        input_strength = (input_code / 7.5) - 1.0
        
        # 计算各权重的电流贡献
        synapse_currents = []
        total_current = 0
        
        for synapse in self.synapses:
            i_synapse = synapse.get_current()  # ±190nA
            # 加权: 乘以输入强度
            i_weighted = i_synapse * input_strength
            synapse_currents.append(i_weighted)
            total_current += i_weighted
        
        # ADC转换
        adc_code, i_recovered = self.bitline.adc_convert(total_current)
        
        return {
            'input': input_code,
            'total_current': total_current,
            'adc_code': adc_code,
            'recovered_current': i_recovered,
            'synapse_currents': np.array(synapse_currents)
        }
    
    def __repr__(self):
        return f"MemoryComputeUnit(20 weights, 4-bit ADC)\nWeights: {self.weights}"
