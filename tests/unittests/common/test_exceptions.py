"""通用异常类测试 - 覆盖性验证和真实场景测试"""

import pytest
from src.common.exceptions import (
    ProjectError,
    InputError,
    InputTypeError,
    InputDataError,
    RuntimeProcessError,
)


# ===================== 测试数据 =====================

SAMPLE_PYTHON_ERRORS = [
    ValueError("invalid value"),
    TypeError("'NoneType' object has no attribute 'process'"),
    KeyError("'missing_key'"),
    IndexError("list index out of range"),
    AttributeError("'dict' object has no attribute 'rule6_1'"),
    ZeroDivisionError("division by zero"),
    FileNotFoundError("[Errno 2] No such file or directory: '/path/to/file'"),
    RuntimeError("unexpected execution failure"),
]


# ===================== 继承体系完整性测试 =====================

class TestExceptionInheritance:
    """异常继承体系完整性测试"""

    def test_input_type_error_chain(self):
        """✅ InputTypeError -> InputError -> ProjectError -> Exception"""
        err = InputTypeError("func", "param", "str", "int")
        assert isinstance(err, InputTypeError)
        assert isinstance(err, InputError)
        assert isinstance(err, ProjectError)
        assert isinstance(err, Exception)
        assert isinstance(err, BaseException)

    def test_input_data_error_chain(self):
        """✅ InputDataError -> InputError -> ProjectError -> Exception"""
        err = InputDataError("Obj", "field", "rule", "value")
        assert isinstance(err, InputDataError)
        assert isinstance(err, InputError)
        assert isinstance(err, ProjectError)
        assert isinstance(err, Exception)

    def test_runtime_process_error_chain(self):
        """✅ RuntimeProcessError -> ProjectError -> Exception"""
        err = RuntimeProcessError("stage", "failure", ValueError())
        assert isinstance(err, RuntimeProcessError)
        assert isinstance(err, ProjectError)
        assert isinstance(err, Exception)

    def test_input_type_error_is_not_runtime_error(self):
        """✅ InputTypeError 不是 RuntimeProcessError 子类"""
        err = InputTypeError("func", "param", "str", "int")
        assert not isinstance(err, RuntimeProcessError)

    def test_input_data_error_is_not_runtime_error(self):
        """✅ InputDataError 不是 RuntimeProcessError 子类"""
        err = InputDataError("Obj", "field", "rule", "value")
        assert not isinstance(err, RuntimeProcessError)

    def test_catch_by_parent_type(self):
        """✅ 可以用父类型捕获所有子类"""
        errors = [
            InputTypeError("f", "p", "str", "int"),
            InputDataError("Obj", "field", "rule", "value"),
            RuntimeProcessError("stage", "failure", ValueError()),
        ]

        for err in errors:
            assert isinstance(err, ProjectError)

    def test_catch_input_errors_together(self):
        """✅ InputTypeError 和 InputDataError 都可以用 InputError 捕获"""
        input_errors = [
            InputTypeError("f", "p", "str", "int"),
            InputDataError("Obj", "field", "rule", "value"),
        ]

        for err in input_errors:
            assert isinstance(err, InputError)
            assert not isinstance(err, RuntimeProcessError)


# ===================== InputTypeError 字段完整性 =====================

class TestInputTypeErrorFields:
    """InputTypeError 字段完整性测试"""

    def test_all_structured_fields(self):
        """✅ 所有结构化字段正确赋值"""
        err = InputTypeError("my_function", "my_param", "ExpectedType", "ActualType")

        assert err.function == "my_function"
        assert err.param == "my_param"
        assert err.expected_type == "ExpectedType"
        assert err.actual_type == "ActualType"

    def test_inherited_fields_from_project_error(self):
        """✅ 继承自 ProjectError 的字段正确"""
        err = InputTypeError("func", "param", "str", "int")

        assert err.message is not None
        assert err.location == "func"
        assert err.details is not None
        assert err.cause is None

    def test_details_dict_contains_all_fields(self):
        """✅ details 字典包含所有必要字段"""
        err = InputTypeError("func", "param", "str", "int")

        assert "function" in err.details
        assert "param" in err.details
        assert "expected_type" in err.details
        assert "actual_type" in err.details

    def test_details_dict_values_match_attributes(self):
        """✅ details 字典值与属性一致"""
        err = InputTypeError("func", "param", "str", "int")

        assert err.details["function"] == err.function
        assert err.details["param"] == err.param
        assert err.details["expected_type"] == err.expected_type
        assert err.details["actual_type"] == err.actual_type


