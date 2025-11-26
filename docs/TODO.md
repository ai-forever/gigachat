# Refactoring Progress

## General
- [x] Initial setup

## Resource Leak in Hybrid Client
- [x] Fix Resource Leak in Hybrid Client (Lazy Initialization)
  - [x] Refactor `GigaChatSyncClient` to use lazy initialization for `_client` and `_auth_client`
  - [x] Refactor `GigaChatAsyncClient` to use lazy initialization for `_aclient` and `_auth_aclient`
  - [x] Update `close()` and `aclose()` to only close initialized clients
  - [x] Add regression test `tests/unit_tests/gigachat/test_lazy_init.py`
