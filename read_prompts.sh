#!/system/bin/sh
# run_prompts.sh
# 用法: sh run_prompts.sh prompts.txt output_dir config_path

set -e

export LD_LIBRARY_PATH=$PWD
export ADSP_LIBRARY_PATH=$PWD
chmod +x /data/local/tmp/genie-qwen2.5-3b/genie-t2t-run




PROMPTS_FILE="$1"
OUTPUT_DIR="$2"
CONFIG_PATH="$3"
# 暂不删除之前的输出结果,保证运行不同学科时，可以中断运行。
# 重新创建目录。确保输出目录存在
#  -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

idx=0
prompt=""
# 使用关联数组存储每个科目的答案（模拟，因为sh不支持关联数组，我们用文件）
temp_dir="${OUTPUT_DIR}/temp"
mkdir -p "$temp_dir"

while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    -----*)  # 行首两个或以上 '-'
      if [ -n "$prompt" ]; then
        # 去掉首尾空白
        # 兼容 adb shell，简化 trim
        prompt=$(printf "%s" "$prompt" | sed -e '1{/^[[:space:]]*$/d}' -e :a -e '$!N;s/\n[[:space:]]*$/\n/;ta')
        
        # 提取科目和问题序号 - 修复正则表达式和处理方式
        subject=$(printf "%s" "$prompt" | grep "^科目：" | sed 's/科目：//' | tr -d '\n\r')
        question_idx=$(printf "%s" "$prompt" | grep "^[0-9][0-9]*\. 问题：" | sed 's/\. 问题：.*//' | tr -d '\n\r')
        
        # 获取已完成的题目数量
        finished_count=$(cat "required_json/finished_subjects.json" | grep -o "\"${subject}_prompts\":[[:space:]]*[0-9]*" | sed 's/.*://' | tr -d ' ')
        [ -z "$finished_count" ] && finished_count=0
        
        # 如果当前问题序号小于已完成数量，跳过处理
        if [ "$question_idx" -lt "$finished_count" ]; then
            echo "=== 跳过 Prompt #$idx (Subject: $subject, Question: $question_idx) - 已完成 $finished_count 题 ==="
            idx=$((idx + 1))
            prompt=""
            continue
        fi
        
        echo "=== Prompt #$idx (Subject: $subject, Question: $question_idx) ==="
        
        # 生成临时输出文件名
        mkdir -p "${OUTPUT_DIR}/temp/${subject}"
        temp_output="${temp_dir}/${subject}/temp_${subject}_${idx}.json"
        
        # 格式化prompt以适应Qwen2.5 3B instruct格式
        formatted_prompt="<|im_start|>system\n你是一个做题专家。先思考并输出解题步骤，解题完后另起一行，此行只输出答案选项，格式必须为“答案：A”，（A或B或C或D，单选）最后一行不要添加格式要求外的任何其他文字或字符。<|im_end|><|im_start|>user\n${prompt}<|im_end|>\n<|im_end|><|im_start|>assistant\n"
        
        # genie-t2t-run的代码，根据文档修改参数
        # 使用--config指定配置文件，--prompt指定输入，输出重定向到文件
        /data/local/tmp/genie-qwen2.5-3b/genie-t2t-run \
          --config "$CONFIG_PATH" \
          --prompt "$formatted_prompt" > "$temp_output" 2>&1

        # 将答案信息添加到对应科目的临时文件中
        subject_file="${temp_dir}/${subject}_answers.txt"
        if [ -f "$temp_output" ]; then
          # 提取[BEGIN] [END]之间的内容作为答案
          model_answer=$(sed -n '/\[BEGIN\]/,/\[KPIS\]/p' "$temp_output" | sed -n 'p/\[END\]/q' | sed 's/\[BEGIN\]: //;s/\[END\].*//')
          echo "Model Answer：\n$model_answer"

          # 提取最终答案（A、B、C或D）
          # final_answer=$(echo "$model_answer" | tail -2 | sed -n 's/.*答案：\([ABCD,、 ]*\).*/\1/p' | sed 's/[ ,、]//g')
          # 放宽，只要最后有答案就提取，不用有“答案：”
          final_answer=$(echo "$model_answer" | tail -2 | sed 's/答案[:：[:space:]]*//g' | sed -n 's/\([ABCD,、 ]*\).*/\1/p' | tr -d '\n' | tr -d '\r' | sed 's/[[:space:],、]//g')
          echo "Final Answer：$final_answer"
          [ -z "$final_answer" ] && final_answer="Answer Not Found"

          # 提取[KPIS]性能指标
          init_time=$(grep "Init Time:" "$temp_output" | sed 's/.*Init Time: \([0-9]*\) us.*/\1/')
          prompt_time=$(grep "Prompt Processing Time:" "$temp_output" | sed 's/.*Prompt Processing Time: \([0-9]*\) us.*/\1/')
          prompt_rate=$(grep "Prompt Processing Rate" "$temp_output" | sed 's/.*Prompt Processing Rate : \([0-9.]*\) toks\/sec.*/\1/')
          token_time=$(grep "Token Generation Time:" "$temp_output" | sed 's/.*Token Generation Time: \([0-9]*\) us.*/\1/')
          token_rate=$(grep "Token Generation Rate:" "$temp_output" | sed 's/.*Token Generation Rate: \([0-9.]*\) toks\/sec.*/\1/')
          
          # 新增：记录当前题目的时间戳（中国时间格式）
          timestamp=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')
          
          # 创建答案条目
          echo "ANSWER_START" >> "$subject_file"
          echo "question_index:$question_idx" >> "$subject_file"
          echo "global_index:$idx" >> "$subject_file"
          echo "timestamp:$timestamp" >> "$subject_file"
          echo "final_answer:$final_answer" >> "$subject_file"
          echo "model_output:" >> "$subject_file"
          echo "$model_answer\n" >> "$subject_file"
          echo "performance_metrics:" >> "$subject_file"
          echo "init_time:$init_time" >> "$subject_file"
          echo "prompt_processing_time:$prompt_time" >> "$subject_file"
          echo "prompt_processing_rate:$prompt_rate" >> "$subject_file"
          echo "token_generation_time:$token_time" >> "$subject_file"
          echo "token_generation_rate:$token_rate" >> "$subject_file"
          echo "ANSWER_END" >> "$subject_file"
          echo "  → processed question $question_idx for subject $subject"
        fi
        
        echo
        
        # 更新已完成题目数量（使用question_idx+1，因为question_idx是从0开始的）
        finished_key="${subject}_prompts"
        next_question=$((question_idx + 1))
        temp_json=$(mktemp)
        
        # 读取当前JSON内容
        cat "required_json/finished_subjects.json" > "$temp_json"
        
        # 更新或添加新的完成数量
        if grep -q "\"$finished_key\"" "$temp_json"; then
            # 已存在，更新值
            sed -i "s/\"$finished_key\":[[:space:]]*[0-9]*/\"$finished_key\": $next_question/" "$temp_json"
        else
            # 不存在，添加新键值对
            if [ "$(cat "$temp_json" | wc -c)" -le 3 ]; then
                # 空对象
                echo "{\"$finished_key\": $next_question}" > "$temp_json"
            else
                # 非空对象
                sed -i "s/}$/, \"$finished_key\": $next_question}/" "$temp_json"
            fi
        fi
        
        # 写回原文件
        cat "$temp_json" > "required_json/finished_subjects.json"
        rm -f "$temp_json"
        
        idx=$((idx + 1))
        prompt=""
        # 让手机adb shell休息
        echo "等待5秒让手机休息..."
        sleep 5
      fi
      ;;
    *)  # 普通行，累积到当前 prompt，注意line后有换行，才加的”
      if echo "$line" | grep -q '[^[:space:]]'; then
        prompt="${prompt}${line}
