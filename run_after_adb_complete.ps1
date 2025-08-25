# 1. 列出所有匹配的远端文件路径
$fileList = adb shell ls data/local/tmp/genie-qwen2.5-3b/result/*_LLM_Answer.json

# 2. 遍历每个远端路径并 pull 到本地
foreach ($remotePath in $fileList) {
    # 去除首尾空白，并提取文件名
    $remotePath = $remotePath.Trim()
    $fileName   = [System.IO.Path]::GetFileName($remotePath)
    # 拉取到目标文件夹（路径中含空格时用双引号）
    adb pull $remotePath ".\subjects_answers_from_model\$fileName"
}

python scripts/analyze_llm_results.py
python scripts/generate_performance_excel.py
python scripts/visualize_performance.py