import os
import re
from glob import glob
from zipfile import ZipFile


class ModReader:
    def __init__(self, base_dir, mod_cache_dir):
        self.mod_cache_dir = mod_cache_dir
        self.mod_to_path = {x: f'{base_dir}/{x}' for x in ['base', 'core']}

    def add_mod(self, mod, version=None):
        if mod in self.mod_to_path:
            return

        target = f'{self.mod_cache_dir}/{mod}'
        if os.path.isdir(target):
            self.mod_to_path[mod] = target
        else:
            raise FileNotFoundError

    def get_text(self, a_path):
        return self.get_binary(a_path).decode('utf-8')

    def get_binary(self, a_path):
        match = re.match('__(.*)__/(.*)', a_path)
        if not match:
            return None

        mod_dir = self.mod_to_path[match[1]]
        filename = match[2]

        with open(f'{mod_dir}/{filename}', 'rb') as x:
            return x.read()

    def glob(self, a_glob):
        match = re.match('__(.*)__/(.*)', a_glob)
        if not match:
            return None

        game_mod = match[1]
        mod_dir = self.mod_to_path[game_mod]
        filename = match[2]

        return [f'__{game_mod}__/' + f.removeprefix(mod_dir)
                for f in glob(f'{mod_dir}/{filename}')]
