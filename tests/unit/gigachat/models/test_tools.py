from gigachat.models.tools import (
    AICheckResult,
    Balance,
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


def test_function_validation_result_creation() -> None:
    data = {
        "status": 200,
        "message": "Function is valid",
        "json_ai_rules_version": "1.0.5",
        "warnings": [{"description": "few_shot_examples are missing", "schema_location": "(root)"}],
    }
    result = FunctionValidationResult.model_validate(data)
    assert result.status == 200
    assert result.message == "Function is valid"
    assert result.warnings is not None
    assert result.warnings[0].schema_location == "(root)"
