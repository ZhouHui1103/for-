import os
import subprocess
import sys
import re

def review_and_correct_file(filepath):
    """
    Processes a markdown file to bold all generated content before conversion.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except FileNotFoundError:
        print(f"修正警告：未找到文件 {filepath}，跳过格式修正。")
        return

    parts = original_content.split('### **正文**')
    if len(parts) < 2:
        return

    header = parts[0]
    body_part = '### **正文**' + parts[1]
    
    # 修正作者描述
    header = re.sub(r'^(资深企业顾问 & 创业导师)$', r'**\1**', header, flags=re.MULTILINE)

    new_body_lines = []
    in_generated_paragraph = False
    
    # 按段落处理
    paragraphs = body_part.split('\n\n')
    
    new_paragraphs = []

    for para in paragraphs:
        # 场景说明，例如 (开场...)
        para = re.sub(r'^(\(.*\))$', r'**\1**', para, flags=re.MULTILINE)
        
        # 如果段落内没有任何时间戳，则认为是生成内容，全部加粗
        if '<sup>' not in para and '###' not in para and para.strip():
            # 移除已有的`**`避免嵌套，然后包裹整个段落
            cleaned_para = para.replace('**', '')
            new_paragraphs.append(f'**{cleaned_para}**')
        else:
            new_paragraphs.append(para)

    corrected_body = "\n\n".join(new_paragraphs)
    new_content = header + corrected_body

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"已完成文件格式修正: {filepath}")


def convert_md_to_docx():
    """
    Converts specific markdown files to docx using pandoc after correcting them.
    """
    # Ensure the script runs with UTF-8 encoding
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    # The files to process are the annotated files
    md_dir = os.path.join("粗剪文稿（生成式）", "赖琴")
    files_to_process = [
        "生成式文稿-女性创业时代_annotated.md",
        "生成式文稿-凭运气赚的钱_annotated.md",
        "生成式文稿-少年得志的陷阱_annotated.md",
        "生成式文稿-小弟都上市了_annotated.md"
    ]

    # Check if pandoc is installed
    try:
        subprocess.run(["pandoc", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误：未找到 pandoc 命令。")
        print("请确保您已安装 Pandoc 并且其路径已添加到系统环境变量中。")
        return

    print("开始修正文件格式并转换为Word文档...")
    print("-" * 30)

    for md_filename in files_to_process:
        md_path = os.path.join(md_dir, md_filename)
        
        # 1. 修正文件
        review_and_correct_file(md_path)

        # 2. 转换为Word文档
        docx_filename = os.path.splitext(md_filename.replace('_annotated', ''))[0] + ".docx"
        docx_path = os.path.join(md_dir, docx_filename)
        
        if not os.path.exists(md_path):
            print(f"警告：未找到文件 '{md_path}'，已跳过。")
            continue

        try:
            print(f"正在转换: {md_filename} ...")
            subprocess.run(
                ["pandoc", "-f", "gfm", md_path, "-o", docx_path],
                check=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            print(f"  -> 已成功生成: {docx_filename}")
        except subprocess.CalledProcessError as e:
            print(f"  -> 转换失败: {md_filename}")
            print(f"     错误信息: {e.stderr}")

    print("-" * 30)
    print("所有转换任务已执行完毕。")

if __name__ == "__main__":
    convert_md_to_docx()
