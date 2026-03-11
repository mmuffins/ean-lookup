# EAN Checker
Downloads product details into obsidian-compatible markdown files.

## Setup
- Get token from https://ean-db.com/account an put it in a file called `token` in the script folder.
- Create a virtual environment
```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install pip-tools
pip-sync
```

## Upgrading dependencies
- Update dependencies
```powershell
pip-compile --upgrade
```

## Adding dependencies
To install additional dependencies, add them to `requirements.in`  and run
```powershell
pip-compile --upgrade
```

## Running the script

Run the script:
```powershell 
python ean_lookup.py <ean code> -o ./output
```

## Cleanup
If needed, the venv can be deleted
```powershell
deactivate
Remove-Item -Path ./.venv/ -Recurse -Force
```
