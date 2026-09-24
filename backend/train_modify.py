import os
from typing import List
import numpy as np
import torch
from torch.utils.data import DataLoader
from sklearn import metrics
from collections import OrderedDict

from util.config import conf
from util.datasets import PhpDataset
from model import BERTClassifier
from torch.cuda.amp import autocast, GradScaler
from tqdm import tqdm  # 进度条库

# 路径配置
train_path = 'phpProcessor/dataset/train1.csv'
test_path = 'phpProcessor/dataset/test1.csv'

# 设备配置
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 标签平滑函数
def label_smoothing(inputs, epsilon=0.1):
    return ((1 - epsilon) * inputs) + (epsilon / 2)

# 损失函数
def loss_fn(outputs, targets):
    return torch.nn.BCEWithLogitsLoss()(outputs, targets)

# 训练函数
def train(epoch, training_loader, model, optimizer, scheduler=None):
    model.train()
    scaler = GradScaler()  # 混合精度训练
    best_f1 = 0  # 保存最佳 F1 分数

    for i in range(epoch):
        total_loss = 0
        total_correct = 0
        num_samples = 0

        # 使用 tqdm 添加进度条
        progress_bar = tqdm(training_loader, desc=f'Epoch {i + 1}/{epoch}', leave=False)
        for batch_idx, data in enumerate(progress_bar):
            targets = data['targets'].view(-1, 1).to(device, dtype=torch.float)  # [batch_size, 1]
            # targets = data['targets'].view(-1).to(device, dtype=torch.float)
            ids = data['ids'].to(device, dtype=torch.long)
            mask = data['mask'].to(device, dtype=torch.long)
            token_type_ids = data['token_type_ids'].to(device, dtype=torch.long)

            optimizer.zero_grad()

            # 混合精度训练
            with autocast():
                outputs = model(ids, mask, token_type_ids)  # [batch_size, 1]
                loss = loss_fn(outputs, targets)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            # 计算准确率
            pred_choice = (torch.sigmoid(outputs) > 0.5).float()  # logits > 0.5
            correct = pred_choice.eq(targets).sum().item()
            total_correct += correct
            total_loss += loss.item()
            num_samples += targets.size(0)

            # 每 10 个批次更新一次进度条
            if batch_idx % 10 == 0:
                progress_bar.set_postfix({
                    'loss': f"{loss.item():.4f}",
                    'acc': f"{correct / targets.size(0):.4f}"
                })

        # 每轮次结束后计算平均损失和准确率
        avg_loss = total_loss / len(training_loader)
        avg_acc = total_correct / num_samples
        print(f'Epoch [{i + 1}/{epoch}] completed. Avg Loss: {avg_loss:.4f}, Avg Accuracy: {avg_acc:.4f}')

        # 保存模型
        if not os.path.exists('./model'):
            os.makedirs('./model')
        save_path = os.path.join('./model/', f'train_{i + 1}.pth')
        torch.save(model.state_dict(), save_path)
        print(f'Model saved to {save_path}')

        # 学习率调度
        if scheduler:
            scheduler.step(avg_loss)

