from functools import cache
import io
import json
import os
import re
import shutil
import urllib.parse
import urllib.request
from glob import glob
from PIL import Image
from typing import Optional
from zipfile import ZipFile


class ModReader:
    def __init__(self, base_dir: str, mod_cache_dir: str, username: str, token: str):
        self.mod_cache_dir = mod_cache_dir
        self.mod_to_path = {x: f'{base_dir}/{x}' for x in ['base', 'core']}
        self.username = username
        self.token = token

    def add_mod(self, mod: str) -> None:
        if mod in self.mod_to_path:
            return

        target_dir = f'{self.mod_cache_dir}/{mod}'
        self.mod_to_path[mod] = target_dir
        if not os.path.isdir(target_dir):
            # Attempt to download and extract the file
            print(f'Downloading the latest version of {mod}...')
            mod_data_url = f'https://mods.factorio.com/api/mods/{urllib.parse.quote(mod, safe="")}'
            mod_data = json.loads(urllib.request.urlopen(mod_data_url).read())
            download_url = mod_data['releases'][-1]['download_url']

            zip_url = f'https://mods.factorio.com{download_url}?username={self.username}&token={self.token}'
            zip_request = urllib.request.Request(
                zip_url,
                headers={
                    'User-Agent': 'Joey Marianer is developing a tool. Hoping not to end up eating too much bandwidth. '
                    'Manual downloads only.'})
            zipfile = urllib.request.urlopen(zip_request).read()
            zipfile = ZipFile(io.BytesIO(zipfile))
            os.mkdir(target_dir)
            for file_info in zipfile.filelist:
                target_path = os.path.join(target_dir, *file_info.filename.split(os.sep)[1:])
                if os.path.basename(target_path) == '':
                    continue
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zipfile.open(file_info) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)

    def get_text(self, a_path: str) -> str:
        return self.get_binary(a_path).decode('utf-8')

    def get_binary(self, a_path: str) -> bytes:
        match = re.match('__(.*)__/(.*)', a_path)
        if not match:
            raise

        mod_dir = self.mod_to_path[match[1]]
        filename = match[2]

        with open(f'{mod_dir}/{filename}', 'rb') as x:
            return x.read()

    def glob(self, a_glob: str) -> list[str]:
        match = re.match('__(.*)__/(.*)', a_glob)
        if not match:
            return []

        game_mod = match[1]
        mod_dir = self.mod_to_path[game_mod]
        filename = match[2]

        return [f'__{game_mod}__/' + f.removeprefix(mod_dir)
                for f in glob(f'{mod_dir}/{filename}')]

    @cache
    def get_image(self, path: str) -> Image.Image:
        return Image \
            .open(io.BytesIO(self.get_binary(path))) \
            .convert('RGBA')
