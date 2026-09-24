import os
import re

# 解析 YARA 规则，确保 { } 结构完整
def extract_web_rules_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    rules = []
    inside_rule = False
    brace_count = 0
    rule_lines = []
    rule_name = None
    rule_pattern = re.compile(r'(?i)^\s*rule\s+([a-zA-Z0-9_]+web[a-zA-Z0-9_]*)\s*\{')

    for line in lines:
        if not inside_rule:
            match = rule_pattern.search(line)
            if match:
                inside_rule = True
                brace_count = 1
                rule_name = match.group(1)
                rule_lines.append(line.strip())
            continue

        if inside_rule:
            rule_lines.append(line.strip())
            brace_count += line.count('{')
            brace_count -= line.count('}')

            if brace_count == 0:
                rules.append(('\n'.join(rule_lines), rule_name))
                inside_rule = False
                rule_lines = []
                rule_name = None

    return rules if rules else None

# 递归遍历文件夹，获取所有文件中的 web 规则
def process_yar_files(directory):
    web_rules = {}

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.yar'):
                file_path = os.path.join(root, filename)
                try:
                    rules = extract_web_rules_from_file(file_path)
                    if rules:
                        for rule, rule_name in rules:
                            if rule_name.lower() not in web_rules:
                                web_rules[rule_name.lower()] = rule
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")

    return list(web_rules.values())

# 将提取的规则输出到一个新的 yar 文件
def write_to_yar_file(output_file, web_rules):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('// Extracted rules with "web" in their name\n\n')
        for rule in web_rules:
            f.write(rule + '\n')

# 定义输入和输出文件夹路径
input_directory = 'yara'  # 修改为实际输入文件夹路径
output_file = 'yara/yara1/filtered_rules.yar'  # 修改为实际输出文件路径

# 获取所有包含 web 的规则
web_rules = process_yar_files(input_directory)

# 输出到文件
write_to_yar_file(output_file, web_rules)

print(f'Filtered rules have been written to {output_file}')
