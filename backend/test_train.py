import os
from typing import List
import torch
from torch.utils.data import DataLoader
from sklearn import metrics
from torch.cuda.amp import autocast, GradScaler
from tqdm import tqdm

from Trainer import Trainer
from util.config import conf
from util.datasets import PhpDataset
from model import BERTClassifier

def main():
    conf.set(
        seq_len=8,
        batch_size=8,
        num_batch=16,
        lr=0.01,
        weight_decay=0.0001,
        num_epochs=2
    )

    # 加载数据集
    train_dataset = PhpDataset("phpProcessor/dataset/1.csv")
    test_dataset = PhpDataset("phpProcessor/files/sequence/test/test.csv")

    train_loader = DataLoader(train_dataset, batch_size=conf.batch_size, shuffle=True, num_workers=4, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=conf.batch_size, shuffle=False, num_workers=4, pin_memory=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # 初始化模型
    model = BERTClassifier().to(device)

    # 预训练权重
    pretrain_path = "model/pre_train0.pth"
    if os.path.exists(pretrain_path):
        model.load_state_dict(torch.load(pretrain_path, map_location=device), strict=False)
        print(f"Loaded pretrained weights from {pretrain_path}")

    # 优化器 & 调度器
    optimizer = torch.optim.Adam(model.parameters(), lr=conf.lr, betas=(0.9, 0.999))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=2)

    # 训练管理器
    trainer = Trainer(model, train_loader, test_loader, optimizer, scheduler)

    # 加载已有训练进度
    checkpoint_path = "./model/checkpoint_epoch_0.pth"
    trainer.load_checkpoint(checkpoint_path)

    # 训练 5 轮（可分批进行）
    for _ in range(5):
        trainer.train_one_epoch()

    # 验证
    trainer.validate()

if __name__ == '__main__':
    main()