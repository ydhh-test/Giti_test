# PR: feat: Rule 16/17 RIB 横向连续性拼接脚本

**分支**: `feature/rule12_16_17`
**目标分支**: `dev`
**创建日期**: 2026-04-02
**状态**: Ready for Review

---

## 一、背景

Rule 16/17 (`rules/rule12_16_17.py` + `algorithms/stitching/rib_continuity_stitch.py`) 在本分支已完成实现与单元测试，但尚未集成到 `services/postprocessor.py` 后处理主流程。

为便于在集成前独立验证和调试拼接效果，本 PR 新增一个独立运行脚本 `scripts/run_rule12_16_17.py`，可直接从命令行调用 `process_rib_continuity`。

---

## 二、变更概览

### 本 PR 变更文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `scripts/run_rule12_16_17.py` | **新增** | Rule 16/17 独立运行脚本 |

### 本分支累计变更（相对 dev）

| 文件 | 操作 | 行数 |
|------|------|------|
| `algorithms/stitching/rib_continuity_stitch.py` | 新增 | +551 |
| `rules/rule12_16_17.py` | 新增 | +232 |
| `tests/unittests/rules/test_rule12_16_17.py` | 新增 | +140 |
| `scripts/run_rule12_16_17.py` | 新增 | +170 |
| `.gitignore` | 修改 | +2/-2 |

---

## 三、脚本功能

### 3.1 命令行接口

```bash
python scripts/run_rule12_16_17.py --task_id <task_id> [options]
```

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--task_id` | ✅ | — | 任务 ID |
| `--base_path` | 否 | `.results` | 基础结果路径 |
| `--input_dir` | 否 | `split` | split 子目录名 |
| `--output_dir` | 否 | `rule12_16_17` | 输出子目录名 |
| `--continuity_mode` | 否 | `none` | 中间 RIB 连续性模式 |
| `--groove_width_mm` | 否 | `10.0` | 主沟宽度 (mm) |
| `--pixel_per_mm` | 否 | `2.0` | 像素/毫米比例 |
| `--blend_width` | 否 | `10` | 边缘融合宽度 (像素) |
| `--edge_rib12` | 否 | 不控制 | RIB1-RIB2 连续概率 0.0~1.0 |
| `--edge_rib45` | 否 | 不控制 | RIB4-RIB5 连续概率 0.0~1.0 |
| `--group_filter` | 否 | 全部 | 只处理指定分组（可多个） |
| `--pretty` | 否 | false | 以缩进格式打印 JSON 结果 |

`--continuity_mode` 可选值：`none` / `RIB2-RIB3` / `RIB3-RIB4` / `RIB2-RIB3-RIB4`

### 3.2 输入输出路径

```
输入:
  .results/task_id_<task_id>/split/center_horz/*.png
  .results/task_id_<task_id>/split/side_horz/*.png

输出:
  .results/task_id_<task_id>/rule12_16_17/tread_<group>.png
  .results/task_id_<task_id>/rule12_16_17/debug_<group>/   (过程图)
```

### 3.3 输出示例

```bash
$ python scripts/run_rule12_16_17.py --task_id abc123 \
    --continuity_mode RIB2-RIB3 \
    --edge_rib12 0.8 --edge_rib45 0.5 --pretty
```

```json
{
  "task_id": "abc123",
  "output_dir": ".results/task_id_abc123/rule12_16_17",
  "directories": {
    "rule12_16_17": {
      "total_count": 3,
      "processed_count": 3,
      "success_count": 3,
      "failed_count": 0,
      "skipped_count": 0,
      "images": {
        "tread_img_001.png": {
          "status": "success",
          "continuity_map": {"RIB2-RIB3": "continuous", "RIB3-RIB4": "independent"},
          ...
        }
      }
    }
  }
}

[rule12_16_17] 合计: 3  成功: 3  失败: 0  跳过: 0

输出目录: .results/task_id_abc123/rule12_16_17
```

---

## 四、未集成项说明

本 PR **不** 修改 `services/postprocessor.py`。Rule 16/17 后续集成到后处理流程将作为独立 PR 提交，届时需要：

1. 在 `services/postprocessor.py` 新增 `_rib_continuity_stitch` 阶段
2. 在 `configs/user_config.py` 添加 `DEFAULT_RIB_CONTINUITY_CONF`
3. 在 `configs/complete_config.py` / `module_config.py` 注册配置项

---

## 五、测试

### 5.1 单元测试（已有）

```bash
pytest tests/unittests/rules/test_rule12_16_17.py -v
```

覆盖 4 × 2 × 2 = **16 种参数组合**（center_mode × edge_rib12 × edge_rib45）。

### 5.2 脚本冒烟测试

```bash
# 使用测试任务数据验证脚本可正常运行
python scripts/run_rule12_16_17.py --task_id 1778457600 --pretty

# 测试退出码：成功应为 0
echo $?
```

---

## 六、Checklist

- [x] 新增 `scripts/run_rule12_16_17.py`
- [x] 脚本不修改后处理主流程
- [x] 支持全部 rule12_16_17 的配置参数
- [x] 对概率参数 `--edge_rib12` / `--edge_rib45` 做合法性校验
- [x] 失败时 `sys.exit(1)` 返回非零退出码
- [x] JSON 结果通过 stdout 输出，便于管道接入
- [ ] 集成测试（待后续 PR 集成到 postprocessor 后补充）
