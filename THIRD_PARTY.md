# Third-party notices

## Tokamak explainer

The integrated Tokamak snapshot is from [shawnq-msft/voice-anatomy](https://github.com/shawnq-msft/voice-anatomy), under the MIT license. Its upstream license is reproduced in `sources/tokamak/LICENSE`. Lucas Lab adds navigation and a noindex tag; scientific citations remain in the page.

## Python runtime

The files in `practice/runtime/` are unmodified Pyodide 0.27.7 release artifacts, downloaded from `https://cdn.jsdelivr.net/pyodide/v0.27.7/full/` (except the license copies). Pyodide is distributed under MPL-2.0; see `practice/runtime/LICENSE`. Corresponding source: https://github.com/pyodide/pyodide/tree/0.27.7 . Build and dependency instructions are in that source tree. No runtime files were modified.

The bundled CPython is 3.12.7 (see `pyodide-lock.json`), under the Python Software Foundation license and its included third-party notices, reproduced in `practice/runtime/CPYTHON-LICENSE`. Corresponding source: https://github.com/python/cpython/tree/v3.12.7 .

`runtime-sha256.json` records the original distributed runtime hashes for reproducibility. Optional packages in the lockfile are not downloaded by this learning app.
