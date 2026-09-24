import ast
import pandas
import torch
import os
import json

from util.config import conf

from torch.utils.data import Dataset
from transformers import RobertaTokenizer


# dataset used in training mode (webshell detection task)
# when training a model, we first parse all PHP files into json files(corresponding sequence representation)
# the json is
#   "tokenSequence" -> tokenSequence of the PHP file
#   "stringSequence" -> stringLiterals of the PHP file
#   "tags" -> node tags of the PHP file
# 训练模式下使用的数据集（用于 Webshell 检测任务）
# 在训练模型时，我们首先将所有 PHP 文件解析为 JSON 文件（对应的序列表示）。
# JSON 文件的结构如下：
# - "tokenSequence": PHP 文件的标记序列
# - "stringSequence": PHP 文件中的字符串字面量序列
# - "tags": PHP 文件的节点标签

class PhpDataset2(Dataset):
    def __init__(self, path):
        self.black_file_list = os.listdir(path + 'webshell/')
        self.white_file_list = os.listdir(path + 'normal/')
        self.black = [path + 'webshell/' + i for i in self.black_file_list]
        self.white = [path + 'normal/' + i for i in self.white_file_list]

        self.tokenizer = RobertaTokenizer.from_pretrained("./codebert")
        # self.tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
        self.df = self.black + self.white

    def __getitem__(self, item):
        try:
            rf = open(self.df[item], 'r', encoding='utf-8', errors='ignore')
            raw_data = json.load(rf)
        finally:
            rf.close()

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

        ids = inputs['input_ids']
        mask = inputs['attention_mask']
        token_type_ids = inputs["token_type_ids"]


        return {
            'ids': torch.tensor(ids, dtype=torch.long),
            'mask': torch.tensor(mask, dtype=torch.long),
            'token_type_ids': torch.tensor(token_type_ids, dtype=torch.long),
            'targets': torch.tensor(1 if 'webshell' in self.df[item] else 0)
        }


    def __len__(self):
        return len(self.df)

class PhpDataset3(Dataset):
    def __init__(self, csv_path):
        # 读取CSV文件
        self.df = pandas.read_csv(csv_path)

        # 过滤出webshell和normal类别的文件
        self.webshell_data = self.df[self.df['label'] == 'webshell']
        self.normal_data = self.df[self.df['label'] == 'normal']

        # 将webshell和normal数据合并
        self.data = pandas.concat([self.webshell_data, self.normal_data], ignore_index=True)

        # 初始化tokenizer
        self.tokenizer = RobertaTokenizer.from_pretrained("./codebert")
        # self.tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")

    def __getitem__(self, item):
        # 从DataFrame中获取数据
        raw_data = self.data.iloc[item]
        # 确保tokenSequence和stringSequence是列表
        token_sequence = raw_data["tokenSequence"] if isinstance(raw_data["tokenSequence"], list) else raw_data[
            "tokenSequence"].split()
        string_sequence = raw_data["stringSequence"] if isinstance(raw_data["stringSequence"], list) else raw_data[
            "stringSequence"].split()

        # 拼接数据
        data = token_sequence + ["</s>"] + string_sequence

        # Tokenization
        inputs = self.tokenizer.encode_plus(
            data,
            None,
            add_special_tokens=True,
            max_length=conf.seq_len,
            padding='max_length',
            return_token_type_ids=True,
            truncation=True,
        )

        ids = inputs['input_ids']
        mask = inputs['attention_mask']
        token_type_ids = inputs["token_type_ids"]

        # 根据文件的类别标签返回target值
        target = 1 if raw_data['label'] == 'webshell' else 0

        return {
            'ids': torch.tensor(ids, dtype=torch.long),
            'mask': torch.tensor(mask, dtype=torch.long),
            'token_type_ids': torch.tensor(token_type_ids, dtype=torch.long),
            'targets': torch.tensor(target, dtype=torch.long)
        }

    def __len__(self):
        return len(self.data)

