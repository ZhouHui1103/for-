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
            # Find all text blocks associated with '说话人 1'
            matches = re.finditer(r"说话人 1 (\d{2}:\d{2})\s*\n([\s\S]*?)(?=\n\n说话人 1|\Z)", content)
            for match in matches:
                timestamp = match.group(1)
                text = match.group(2).replace('\n', ' ').replace('  ', ' ').strip()
                sources.append({
                    'text': text,
                    'timestamp': timestamp,
                    'source': os.path.basename(file_path)
                })
    return sources

def find_best_match(sentence, sources):
    """
    Finds the best matching source text for a given sentence.
    """
    best_ratio = 0.7  # Minimum similarity threshold
    best_match = None
    
    # Normalize sentence for better matching
    clean_sentence = sentence.strip()

    for source in sources:
        # Use SequenceMatcher to find the best block match ratio
        s = SequenceMatcher(None, clean_sentence, source['text'])
        ratio = s.ratio()
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = source
            
    return best_match

def re_annotate_markdown(md_path, sources):
    """
    Re-annotates a markdown file by comparing its content against the sources.
    Generated text is wrapped in parentheses, original text gets a timestamp.
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # Preserve header and split body
    parts = original_content.split('### **正文**')
    if len(parts) < 2:
        return

    header = parts[0]
    body = parts[1]

    # Clean up the body from old annotations to get raw text paragraphs
    body = re.sub(r'\(\(\(\(.*\)\)\)\)', '', body) # Remove (((...)))
    body = re.sub(r'<sup.*?/sup>', '', body) # Remove old sup tags
    body = body.replace('**', '') # Remove bold markers

    paragraphs = [p.strip() for p in body.split('\n') if p.strip()]
    
    new_body_content = []

    for para in paragraphs:
        # Simple sentence splitting
        sentences = re.split(r'([。？！])', para)
        sentences = [s for s in sentences if s] # filter out empty strings
        
        output_line = ""
        # Process sentence by sentence
        i = 0
        while i < len(sentences):
            # Combine sentence and its punctuation
            sent = sentences[i]
            if (i + 1) < len(sentences) and sentences[i+1] in '。？！':
                sent += sentences[i+1]
                i += 2
            else:
                i += 1
            
            sent = sent.strip()
            if not sent:
                continue

            match = find_best_match(sent, sources)
            if match:
                # Original text found
                output_line += f"{sent} <sup>({match['source']}, {match['timestamp']})</sup>"
            else:
                # Generated text
                output_line += f"({sent})"
        
        new_body_content.append(output_line)

    # --- Create the new file ---
    new_filepath = md_path.replace('_annotated.md', '_reannotated.md')
    final_content = header + "### **正文**\n\n" + "\n\n".join(new_body_content)

    with open(new_filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"已生成新的标注文件: {new_filepath}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python re_annotate.py <markdown_file1> ...")
        sys.exit(1)
        
    source_txt_files = [
        os.path.join("输入文件（录音", "赖琴2", "赖琴录音素材1.txt"),
        os.path.join("输入文件（录音", "赖琴2", "赖琴录音素材2 .txt"),
        os.path.join("输入文件（录音", "赖琴2", "赖琴录音素材3.txt"),
    ]
    
    print("正在加载源录音文稿...")
    sources = load_sources(source_txt_files)
    print(f"加载了 {len(sources)} 个原文片段。")
    print("-" * 30)

    markdown_files = sys.argv[1:]
    for md_file in markdown_files:
        print(f"正在处理: {md_file}")
        re_annotate_markdown(md_file, sources)

    print("-" * 30)
    print("所有文件处理完毕。")
