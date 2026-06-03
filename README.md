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
- Manually update the python version in `devenv.nix`
- Manually update the python version in `pyproject.toml`
- Update devenv:
```bash
devenv update
```

- Update uv:
```bash
# Get outdated packages
$ uv tree --outdated --depth 1

# Update package
$ uvpkg=mutagen && uv remove $uvpkg && uv add $uvpkg

# or
$ uv add "mutagen>=1.47.0"
```

uv automatically upgrades versions matching the constraint, and will do so silently, they will not be listed in the outdated packages. `uv tree --outdated` only highlights packages that need to be upgraded manually.