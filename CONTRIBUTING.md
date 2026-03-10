# 贡献指南

感谢您对轮胎AI模式识别项目的关注！

## 贡献方式

### 报告问题
- 使用 GitHub Issues 报告 bug
- 提供重现步骤和错误信息
- 附上相关日志或截图

### 提交代码
1. Fork 项目仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

### 文档改进
- 修正错别字和语法错误
- 补充缺失的文档
- 添加使用示例

## 开发流程

### 环境准备

```bash
# 1. Fork 并克隆项目
git clone <your-fork-url>
cd giti-tire-ai-pattern

# 2. 安装依赖
pip install -r requirements.txt
```

### 分支策略

- `main` - 主分支，稳定版本
- `dev` - 开发分支
- `feature/*` - 新功能分支
- `bugfix/*` - bug修复分支
- `hotfix/*` - 紧急修复分支

### 提交规范

#### Commit Message 格式

```
<type>(<scope>): <subject>

<body>
```

#### Type 类型

- `feat`: 新功能
- `fix`: 修复bug
- `test`: 添加测试
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `chore`: 构建/工具相关

#### 示例

```
feat(analyzer): 添加新的连续性检测算法

- 实现基于深度学习的检测方法
- 提升检测准确率至98%
- 添加可视化支持

Closes #123
```

## 代码规范

### Python 代码风格

- 遵循 PEP 8 编码规范
- 使用 4 空格缩进
- 最大行长度 120 字符
- 使用类型注解

### 注释规范

```python
def function_name(param1: str, param2: int) -> bool:
    """
    函数功能描述

    Args:
        param1: 参数1的说明
        param2: 参数2的说明

    Returns:
        返回值说明

    Raises:
        异常类型: 异常说明
    """
    pass
```

## 测试要求

### 单元测试

- 为新功能编写单元测试
- 使用 pytest 框架

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/unittests/algorithms/detection/test_pattern_continuity.py -v
```

## Pull Request 流程

### PR 前检查

- [ ] 代码通过所有测试
- [ ] 代码符合项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] Commit message 符合规范

### PR 审查流程

1. 代码审查者进行代码审查
2. 提出修改建议（如有）
3. 贡献者根据建议修改代码
4. 审查通过后合并代码

## 常见问题

### Q: 如何选择要贡献的issue？

A: 查看 GitHub Issues 中标记为 `good first issue` 或 `help wanted` 的issue。

### Q: 如果我的PR被拒绝了怎么办？

A: 仔细查看审查意见，进行相应修改，然后重新提交。

### Q: 如何获取帮助？

A: 通过 GitHub Issues 提问或联系项目维护者。

## 技术支持

- **GitHub Issues**：https://github.com/your-org/giti-tire-ai-pattern/issues

---

**最后更新**：2026-03-08
