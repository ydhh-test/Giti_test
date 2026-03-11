# 计划：scripts/pieces_2_standard_input.py

## 目标
编写一个图片批量处理脚本，将指定 task_id 下的 center 和 side 目录中的所有 PNG 图片 resize 为 128x128，并按顺序重命名保存到对应的输出目录。

---

## 输入输出

| 类型 | 内容 |
|------|------|
| **输入** | `task_id` (字符串)，通过命令行参数 `--task_id` 传入 |
| **输出** | 成功处理的图片总数（终端打印） |

---

## 处理流程

```
1. 解析命令行参数 --task_id
   ↓
2. 构建路径
   - source_center: .results/task_id_<task_id>/pieces/center
   - source_side: .results/task_id_<task_id>/pieces/side
   - target_center: .results/task_id_<task_id>/center_inf
   - target_side: .results/task_id_<task_id>/side_inf
   ↓
3. 验证源目录是否存在（不存在则抛出异常）
   ↓
4. 清空/创建输出目录
   ↓
5. 处理 center 目录：
   - 获取所有 .png 文件
   - 按文件名字典序排序
   - 依次读取 → resize(128, 128) → 保存为 0.png, 1.png, 2.png...
   ↓
6. 处理 side 目录（同上）
   ↓
7. 打印统计信息
```

---

## 技术规格

### 依赖
- `Pillow` - 图像处理（用户确认已安装）
- `argparse` - 命令行参数解析（标准库）
- `pathlib` - 路径处理（标准库）

### 图片处理参数
| 项目 | 设置 |
|------|------|
| 目标尺寸 | 128x128 |
| 缩放策略 | 强制拉伸（不考虑原图比例） |
| 输出格式 | PNG（默认参数保存） |

### 排序规则
- 源文件按**文件名字典序**排序

### 错误处理
- 源目录不存在：抛出异常并退出
- 输出目录：执行前先清空

---

## 调用方式

```bash
python scripts/pieces_2_standard_input.py --task_id <task_id>
```

---

## 输出示例

```
Successfully processed 15 images (center: 8, side: 7)
```

---

## 目录结构假设

```
.results/
└── task_id_<task_id>/
    ├── pieces/
    │   ├── center/
    │   │   ├── image1.png
    │   │   ├── image2.png
    │   │   └── ...
    │   └── side/
    │       ├── image1.png
    │       ├── image2.png
    │       └── ...
    ├── center_inf/    (输出目录，脚本创建/清空)
    └── side_inf/      (输出目录，脚本创建/清空)
```

---

## 实现清单

- [ ] 创建 `scripts/pieces_2_standard_input.py`
- [ ] 实现命令行参数解析
- [ ] 实现路径构建和验证
- [ ] 实现图片处理逻辑
- [ ] 添加执行权限
- [ ] 测试验证
