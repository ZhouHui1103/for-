import re
import sys
import os

LINKING_WORDS = ['因为', '所以', '但是', '而且', '那么', '不过', '同时', '另外', '那', '但', '然后']

def parse_rough_cut(file_path):
    """
    Parses the rough cut markdown file to extract a structured representation.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    header, body = content.split('### **正文**', 1)
    header += '### **正文**\n'
    
    structure = []
    
    body_parts = body.split('\n\n')
    
    for part in body_parts:
        part = part.strip()
        if not part:
            continue
        if part.startswith('(') and part.endswith(')'):
            structure.append({'type': 'subheader', 'content': part})
        elif part.startswith('**素材**'):
            match = re.search(r"\*\*素材\*\*: (.*?)\n\*\*时间\*\*: (.*?)\n\*\*内容\*\*: (.*)", part, re.DOTALL)
            if match:
                 structure.append({
                    'type': 'snippet',
                    'source': match.group(1).strip(),
                    'timestamp': match.group(2).strip(),
                    'content': match.group(3).strip()
                })

    return header, structure


def generate_annotated_text(structure):
    """
    Generates the final annotated text body from the structured data.
    """
    output_lines = []
    current_paragraph = ""

    for i, block in enumerate(structure):
        if block['type'] == 'subheader':
            if current_paragraph:
                output_lines.append(current_paragraph)
            output_lines.append(f"\n{block['content']}")
            current_paragraph = ""
        
        elif block['type'] == 'snippet':
            content = block['content']
            source = block['source']
            timestamp = block['timestamp']
            
            processed_content = content
            prefix = ""
            
            for word in LINKING_WORDS:
                if content.startswith(word):
                    prefix = f"({word})"
                    processed_content = content[len(word):].lstrip()
                    break
            
            processed_content = f"{processed_content} <sup>({source}, {timestamp})</sup>"
            
            if not current_paragraph:
                current_paragraph += "\n"

            if current_paragraph.strip() and not current_paragraph.strip().endswith(('。','？','！', ' ')):
                 current_paragraph += " "
            
            current_paragraph += prefix + processed_content

    if current_paragraph:
        output_lines.append(current_paragraph)
        
    return "".join(output_lines)


def process_file(input_path, output_dir):
    """
    Reads an input file, processes it, and writes to an output file.
    """
    print(f"--> 正在处理: {input_path}")
    header, structure = parse_rough_cut(input_path)
    
    body_text = generate_annotated_text(structure)
    
    final_content = header + body_text
    
    base_name = os.path.basename(input_path)
    output_name = base_name.replace('粗剪文稿', '生成式文稿')
    output_path = os.path.join(output_dir, output_name)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    print(f"    --> 已生成: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python generate_final_script.py <input_file1> <input_file2> ...")
        sys.exit(1)

    input_files = sys.argv[1:]
    output_directory = os.path.join("粗剪文稿（生成式）", "赖琴")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for file_path in input_files:
        process_file(file_path, output_directory)

    print("\n所有文件生成完毕。")
