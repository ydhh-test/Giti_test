# Rules RuleRunner 设计方案

## 1. 背景

Rules 层负责规则解释、特征计算、评分计算，以及规则驱动的图片操作定义和调度。

Rules 层可以调用 `src.core` 的基础算法能力，但不负责文件 IO、目录遍历、debug 落盘或 pipeline 编排。节点层负责批量处理、流程编排和结果写回。

## 2. 设计目标

1. 规则自动发现，不在业务流程里写硬编码 `if/elif`。
2. `feature` 和 `score` 独立，支持复用已有 feature 重新算分。
3. `exec_feature` 中的图片入参使用 `BaseImage` / `SmallImage` / `BigImage`。
4. `exec_image_operation(image, config)` 执行真实图片操作并返回 `BigImage`。
5. Rules 层不直接写回 `SmallImage` / `BigImage` / `TireStruct`。
6. 数据更新赋值发生在 nodes 层，例如 `tire_struct.big_image = new_big_image`。
7. Rules 调用 core 时显式传参，不把完整业务对象传给 core。

## 3. 总体架构

```text
src.api
  选择 generation / stitching / scoring / splitting pipeline

src.nodes
  负责节点级流程编排
  负责批量处理
  负责初始化和写回 ImageEvaluation / TireStruct.big_image
  调用 RuleRunner

src.rules
  RuleRunner：规则执行调度器
  RuleExecutor：单规则执行器
  registry：规则执行器注册表
  调用 src.core
  返回 RuleFeature / RuleScore / BigImage

src.core
  实际检测、拼接、装饰、图像处理算法
  不认识 rule_name
  不依赖 RuleConfig / RuleFeature / RuleScore / Image

src.models
  定义 RuleConfig / RuleFeature / RuleScore / Scheme / Image
```

## 4. RuleRunner 职责

`RuleRunner` 是规则执行调度器，非数据类，不持有业务状态。

### 4.1 必须负责

- 根据 `config.name` 查找对应 `RuleExecutor`。
- 调用 `exec_feature(image, config)`。
- 调用 `exec_score(config, feature)`。
- 调用 `exec_image_operation(image, config)`。
- 对外提供稳定统一入口。

### 4.2 不应负责

- 不实现单条规则业务逻辑。
- 不接收单独的 `rule_name` 参数。
- 不额外做 `_validate_config` / `_validate_feature`。
- 不把结果写回 image 或 tire_struct。
- 不构造 API 响应。
- 不遍历规则配置列表。
- 不做 pipeline 编排。
- 不缓存 feature 或 score。
- 不读写文件。

## 5. RuleExecutor 职责

`RuleExecutor` 是单条规则的执行器。当前阶段规则实现集中放在一个文件中，例如 `src/rules/rule_executors.py`。

每个 executor 必须继承 `RuleExecutor` 基类。

每个 executor 必须实现：

- `exec_feature`
- `exec_score`

可选实现：

- `exec_image_operation`

`Rule19Executor` 不需要定义 `rule_name`，但必须定义 `rule_cls`。注册时使用装饰器自动完成，注册名从 `rule_cls` 类名推导，例如 `Rule19Config -> rule19`：

```python
@register_rule_executor
class Rule19Executor(RuleExecutor):
    rule_cls = Rule19Config
```

当前 `rule_executors.py` 集中注册 `Rule1Executor` 到 `Rule22Executor`，包含 `Rule6AExecutor`。除 `Rule19Executor` 外，其余 executor 不定义 `exec_image_operation`，只继承基类默认的可选图片操作行为。

## 6. 核心接口

### 6.1 `exec_feature(image, config)`

用途：执行特征提取。

要求：

- 接收 `BaseImage` 或其子类，以及对应 rule config。
- 可以调用 `src.core` 基础算法。
- 调 core 时显式传参，不传完整 `config` 或完整业务 `image` 对象。
- 返回 `RuleNFeature`。
- 不计算 score。
- 不写回 image。
- 不保存 debug 结果。

示意：

```python
from src.models.image_models import BaseImage


def exec_feature(self, image: BaseImage, config: Rule8Config) -> Rule8Feature:
    result = detect_transverse_grooves(
        image_base64=image.image_base64,
        groove_width_center=config.groove_width_center,
        groove_width_side=config.groove_width_side,
    )
    return Rule8Feature(num_transverse_grooves=result.num_transverse_grooves)
```

### 6.2 `exec_score(config, feature)`

用途：执行评分计算。

要求：

- 只依赖 `config + feature`。
- 不依赖 image。
- 不调用图像算法。
- 支持传入新 config 重新计算 score。
- 返回 `RuleNScore`。

