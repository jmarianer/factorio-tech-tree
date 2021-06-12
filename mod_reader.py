import fnmatch
import re
from glob import glob
from os import path
from zipfile import ZipFile


class ModReader:
    def __init__(self, base_dir, mods_dir):
        self.base_dir = base_dir
        self.mods_dir = mods_dir

    def get_text(self, a_path):
        return self.get_binary(a_path).decode('utf-8')

    def get_binary(self, a_path):
        match = re.match('__(.*)__/(.*)', a_path)
        if not match:
            return None

        game_mod = match[1]
        filename = match[2]

        if game_mod in ['base', 'core']:
            with open(f'{self.base_dir}/{game_mod}/{filename}', 'rb') as x:
                return x.read()

        dir_or_zip = glob(f'{self.mods_dir}/{game_mod}*')[-1]
        if path.isdir(dir_or_zip):
            with open(f'{dir_or_zip}/{filename}', 'rb') as x:
                return x.read()

        zipfile = ZipFile(dir_or_zip)
        zipped_names = [n for n in zipfile.namelist() if n.endswith('/' + filename)]
        if len(zipped_names) != 1:
            raise FileNotFoundError

        with zipfile.open(zipped_names[0], 'r') as x:
            return x.read()

    def glob(self, a_glob):
        match = re.match('__(.*)__/(.*)', a_glob)
        if not match:
            return None

        game_mod = match[1]
        filename = match[2]

        if game_mod in ['base', 'core']:
            return [f'__{game_mod}__/' + f.removeprefix(f'{self.base_dir}/{game_mod}/')
                    for f in glob(f'{self.base_dir}/{game_mod}/{filename}')]

        dir_or_zip = glob(f'{self.mods_dir}/{game_mod}*')[-1]
        if path.isdir(dir_or_zip):
            return [f'__{game_mod}__/' + f.removeprefix(f'{dir_or_zip}/')
                    for f in glob(f'{dir_or_zip}/{filename}')]

        zipfile = ZipFile(dir_or_zip)
        return [f'__{game_mod}__/' + '/'.join(f.split('/')[1:])
                for f in fnmatch.filter(zipfile.namelist(), '*/' + filename)]
