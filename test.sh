# The FACTORIO_BASE, FACTORIO_USERNAME and FACTORIO_TOKEN variables must be
# exported in the calling shell.
mkdir -p frontend/public/generated/{base,spacex,ind,angelbobs,k2spacex}

set -x
time python backend/cli.py dump-data -q --output frontend/public/generated/base
time python backend/cli.py dump-data -q --output frontend/public/generated/spacex --mods space-exploration --mods space-exploration-postprocess
time python backend/cli.py dump-data -q --output frontend/public/generated/ind --mods IndustrialRevolution
time python backend/cli.py dump-data -q --output frontend/public/generated/k2spacex --mods space-exploration --mods space-exploration-postprocess --mods Krastorio2

# Bugs in the preprocessor prevent Krastorio2 or Angelbob's mods from working at this time.
# time python backend/cli.py dump-data -q --output frontend/public/generated/angelbobs --mods SpaceMod --mods angelsaddons-storage --mods angelsbioprocessing --mods angelspetrochem --mods angelsrefining --mods angelssmelting --mods bobassembly --mods bobelectronics --mods bobenemies --mods bobequipment --mods bobinserters --mods boblibrary --mods boblogistics --mods bobmining --mods bobmodules --mods bobores --mods bobplates --mods bobpower --mods bobrevamp --mods bobtech --mods bobwarfare