示意：

```python
def exec_score(self, config: Rule8Config, feature: Rule8Feature) -> Rule8Score:
    score = config.max_score if feature.num_transverse_grooves > 0 else 0
    return Rule8Score(score=score)
```

### 6.3 `exec_image_operation(image, config)`

用途：执行规则驱动的真实图片操作，并返回操作后的 `BigImage`。

要求：

- 接收 `BaseImage` 或其子类，以及对应 rule config。
- 返回 `BigImage`。
- 可以调用 `src.core` 图像算法，但调用时必须显式传参。
- 不直接修改 `TireStruct.big_image`。
- 不写文件，不落盘 debug 结果。
- 不替代 `exec_feature / exec_score`。

示意：

```python
from src.models.image_models import BaseImage, BigImage


def exec_image_operation(
    self,
    image: BaseImage,
    config: Rule19Config,
) -> BigImage:
    image_base64 = add_gray_borders(
        image_base64=image.image_base64,
        tire_design_width=config.tire_design_width,
        alpha=config.decoration_border_alpha,
        gray=config.decoration_gray_color,
    )
    return BigImage(
        image_base64=image_base64,
        meta=updated_meta,
        biz=updated_biz,
        evaluation=image.evaluation,
        lineage=getattr(image, "lineage", None),
    )
```

## 7. RuleExecutor 基类

```python
from abc import ABC, abstractmethod
from typing import ClassVar

from src.models.image_models import BaseImage, BigImage
from src.models.rule_models import BaseRuleConfig, BaseRuleFeature, BaseRuleScore


class RuleExecutor(ABC):
    rule_cls: ClassVar[type[BaseRuleConfig]]

    @abstractmethod
    def exec_feature(
        self,
        image: BaseImage,
        config: BaseRuleConfig,
    ) -> BaseRuleFeature:
        ...

    @abstractmethod
    def exec_score(
        self,
        config: BaseRuleConfig,
        feature: BaseRuleFeature,
    ) -> BaseRuleScore:
        ...

    def exec_image_operation(
        self,
        image: BaseImage,
        config: BaseRuleConfig,
    ) -> BigImage:
        raise NotImplementedError("exec_image_operation is not implemented")
```

`exec_feature` 和 `exec_score` 是抽象方法，子类必须实现。`exec_image_operation` 是可选能力，默认抛出 `NotImplementedError`；只有图片操作类规则需要覆盖它。

## 8. RuleRunner 接口

```python
from collections.abc import Callable

from src.models.image_models import BaseImage, BigImage
from src.models.rule_models import BaseRuleConfig, BaseRuleFeature, BaseRuleScore
from src.rules.base import RuleExecutor
from src.rules.registry import get_rule_executor


class RuleRunner:
    def __init__(
        self,
        get_executor: Callable[[str], RuleExecutor] = get_rule_executor,
    ) -> None:
        self._get_executor = get_executor

    def exec_feature(
        self,
        image: BaseImage,
        config: BaseRuleConfig,
    ) -> BaseRuleFeature:
        executor = self._get_executor(config.name)
        return executor.exec_feature(image, config)

    def exec_score(
        self,
        config: BaseRuleConfig,
        feature: BaseRuleFeature,
    ) -> BaseRuleScore:
        executor = self._get_executor(config.name)
        return executor.exec_score(config, feature)

    def exec_image_operation(
        self,
        image: BaseImage,
        config: BaseRuleConfig,
    ) -> BigImage:
        executor = self._get_executor(config.name)
        return executor.exec_image_operation(image, config)
```

## 9. 注册机制

规则执行器通过装饰器注册。装饰器读取 executor 的 `rule_cls`，按 `BaseRuleConfig.name` 的同一规则推导注册名。

```python
from src.rules.base import RuleExecutor


class RuleExecutorRegistry:
    def __init__(self) -> None:
        self._executors: dict[str, RuleExecutor] = {}

    def register(self, rule_name: str, executor: RuleExecutor) -> RuleExecutor:
        if rule_name in self._executors:
            raise ValueError(f"duplicate rule executor: {rule_name}")
        self._executors[rule_name] = executor
        return executor

    def get(self, rule_name: str) -> RuleExecutor:
        try:
            return self._executors[rule_name]
        except KeyError:
            raise ValueError(f"rule executor is not registered: {rule_name}") from None


def register_rule_executor(cls: type[RuleExecutor]) -> type[RuleExecutor]:
    if not issubclass(cls, RuleExecutor):
        raise TypeError("rule executor must inherit RuleExecutor")
    rule_cls = getattr(cls, "rule_cls", None)
    if rule_cls is None:
        raise ValueError("rule executor must define rule_cls")
    rule_name = rule_cls.__name__.lower().replace("config", "")
    _GLOBAL_REGISTRY.register(rule_name, cls())
    return cls
```

