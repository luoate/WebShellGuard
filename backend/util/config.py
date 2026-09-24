import torch

class Config:
    def __init__(self):
        # self.seq_len = 512
        # self.batch_size = 64
        # self.num_batch = 32
        # self.lr = 0.01
        # self.weight_decay = 1e-4
        # self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # self.num_workers = 4
        # self.num_epochs = 10
        self.seq_len = 8
        self.batch_size = 8
        self.num_batch = 16
        self.lr = 0.01
        self.weight_decay = 1e-4
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.num_workers = 4
        self.num_epochs = 10
    def set(self, **kwargs):
        """
        动态更新配置参数
        :param kwargs: 传入键值对，例如 set(seq_len=128, batch_size=32)
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                print(f"✔ 更新: {key} = {value}")
            else:
                print(f"⚠️ 警告: {key} 不是一个有效的配置项")

conf = Config()