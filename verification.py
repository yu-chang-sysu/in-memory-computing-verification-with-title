"""
验证框架
- 随机生成输入
- 对比目标输出和实际输出
- 计算误差指标
"""

import numpy as np
import matplotlib

# ==========================================
# 0. 设置绘图后端以兼容 PyCharm
# ==========================================
try:
    matplotlib.use('TkAgg')
except:
    try:
        matplotlib.use('Qt5Agg')
    except:
        pass

# ==========================================
# 1. 设置中文字体支持
# ==========================================
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

import matplotlib.pyplot as plt
from memory_compute import MemoryComputeUnit


class Verification:
    """验证工具"""
    
    def __init__(self, num_tests=100, seed=None):
        """
        初始化验证框架
        Args:
            num_tests: 测试样本数
            seed: 随机种子
        """
        if seed is not None:
            np.random.seed(seed)
        
        self.num_tests = num_tests
        self.mcu = MemoryComputeUnit()  # 随机权重
        
        print("=" * 60)
        print("存算结构验证框架")
        print("=" * 60)
        print(f"配置:")
        print(f"  - 权重组织: 10串 × 10个")
        print(f"  - Input: 4-bit (0-15)")
        print(f"  - Cell电流范围: 10nA - 200nA")
        print(f"  - ADC: 6-bit动态范围 (64等级)")
        print(f"  - 测试样本数: {num_tests}")
        print(f"\n权重配置:\n{self.mcu.weights}")
        print("=" * 60)
    
    def run_tests(self):
        """运行验证测试"""
        results = []
        
        for i in range(self.num_tests):
            # 随机输入
            input_code = np.random.randint(0, 16)
            
            # 执行计算
            result = self.mcu.compute(input_code)
            result['test_id'] = i
            results.append(result)
        
        return np.array(results, dtype=object)
    
    def analyze_results(self, results):
        """分析结果"""
        print(f"\n验证测试结果 (共 {len(results)} 样本)")
        print("-" * 60)
        
        # 提取数据
        inputs = np.array([r['input'] for r in results])
        total_currents = np.array([r['total_current'] for r in results])
        adc_codes = np.array([r['adc_code'] for r in results])
        recovered_currents = np.array([r['recovered_current'] for r in results])
        
        # 计算误差
        quantization_errors = recovered_currents - total_currents
        abs_errors = np.abs(quantization_errors)
        
        # 统计指标
        print(f"\n输入信号统计:")
        print(f"  - 输入范围: {inputs.min()}-{inputs.max()}")
        print(f"  - 平均输入: {inputs.mean():.2f}")
        
        print(f"\n电流统计:")
        print(f"  - 总电流范围: {total_currents.min()*1e6:.4f} - {total_currents.max()*1e6:.4f} uA")
        print(f"  - 平均电流: {total_currents.mean()*1e6:.4f} uA")
        print(f"  - 电流标准差: {total_currents.std()*1e6:.4f} uA")
        
        print(f"\nADC输出统计:")
        print(f"  - ADC码范围: {adc_codes.min()}-{adc_codes.max()}")
        print(f"  - ADC码平均值: {adc_codes.mean():.2f}")
        
        print(f"\n量化误差统计:")
        print(f"  - 最大绝对误差: {abs_errors.max()*1e9:.4f} nA")
        print(f"  - 平均绝对误差: {abs_errors.mean()*1e9:.4f} nA")
        print(f"  - 误差RMS: {np.sqrt(np.mean(quantization_errors**2))*1e9:.4f} nA")
        
        # 计算相对误差，避免除以零
        relative_errors = []
        for i in range(len(total_currents)):
            if total_currents[i] != 0:
                relative_errors.append(abs_errors[i] / np.abs(total_currents[i]))
        
        if relative_errors:
            print(f"  - 平均相对误差: {np.mean(relative_errors)*100:.2f}%")
        else:
            print(f"  - 平均相对误差: N/A (全为零)")
        
        return {
            'inputs': inputs,
            'total_currents': total_currents,
            'adc_codes': adc_codes,
            'recovered_currents': recovered_currents,
            'quantization_errors': quantization_errors,
            'abs_errors': abs_errors
        }
    
    def plot_results(self, analysis):
        """绘制结果"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('存算结构验证结果', fontsize=14, fontweight='bold')
        
        # 1. 输入vs总电流
        ax = axes[0, 0]
        scatter = ax.scatter(analysis['inputs'], analysis['total_currents']*1e6, 
                           alpha=0.6, s=50, c=analysis['inputs'], cmap='viridis')
        ax.set_xlabel('输入码 (0-15)')
        ax.set_ylabel('总电流 (uA)')
        ax.set_title('输入 vs 位线总电流')
        ax.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax, label='Input Code')
        
        # 2. ADC输出分布
        ax = axes[0, 1]
        ax.hist(analysis['adc_codes'], bins=64, edgecolor='black', alpha=0.7)
        ax.set_xlabel('ADC码 (0-63)')
        ax.set_ylabel('出现次数')
        ax.set_title('ADC输出分布')
        ax.grid(True, alpha=0.3, axis='y')
        
        # 3. 量化误差
        ax = axes[1, 0]
        ax.scatter(range(len(analysis['quantization_errors'])), 
                  analysis['quantization_errors']*1e9, alpha=0.6, s=30)
        ax.axhline(y=0, color='r', linestyle='--', label='Zero Error')
        ax.set_xlabel('样本索引')
        ax.set_ylabel('量化误差 (nA)')
        ax.set_title('量化误差分布')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # 4. 目标vs实际电流
        ax = axes[1, 1]
        ax.scatter(analysis['total_currents']*1e6, analysis['recovered_currents']*1e6,
                  alpha=0.6, s=50, label='ADC Output')
        # 绘制理想曲线
        i_min = min(analysis['total_currents'].min(), analysis['recovered_currents'].min())
        i_max = max(analysis['total_currents'].max(), analysis['recovered_currents'].max())
        i_range = np.linspace(i_min, i_max, 100)
        ax.plot(i_range, i_range, 'r--', linewidth=2, label='Ideal')
        ax.set_xlabel('目标电流 (uA)')
        ax.set_ylabel('恢复电流 (uA)')
        ax.set_title('目标vs实际电流')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_aspect('equal')
        
        plt.tight_layout()
        return fig
    
    def print_sample_results(self, results, num_samples=10):
        """打印样本结果"""
        print(f"\n前 {num_samples} 个样本的详细结果:")
        print("-" * 100)
        print(f"{'ID':>3} {'Input':>5} {'总电流(uA)':>12} {'ADC码':>7} {'恢复电流(uA)':>14} {'误差(nA)':>10}")
        print("-" * 100)
        
        for i in range(min(num_samples, len(results))):
            r = results[i]
            error = r['recovered_current'] - r['total_current']
            print(f"{i:3d} {r['input']:5d} {r['total_current']*1e6:12.4f} "
                  f"{r['adc_code']:7d} {r['recovered_current']*1e6:14.4f} {error*1e9:10.2f}")


def main():
    """主函数"""
    # 创建验证框架
    verif = Verification(num_tests=100, seed=42)
    
    # 运行测试
    print("\n开始运行验证测试...")
    results = verif.run_tests()
    
    # 分析结果
    analysis = verif.analyze_results(results)
    
    # 打印样本
    verif.print_sample_results(results, num_samples=15)
    
    # 绘制结果
    fig = verif.plot_results(analysis)
    plt.savefig('verification_results.png', dpi=150, bbox_inches='tight')
    print("\n图表已保存为: verification_results.png")
    plt.show()


if __name__ == '__main__':
    main()
