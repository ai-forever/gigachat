import gigachat
import gigachat.models
from gigachat import (
    AICheckResult,
    Balance,
    BalanceValue,
    DeletedFile,
    DownloadedFile,
    OpenApiFunctions,
    TokensCount,
    UnprocessableEntityError,
    UploadedFile,
    UploadedFiles,
    authorization_cvar,
    client_id_cvar,
)
from gigachat.models import ChatFunctionExample, ChatFunctionResult, ChatSource


def test_root_exports_documented_response_types_and_context() -> None:
    exports = (
        AICheckResult,
        Balance,
        BalanceValue,
        DeletedFile,
        DownloadedFile,
        OpenApiFunctions,
        TokensCount,
        UnprocessableEntityError,
        UploadedFile,
        UploadedFiles,
        authorization_cvar,
        client_id_cvar,
    )
    names = (
        "AICheckResult",
        "Balance",
        "BalanceValue",
        "DeletedFile",
        "DownloadedFile",
        "OpenApiFunctions",
        "TokensCount",
        "UnprocessableEntityError",
        "UploadedFile",
        "UploadedFiles",
        "authorization_cvar",
        "client_id_cvar",
    )

    assert all(export is not None for export in exports)
    assert all(name in gigachat.__all__ for name in names)


def test_models_exports_primary_chat_nested_types() -> None:
    exports = (ChatFunctionExample, ChatFunctionResult, ChatSource)

    assert all(export is not None for export in exports)
    assert all(name in gigachat.models.__all__ for name in (export.__name__ for export in exports))
