import re
import os

# --- 配置 ---

# 需要验证的Markdown文件
MARKDOWN_FILE_PATH = '粗剪文档（按时间戳）/粗剪文稿-澳门官也街/粗剪文稿-澳门IP-官也街创业.md'

# 原文素材文件列表
SOURCE_FILES = [
    '输入文件（录音/官也街/00_03-05_34 _ 10月27日.txt',
    '输入文件（录音/官也街/00_21-05_30 _ A0013.txt',
    '输入文件（录音/官也街/01_31-27_53 _ A0014.txt'
]

# 生成的带有高亮标记的输出文件
OUTPUT_FILE_PATH = '粗剪文档（按时间戳）/粗剪文稿-澳门官也街/粗剪文稿-澳门IP-官也街创业_validation.md'


def load_source_content(files):
    """加载所有原文素材文件内容到一个字符串中"""
    content = ""
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content += f.read()
        except FileNotFoundError:
            print(f"警告: 原文素材文件未找到: {file_path}")
    return content

def clean_content_for_search(text):
    """清理从Markdown中提取的内容，以便在原文中搜索"""
    # 移除HTML/XML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除Markdown标题标记
    text = re.sub(r'##\s*', '', text)
    # 移除特殊占位符和分隔符
    text = text.replace('|', '')
    text = text.replace('（...）', '')
    # 移除括号
    text = text.replace('(', '').replace(')', '')
    # 移除全角括号
    text = text.replace('（', '').replace('）', '')
    # 移除字符串首位的空格
    return text.strip()

def validate_markdown_file(markdown_path, source_text, output_path):
    """
    验证Markdown文件，并将无法溯源的内容标记为红色。
    """
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: Markdown文件未找到: {markdown_path}")
        return

    output_lines = []
    # 正则表达式，用于捕获'内容:'后面的所有文本
    content_regex = re.compile(r"(\*\*\s*内容\s*\*\*:)(.*)", re.IGNORECASE)

    for line in markdown_lines:
        match = content_regex.match(line.strip())
        if match:
            original_content_part = match.group(2).strip()
            
            # 如果内容部分为空，则直接保留原样
            if not original_content_part:
                output_lines.append(line)
                continue

            cleaned_content = clean_content_for_search(original_content_part)

            # 在原文中搜索清理后的内容
            if cleaned_content not in source_text:
                # 如果找不到，将这部分内容标记为红色
                new_line = f'{match.group(1)} <font color="red">{original_content_part}</font>\n'
                output_lines.append(new_line)
                print(f"【未找到原文】: {cleaned_content}")
            else:
                # 如果找到了，保留原样
                output_lines.append(line)
        else:
            # 如果不是'内容:'行，直接保留
            output_lines.append(line)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    print(f"\n验证完成！结果已保存到: {output_path}")


def main():
    print("开始加载原文素材...")
    source_text = load_source_content(SOURCE_FILES)
    if not source_text:
        print("错误: 未能加载任何原文素材，脚本终止。")
        return
    
    print("开始验证Markdown文件...")
    validate_markdown_file(MARKDOWN_FILE_PATH, source_text, OUTPUT_FILE_PATH)

if __name__ == '__main__':
    main()
