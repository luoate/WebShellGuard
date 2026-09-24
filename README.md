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