class PhpDataset(Dataset):
    def __init__(self, csv_path):
        # 读取CSV文件
        self.data = pandas.read_csv(csv_path)

        # 初始化tokenizer
        self.tokenizer = RobertaTokenizer.from_pretrained("./codebert")
        # self.tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")

    def __getitem__(self, item):
        # 从DataFrame中获取数据
        raw_data = self.data.iloc[item]
        # 确保tokenSequence和stringSequence是列表
        # token_sequence = raw_data["tokenSequence"] if isinstance(raw_data["tokenSequence"], list) else raw_data[
        #     "tokenSequence"].split()
        # string_sequence = raw_data["stringSequence"] if isinstance(raw_data["stringSequence"], list) else raw_data[
        #     "stringSequence"].split()
        # print(type(raw_data["tokenSequence"]))
        # print(raw_data["tokenSequence"])
        token_sequence = ast.literal_eval(raw_data["tokenSequence"]) if raw_data["tokenSequence"] else []
        string_sequence = ast.literal_eval(raw_data["stringSequence"]) if raw_data["stringSequence"] else []


        # 拼接数据
        data = token_sequence + ["</s>"] + string_sequence
        # print(token_sequence)
        # print(type(token_sequence))
        # print(type(data))

        # Tokenization
        inputs = self.tokenizer.encode_plus(
            data,
            None,
            add_special_tokens=True,
            max_length=conf.seq_len,
            padding='max_length',
            return_token_type_ids=True,
            truncation=True,
        )

        ids = inputs['input_ids']
        mask = inputs['attention_mask']
        token_type_ids = inputs["token_type_ids"]

        # 根据文件的类别标签返回target值
        target = 1 if raw_data['label'] == 'webshell' else 0

        return {
            'ids': torch.tensor(ids, dtype=torch.long),
            'mask': torch.tensor(mask, dtype=torch.long),
            'token_type_ids': torch.tensor(token_type_ids, dtype=torch.long),
            'targets': torch.tensor(target, dtype=torch.long)
        }

    def __len__(self):
        return len(self.data)

class TestDataset(Dataset):
    def __init__(self, path):
        self.black_file_list = os.listdir(path + 'webshell/')
        self.white_file_list = os.listdir(path + 'normal/')
        self.black = [path + 'webshell/' + i for i in self.black_file_list]
        self.white = [path + 'normal/' + i for i in self.white_file_list]

        self.tokenizer = RobertaTokenizer.from_pretrained("./codebert")
        # self.tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
        self.df = self.black + self.white

    def __getitem__(self, item):
        try:
            rf = open(self.df[item], 'r', encoding='utf-8', errors='ignore')
            raw_data = json.load(rf)
        finally:
            rf.close()

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

        ids = inputs['input_ids']
        mask = inputs['attention_mask']
        token_type_ids = inputs["token_type_ids"]


        return {
            'ids': torch.tensor(ids, dtype=torch.long),
            'mask': torch.tensor(mask, dtype=torch.long),
            'token_type_ids': torch.tensor(token_type_ids, dtype=torch.long),
            'targets': torch.tensor(1 if 'webshell' in self.df[item] else 0)
        }


    def __len__(self):
        return len(self.df)

# BIO mode
def prepare_sequence(seq, to_idx, max_seq_num):
    if (len(seq) >= max_seq_num - 2):
        seq = ['START'] + seq[: max_seq_num - 2] + ['END']
    else:
        seq = ['START'] + seq + ['END'] + ['O'] * (max_seq_num - len(seq) - 2)
    idx = [to_idx[w] for w in seq]
    return torch.tensor(idx, dtype=torch.long)

# dataset used when pretrain a model in Node tagging task, to save time we convert labelled json to another json file
# for example, if a raw json is
#  {
#    "tokenSequence": T1, T2, T3, T4, ....
#    "stringSequence":  S1, S2
#    "nodeTags": N1, N2, N3, N4, ...
#  }
# The RobertTokenizer may tokenize a token Ti into several subtoken Ti1,..., Tij, so we need to convert tag sequences,
# and save converted json data into a new json file to save time when pretraining( avoid duplication of efforts)
# converted json file is(example):  we remove key stringSequence because we don't need it in pretrain task
# {
#    "tokenSequence": T11, T12, T2, T31, T32, T33, T4, ...
#    "nodeTags: B-N1, I-N1, B-N2, B-N3, I-N3, I-N3, B-N4, ...
# }
# 在进行节点标记任务的模型预训练时使用的数据集，为了节省时间，我们将标注的json转换成另一个json文件
# 例如，如果原始json是：
#  {
#    "tokenSequence": T1, T2, T3, T4, ....
#    "stringSequence":  S1, S2
#    "nodeTags": N1, N2, N3, N4, ...
#  }
# 由于RobertaTokenizer可能会将一个token Ti 拆分为多个子token Ti1,..., Tij，因此我们需要转换标签序列，
# 并将转换后的json数据保存到一个新的json文件中，以便在预训练时节省时间（避免重复劳动）。
# 转换后的json文件示例：我们去掉了stringSequence键，因为在预训练任务中我们不需要它。
# {
#    "tokenSequence": T11, T12, T2, T31, T32, T33, T4, ...
#    "nodeTags: B-N1, I-N1, B-N2, B-N3, I-N3, I-N3, B-N4, ...
# }

