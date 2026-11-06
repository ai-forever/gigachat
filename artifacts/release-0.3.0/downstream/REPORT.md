# Downstream SDK 0.3.0 series compatibility checks

The current candidate is the unpublished **0.3.0a1 alpha**. The results below used the earlier unpublished 0.3.0 build; packaged runtime code is unchanged. See [ALPHA_BUILD.md](../ALPHA_BUILD.md) for the current artifacts. Both root TODOs now distinguish explicit alpha testing from the eventual stable dependency update.

The findings informed the requested `TODO_GIGACHAT_0_3_0.md` files in the downstream repository roots. Compatibility adaptations were made only in isolated temporary checkouts for testing; no downstream product code, dependency bounds or lockfiles were changed in the original worktrees.

| Project | Source commit tested | Source repository |
|---|---|---|
| GPT2GIGA | `c3e2546095d024e692184088dd38b4766f82f47b` | `/Users/riyakupov/code_projects/gpt2giga` |
| langchain-gigachat | `b62265b8702a59b5691add7ae4de6504ccedd138` | `/Users/riyakupov/PycharmProjects/langchain-gigachat` |

The downstream checks used `dist/gigachat-0.3.0-py3-none-any.whl`, SHA-256 `3b8cc523f0715f9a0350e407d430cd6bb6a303aa33d80baca4522300c80d2d5a`. The wheel archive was placed on `PYTHONPATH`; Python dependencies and pytest were taken from existing downstream environments. This checks imported wheel code with those environments; it is not a clean downstream wheel installation or an all-versions dependency resolution.

## GPT2GIGA

The temporary adaptation changed the SDK requirement to `>=0.3.0,<0.4.0`, removed the private HTTP transport mutation hook, and used `GigaChat.with_options(extra_query=..., extra_body=...)` on scoped client views. Existing header ContextVars were retained; SDK wire fixtures used HTTPX2. The test run included canonical header lookup, cache-session propagation and stream cleanup regressions.

On Python 3.13, the selected contract, SDK-wire, router, configuration, artifact-policy and release-contract tests produced **701 passed, 1 xfailed, 1 failed**. The failure was `test_source_lock_is_current`: `uv.lock` still refers to SDK 0.2.4 and cannot resolve the proposed unpublished 0.3.0 from the local registry cache. `uv lock --offline --check` explicitly reported that only `gigachat<=0.2.4` was available. This remains a release blocker. Synthetic SDK transport tests exercised concurrent option isolation, repeated query keys, body additions, borrowed client lifetime and OAuth option separation. Additional local HTTP-server calls passed with native HTTPX2 and aiohttp. Five Pydantic warnings concerned storage serialization and production-mode wildcard CORS.

## LangChain GigaChat

The temporary adaptation changed the SDK requirement to `>=0.3.0,<0.4`, switched SDK transport mocking from HTTPX to HTTPX2, and added an aiohttp development dependency for backend tests. It retained the existing public integration surface. On Python 3.12, the wheel passed **452 unit tests**, including loopback `ainvoke` with each backend. The aiohttp test selected the backend through the integration's client-initialization override; the temporary adaptation did not add a new public backend configuration field.

Its `uv lock --offline --check` also failed because the local registry contains only SDK versions through 0.2.4. Regenerate and verify the lock after 0.3.0 is published; do not replace it with a machine-specific wheel path.

## Remaining checks

- Implement the downstream TODOs after SDK finalization; regenerate both lockfiles against actual published artifacts and rerun lock checks, package builds, installed-wheel checks, CI matrix, and downstream tests.
- These checks made no live GigaChat API calls and establish no model quality, credentials, permission, or production workload compatibility.
- The GPT2GIGA tests above cover a selected subset, not its entire repository test suite. LangChain tests cover the unit suite, not live integration tests.
