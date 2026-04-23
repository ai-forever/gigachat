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
5. `[pending]` Добавить deprecated shims.
6. `[pending]` Обновить error messages/docstrings.
7. `[pending]` Обновить README/examples.
8. `[pending]` Добавить/обновить unit tests.
9. `[pending]` Прогнать `make fmt`, `make mypy`, `make test`.

## Журнал

- 2026-04-23: завершён срез 1. Добавлен пакет `src/gigachat/resources/` с chat namespace/resource-классами и зафиксированы правила исполнения плана.
- 2026-04-23: завершён срез 2. `client.chat` и `client.achat` переведены на `cached_property` namespace-объекты; для рабочей маршрутизации добавлены private legacy chat helper methods, но отдельные deprecated shims и doc updates остаются следующими срезами.
- 2026-04-23: завершён срез 3. Legacy chat-логика окончательно закреплена за private helper methods в `client.py`, а `resources/chat.py` использует только эти private entrypoints без обхода через public compatibility paths.
- 2026-04-23: завершён срез 4. `assistants`, `threads`, `a_assistants` и `a_threads` переведены с eager initialization на `cached_property`; добавлены unit tests на ленивое кеширование ресурсов и прогнаны профильные client tests.
