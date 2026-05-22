# Формат primary `chat/completions`

Этот документ фиксирует wire-format нового primary chat surface, который в рабочих материалах иногда назывался `v2`.

Источник:
- `request_v2.pdf`
- `response_v2.pdf`
- текущая tolerантная реализация SDK в `src/gigachat/models/chat_completions.py`

## Что важно заранее

- Это отдельный контракт, а не расширение legacy `chat`-формата.
- SDK намеренно парсит его не слишком строго: в моделях включен `extra="allow"`.
- `messages[].content` в PDF описан как массив частей, но в примерах и живом трафике может приходить строкой. SDK нормализует строку, объект и массив к списку частей.
- Request-модель SDK шире PDF: некоторые поля response-message принимаются в `ChatMessage` для round-trip/толерантного парсинга, но wire-format request ниже описан по `request_v2.pdf`.
- Для совместимости SDK также принимает `tool_state_id` и `functions_state_id` как alias для `tools_state_id`.
- В response SDK принимает `created` как alias для `created_at`.

## Request

Корневой объект запроса соответствует `ChatCompletionRequest`.

### Root fields

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `model` | `string` | условно | Идентификатор модели. Может быть опущен, если запрос идет через `assistant_id` или в уже существующий `storage.thread_id`. |
| `assistant_id` | `string` | нет | Идентификатор ассистента. Для stateful-сценария передается при создании треда, только в первом сообщении; для stateless - в каждом запросе, где нужен ассистент. Нельзя передавать вместе с `model`; при передаче `storage.thread_id` не передается. |
| `messages` | `array[object]` | да | История чата. |
| `tools_state_id` | `string` | нет | Идентификатор состояния tool execution. |
| `model_options` | `object` | нет | Параметры генерации модели, reasoning и формат ответа. |
| `stream` | `bool` | нет | Включает SSE-streaming, поток завершается `data: [DONE]`. |
| `disable_filter` | `bool` | нет | Выключение фильтрации. |
| `filter_config` | `object` | нет | Тонкая настройка фильтрации. |
| `flags` | `array[string]` | нет | Фича-флаги, например `preprocess`. |
| `storage` | `object` или `bool` | нет | Параметры stateful-хранения контекста. `bool` указан как future-режим. |
| `ranker_options` | `object` | нет | Настройки ранжирования tools/functions. |
| `user_info` | `object` | нет | Дополнительная информация о пользователе, например timezone. |
| `tool_config` | `object` | нет | Политика вызова tools/functions. |
| `tools` | `array[object]` | нет | Доступные built-in tools и client functions. |

### `messages[]`

Каждый элемент массива соответствует `ChatMessage`.

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `role` | `string` | да | Роль сообщения. В PDF явно перечислены `user`, `system`, `assistant`, `tool`, `reasoning`; контракт допускает и другие роли. |
| `tools_state_id` | `string` | нет | Состояние работы с tools на уровне сообщения. |
| `content` | `array[object]` | условно | Контент сообщения. Обязателен для `role="system"`, для остальных ролей может отсутствовать. На практике SDK также принимает строку или один объект и нормализует их в список частей. |

### `content[]`

Каждая часть соответствует `ChatContentPart`.

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `inline_data` | `object` | нет | Дополнительные данные части, например `sources` от SP. |
| `text` | `string` | нет | Текстовая часть сообщения. |
| `files` | `array[object]` | нет | Информация о предзагруженном файле. |
| `function_result` | `object` | нет | Результат вызова клиентской функции внутри content-part. |
| `function_call` | `object` | нет | Инструкция на вызов клиентской функции внутри content-part. |

Структура `function_result`:

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `name` | `string` | да | Наименование функции. |
| `result` | `object` или `string` | да | Результат выполнения функции. |

Структура `function_call`:

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `name` | `string` | да | Наименование функции. |
| `arguments` | `object` | да | Аргументы функции в формате словаря. |

Структура `files[]`:

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `id` | `string` | да | Идентификатор предзагруженного файла. В SDK это поле маппится в `ChatContentFile.id_`. |

Структура `inline_data`:

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `sources` | `object` | нет | Карта источников вида `{id: {url, title}}`. |
| `images` | `array[object]` | нет | Дополнительные изображения. |

