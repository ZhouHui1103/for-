import re
import os

# --- 配置 ---
# 要处理的生成式文稿及其对应的输出文件名
GEN_FILES_TO_PROCESS = {
    '粗剪文稿（生成式）/赖琴/生成式文稿-女性创业时代.md': '粗剪文稿（生成式）/赖琴/生成式文稿-女性创业时代_annotated.md',
    '粗剪文稿（生成式）/赖琴/生成式文稿-凭运气赚的钱.md': '粗剪文稿（生成式）/赖琴/生成式文稿-凭运气赚的钱_annotated.md',
    '粗剪文稿（生成式）/赖琴/生成式文稿-少年得志的陷阱.md': '粗剪文稿（生成式）/赖琴/生成式文稿-少年得志的陷阱_annotated.md',
    '粗剪文稿（生成式）/赖琴/生成式文稿-小弟都上市了.md': '粗剪文稿（生成式）/赖琴/生成式文稿-小弟都上市了_annotated.md'
}

# 原文素材文件列表
SOURCE_FILES = [
    '输入文件（录音/赖琴2/赖琴录音素材1.txt',
    '输入文件（录音/赖琴2/赖琴录音素材2 .txt',
    '输入文件（录音/赖琴2/赖琴录音素材3.txt'
]

def parse_source_files(file_paths):
    """
    解析所有源文件，创建一个包含（文本片段，时间戳，文件名）的列表。
    """
    source_data = []
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 提取文件名
                file_name = os.path.basename(file_path)
                
                # 使用正则表达式查找所有说话人和时间戳
                # (说话人 \d \d{2}:\d{2})\s*\n([\s\S]*?)
                # 匹配模式：(说话人 1 00:00)\n(text block)
                # 使用 re.split 来根据 "说话人..." 分割文本
                parts = re.split(r'(说话人 \d \d{2}:\d{2})', content)
                
                # "文字记录:" 之后的部分是第一个文本块
                initial_split = parts[0].split('文字记录:')
                current_ts = "00:00"
                if len(initial_split) > 1:
                    text_block = initial_split[1].strip()
                    if text_block:
                        source_data.append({'text': text_block, 'ts': current_ts, 'file': file_name})

                # 处理其余部分
                for i in range(1, len(parts), 2):
                    ts_marker = parts[i]
                    text_block = parts[i+1].strip()
                    # 从 "说话人 1 01:13" 中提取 "01:13"
                    match = re.search(r'(\d{2}:\d{2})', ts_marker)
                    if match:
                        current_ts = match.group(1)
                    if text_block:
                        source_data.append({'text': text_block, 'ts': current_ts, 'file': file_name})

        except FileNotFoundError:
            print(f"警告: 原文素材文件未找到: {file_path}")
            
    return source_data

def find_match_in_source(text, source_data):
    """
    在源数据中查找文本片段，返回最佳匹配项（时间戳和文件名）。
    """
    text_to_find = text.strip()
    if not text_to_find:
        return None
        
    for entry in source_data:
        if text_to_find in entry['text']:
            return {'ts': entry['ts'], 'file': entry['file']}
    return None

def process_generative_file(gen_file_path, output_file_path, source_data):
    """
    处理单个生成式文件，生成带标注的版本。
    """
    try:
        with open(gen_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误: 生成式文件未找到: {gen_file_path}")
        return

    output_content = []
    in_body = False
    for line in lines:
        if line.strip() == '### **正文**':
            in_body = True
            output_content.append(line)
            continue
        
        if not in_body or not line.strip() or line.strip().startswith('('):
            output_content.append(line)
            continue

        # 处理正文内容
        # 使用正则表达式按标点符号分割，同时保留标点符号
        fragments = re.split(r'([。，、？|])', line)
        new_line = ""
        for i in range(0, len(fragments) - 1, 2):
            text_part = fragments[i]
            punctuation = fragments[i+1]
            
            # 清理文本以进行搜索
            clean_text = re.sub(r'<[^>]+>', '', text_part).strip()
            
            match_info = find_match_in_source(clean_text, source_data)
            
            if match_info:
                # 找到匹配，添加时间和素材戳
                annotation = f" <sup>({match_info['file']}, {match_info['ts']})</sup>"
                new_line += text_part + annotation + punctuation
            else:
                # 未找到匹配，标记为红色
                if clean_text: # 只标记有内容的片段
                    new_line += f'<font color="red">{text_part}</font>{punctuation}'
                else:
                    new_line += text_part + punctuation
        
        # 处理行尾无标点的情况
        if len(fragments) % 2 == 1:
             text_part = fragments[-1]
             clean_text = re.sub(r'<[^>]+>', '', text_part).strip()
             match_info = find_match_in_source(clean_text, source_data)
             if match_info:
                annotation = f" <sup>({match_info['file']}, {match_info['ts']})</sup>"
                new_line += text_part.strip() + annotation + '\n'
             else:
                if clean_text:
                    new_line += f'<font color="red">{text_part.strip()}</font>\n'
                else:
                    new_line += text_part

        output_content.append(new_line)

    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.writelines(output_content)
    print(f"标注完成: {output_file_path}")

def main():
    print("开始解析原文素材...")
    source_data = parse_source_files(SOURCE_FILES)
    if not source_data:
        print("错误: 未能加载或解析任何原文素材，脚本终止。")
        return
    
    print(f"原文素材解析完成，共找到 {len(source_data)} 个带时间戳的文本块。")

    for gen_file, out_file in GEN_FILES_TO_PROCESS.items():
        print(f"\n正在处理: {gen_file}...")
        process_generative_file(gen_file, out_file, source_data)
        
    print("\n所有文件处理完毕。")

if __name__ == '__main__':
    main()
