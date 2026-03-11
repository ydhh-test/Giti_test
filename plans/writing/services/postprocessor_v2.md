# 后处理流程调整计划 (Postprocessor V2)

**创建日期:** 2026-03-11
**状态:** 待实施
**负责人:** 研发团队

---

## 一、目标

重构 `services/postprocessor.py` 的 `postprocessor` 函数，实现新的接口和 9 阶段处理流程。

---

## 二、接口设计

### 2.1 函数签名
```python
def postprocessor(task_id: str, user_conf: dict | str) -> tuple[bool, dict]
```

### 2.2 输入说明
| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | `str` | 任务唯一标识 |
| `user_conf` | `dict | str` | 用户配置（dict 或 JSON 文件路径） |

### 2.3 输出说明

**成功时：**
```python
(True, {
    "image_gen_number": 10,
    "0": {
        "image_score": 85.5,
        "image_path": "/path/to/image.png",
        "image_score_details": "/path/to/score_details.json"
    },
    "1": {...},
    ...
})
```

**失败时：**
```python
(False, {
    "err_msg": "错误描述",
    "failed_stage": "conf_processing",
    "task_id": "xxx"
})
```

---

## 三、实施步骤

### Step 1: 实现配置处理模块

**文件：** `services/postprocessor.py`

**任务：**

1. 实现 `_load_user_conf(user_conf: dict | str) -> dict` 内部函数
   - 如果 `user_conf` 是 `dict`：直接返回
   - 如果 `user_conf` 是 `str`：读取并解析 JSON 文件
   - 类型校验：既不是 dict 也不是 str 则抛出异常
   - JSON 解析失败则抛出异常

2. 实现 `_merge_conf_from_complete_config(task_id: str, user_conf: dict) -> dict` 内部函数
   - 实例化 `CompleteConfig`
   - 调用 `to_legacy_dict()` 获取基础配置
   - 用 `user_conf` 覆盖同名项
   - 返回合并后的配置

3. 实现 `_create_error_response(task_id: str, err_msg: str, failed_stage: str) -> tuple[bool, dict]` 内部函数
   - 统一返回错误格式

---

### Step 2: 重构主入口函数

**文件：** `services/postprocessor.py`

**任务：**
```python
def postprocessor(task_id: str, user_conf: dict | str) -> tuple[bool, dict]:
    # Stage 1: Conf 处理
    try:
        user_conf_dict = _load_user_conf(user_conf)
        merged_conf = _merge_conf_from_complete_config(task_id, user_conf_dict)
    except Exception as e:
        return _create_error_response(task_id, str(e), "conf_processing")

    # Stage 2: 小图筛选
    small_image_filter_conf = merged_conf.get("small_image_filter_conf", {})
    flag, details = _small_image_filter(task_id, small_image_filter_conf)
    if not flag:
        return False, {**details, "failed_stage": "small_image_filter", "task_id": task_id}

    # Stage 3: 小图打分
    small_image_score_conf = merged_conf.get("small_image_score_conf", {})
    flag, details = _small_image_score(task_id, small_image_score_conf)
    if not flag:
        return False, {**details, "failed_stage": "small_image_score", "task_id": task_id}

    # Stage 4: 纵图拼接
    vertical_stitch_conf = merged_conf.get("vertical_stitch_conf", {})
    flag, details = _vertical_stitch(task_id, vertical_stitch_conf)
    if not flag:
        return False, {**details, "failed_stage": "vertical_stitch", "task_id": task_id}

    # Stage 5: 横图拼接
    horizontal_stitch_conf = merged_conf.get("horizontal_stitch_conf", {})
    flag, details = _horizontal_stitch(task_id, horizontal_stitch_conf)
    if not flag:
        return False, {**details, "failed_stage": "horizontal_stitch", "task_id": task_id}

    # Stage 6: 横图打分
    horizontal_image_score_conf = merged_conf.get("horizontal_image_score_conf", {})
    flag, details = _horizontal_image_score(task_id, horizontal_image_score_conf)
    if not flag:
        return False, {**details, "failed_stage": "horizontal_image_score", "task_id": task_id}

    # Stage 7: 装饰边框
    decoration_conf = merged_conf.get("decoration_conf", {})
    flag, details = _add_decoration_borders(task_id, decoration_conf, merged_conf)
    if not flag:
        return False, {**details, "failed_stage": "decoration_borders", "task_id": task_id}

    # Stage 8: 统计总分
    calculate_total_score_conf = merged_conf.get("calculate_total_score_conf", {})
    flag, details = _calculate_total_score(task_id, calculate_total_score_conf)
    if not flag:
        return False, {**details, "failed_stage": "calculate_total_score", "task_id": task_id}

    # Stage 9: 整理输出
    standard_input_conf = merged_conf.get("standard_input_conf", {})
    flag, details = _standard_input(task_id, standard_input_conf)
    if not flag:
        return False, {**details, "failed_stage": "standard_input", "task_id": task_id}

    return True, details
```