### `model_options`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `preset` | `string` | Пресет модели/фильтра/LoRA. |
| `temperature` | `number` | Температура сэмплирования. Дефолт зависит от модели. |
| `top_p` | `number` | Nucleus sampling, значение от 0 до 1. Дефолт зависит от модели. |
| `max_tokens` | `integer` | Лимит выходных токенов, допустимое значение > 0. В PDF указан дефолт `1024`. |
| `repetition_penalty` | `number` | Штраф за повторения, допустимое значение > 0. Дефолт зависит от модели. |
| `update_interval` | `number` | Частота отправки токенов в stream-режиме. По умолчанию `0`: токены отправляются сразу после генерации; значение `1` означает отправку накопленных токенов раз в секунду. |
| `unnormalized_history` | `bool` | Отключение серверной нормализации истории. По умолчанию `false`; нормализация может заменять одиночный `system` на `user` и конкатенировать соседние `user`/`assistant` сообщения. |
| `top_logprobs` | `integer` | Сколько top tokens вернуть в `logprobs`. Функциональность закрыта permission, допустимые значения от 1 до 5. |
| `reasoning` | `object` | Настройки reasoning. |
| `response_format` | `object` | Настройки формата ответа модели. |

### `model_options.reasoning`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `effort` | `string` | Степень reasoning. В PDF перечислены `low`, `medium`, `high`, при этом указано, что сейчас фактически используется только `medium`. |

### `model_options.response_format`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `type` | `string` | Формат ответа: `text`, `json_schema` или `regex`. |
| `schema` | `object` | JSON Schema ответа. Обязательна при `type="json_schema"`. В SDK дополнительно допускается Pydantic model/class, которая конвертируется в schema, и tolerant string-payload. |
| `strict` | `bool` | Строгое соответствие схеме. |
| `regex` | `string` | Регулярное выражение. Обязательно при `type="regex"`. |

### `filter_config`

`filter_config` закрыт permissions, но в PDF описана такая структура:

| Поле | Тип | Назначение |
| --- | --- | --- |
| `request_content.neuro` | `bool` | Проверка запроса моделью-цензором. |
| `request_content.blacklist` | `bool` | Проверка запроса по blacklist-правилам. |
| `request_content.whitelist` | `bool` | Проверка специальных whitelist-триггеров. |
| `response_content.blacklist` | `bool` | Проверка ответа по blacklist-правилам. |

### `storage`

`storage` описан в PDF как `object || bool` с пометкой, что `bool` - future-режим. Если передан пустой object, запрос все равно считается stateful, просто тред еще не создан.

| Поле | Тип | Назначение |
| --- | --- | --- |
| `limit` | `integer` | Сколько сообщений исторического контекста отправлять в модель. Если в истории есть `system` или инструкция ассистента, к лимиту добавляется системный промпт; если параметр не передан, отправляется весь контекст. |
| `thread_id` | `string` | Идентификатор треда. Не заполняется для первого сообщения. |
| `metadata` | `object` | Метаданные треда. Если передается к существующему треду, значение перезаписывается; если поле не передано, текущее значение не меняется. |

### `ranker_options`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `enabled` | `bool` | Включение ранжирования tools/functions. |
| `top_n` | `integer` | Сколько tools/functions передать в модель после ранжирования. |
| `embeddings_model` | `string` | Алиас эмбеддера для ранжирования. |

### `user_info`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `timezone` | `string` | IANA timezone, например `Europe/Moscow`. |

### `tool_config`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `mode` | `string` | Режим вызова: `auto`, `none`, `forced`. |
| `tool_name` | `string` | Имя built-in tool для `mode="forced"`. |
| `function_name` | `string` | Имя client function для `mode="forced"`. |

### `tools[]`

Каждый элемент - oneof-конфигурация одного tool.

Поддержанные поля в PDF и в SDK:

| Поле | Тип | Назначение |
| --- | --- | --- |
| `code_interpreter` | `object` | Built-in code interpreter. |
| `image_generate` | `object` | Built-in text-to-image tool. |
| `web_search` | `object` | Built-in web search. |
| `url_content_extraction` | `object` | Built-in URL extraction. |
| `model_3d_generate` | `object` | Built-in 3D generation. |
| `functions` | `object` | Client-defined functions. |

`tools[].web_search`:

| Поле | Тип | Назначение |
| --- | --- | --- |
| `type` | `string` | Тип поиска: `web_search`, `actual_info_web_search`, `safe_search`. По умолчанию `web_search`; для `safe_search` не нужен `get_datetime`. |
| `indexes` | `array[string]` | Индексы провайдера поиска. |
| `flags` | `array[string]` | Флаги провайдера поиска. |

`tools[].functions.specifications[]`:

| Поле | Тип | Обязательность | Назначение |
| --- | --- | --- | --- |
| `name` | `string` | да | Имя функции. |
| `description` | `string` | да | Описание функции. |
| `parameters` | `object` | да | JSON Schema параметров. |
| `few_shot_examples` | `array[object]` | нет | Примеры сопоставления user request -> params. |
| `return_parameters` | `object` | нет | JSON Schema возвращаемого значения. |

## Response

Корневой объект ответа соответствует `ChatCompletionResponse`, а stream-фрагменты - `ChatCompletionChunk`.

### Root fields

