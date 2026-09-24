import json
import os

def check_file_content(file_path):
    # 定义目标 JSON 数据结构
    # target_structure = {"tokenSequence": [], "stringSequence": [], "tags": []}

    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()

        # 尝试将文件内容解析为 JSON
        data = json.loads(file_content)

        # 检查数据是否匹配目标结构
        if data.get("tokenSequence") == [] and data.get("stringSequence") == []:
            print(f"文件 {file_path} 的内容与目标结构匹配。")
            return True
        else:
            # print(f"文件 {file_path} 的内容不匹配。")
            return False

    except json.JSONDecodeError:
        print(f"文件 {file_path} 不是有效的 JSON 格式。")
        return False
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到，请检查路径。")
        return False

def check_directory(directory_path):
    if not os.path.isdir(directory_path):
        print(f"路径 {directory_path} 不是一个有效的目录。")
        return

    print(f"正在检查目录 {directory_path} 中的文件...")
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            check_file_content(file_path)

# 测试函数
if __name__ == "__main__":
    directory_path = "phpProcessor/files/sequence/pre_test/"
    check_directory(directory_path)