class TestInputTypeErrorMessageFormat:
    """InputTypeError 消息格式覆盖测试"""

    def test_standard_format(self):
        """✅ 标准格式"""
        err = InputTypeError("func", "param", "ExpectedType", "ActualType")
        assert str(err) == "func: argument 'param' expects ExpectedType, got ActualType"

    def test_with_complex_type_names(self):
        """✅ 复杂类型名称"""
        err = InputTypeError("process", "data", "List[FakeTireStruct]", "dict")
        assert "List[FakeTireStruct]" in str(err)
        assert "dict" in str(err)

    def test_with_class_name_actual_type(self):
        """✅ 使用 type().__name__ 获取实际类型"""
        err = InputTypeError("func", "data", "FakeTireStruct", type({}).__name__)
        assert "dict" in str(err)


# ===================== InputDataError 字段完整性 =====================

class TestInputDataErrorFields:
    """InputDataError 字段完整性测试"""

    def test_all_structured_fields(self):
        """✅ 所有结构化字段正确赋值"""
        err = InputDataError("MyObj", "field.path", "rule desc", "actual_val")

        assert err.object_name == "MyObj"
        assert err.field_path == "field.path"
        assert err.rule == "rule desc"
        assert err.actual_value == "actual_val"

    def test_inherited_fields(self):
        """✅ 继承自 ProjectError 的字段正确"""
        err = InputDataError("Obj", "field", "rule", "value")

        assert err.location == "Obj.field"
        assert err.details["object_name"] == "Obj"
        assert err.details["field_path"] == "field"
        assert err.details["rule"] == "rule"
        assert err.details["actual_value"] == "value"


class TestInputDataErrorMessageFormat:
    """InputDataError 消息格式覆盖测试"""

    def test_with_actual_value(self):
        """✅ 包含实际值"""
        err = InputDataError("Obj", "field", "rule", "value")
        assert str(err) == "Obj.field: rule, got 'value'"

    def test_without_actual_value(self):
        """✅ 不包含实际值 (actual_value=None)"""
        err = InputDataError("Obj", "field", "rule")
        assert str(err) == "Obj.field: rule"
        assert "got" not in str(err)

    def test_with_none_explicit(self):
        """✅ 显式传递 None 作为 actual_value"""
        err = InputDataError("Obj", "field", "rule", actual_value=None)
        assert str(err) == "Obj.field: rule"

    def test_with_integer_value(self):
        """✅ 整数实际值"""
        err = InputDataError("Obj", "count", "must be >= 1", 0)
        assert "got 0" in str(err)

    def test_with_dict_value(self):
        """✅ 字典实际值"""
        err = InputDataError("Obj", "config", "invalid", {"key": "value"})
        assert "got {'key': 'value'}" in str(err)

    def test_with_list_value(self):
        """✅ 列表实际值"""
        err = InputDataError("Obj", "items", "must not be empty", [])
        assert "got []" in str(err)

    def test_with_long_string_value(self):
        """✅ 长字符串实际值"""
        long_value = "x" * 200
        err = InputDataError("Obj", "field", "rule", long_value)
        assert long_value in str(err)

    def test_with_special_characters(self):
        """✅ 包含特殊字符"""
        err = InputDataError("Obj", "field", "must not contain <script>", "<script>alert(1)</script>")
        assert "<script>" in str(err)

    def test_with_unicode(self):
        """✅ 包含 Unicode 字符"""
        err = InputDataError("对象", "字段", "规则：必须 >= 1", 0)
        assert "对象.字段: 规则：必须 >= 1, got 0" in str(err)


