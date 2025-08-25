#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的JSON文件是否能正常解析
"""

import json
import os
from pathlib import Path


def test_json_file(file_path):
    """测试单个JSON文件是否能正常解析"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查基本结构
        if 'subject' not in data:
            return False, "缺少 'subject' 字段"
        
        if 'answers' not in data:
            return False, "缺少 'answers' 字段"
        
        answers = data['answers']
        if not isinstance(answers, list):
            return False, "'answers' 不是列表类型"
        
        # 检查前几个答案的结构
        for i, answer in enumerate(answers[:5]):
            if 'final_answer' not in answer:
                return False, f"答案 {i} 缺少 'final_answer' 字段"
            
            if 'performance_metrics' not in answer:
                return False, f"答案 {i} 缺少 'performance_metrics' 字段"
            
            # 检查 final_answer 是否为字符串
            if not isinstance(answer['final_answer'], str):
                return False, f"答案 {i} 的 'final_answer' 不是字符串类型"
        
        return True, f"✓ 成功解析，包含 {len(answers)} 个答案"
        
    except json.JSONDecodeError as e:
        return False, f"JSON解析错误: {e}"
    except Exception as e:
        return False, f"其他错误: {e}"


def main():
    """主函数"""
    
    script_dir = Path(__file__).parent
    subjects_dir = script_dir.parent / "subjects_answers_from_model"
    
    if not subjects_dir.exists():
        print(f"错误：目录不存在 {subjects_dir}")
        return
    
    # 获取所有JSON文件
    json_files = list(subjects_dir.glob("*_LLM_Answer.json"))
    
    if not json_files:
        print("没有找到JSON文件")
        return
    
    print(f"测试 {len(json_files)} 个JSON文件...")
    print("=" * 80)
    
    success_count = 0
    fail_count = 0
    failed_files = []
    
    for json_file in sorted(json_files):
        success, message = test_json_file(json_file)
        
        if success:
            print(f"✓ {json_file.name:<40} {message}")
            success_count += 1
        else:
            print(f"✗ {json_file.name:<40} {message}")
            fail_count += 1
            failed_files.append(json_file.name)
    
    # 输出统计结果
    print("=" * 80)
    print(f"测试完成！")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")
    
    if failed_files:
        print(f"\n失败的文件:")
        for file_name in failed_files:
            print(f"  - {file_name}")


if __name__ == "__main__":
    main()
