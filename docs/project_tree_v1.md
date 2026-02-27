giti-tire-ai-pattern/
├── configs/                      # 配置管理
│   ├── __init__.py
│   ├── base_config.py            # 基础配置（路径、默认参数）
│   ├── postprocessor_config.py   # 基础配置（路径、默认参数）
│   └── rules_config.py           # 规则的配置
├── docs/                         # 文档
├── services/                     # 业务逻辑层：任务拆解的核心实现
│   ├── __init__.py
│   ├── preprocessor.py           # 用户输入数据的预处理（去灰边、CMYK转换）
│   ├── inference.py              # 花纹块生成调用（中部/边缘）
│   ├── postprocessor.py          # 后处理（后处理主流程）（拼RIB、对称性实现）
│   ├── analyzers.py              # 几何合理性分析（周期检测、海陆比）
│   └── scorer.py                 # 评分系统（业务/美感评分）
├── utils/                        # 公共函数库：与业务无关的基础功能
│   ├── __init__.py
│   ├── io_utils.py               # 文件读写、文件夹遍历
│   ├── cv_utils.py               # 基础图像操作封装（缩放、裁剪、颜色转换）
│   └── logger.py                 # 标准化日志系统
├── tests/                        # 测试用例
│   ├── datasets                  # 测试图片
├── scripts/                      # 脚本工具（训练启动、数据扩增脚本）
└── README.md                     # 项目说明文档
