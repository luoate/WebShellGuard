import pandas as pd


def count_labels(csv_file):
    # 读取 CSV 文件
    df = pd.read_csv(csv_file)

    # 确保 'label' 列存在
    if 'label' not in df.columns:
        print("CSV 文件中没有 'label' 列")
        return

    # 统计 'webshell' 和 'normal' 的数量
    webshell_count = (df['label'] == 'webshell').sum()
    normal_count = (df['label'] == 'normal').sum()

    print(f"Webshell 数量: {webshell_count}")
    print(f"Normal 数量: {normal_count}")


# 示例调用
csv_file_path = "phpProcessor/dataset/test2.csv"  # 替换为你的 CSV 文件路径
count_labels(csv_file_path)

# 读取 CSV 文件的前 5 行
df_head = pd.read_csv(csv_file_path, nrows=5)

# 打印 DataFrame
print(df_head)