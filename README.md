# Factorio web generator

## Installation

```
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Usage

```
export FACTORIO_USERNAME=you
export FACTORIO_TOKEN=12345  # from player-data.json
python cli.py create-tech-tree --output some_directory --mods IndustrialRevolution
```

See `test.sh` for more examples.

## Type checking

```
mypy . --strict
Success: no issues found in 8 source files
```
