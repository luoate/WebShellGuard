# WebShellGuard

PHP Webshell 检测系统，基于深度学习的静态分析工具。

## 项目简介

WebShellGuard 是一个集 Webshell 检测、模型训练、数据集管理于一体的综合平台。系统采用前后端分离架构，提供友好的 Web 界面进行操作。

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    WebShellGuard                         │
├─────────────────────────────────────────────────────────┤
│  frontend (Vue3 + TypeScript)     backend (Python Flask) │
│  ├── pure-admin 后台框架            ├── Webshell 检测    │
│  ├── 用户认证管理                    ├── 模型训练         │
│  ├── 文件上传检测                    ├── 数据集管理       │
│  ├── 检测历史记录                    ├── 用户管理         │
│  └── 模型评估部署                                     │
└─────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
   Port 5173 (前端)              Port 11451 (后端 API)
```

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.7+
- Conda (推荐用于 Python 环境管理)
- JDK 11+ (用于 PHP 解析预处理)

### 后端部署

```bash
cd backend

# 创建并激活 conda 环境
conda create --name WebShellGuard python=3.7
conda activate WebShellGuard

# 安装 Python 依赖
pip install torch==1.7.1 torchvision==0.8.2 torchaudio==0.7.2 cudatoolkit=11.0 -c pytorch
pip install scikit-learn==0.24.1 transformers==4.0.1 flask flask-cors pymysql
pip install numpy==1.21.0 pandas ssdeep py-tlsh python-magic-bin openai dashscope

# 安装 PHP 解析器依赖 (JDK 11+)
# 下载 antlr4-runtime 并配置

# 启动后端服务
python app.py
```

后端服务运行在 http://127.0.0.1:11451

### 前端部署

```bash
cd frontend

# 安装依赖
pnpm install

# 开发模式启动
pnpm dev

