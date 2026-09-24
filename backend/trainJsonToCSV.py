import os
import json
import pandas as pd

# 定义文件夹路径
a = 'test'
root = f'phpProcessor/files/sequence/{a}/'
webshell_folder = root + 'webshell'
normal_folder = root + 'normal'

# 创建一个空的列表来存储所有数据
data = []

# 读取webshell文件夹中的JSON文件
for filename in os.listdir(webshell_folder):
    if filename.endswith('.json'):
        file_path = os.path.join(webshell_folder, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            json_data['label'] = 'webshell'  # 给webshell文件加一个类别标签
            data.append(json_data)

# 读取normal文件夹中的JSON文件
for filename in os.listdir(normal_folder):
    if filename.endswith('.json'):
        file_path = os.path.join(normal_folder, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            json_data['label'] = 'normal'  # 给normal文件加一个类别标签
            data.append(json_data)

# 将数据转换为DataFrame
df = pd.DataFrame(data)

# 将DataFrame写入CSV文件
df.to_csv(root + f'{a}.csv', index=False, encoding='utf-8')

print("JSON文件已成功合并为CSV文件。")
