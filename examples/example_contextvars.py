"""Example of forwarding request headers to GigaChat"""

import asyncio

import gigachat.context
from gigachat import GigaChat

ACCESS_TOKEN = ...

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "X-Session-ID": "8324244b-7133-4d30-a328-31d8466e5502",
    "X-Request-ID": "8324244b-7133-4d30-a328-31d8466e5502",
    "X-Service-ID": "my_custom_service",
    "X-Operation-ID": "my_custom_qna",
    "X-Trace-ID": "trace-id-1234567890",
    "X-Agent-ID": "agent-id-1234567890",
}

# Setting variables for the client
with GigaChat(verify_ssl_certs=False) as giga:
    gigachat.context.authorization_cvar.set(headers.get("Authorization"))
    gigachat.context.session_id_cvar.set(headers.get("X-Session-ID"))
    gigachat.context.request_id_cvar.set(headers.get("X-Request-ID"))
    gigachat.context.service_id_cvar.set(headers.get("X-Service-ID"))
    gigachat.context.operation_id_cvar.set(headers.get("X-Operation-ID"))
    gigachat.context.trace_id_cvar.set(headers.get("X-Trace-ID"))
    gigachat.context.agent_id_cvar.set(headers.get("X-Agent-ID"))
    gigachat.context.custom_headers_cvar.set({"X-Custom-Header": "CustomValue"})

    response = giga.chat("What factors affect the cost of home insurance?")
    print(response.choices[0].message.content)


# Setting variables for each call (async only)
async def ask_with_headers(giga, some_custom_header, prompt):
    gigachat.context.custom_headers_cvar.set({"X-Custom-Header": some_custom_header})

    response = await giga.achat(prompt)
    print(response.choices[0].message.content)


async def async_main():
    async with GigaChat(verify_ssl_certs=False) as giga:
        await asyncio.gather(
            ask_with_headers(giga, "CustomValue 1", "Who made you?"),
            ask_with_headers(giga, "CustomValue 2", "What is your name?"),
        )


if __name__ == "__main__":
    asyncio.run(async_main())
