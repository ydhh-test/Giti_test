# 配置系统指南

## 配置目录结构

```
configs/
├── __init__.py              # 包初始化，导出 CompleteConfig
├── base_config.py           # 基础系统配置
├── complete_config.py       # 完整配置（聚合所有子配置）
├── module_config.py         # 模块配置
├── postprocessor_config.py  # 后处理配置
├── rules_config.py          # 规则配置
└── user_config.py           # 用户自定义配置
```

---

## 各配置文件说明

### base_config.py - 基础系统配置

包含系统级配置参数：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `base_path` | str | "." | 基础路径，默认为当前工作目录 |
| `input_path` | str | "input" | 输入路径 |
| `output_path` | str | "output" | 输出路径 |
| `temp_path` | str | "temp" | 临时文件路径 |
| `log_path` | str | "logs" | 日志文件路径 |
| `max_image_size` | tuple | (4096, 4096) | 最大图片尺寸（像素） |
| `max_file_size_mb` | int | 50 | 最大文件大小（MB） |
| `max_batch_size` | int | 100 | 最大批量处理大小 |
| `concurrent_workers` | int | 4 | 并发工作线程数 |
| `enable_gpu` | bool | False | 是否启用 GPU 加速 |

### postprocessor_config.py - 后处理配置

包含后处理 9 阶段流程的各阶段配置：

#### 小图筛选配置 (small_image_filter_conf)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `min_width` | int | 100 | 最小宽度（像素） |
| `min_height` | int | 100 | 最小高度（像素） |
| `min_area` | int | 10000 | 最小面积（像素²） |

#### 纵图拼接配置 (vertical_stitch_conf)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `rib_count` | int | 4 | RIB 数量 |
| `blend_width` | int | 10 | 边缘融合宽度（像素） |

#### 横图拼接配置 (horizontal_stitch_conf)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `rib_count` | int | 5 | RIB 数量（4 或 5） |
| `symmetry_type` | str | "rotate180" | 对称类型 |
| `center_size` | tuple | (200, 1241) | center RIB 目标尺寸（宽，高） |
| `side_size` | tuple | (400, 1241) | side RIB 目标尺寸（宽，高） |
| `blend_width` | int | 10 | 边缘融合宽度（像素） |
| `max_per_mode` | int | 10 | 每种模式最大生成数 |

#### 装饰边框配置 (decoration_conf)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `decoration_style` | str | "simple" | 装饰风格 |
| `decoration_border_alpha` | float | 0.5 | 装饰边框透明度 |
| `tire_design_width` | int | 200 | 轮胎花纹宽度 |

### rules_config.py - 规则配置

包含业务规则相关配置：

- 规则编号与配置映射
- 规则参数说明
- 连续性检测配置

### user_config.py - 用户自定义配置

包含用户可自定义的配置项：

- 默认配置值
- 配置覆盖优先级说明

---

## 配置使用方式

### 方式 1: 代码中直接引用

```python
from configs.postprocessor_config import VERTICAL_STITCH_CONFIG

# 直接使用配置字典
config = VERTICAL_STITCH_CONFIG
print(f"RIB 数量：{config['rib_count']}")
```

### 方式 2: 通过 CompleteConfig 获取

```python
from configs import CompleteConfig

# 实例化 CompleteConfig 获取完整配置
cc = CompleteConfig()
conf = cc.to_legacy_dict()

# 访问配置项
print(conf['vertical_stitch_conf'])
print(conf['rules_config'])
```

### 方式 3: 用户配置覆盖

在后处理 API 中使用：

```python
from services.postprocessor import postprocessor

# 用户配置只覆盖需要的项
user_conf = {
    "vertical_stitch_conf": {
        "enabled": True,
        "rib_count": 5  # 覆盖默认值
    }
}

success, result = postprocessor(
    task_id="1778457600",
    user_conf=user_conf
)
```

### 方式 4: 使用 JSON 配置文件

创建 `my_config.json`：

```json
{
  "vertical_stitch_conf": {
    "rib_count": 5,
    "blend_width": 15
  },
  "decoration_conf": {
    "decoration_style": "custom"
  }
}
```

命令行运行：

```bash
python scripts/postprocessor.py --task-id 1778457600 --config my_config.json
```

---

## 配置优先级

```
用户配置 > 子配置 > 基础配置
```

1. **用户配置**：通过 `user_conf` 参数传入的配置优先级最高
2. **子配置**：各模块配置文件中定义的默认值
3. **基础配置**：`base_config.py` 中的系统级配置

---

## 配置规范

### 路径配置原则

- 所有配置路径指向 `.results/` 目录（项目根目录的子目录）
- 测试数据由测试准备函数从 `tests/datasets/` 拷贝到 `.results/`
- 功能函数对 `.results/` 目录进行操作，不直接操作 `tests/datasets/`
- 使用 `Path` 进行路径拼接，确保跨平台兼容（Windows/Linux/macOS）

### 配置命名规范

- 配置字典使用大写字母命名（如 `VERTICAL_STITCH_CONFIG`）
- 配置键使用小写字母和下划线（如 `rib_count`）
- 配置模块使用小写字母和下划线（如 `postprocessor_config.py`）

---

## 常见配置场景

### 场景 1: 修改纵图拼接参数

```python
user_conf = {
    "vertical_stitch_conf": {
        "rib_count": 5,       # 修改 RIB 数量
        "blend_width": 15     # 修改融合宽度
    }
}
```

### 场景 2: 修改横图对称类型

```python
user_conf = {
    "horizontal_stitch_conf": {
        "symmetry_type": "mirror",  # 修改对称类型
        "max_per_mode": 20          # 修改最大生成数
    }
}
```

### 场景 3: 修改装饰边框样式

```python
user_conf = {
    "decoration_conf": {
        "decoration_border_alpha": 0.8,  # 修改透明度
        "tire_design_width": 300         # 修改花纹宽度
    }
}
```

---

## 完整配置示例

```python
from configs import CompleteConfig

# 获取完整配置
cc = CompleteConfig()
full_conf = cc.to_legacy_dict()

# 配置结构
"""
{
    'system_config': {...},
    'small_image_filter_conf': {...},
    'small_image_score_conf': {...},
    'vertical_stitch_conf': {...},
    'horizontal_stitch_conf': {...},
    'horizontal_image_score_conf': {...},
    'decoration_conf': {...},
    'calculate_total_score_conf': {...},
    'standard_input_conf': {...},
    'rules_config': {...}
}
"""
```

---

## 相关文件

- [后处理 API 文档](api_postprocessor.md) - API 使用说明
- [部署指南](deployment.md) - 部署和运行说明
