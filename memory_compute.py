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
        self.bitline = BitLine(adc_i_min=0, adc_i_max=20e-6, adc_bits=4)
        
        # 统计信息
        self.i_min_per_input = 10e-9 * 20  # 最小输入电流 (20个cell最小值)
        self.i_max_per_input = 200e-9 * 20  # 最大输入电流 (20个cell最大值)
    
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
        
        # 计算各权重的电流贡献
        # input_code作为控制信号，决定了通过的"信号强度"
        # 简单模型: 总电流 = sum(weight_current * input_code)
        synapse_currents = []
        total_current = 0
        
        for synapse in self.synapses:
            i_synapse = synapse.get_current()
            # 加权
            i_weighted = i_synapse * (input_code / 15.0)  # 归一化到[0,1]
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