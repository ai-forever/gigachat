# PLANS Progress

План: `docs/internal/PLANS.md`

## Правила

- Один чат = один срез из раздела `Предлагаемый порядок работы`.
- После каждого завершённого среза делается отдельный commit.
- Статус каждого среза фиксируется в этом файле до перехода к следующему.

## Срезы

1. `[done]` Создать `src/gigachat/resources/chat.py` и `src/gigachat/resources/__init__.py`.
2. `[done]` Добавить `cached_property` namespaces/resources в client classes.
3. `[done]` Вынести текущую legacy chat-логику в private helper methods.
4. `[done]` Перевести `assistants` / `threads` / `a_assistants` / `a_threads` на `cached_property`.
5. `[done]` Добавить deprecated shims.
6. `[done]` Обновить error messages/docstrings.
7. `[done]` Обновить README/examples.
8. `[done]` Добавить/обновить unit tests.
9. `[done]` Прогнать `make fmt`, `make mypy`, `make test`.

## Журнал

- 2026-04-23: завершён срез 1. Добавлен пакет `src/gigachat/resources/` с chat namespace/resource-классами и зафиксированы правила исполнения плана.
- 2026-04-23: завершён срез 2. `client.chat` и `client.achat` переведены на `cached_property` namespace-объекты; для рабочей маршрутизации добавлены private legacy chat helper methods, но отдельные deprecated shims и doc updates остаются следующими срезами.
- 2026-04-23: завершён срез 3. Legacy chat-логика окончательно закреплена за private helper methods в `client.py`, а `resources/chat.py` использует только эти private entrypoints без обхода через public compatibility paths.
- 2026-04-23: завершён срез 4. `assistants`, `threads`, `a_assistants` и `a_threads` переведены с eager initialization на `cached_property`; добавлены unit tests на ленивое кеширование ресурсов и прогнаны профильные client tests.
- 2026-04-23: завершён срез 5. Корневые legacy compatibility methods `stream`, `chat_parse`, `astream` и `achat_parse` теперь выдают `DeprecationWarning` и делегируют в `client.chat.legacy.*` / `client.achat.legacy.*`; добавлены smoke-tests на deprecated shim warnings и повторно прогнаны chat/client unit tests.
- 2026-04-23: завершён срез 6. Сообщение `_validate_response_format(...)` теперь направляет на `client.chat.legacy.parse(...)` / `client.achat.legacy.parse(...)`, а docstrings в `client.py` и `resources/chat.py` описывают `chat`/`achat` как namespace с legacy surface и помечают root compatibility shims как deprecated; профильные tests на deprecated namespace/shim вызовы прогнаны успешно.
- 2026-04-23: завершён срез 7. `README.md`, `examples/README.md` и публичные notebook-примеры переведены на канонический `client.chat.legacy.*` / `client.achat.legacy.*`, добавлен migration note про deprecated root shims и резервирование namespace под будущий `v2/chat/completions`.
- 2026-04-23: завершён срез 8. Unit tests переведены на канонический `client.chat.legacy.*` / `client.achat.legacy.*`, добавлены явные проверки отсутствия `DeprecationWarning` для legacy resources и кеширования `chat`/`achat` namespaces; локально успешно прогнаны `uv run pytest tests/unit/gigachat/test_client_chat.py`, `tests/unit/gigachat/test_client_chat_parse.py` и `tests/unit/gigachat/test_client_lifecycle.py`.
- 2026-04-23: завершён срез 9. Полный финальный прогон `make fmt`, `make mypy` и `make test` завершён успешно; по ходу прогона исправлены D401 docstrings в deprecated shims и runtime-регрессия в `src/gigachat/resources/chat.py` из-за forward references без `__future__`.
