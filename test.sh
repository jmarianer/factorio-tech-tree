# The FACTORIO_BASE, FACTORIO_USERNAME and FACTORIO_TOKEN variables must be
# exported in the calling shell.
mkdir -p output/{base,spacex,ind,angelbobs,k2spacex}

python cli.py dump-data -q --output output/base.json
python cli.py dump-data -q --output output/spacex.json --mods space-exploration --mods space-exploration-postprocess
python cli.py dump-data -q --output output/k2spacex.json --mods space-exploration --mods space-exploration-postprocess --mods Krastorio2
python cli.py dump-data -q --output output/ind.json --mods IndustrialRevolution
python cli.py dump-data -q --output output/angelbobs.json --mods SpaceMod --mods angelsaddons-storage --mods angelsbioprocessing --mods angelspetrochem --mods angelsrefining --mods angelssmelting --mods bobassembly --mods bobelectronics --mods bobenemies --mods bobequipment --mods bobinserters --mods boblibrary --mods boblogistics --mods bobmining --mods bobmodules --mods bobores --mods bobplates --mods bobpower --mods bobrevamp --mods bobtech --mods bobwarfare


python cli.py create-tech-tree -q --output output/base
python cli.py create-tech-tree -q --output output/k2spacex --mods space-exploration --mods space-exploration-postprocess --mods Krastorio2
python cli.py create-tech-tree -q --output output/spacex --mods space-exploration --mods space-exploration-postprocess
python cli.py create-tech-tree -q --output output/ind --mods IndustrialRevolution
python cli.py create-tech-tree -q --output output/angelbobs --mods SpaceMod --mods angelsaddons-storage --mods angelsbioprocessing --mods angelspetrochem --mods angelsrefining --mods angelssmelting --mods bobassembly --mods bobelectronics --mods bobenemies --mods bobequipment --mods bobinserters --mods boblibrary --mods boblogistics --mods bobmining --mods bobmodules --mods bobores --mods bobplates --mods bobpower --mods bobrevamp --mods bobtech --mods bobwarfare
