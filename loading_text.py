

import subprocess
import json
from pathlib import Path
import configparser
from yaml import load, CSafeLoader


def to_json(save_path: str,json_path: str) :

    """ Creates Json from ck3 save file using rakaly. Save can be ironman. jq is used to truncate the json from unuseful
     info to increasing load time"""

    command = (
        f'rakaly json --duplicate-keys group --format utf-8 "{save_path}" | jq -c '
        f'"{{landed_titles: .landed_titles.landed_titles, '
        'dynasties: .dynasties.dynasty_house, characters: (.living + .dead_unprunable + '
        f'.characters.dead_prunable),religion: .religion.faiths, culture: .culture_manager.cultures}}" > "{json_path}"'
    )
    result = subprocess.run(command, shell=True, stderr = subprocess.PIPE, text=True)
    stderr = result.stderr

    if stderr:
        return stderr
    return print(f'JSON Created in {json_path}')


class Load:
    def __init__(self):

        # Create a ConfigParser object
        config = configparser.ConfigParser()

        # Read the configuration file
        config.read('config.ini')

        # Access values from the configuration file
        self.ck3_path = config.get('Default', 'CK3 DIRECTORY')
        self.save_path = config.get('Default', 'GAME SAVE DIRECTORY')
        if 'CK3 RESOURCE DIRECTORY' in config['Default']:
            self.resource_path = config.get('Default', 'CK3 RESOURCE DIRECTORY')
        else:
            self.resource_path = './resources'
        self.loc_path = None
        self.processed_yml = []
        self.processed_traits =[]

    def get_loc_path(self, local_lang='english'):

        """Localization only supports english currently. Search if all localization paths are correct and add
        them into a list for processing. The YAML files are non and requires some corrections"""

        folder_path = Path(f'{self.ck3_path}/game/localization/{local_lang}')
        if not folder_path.is_dir():
            print('Localization folder not found')
            return None

        loc_path = [
            folder_path / f'names/character_names_l_{local_lang}.yml',
            folder_path / f'dynasties/dynasty_names_l_{local_lang}.yml',
            folder_path / f'culture/cultures_l_{local_lang}.yml',
            folder_path / f'titles_l_{local_lang}.yml',
            * (folder_path / 'religion').iterdir()
        ]

        if all(file.is_file() for file in loc_path):
            self.loc_path = loc_path
        else:
            raise Exception("Some localization files not found, Please double check your game directory")



    def process_yaml(self):

        """Corrects a YAML file in the resource folder so that they can be loaded in as a Dict. These files will be
        combined with a traits file that comes with the program. Haven't come up a way to have the traits file
        automated by user due to inconsistency in naming patterns and localization text traits scattered uses.
        Used the commented snippet in this function to do the first step of traits yaml processing
        that continues in a separate traits function"""

        for yaml_path in self.loc_path:
            try:
                text = [line.strip() for line in yaml_path.read_text(encoding='utf-8-sig').splitlines()]
                cleaned_lines = []
                for line in text:
                    if '"' in line and line[1] != '#':
                        key, value = line.split('"', 1)
                        if key.isupper():
                            continue
                        value = value.split('"')[0] + '"'
                        value = value.replace('#', '|').replace(':', '-').rstrip() + '\n'
                        cleaned_lines.append(f"{key.split(':', 1)[0]}: \"{value}")

     #         if 'traits_l' in str(yaml_path):
     #               cleaned_lines = [line.replace('trait_', '') for line in cleaned_lines if "_desc:" not in line
     #                              and "_character_desc" not in line and 'trait_' in line]
     #               self.processed_traits.extend(cleaned_lines)

                if cleaned_lines:
                    corrected_yaml = ''.join(cleaned_lines)
                    self.processed_yml.append(corrected_yaml)
                    print(f'Processed path {yaml_path}')
                else:
                    print(f'Path {yaml_path} not processed.')

            except FileNotFoundError:
                print(f"File not found: {yaml_path}")

    def loading_traits(self):

        """Create Trait yml file located in Resource folder processed from commented snippet in process_yaml.
        It matches the order that the trait definition appears in 00_trait.txt with the localized text.
        Not for user."""

        try:
            with open('./resources/00_traits.txt', 'r', encoding='utf-8-sig') as f:
                lines = [line.split(' ', 1)[0] for line in f.readlines()[1:] if line[0].islower()]

            combined = []
            for line in lines:
                for num, text in enumerate(self.processed_traits):
                    if line == text.split(':')[0]:
                        combined.append(f'{(line)}:{text.split(":")[1]}')
                        break
                    elif self.processed_traits[num] == self.processed_traits[-1]:
                        combined.append(f'{(line)}: "NO REFERENCE"\n')

            combined[-1] = combined[-1].strip('\n')

            with open('./resources/traits_trial.txt', 'w', encoding='utf-8-sig') as f:
                f.writelines(combined)

        except FileNotFoundError as e:
            print(f"File not found: {e}")

    def loading_main(self, json_file: str) -> tuple[dict, dict]:

        """Main function loading in localization and data file. It also combines that traits file with the combined
         YAML."""

        processed_yml_file = Path(f'{self.resource_path}/loc_data.yml')
        traits_yml_file = Path(f'{self.resource_path}/traits.txt')
        json_file = Path(json_file)

        if processed_yml_file.is_file():
            print('Processed YAML Found')
            with processed_yml_file.open(encoding='utf-8-sig') as r:
                yaml_data = json.load(r)
            print('Processed YAML Loaded')
            with json_file.open(encoding='utf-8-sig') as r:
                data = json.load(r)
                print('JSON Loaded')
        else:
            self.get_loc_path()
            self.process_yaml()

            with traits_yml_file.open(encoding='utf-8-sig') as r:
                trait_data = r.read()
                self.processed_yml.append(trait_data)

            self.processed_yml = ''.join(self.processed_yml)
            yaml_data = load(self.processed_yml, Loader=CSafeLoader)

            with processed_yml_file.open('w', encoding='utf-8-sig') as w:
                json.dump(yaml_data, w)

            with json_file.open(encoding='utf-8-sig') as r:
                data = json.load(r)

        return data, yaml_data