class TestInputDataErrorRealWorldScenarios:
    """InputDataError 真实场景测试"""

    def test_scheme_rank_invalid(self):
        """✅ FakeTireStruct.scheme_rank 非法值"""
        err = InputDataError("FakeTireStruct", "scheme_rank", "must be >= 1", 0)
        assert "FakeTireStruct.scheme_rank" in str(err)

    def test_small_images_empty(self):
        """✅ FakeTireStruct.small_images 为空"""
        err = InputDataError("FakeTireStruct", "small_images", "must not be empty", [])
        assert "must not be empty" in str(err)

    def test_big_image_not_none(self):
        """✅ FakeTireStruct.big_image 在请求中必须为 None"""
        err = InputDataError(
            "FakeTireStruct",
            "big_image",
            "must be None in request",
            {"image_base64": "data:image/png;base64,xxx"},
        )
        assert "must be None" in str(err)

    def test_nested_field_path(self):
        """✅ 嵌套字段路径"""
        err = InputDataError("TireStruct", "big_image.meta.width", "must be positive", -1)
        assert "big_image.meta.width" in str(err)


# ===================== RuntimeProcessError 字段完整性 =====================

class TestRuntimeProcessErrorFields:
    """RuntimeProcessError 字段完整性测试"""

    def test_all_structured_fields(self):
        """✅ 所有结构化字段正确赋值"""
        original = ValueError("original")
        err = RuntimeProcessError("my_stage", "my_failure", original)

        assert err.stage == "my_stage"
        assert err.original_error is original

    def test_inherited_fields(self):
        """✅ 继承自 ProjectError 的字段正确"""
        original = ValueError("original")
        err = RuntimeProcessError("stage", "failure", original)

        assert err.location == "stage"
        assert err.details["stage"] == "stage"
        assert err.cause is original

    def test_exception_chain_is_preserved(self):
        """✅ Python 异常链被正确保留"""
        original = ValueError("original error")
        err = RuntimeProcessError("stage", "failure", original)

        assert err.__cause__ is original
        assert err.cause is original
        assert err.original_error is original


class TestRuntimeProcessErrorMessageFormat:
    """RuntimeProcessError 消息格式覆盖测试"""

    def test_standard_format(self):
        """✅ 标准格式"""
        original = ValueError("original error")
        err = RuntimeProcessError("stage", "failure", original)

        assert str(err) == "stage: failure: original error"

    def test_message_contains_all_parts(self):
        """✅ 消息包含所有部分"""
        original = KeyError("missing_key")
        err = RuntimeProcessError(
            "create_success_response",
            "failed to build fake big image",
            original,
        )

        assert "create_success_response" in str(err)
        assert "failed to build fake big image" in str(err)
        assert "missing_key" in str(err)


