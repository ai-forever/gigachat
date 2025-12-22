"""Example - using functions.
The ddgs utility is used for the search system.
Install the corresponding library using the command

pip install -U ddgs
"""

import json
import os

from ddgs import DDGS

from gigachat import GigaChat
from gigachat.models import Chat, Function, FunctionParameters, Messages, MessagesRole

if "GIGACHAT_CREDENTIALS" not in os.environ:
    os.environ["GIGACHAT_CREDENTIALS"] = input("GigaChat Credentials: ")

if "GIGACHAT_SCOPE" not in os.environ:
    os.environ["GIGACHAT_SCOPE"] = input("GigaChat Scope: ")


def search_ddg(search_query):
    """
    Search in DuckDuckGo.

    Useful when you need to answer questions about current events.
    The input should be a search query.
    """
    return DDGS().text(search_query, max_results=10)


with GigaChat(verify_ssl_certs=False) as giga:
    search = Function(
        name="duckduckgo_search",
        description="""Search in DuckDuckGo.
Useful when you need to answer questions about current events.
The input should be a search query.""",
        parameters=FunctionParameters(
            type="object",
            properties={"query": {"type": "string", "description": "Search query"}},
            required=["query"],
        ),
    )

    messages = []
    function_called = False
    while True:
        # If the previous LLM response was not a function call - ask the user to continue the dialogue
        if not function_called:
            query = input("\033[92mUser: \033[0m")
            messages.append(Messages(role=MessagesRole.USER, content=query))

        chat = Chat(messages=messages, functions=[search])

        resp = giga.chat(chat).choices[0]
        mess = resp.message
        messages.append(mess)

        print("\033[93m" + f"Bot: \033[0m{mess.content}")

        function_called = False
        func_result = ""
        if resp.finish_reason == "function_call":
            print("\033[90m" + f"  >> Processing function call {mess.function_call}" + "\033[0m")
            if mess.function_call.name == "duckduckgo_search":
                query = mess.function_call.arguments.get("query", None)
                if query:
                    func_result = search_ddg(query)
            print("\033[90m" + f"  << Function result: {func_result}\n\n" + "\033[0m")

            messages.append(
                Messages(role=MessagesRole.FUNCTION, content=json.dumps({"result": func_result}, ensure_ascii=False))
            )
            function_called = True
