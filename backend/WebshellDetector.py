import ast
import csv
from typing import List
from sklearn.metrics import accuracy_score
import pandas
import torch
import torch.nn as nn
from transformers import RobertaModel, RobertaTokenizer
import json
import os
from model import BERTClassifier
import pandas as pd
import json
import torch
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
        # self.load_pretrained_model(
        #     checkpoint_path=model_path,
        #     exclude_layers=['fc']  # 排除所有包含 'fc' 的层
        # )

    def load_model(self, model_path):
        """
        Load the pre-trained model from the specified path.
        :param model_path: Path to the model weights file
        """
        try:
            state_dict = torch.load(model_path)
            self.model.load_state_dict(state_dict)
            print(f"Model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            exit(1)

    # def load_pretrained_model(
    #         self,
    #         checkpoint_path: str,
    #         exclude_layers: List[str] = None
    # ):
    #     """
    #     加载预训练模型的权重，并排除指定层的权重。
    #
    #     参数:
    #         model (torch.nn.Module): 需要加载权重的模型实例。
    #         checkpoint_path (str): 预训练模型权重的路径。
    #         exclude_layers (List[str]): 需要排除的层名称（默认为空）。
    #
    #     返回:
    #         torch.nn.Module: 加载了预训练权重的模型。
    #     """
    #     # 加载预训练模型的 checkpoint
    #     checkpoint = torch.load(checkpoint_path, map_location=conf.device)
    #
    #     # 如果 checkpoint 是一个完整的训练状态，提取 model_state_dict
    #     if 'model_state_dict' in checkpoint:
    #         checkpoint = checkpoint['model_state_dict']
    #
    #     # 如果未指定排除层，则默认为空列表
    #     if exclude_layers is None:
    #         exclude_layers = []
    #
    #     # 过滤掉需要排除的层
    #     pretrained_params = {
    #         k: v for k, v in checkpoint.items()
    #         if not any(exclude in k for exclude in exclude_layers)
    #     }
    #
    #     # 获取当前模型的状态字典
    #     model_state_dict = self.model.state_dict()
    #
    #     # 更新当前模型的状态字典
    #     model_state_dict.update(pretrained_params)
    #
    #     # 加载更新后的状态字典
    #     self.model.load_state_dict(model_state_dict)



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


    # def predict_from_csv(self, file_path=None, threshold=0.6):


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

    # def predict_from_csv(self, csv_path, output_path="webshellresults.txt", threshold=0.6):
    #     """
    #     Predict if each sample in the CSV is a webshell and save results to a TXT file.
    #     Uses pandas for CSV parsing.
    #     :param csv_path: Path to the CSV file
    #     :param output_path: Path to the output TXT file
    #     :param threshold: Classification threshold
    #     :return: None
    #     """
    #     results = []
    #     correct = 0
    #     total = 0

    #     try:
    #         df = pd.read_csv(csv_path)

    #         for idx, row in df.iterrows():
    #             try:
    #                 token_seq = json.loads(row['tokenSequence']) if isinstance(row['tokenSequence'], str) else row['tokenSequence']
    #                 string_seq = json.loads(row['stringSequence']) if isinstance(row['stringSequence'], str) else row['stringSequence']
    #                 real_label = int(row['label'])

    #                 data = token_seq + ["</s>"] + string_seq

    #                 inputs = self.tokenizer.encode_plus(
    #                     data,
    #                     None,
    #                     add_special_tokens=True,
    #                     max_length=conf.seq_len,
    #                     padding='max_length',
    #                     return_token_type_ids=True,
    #                     truncation=True,
    #                 )

    #                 ids = torch.tensor([inputs['input_ids']], dtype=torch.long).to(self.device)
    #                 mask = torch.tensor([inputs['attention_mask']], dtype=torch.long).to(self.device)
    #                 token_type_ids = torch.tensor([inputs["token_type_ids"]], dtype=torch.long).to(self.device)

    #                 self.model.eval()
    #                 with torch.no_grad():
    #                     logits = self.model(ids, mask, token_type_ids)
    #                     prob = torch.sigmoid(logits).item()
    #                     is_webshell = int(prob > threshold)

    #                     results.append((idx, is_webshell, prob, real_label))

    #                     total += 1
    #                     if is_webshell == real_label:
    #                         correct += 1

    #             except Exception as sample_err:
    #                 print(f"[Sample {idx}] Error: {sample_err}")
    #                 results.append((idx, None, None, row.get('label', 'unknown')))

    #         # 写入结果到 TXT 文件
    #         with open(output_path, 'w', encoding='utf-8') as f:
    #             f.write("Index\tPredicted\tProbability\tRealLabel\n")
    #             for idx, pred, prob, label in results:
    #                 prob_str = f"{prob:.4f}" if prob is not None else "None"
    #                 f.write(f"{idx}\t{pred}\t{prob_str}\t{label}\n")

    #             # 统计信息
    #             if total > 0:
    #                 accuracy = correct / total
    #                 f.write("\n")
    #                 f.write(f"Total samples: {total}\n")
    #                 f.write(f"Correct predictions: {correct}\n")
    #                 f.write(f"Accuracy: {accuracy:.4f}\n")
    #             else:
    #                 f.write("\nNo valid samples to evaluate.\n")

    #         print(f"Results and statistics saved to {output_path}")

    #     except Exception as e:
    #         print(f"Error reading CSV with pandas: {e}")
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
    # Initialize WebshellDetector
    model_path = 'model/train_3.pth'
    # tokenizer = RobertaTokenizer.from_pretrained('./codebert')
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
        is_webshell, probability = detector.predict(file_to_predict, threshold)
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