| Поле | Тип | Назначение |
| --- | --- | --- |
| `model` | `string` | Имя модели, которая реально обработала запрос. |
| `thread_id` | `string` | Идентификатор треда, если включено storage. |
| `created_at` | `unix time` | Время создания ответа. SDK также принимает alias `created`. |
| `messages` | `array[object]` | Возвращенные сообщения или их фрагменты. |
| `message_id` | `string` | Идентификатор сообщения. На практике может находиться и внутри `messages[]`; SDK допускает top-level поле. |
| `usage` | `object` | Токен-usage. |
| `tool_execution` | `object` | Состояние top-level built-in tool execution. |
| `logprobs` | `array[object]` | Top-level логарифмические вероятности. |
| `additional_data` | `array[object]` | Дополнительные метаданные ответа. SDK сохраняет элементы как opaque objects без детализации закрытых permission-полей. |

### `messages[]`

Структура сообщения ответа в целом совпадает с request message:

| Поле | Тип | Назначение |
| --- | --- | --- |
| `message_id` | `string` | Идентификатор сообщения. В PDF описан внутри `messages[]`. |
| `role` | `string` | Роль участника диалога. |
| `tools_state_id` | `string` | Состояние работы с tools. |
| `content` | `array[object]` | Контент сообщения. |
| `function_call` | `object` | Вызов client function, предложенный моделью. |
| `tool_execution` | `object` | Состояние built-in tool execution. |
| `logprobs` | `array[object]` | Логарифмические вероятности токенов. |
| `finish_reason` | `string` | Причина завершения генерации. |

### `messages[].content[]`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `inline_data` | `object` | Дополнительные данные. |
| `text` | `string` | Текст сообщения для `type="text"`. |
| `files` | `array[object]` | Идентификаторы сгенерированных файлов. |
| `function_call` | `object` | Политика вызова функции. |

`messages[].content[].inline_data`:

| Поле | Тип | Назначение |
| --- | --- | --- |
| `sources` | `object` | Список ссылок. |
| `images` | `array[object]` | Список картинок. |
| `widgets` | `array[object]` | Виджеты из ответа v2/retrieval при вызове search. Передаются без валидации, as-is. |

`messages[].content[].files[]`:

| Поле | Тип | Назначение |
| --- | --- | --- |
| `target` | `string` | Назначение файла: `image`, `audio`, `cover`, `video`, `3dmodel`. |
| `id` | `string` | Идентификатор файла. |
| `mime` | `string` | MIME type файла. |

`messages[].content[].function_call`:

| Поле | Тип | Назначение |
| --- | --- | --- |
| `name` | `string` | Наименование функции. |
| `arguments` | `object` | Аргументы функции в формате словаря. |

### `usage`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `input_tokens` | `int` | Токены входного запроса. |
| `input_tokens_details.cached_tokens` | `int` | Кешированные входные токены. |
| `output_tokens` | `int` | Токены ответа. |
| `total_tokens` | `int` | Суммарное потребление. |

### `tool_execution`

| Поле | Тип | Назначение |
| --- | --- | --- |
| `name` | `string` | Имя платформенного инструмента, например `image_generation`. |
| `status` | `string` | `success` или `fail`. |
| `seconds_left` | `int` | Оценка оставшегося времени, прежде всего для stream. |
| `censored` | `bool` | Признак срабатывания фильтра. |

### `logprobs`

Каждый элемент:

| Поле | Тип | Назначение |
| --- | --- | --- |
| `chosen` | `object` | Выбранный токен. |
| `top` | `array[object]` | Наиболее вероятные токены для позиции. |

Структура токена:

| Поле | Тип | Назначение |
| --- | --- | --- |
| `token` | `string` | Текст токена. |
| `token_id` | `integer` | Идентификатор токена. |
| `logprob` | `float` | Логарифмическая вероятность. |

## Минимальные примеры

### Request

```json
{
  "model": "GigaChat",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "text": "Найди свежий курс евро и приложи источники."
        }
      ]
    }
  ],
  "model_options": {
    "temperature": 0.2,
    "max_tokens": 512
  },
  "tool_config": {
    "mode": "auto"
  },
  "tools": [
    {
      "web_search": {
        "type": "web_search"
      }
    }
  ],
  "user_info": {
    "timezone": "Europe/Moscow"
  }
}
```

### Response

```json
{
  "model": "GigaChat-2-Max",
  "created_at": 1760000000,
  "thread_id": "thread_123",
  "messages": [
    {
      "role": "assistant",
      "content": [
        {
          "text": "Официальный курс евро на сегодня ..."
        }
      ],
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "input_tokens": 120,
    "input_tokens_details": {
      "cached_tokens": 64
    },
    "output_tokens": 48,
    "total_tokens": 168
  }
}
```
