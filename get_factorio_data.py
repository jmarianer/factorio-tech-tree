import math
from factorio_data import FactorioData
from utils import image_to_data_url


# CONFIG
SUPPORT='/Users/joeym/Library/Application Support'
BASE_DIR=f'{SUPPORT}/Steam/steamapps/common/Factorio/factorio.app/Contents/data'
MODS_DIR=f'{SUPPORT}/Factorio/mods'
MODS=['Krastorio2', 'space-exploration', 'space-exploration-postprocess']


# MAIN
data = FactorioData(BASE_DIR, MODS_DIR, MODS)
tech_and_prereqs = {
        k: set(v.get('prerequisites', []))
        for k, v in data.raw['technology'].items()}
prereqs_available = set()
positions = {}
top = 34
while True:
    new_available = {
            k
            for k, v in tech_and_prereqs.items()
            if v.issubset(prereqs_available)}
    if len(new_available - prereqs_available) == 0:
        break

    left = 20
    for tech_name in new_available - prereqs_available:
        positions[tech_name] = (left, top)
        left += 101
    top += 168
    prereqs_available.update(new_available)


# HTML output, yuck
with open('output/index.html', 'w') as index:
    index.write('''
        <title>Tech Tree</title>
        <link rel="stylesheet" href="../tech-tree.css" />
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
        <script src="../tech-tree.js" charset="UTF-8"></script>
        </head>
        <body>
        <div id="tooltip">
        <div class="tiptitle"></div>
        <div class="tip1 tipheading">Products:</div>
        <div class="tip2"></div>
        <div class="tip3 tipheading">Ingredients:</div>
        <div class="tip4"></div>
        </div>
    ''')

    for tech_name in tech_and_prereqs:
        left, top = positions[tech_name]
        data.get_tech_icon(tech_name).save(f'output/{tech_name}.png')
        title = data.localize('technology-name', tech_name)
        prereqs = ','.join(tech_and_prereqs[tech_name])
        index.write(f'<div style="left:{left}px;top:{top}px" id="{tech_name}" class="tech L1" data-prereqs="{prereqs}" data-title="{title}"><img class="pic" src="{tech_name}.png"></div>\n')

    for t in tech_and_prereqs:
        for p in tech_and_prereqs[t]:
            # Draw a line from (x1, y1) to (x2, y2)
            x1, y1 = positions[t]
            x2, y2 = positions[p]

            x1 += 40
            x2 += 40
            y1 += 34
            y2 += 34

            xmid = (x1 + x2) / 2
            ymid = (y1 + y2) / 2
            angle = math.atan2((y2 - y1), (x2 - x1))
            length = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)

            left = xmid - length / 2
            index.write(f'<div id="{t}_{p}" class="path dark" style="left:{left}px;top:{ymid}px;width:{length}px;transform:rotate({angle}rad)"></div>')