class TestRuntimeProcessErrorRealPythonErrors:
    """RuntimeProcessError 包装真实 Python 错误的测试"""

    @pytest.mark.parametrize("original_error,expected_in_message", [
        (ValueError("invalid value"), "invalid value"),
        (TypeError("'NoneType' object has no attribute 'process'"), "NoneType"),
        (KeyError("missing_key"), "missing_key"),
        (IndexError("list index out of range"), "out of range"),
        (AttributeError("'dict' object has no attribute 'rule6_1'"), "rule6_1"),
        (ZeroDivisionError("division by zero"), "division by zero"),
        (RuntimeError("unexpected execution failure"), "unexpected"),
    ])
    def test_wrap_various_python_errors(self, original_error, expected_in_message):
        """✅ 包装各种 Python 异常类型"""
        err = RuntimeProcessError("stage", "failure", original_error)

        assert err.original_error is original_error
        assert expected_in_message in str(err)
        assert "stage" in str(err)
        assert "failure" in str(err)

    def test_wrap_none_type_attribute_error(self):
        """✅ 包装最常见的 NoneType 属性访问错误"""
        try:
            obj = None
            obj.process()
        except AttributeError as e:
            err = RuntimeProcessError(
                "create_success_response",
                "failed to build fake big image",
                e,
            )

        assert "'NoneType' object has no attribute 'process'" in str(err)
        assert err.original_error is not None
        assert isinstance(err.original_error, AttributeError)

    def test_wrap_key_error_from_dict_access(self):
        """✅ 包装字典键访问错误"""
        try:
            data = {}
            _ = data["missing_key"]
        except KeyError as e:
            err = RuntimeProcessError(
                "build_response",
                "missing required field",
                e,
            )

        assert "missing_key" in str(err)
        assert isinstance(err.original_error, KeyError)

    def test_wrap_value_error_from_parsing(self):
        """✅ 包装解析/转换错误"""
        try:
            int("not_a_number")
        except ValueError as e:
            err = RuntimeProcessError(
                "parse_input",
                "failed to parse integer value",
                e,
            )

        assert "invalid literal" in str(err)
        assert isinstance(err.original_error, ValueError)

    def test_wrap_zero_division(self):
        """✅ 包装除零错误"""
        try:
            _ = 1 / 0
        except ZeroDivisionError as e:
            err = RuntimeProcessError(
                "calculate_score",
                "division operation failed",
                e,
            )

        assert "division by zero" in str(err)
        assert isinstance(err.original_error, ZeroDivisionError)

    def test_wrap_index_error(self):
        """✅ 包装索引越界错误"""
        try:
            lst = [1, 2, 3]
            _ = lst[10]
        except IndexError as e:
            err = RuntimeProcessError(
                "access_list",
                "list access failed",
                e,
            )

        assert "out of range" in str(err)
        assert isinstance(err.original_error, IndexError)


# ===================== 真实执行场景测试 =====================

