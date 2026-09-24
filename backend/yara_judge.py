#!/usr/bin/env python3
import os
import yara
import sys
import re
import warnings

# ==================== 硬编码配置区域 ====================
TARGET_DIR = "yara/yara1"  # YARA规则源目录
SCAN_TARGET = r"C:\Users\lowi\Downloads\dataset\webshell\dest\black_2da34b14c430db432fa254c8d0cbbacb.php"  # 要扫描的目标文件/目录
INDEX_NAME = "yara/index.yar"  # 生成的索引文件名
# ======================================================

def generate_yara_index():
    """生成YARA索引文件，仅包含名称包含'web'的规则"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(script_dir, INDEX_NAME)

    if not os.path.exists(TARGET_DIR):
        print(f"[错误] 规则目录不存在：{TARGET_DIR}")
        sys.exit(1)

    rule_contents = []

    for root, dirs, files in os.walk(TARGET_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in ('.yar', '.yara'):
                full_path = os.path.join(root, file)

                try:
                    # 语法检查
                    yara.compile(filepath=full_path)

                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        matches = re.findall(r'rule\s+([\w_-]+)', content)
                        if any('web' in rule_name.lower() for rule_name in matches):
                            rule_contents.append(content)
                except yara.SyntaxError as e:
                    print(f"[跳过] 语法错误文件：{full_path} \n\t错误详情：{e}")
                except yara.Error as e:
                    print(f"[跳过] 规则错误文件：{full_path} \n\t错误类型：{type(e).__name__}")
                except Exception as e:
                    print(f"[跳过] 异常文件：{full_path} \n\t错误原因：{str(e)}")

    if not rule_contents:
        print("[错误] 未找到符合条件的YARA规则")
        sys.exit(1)

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(rule_contents))

    print(f"[成功] 生成包含 {len(rule_contents)} 条规则的索引文件：{index_path}")
    return index_path
#通过字典找出出现次数最多的元素
def most_frequent(lst):
    counts = {}
    for item in lst:
        counts[item] = counts.get(item, 0) + 1
    return max(counts, key=counts.get)

def compile_rules(rule_path):
    """编译YARA规则（兼容旧版本）"""
    try:
        return yara.compile(filepath=rule_path)
    except yara.SyntaxError as e:
        print(f"[错误] 规则语法错误：{e}")
        sys.exit(1)
    except Exception as e:
        print(f"[错误] 规则编译失败：{e}")
        sys.exit(1)

def scan_target(rules, target_path):
    """执行扫描操作"""
    if not os.path.exists(target_path):
        print(f"[错误] 扫描目标不存在：{target_path}")
        sys.exit(1)

    def scan_file(file_path):
        try:
            with warnings.catch_warnings():  # 新增：捕获警告
                warnings.simplefilter("ignore", RuntimeWarning)
                return rules.match(file_path)
        except Exception as e:
            print(f"[警告] 扫描失败 {file_path}: {e}")
            return None

    if os.path.isfile(target_path):
        print(f"\n扫描文件：{target_path}")
        return {target_path: scan_file(target_path)}

    results = {}
    print(f"\n扫描目录：{target_path}")
    for root, _, files in os.walk(target_path):
        for file in files:
            file_path = os.path.join(root, file)
            results[file_path] = scan_file(file_path)
    return results

def print_results(results, rule_mapping):
    """打印带规则来源的扫描结果"""
    total_files = len(results)
    matches = sum(1 for v in results.values() if v)

    print(f"\n{'=' * 40}")
    print(f"扫描完成！共处理 {total_files} 个文件")
    print(f"发现匹配文件：{matches} 个")
    print(f"{'=' * 40}\n")

    for path, match in results.items():
        if match:
            print(f"[发现] {path}")
            #存储病毒种类的列表
            # types = []
            for m in match:
                source_file = rule_mapping.get(m.rule, "未知来源")
                # if source_file != "未知来源":
                #     malware_type = source_file.split("/")[9]
                #     types.append(malware_type)
                # else:
                #     malware_type = "未知"
                # print(f"  ├─ 病毒种类：{malware_type}")
                print(f"  ├─ 规则名称：{m.rule}")
                print(f"  ├─ 来源文件：{source_file}")
                print(f"  ├─ 规则标签：{m.tags}")
                print(f"  └─ 元数据：{m.meta}\n")
            #统计出现最多次的病毒种类
            # if types:
            #     print(f"病毒种类:{most_frequent(types)}")
            # else:
            #     print(f"病毒种类:未知")

def main():
    # 阶段1：生成索引文件和规则映射
    rule_file, rule_mapping = generate_yara_index()

    # 阶段2：编译规则
    print("\n正在编译YARA规则...")
    rules = compile_rules(rule_file)

    # 阶段3：执行扫描
    print("\n开始安全扫描...")
    scan_results = scan_target(rules, SCAN_TARGET)

    # 显示结果
    print_results(scan_results, rule_mapping)

if __name__ == "__main__":
    main()