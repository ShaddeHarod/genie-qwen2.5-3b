import json
import os
import re
import traceback
from pathlib import Path
import statistics

def robust_json_load(file_path):
    """使用多种方法尝试加载可能损坏的JSON文件"""
    
    # 方法0：预处理修复常见的格式问题
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            lines = f.readlines()
        
        # 修复 "model_output": 后跟换行和裸字符串的问题
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            if '"model_output":' in line and line.strip().endswith(':'):
                # 找到 model_output 行，检查下一行
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('"') and (next_line.endswith('",') or next_line.endswith('",')):
                        # 将两行合并
                        fixed_line = line + ' ' + next_line + '\n'
                        fixed_lines.append(fixed_line)
                        i += 2  # 跳过下一行
                        continue
                    elif next_line.startswith('"') and next_line.endswith('"'):
                        # 将两行合并并添加逗号
                        fixed_line = line + ' ' + next_line + ',\n'
                        fixed_lines.append(fixed_line)
                        i += 2  # 跳过下一行
                        continue
            
            fixed_lines.append(line + '\n')
            i += 1
        
        # 重新组合内容
        content = ''.join(fixed_lines)
        
        # 尝试解析修复后的内容
        return json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"预处理修复失败: {e}")
    
    # 方法1：直接尝试加载
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"直接加载失败: {e}")
    
    # 方法2：忽略编码错误
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            content = f.read()
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"忽略编码错误加载失败: {e}")
    
    # 方法3：清理控制字符
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            content = f.read()
        
        # 移除控制字符但保留有效的转义序列
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        
        # 修复未转义的反斜杠
        content = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', '\\\\', content)
        
        # 修复可能的引号问题
        content = re.sub(r'"([^"]*)"([^"]*)"([^"]*)"', r'"\1\2\3"', content)
        
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"清理控制字符后加载失败: {e}")
    
    # 方法4：逐行修复
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            lines = f.readlines()
        
        # 清理每行
        cleaned_lines = []
        for line in lines:
            line = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', line)
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        # 尝试重新组合
        content = '\n'.join(cleaned_lines)
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"逐行修复后加载失败: {e}")
    
    # 方法5：使用正则表达式提取关键部分
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            content = f.read()
        
        # 尝试提取subject
        subject_match = re.search(r'"subject"\s*:\s*"([^"]+)"', content)
        subject = subject_match.group(1) if subject_match else "unknown"
        
        # 尝试提取answers数组
        answers_match = re.search(r'"answers"\s*:\s*\[(.*?)\](?=\s*[,}])', content, re.DOTALL)
        if answers_match:
            answers_str = answers_match.group(1)
            
            # 尝试解析每个answer对象
            answer_pattern = r'\{\s*"question_index"\s*:\s*(\d+)\s*,\s*"final_answer"\s*:\s*"([^"]*)"[^}]*"performance_metrics"\s*:\s*\{[^}]*"prompt_processing_rate_toks_per_sec"\s*:\s*([\d.]+)[^}]*"token_generation_rate_toks_per_sec"\s*:\s*([\d.]+)[^}]*\}'
            matches = re.findall(answer_pattern, answers_str, re.DOTALL)
            
            if matches:
                answers = []
                for match in matches:
                    try:
                        answers.append({
                            "question_index": int(match[0]),
                            "final_answer": match[1],
                            "performance_metrics": {
                                "prompt_processing_rate_toks_per_sec": float(match[2]),
                                "token_generation_rate_toks_per_sec": float(match[3])
                            }
                        })
                    except (ValueError, IndexError):
                        continue
                
                return {"subject": subject, "answers": answers}
    
    except Exception as e:
        print(f"正则表达式提取失败: {e}")
    
    # 方法6：使用更激进的清理方法
    try:
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            content = f.read()
        
        # 移除所有控制字符
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\t\n\r')
        
        # 修复LaTeX转义字符
        content = content.replace('\\(', '\\\\(').replace('\\)', '\\\\)')
        content = content.replace('\\[', '\\\\[').replace('\\]', '\\\\]')
        content = content.replace('\\{', '\\\\{').replace('\\}', '\\\\}')
        
        # 修复双反斜杠
        content = re.sub(r'(?<!\\)\\(?!\\)', '\\\\', content)
        
        # 修复引号内的转义
        content = re.sub(r'"([^"]*)\\([^\\"])"', r'"\1\\\\\2"', content)
        
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"激进清理方法失败: {e}")
    
    # 方法7：逐字符修复
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        # 尝试不同的编码
        for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin1']:
            try:
                content = raw_data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            content = raw_data.decode('utf-8', errors='ignore')
        
        # 使用json5库作为最后手段（如果可用）
        try:
            import json5
            return json5.loads(content)
        except ImportError:
            pass
        
        # 手动构建数据
        lines = content.split('\n')
        answers = []
        
        current_answer = {}
        for line in lines:
            line = line.strip()
            if '"question_index"' in line:
                if current_answer:
                    answers.append(current_answer)
                current_answer = {}
                match = re.search(r':\s*(\d+)', line)
                if match:
                    current_answer['question_index'] = int(match.group(1))
            elif '"final_answer"' in line and current_answer:
                match = re.search(r':\s*"([^"]*)"', line)
                if match:
                    current_answer['final_answer'] = match.group(1)
            elif '"prompt_processing_rate_toks_per_sec"' in line and current_answer:
                if 'performance_metrics' not in current_answer:
                    current_answer['performance_metrics'] = {}
                match = re.search(r':\s*([\d.]+)', line)
                if match:
                    current_answer['performance_metrics']['prompt_processing_rate_toks_per_sec'] = float(match.group(1))
            elif '"token_generation_rate_toks_per_sec"' in line and current_answer:
                if 'performance_metrics' not in current_answer:
                    current_answer['performance_metrics'] = {}
                match = re.search(r':\s*([\d.]+)', line)
                if match:
                    current_answer['performance_metrics']['token_generation_rate_toks_per_sec'] = float(match.group(1))
        
        if current_answer:
            answers.append(current_answer)
        
        # 提取subject
        subject_match = re.search(r'"subject"\s*:\s*"([^"]+)"', content)
        subject = subject_match.group(1) if subject_match else "unknown"
        
        return {"subject": subject, "answers": answers}
    
    except Exception as e:
        print(f"最终手动修复方法失败: {e}")
    
    raise ValueError(f"无法解析JSON文件: {file_path}")

