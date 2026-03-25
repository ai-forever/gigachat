from gigachat.models import Chat
from tests.utils import get_bytes, get_json

BASE_URL = "http://base_url"
AUTH_URL = "http://auth_url"

# Mock Credentials (valid base64)
CREDENTIALS = "NmIwNzhlODgtNDlkNC00ZjFmLTljMjMtYjFiZTZjMjVmNTRlOmU3NWJlNjVhLTk4YjAtNGY0Ni1iOWVhLTljMDkwZGE4YTk4MQ=="

# Test authentication values
ACCESS_TOKEN = "access_token"
USER = "user"
PASSWORD = "password"

# Token expiration timestamps (milliseconds)
# 2000-01-01 00:00:00 UTC - always expired
EXPIRES_AT_EXPIRED = 946684800000
# 2100-01-01 00:00:00 UTC - always valid
EXPIRES_AT_VALID = 4102444800000

# Mock token string (same for all variants)
MOCK_TOKEN_STRING = (
    "eyJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUlNBLU9BRVAtMjU2In0."
    "DCXAAnwXjmRleOrIJcXDWbQwsP5UGSptcY3x5XXRkYZm6x3QkDQBL63DKQZzwrwmtuFbKajq6ULHuQhsmGax-l_"
    "R6AhRkr7pWzJi1jpzCenq9PAN2UjF0BX_IiDRgmEExH6_2OtHaJ_7KbudukIOLEgxD9l8WcXFY992dgqLL6eK2n"
    "nnUvyfmr4ITc9PWuAFsMIO6jweNFw0e9vRYEDkAbnv9EGR-w9CGwfBsHNWZwZlo7fyu07fkSfmqmGdBvU434434"
    "4luNNrHwktSGOzNhpLhu0-0A3KI950vmp_37QY8isDi3epGU3HShdrBZkk70fdXxBKQA."
    "MV2IksoyxTV_c-qm6hSXaQ.LUT4JqOzKqmFOR07-Asq7Fhqj_eYSTXcsJAK-JchmM1QUqhPLBXsUyXXh6ZcjsnN"
    "7Q0QXzuBlSjaBWekgWANDirI6HP_MsEM4FxfJAOh73aowC700cEQPPYAxzPYG0d4bOqsZh8Ss57lJB2VM7M6Y2F"
    "cG2hb5Q0i2zPskqSWxXejuCyr2uIlY7Fe4bu4NUqtCaKJVwqriVWLfbA0OzZyA0osDc42Ba0u1adFAdaZDCE."
    "IlKOixP8hSUimEI2pdP118Tx0StZjcLdbSauE5R0YAA"
)

# URLs derived from BASE_URL
CHAT_URL = f"{BASE_URL}/chat/completions"
CHAT_V2_BASE_URL = f"{BASE_URL}/api/v2"
CHAT_V2_URL = f"{BASE_URL}/api/v2/chat/completions"
TOKEN_URL = f"{BASE_URL}/token"
FILES_URL = f"{BASE_URL}/files"
GET_FILE_URL = f"{BASE_URL}/files/1"
GET_FILES_URL = f"{BASE_URL}/files"
FILE_DELETE_URL = f"{BASE_URL}/files/1/delete"
IMAGE_URL = f"{BASE_URL}/files/img_file/content"
MODELS_URL = f"{BASE_URL}/models"
MODEL_URL = f"{BASE_URL}/models/model"
GET_THREADS_URL = f"{BASE_URL}/threads"
GET_THREADS_MESSAGES_URL = f"{BASE_URL}/threads/messages?thread_id=111"
GET_THREADS_RUN_URL = f"{BASE_URL}/threads/run?thread_id=111"
POST_THREAD_MESSAGES_RERUN_URL = f"{BASE_URL}/threads/messages/rerun"
POST_THREAD_MESSAGES_RUN_URL = f"{BASE_URL}/threads/messages/run"
POST_THREADS_DELETE_URL = f"{BASE_URL}/threads/delete"
POST_THREADS_MESSAGES_URL = f"{BASE_URL}/threads/messages"
POST_THREADS_RUN_URL = f"{BASE_URL}/threads/run"
POST_THREADS_RETRIEVE_URL = f"{BASE_URL}/threads/retrieve"
TOKENS_COUNT_URL = f"{BASE_URL}/tokens/count"
BALANCE_URL = f"{BASE_URL}/balance"
CONVERT_FUNCTIONS_URL = f"{BASE_URL}/functions/convert"
VALIDATE_FUNCTION_URL = f"{BASE_URL}/functions/validate"
AI_CHECK_URL = f"{BASE_URL}/ai/check"
EMBEDDINGS_URL = f"{BASE_URL}/embeddings"
BATCHES_URL = f"{BASE_URL}/batches"
BATCH_BY_ID_URL = f"{BASE_URL}/batches?batch_id=batch_1"
GET_ASSISTANTS_URL = f"{BASE_URL}/assistants"
POST_ASSISTANTS_URL = f"{BASE_URL}/assistants"
POST_ASSISTANT_MODIFY_URL = f"{BASE_URL}/assistants/modify"
POST_ASSISTANT_FILES_DELETE_URL = f"{BASE_URL}/assistants/files/delete"
POST_ASSISTANT_DELETE_URL = f"{BASE_URL}/assistants/delete"
MOCK_URL = f"{BASE_URL}/chat/completions"  # Alias for CHAT_URL in some tests

