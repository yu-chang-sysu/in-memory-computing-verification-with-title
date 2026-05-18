# 存算结构Python验证框架

## 项目概述

这是一个专业的存算（In-Memory Computing）结构的Python验证框架，用于对基于模拟电流模式的神经网络加速器进行系统级仿真和验证。

## 系统架构

```
4-bit Input (0-15)
      |
      v
  ┌─────────────────────┐
  │  20个差分对权重单元  │
  │  (范围: -7 到 +7)   │
  └─────────────────────┘
      |
      v (电流汇聚)
  ┌─────────────────────┐
  │    位线(BitLine)    │
  │   20路电流求和      │
  └─────────────────────┘
      |
      v
  ┌─────────────────────┐
  │   4-bit ADC (16级)  │
  │ (0-20uA, LSB=1.43uA)│
  └─────────────────────┘
      |
      v
  4-bit Output (0-15)
```

## 核心模块

### 1. **cell.py** - Cell模型
- **功能**: 3-bit编码存储元件
- **特性**:
  - 编码范围: 0-7（3-bit）
  - 输出电流范围: 10nA - 200nA
  - 线性映射关系

```python
from cell import Cell

cell = Cell(5)  # 3-bit值为5
i = cell.get_current()  # 获取对应的电流值
```

### 2. **synapse.py** - 差分对权重
- **功能**: 带符号权重单元
- **特性**:
  - 权重范围: -7 到 +7（4-bit signed）
  - 由正负两个Cell组成
  - 支持正负权重表示

```python
from synapse import Synapse

synapse = Synapse(3)   # 正权重 +3
synapse = Synapse(-5)  # 负权重 -5
i_diff = synapse.get_current()  # 获取差分电流
```

### 3. **bitline.py** - 位线与ADC
- **功能**: 电流汇聚和数字转换
- **特性**:
  - 电流输入范围: 0 - 20μA
  - ADC分辨率: 4-bit（16个量化等级）
  - LSB大小: ~1.43μA
  - 支持量化和恢复

```python
from bitline import BitLine

bitline = BitLine(adc_i_min=0, adc_i_max=20e-6, adc_bits=4)
adc_code, i_recovered = bitline.adc_convert(i_total)
```

### 4. **memory_compute.py** - 完整系统
- **功能**: 集成所有模块的完整计算单元
- **特性**:
  - 4-bit输入（0-15）
  - 20个权重通道
  - 4-bit ADC输出（0-15）
  - 支持系统级计算

```python
from memory_compute import MemoryComputeUnit

mcu = MemoryComputeUnit()  # 随机初始化权重
result = mcu.compute(input_code=7)

# result包含:
# - input: 输入码
# - total_current: 位线总电流
# - adc_code: ADC输出
# - recovered_current: 恢复的电流
# - synapse_currents: 各权重的电流
```

### 5. **verification.py** - 验证框架
- **功能**: 完整的测试、分析和可视化
- **特性**:
  - 随机输入生成
  - 自动错误分析
  - 统计指标计算
  - 可视化输出

## 工作原理

### 计算流程

1. **输入阶段**: 4-bit输入码（0-15）
2. **权重计算**: 
   ```
   I_synapse_i = weight_i × (input / 15.0)
   ```
3. **电流汇聚**: 
   ```
   I_total = sum(I_synapse_i) for i=1 to 20
   ```
4. **ADC量化**:
   ```
   ADC_code = round((I_total - I_min) / LSB)
   I_recovered = I_min + ADC_code × LSB
   ```

### 误差来源

- **量化误差**: ADC将连续电流映射到16个离散等级
- **饱和误差**: 电流超出0-20μA范围时的限幅

## 快速开始

### 安装依赖

```bash
pip install numpy matplotlib
```

### 运行验证

```bash
python verification.py
```

### 输出示例

```
============================================================
存算结构验证框架
============================================================
配置:
  - 权重数: 20
  - Input: 4-bit (0-15)
  - Cell电流范围: 10nA - 200nA
  - ADC: 4-bit (16等级)
  - 测试样本数: 100

权重配置:
[-2  5 -1  3 -4  2  6 -3  1 -5  4 -2  3  5 -1 -4  2  6 -3  1]
============================================================

开始运行验证测试...

验证测试结果 (共 100 样本)
------------------------------------------------------------

输入信号统计:
  - 输入范围: 0-15
  - 平均输入: 7.50

电流统计:
  - 总电流范围: 0.0000 - 7.6229 uA
  - 平均电流: 3.8115 uA
  - 电流标准差: 2.3456 uA

ADC输出统计:
  - ADC码范围: 0-8
  - ADC码平均值: 2.67

量化误差统计:
  - 最大绝对误差: 0.7171 uA
  - 平均绝对误差: 0.3585 uA
  - 误差RMS: 0.4216 uA
  - 相对误差: 9.41%
```

## 性能指标

| 指标 | 值 |
|------|-----|
| **输入范围** | 0-15 (4-bit) |
| **权重范围** | -7 到 +7 (4-bit signed) |
| **权重数量** | 20 |
| **输出范围** | 0-15 (4-bit) |
| **电流范围** | 0-20 μA |
| **ADC分辨率** | 4-bit (16级) |
| **LSB精度** | ~1.43 μA |
| **典型量化误差** | ~300-400 nA |

## 可视化输出

验证框架生成4个关键图表：

1. **输入vs位线总电流**: 展示输入与电流的线性关系
2. **ADC输出分布**: 显示量化后的码字分布
3. **量化误差分布**: 反映ADC的量化特性
4. **目标vs实际电流**: 比较理想值和实际ADC恢复值

## 文件结构

```
in-memory-computing-verification-with-title/
├── cell.py              # Cell模型
├── synapse.py           # 差分对权重
├── bitline.py           # 位线和ADC
├── memory_compute.py    # 完整系统
├── verification.py      # 验证框架
├── README.md            # 本文档
├── requirements.txt     # Python依赖
└── verification_results.png  # 输出图表
```

## 技术指标

### Cell设计
- 编码精度: 8个离散电流值
- 电流范围: 10nA - 200nA
- 分辨率: 190nA/7 ≈ 27.14 nA/LSB

### Synapse设计  
- 权重精度: 15个离散值 (-7到+7)
- 差分对输出: ±190nA

### ADC设计
- 分辨率: 4-bit
- 输入范围: 0-20 μA
- 量化精度: 1.43 μA/LSB
- 理想INL: ≤ 0.5 LSB
- 理想DNL: ≤ 0.5 LSB

## 使用场景

1. **电路设计验证**: 验证存算架构的功能正确性
2. **系统性能评估**: 评估ADC量化对准确性的影响
3. **功能模拟**: 快速原型设计和算法测试
4. **教学用途**: 理解存算结构的工作原理

## 注意事项

- 当前模型不包含工艺偏差、版图失配等影响
- 噪声模型可按需添加（1/f噪声、热噪声等）
- ADC模型为理想量化器，无非线性特性
- 权重初始化为均匀分布，可自定义

## 未来改进方向

- [ ] 添加1/f噪声模型
- [ ] 添加热噪声模型
- [ ] 支持工艺偏差仿真
- [ ] 添加版图失配模型
- [ ] 实现非理想ADC特性
- [ ] 支持功耗估计
- [ ] 添加温度相关模型