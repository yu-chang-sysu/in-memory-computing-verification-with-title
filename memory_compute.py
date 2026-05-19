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
        
        # ====== 关键修复：自动计算ADC范围 ======
        # 基于实际权重产生的电流范围来设置ADC范围
        
        # 计算单个权重的最大和最小电流
        # Synapse输出: I_pos - I_neg
        # 当weight=+7: pos_cell(7)=200nA, neg_cell(0)=10nA -> +190nA
        # 当weight=-7: pos_cell(0)=10nA, neg_cell(7)=200nA -> -190nA
        # 当weight=0: pos_cell(0)=10nA, neg_cell(0)=10nA -> 0nA
        
        # 计算单个Synapse的电流范围
        i_max_single_synapse = 190e-9  # 最大差分电流: 190nA
        i_min_single_synapse = -190e-9  # 最小差分电流: -190nA
        
        # 20个权重的总电流范围（未加权）
        i_total_max = 20 * i_max_single_synapse  # 3.8 uA
        i_total_min = 20 * i_min_single_synapse  # -3.8 uA
        
        # 加权后（input_strength ∈ [-1, +1]），电流范围不变
        # 设置ADC范围为实际范围的110%，留出安全余量
        adc_i_min = i_total_min * 1.1  # -4.18 uA
        adc_i_max = i_total_max * 1.1  # +4.18 uA
        
        print(f"[ADC自适应配置]")
        print(f"  - 单个Synapse电流范围: {i_min_single_synapse*1e9:.1f} ~ {i_max_single_synapse*1e9:.1f} nA")
        print(f"  - 20个权重总电流范围: {i_total_min*1e6:.2f} ~ {i_total_max*1e6:.2f} uA")
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
                'total_current': 总电流,
                'adc_code': ADC输出码 (0-15),
                'recovered_current': ADC恢复的电流,
                'synapse_currents': 各权重的电流列表
            }
        """
        assert 0 <= input_code <= 15, "Input must be 0-15 (4-bit)"
        
        # 将 input_code (0-15) 映射到 input_strength (-1, +1)
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
