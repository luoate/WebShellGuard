import os
from typing import List
import numpy
import torch
from torch.utils.data import DataLoader
from sklearn import metrics
from torch.cuda.amp import autocast, GradScaler
from tqdm import tqdm

from util.config import conf
from util.datasets import PhpDataset
from model import BERTClassifier
import time

# 设备配置
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 损失函数
def loss_fn(outputs, targets):
    return torch.nn.BCEWithLogitsLoss()(outputs, targets)

    # 用于检查中止标志的函数
def check_stop_flag():
    try:
        with open('stop_flag.txt', "r") as f:
            content = f.read().strip()
            return content == "STOP"
    except FileNotFoundError:
        return False
def clear_stop_flag():
    os.remove('stop_flag.txt')


class Trainer:
    # def __init__(self, model, train_loader, test_loader, optimizer, scheduler=None, save_dir="./model"):
    #     self.model = model.to(device)
    #     self.train_loader = train_loader
    #     self.test_loader = test_loader
    #     self.optimizer = optimizer
    #     self.scheduler = scheduler
    #     self.scaler = GradScaler()
    #     self.best_f1 = 0 
    #     self.epoch = 0  # 记录当前 epoch 进度
    #     self.save_dir = save_dir
    #     os.makedirs(self.save_dir, exist_ok=True)
    def __init__(self, model=None, train_dataset_path=None, test_dataset_path="phpProcessor/files/sequence/test/test.csv", optimizer=None, scheduler=None, save_dir="./model"):
        self.model = model.to(device)
        self.train_dataset_path = train_dataset_path
        self.test_dataset_path = test_dataset_path
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.scaler = GradScaler()
        self.best_f1 = 0 
        self.epoch = 0  # 记录当前 epoch 进度
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def save_checkpoint(self):
        save_path = os.path.join(self.save_dir, f"tmp/checkpoint_epoch_{self.epoch}.pth")
        torch.save({
            "epoch": self.epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict() if self.scheduler else None
        }, save_path)
        print(f"Checkpoint saved at {save_path}")

    def load_checkpoint(self, checkpoint_path):
        if os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=device)
            self.epoch = checkpoint["epoch"]
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            if self.scheduler and "scheduler_state_dict" in checkpoint and checkpoint["scheduler_state_dict"]:
                self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
            print(f"Resumed training from epoch {self.epoch}")
        else:
            print(f"Checkpoint not found at {checkpoint_path}, starting from scratch.")


    def train_one_epoch(self):
        train_dataset = PhpDataset(self.train_dataset_path)
        train_loader = DataLoader(train_dataset, batch_size=conf.batch_size, shuffle=True, num_workers=4, pin_memory=True)

        self.model.train()
        total_loss, total_correct, num_samples = 0, 0, 0

        progress_bar = tqdm(train_loader, desc=f"Epoch {self.epoch + 1}", leave=False)
        for batch_idx, data in enumerate(progress_bar):
            # 中止标识
            if check_stop_flag():
                clear_stop_flag()
                return False, False
            
            targets = data["targets"].view(-1, 1).to(device, dtype=torch.float)
            ids = data["ids"].to(device, dtype=torch.long)
            mask = data["mask"].to(device, dtype=torch.long)
            token_type_ids = data["token_type_ids"].to(device, dtype=torch.long)

            self.optimizer.zero_grad()

            with autocast():
                outputs = self.model(ids, mask, token_type_ids)
                loss = loss_fn(outputs, targets)

            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()

            pred_choice = (torch.sigmoid(outputs) > 0.5).float()
            total_correct += pred_choice.eq(targets).sum().item()
            total_loss += loss.item()
            num_samples += targets.size(0)

            if batch_idx % 10 == 0:
                progress_bar.set_postfix({"loss": f"{loss.item():.4f}", "acc": f"{total_correct / num_samples:.4f}"})

        avg_loss = total_loss / len(train_loader)
        avg_acc = total_correct / num_samples
        print(f"Epoch {self.epoch + 1} completed. Loss: {avg_loss:.4f}, Accuracy: {avg_acc:.4f}")

        if self.scheduler:
            self.scheduler.step(avg_loss)

        self.epoch += 1
        self.save_checkpoint()
        # self.validate()

        return avg_acc, avg_loss

    def validate(self):
        test_dataset = PhpDataset(self.test_dataset_path)
        test_loader = DataLoader(test_dataset, batch_size=conf.batch_size, shuffle=False, num_workers=4, pin_memory=True)
        self.model.eval()
        outs, tars = [], []
        total_loss = 0
        total_samples = 0
        loss_fn = torch.nn.BCEWithLogitsLoss()
        total_loss = 0

        start_time = time.time()  # 开始计时

        with torch.no_grad():
            for _, data in enumerate(test_loader):
                targets = data["targets"].to(device, dtype=torch.long)
                ids = data["ids"].to(device, dtype=torch.long)
                mask = data["mask"].to(device, dtype=torch.long)
                token_type_ids = data["token_type_ids"].to(device, dtype=torch.long)

                outputs = self.model(ids, mask, token_type_ids)
                loss = loss_fn(outputs.view(-1), targets.view(-1).float())
                total_loss += loss.item()
                total_samples += ids.size(0)  # 统计样本数量（BERT输入通常以batch为单位）

                preds = (torch.sigmoid(outputs) > 0.6).float().squeeze(-1)
                # print(torch.sigmoid(outputs))
                outs.append(preds.cpu())
                tars.append(targets.cpu())

        end_time = time.time()  # 结束计时
        total_time = end_time - start_time
        throughput = total_samples / total_time  # 吞吐量：样本数 / 秒
        inference_speed = total_time / total_samples  # 每个样本的平均推理时间

        output = torch.cat(outs, 0).numpy()
        target = torch.cat(tars, 0).numpy()

        acc = metrics.accuracy_score(target, output)
        f1 = metrics.f1_score(target, output)
        recall = metrics.recall_score(target, output)
        precision = metrics.precision_score(target, output)
        avg_loss = total_loss / len(test_loader)

        # print("Sigmoid outputs (first 10):", torch.sigmoid(outputs[:10]))
        # print("Preds (first 10):", preds[:10])
        # print("Targets (first 10):", targets[:10])
        print("Confusion Matrix:")
        print(metrics.confusion_matrix(target, output))


        print(
            f"Validation Metrics - Loss: {avg_loss:.4f}, Accuracy: {acc:.4f}, F1: {f1:.4f}, Recall: {recall:.4f}, Precision: {precision:.4f}")
        print(f"Inference Time: {total_time:.2f}s, Throughput: {throughput:.2f} samples/s, Per Sample: {inference_speed*1000:.2f} ms")

        return acc, avg_loss, recall, precision, f1, throughput, inference_speed*1000


    def validate2(self):
        test_dataset = PhpDataset(self.test_dataset_path)
        test_loader = DataLoader(test_dataset, batch_size=conf.batch_size, shuffle=False, num_workers=4, pin_memory=True)

        self.model.eval()
        total_loss, total_correct, num_samples = 0, 0, 0
        all_preds, all_labels = [], []
        all_logits, all_probs = [], []

        with torch.no_grad():
            for data in tqdm(test_loader, desc="Validating", leave=False):
                targets = data["targets"].view(-1, 1).to(device, dtype=torch.float)
                ids = data["ids"].to(device, dtype=torch.long)
                mask = data["mask"].to(device, dtype=torch.long)
                token_type_ids = data["token_type_ids"].to(device, dtype=torch.long)

                with autocast():
                    outputs = self.model(ids, mask, token_type_ids)
                    loss = loss_fn(outputs, targets)

                probs = torch.sigmoid(outputs)
                # print(probs.squeeze().item())
                preds = (probs > 0.5).float()

                total_correct += preds.eq(targets).sum().item()
                total_loss += loss.item()
                num_samples += targets.size(0)

                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(targets.cpu().numpy())
                all_logits.extend(outputs.cpu().numpy())
                all_probs.extend(probs.cpu().numpy())

        avg_loss = total_loss / len(test_loader)
        avg_acc = total_correct / num_samples
        precision = metrics.precision_score(all_labels, all_preds, zero_division=0)
        recall = metrics.recall_score(all_labels, all_preds, zero_division=0)
        f1 = metrics.f1_score(all_labels, all_preds, zero_division=0)

        print(f"Validation - Loss: {avg_loss:.4f}, Accuracy: {avg_acc:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")

        logits_np = numpy.array(all_logits).flatten()
        probs_np = numpy.array(all_probs).flatten()

        print(f"Logits stats: min={logits_np.min():.4f}, max={logits_np.max():.4f}, mean={logits_np.mean():.4f}, std={logits_np.std():.4f}")
        print(f"Sigmoid probs stats: min={probs_np.min():.4f}, max={probs_np.max():.4f}, mean={probs_np.mean():.4f}, std={probs_np.std():.4f}")

        # 保存最佳模型
        # if f1 > self.best_f1:
        #     self.best_f1 = f1
        #     best_model_path = os.path.join(self.save_dir, "best_model.pth")
        #     torch.save(self.model.state_dict(), best_model_path)
        #     print(f"New best model saved with F1: {f1:.4f}")

        return avg_acc, avg_loss, recall, precision, 0, 0
        # return acc, avg_loss, recall, precision, throughput, inference_speed*1000
    def validate3(self):
        # 加载验证集数据
        test_dataset = PhpDataset(self.test_dataset_path)
        test_loader = DataLoader(test_dataset, batch_size=conf.batch_size, shuffle=False, num_workers=4, pin_memory=True)

        # 设置模型为评估模式
        self.model.eval()
        total_loss, total_correct, num_samples = 0, 0, 0
        TP, FP, FN = 0, 0, 0  # 用于计算 F1 值

        # 禁用梯度计算
        with torch.no_grad():
            progress_bar = tqdm(test_loader, desc=f"Validation Epoch {self.epoch}", leave=False)
            for batch_idx, data in enumerate(progress_bar):
                # 准备数据
                targets = data["targets"].view(-1, 1).to(device, dtype=torch.float)
                ids = data["ids"].to(device, dtype=torch.long)
                mask = data["mask"].to(device, dtype=torch.long)
                token_type_ids = data["token_type_ids"].to(device, dtype=torch.long)

                # 前向传播
                outputs = self.model(ids, mask, token_type_ids)
                loss = loss_fn(outputs, targets)

                # 计算预测结果
                pred_choice = (torch.sigmoid(outputs) > 0.5).float()

                # 更新准确率和损失
                total_correct += pred_choice.eq(targets).sum().item()
                total_loss += loss.item()
                num_samples += targets.size(0)

                # 计算 TP, FP, FN 用于 F1 值
                TP += ((pred_choice == 1) & (targets == 1)).sum().item()
                FP += ((pred_choice == 1) & (targets == 0)).sum().item()
                FN += ((pred_choice == 0) & (targets == 1)).sum().item()

                # 每 10 个 batch 更新进度条
                if batch_idx % 10 == 0:
                    progress_bar.set_postfix({"loss": f"{loss.item():.4f}", "acc": f"{total_correct / num_samples:.4f}"})

        # 计算平均指标
        avg_loss = total_loss / len(test_loader)
        avg_acc = total_correct / num_samples
        precision = TP / (TP + FP + 1e-8)  # 加小值避免除零
        recall = TP / (TP + FN + 1e-8)
        f1 = 2 * (precision * recall) / (precision + recall + 1e-8)

        # 打印验证结果
        print(f"Validation Epoch {self.epoch} completed. Loss: {avg_loss:.4f}, Accuracy: {avg_acc:.4f}, F1: {f1:.4f}")

        # 保存最佳模型
        # if f1 > self.best_f1:
        #     self.best_f1 = f1
        #     save_path = os.path.join(self.save_dir, "best_model.pth")
        #     torch.save(self.model.state_dict(), save_path)
        #     print(f"Best model saved at {save_path} with F1: {f1:.4f}")

        # 返回验证指标
        return avg_acc, avg_loss, recall, precision, 0, 0
        # return acc, avg_loss, recall, precision, throughput, inference_speed*1000



# 主程序
if __name__ == "__main__":
    conf.set(
        seq_len=8,
        batch_size=8,
        num_batch=16,
        lr=0.01,
        weight_decay=0.0001,
        num_epochs=2
    )

    # 加载数据集
    train_dataset_path = "phpProcessor/dataset/1.csv"
    test_dataset_path = "phpProcessor/files/sequence/test/test.csv"
    # train_dataset = PhpDataset("phpProcessor/dataset/1.csv")
    # test_dataset = PhpDataset("phpProcessor/files/sequence/test/test.csv")

    # train_loader = DataLoader(train_dataset, batch_size=conf.batch_size, shuffle=True, num_workers=4, pin_memory=True)
    # test_loader = DataLoader(test_dataset, batch_size=conf.batch_size, shuffle=False, num_workers=4, pin_memory=True)

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
    trainer = Trainer(model, train_dataset_path, test_dataset_path, optimizer, scheduler)

    # 加载已有训练进度
    checkpoint_path = "./model/tmp/checkpoint_epoch_0.pth"
    trainer.load_checkpoint(checkpoint_path)

    # 训练 5 轮（可分批进行）
    for _ in range(5):
        trainer.train_one_epoch()

    # 验证
    trainer.validate()