def analyze_subject_results(llm_file_path, ground_truth_path):
    """分析单个学科的结果"""
    
    try:
        # 读取LLM结果
        llm_data = robust_json_load(llm_file_path)
        
        # 验证必要字段
        if 'subject' not in llm_data:
            raise ValueError("LLM结果中缺少'subject'字段")
        if 'answers' not in llm_data:
            raise ValueError("LLM结果中缺少'answers'字段")
        
        subject = llm_data['subject']
        answers = llm_data['answers']
        
        if not isinstance(answers, list):
            raise ValueError("'answers'字段应该是列表类型")
        
        # 读取真实答案
        ground_truth_file = os.path.join(ground_truth_path, f"{subject}.json")
        if not os.path.exists(ground_truth_file):
            raise ValueError(f"找不到真实答案文件: {ground_truth_file}")
        
        ground_truth = robust_json_load(ground_truth_file)
        
        # 初始化统计变量
        total_questions = len(answers)
        correct_count = 0
        wrong_count = 0
        answer_not_found_count = 0
        answer_not_found_indices = []
        
        prompt_processing_rates = []
        token_generation_rates = []
        
        # 处理每个答案
        for i, answer_data in enumerate(answers):
            try:
                question_index = str(answer_data.get('question_index', i))
                final_answer = str(answer_data.get('final_answer', ''))
                
                # 收集性能指标
                if 'performance_metrics' in answer_data and isinstance(answer_data['performance_metrics'], dict):
                    metrics = answer_data['performance_metrics']
                    prompt_rate = float(metrics.get('prompt_processing_rate_toks_per_sec', 0))
                    token_rate = float(metrics.get('token_generation_rate_toks_per_sec', 0))
                    
                    if prompt_rate > 0:
                        prompt_processing_rates.append(prompt_rate)
                    if token_rate > 0:
                        token_generation_rates.append(token_rate)
                
                # 检查是否为"Answer Not Found"
                if final_answer.strip() == "Answer Not Found":
                    answer_not_found_count += 1
                    answer_not_found_indices.append(int(question_index))
                    wrong_count += 1
                    continue
                
                # 获取真实答案并对比
                true_answer = ground_truth.get(question_index)
                if true_answer is None:
                    print(f"警告：在{subject}中找不到问题{question_index}的真实答案")
                    wrong_count += 1
                    continue
                
                # 标准化答案比较（忽略大小写和空格）
                normalized_llm = final_answer.strip().upper()
                normalized_truth = str(true_answer).strip().upper()
                
                if normalized_llm == normalized_truth:
                    correct_count += 1
                else:
                    wrong_count += 1
                    
            except Exception as e:
                print(f"处理问题{i}时出错: {e}")
                wrong_count += 1
                continue
        
        # 计算平均性能指标
        avg_prompt_processing_rate = statistics.mean(prompt_processing_rates) if prompt_processing_rates else 0.0
        avg_token_generation_rate = statistics.mean(token_generation_rates) if token_generation_rates else 0.0
        
        # 构建结果
        result = {
            "subject": subject,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "accuracy_rate": round(correct_count / total_questions, 4) if total_questions > 0 else 0.0,
            "answer_not_found": {
                "count": answer_not_found_count,
                "question_indices": sorted(answer_not_found_indices)
            },
            "performance_metrics": {
                "avg_prompt_processing_rate_toks_per_sec": round(avg_prompt_processing_rate, 3),
                "avg_token_generation_rate_toks_per_sec": round(avg_token_generation_rate, 3),
                "total_processed_answers": len(prompt_processing_rates)
            }
        }
        
        return result
        
    except Exception as e:
        print(f"分析文件 {llm_file_path} 时发生错误: {e}")
        traceback.print_exc()
        raise

