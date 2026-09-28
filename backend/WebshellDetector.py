import ast
import json
import os

import torch
from sklearn.metrics import accuracy_score
import pandas as pd
from transformers import RobertaTokenizer

from model import BERTClassifier
from util.config import conf

class WebshellDetector:
    def __init__(self, model_path = './model/train_3_good.pth', tokenizer = RobertaTokenizer.from_pretrained("./codebert"), device=None):
        """
        Initialize WebshellDetector with model and tokenizer.
        :param model_path: Path to the trained model
        :param tokenizer_path: Path to the tokenizer
        :param device: Device to use for computation (e.g., 'cuda' or 'cpu')
        """
        self.device = device if device else conf.device
        self.tokenizer = tokenizer
        self.model = BERTClassifier().to(self.device)
        self.load_model(model_path)

    def load_model(self, model_path):
        """
        Load the pre-trained model from the specified path.
        :param model_path: Path to the model weights file
        """
        try:
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            print(f"Model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            exit(1)

    def predict(self, file_path = None, json_str = None, threshold=0.6):
        """
        Predict if a single file is a webshell.
        :param file_path: Path to the file
        :param threshold: Classification threshold (default: 0.5)
        :return: Tuple (is_webshell, probability)
        """
        if json_str is None:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as rf:
                    raw_data = json.load(rf)
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                return None, None
        else:
            raw_data = json.loads(json_str)

        data = raw_data["tokenSequence"] + ["</s>"] + raw_data["stringSequence"]
        inputs = self.tokenizer.encode_plus(
            data,
            None,
            add_special_tokens=True,
            max_length=conf.seq_len,
            padding='max_length',
            return_token_type_ids=True,
            truncation=True,
        )

        ids = torch.tensor([inputs['input_ids']], dtype=torch.long).to(self.device)
        mask = torch.tensor([inputs['attention_mask']], dtype=torch.long).to(self.device)
        token_type_ids = torch.tensor([inputs["token_type_ids"]], dtype=torch.long).to(self.device)

        self.model.eval()
        with torch.no_grad():
            logits = self.model(ids, mask, token_type_ids)
            prob = torch.sigmoid(logits).item()  # Convert to probability
            is_webshell = prob > threshold

        return is_webshell, prob
    def safe_json_parse(self, text, default=[]):
        try:
            return json.loads(text)
        except:
            print(f"Warning: Failed to parse JSON: {text[:50]}...")
            return default

    def predict_from_csv(self, file_path=None, output_txt="websahellresults.txt", threshold=0.6):
        """
        预测 CSV 文件中的样本是否为 webshell，并将结果保存到 TXT 文件，同时计算准确率。
        :param file_path: 包含 tokenSequence, stringSequence, tags, label 列的 CSV 文件路径
        :param output_txt: 预测结果保存的 TXT 文件路径（默认：results.txt）
        :param threshold: 分类阈值（默认：0.6）
        :return: 预测结果列表 [(is_webshell, probability, label), ...] 和准确率
        """
        # 检查 tokenizer 是否初始化
        if self.tokenizer is None:
            print("错误：tokenizer 未初始化。请检查类初始化代码或配置。")
            return [], 0.0

        if file_path is None:
            print("错误：未提供文件路径")
            return [], 0.0

        try:
            # 使用 pandas 读取 CSV 文件
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
            
            # 验证所需列是否存在
            required_columns = ['tokenSequence', 'stringSequence', 'tags', 'label']
            if not all(col in df.columns for col in required_columns):
                print(f"错误：CSV 文件必须包含以下列：{required_columns}")
                return [], 0.0

            results = []
            predictions = []
            true_labels = []
            self.model.eval()

            # 遍历 DataFrame 的每一行
            for index, row in df.iterrows():
                try:
                    # 解析 tokenSequence 和 stringSequence
                    token_sequence = ast.literal_eval(row['tokenSequence']) if row['tokenSequence'] else []
                    string_sequence = ast.literal_eval(row['stringSequence']) if row['stringSequence'] else []
                    
                    # 组合序列
                    data = token_sequence + ["</s>"] + string_sequence

                    # 编码输入
                    inputs = self.tokenizer.encode_plus(
                        data,
                        None,
                        add_special_tokens=True,
                        max_length=conf.seq_len,
                        padding='max_length',
                        return_token_type_ids=True,
                        truncation=True,
                    )

                    # 准备张量
                    ids = torch.tensor([inputs['input_ids']], dtype=torch.long).to(self.device)
                    mask = torch.tensor([inputs['attention_mask']], dtype=torch.long).to(self.device)
                    token_type_ids = torch.tensor([inputs["token_type_ids"]], dtype=torch.long).to(self.device)

                    # 执行预测
                    with torch.no_grad():
                        logits = self.model(ids, mask, token_type_ids)
                        prob = torch.sigmoid(logits).item()  # 转换为概率
                        is_webshell = prob > threshold

                    # 转换标签为二元形式以计算准确率
                    true_label = 1 if row['label'].lower() == 'webshell' else 0
                    pred_label = 1 if is_webshell else 0

                    # 保存结果
                    results.append((is_webshell, prob, row['label']))
                    predictions.append(pred_label)
                    true_labels.append(true_label)

                except Exception as e:
                    print(f"处理第 {index} 行时出错：{e}")
                    continue

            # 计算准确率
            if predictions and true_labels:
                accuracy = accuracy_score(true_labels, predictions)
            else:
                accuracy = 0.0

            # 将结果保存到 TXT 文件
            try:
                with open(output_txt, 'w', encoding='utf-8') as f:
                    f.write("预测结果：\n")
                    for idx, (is_webshell, prob, label) in enumerate(results):
                        f.write(f"样本 {idx}: 是否为 webshell: {is_webshell}, 概率: {prob:.4f}, 实际标签: {label}\n")
                    f.write(f"\n总样本数: {len(results)}\n")
                    f.write(f"准确率: {accuracy:.4f}\n")
                print(f"结果已保存到 {output_txt}")
            except Exception as e:
                print(f"保存结果到 {output_txt} 时出错：{e}")

            return results, accuracy

        except Exception as e:
            print(f"读取 CSV 文件 {file_path} 时出错：{e}")
            return [], 0.0

    def predict_directory(self, dir_path, threshold=0.5):
        """
        Predict if files in the directory are webshells.
        :param dir_path: Path to the directory
        :param threshold: Classification threshold (default: 0.5)
        """
        if not os.path.isdir(dir_path):
            print(f"Error: {dir_path} is not a directory.")
            return

        json_files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
        if not json_files:
            print(f"No JSON files found in {dir_path}.")
            return

        print(f"Found {len(json_files)} JSON files in {dir_path}. Starting prediction...")
        for file_name in json_files:
            file_path = os.path.join(dir_path, file_name)
            is_webshell, probability = self.predict(file_path, threshold)
            if is_webshell is not None:
                print(f"File: {file_path}")
                print(f"Probability of being a webshell: {probability:.4f}")
                print(f"Prediction: {'Webshell' if is_webshell else 'Normal'}")
                print("-" * 50)
            else:
                print(f"Skipping {file_path} due to processing error.")

if __name__ == "__main__":
    model_path = 'model/train_3.pth'
    detector = WebshellDetector(model_path)

    # Specify the file or directory to predict
    file_to_predict = None  # Example: 'path_to_your_file.json'
    dir_to_predict = 'phpProcessor/files/sequence/test/normal'  # Example: 'your_directory/'
    threshold = 0.5  # Classification threshold, can adjust

    # Prediction logic
    if file_to_predict and dir_to_predict:
        print("Error: Please specify either a file or a directory, not both.")
    elif file_to_predict:
        # Predict a single file
        is_webshell, probability = detector.predict(file_path=file_to_predict, threshold=threshold)
        if is_webshell is not None:
            print(f"File: {file_to_predict}")
            print(f"Probability of being a webshell: {probability:.4f}")
            print(f"Prediction: {'Webshell' if is_webshell else 'Normal'}")
        else:
            print("Prediction failed.")
    elif dir_to_predict:
        # Predict files in the directory
        detector.predict_directory(dir_to_predict, threshold)
    else:
        print("Error: Please specify either a file or a directory to predict.")
