# PLANS Progress

План: `docs/internal/PLANS.md`

## Правила

- Один чат = один срез из раздела `Предлагаемый порядок работы`.
- После каждого завершённого среза делается отдельный commit.
- Статус каждого среза фиксируется в этом файле до перехода к следующему.

## Срезы

1. `[done]` Создать `src/gigachat/resources/chat.py` и `src/gigachat/resources/__init__.py`.
2. `[pending]` Добавить `cached_property` namespaces/resources в client classes.
3. `[pending]` Вынести текущую legacy chat-логику в private helper methods.
4. `[pending]` Перевести `assistants` / `threads` / `a_assistants` / `a_threads` на `cached_property`.
5. `[pending]` Добавить deprecated shims.
6. `[pending]` Обновить error messages/docstrings.
7. `[pending]` Обновить README/examples.
8. `[pending]` Добавить/обновить unit tests.
9. `[pending]` Прогнать `make fmt`, `make mypy`, `make test`.

## Журнал

- 2026-04-23: завершён срез 1. Добавлен пакет `src/gigachat/resources/` с chat namespace/resource-классами и зафиксированы правила исполнения плана.
