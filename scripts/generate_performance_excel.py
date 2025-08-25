import json
import pandas as pd
import os
import glob

# Set directory paths - using relative path from script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
perf_dir = os.path.join(script_dir, "..", "subjects_perf_results")

# Get all JSON files
json_files = glob.glob(os.path.join(perf_dir, "*_perf.json"))

# Prepare data list
data_list = []

# Iterate through all JSON files
for json_file in json_files:
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract required fields
        row = {
    'subject': data.get('subject', ''),
    'total_questions': data.get('total_questions', 0),
    'accuracy_rate': data.get('accuracy_rate', 0),
    'answer_not_found_count': data.get('answer_not_found', {}).get('count', 0),
    'avg_prompt_processing_rate_toks_per_sec': data.get('performance_metrics', {}).get('avg_prompt_processing_rate_toks_per_sec', 0),
    'avg_token_generation_rate_toks_per_sec': data.get('performance_metrics', {}).get('avg_token_generation_rate_toks_per_sec', 0)
}
        
        data_list.append(row)
        
    except Exception as e:
        print(f"Error processing {json_file}: {e}")

# Create DataFrame
df = pd.DataFrame(data_list)

# Sort by subject
df = df.sort_values('subject')

# Calculate total row
total_questions = df['total_questions'].sum()
total_correct = (df['total_questions'] * df['accuracy_rate']).sum()
overall_accuracy = total_correct / total_questions if total_questions > 0 else 0
total_answer_not_found = df['answer_not_found_count'].sum()

# Calculate weighted average throughput (weighted by number of questions)
weighted_prompt_rate = (df['total_questions'] * df['avg_prompt_processing_rate_toks_per_sec']).sum() / total_questions if total_questions > 0 else 0
weighted_token_rate = (df['total_questions'] * df['avg_token_generation_rate_toks_per_sec']).sum() / total_questions if total_questions > 0 else 0

# Add total row
total_row = {
    'subject': 'Total',
    'total_questions': total_questions,
    'accuracy_rate': overall_accuracy,
    'answer_not_found_count': total_answer_not_found,
    'avg_prompt_processing_rate_toks_per_sec': weighted_prompt_rate,
    'avg_token_generation_rate_toks_per_sec': weighted_token_rate
}

# Add total row to DataFrame
df_with_total = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

# Save as Excel file
excel_path = os.path.join(perf_dir, 'performance_summary.xlsx')
df_with_total.to_excel(excel_path, index=False, engine='openpyxl')

# Save as CSV file
csv_path = os.path.join(perf_dir, 'performance_summary.csv')
df_with_total.to_csv(csv_path, index=False, encoding='utf-8')

print(f"Excel file generated: {excel_path}")
print(f"CSV file generated: {csv_path}")
print(f"Processed {len(data_list)} JSON files")
print(f"\n=== Overall Statistics ===")
print(f"Total questions: {total_questions}")
print(f"Overall accuracy: {overall_accuracy*100:.2f}%")
print(f"Total unanswered: {total_answer_not_found}")
print(f"Weighted average prompt processing rate: {weighted_prompt_rate:.1f} tokens/sec")
print(f"Weighted average token generation rate: {weighted_token_rate:.1f} tokens/sec")