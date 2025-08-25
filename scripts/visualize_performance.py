import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import rcParams

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_accuracy_bar_chart(df):
    """创建前20个科目准确率柱状图"""
    plt.figure(figsize=(12, 8))
    top_20 = df.nlargest(20, 'accuracy_rate')
    bars = plt.bar(range(len(top_20)), top_20['accuracy_rate']*100, color='skyblue')
    plt.xticks(range(len(top_20)), top_20['subject'], rotation=45, ha='right')
    plt.title('Top 20 科目准确率', fontsize=14, fontweight='bold')
    plt.ylabel('准确率 (%)')
    plt.xlabel('科目')
    plt.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for i, (bar, value) in enumerate(zip(bars, top_20['accuracy_rate'])):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{value*100:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('subjects_perf_results/accuracy_bar_chart.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_distribution_histogram(df):
    """创建准确率分布直方图"""
    plt.figure(figsize=(10, 6))
    n, bins, patches = plt.hist(df['accuracy_rate']*100, bins=15, color='lightgreen', 
                               alpha=0.7, edgecolor='black')
    plt.title('准确率分布', fontsize=14, fontweight='bold')
    plt.xlabel('准确率 (%)')
    plt.ylabel('科目数量')
    plt.grid(axis='y', alpha=0.3)
    
    # 添加统计信息
    mean_acc = df['accuracy_rate'].mean()*100
    plt.axvline(mean_acc, color='red', linestyle='--', linewidth=2, 
               label=f'平均值: {mean_acc:.1f}%')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('subjects_perf_results/distribution_histogram.png', dpi=300, bbox_inches='tight')
    plt.close()


def create_unanswered_chart(df):
    """创建未找到答案的题目数量图"""
    plt.figure(figsize=(12, 8))
    bars = plt.bar(range(len(df)), df['answer_not_found_count'], color='salmon')
    plt.xticks(range(len(df)), df['subject'], rotation=45, ha='right')
    plt.title('未找到答案的题目数量', fontsize=14, fontweight='bold')
    plt.ylabel('数量')
    plt.xlabel('科目')
    plt.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('subjects_perf_results/unanswered_chart.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_performance_categories(df):
    """创建性能分级饼图"""
    # 性能分级
    high_perf = df[df['accuracy_rate'] >= 0.7]
    medium_perf = df[(df['accuracy_rate'] >= 0.5) & (df['accuracy_rate'] < 0.7)]
    low_perf = df[df['accuracy_rate'] < 0.5]
    
    plt.figure(figsize=(8, 8))
    sizes = [len(high_perf), len(medium_perf), len(low_perf)]
    labels = [f'高表现\n(≥70%)\n{len(high_perf)}个', 
             f'中等表现\n(50-70%)\n{len(medium_perf)}个', 
             f'低表现\n(<50%)\n{len(low_perf)}个']
    colors = ['#90EE90', '#FFD700', '#FFB6C1']
    
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('性能分级分布', fontsize=14, fontweight='bold')
    plt.axis('equal')
    
    plt.tight_layout()
    plt.savefig('subjects_perf_results/performance_categories.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_detailed_table(df):
    """创建详细数据表"""
    fig, ax = plt.subplots(figsize=(16, 20))
    ax.axis('tight')
    ax.axis('off')
    
    # 计算总体准确率
    total_questions = df['total_questions'].sum()
    total_correct = (df['total_questions'] * df['accuracy_rate']).sum()
    overall_accuracy = total_correct / total_questions if total_questions > 0 else 0
    
    # 准备表格数据
    df_sorted = df.sort_values('accuracy_rate', ascending=False)
    table_data = []
    for _, row in df_sorted.iterrows():
        table_data.append([
            row['subject'],
            row['total_questions'],
            f"{row['accuracy_rate']*100:.1f}%",
            row['answer_not_found_count'],
            f"{(row['answer_not_found_count']/row['total_questions']*100):.1f}%"
        ])
    
    col_labels = ['科目名称', '题目数量', '准确率', '未找到答案', '未找到比例']
    
    table = ax.table(cellText=table_data, colLabels=col_labels, 
                    cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(6)
    table.scale(1.2, 1.2)
    
    # 设置表头样式
    for i in range(len(col_labels)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # 交替行颜色
    for i in range(1, len(table_data)+1):
        color = '#f0f0f0' if i % 2 == 0 else 'white'
        for j in range(len(col_labels)):
            table[(i, j)].set_facecolor(color)
    
    ax.set_title(f'{len(df)}科目详细性能数据表\n总体准确率: {overall_accuracy*100:.2f}% (总题目数: {total_questions})', 
                 fontsize=16, fontweight='bold', pad=20)
    plt.savefig('subjects_perf_results/detailed_table.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # 读取数据
    csv_path = 'subjects_perf_results/performance_summary.csv'
    df = pd.read_csv(csv_path)
    
    # 创建各个图表
    create_accuracy_bar_chart(df)
    create_distribution_histogram(df)
    create_unanswered_chart(df)
    create_performance_categories(df)
    create_detailed_table(df)
    
    # 打印统计信息
    print("=== 大模型端侧部署基准测试统计摘要 ===")
    print(f"总科目数量: {len(df)}")
    print(f"总题目数量: {df['total_questions'].sum()}")
    print(f"平均准确率: {df['accuracy_rate'].mean()*100:.2f}%")
    print(f"最高准确率: {df['accuracy_rate'].max()*100:.1f}% ({df.loc[df['accuracy_rate'].idxmax(), 'subject']})")
    print(f"最低准确率: {df['accuracy_rate'].min()*100:.1f}% ({df.loc[df['accuracy_rate'].idxmin(), 'subject']})")
    print(f"平均未找到答案: {df['answer_not_found_count'].mean():.1f} 题/科目")
    
    # 性能分级统计
    high_perf = df[df['accuracy_rate'] >= 0.7]
    mid_perf = df[(df['accuracy_rate'] >= 0.5) & (df['accuracy_rate'] < 0.7)]
    low_perf = df[df['accuracy_rate'] < 0.5]
    
    print(f"\n高表现科目 (≥70%): {len(high_perf)}个")
    print(f"中等表现科目 (50-70%): {len(mid_perf)}个")
    print(f"低表现科目 (<50%): {len(low_perf)}个")
    
    print("\n=== 图表已保存 ===")
    print("已生成以下单独图表文件:")
    print("1. accuracy_bar_chart.png - 前20科目准确率柱状图")
    print("2. distribution_histogram.png - 准确率分布直方图")
    print("3. unanswered_chart.png - 未找到答案题目数量图")
    print("4. performance_categories.png - 性能分级饼图")
    print("5. detailed_table.png - 详细数据表")

if __name__ == "__main__":
    main()