新增规则时：

1. 在 `src.models.rule_models` 中定义 `RuleNConfig / RuleNFeature / RuleNScore`。
2. 在 `src.rules.rule_executors` 中定义 `RuleNExecutor`。
3. `RuleNExecutor` 继承 `RuleExecutor`，定义 `rule_cls = RuleNConfig`。
4. 使用 `@register_rule_executor` 装饰器注册。

## 10. 与节点层协作

### 10.1 特征和评分写回

节点层负责写回：

```python
runner = RuleRunner()

feature = runner.exec_feature(image, rule8_config)
score = runner.exec_score(rule8_config, feature)

image.evaluation.set_feature(rule8_config.name, feature)
image.evaluation.set_score(rule8_config.name, score)
```

### 10.2 新配置重算分

```python
old_feature = image.evaluation.get_rule(rule8_config.name).feature
new_score = runner.exec_score(new_rule8_config, old_feature)
image.evaluation.set_score(new_rule8_config.name, new_score)
```

该流程不重跑 feature。

### 10.3 图片操作写回

```python
runner = RuleRunner()

new_big_image = runner.exec_image_operation(
    image=tire_struct.big_image,
    config=rule19_config,
)
tire_struct.big_image = new_big_image
```

数据更新赋值位置在节点层。`RuleRunner` 只返回 `BigImage`，由当前 pipeline 节点执行 `tire_struct.big_image = new_big_image`。

## 11. 规则类型分类

### 11.1 检测评分类规则

示例：

- rule8
- rule11
- rule13
- rule14

主要实现：

- `exec_feature`
- `exec_score`

### 11.2 图片操作类规则

示例：

- rule19

主要实现：

- `exec_image_operation`

这类规则执行真实图片操作并返回 `BigImage`。它不直接修改 `TireStruct.big_image`，也不负责文件保存。

## 12. 与 core 的调用约束

Rules 调用 core 必须显式传参。

推荐：

```python
add_gray_borders(
    image_base64=image.image_base64,
    tire_design_width=config.tire_design_width,
    alpha=config.decoration_border_alpha,
    gray=config.decoration_gray_color,
)
```

不推荐：

```python
add_gray_borders(image=image, config=config)
```

原因：

- core 不应认识业务数据模型。
- core 不应依赖 `RuleConfig`。
- core 应保持为可复用基础算法。

## 13. 目录建议

第一阶段建议：

```text
src/rules/
  __init__.py
  base.py
  registry.py
  runner.py
  rule_executors.py
```

当前不拆成每个 rule 一个文件。规则数量变多后，再考虑按能力拆分。

第一阶段先在 `rule_executors.py` 中完成所有规则 executor 的集中注册。未实现具体业务逻辑的规则继承 `UnsupportedRuleExecutor`，用于明确表示“已注册但 feature / score 尚未落地”。

## 14. 测试策略

### 14.1 registry 单元测试

覆盖：

- 正确注册和获取 executor。
- 重复注册报错。
- 未注册规则报错。

### 14.2 RuleRunner 单元测试

覆盖：

- `exec_feature` 使用 `config.name` 查找 executor。
- `exec_score` 使用 `config.name` 查找 executor。
- `exec_image_operation` 使用 `config.name` 查找 executor。
- Runner 不接收单独 `rule_name` 参数。

### 14.3 单规则测试

覆盖：

- feature 输入输出。
- score 输入输出。
- image operation 输入输出。
- image operation 返回 `BigImage`。
- image operation 不写文件 IO。
- executor 必须继承 `RuleExecutor`。
- executor 缺少 `exec_feature` 或 `exec_score` 时不能实例化。

### 14.4 节点层集成测试

覆盖：

- 筛选当前节点生效的规则配置。
- 调用 `RuleRunner.exec_image_operation(image, config)`。
- 将返回的 `BigImage` 赋值给 `TireStruct.big_image`。

## 15. 当前结论

Rules 层形成三段能力：

```text
Feature: 规则观察到了什么
Score: 基于观察结果怎么打分
ImageOperation: 基于规则配置对图片执行真实操作，并返回 BigImage
```

`RuleRunner` 统一调度，`RuleExecutor` 承载单规则实现，`Config / Feature / Score / Image` 继续保持数据模型职责。

主链路保持：

```text
api -> nodes -> rules -> core
```