def validation_gpt(testing_loader, model):
    model.eval()

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in testing_loader:
            targets = batch['targets'].view(-1).to(device, dtype=torch.long)
            ids = batch['ids'].to(device, dtype=torch.long)
            mask = batch['mask'].to(device, dtype=torch.long)
            token_type_ids = batch['token_type_ids'].to(device, dtype=torch.long)

            outputs = model(ids, mask, token_type_ids)  # shape: [batch_size, 1]
            # preds = (torch.sigmoid(outputs) > 0.5).long().view(-1)  # shape: [batch_size]
            preds = (torch.sigmoid(outputs) > 0.5).float().squeeze().view(-1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(targets.cpu().numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    print("Confusion Matrix:\n", metrics.confusion_matrix(all_labels, all_preds))
    print("Accuracy:", metrics.accuracy_score(all_labels, all_preds))
    print("F1 Score:", metrics.f1_score(all_labels, all_preds))
    print("Recall:", metrics.recall_score(all_labels, all_preds))
    print("Precision:", metrics.precision_score(all_labels, all_preds))


def validation_old(testing_loader, model):
    model.eval()

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in testing_loader:
            # 原始标签 (0 或 1)，shape: [batch_size]
            targets = batch['targets'].view(-1).to(device, dtype=torch.long)

            # 模型输入
            ids = batch['ids'].to(device, dtype=torch.long)
            mask = batch['mask'].to(device, dtype=torch.long)
            token_type_ids = batch['token_type_ids'].to(device, dtype=torch.long)

            # 模型输出 logits
            outputs = model(ids, mask, token_type_ids)  # shape: [batch_size, 2]
            preds = torch.argmax(outputs, dim=1)        # shape: [batch_size]

            # 收集 CPU 上的结果
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(targets.cpu().numpy())

    # 转为 NumPy 数组
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    # 输出评估指标
    print("Confusion Matrix:\n", metrics.confusion_matrix(all_labels, all_preds))
    print("Accuracy:", metrics.accuracy_score(all_labels, all_preds))
    print("F1 Score:", metrics.f1_score(all_labels, all_preds))
    print("Recall:", metrics.recall_score(all_labels, all_preds))
    print("Precision:", metrics.precision_score(all_labels, all_preds))

# 验证函数
def validation(testing_loader, model):
    model.eval()
    outs = []
    tars = []

    with torch.no_grad():
        for _, data in enumerate(testing_loader):
            targets = data['targets'].to(device, dtype=torch.float)  # [batch_size]
            ids = data['ids'].to(device, dtype=torch.long)
            mask = data['mask'].to(device, dtype=torch.long)
            token_type_ids = data['token_type_ids'].to(device, dtype=torch.long)

            outputs = model(ids, mask, token_type_ids)  # [batch_size, 1]
            preds = (torch.sigmoid(outputs) > 0.5).float().squeeze()  # [batch_size]

            outs.append(preds.cpu())
            tars.append(targets.cpu())

    output = torch.cat(outs, 0).numpy()
    target = torch.cat(tars, 0).numpy()

    print("Validation Metrics:")
    print(f"Accuracy: {metrics.accuracy_score(target, output):.4f}")
    print(f"F1 Score: {metrics.f1_score(target, output):.4f}")
    print(f"Recall: {metrics.recall_score(target, output):.4f}")
    print(f"Precision: {metrics.precision_score(target, output):.4f}")
    print("Confusion Matrix:")
    print(metrics.confusion_matrix(target, output))

    return metrics.f1_score(target, output)  # 返回 F1 分数

# 加载预训练模型
def load_pretrained_model(
        model: torch.nn.Module,
        checkpoint_path: str,
        exclude_layers: List[str] = None
) -> torch.nn.Module:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    if 'model_state_dict' in checkpoint:
        checkpoint = checkpoint['model_state_dict']
    if exclude_layers is None:
        exclude_layers = []
    pretrained_params = {k: v for k, v in checkpoint.items() if not any(exclude in k for exclude in exclude_layers)}
    model_state_dict = model.state_dict()
    model_state_dict.update(pretrained_params)
    model.load_state_dict(model_state_dict, strict=False)
    # print(f"Loaded pretrained weights from {checkpoint_path}, excluding layers: {exclude_layers}")
    return model

# 主函数
if __name__ == '__main__':
    # 加载数据集
    train_dataset = PhpDataset(train_path)
    test_dataset = PhpDataset(test_path)

    training_loader = DataLoader(
        dataset=train_dataset,
        batch_size=conf.batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
        drop_last=False
    )
    testing_loader = DataLoader(
        dataset=test_dataset,
        batch_size=conf.batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True,
        drop_last=False
    )
    conf.set(
        seq_len=8,
        batch_size=8,
        num_batch=4,
        lr=0.01,
        num_epochs=10
    )

    # 初始化模型
    model = BERTClassifier().to(device)

    # 加载预训练权重
    pretrain_pos_path = 'model/pre_train0.pth'
    model = load_pretrained_model(
        model=model,
        checkpoint_path=pretrain_pos_path,
        exclude_layers=['fc']  # 排除全连接层
    )
    # torch.save(model.state_dict(), 'model/pre_train_no_fc.pth')

    # 优化器和学习率调度器
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-5, betas=(0.9, 0.999))
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=2)

    # 训练和验证
    # train(1, training_loader, model, optimizer, scheduler)
    
    model.load_state_dict(torch.load("model/train_3_good.pth"))
    validation_gpt(testing_loader, model)