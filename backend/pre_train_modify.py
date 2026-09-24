from seqeval.metrics import accuracy_score, classification_report
from transformers import get_linear_schedule_with_warmup

from model import *
from util.datasets import POS_Lable_datasets
from torch.utils.data import DataLoader
from tqdm import tqdm
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List

# 设备检测
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# 数据加载优化
def collate_fn(batch):
    return {
        'ids': torch.stack([x['ids'] for x in batch]),
        'mask': torch.stack([x['mask'] for x in batch]),
        'token_type_ids': torch.stack([x['token_type_ids'] for x in batch]),
        'tags': torch.stack([x['tags'] for x in batch])
    }


# 设备转移函数
def move_to_device(data: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    return {k: v.to(device, non_blocking=True) for k, v in data.items()}


# 初始化数据
label_dict = json.load(open('label_dict.json', 'r', encoding='utf-8'))
labels = json.load(open('labels.json', 'r', encoding='utf-8'))

train_dataset = POS_Lable_datasets('phpProcessor/files/sequence/pre_train.csv',
                                   total_len=conf.seq_len,
                                   label_dict=label_dict)
test_dataset = POS_Lable_datasets('phpProcessor/files/sequence/pre_test.csv',
                                  total_len=conf.seq_len,
                                  label_dict=label_dict)

training_loader = DataLoader(
    train_dataset,
    batch_size=conf.batch_size,
    shuffle=True,
    num_workers=conf.num_workers,
    pin_memory=True,
    collate_fn=collate_fn
)

testing_loader = DataLoader(
    test_dataset,
    batch_size=conf.batch_size,
    shuffle=False,
    num_workers=conf.num_workers,
    pin_memory=True,
    collate_fn=collate_fn
)


# 训练函数
def train(model: nn.Module,
          train_loader: DataLoader,
          val_loader: DataLoader,
          optimizer: torch.optim.Optimizer,
          scheduler: torch.optim.lr_scheduler._LRScheduler,
          num_epochs: int) -> List[float]:
    best_acc = 0.0
    results = []
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(num_epochs):
        model.train()
        epoch_loss = 0.0
        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{num_epochs}")

        for batch_idx, batch in enumerate(progress_bar):
            optimizer.zero_grad()
            batch = move_to_device(batch)

            # 前向传播
            emissions = model(
                batch['ids'],
                batch['mask'],
                batch['token_type_ids']
            )

            # 计算损失
            loss = loss_fn(
                emissions.view(-1, emissions.size(-1)),
                batch['tags'].view(-1)
            )

            # 反向传播
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), conf.max_grad_norm)
            optimizer.step()
            scheduler.step()

            # 更新进度条
            epoch_loss += loss.item()

            # 实时打印日志
            if batch_idx % 10 == 0:
                # 计算当前batch的准确率
                preds = torch.argmax(emissions, dim=2).cpu().tolist()
                targets = batch['tags'].cpu().tolist()
                acc = accuracy_score(targets, preds)

                # 打印日志
                progress_bar.set_postfix({
                    'loss': f"{loss.item():.4f}",
                    'acc': f"{acc:.4f}"
                })
                # print(f"epoch:{epoch + 1} sets:{batch_idx}/{len(train_loader)}, "
                #       f"loss:{loss.item():.4f}, acc:{acc:.4f}")

        # 验证
        val_acc = validate(model, val_loader)
        results.append(val_acc)

        # 保存最佳模型
        # if val_acc > best_acc:
        #     best_acc = val_acc
        #     torch.save({
        #         'epoch': epoch,
        #         'model_state_dict': model.state_dict(),
        #         'optimizer_state_dict': optimizer.state_dict(),
        #         'loss': loss,
        #     }, 'best_model.pth')
        torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'loss': loss,
                }, 'model/pre_train{}.pth'.format(epoch))

        print(f"Epoch {epoch + 1} | Avg Loss: {epoch_loss / len(train_loader):.4f} | Val Acc: {val_acc:.4f}")

    return results


# 验证函数
def validate(model: nn.Module, val_loader: DataLoader) -> float:
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Validating"):
            batch = move_to_device(batch)

            emissions = model(
                batch['ids'],
                batch['mask'],
                batch['token_type_ids']
            )

            preds = torch.argmax(emissions, dim=2).cpu().tolist()
            targets = batch['tags'].cpu().tolist()

            all_preds.extend(preds)
            all_targets.extend(targets)

    # 转换标签
    id2label = {v: k for k, v in label_dict.items()}
    pred_labels = [[id2label[id] for id in seq] for seq in all_preds]
    true_labels = [[id2label[id] for id in seq] for seq in all_targets]

    # 计算指标
    acc = accuracy_score(true_labels, pred_labels)
    print(classification_report(true_labels, pred_labels))
    return acc


if __name__ == '__main__':
    # 初始化模型
    model = BERT_POS(len(labels)).to(device)

    # 优化器设置
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=conf.lr,
        weight_decay=conf.weight_decay
    )

    # 学习率调度
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=100,
        num_training_steps=len(training_loader) * conf.num_epochs
    )

    # 训练
    results = train(
        model,
        training_loader,
        testing_loader,
        optimizer,
        scheduler,
        conf.num_epochs
    )

    # 输出结果
    print("Best validation accuracy:", max(results))