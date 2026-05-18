"""
存算结构中的Cell模型
- 每个cell为3bit编码
- 输出电流范围: 10nA 到 200nA
"""

import numpy as np


class Cell:
    """
    Cell模型
    - 3bit编码: 0-7对应不同的电流值
    - 输出为线性分布的电流
    """
    
    def __init__(self, cell_value, i_min=10e-9, i_max=200e-9):
        """
        初始化Cell
        
        Args:
            cell_value: 0-7的整数，表示3bit编码
            i_min: 最小电流 (默认 10nA)
            i_max: 最大电流 (默认 200nA)
        """
        assert 0 <= cell_value <= 7, "Cell value must be 0-7 (3-bit)"
        self.cell_value = cell_value
        self.i_min = i_min
        self.i_max = i_max
        
        # 线性映射: cell_value -> 电流
        self.i_cell = i_min + (cell_value / 7.0) * (i_max - i_min)
    
    def get_current(self):
        """获取Cell输出电流"""
        return self.i_cell
    
    def __repr__(self):
        return f"Cell({self.cell_value}, I={self.i_cell*1e9:.2f}nA)"