class TestRealExecutionScenarios:
    """真实执行中捕获并包装异常的测试"""

    def test_method_raises_attribute_error_wrapped(self):
        """✅ 方法调用时 None 导致 AttributeError 被包装"""
        def process_data(data):
            """模拟会抛出 AttributeError 的方法"""
            if data.get("config") is None:
                data["config"].rule6_1
            return "success"

        test_data = {"config": None}

        try:
            process_data(test_data)
        except AttributeError as original:
            wrapped = RuntimeProcessError(
                stage="process_data",
                high_level_failure="failed to access config.rule6_1",
                original_error=original,
            )

        assert "process_data" in str(wrapped)
        assert "config.rule6_1" in str(wrapped)
        assert "NoneType" in str(wrapped)
        assert isinstance(wrapped.original_error, AttributeError)

    def test_method_raises_key_error_wrapped(self):
        """✅ 字典访问缺失键被包装"""
        def extract_field(data):
            """模拟会抛出 KeyError 的方法"""
            return data["required_field"]["nested_value"]

        test_data = {"other_field": "value"}

        try:
            extract_field(test_data)
        except KeyError as original:
            wrapped = RuntimeProcessError(
                stage="extract_field",
                high_level_failure="missing required field",
                original_error=original,
            )

        assert "extract_field" in str(wrapped)
        assert "required_field" in str(wrapped)
        assert isinstance(wrapped.original_error, KeyError)

    def test_method_raises_type_error_wrapped(self):
        """✅ 类型不匹配被包装"""
        def add_numbers(a, b):
            """模拟会抛出 TypeError 的方法"""
            return a + b

        try:
            add_numbers("string", 42)
        except TypeError as original:
            wrapped = RuntimeProcessError(
                stage="add_numbers",
                high_level_failure="type mismatch in addition",
                original_error=original,
            )

        assert "add_numbers" in str(wrapped)
        assert isinstance(wrapped.original_error, TypeError)

    def test_method_raises_value_error_wrapped(self):
        """✅ 值错误被包装"""
        def parse_config(config_str):
            """模拟会抛出 ValueError 的方法"""
            import json
            return json.loads(config_str)

        try:
            parse_config("not_valid_json")
        except ValueError as original:
            wrapped = RuntimeProcessError(
                stage="parse_config",
                high_level_failure="invalid JSON format",
                original_error=original,
            )

        assert "parse_config" in str(wrapped)
        assert "invalid" in str(wrapped).lower()
        assert isinstance(wrapped.original_error, ValueError)

    def test_chained_exception_preserves_full_context(self):
        """✅ 链式异常保留完整上下文"""
        def inner_function():
            """内层函数抛出原始错误"""
            return int("not_a_number")

        def outer_function():
            """外层函数捕获并包装"""
            try:
                return inner_function()
            except ValueError as e:
                raise RuntimeProcessError(
                    stage="outer_function",
                    high_level_failure="inner_function failed",
                    original_error=e,
                )

        with pytest.raises(RuntimeProcessError) as exc_info:
            outer_function()

        err = exc_info.value
        assert "outer_function" in str(err)
        assert "inner_function failed" in str(err)
        assert isinstance(err.original_error, ValueError)
        assert err.__cause__ is err.original_error

    def test_nested_wr_exception(self):
        """✅ 嵌套包装场景"""
        def level3():
            raise KeyError("deep_error")

        def level2():
            try:
                level3()
            except KeyError as e:
                raise RuntimeProcessError(
                    stage="level2",
                    high_level_failure="level3 failed",
                    original_error=e,
                )

        def level1():
            try:
                level2()
            except RuntimeProcessError as e:
                raise RuntimeProcessError(
                    stage="level1",
                    high_level_failure="level2 failed",
                    original_error=e,
                )

        with pytest.raises(RuntimeProcessError) as exc_info:
            level1()

        top_error = exc_info.value
        assert top_error.stage == "level1"
        assert isinstance(top_error.original_error, RuntimeProcessError)
        assert top_error.original_error.stage == "level2"

    def test_runtime_error_used_in_api_pattern(self):
        """✅ RuntimeProcessError 在 API 模式中的使用"""
        def api_generate(tire_struct):
            """模拟 API 端点"""
            try:
                raise AttributeError("'NoneType' object has no attribute 'rule6_1'")
            except Exception as e:
                runtime_error = RuntimeProcessError(
                    stage="create_success_response",
                    high_level_failure="failed to build fake big image",
                    original_error=e,
                )
                return {
                    "flag": False,
                    "err_code": "RUNTIME_ERROR",
                    "err_msg": str(runtime_error),
                }

        result = api_generate({})

        assert result["flag"] is False
        assert result["err_code"] == "RUNTIME_ERROR"
        assert "create_success_response" in result["err_msg"]
        assert "failed to build fake big image" in result["err_msg"]
        assert "'NoneType' object has no attribute 'rule6_1'" in result["err_msg"]

    def test_original_error_traceback_accessible(self):
        """✅ 原始错误的 traceback 可访问"""
        try:
            _ = 1 / 0
        except ZeroDivisionError as e:
            err = RuntimeProcessError("calc", "division failed", e)

        assert err.original_error.__traceback__ is not None

    def test_error_can_be_re_raised(self):
        """✅ 包装后的异常可以再次抛出"""
        try:
            raise ValueError("original")
        except ValueError as e:
            wrapped = RuntimeProcessError("stage", "failure", e)

        with pytest.raises(RuntimeProcessError):
            raise wrapped


# ===================== 边界条件测试 =====================

