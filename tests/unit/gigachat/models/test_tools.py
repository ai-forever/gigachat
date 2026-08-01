from gigachat.models.tools import (
    AICheckResult,
    Balance,
    CustomFunction,
    FunctionValidationResult,
    OpenApiFunctions,
    TokensCount,
)


def test_ai_check_result_creation() -> None:
    data = {
        "category": "ai",
        "characters": 100,
        "tokens": 20,
        "ai_intervals": [[0, 100]],
    }
    res = AICheckResult.model_validate(data)
    assert res.category == "ai"
    assert res.tokens == 20


def test_balance_creation() -> None:
    data = {
        "balance": [{"usage": "GigaChat", "value": 1000.5}],
    }
    bal = Balance.model_validate(data)
    assert len(bal.balance) == 1
    assert bal.balance[0].usage == "GigaChat"
    assert bal.balance[0].value == 1000.5


def test_tokens_count_creation() -> None:
    data = {
        "tokens": 50,
        "characters": 200,
        "object": "tokens",
    }
    cnt = TokensCount.model_validate(data)
    assert cnt.tokens == 50
    assert cnt.object_ == "tokens"


def test_openapi_functions_creation() -> None:
    data = {"functions": [{"name": "func1", "description": "desc"}]}
    funcs = OpenApiFunctions.model_validate(data)
    assert len(funcs.functions) == 1
    assert funcs.functions[0].name == "func1"


def test_custom_function_keeps_arbitrary_json_schema_keywords() -> None:
    function = CustomFunction.model_validate(
        {
            "name": "send_sms",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string", "minLength": 1, "pattern": "^.+$"}},
                "additionalProperties": False,
            },
        }
    )

    assert function.parameters["properties"]["text"]["minLength"] == 1
    assert function.parameters["additionalProperties"] is False


def test_function_validation_result_allows_errors_and_optional_fields() -> None:
    result = FunctionValidationResult.model_validate(
        {
            "message": "Incorrect function syntax",
            "errors": [{"description": "name is required", "schema_location": "(root)"}],
        }
    )

    assert result.status is None
    assert result.errors is not None
    assert result.errors[0].description == "name is required"
