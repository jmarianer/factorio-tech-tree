# ./env is assumed to export the FACTORIO_BASE, FACTORIO_USERNAME and
# FACTORIO_TOKEN variables, and is never checked into git for obvious reasons.
source ./env
mkdir -p output/{base,spacex,ind,angelbobs}

python cli.py dump-data
python cli.py dump-data --mods space-exploration --mods space-exploration-postprocess
python cli.py dump-data --mods IndustrialRevolution
python cli.py dump-data --mods SpaceMod --mods angelsaddons-storage --mods angelsbioprocessing --mods angelspetrochem --mods angelsrefining --mods angelssmelting --mods bobassembly --mods bobelectronics --mods bobenemies --mods bobequipment --mods bobinserters --mods boblibrary --mods boblogistics --mods bobmining --mods bobmodules --mods bobores --mods bobplates --mods bobpower --mods bobrevamp --mods bobtech --mods bobwarfare


python cli.py create-tech-tree --output output/base
python cli.py create-tech-tree --output output/spacex --mods space-exploration --mods space-exploration-postprocess
python cli.py create-tech-tree --output output/ind --mods IndustrialRevolution
python cli.py create-tech-tree --output output/angelbobs --mods SpaceMod --mods angelsaddons-storage --mods angelsbioprocessing --mods angelspetrochem --mods angelsrefining --mods angelssmelting --mods bobassembly --mods bobelectronics --mods bobenemies --mods bobequipment --mods bobinserters --mods boblibrary --mods boblogistics --mods bobmining --mods bobmodules --mods bobores --mods bobplates --mods bobpower --mods bobrevamp --mods bobtech --mods bobwarfare
