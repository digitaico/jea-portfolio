# GEMINI

+ When running Python tools prefer to use `python3` instead of `python` unless otherwise specified.
+ When running Python tools, prefer to use ivs where possible.
+ When installing Python packages, prefer to use `uv` and endure you are installing to a virtual environment.
## Mandatory Tooling
To ensure Python code adheres to required standards, the following commands **must** be run before creating or modifying any 
`.py` files.  These commands will automatically fix many common issues and flag any that require manual intervention. T
he commands must be run from the root of the project:

1.  **Check and fix linting issues:**
```bash
uvx ruff@latest check --fix .
```
2.  **Format the code:**
```bash
uvx ruff@latest format .
```
