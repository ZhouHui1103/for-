import re
import sys
import os
from difflib import SequenceMatcher

def load_sources(source_files):
    """
    Loads all source text files and parses them to extract text blocks with timestamps.
    Returns a list of {'text': str, 'timestamp': str, 'source': str}.
    """
    sources = []
    for file_path in source_files:
        if not os.path.exists(file_path):
            print(f"警告: 源文件不存在 {file_path}, 已跳过。")
            continue
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = re.finditer(r"说话人 1 (\d{2}:\d{2})\s*\n([\s\S]*?)(?=\n\n说话人 1|\Z)", content)
            for match in matches:
                timestamp = match.group(1)
                text = match.group(2).replace('\n', ' ').strip()
                # Further cleaning of source text for better comparison
                text = re.sub(r'\s+', ' ', text)
                sources.append({
                    'text': text,
                    'timestamp': timestamp,
                    'source': os.path.basename(file_path)
                })
    return sources

def find_best_source_block(paragraph, sources):
    """Finds the best matching source text block for a given paragraph."""
    best_ratio = 0.4  # Lowered threshold for finding a relevant block
    best_match = None
    # Clean the paragraph for a better comparison score
    clean_paragraph = re.sub(r'[\(\)（）。？！，]', '', paragraph)

    for source in sources:
        clean_source = re.sub(r'[\(\)（）。？！，]', '', source['text'])
        s = SequenceMatcher(None, clean_paragraph, clean_source)
        if s.ratio() > best_ratio:
            best_ratio = s.ratio()
            best_match = source
    return best_match

def diff_and_annotate(md_path, sources):
    """
    Performs a diff between the markdown and source texts and annotates the differences.
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    parts = original_content.split('### **正文**')
    if len(parts) < 2:
        return

    header = parts[0]
    body = parts[1]

    # Clean the body of all previous, incorrect annotations
    body = re.sub(r'\(\(\(\((.*?)\)\)\)\)', r'\1', body)
    body = re.sub(r'<sup.*?/sup>', '', body)
    body = re.sub(r'</?font.*?>|</?mark>', '', body)
    body = body.replace('**', '')

    paragraphs = [p.strip() for p in body.split('\n') if p.strip()]
    
    new_body_content = []

    for para in paragraphs:
        if not para:
            continue
        
        # Handle structural elements like (开场...)
        if para.startswith('(') and para.endswith(')'):
             new_body_content.append(f"({para.strip('()')})")
             continue

        best_source = find_best_source_block(para, sources)

        if not best_source:
            new_body_content.append(f"({para})")
            continue

        s = SequenceMatcher(None, para, best_source['text'], autojunk=False)
        output_para = ""
        
        for tag, j1, j2, i1, i2 in s.get_opcodes():
            md_text = para[j1:j2]
            source_text = best_source['text'][i1:i2]

            if tag == 'equal':
                output_para += md_text
            elif tag == 'insert':
                if md_text.strip():
                    output_para += f"({md_text})"
            elif tag == 'replace':
                if md_text.strip():
                     output_para += f"({md_text})"
        
        output_para += f" <sup>({best_source['source']}, {best_source['timestamp']})</sup>"
        new_body_content.append(output_para)

    new_filepath = md_path.replace('_annotated.md', '_final_annotated.md')
    final_content = header + "### **正文**\n\n" + "\n\n".join(new_body_content)

    with open(new_filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"已生成最终标注文件: {new_filepath}")

if __name__ == "__main__":
    source_txt_files = [
        os.path.join("输入文件（录音", "赖琴2", "赖琴录音素材1.txt"),
        os.path.join("输入文件（录音", "赖琴2", "赖琴录音素材2 .txt"),
        os.path.join("输入文件（录音", "赖琴2", "赖琴录音素材3.txt"),
    ]
    
    print("正在加载源录音文稿...")
    sources = load_sources(source_txt_files)
    
    markdown_files = sys.argv[1:]
    for md_file in markdown_files:
        print(f"正在处理: {md_file}")
        diff_and_annotate(md_file, sources)

    print("所有文件处理完毕。")
