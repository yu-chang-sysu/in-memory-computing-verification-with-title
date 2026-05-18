"""
差分对权重 - 正负电流输出
"""

from cell import Cell


class Synapse:
    """
    差分对权重单元
    - 权重为signed，范围 -7 到 +7 (4-bit signed)
    - 由两个Cell组成: 正Cell + 负Cell
    - 净电流 = I_pos - I_neg
    """
    
    def __init__(self, weight_value):
        """
        初始化Synapse
        Args:
            weight_value: -7 到 +7的整数，4bit signed
        """
        assert -7 <= weight_value <= 7, "Weight must be -7 to +7 (4-bit signed)"
        self.weight_value = weight_value
        
        if weight_value >= 0:
            # 正权重: pos_cell = weight, neg_cell = 0
            self.pos_cell = Cell(weight_value)
            self.neg_cell = Cell(0)
        else:
            # 负权重: pos_cell = 0, neg_cell = |weight|
            self.pos_cell = Cell(0)
            self.neg_cell = Cell(-weight_value)
    
    def get_current(self, signed=True):
        """
        获取差分对输出电流
        Args:
            signed: True返回净电流(带符号), False返回绝对值
        
        Returns:
            差分电流 I_pos - I_neg
        """
        i_pos = self.pos_cell.get_current()
        i_neg = self.neg_cell.get_current()
        i_diff = i_pos - i_neg
        
        return i_diff if signed else abs(i_diff)
    
    def __repr__(self):
        return f"Synapse(W={self.weight_value:+d}, I={self.get_current()*1e9:+.2f}nA)"