# 构建生产版本
pnpm build
```

前端服务运行在 http://localhost:5173

## 模型文件与训练

本仓库只包含源码，约 7GB 的模型权重、训练数据和生成产物都被 `.gitignore` 排除（GitHub 单文件上限 100MB，仓库无法容纳）。克隆后需要按下表自行准备，否则后端启动或训练会报文件不存在。

| 路径 | 内容 | 体积 | 获取方式 |
|------|------|------|----------|
| `backend/codebert/` | CodeBERT 权重与分词器 | 477MB | 从 HuggingFace 下载，见下 |
| `backend/model/pre_train0.pth` | POS 预训练权重 | 476MB | 本地预训练生成 |
| `backend/model/pre_train0_no_fc.pth` | 去掉 `fc` 层的预训练权重，微调的初始化文件 | 476MB | 由 `pre_train0.pth` 转换 |
| `backend/model/train/*.pth` | 微调后的检测模型 | 每个 476MB | 本地训练生成 |
| `backend/phpProcessor/files/` | PHP 原始样本 + 解析出的 token 序列 JSON | 2.2GB | 由 PHP 解析服务批量生成 |
| `backend/phpProcessor/dataset/*.csv` | 训练用数据集 | 274MB | 由序列 JSON 汇总生成，或从界面上传 |
| `backend/phpProcessor/target/` | Maven 构建产物（jar） | 22MB | `mvn package` 生成 |
| `backend/labels.json`、`backend/label_dict.json` | 节点标签词表，预训练必需 | <10KB | 由 `generateLabels.py` 重建 |
| `backend/upload/`、`backend/avatars/` | 运行时上传文件与用户头像 | ~45MB | 程序自动创建 |

### 1. 下载 CodeBERT

`model.py` 与 `WebshellDetector.py` 都从相对路径 `./codebert` 加载，因此必须在 `backend/` 目录下执行，且目录中要有 `config.json`、`vocab.json`、`merges.txt`、`tokenizer_config.json`、`special_tokens_map.json`、`pytorch_model.bin` 六个文件。

```bash
cd backend

# 方式一：huggingface_hub CLI
pip install -U huggingface_hub
huggingface-cli download microsoft/codebert-base --local-dir codebert

# 方式二：git clone（需先安装 git-lfs）
git lfs install
git clone https://huggingface.co/microsoft/codebert-base codebert
```

### 2. 构建并启动 PHP 解析服务

上传检测与数据集预处理都依赖它：`router/upload.py`、`router/dataset.py` 会向 `http://localhost:9090/api/parser` POST PHP 原文，拿回 `{tokenSequence, stringSequence, tags}`。

```bash
cd backend/phpProcessor
mvn clean package -DskipTests          # JDK 11 + Maven 3.6+，产物在 target/
java -jar target/phpProcessor-1.0-SNAPSHOT.jar
```

批量把一个目录里的 PHP 转成序列 JSON，可改 `src/main/java/com/example/Main.java` 里的输入/输出路径后直接跑 `Main`（内部调用 `FileProcessor.processDirectoryFiles`，按 `1.json`、`2.json` 顺序命名）。预训练语料可用 `CSN_process.py` 从 [CodeSearchNet](https://github.com/github/CodeSearchNet) 的 jsonl 中导出 PHP 文件，样本来源清单见 [backend/README.md](backend/README.md)。

### 3. 生成训练数据集 CSV

训练读取的是 `backend/phpProcessor/dataset/{datasetName}.csv`，列为 `tokenSequence,stringSequence,tags,label`，`label` 取值 `webshell` / `normal`。

```bash
cd backend
# 1) 序列 JSON 按目录汇总成 CSV（脚本里改 a = 'train' / 'test' 选择目录）
python trainJsonToCSV.py          # -> phpProcessor/files/sequence/{train,test}/{train,test}.csv
python preJsonToCSV.py            # 预训练语料同理，改 input_dir/output_file 为 pre_train 或 pre_test

# 2) 放到训练读取的位置
mkdir -p phpProcessor/dataset
cp phpProcessor/files/sequence/train/train.csv phpProcessor/dataset/my_dataset.csv
```

也可以完全走界面/接口采集自己的数据集：`POST /dataset/create` 新建空白数据集（只写入表头）或复制已有数据集，`POST /dataset/upload`（multipart，字段 `dataset`、`sampleType`、`file`）把单个 PHP 文件送去解析并追加为一行样本。原始数据集因原作者与合作方约定未公开，需要用 [backend/README.md](backend/README.md) 列出的公开 Webshell 样本库自行采集。

### 4. 预训练（词性/标签标注任务）

```bash
cd backend
# labels.json / label_dict.json 是预训练用的标签词表，被 .gitignore 排除，需先重建。
# generateLabels.py 默认从 labels.json 读取、写出 label_dict.json，而生成 labels.json
# 的那段（顶部标签列表 + 末尾的 json.dump）是注释状态：首次使用时取消这两处注释、
# 并注释掉读取 labels.json 的那两行，运行一次得到 labels.json（注意补上列表里缺的
# "lambdaFunctionUseVar"）；再恢复原状运行一次得到 label_dict.json。
python generateLabels.py
python pre_train_modify.py # 读 phpProcessor/files/sequence/pre_train.csv、pre_test.csv
```

输出为 `model/pre_train{epoch}.pth`，其中 `pre_train0.pth` 是后续步骤的输入。`BERT_POS` 的 `fc` 输出维度是标签数，与分类器的 `fc(768→1)` 不兼容，需要在 `train_modify.py` 中放开保存行来导出去掉 `fc` 的版本：

```python
# train_modify.py 约 240-246 行
model = load_pretrained_model(model=model, checkpoint_path='model/pre_train0.pth', exclude_layers=['fc'])
torch.save(model.state_dict(), 'model/pre_train_no_fc.pth')
```

注意 `router/train.py` 硬编码的初始化文件名为 `model/pre_train0_no_fc.pth`，与上面的默认输出名不同，需要重命名后再训练：

```bash
mv model/pre_train_no_fc.pth model/pre_train0_no_fc.pth
```

不存在该文件时训练不会报错，只是跳过预训练权重加载（从零开始微调）。

### 5. 微调检测模型

训练按 epoch 逐轮调用，前端「模型训练」页面每轮 POST 一次 `/train`，再 POST `/train/save` 落盘：

```bash
# 单轮训练（每轮一次请求）
curl -X POST http://127.0.0.1:11451/train -H 'Content-Type: application/json' -d '{
  "epoch": 1,
  "modelParams": {"modelName": "my_model", "datasetName": "my_dataset",
                  "optimizer": "adam", "learningRate": 1e-5,
                  "seqLen": 512, "batchSize": 8, "batchNum": 16, "epochs": 10}
}'
```

中间检查点写到 `model/tmp/checkpoint_epoch_{n}.pth`，保存后得到 `model/train/{modelName}.pth`，训练参数与准确率写入 MySQL 的 `model_train` 表，`model/tmp` 会被清空。命令行训练可用 `python train_modify.py` 或 `python test_train.py`。

训练超参默认值在 `backend/util/config.py`，注意其中 `seq_len` 当前为 `8`（论文配置为 512），正式训练前请通过请求参数或修改配置调整。硬件建议 GPU + CUDA 11.0、PyTorch 1.7.1、transformers 4.0.1，与 `backend/README.md` 的环境一致。

### 6. 推理

`WebshellDetector` 默认加载 `model/train_3_good.pth`，检测接口实际使用 `model/train/{模型名}.pth`。两者都需自行训练得到；已有权重换机器时，可用 `GET /model/download?modelName=…` 取回，或放到 GitHub Release 附件里分发。

## 核心功能

### 1. Webshell 检测
- 支持单文件和批量文件检测
- 即时返回检测结果
- 支持 PHP 代码片段分析

### 2. 模型训练
- 自定义数据集上传
- 基于 CodeBERT 的模型训练
- 训练过程可视化
- 模型保存与管理

### 3. 模型评估
- 多维度性能指标分析
- 混淆矩阵可视化
- 评估历史记录

### 4. 用户管理
- 用户注册与认证
- 个人资料管理
- 操作日志记录

## 技术栈

### 前端
- Vue 3 + Composition API
- TypeScript
- Element Plus
- Vite
- Pinia (状态管理)
- Vue Router

### 后端
- Flask
- PyTorch + Transformers (CodeBERT)
- MySQL
- Java ANTLR (PHP 解析)

## 项目结构

```
WebShellGuard/
├── backend/                    # 后端服务
│   ├── app.py                  # Flask 入口
│   ├── WebshellDetector.py     # 检测核心
│   ├── model.py                # 模型定义
│   ├── router/                 # API 路由
│   ├── phpProcessor/           # PHP 解析模块
│   ├── codebert/               # 预训练模型
│   ├── model/                  # 训练好的模型
│   └── uploads/                # 上传文件目录
│
├── frontend/                   # 前端应用
│   ├── src/                    # 源代码
│   ├── public/                 # 静态资源
│   ├── package.json            # 依赖配置
│   └── vite.config.ts          # Vite 配置
│
└── README.md                   # 项目文档
```

## 参考论文

```
@InProceedings{10.1007/978-3-031-10363-6_11,
 author={Baijun Cheng, Yanhui Guo, Yan Ren, Gang Yang, Guosheng Xu},
 title={MSDetector: A Static PHP Webshell Detection System Based on Deep-Learning},
 booktitle="Theoretical Aspects of Software Engineering",
 year={2022},
 publisher={Springer International Publishing},
 pages={155--172}
}
```

## 许可证

MIT License

## 致谢

- 基于 [vue-pure-admin](https://github.com/pure-admin/vue-pure-admin) 构建前端界面
- 检测模型基于 [Microsoft CodeBERT](https://github.com/microsoft/CodeBERT)