# class POS_Lable_datasets(Dataset):
#     def __init__(self, path, total_len, label_dict):
#         self.file_list = os.listdir(path)
#         self.df = [path + i for i in self.file_list]
#         self.tokenizer = RobertaTokenizer.from_pretrained("./codebert")
#         self.total_len = total_len
#         self.label_dict = label_dict # label_dict is to map node tag to a index,
#
#     def __len__(self):
#         return len(self.df)
#
#     def __getitem__(self, item):
#         fp = open(self.df[item], 'r', encoding='utf-8')
#         raw_datas = json.load(fp)
#         # 调试数据内容
#         # print(f"Processing file: {self.df[item]}")
#         # print(f"Raw data: {raw_datas}")
#
#         tokens = raw_datas.get("tokenSequence", [])
#         if not tokens or not isinstance(tokens, list):
#             raise ValueError(f"Invalid or empty token sequence in file: {self.df[item]}")
#         # tokens = raw_datas["tokenSequence"]
#         # tokens = [token if token is not None else "" for token in tokens]
#         inputs_token = self.tokenizer.encode_plus(
#             tokens,
#             None,
#             add_special_tokens=True,
#             max_length=self.total_len,
#             padding='max_length',
#             return_token_type_ids=True,
#             truncation=True,
#         )
#
#         ids = inputs_token['input_ids']
#         mask = inputs_token['attention_mask']
#         token_type_ids = inputs_token["token_type_ids"]
#
#         return {
#             'ids': torch.tensor(ids, dtype=torch.long),
#             'mask': torch.tensor(mask, dtype=torch.long),
#             'token_type_ids': torch.tensor(token_type_ids, dtype=torch.long),
#             'tags': prepare_sequence(seq=raw_datas["tags"], to_idx=self.label_dict, max_seq_num=self.total_len)
#         }
class POS_Lable_datasets(Dataset):
    def __init__(self, csv_path, total_len, label_dict):
        """
        csv_path: CSV 文件路径
        total_len: 句子最大长度
        label_dict: 标签映射字典
        """
        self.df = pandas.read_csv(csv_path)  # 读取 CSV 数据
        self.tokenizer = RobertaTokenizer.from_pretrained("./codebert")
        self.total_len = total_len
        self.label_dict = label_dict  # 标签映射字典

    def __len__(self):
        return len(self.df)

    def __getitem__(self, item):
        """
        读取 CSV 数据并进行 tokenization
        """
        # 读取当前行数据
        row = self.df.iloc[item]

        # 解析 tokenSequence，确保是字符串并转换成列表
        tokens = eval(row["tokenSequence"]) if isinstance(row["tokenSequence"], str) else row["tokenSequence"]
        if not tokens or not isinstance(tokens, list):
            raise ValueError(f"Invalid or empty token sequence at index: {item}")

        # 进行 tokenization
        inputs_token = self.tokenizer.encode_plus(
            tokens,
            None,
            add_special_tokens=True,
            max_length=self.total_len,
            padding='max_length',
            return_token_type_ids=True,
            truncation=True,
        )

        ids = inputs_token['input_ids']
        mask = inputs_token['attention_mask']
        token_type_ids = inputs_token["token_type_ids"]

        # 解析标签数据
        tags = eval(row["tags"]) if isinstance(row["tags"], str) else row["tags"]
        tags_tensor = prepare_sequence(seq=tags, to_idx=self.label_dict, max_seq_num=self.total_len)

        return {
            'ids': torch.tensor(ids, dtype=torch.long),
            'mask': torch.tensor(mask, dtype=torch.long),
            'token_type_ids': torch.tensor(token_type_ids, dtype=torch.long),
            'tags': tags_tensor
        }