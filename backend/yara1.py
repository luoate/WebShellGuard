import yara

def load_yar_rule(yar_file):
    try:
        # 加载YARA规则
        rules = yara.compile(filepath=yar_file)
        return rules
    except Exception as e:
        print(f"加载YARA规则失败: {e}")
        return None

def analyze_file(rules, target_file):
    try:
        # 使用规则分析目标文件
        matches = rules.match(target_file)
        if matches:
            print(f"检测到匹配: {matches}")
            for m in matches:
                # source_file = rule_mapping.get(m.rule, "未知来源")
                # if source_file != "未知来源":
                #     malware_type = source_file.split("/")[9]
                #     types.append(malware_type)
                # else:
                #     malware_type = "未知"
                # print(f"  ├─ 病毒种类：{malware_type}")
                print(f"  ├─ 规则名称：{m.rule}")
                # print(f"  ├─ 来源文件：{source_file}")
                print(f"  ├─ 规则标签：{m.tags}")
                print(f"  └─ 元数据：{m.meta}\n")
        else:
            print("没有匹配的规则")
    except Exception as e:
        print(f"分析文件时出错: {e}")

if __name__ == "__main__":
    yar_file = "yara/yara1/filtered_rules.yar"  # YAR文件路径
    target_file = r"C:\Users\lowi\Downloads\dataset\webshell\dest\black_0396bb6a40b74c40fb260aa80525c86f.php"  # 需要分析的文件路径

    # 加载YARA规则
    rules = load_yar_rule(yar_file)

    if rules:
        # 分析目标文件
        analyze_file(rules, target_file)
