#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 subjects_answers_from_model 目录中 JSON 文件的 model_output 格式问题

问题描述:
- model_output 字段的内容可能包含控制字符、换行符等
- 导致 JSON 解析时出现 "Invalid control character" 错误
- 这些内容对分析结果没有价值，只会造成解析问题

解决方案:
- 自动创建 original_backup 目录并移动原始JSON文件进行备份
- 直接删除整个 model_output 字段
- 保留 final_answer 和 performance_metrics 等有用字段
- 确保 JSON 格式完全正确，避免所有解析错误

使用方法:
- 直接运行脚本，无需手动创建目录或移动文件
- 脚本会自动处理备份和修复流程
"""

import os
import re
import json
from pathlib import Path


def fix_model_output_in_file(source_file_path, output_dir):
    """删除单个JSON文件中的model_output字段以修复格式问题"""
    print(f"正在处理: {source_file_path.name}")
    
    try:
        # 读取原文件内容
        with open(source_file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            content = f.read()
        
        # 修复 model_output 格式
        fixed_content = fix_model_output_content(content)
        
        # 验证修复后的JSON是否有效
        try:
            data = json.loads(fixed_content)
            print(f"  ✓ JSON验证成功")
            
            # 保存修复后的文件到输出目录
            output_file_path = output_dir / source_file_path.name
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"  ✓ 文件修复完成: {output_file_path}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON验证失败: {e}")
            # 如果JSON仍然无效，保存修复尝试的内容以供调试
            debug_path = output_dir / (source_file_path.stem + '.debug')
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"  调试文件已保存: {debug_path}")
            return False
            
    except Exception as e:
        print(f"  ✗ 处理文件失败: {e}")
        return False


def fix_model_output_content(content):
    """删除model_output字段来修复JSON格式问题"""
    # 方法1: 跨行、非贪婪删除：从 ,"model_output": 开始，一直到下一个 ,"performance_metrics" 之前
    # 说明：
    # - 使用 [\s\S]*? 覆盖任意字符（包括换行）
    # - 使用前瞻确保不吞掉后续的 ,"performance_metrics"
    pattern_crossline = r',\s*"model_output"\s*:\s*[\s\S]*?(?=(,\s*"performance_metrics"))'
    fixed_content = re.sub(pattern_crossline, '', content)
    
    # 方法2: 如果方法1没有匹配到，尝试逐行处理
    if fixed_content == content:
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        skip_mode = False
        
        while i < len(lines):
            line = lines[i]
            
            # 检查是否进入 model_output 区域
            if '"model_output":' in line:
                skip_mode = True
                # 跳过这行，但保留前面的内容直到 model_output
                before_model_output = line[:line.find('"model_output"')]
                if before_model_output.strip().endswith(','):
                    # 如果前面有逗号，保留到逗号前
                    before_model_output = before_model_output.rstrip().rstrip(',')
                
                # 查找 performance_metrics 开始的行
                temp_i = i
                while temp_i < len(lines):
                    temp_line = lines[temp_i]
                    if '"performance_metrics"' in temp_line:
                        # 找到 performance_metrics，添加逗号连接
                        if before_model_output.strip():
                            fixed_lines.append(before_model_output + ',')
                        fixed_lines.append(temp_line)
                        i = temp_i + 1
                        skip_mode = False
                        break
                    temp_i += 1
                else:
                    # 没找到 performance_metrics，保持原样
                    fixed_lines.append(line)
                    i += 1
                    skip_mode = False
            elif skip_mode:
                # 在跳过模式中，检查是否到达 performance_metrics
                if '"performance_metrics"' in line:
                    fixed_lines.append(line)
                    skip_mode = False
                # 否则跳过这行
                i += 1
            else:
                # 正常行，直接添加
                fixed_lines.append(line)
                i += 1
        
        fixed_content = '\n'.join(fixed_lines)
    
    return fixed_content


def main():
    """主函数"""
    
    # 设置路径
    script_dir = Path(__file__).parent
    subjects_dir = script_dir.parent / "subjects_answers_from_model"
    original_dir = subjects_dir / "original_backup"
    output_dir = subjects_dir
    
    # 检查subjects_answers_from_model目录是否存在
    if not subjects_dir.exists():
        print(f"错误：目录不存在 {subjects_dir}")
        return
    
    # 如果original_backup目录不存在，创建它并移动JSON文件
    if not original_dir.exists():
        print(f"创建备份目录: {original_dir}")
        original_dir.mkdir(parents=True, exist_ok=True)
        
        # 查找subjects_answers_from_model中的JSON文件
        json_files_to_move = list(subjects_dir.glob("*_LLM_Answer.json"))
        
        if json_files_to_move:
            print(f"找到 {len(json_files_to_move)} 个JSON文件，正在移动到备份目录...")
            for json_file in json_files_to_move:
                backup_path = original_dir / json_file.name
                json_file.rename(backup_path)
                print(f"  已移动: {json_file.name}")
        else:
            print("警告：未找到任何JSON文件需要备份")
    
    # 获取所有JSON文件
    json_files = list(original_dir.glob("*_LLM_Answer.json"))
    
    if not json_files:
        print("没有找到需要处理的JSON文件")
        return
    
    print(f"找到 {len(json_files)} 个JSON文件，开始处理...")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    failed_files = []
    
    for json_file in sorted(json_files):
        if fix_model_output_in_file(json_file, output_dir):
            success_count += 1
        else:
            fail_count += 1
            failed_files.append(json_file.name)
        print("-" * 40)
    
    # 输出统计结果
    print("=" * 60)
    print("处理完成！")
    print(f"成功修复: {success_count} 个文件")
    print(f"修复失败: {fail_count} 个文件")
    
    if failed_files:
        print(f"\n失败的文件:")
        for file_name in failed_files:
            print(f"  - {file_name}")
    
    print(f"\n原始文件保存在: {original_dir}")
    print(f"修复后文件保存在: {output_dir}")
    print("如果出现问题，原始文件仍保持完整")


if __name__ == "__main__":
    main()