"
      fi
      ;;
  esac
done < "$PROMPTS_FILE"



echo "=== 生成最终的科目答案JSON文件 ==="

# 为每个科目生成最终的JSON文件
for subject_file in "$temp_dir"/*_answers.txt; do
  [ -f "$subject_file" ] || continue
  
  # 提取科目名
  subject=$(basename "$subject_file" "_answers.txt")
  output_file="${OUTPUT_DIR}/${subject}_LLM_Answer.json"
  [ -f "$output_file" ] && continue
  
  echo "生成 $output_file..."
  
  # 创建JSON文件
  echo "{" > "$output_file"
  echo "  \"subject\": \"$subject\"," >> "$output_file"
  echo "  \"answers\": [" >> "$output_file"
  
  # 解析答案文件并生成JSON
  first_answer=true
  while IFS= read -r line; do
    case "$line" in
      "ANSWER_START")
        if [ "$first_answer" = "true" ]; then
          first_answer=false
        else
          echo "    }," >> "$output_file"
        fi
        echo "    {" >> "$output_file"
        ;;
      "question_index:"*)
        q_idx=$(echo "$line" | sed 's/question_index://')
        echo "      \"question_index\": $q_idx," >> "$output_file"
        ;;
      "global_index:"*)
        g_idx=$(echo "$line" | sed 's/global_index://')
        echo "      \"global_index\": $g_idx," >> "$output_file"
        ;;
      "timestamp:"*)
        ts=$(echo "$line" | sed 's/timestamp://')
        echo "      \"timestamp\": \"$ts\"," >> "$output_file"
        ;;
      "final_answer:"*)
        f_ans=$(echo "$line" | sed 's/final_answer://')
        echo "      \"final_answer\": \"$f_ans\"," >> "$output_file"
        ;;
      "model_output:")
        echo "      \"model_output\": " >> "$output_file"
        # 读取到performance_metrics之前的所有内容作为model_output
        model_output=""
        first_line=true
        while IFS= read -r output_line; do
          if [ "$output_line" = "performance_metrics:" ] || [ "$output_line" = "ANSWER_END" ]; then
            break
          fi
          if [ "$first_line" = "true" ]; then
            model_output="\"$output_line"
            first_line=false
          else
            model_output="${model_output}\n${output_line}"
          fi
        done
        model_output="${model_output}\""
        # 直接输出model_output（不需要去掉换行符）
        printf "%s" "$model_output" >> "$output_file"
        
        # 如果当前行是performance_metrics，则继续读取性能指标
        if [ "$output_line" = "performance_metrics:" ]; then
          echo "," >> "$output_file"
          echo "      \"performance_metrics\": {" >> "$output_file"
          
          # 读取性能指标
          perf_count=0
          while IFS= read -r perf_line; do
            if [ "$perf_line" = "ANSWER_END" ]; then
              break
            fi
            if [ $perf_count -gt 0 ]; then
              echo "," >> "$output_file"
            fi
            case "$perf_line" in
              "init_time:"*)
                init_time_val=$(echo "$perf_line" | sed 's/init_time://')
                printf "        \"init_time_us\": $init_time_val" >> "$output_file"
                ;;
              "prompt_processing_time:"*)
                prompt_time_val=$(echo "$perf_line" | sed 's/prompt_processing_time://')
                printf "        \"prompt_processing_time_us\": $prompt_time_val" >> "$output_file"
                ;;
              "prompt_processing_rate:"*)
                prompt_rate_val=$(echo "$perf_line" | sed 's/prompt_processing_rate://')
                printf "        \"prompt_processing_rate_toks_per_sec\": $prompt_rate_val" >> "$output_file"
                ;;
              "token_generation_time:"*)
                token_time_val=$(echo "$perf_line" | sed 's/token_generation_time://')
                printf "        \"token_generation_time_us\": $token_time_val" >> "$output_file"
                ;;
              "token_generation_rate:"*)
                token_rate_val=$(echo "$perf_line" | sed 's/token_generation_rate://')
                printf "        \"token_generation_rate_toks_per_sec\": $token_rate_val" >> "$output_file"
                ;;
            esac
            perf_count=$((perf_count + 1))
          done
          
          echo "" >> "$output_file"
          echo "      }" >> "$output_file"
        fi
        ;;
    esac
  done < "$subject_file"
  
  # 结束最后一个答案和整个JSON
  echo "    }" >> "$output_file"
  echo "  ]" >> "$output_file"
  echo "}" >> "$output_file"
  
  echo "  → saved to $output_file"
done

# 清理临时文件
#rm -rf "$temp_dir"

echo "=== 所有科目答案文件生成完成 ==="