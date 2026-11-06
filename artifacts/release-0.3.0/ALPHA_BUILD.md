# Alpha candidate build: 0.3.0a1

Date: 2026-11-06. Branch: `feature/gigachat-0.3.0`. Status: unpublished alpha.

The candidate is explicitly designated `0.3.0a1`, with the PyPI classifier
`Development Status :: 3 - Alpha`. The lockfile, README, migration guide and
changelog reflect that decision. Dependency versions and runtime source are unchanged.

## Verification

- `uv lock --check --offline`: passed using the existing validation cache.
- `uv build --out-dir dist`: source distribution and wheel built successfully; the wheel was built from the sdist.
- Wheel metadata reports version `0.3.0a1` and Alpha, with no Production/Stable classifier.
- Every packaged file under `gigachat/` is byte-identical to the previously validated candidate.
- Exact alpha wheel installation, import, version and client-construction smoke passed on Python 3.10.19 and 3.15.0. Neither legacy HTTPX nor aiohttp was installed in these base environments.
- The Russian implementation plan is absent from the wheel. No publication, commit, push or live API request was performed.

The full 950-test plus 33-cassette matrix in [VALIDATION.md](VALIDATION.md) applies
to the unchanged runtime source; it was not rerun for this metadata-only change.
The downstream test results likewise predate the alpha designation. Both root
TODO files now explain explicit alpha selection and the later stable-range update.

Previous unpublished `0.3.0` build artifacts were moved out of `dist` to
`/private/tmp/gigachat-pre-alpha-20261106/` to avoid accidental stable publication.
The 0.3.0 series in `dist` now contains only alpha artifacts. Pre-existing 0.2.4 artifacts were preserved.

## Artifact SHA-256

- `dist/gigachat-0.3.0a1-py3-none-any.whl`: `afd48d588f30787db487e947a57143acbeaa0207dcd7c87c8ff0b1a113e88cb7`
- `dist/gigachat-0.3.0a1.tar.gz`: `dcb74a7dce6624616c5a543d21acea388244ea3f60d241427a849c0584ec598f`
