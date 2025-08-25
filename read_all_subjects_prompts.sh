#!/system/bin/sh
# read_all_subjects_prompts.sh
# 循环运行read_prompts.sh处理所有科目的prompts文件

set -e

# 定义目录和文件
PROMPTS_DIR="prompts_by_subject"
FINISHED_FILE="required_json/finished_subjects.json"
QUESTION_COUNTS_FILE="required_json/question_counts_by_subject.json"
# 如果finished_subjects.json不存在，创建一个空的JSON文件
if [ ! -f "$FINISHED_FILE" ]; then
    echo "{}" > "$FINISHED_FILE"
fi

# 计数器
total_files=0
processed_files=0
skipped_files=0

# 遍历prompts_by_subject目录下的所有*_prompts.txt文件
for prompt_file in "$PROMPTS_DIR"/*_prompts.txt; do
    [ -f "$prompt_file" ] || continue
    
    total_files=$((total_files + 1))
    
    # 获取文件名（不含路径）
    filename=$(basename "$prompt_file")
    
    # 去掉_prompts.txt后缀作为subject key
    finished_subject_key=$(basename "$filename" .txt)
    total_subject_key=$(basename "$filename" _prompts.txt)
    subject_key=$total_subject_key
    # 获取已完成的题目数量和总题目数量
    finished_count=$(cat "$FINISHED_FILE" | grep -o "\"${finished_subject_key}\":[[:space:]]*[0-9]*" | sed 's/.*://' | tr -d ' ')
    total_count=$(cat "$QUESTION_COUNTS_FILE" | grep -o "\"${total_subject_key}\":[[:space:]]*[0-9]*" | sed 's/.*://' | tr -d ' ')
    
    # # 如果finished_count为空，设为0
    # [ -z "$finished_count" ] && finished_count=0
    
    # 如果已完成数量等于总数量，跳过该科目
    if [ "$finished_count" -eq "$total_count" ]; then
        echo "跳过已完成的科目: $subject_key ($finished_count/$total_count)"
        skipped_files=$((skipped_files + 1))
        continue
    fi
    
    # 如果已完成数量大于等于总数量，也跳过
    if [ "$finished_count" -ge "$total_count" ]; then
        echo "科目 $subject_key 已完成 ($finished_count/$total_count)，跳过"
        skipped_files=$((skipped_files + 1))
        continue
    fi
    
    echo "开始处理科目: $subject_key"
    
    # 运行read_prompts.sh脚本
    sh read_prompts.sh "$prompt_file" "result" "genie_config.json"
    
    processed_files=$((processed_files + 1))
    echo "完成处理科目: $subject_key"
    
    # 让手机adb shell休息5分钟
    echo "等待5分钟让手机adb shell休息..."
    sleep 300
done

echo "=== 处理完成统计 ==="
echo "总文件数: $total_files"
echo "已处理: $processed_files"
echo "已跳过: $skipped_files"
echo "所有科目的prompts文件处理完成！"