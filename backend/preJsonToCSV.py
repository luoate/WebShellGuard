import os
import json
import pandas as pd

# 文件路径
input_dir = "phpProcessor/files/sequence/pre_test"  # 解压后的文件夹
output_file = "phpProcessor/files/sequence/pre_test.csv"  # 目标 CSV 文件

# 读取所有 JSON 文件
data_list = []
for file_name in os.listdir(input_dir):
    if file_name.endswith(".json"):  # 只处理 JSON 文件
        file_path = os.path.join(input_dir, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)  # 读取 JSON
                data_list.append(data)  # 存入列表
        except Exception as e:
            print(f"跳过 {file_name}: {e}")

# 转换为 DataFrame
df = pd.DataFrame(data_list)

# 保存为 CSV
df.to_csv(output_file, index=False)
print(f"CSV 文件已保存至 {output_file}")


df = pd.read_csv(output_file)
print(df.head())