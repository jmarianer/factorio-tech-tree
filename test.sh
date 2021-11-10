# ./env is assumed to export the FACTORIO_BASE, FACTORIO_USERNAME and
# FACTORIO_TOKEN variables, and is never checked into git for obvious reasons.
source ./env
python cli.py dump-data
python cli.py dump-data --mods space-exploration --mods space-exploration-postprocess
python cli.py dump-data --mods IndustrialRevolution
python cli.py dump-data --mods SpaceMod --mods angelsaddons-storage --mods angelsbioprocessing --mods angelspetrochem --mods angelsrefining --mods angelssmelting --mods bobassembly --mods bobelectronics --mods bobenemies --mods bobequipment --mods bobinserters --mods boblibrary --mods boblogistics --mods bobmining --mods bobmodules --mods bobores --mods bobplates --mods bobpower --mods bobrevamp --mods bobtech --mods bobwarfare