class TestBoundaryConditions:
    """异常类边界条件测试"""

    def test_input_type_error_empty_strings(self):
        """✅ InputTypeError 使用空字符串参数"""
        err = InputTypeError("", "", "", "")
        assert str(err) == ": argument '' expects , got "

    def test_input_data_error_empty_object_and_field(self):
        """✅ InputDataError 使用空对象名和字段"""
        err = InputDataError("", "", "rule", "value")
        assert str(err) == ".: rule, got 'value'"

    def test_runtime_error_empty_stage_and_failure(self):
        """✅ RuntimeProcessError 使用空阶段和失败描述"""
        original = ValueError("error")
        err = RuntimeProcessError("", "failure", original)
        assert ": failure: error" in str(err)

    def test_input_data_error_with_empty_string_as_value(self):
        """✅ InputDataError 实际值为空字符串"""
        err = InputDataError("Obj", "field", "must not be empty", "")
        assert "got ''" in str(err)

    def test_input_data_error_with_false_as_value(self):
        """✅ InputDataError 实际值为 False"""
        err = InputDataError("Obj", "flag", "must be True", False)
        assert "got False" in str(err)

    def test_input_data_error_with_zero_as_value(self):
        """✅ InputDataError 实际值为 0"""
        err = InputDataError("Obj", "count", "must be > 0", 0)
        assert "got 0" in str(err)


# ===================== 异常处理集成测试 =====================

class TestExceptionHandlingIntegration:
    """异常处理分层集成测试"""

    def test_api_layer_does_not_catch_type_error(self):
        """✅ API 层不捕获 InputTypeError"""
        def api_function(data):
            if not isinstance(data, dict):
                raise InputTypeError("api_function", "data", "dict", type(data).__name__)
            return {"flag": True}

        with pytest.raises(InputTypeError):
            api_function("not_a_dict")

    def test_data_error_converted_to_data_error_response(self):
        """✅ InputDataError 转换为 DATA_ERROR 响应"""
        def api_function(data):
            if data.get("scheme_rank", 1) < 1:
                err = InputDataError("FakeTireStruct", "scheme_rank", "must be >= 1", data["scheme_rank"])
                return {"err_code": "DATA_ERROR", "err_msg": str(err)}
            return {"flag": True}

        result = api_function({"scheme_rank": 0})
        assert result["err_code"] == "DATA_ERROR"
        assert "must be >= 1" in result["err_msg"]
        assert "got 0" in result["err_msg"]

    def test_runtime_error_converted_to_runtime_error_response(self):
        """✅ RuntimeProcessError 转换为 RUNTIME_ERROR 响应"""
        def api_function(data):
            try:
                raise ValueError("internal error")
            except Exception as e:
                err = RuntimeProcessError("api_function", "business logic failed", e)
                return {"err_code": "RUNTIME_ERROR", "err_msg": str(err)}

        result = api_function({})
        assert result["err_code"] == "RUNTIME_ERROR"
        assert "internal error" in result["err_msg"]

    def test_full_api_pattern_with_all_three_error_types(self):
        """✅ 完整 API 模式：三种错误类型的处理"""
        def full_api_pattern(data):
            if not isinstance(data, dict):
                raise InputTypeError("full_api_pattern", "data", "dict", type(data).__name__)

            if data.get("scheme_rank", 1) < 1:
                err = InputDataError("FakeTireStruct", "scheme_rank", "must be >= 1", data.get("scheme_rank"))
                return {"err_code": "DATA_ERROR", "err_msg": str(err)}

            try:
                if data.get("should_fail"):
                    raise KeyError("missing_key_in_business_logic")
                return {"flag": True}
            except Exception as e:
                err = RuntimeProcessError("full_api_pattern", "business logic failed", e)
                return {"err_code": "RUNTIME_ERROR", "err_msg": str(err)}

        # 场景 1：类型错误 - 不捕获
        with pytest.raises(InputTypeError):
            full_api_pattern("not_a_dict")

        # 场景 2：数据错误 - 转换为 DATA_ERROR
        result = full_api_pattern({"scheme_rank": 0})
        assert result["err_code"] == "DATA_ERROR"

        # 场景 3：运行时错误 - 转换为 RUNTIME_ERROR
        result = full_api_pattern({"scheme_rank": 1, "should_fail": True})
        assert result["err_code"] == "RUNTIME_ERROR"
        assert "missing_key_in_business_logic" in result["err_msg"]

        # 场景 4：成功
        result = full_api_pattern({"scheme_rank": 1})
        assert result["flag"] is True

    def test_multiple_validations_first_error_returned(self):
        """✅ 多个校验错误只返回第一个"""
        def validate(data):
            if not data.get("small_images"):
                err = InputDataError("FakeTireStruct", "small_images", "must not be empty")
                return str(err)
            if data.get("scheme_rank", 1) < 1:
                err = InputDataError("FakeTireStruct", "scheme_rank", "must be >= 1", data["scheme_rank"])
                return str(err)
            return None

        data = {"small_images": [], "scheme_rank": 0}
        result = validate(data)
        assert "small_images" in result
        assert "must not be empty" in result

    def test_error_response_preserves_original_context(self):
        """✅ 错误响应保留原始错误上下文"""
        def business_logic():
            raise RuntimeError("database connection failed: timeout after 30s")

        def api_call():
            try:
                business_logic()
            except Exception as e:
                err = RuntimeProcessError("api_call", "database operation failed", e)
                return {
                    "flag": False,
                    "err_code": "RUNTIME_ERROR",
                    "err_msg": str(err),
                }

        result = api_call()
        assert "database connection failed" in result["err_msg"]
        assert "timeout after 30s" in result["err_msg"]
        assert "api_call" in result["err_msg"]


