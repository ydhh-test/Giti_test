# rule1to5.py 测试计划

## 测试目标

验证 `rules/rule1to5.py` 横图拼接中间层的功能正确性，包括正常流程和异常处理。

---

## 测试数据

### 数据位置
```
tests/datasets/task_id_test_rule1to5/
├── center_vertical/
│   ├── 2.png
│   └── 5.png
└── side_vertical/
    ├── 0.png
    └── 4.png
```

### 数据说明
- **center_vertical**: 2 张 center 图片
- **side_vertical**: 2 张 side 图片

### 运行时准备
1. 将测试数据复制到 `.results/task_id_test_rule1to5/` 目录
2. 测试执行时使用伪造的 uuid: `test_rule1to5`

---

## 测试用例

### TC-01: 正常横图拼接流程

| 项目 | 内容 |
|------|------|
| **方法名** | `test_process_horizontal_stitch_success` |
| **场景** | 正常流程，有 center/side 图片 |
| **配置** | `{"rib_count": 5, "symmetry_type": "both"}` |
| **预期结果** | flag=True, total_count=34, success_count=34, images=34 |
| **清理策略** | 保留 combine_horizontal 目录（34 张图都保留） |

**验证点**:
1. `flag == True`
2. `result["task_id"] == "test_rule1to5"`
3. `stats["total_count"] == 34`
4. `stats["success_count"] == 34`
5. `len(stats["images"]) == 34`
6. 实际文件存在且数量为 34

---

### TC-02: 空配置异常

| 项目 | 内容 |
|------|------|
| **方法名** | `test_process_horizontal_stitch_empty_conf` |
| **场景** | 传入空配置 conf={} |
| **配置** | `{}` |
| **预期结果** | flag=False, err_msg 包含 "conf 不能为空" |
| **清理策略** | 清理临时文件（如有） |

**验证点**:
1. `flag == False`
2. `result["err_msg"]` 包含 "conf 不能为空"
3. `result["task_id"] == "test_rule1to5"`

---

### TC-03: 无图片异常

| 项目 | 内容 |
|------|------|
| **方法名** | `test_process_horizontal_stitch_no_images` |
| **场景** | center/side 目录为空 |
| **配置** | `{"rib_count": 5, "symmetry_type": "both"}` |
| **预期结果** | flag=False, err_msg 包含 "图片加载失败" |
| **清理策略** | 清理临时文件（如有） |

**验证点**:
1. `flag == False`
2. `result["err_msg"]` 包含 "图片加载失败"
3. `result["task_id"] == "test_rule1to5"`

---

## 测试文件位置

```
tests/unittests/rules/test_rule1to5.py
```

---

## 配置说明

### max_per_mode
- 位置：`DEFAULT_HORIZONTAL_STITCH_CONF["generation"]["max_per_mode"]`
- 默认值：10
- 作用：每种对称模式最大生成数

### 生成数量说明
使用 2 张 center + 2 张 side 图片，配置 `symmetry_type="both"` 时：
- **asymmetric 模式**: 10 张（受 max_per_mode 限制）
- **rotate180 模式**: 8 张
- **mirror 模式**: 8 张
- **mirror_shifted 模式**: 8 张
- **总计**: 34 张

---

## 清理策略总结

| 用例类型 | 清理策略 |
|----------|----------|
| 正例（成功） | 保留输出目录 `.results/task_id_test_rule1to5/combine_horizontal/` |
| 反例（失败） | 清理临时文件 |
