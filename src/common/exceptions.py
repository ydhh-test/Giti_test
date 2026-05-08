from __future__ import annotations

from typing import Any


class ProjectError(Exception):
    """项目级统一异常基类。"""

    def __init__(
        self,
        message: str,
        *,
        location: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.location = location
        self.details = details
        self.cause = cause

    def __str__(self) -> str:
        return self.message


class InputError(ProjectError):
    """输入相关错误基类。"""


class InputTypeError(InputError):
    """函数收到的参数类型不符合约定。"""

    def __init__(self, function: str, param: str, expected_type: str, actual_type: str) -> None:
        message = f"{function}: argument '{param}' expects {expected_type}, got {actual_type}"
        super().__init__(
            message,
            location=function,
            details={
                "function": function,
                "param": param,
                "expected_type": expected_type,
                "actual_type": actual_type,
            },
        )
        self.function = function
        self.param = param
        self.expected_type = expected_type
        self.actual_type = actual_type


class InputDataError(InputError):
    """输入对象类型正确，但数据内容不满足约束。"""

    def __init__(
        self,
        object_name: str,
        field_path: str,
        rule: str,
        actual_value: Any | None = None,
    ) -> None:
        message = f"{object_name}.{field_path}: {rule}"
        if actual_value is not None:
            message = f"{message}, got {actual_value!r}"
        super().__init__(
            message,
            location=f"{object_name}.{field_path}",
            details={
                "object_name": object_name,
                "field_path": field_path,
                "rule": rule,
                "actual_value": actual_value,
            },
        )
        self.object_name = object_name
        self.field_path = field_path
        self.rule = rule
        self.actual_value = actual_value


class RuntimeProcessError(ProjectError):
    """执行过程失败，且问题不在输入本身。"""

    def __init__(self, stage: str, high_level_failure: str, original_error: Exception) -> None:
        message = f"{stage}: {high_level_failure}: {original_error}"
        super().__init__(
            message,
            location=stage,
            details={"stage": stage},
            cause=original_error,
        )
        self.stage = stage
        self.high_level_failure = high_level_failure
        self.original_error = original_error
        # 显式设置 __cause__ 以支持 Python 异常链
        self.__cause__ = original_error

    def __reduce__(self):
        """支持 pickle 序列化"""
        return (
            self.__class__,
            (self.stage, self.high_level_failure, self.original_error),
        )
