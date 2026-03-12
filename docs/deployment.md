# 部署指南

## 环境要求

- **Python**: 3.12+
- **操作系统**: Linux / macOS / Windows
- **内存**: 建议 8GB 以上

## 部署步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd giti-tire-ai-pattern
```

### 2. 创建虚拟环境(或conda)

```bash
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 验证安装

```bash
python -c "import cv2; import numpy; import PIL; print('依赖安装成功')"
```

### 5. 配置检查

- 确认 `configs/` 目录下的配置文件已根据实际需求调整
- 确认输入/输出目录路径配置正确（在 `configs/base_config.py` 中）

## 运行方式

项目提供三个主要脚本：

### 测试预处理（可选）

```bash
pytest tests/unittests/services/test_preprocessor.py -v
```

### 准备输入数据

```bash
python scripts/pieces_2_standard_input.py --task_id <TASK_ID>
```

参数说明：
- `--task_id`: 任务 ID，用于定位输入和输出目录

### 运行后处理

```bash
python scripts/postprocessor.py --task-id <TASK_ID>
```

参数说明：
- `--task-id`: 任务 ID
- `--user-conf`: （可选）用户配置文件路径

## 输出位置

- 结果输出到 `.results/task_id_<TASK_ID>/` 目录
- 主要输出文件：
  - `.results/task_id_<TASK_ID>/combine/` - 拼接后的图片

## 常见问题

### Q: 如何修改输入/输出目录？
A: 编辑 `configs/base_config.py` 中的路径配置。

### Q: 如何使用自定义配置？
A: 运行脚本时添加 `--user-conf` 参数指定配置文件路径。

### Q: 测试数据在哪里？
A: 测试数据位于 `tests/datasets/` 目录，功能代码操作 `.results/` 目录。