# ===================== 序列化测试 =====================

class TestExceptionSerialization:
    """异常序列化测试"""

    def test_str_returns_message_for_all_types(self):
        """✅ str() 对所有异常类型返回消息"""
        errors = [
            InputTypeError("f", "p", "str", "int"),
            InputDataError("Obj", "field", "rule", "value"),
            RuntimeProcessError("stage", "failure", ValueError("test")),
        ]

        for err in errors:
            msg = str(err)
            assert msg
            assert isinstance(msg, str)

    def test_repr_is_informative(self):
        """✅ repr() 提供有用信息"""
        err = InputTypeError("func", "param", "str", "int")
        repr_str = repr(err)
        assert "InputTypeError" in repr_str

    def test_exception_can_be_pickled(self):
        """✅ 异常可以被 pickle 序列化"""
        import pickle

        original = ValueError("test error")
        err = RuntimeProcessError("stage", "failure", original)

        pickled = pickle.dumps(err)
        unpickled = pickle.loads(pickled)

        assert unpickled.stage == err.stage
        assert unpickled.message == err.message


# ===================== 项目规范符合性测试 =====================

class TestProjectSpecCompliance:
    """项目规范符合性测试"""

    def test_error_message_has_location_value(self):
        """✅ 所有异常都有 location 值"""
        errors = [
            InputTypeError("func_name", "param", "str", "int"),
            InputDataError("Obj", "field", "rule", "value"),
            RuntimeProcessError("stage_name", "failure", ValueError()),
        ]

        for err in errors:
            assert err.location is not None
            assert len(err.location) > 0

    def test_error_message_is_not_generic(self):
        """✅ 异常消息不是泛泛描述，有具体定位价值"""
        type_err = InputTypeError("generate_big_image", "tire_struct", "FakeTireStruct", "dict")
        assert "generate_big_image" in str(type_err)
        assert "tire_struct" in str(type_err)

        data_err = InputDataError("FakeTireStruct", "scheme_rank", "must be >= 1", 0)
        assert "FakeTireStruct" in str(data_err)
        assert "scheme_rank" in str(data_err)

        runtime_err = RuntimeProcessError("create_response", "build failed", ValueError("details"))
        assert "create_response" in str(runtime_err)
        assert "build failed" in str(runtime_err)
        assert "details" in str(runtime_err)

    def test_exception_does_not_swallow_context(self):
        """✅ 异常不吞掉底层上下文"""
        original = AttributeError("'NoneType' object has no attribute 'rule6_1'")
        wrapped = RuntimeProcessError("stage", "failure", original)

        assert wrapped.original_error is original
        assert "rule6_1" in str(wrapped)
        assert wrapped.cause is original
