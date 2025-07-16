# Factorio browser

## Installation

```
python -m venv venv
. venv/bin/activate
pip install -r requirements.txt
(cd frontend/ && npm i)
```

## Download and create resources

```
# This value of FACTORIO_BASE works on my macOS system. Not sure what the values are for other systems.
# Change the username, of course!
export FACTORIO_BASE='/Users/joeym/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents/data'
export FACTORIO_USERNAME=you
export FACTORIO_TOKEN=12345  # from player-data.json
./test.sh
```

## Run frontend

```
cd frontend
npm start
```


## Linting and type checking

```
mypy . --strict
pycodestyle *.py* lupa/ --max-line-length 120
```
