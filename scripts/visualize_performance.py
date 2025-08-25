import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import rcParams

# Set font for better display
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_detailed_table(df):
    """Create detailed performance table"""
    fig, ax = plt.subplots(figsize=(18, 24))
    ax.axis('tight')
    ax.axis('off')
    
    # Calculate overall statistics
    total_questions = df['total_questions'].sum()
    total_correct = (df['total_questions'] * df['accuracy_rate']).sum()
    overall_accuracy = total_correct / total_questions if total_questions > 0 else 0
    total_answer_not_found = df['answer_not_found_count'].sum()
    overall_not_found_rate = total_answer_not_found / total_questions if total_questions > 0 else 0
    
    # Calculate weighted average throughput (weighted by number of questions)
    weighted_prompt_rate = (df['total_questions'] * df['avg_prompt_processing_rate_toks_per_sec']).sum() / total_questions if total_questions > 0 else 0
    weighted_token_rate = (df['total_questions'] * df['avg_token_generation_rate_toks_per_sec']).sum() / total_questions if total_questions > 0 else 0
    
    # Prepare table data
    df_sorted = df.sort_values('accuracy_rate', ascending=False)
    table_data = []
    for _, row in df_sorted.iterrows():
        table_data.append([
            row['subject'],
            row['total_questions'],
            f"{row['accuracy_rate']*100:.1f}%",
            row['answer_not_found_count'],
            f"{(row['answer_not_found_count']/row['total_questions']*100):.1f}%",
            f"{row.get('avg_prompt_processing_rate_toks_per_sec', 0):.1f}",
            f"{row.get('avg_token_generation_rate_toks_per_sec', 0):.1f}"
        ])
    
    # Add total row
    table_data.append([
        'Total',
        total_questions,
        f"{overall_accuracy*100:.1f}%",
        total_answer_not_found,
        f"{overall_not_found_rate*100:.1f}%",
        f"{weighted_prompt_rate:.1f}",
        f"{weighted_token_rate:.1f}"
    ])
    
    col_labels = ['Subject', 'Total Questions', 'Accuracy Rate', 'Answer Not Found', 'Not Found Rate', 
                  'Prompt Processing Rate (toks/sec)', 'Token Generation Rate (toks/sec)']
    
    table = ax.table(cellText=table_data, colLabels=col_labels, 
                    cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(6)
    table.scale(1.2, 1.2)
    
    # Set header style
    for i in range(len(col_labels)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Alternating row colors
    for i in range(1, len(table_data)):  # Exclude total row
        color = '#f0f0f0' if i % 2 == 0 else 'white'
        for j in range(len(col_labels)):
            table[(i, j)].set_facecolor(color)
    
    # Set total row style (last row)
    total_row_index = len(table_data)
    for j in range(len(col_labels)):
        table[(total_row_index, j)].set_facecolor('#FFE4B5')  # Light orange
        table[(total_row_index, j)].set_text_props(weight='bold')
    
    ax.set_title(f'Detailed Performance Data Table for {len(df)} Subjects\nOverall Accuracy: {overall_accuracy*100:.2f}% (Total Questions: {total_questions})', 
                 fontsize=16, fontweight='bold', pad=20)
    plt.savefig('subjects_perf_results/detailed_table.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_throughput_chart(df):
    """Create throughput comparison chart"""
    plt.figure(figsize=(12, 8))
    df_sorted = df.sort_values('subject')
    
    # Plot prompt processing rate
    plt.plot(df_sorted['subject'], df_sorted['avg_prompt_processing_rate_toks_per_sec'], 
             marker='o', color='blue', label='Prompt Processing Rate (toks/sec)')
    
    # Plot token generation rate
    plt.plot(df_sorted['subject'], df_sorted['avg_token_generation_rate_toks_per_sec'], 
              marker='x', color='green', label='Token Generation Rate (toks/sec)')
    
    plt.title('Throughput Comparison', fontsize=14, fontweight='bold')
    plt.xlabel('Subject')
    plt.ylabel('Throughput (toks/sec)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('subjects_perf_results/throughput_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Load data
    csv_path = 'subjects_perf_results/performance_summary.csv'
    df = pd.read_csv(csv_path)
    
    # Exclude the existing 'Total' row if it exists to avoid double counting
    df = df[df['subject'] != 'Total']
    
    # Create charts
    create_detailed_table(df)
    
    # Print statistics
    print("=== LLM Edge Deployment Benchmark Test Summary ===")
    print(f"Total subjects: {len(df)}")
    print(f"Total questions: {df['total_questions'].sum()}")
    print(f"Average accuracy: {df['accuracy_rate'].mean()*100:.2f}%")
    print(f"Highest accuracy: {df['accuracy_rate'].max()*100:.1f}% ({df.loc[df['accuracy_rate'].idxmax(), 'subject']})")
    print(f"Lowest accuracy: {df['accuracy_rate'].min()*100:.1f}% ({df.loc[df['accuracy_rate'].idxmin(), 'subject']})")
    print(f"Average unanswered questions: {df['answer_not_found_count'].mean():.1f} questions/subject")
    
    # Performance category statistics
    high_perf = df[df['accuracy_rate'] >= 0.7]
    mid_perf = df[(df['accuracy_rate'] >= 0.5) & (df['accuracy_rate'] < 0.7)]
    low_perf = df[df['accuracy_rate'] < 0.5]
    
    print(f"\nHigh performance subjects (≥70%): {len(high_perf)} subjects")
    print(f"Medium performance subjects (50-70%): {len(mid_perf)} subjects")
    print(f"Low performance subjects (<50%): {len(low_perf)} subjects")
    
    # Throughput statistics
    avg_prompt_rate = df['avg_prompt_processing_rate_toks_per_sec'].mean()
    avg_token_rate = df['avg_token_generation_rate_toks_per_sec'].mean()
    
    print(f"\n=== Throughput Statistics ===")
    print(f"Average prompt processing rate: {avg_prompt_rate:.1f} tokens/sec")
    print(f"Average token generation rate: {avg_token_rate:.1f} tokens/sec")
    print(f"Highest prompt processing rate: {df['avg_prompt_processing_rate_toks_per_sec'].max():.1f} tokens/sec")
    print(f"Highest token generation rate: {df['avg_token_generation_rate_toks_per_sec'].max():.1f} tokens/sec")
    
    print("\n=== Charts Saved ===")
    print("Generated chart files:")
    print("1. detailed_table.png - Detailed data table (with throughput)")

if __name__ == "__main__":
    main()