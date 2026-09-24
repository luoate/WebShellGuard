import torch
import torch.nn as nn
from transformers import RobertaModel, RobertaTokenizer
import json
import os

from model import BERTClassifier
from util.config import conf


# 推理函数
def predict_file(file_path, model, tokenizer, threshold=0.5):
    """
    预测单个文件是否为 webshell
    :param file_path: 输入文件的路径
    :param model: 加载的训练模型
    :param tokenizer: CodeBERT 的 tokenizer
    :param threshold: 分类阈值（默认 0.5）
    :return: 是否为 webshell (True/False) 和预测概率
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as rf:
            raw_data = json.load(rf)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None, None

    data = raw_data["tokenSequence"] + ["</s>"] + raw_data["stringSequence"]
    inputs = tokenizer.encode_plus(
        data,
        None,
        add_special_tokens=True,
        max_length=conf.seq_len,
        padding='max_length',
        return_token_type_ids=True,
        truncation=True,
    )

    ids = torch.tensor([inputs['input_ids']], dtype=torch.long).to(conf.device)
    mask = torch.tensor([inputs['attention_mask']], dtype=torch.long).to(conf.device)
    token_type_ids = torch.tensor([inputs["token_type_ids"]], dtype=torch.long).to(conf.device)

    model.eval()
    with torch.no_grad():
        logits = model(ids, mask, token_type_ids)  # [1, 1]
        prob = torch.sigmoid(logits).item()  # 转换为概率
        is_webshell = prob > threshold

    return is_webshell, prob

# 遍历目录并预测
def predict_directory(dir_path, model, tokenizer, threshold=0.5):
    """
    预测目录下所有 JSON 文件是否为 webshell
    :param dir_path: 输入目录路径
    :param model: 加载的训练模型
    :param tokenizer: CodeBERT 的 tokenizer
    :param threshold: 分类阈值（默认 0.5）
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
        is_webshell, probability = predict_file(file_path, model, tokenizer, threshold)
        if is_webshell is not None:
            print(f"File: {file_path}")
            print(f"Probability of being a webshell: {probability:.4f}")
            print(f"Prediction: {'Webshell' if is_webshell else 'Normal'}")
            print("-" * 50)
        else:
            print(f"Skipping {file_path} due to processing error.")

# 主程序
if __name__ == "__main__":
    # 加载 tokenizer
    tokenizer = RobertaTokenizer.from_pretrained("./codebert")

    # 加载模型
    model = BERTClassifier().to(conf.device)
    model_path = 'model/cls_model_epoch_3_no_module.pth'
    state_dict = torch.load(model_path)
    # 去除 "module." 前缀
    # state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
    # # 保存新的权重文件
    # new_save_path = 'model/cls_model_epoch_3_no_module.pth'
    # torch.save(state_dict, new_save_path)
    try:
        model.load_state_dict(state_dict)
        print(f"Model loaded from {model_path} after removing 'module.' prefix")
    except Exception as e:
        print(f"Error loading model: {e}")
        exit(1)

    # 指定要预测的文件或目录（根据需要修改）
    file_to_predict = None  # 例如：'path_to_your_file.json'，设为 None 表示不预测单个文件
    dir_to_predict = 'phpProcessor/files/sequence/test/normal'  # 例如：'your_directory/'，设为 None 表示不预测目录
    # dir_to_predict = None  # 例如：'your_directory/'，设为 None 表示不预测目录
    threshold = 0.5  # 分类阈值，可以根据需要调整

    # 预测逻辑
    if file_to_predict and dir_to_predict:
        print("Error: Please specify either a file or a directory, not both.")
    elif file_to_predict:
        # 预测单个文件
        is_webshell, probability = predict_file(file_to_predict, model, tokenizer, threshold)
        if is_webshell is not None:
            print(f"File: {file_to_predict}")
            print(f"Probability of being a : {probability:.4f}")
            print(f"Prediction: {'Webshell' if is_webshell else 'Normal'}")
        else:
            print("Prediction failed.")
    elif dir_to_predict:
        # 预测目录
        predict_directory(dir_to_predict, model, tokenizer, threshold)
    else:
        print("Error: Please specify either a file or a directory to predict.")