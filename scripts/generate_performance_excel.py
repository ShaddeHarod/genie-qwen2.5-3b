import json
import pandas as pd
import os
import glob

# 设置目录路径 - 使用脚本所在目录的相对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
perf_dir = os.path.join(script_dir, "..", "subjects_perf_results")

# 获取所有JSON文件
json_files = glob.glob(os.path.join(perf_dir, "*_perf.json"))

# 准备数据列表
data_list = []

# 遍历所有JSON文件
for json_file in json_files:
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取所需字段
        row = {
            'subject': data.get('subject', ''),
            'total_questions': data.get('total_questions', 0),
            'accuracy_rate': data.get('accuracy_rate', 0),
            'answer_not_found_count': data.get('answer_not_found', {}).get('count', 0)
        }
        
        data_list.append(row)
        
    except Exception as e:
        print(f"Error processing {json_file}: {e}")

# 创建DataFrame
df = pd.DataFrame(data_list)

# 按subject排序
df = df.sort_values('subject')

# 保存为Excel文件
excel_path = os.path.join(perf_dir, 'performance_summary.xlsx')
df.to_excel(excel_path, index=False, engine='openpyxl')

# 保存为CSV文件
csv_path = os.path.join(perf_dir, 'performance_summary.csv')
df.to_csv(csv_path, index=False, encoding='utf-8')

print(f"Excel文件已生成: {excel_path}")
print(f"CSV文件已生成: {csv_path}")
print(f"共处理了 {len(data_list)} 个JSON文件")