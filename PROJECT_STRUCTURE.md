# WebShellGuard 项目结构

```
WebShellGuard/
│
├── README.md                    # 项目总文档
├── docker-compose.yml           # Docker 编排配置
│
├── backend/                     # ─────────────────────────────
│   ├── app.py                   # Flask 应用入口
│   │
│   ├── WebshellDetector.py      # Webshell 检测核心类
│   ├── model.py                 # CodeBERT 模型定义
│   │
│   ├── router/                  # API 路由模块
│   │   ├── account.py           # 账户相关 API
│   │   ├── auth.py              # 认证相关 API
│   │   ├── dataset.py           # 数据集管理 API
│   │   ├── model.py             # 模型管理 API
│   │   ├── train.py             # 训练相关 API
│   │   ├── upload.py            # 文件上传 API
│   │   └── user.py              # 用户管理 API
│   │
│   ├── phpProcessor/            # PHP 解析模块 (Java ANTLR)
│   │   └── src/
│   │       ├── main/java/       # Java 源代码
│   │       └── test/files/      # 测试用例
│   │
│   ├── codebert/                # CodeBERT 预训练模型文件
│   ├── model/                   # 训练好的模型存储
│   ├── uploads/                 # 用户上传文件目录
│   ├── avatars/                 # 用户头像目录
│   └── util/                    # 工具函数
│
└── frontend/                    # ─────────────────────────────
    ├── package.json             # 依赖配置
    ├── pnpm-lock.yaml           # 锁文件
    ├── vite.config.ts           # Vite 配置 (代理到后端 11451)
    │
    ├── src/                     # 源代码
    │   ├── api/                 # API 调用
    │   │   ├── user.ts          # 用户 API
    │   │   ├── list.ts          # 列表 API
    │   │   ├── routes.ts        # 路由配置
    │   │   └── mock.ts          # Mock 数据
    │   │
    │   ├── views/               # 页面组件
    │   ├── components/          # 公共组件
    │   ├── store/               # 状态管理
    │   ├── router/              # 路由配置
    │   └── styles/              # 样式文件
    │
    ├── public/                  # 静态资源
    ├── mock/                    # Mock 服务
    ├── types/                   # TypeScript 类型定义
    ├── build/                   # 构建配置
    └── .env.development         # 开发环境变量
```

## 前后端通信

前端开发服务器 (localhost:5173) 通过 Vite 代理访问后端 API：

- 请求 `/api/*` → 代理到 `http://127.0.0.1:11451/*`

主要 API 端点：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/login` | POST | 用户登录 |
| `/register` | POST | 用户注册 |
| `/upload` | POST | 上传文件检测 |
| `/train` | POST | 提交训练任务 |
| `/dataset/*` | POST/GET | 数据集管理 |
| `/model/*` | GET/POST | 模型管理 |
| `/history` | GET | 检测历史 |

## 环境要求

### 后端
- Python 3.7+
- CUDA 11.0+ (GPU 训练)
- JDK 11+ (PHP 解析)

### 前端
- Node.js 18+
- pnpm 8+