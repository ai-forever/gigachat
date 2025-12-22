# GigaChat Usage Examples

In this section you will find examples of working with the GigaChat library:

* Simple generation request:
  * [version](./example_ask.py) with certificate verification disabled;
  * [version](./example_russian_trusted_root_ca.py) with the root certificate of the Russian Ministry of Digital Development.

  In both cases, the example code sends a message to the model and outputs its response.

* [Working with chat](./example_simple_chat.py)
* [Asynchronous work with streaming token processing](./example_streaming_asyncio.py)
* [Mutual TLS (mTLS) authentication](./example_auth_certs_mtls.py)
* [Using optional headers](./example_contextvars.py)

  The example demonstrates how you can pass optional headers `X-Session-ID`, `X-Request-ID` and others using the library.

  Optional headers can be used for various purposes. For example, to simplify logging or for [request caching](https://developers.sber.ru/docs/ru/gigachat/api/keeping-context#keshirovanie-zaprosov).

* [Token counting example](./example_tokens.py)

  The example shows how you can estimate the number of tokens in the data being sent before making a generation request.

* [Embeddings example](./example_embeddings.py)

  The example demonstrates how to get embeddings for text.

* [Functions example](./example_functions.py)

  The example shows how to use function calling with the library, including a DuckDuckGo search integration.

* [AI detection example](./example_ai_check.py)

  The example demonstrates how to check if text was written by AI using the GigaCheckDetection model.

* [Image retrieval example](./example_get_image.py)

  The example shows how to get image.

* [GigaChat Vision example](./vision/example_vision.py)

  The example demonstrates how to work with images using the library and GigaChat API.
