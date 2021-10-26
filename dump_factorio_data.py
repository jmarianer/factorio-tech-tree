import json

from factorio_data import FactorioData

# CONFIG
SUPPORT='/Users/joeym/Library/Application Support'
BASE_DIR=f'{SUPPORT}/Steam/steamapps/common/Factorio/factorio.app/Contents/data'
MODS_DIR=f'{SUPPORT}/Factorio/mods'
MODS=['IndustrialRevolution']


# MAIN
print('Getting Factorio data...')
data = FactorioData(BASE_DIR, MODS_DIR, MODS)

with open('data.json', 'w') as f:
    f.write(json.dumps(data.raw, sort_keys=True, indent=4))
