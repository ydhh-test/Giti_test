# 后处理 API 参考文档

## 1. 概述

后处理模块提供两种使用方式：

1. **命令行脚本** - 适合独立运行、开发调试
2. **服务类 API** - 适合集成到 Python 代码中调用

后处理实现完整的 9 阶段处理流程：

```
Conf 处理 → 小图筛选 → 小图打分 → 纵图拼接 → 横图拼接 → 横图打分 → 装饰边框 → 统计总分 → 整理输出
```

---

## 2. 命令行脚本 API

### scripts/postprocessor.py

#### 使用方法

```bash
source .setup_giti_speckit_py12.sh
python scripts/postprocessor.py --task-id <task_id> [--config <config.json>] [--log <info|debug>]
```

#### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--task-id` | str | 是 | - | 任务唯一标识 |
| `--config` | str | 否 | None | 用户配置文件路径（JSON 格式） |
| `--log` | str | 否 | debug | 日志级别：info 或 debug |

#### 使用示例

**基本用法**
```bash
source .setup_giti_speckit_py12.sh
python scripts/postprocessor.py --task-id 1778457600
```

**带用户配置**
```bash
python scripts/postprocessor.py --task-id 1778457600 --config /path/to/config.json
```

**指定日志级别**
```bash
python scripts/postprocessor.py --task-id 1778457600 --log info
```

#### 输出说明

脚本执行后会调用 `services.postprocessor.postprocessor` 函数，返回：

- **成功**: `(True, result_dict)`
  - `result_dict` 包含 `image_gen_number` 和每张图片的详细信息
- **失败**: `(False, error_dict)`
  - `error_dict` 包含 `err_msg`、`failed_stage`、`task_id`

---

## 3. 服务类 API

### services/postprocessor.py

#### 函数签名

```python
def postprocessor(task_id: str, user_conf: Union[dict, str]) -> tuple[bool, dict]
```

#### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | str | 任务唯一标识，用于定位输入和输出目录 |
| `user_conf` | dict 或 str | 用户配置，可以是字典或 JSON 配置文件路径 |

#### 返回值说明

**成功时：**
```python
(True, {
    "image_gen_number": 3,
    "0": {
        "image_score": 85,
        "image_score_details": {...},
        "image_path": "...",
        ...
    },
    "1": {...},
    "2": {...}
})
```

**失败时：**
```python
(False, {
    "err_msg": "错误信息",
    "failed_stage": "vertical_stitch",  # 失败的阶段名称
    "task_id": "1778457600"
})
```

#### 9 阶段流程

后处理按顺序执行以下 9 个阶段，任何阶段失败会立即返回：

| 阶段 | 名称 | 说明 |
|------|------|------|
| 1 | Conf 处理 | 配置加载和初始化 |
| 2 | 小图筛选 | 过滤小尺寸图片 |
| 3 | 小图打分 | 对小图进行初步评分 |
| 4 | 纵图拼接 | 纵向图片拼接 |
| 5 | 横图拼接 | 横向图片拼接 |
| 6 | 横图打分 | 对横图进行评分 |
| 7 | 装饰边框 | 添加装饰边框 |
| 8 | 统计总分 | 计算综合得分 |
| 9 | 整理输出 | 结果整合和输出 |

---

## 4. 常见使用场景

### 场景 1：标准流程运行

```bash
# 步骤 1: 激活环境
source .setup_giti_speckit_py12.sh

# 步骤 2: 准备数据
python scripts/pieces_2_standard_input.py --task_id 1778457600

# 步骤 3: 运行后处理
python scripts/postprocessor.py --task-id 1778457600

# 步骤 4: 查看结果
ls .results/tasks/1778457600/combine/
```

### 场景 2：使用自定义配置

创建自定义配置文件 `my_config.json`：

```json
{
  "vertical_stitch_conf": {
    "enabled": true
  },
  "decoration_conf": {
    "border_width": 10
  }
}
```

运行：

```bash
python scripts/postprocessor.py --task-id 1778457600 --config my_config.json
```

### 场景 3：集成到 Python 代码

```python
from services.postprocessor import postprocessor

# 方式 1: 使用空配置
success, result = postprocessor(
    task_id="1778457600",
    user_conf={}
)

# 方式 2: 使用配置字典
user_conf = {
    "vertical_stitch_conf": {"enabled": True}
}
success, result = postprocessor(
    task_id="1778457600",
    user_conf=user_conf
)

# 方式 3: 使用配置文件
success, result = postprocessor(
    task_id="1778457600",
    user_conf="/path/to/config.json"
)

# 处理结果
if success:
    print(f"生成图片数量：{result['image_gen_number']}")
    for idx, img_info in result.items():
        if idx.isdigit():
            print(f"图片{idx}: 得分={img_info['image_score']}")
else:
    print(f"失败阶段：{result['failed_stage']}")
    print(f"错误信息：{result['err_msg']}")
```

### 场景 4：错误处理

```python
from services.postprocessor import postprocessor
from pathlib import Path

def run_postprocessing(task_id: str, config_path: str = None):
    """运行后处理并处理错误"""

    # 准备配置
    user_conf = {}
    if config_path:
        if not Path(config_path).exists():
            print(f"配置文件不存在：{config_path}")
            return
        user_conf = config_path

    # 调用后处理
    success, result = postprocessor(task_id, user_conf)

    if success:
        print(f"处理成功！生成 {result['image_gen_number']} 张图片")
        # 处理每张图片的结果
        for key in result:
            if key.isdigit():
                img = result[key]
                print(f"  图片{key}: 得分={img.get('image_score', 'N/A')}")
    else:
        print(f"处理失败！")
        print(f"  失败阶段：{result['failed_stage']}")
        print(f"  错误信息：{result['err_msg']}")

# 使用示例
run_postprocessing("1778457600")
```

---

## 5. 配置项说明

后处理涉及的主要配置项：

| 配置项 | 说明 | 所属阶段 |
|--------|------|----------|
| `small_image_filter_conf` | 小图筛选配置 | 阶段 2 |
| `small_image_score_conf` | 小图打分配置 | 阶段 3 |
| `vertical_stitch_conf` | 纵图拼接配置 | 阶段 4 |
| `horizontal_stitch_conf` | 横图拼接配置 | 阶段 5 |
| `horizontal_score_conf` | 横图打分配置 | 阶段 6 |
| `decoration_conf` | 装饰边框配置 | 阶段 7 |
| `tire_design_width` | 轮胎花纹宽度 | 阶段 7 |
| `decoration_border_alpha` | 装饰边框透明度 | 阶段 7 |

详细配置参数请参考 [docs/configuration.md](docs/configuration.md)

---

## 6. 常见问题

### Q: 如何查看后处理日志？
A: 使用 `--log debug` 参数运行脚本，日志会输出到控制台和 `.logs/` 目录。

### Q: 后处理失败如何定位问题？
A: 返回值中包含 `failed_stage` 字段，指示失败的阶段名称。检查对应阶段的配置和输入数据。

### Q: 如何跳过某个阶段？
A: 在配置中将对应阶段的 `enabled` 设置为 `false`（如果该阶段支持）。

### Q: 输入数据应该放在哪里？
A: 输入数据应放在 `.results/tasks/<task_id>/` 目录下，具体子目录根据阶段不同而不同。

### Q: 输出结果在哪里？
A: 输出结果在 `.results/tasks/<task_id>/combine/` 和 `.results/tasks/<task_id>/rst/` 目录。
