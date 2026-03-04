# Postprocessor 入口函数实现计划

## 函数签名
```python
def postprocessor(task_id: str, conf: dict, user_conf: dict) -> tuple[int, dict]:
    ...
```

## 大流程

### 0. Conf处理
- **输入**: conf, user_conf
- **输出**: merged_conf (dict)
- **说明**: 将 user_conf 合并到 conf 中

### 1. 小图筛选 (small_image_filter)
- **输入**: task_id, small_image_filter_conf (从 merged_conf 中提取)
- **输出**: flag (bool), small_image_filter_details (dict)
- **说明**: flag 表示成功/失败，失败时 details 包含 err_msg

### 2. 纵图拼接 (vertical_stitch)
- **输入**: task_id, vertical_stitch_conf (从 merged_conf 中提取)
- **输出**: flag (bool), vertical_stitch_details (dict)

### 3. 横图拼接 (horizontal_stitch)
- **输入**: task_id, horizontal_stitch_conf (从 merged_conf 中提取)
- **输出**: flag (bool), horizontal_stitch_details (dict)

### 4. 统计总分 (calculate_total_score)
- **输入**: task_id, calculate_total_score_conf (从 merged_conf 中提取)
- **输出**: flag (bool), calculate_total_score_details (dict)
- **说明**: 最终分数从 conf 中获取，当前不实装

### 5. 整理输出 (organize_output)
- **说明**: 暂时不实现，留注释

## 流程控制逻辑

- 每个步骤失败时立即返回，不继续后续流程
- 返回 score=0, details={err_msg: "xxx", failed_stage: "xxx"}

## 配置结构

merged_conf 中包含以下固定 key：
- `small_image_filter_conf`
- `vertical_stitch_conf`
- `horizontal_stitch_conf`
- `calculate_total_score_conf`
