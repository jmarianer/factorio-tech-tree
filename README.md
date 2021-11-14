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

## Linting and type checking

```
mypy . --strict
pycodestyle *.py* lupa/ --max-line-length 120
```