---

### Step 3: 实现 9 个阶段的内部函数

所有阶段函数签名统一为：
```python
def _stage_name(task_id: str, conf: dict) -> tuple[bool, dict]:
```

| 阶段 | 函数名 | 职责 | 实现状态 |
|------|--------|------|----------|
| 1 | `_load_user_conf` | 加载用户配置 | 需实现 |
| 2 | `_small_image_filter` | 小图筛选 | 空函数 |
| 3 | `_small_image_score` | 小图打分 | 空函数 |
| 4 | `_vertical_stitch` | 纵图拼接 | 空函数 |
| 5 | `_horizontal_stitch` | 横图拼接 | 空函数 |
| 6 | `_horizontal_image_score` | 横图打分 | 空函数 |
| 7 | `_add_decoration_borders` | 装饰边框 | 需适配新返回格式 |
| 8 | `_calculate_total_score` | 统计总分 | 空函数 |
| 9 | `_standard_input` | 整理输出 | 空函数 |

**空函数统一返回格式：**
```python
def _stage_name(task_id: str, conf: dict) -> tuple[bool, dict]:
    """阶段说明"""
    # TODO: 实现具体逻辑
    return True, {"image_gen_number": 0, "task_id": task_id}
```

---

### Step 4: 适配现有 `_add_decoration_borders` 函数

**文件：** `services/postprocessor.py`

**任务：**
- 保留现有逻辑
- 修改返回格式，使其符合新的输出格式要求
- 确保返回的 `details` 包含 `image_gen_number` 和每张图片的信息

---

### Step 5: 更新配置文件

**文件：** `configs/postprocessor_config.py`

**任务：**
- 添加新阶段的配置项（如 `small_image_score_conf`, `horizontal_image_score_conf`, `standard_input_conf` 等）
- 保持配置结构与新的阶段命名一致

---

### Step 6: 编写单元测试

**文件：** `tests/unittests/test_postprocessor.py`（或新建）

**测试用例：**

| 测试项 | 描述 |
|--------|------|
| `test_user_conf_dict_input` | 测试 dict 类型输入 |
| `test_user_conf_json_path_input` | 测试 JSON 文件路径输入 |
| `test_user_conf_invalid_type` | 测试无效类型输入（应报错） |
| `test_user_conf_invalid_json` | 测试无效 JSON 文件（应报错） |
| `test_complete_config_merge` | 测试配置合并逻辑 |
| `test_error_response_format` | 测试错误返回格式 |
| `test_success_response_format` | 测试成功返回格式 |
| `test_stage_failure_propagation` | 测试各阶段失败的处理 |

---

## 四、文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `services/postprocessor.py` | 重构 | 主入口函数和 9 个阶段函数 |
| `configs/postprocessor_config.py` | 修改 | 添加新阶段配置 |
| `tests/unittests/test_postprocessor.py` | 新增 | 单元测试 |