# Test Data - OAuth token variants (/oauth endpoint, access_token/expires_at format)
OAUTH_TOKEN_VALID = {"access_token": MOCK_TOKEN_STRING, "expires_at": EXPIRES_AT_VALID}
OAUTH_TOKEN_EXPIRED = {"access_token": MOCK_TOKEN_STRING, "expires_at": EXPIRES_AT_EXPIRED}

# Test Data - Password auth token variants (/token endpoint, tok/exp format)
PASSWORD_TOKEN_VALID = {"tok": MOCK_TOKEN_STRING, "exp": EXPIRES_AT_VALID}
PASSWORD_TOKEN_EXPIRED = {"tok": MOCK_TOKEN_STRING, "exp": EXPIRES_AT_EXPIRED}
CHAT = Chat.model_validate(get_json("chat.json"))
CHAT_FUNCTION = Chat.model_validate(get_json("chat_function.json"))
CHAT_COMPLETION = get_json("chat_completion.json")
CHAT_COMPLETION_FUNCTION = get_json("chat_completion_function.json")
CHAT_COMPLETION_STREAM = get_bytes("chat_completion.stream")
CHAT_V2 = get_json("chat_v2.json")
CHAT_COMPLETION_V2 = get_json("chat_completion_v2.json")
CHAT_COMPLETION_V2_STREAM = get_bytes("chat_completion_v2.stream")

HEADERS_STREAM = {"Content-Type": "text/event-stream"}
X_CUSTOM_HEADER = "X-Custom-Header"

GET_ASSISTANTS = get_json("assistants/get_assistants.json")
POST_ASSISTANTS = get_json("assistants/post_assistants.json")
POST_ASSISTANT_MODIFY = get_json("assistants/post_assistant_modify.json")
POST_ASSISTANT_FILES_DELETE = get_json("assistants/post_assistant_files_delete.json")
POST_ASSISTANT_DELETE = get_json("assistants/post_assistant_delete.json")

EMBEDDINGS = get_json("embeddings.json")
BATCH = get_json("batch.json")
BATCHES = get_json("batches.json")
BATCHES_LIST = BATCHES["batches"]

FILES = get_json("post_files.json")
GET_FILE = get_json("get_file.json")
GET_FILES = get_json("get_files.json")
FILE_DELETE = get_json("post_files_delete.json")
FILE = get_bytes("image.jpg")
IMAGE = get_bytes("image.jpg")

MODELS = get_json("models.json")
MODEL = get_json("model.json")

GET_THREADS = get_json("threads/get_threads.json")
THREAD = GET_THREADS["threads"][0]
GET_THREADS_MESSAGES = get_json("threads/get_threads_messages.json")
GET_THREADS_RUN = get_json("threads/get_threads_run.json")
POST_THREAD_MESSAGES_RERUN = get_json("threads/post_thread_messages_rerun.json")
POST_THREAD_MESSAGES_RERUN_STREAM = get_bytes("threads/post_thread_messages_rerun.stream")
POST_THREAD_MESSAGES_RUN = get_json("threads/post_thread_messages_run.json")
POST_THREAD_MESSAGES_RUN_STREAM = get_bytes("threads/post_thread_messages_run.stream")
POST_THREADS_DELETE = get_bytes("threads/post_threads_delete.txt")
POST_THREADS_MESSAGES = get_json("threads/post_threads_messages.json")
POST_THREADS_RUN = get_json("threads/post_threads_run.json")
POST_THREADS_RETRIEVE = get_json("threads/post_threads_retrieve.json")

TOKENS_COUNT = get_json("tokens_count.json")
BALANCE = get_json("balance.json")
CONVERT_FUNCTIONS = get_json("convert_functions.json")
FUNCTION_VALIDATION = {
    "status": 200,
    "message": "Function is valid",
    "json_ai_rules_version": "1.0.5",
    "warnings": [{"description": "few_shot_examples are missing", "schema_location": "(root)"}],
}
AI_CHECK = get_json("ai_check.json")
