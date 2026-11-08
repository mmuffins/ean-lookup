# EAN Checker
Downloads product details into obsidian-compatible markdown files.

## Running
- Get token from https://ean-db.com/account an put it in a file called `token` in the script folder.
- Load devenv, only needed on linux
Linux:
```bash
$ devenv shell
```
- Run the script:
Linux:
```bash
$ uv run ean_lookup.py -o '[TARGET_DIRECTORY] [EAN code]'
```

## Updating
```bash
devenv update
devenv shell
uv sync --upgrade
```

This updates devenv, nixpkgs, Python, uv, and all Python dependencies allowed by
`pyproject.toml`. Only raise `requires-python` in `pyproject.toml` when intentionally dropping support for older Python.

- Update uv:
```bash
# List all top level packages and show which need to be
$ uv tree --outdated --depth 1

# Update package
$ uvpkg=eandb && uv remove $uvpkg && uv add $uvpkg

# or
$ uv add "eandb>=1.47.0"
```

uv automatically upgrades versions matching the constraint, and will do so silently, they will not be listed in the outdated packages. `uv tree --outdated` only highlights packages that need to be upgraded manually.
