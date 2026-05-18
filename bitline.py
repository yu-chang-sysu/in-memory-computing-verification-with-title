"""
位线模型和4-bit ADC
"""

import numpy as np


class BitLine:
    """
    位线模型
    - 汇聚多个权重的差分电流
    - 集成4-bit ADC
    """
    
    def __init__(self, adc_i_min=0, adc_i_max=20e-6, adc_bits=4):
        """
        初始化BitLine
        Args:
            adc_i_min: ADC输入范围最小值 (默认 0A)
            adc_i_max: ADC输入范围最大值 (默认 20uA)
            adc_bits: ADC分辨率 (默认 4-bit = 16个等级)
        """
        self.adc_i_min = adc_i_min
        self.adc_i_max = adc_i_max
        self.adc_bits = adc_bits
        self.adc_levels = 2 ** adc_bits  # 16个等级
        
        # ADC量化间隔
        self.adc_lsb = (adc_i_max - adc_i_min) / (self.adc_levels - 1)
    
    def adc_convert(self, i_total):
        """
        4-bit ADC转换
        Args:
            i_total: 输入电流 (A)
        
        Returns:
            adc_code: 0-15的4-bit数字码
            i_recovered: 恢复的电流值
        """
        # 限幅
        i_clipped = np.clip(i_total, self.adc_i_min, self.adc_i_max)
        
        # 量化
        adc_code = int(round((i_clipped - self.adc_i_min) / self.adc_lsb))
        adc_code = np.clip(adc_code, 0, self.adc_levels - 1)
        
        # 恢复电流
        i_recovered = self.adc_i_min + adc_code * self.adc_lsb
        
        return adc_code, i_recovered
    
    def __repr__(self):
        return f"BitLine(ADC: {self.adc_bits}-bit, LSB={self.adc_lsb*1e9:.2f}nA)"