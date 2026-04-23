from gigachat.models.legacy_chat import (
    LegacyChat,
    LegacyChatCompletion,
    LegacyChatCompletionChunk,
    LegacyChatFunctionCall,
    LegacyChoice,
    LegacyChoiceChunk,
    LegacyFewShotExample,
    LegacyFunction,
    LegacyFunctionCall,
    LegacyFunctionParameters,
    LegacyFunctionParametersProperty,
    LegacyMessage,
    LegacyMessageChunk,
    LegacyMessageRole,
    LegacyStorage,
    LegacyUsage,
)


class FunctionCall(LegacyFunctionCall):
    pass


class FewShotExample(LegacyFewShotExample):
    pass


class Storage(LegacyStorage):
    pass


class Usage(LegacyUsage):
    pass


class FunctionParametersProperty(LegacyFunctionParametersProperty):
    pass


class FunctionParameters(LegacyFunctionParameters):
    pass


class Function(LegacyFunction):
    pass


class ChatFunctionCall(LegacyChatFunctionCall):
    pass


MessagesRole = LegacyMessageRole


class Messages(LegacyMessage):
    pass


class MessagesChunk(LegacyMessageChunk):
    pass


class Choices(LegacyChoice):
    pass


class ChoicesChunk(LegacyChoiceChunk):
    pass


class Chat(LegacyChat):
    pass


class ChatCompletion(LegacyChatCompletion):
    pass


class ChatCompletionChunk(LegacyChatCompletionChunk):
    pass


__all__ = (
    "Chat",
    "ChatCompletion",
    "ChatCompletionChunk",
    "ChatFunctionCall",
    "Choices",
    "ChoicesChunk",
    "FewShotExample",
    "Function",
    "FunctionCall",
    "FunctionParameters",
    "FunctionParametersProperty",
    "LegacyChat",
    "LegacyChatCompletion",
    "LegacyChatCompletionChunk",
    "LegacyChatFunctionCall",
    "LegacyChoice",
    "LegacyChoiceChunk",
    "LegacyFewShotExample",
    "LegacyFunction",
    "LegacyFunctionCall",
    "LegacyFunctionParameters",
    "LegacyFunctionParametersProperty",
    "LegacyMessage",
    "LegacyMessageChunk",
    "LegacyMessageRole",
    "LegacyStorage",
    "LegacyUsage",
    "Messages",
    "MessagesChunk",
    "MessagesRole",
    "Storage",
    "Usage",
)