---

## 五、阶段流程图

```
postprocessor(task_id, user_conf)
       │
       ▼
┌─────────────────────┐
│ 1. Conf 处理          │
│ _load_user_conf     │
│ _merge_conf_from_   │
│ _complete_config    │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ 2. 小图筛选          │
│ _small_image_filter │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ 3. 小图打分          │
│ _small_image_score  │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ 4. 纵图拼接          │
│ _vertical_stitch    │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ 5. 横图拼接          │
│ _horizontal_stitch  │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ 6. 横图打分          │
│ _horizontal_image_  │
│ score               │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ 7. 装饰边框          │
│ _add_decoration_    │
│ borders             │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ 8. 统计总分          │
│ _calculate_total_   │
│ score               │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ 9. 整理输出          │
│ _standard_input     │
└─────────────────────┘
       │
       ▼
   返回 (flag, details)
```

---

## 六、风险与注意事项

1. **向后兼容性**：现有调用 `postprocessor` 的代码需要更新为新的接口
2. **配置一致性**：确保 `CompleteConfig` 中所有子配置都能正确合并
3. **错误处理**：每个阶段都需要妥善处理异常，避免崩溃
4. **图片编号排序**：最终输出需要按得分排序（高分优先，同分按文件名字母序）

---

## 七、设计决策记录

### 7.1 配置处理
- `conf` 应该从 `configs` 里拼出来，不应该传入
- 用 `user_conf` 里给的，覆盖拼出 `conf` 里同名的部分
- `CompleteConfig` 实例化获取基础配置

### 7.2 JSON 路径支持
- 如果传入的是 `str` 类型（json_path），函数内部负责读取和解析 JSON 文件
- 需要类型校验：既不是 dict 也不是 str 则报错
- 仅包含用户自定义的配置项
- 不支持混合模式（要么传 dict，要么传 json_path）

### 7.3 返回值 flag 含义
- `flag: bool` 表示整个后处理流程是否成功
- 不需要"部分成功"，某个阶段失败了，后边的无法进行
- 某个阶段失败时，继续执行到最后（根据后续澄清）

### 7.4 返回格式
- 成功：`details={image_gen_number: <总数>, <序号>:{image_score, image_path, image_score_details}}`
- 失败：`details={err_msg=<err_msg>, failed_stage=<stage>, task_id=<task_id>}`
- 图片序号采用得分序（高分的数字小，同分的看文件名的字母序）
- 图片编号从 0 开始，使用字符串 "0", "1", "2"...

### 7.5 阶段命名
- 所有阶段函数名前加 `_`，作为内部函数
- 生产时不暴露，测试时可以暴露

### 7.6 数据传递
- 每个 stage 的 `details` 不需要传递给下一个 stage
- 关键信息会在具体实现里，通过 conf 给定的名字保存
- `details` 主要是为了 debug 用的
- 每个阶段都需要尝试返回当前已知的图片信息

---

## 八、附录：阶段名称映射

| 阶段序号 | 阶段名称 | 内部函数名 | 配置 key |
|----------|----------|------------|----------|
| 1 | Conf 处理 | `_load_user_conf` + `_merge_conf_from_complete_config` | - |
| 2 | 小图筛选 | `_small_image_filter` | `small_image_filter_conf` |
| 3 | 小图打分 | `_small_image_score` | `small_image_score_conf` |
| 4 | 纵图拼接 | `_vertical_stitch` | `vertical_stitch_conf` |
| 5 | 横图拼接 | `_horizontal_stitch` | `horizontal_stitch_conf` |
| 6 | 横图打分 | `_horizontal_image_score` | `horizontal_image_score_conf` |
| 7 | 装饰边框 | `_add_decoration_borders` | `decoration_conf` |
| 8 | 统计总分 | `_calculate_total_score` | `calculate_total_score_conf` |
| 9 | 整理输出 | `_standard_input` | `standard_input_conf` |
