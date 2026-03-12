# 花纹连续性检测功能实现计划

## 任务描述
实现一个检测输入灰度图花纹连续性的功能。竖线、斜线、横线只要出现在边缘，且上下对不齐，就输出True，否则输出False。

## 需求说明
### 连续性判定规则
1. **空边缘情况**：上下边缘4像素高度内无任何深色线条（黑/灰）→ 连续（返回False）
2. **有线条情况**：
   - 检测上下边缘4像素内的所有线条
   - 计算每条线的x轴中心位置
   - 将上下边缘的线条按x中心位置匹配（最近匹配）
   - 检查每对匹配线条的x中心差值
   - 所有差值≤4像素 → 连续（返回False）
   - 任一差值>4像素 → 不连续（返回True）

### 测试用例
- **正例1**: `tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/1.png` (期望返回True)
- **正例2**: `tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/2.png` (期望返回True)
- **反例1**: `tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/3.png` (期望返回False)

## 单元测试设计
### 测试框架结构
```python
import cv2
import pytest

def test_positive_case_1():
    """测试正例1：花纹不连续，应返回True"""
    pass

def test_positive_case_2():
    """测试正例2：花纹不连续，应返回True"""
    pass

def test_negative_case_1():
    """测试反例1：花纹连续，应返回False"""
    pass
```

### 测试覆盖原则
- 测试只校验函数返回值的正确性
- 正例 → 期望返回 True
- 反例 → 期望返回 False
- 不测试具体的4像素阈值等实现细节

### 简单的测试实现思路
```python
def test_positive_case_1():
    image = load_test_image("1.png")
    result = detect_pattern_continuity(image)
    assert result == True  # 只断言返回值

def test_negative_case_1():
    image = load_test_image("3.png")
    result = detect_pattern_continuity(image)
    assert result == False  # 只断言返回值
```

### 测试数据组织
```
tests/unittests/services/test_analyzers.py  # 单元测试文件位置
tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/
├── 1.png  # 正例1
├── 2.png  # 正例2
└── 3.png  # 反例1
```

### 完整单元测试实现
```python
import cv2
import pytest

# 图片路径配置
TEST_DATA_PATH = "tests/datasets/task_id_9f8d7b6a-5e4d-3c2b-1a09-876543210fed/center_inf/"

def load_test_image(filename):
    """加载测试图片"""
    image_path = f"{TEST_DATA_PATH}{filename}"
    return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

def test_positive_case_1():
    """测试正例1：花纹不连续"""
    image = load_test_image("1.png")
    result = detect_pattern_continuity(image)
    assert result == True

def test_positive_case_2():
    """测试正例2：花纹不连续"""
    image = load_test_image("2.png")
    result = detect_pattern_continuity(image)
    assert result == True

def test_negative_case_1():
    """测试反例1：花纹连续"""
    image = load_test_image("3.png")
    result = detect_pattern_continuity(image)
    assert result == False
```

## 实施步骤

### 步骤1：创建单元测试文件
- 在 `tests/unittests/services/test_analyzers.py` 中创建测试函数
- 实现3个测试用例：2个正例、1个反例
- 包含图片加载辅助函数

### 步骤2：确保测试数据文件存在
- 验证测试图片路径正确
- 确认3个测试图片文件存在

### 步骤3：运行测试验证结构
- 执行测试确保测试框架工作正常
- 此时会失败（因为算法函数还未实现）

### 步骤4：实现算法函数
- 在合适的位置实现 `detect_pattern_continuity()` 函数
- 实现边缘检测、线条匹配、连续性判定逻辑

### 步骤5：运行测试验证功能
- 执行单元测试验证算法正确性
- 确保3个测试用例都通过

### 步骤6：测试清理和文档
- 添加必要的注释和文档
- 确保代码质量

## 技术要求
- 尽可能不使用模型
- 只使用常见图形处理库（如opencv）或自行编写简单逻辑
- 遵循TDD流程：先构建测试后构建功能

## 完成标准
- 所有3个单元测试用例通过
- 代码符合项目规范
- 有适当的注释和文档