def main():
    """主函数"""

    # 设置路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.join(script_dir, "..")
    llm_answers_dir = os.path.join(base_dir, "subjects_answers_from_model")
    ground_truth_dir = os.path.join(base_dir, "subjects_answers_ground_truth")
    output_dir = os.path.join(base_dir, "subjects_perf_results")
    
    # 验证目录存在
    if not os.path.exists(llm_answers_dir):
        print(f"错误：LLM答案目录不存在: {llm_answers_dir}")
        return
    
    if not os.path.exists(ground_truth_dir):
        print(f"错误：真实答案目录不存在: {ground_truth_dir}")
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有LLM答案文件
    llm_files = [f for f in os.listdir(llm_answers_dir) 
                if f.endswith('_LLM_Answer.json') and os.path.isfile(os.path.join(llm_answers_dir, f))]
    
    if not llm_files:
        print("警告：未找到任何LLM答案文件")
        return
    
    print(f"找到 {len(llm_files)} 个学科的结果文件，开始分析...")
    
    # 统计处理结果
    processed_count = 0
    failed_count = 0
    failed_files = []
    
    # 处理每个学科
    for llm_file in llm_files:
        llm_file_path = os.path.join(llm_answers_dir, llm_file)
        
        try:
            print(f"正在处理: {llm_file}")
            
            # 分析结果
            result = analyze_subject_results(llm_file_path, ground_truth_dir)
            
            # 保存结果
            output_file = os.path.join(output_dir, f"{result['subject']}_perf.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 已处理 {result['subject']}: 总题数={result['total_questions']}, "
                  f"正确={result['correct_count']}, 错误={result['wrong_count']}, "
                  f"准确率={result['accuracy_rate']:.2%}")
            
            if result['answer_not_found']['count'] > 0:
                print(f"  - Answer Not Found: {result['answer_not_found']['count']} 题, "
                      f"题号: {result['answer_not_found']['question_indices']}")
            
            processed_count += 1
            
        except Exception as e:
            print(f"✗ 处理 {llm_file} 时出错: {str(e)}")
            failed_count += 1
            failed_files.append(llm_file)
            continue
    
    # 输出总结
    print(f"\n{'='*50}")
    print(f"处理完成！")
    print(f"成功处理: {processed_count} 个学科")
    print(f"处理失败: {failed_count} 个学科")
    
    if failed_files:
        print(f"失败的文件: {', '.join(failed_files)}")
    
    print(f"结果已保存到: {output_dir}")

if __name__ == "__main__":
    main()