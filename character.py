
from house_cleaning import safe_get, safe_get_multiple,combine_values
from pathlib import Path
import csv


class Character():

    # List of characters
    non_dyn_children = set()
    non_dyn_spouse = set()
    all_id_num = set()

    # Dicts to organize individual into families
    child_to_parents = {}
    families = {}
    family_counter = 1

    # Processed data prepared to write to csv file
    marriage_to_csv =[]
    families_to_csv = []
    person_to_csv = []

    skill_names = ('DIP', 'STE', 'MAR', 'INT', 'LEA', 'PRO')

    def __init__(self,id_num: str, person: dict, data: dict, dyn_flag =True, non_dyn_spouse =False):

        """Putting all person and family data into Character object. Custom functions safe_get,safe_get_multiple,
        combine_values, used to parse through variable formats that some information comes through"""

        # Personal Information
        self.id_num = id_num
        if non_dyn_spouse is False: Character.all_id_num.add(self.id_num)
        self.first_name = person.get('first_name')
        self.dynasty_house = person.get ('dynasty_house')
        self.birth = person.get('birth')
        self.death_data = safe_get(person, 'dead_data', 'date')
        self.death_reason = safe_get(person, 'dead_data', 'reason')

        self.skill = [f"{s} {v}" for s, v in zip(Character.skill_names, person.get('skill'))]
        self.traits = person.get('traits')
        self.recessive_traits = person.get('recessive_traits')

        #These are optional in person info and defaults to the house head's info if empty
        self.faith = person.get('faith')
        self.culture = person.get('culture')
        if self.faith is None:
            house_head = safe_get(data['dynasties'][str(self.dynasty_house)])['head_of_house']
            self.faith= data['characters'][str(house_head)]['faith']
        if self.culture is None:
            house_head = safe_get(data['dynasties'][str(self.dynasty_house)])['head_of_house']
            self.culture = data['characters'][str(house_head)]['culture']

        self.sex = 'Female' if person.get('female') else 'Male'
        self.orientation = person.get('sexuality', 'he')
        self.titles = safe_get(person, 'landed_data', 'domain') or safe_get(person, 'dead_data', 'domain')

        # Family Information only for dynasty members

        self.children = safe_get(person, 'family_data', 'child')

        # Loop to link children to parent pair using a parent to iterate from
        if self.children is not None and dyn_flag is True:
            for child in self.children:
                if str(child) not in Character.child_to_parents:
                    Character.child_to_parents[str(child)] = {"husband": None, "wife": None}
                if self.sex == 'Female':
                    Character.child_to_parents[str(child)]['wife'] = self.id_num
                elif self.sex == 'Male':
                    Character.child_to_parents[str(child)]['husband'] = self.id_num

        elif non_dyn_spouse is True and self.children is not None:
            for child in self.children:
                if str(child) in Character.all_id_num:

                    if self.sex == 'Female':
                        Character.child_to_parents[str(child)]['wife'] = self.id_num

                    elif self.sex == 'Male':
                        Character.child_to_parents[str(child)]['husband'] = self.id_num

        spouse_keys = ['spouse', 'former_spouses', 'concubinist', 'former_concubinists']
        self.spouse = set(combine_values(*safe_get_multiple(person, 'family_data', *spouse_keys)))


        if non_dyn_spouse is True and self.spouse is not None:
            self.spouse_no_kids()

        # Joining non_dynasty members to later loop
        if dyn_flag is True:
            Character.non_dyn_spouse.update(self.spouse or [])
           # if self.unwed is not None: Character.non_dyn_spouse.add(self.unwed)
            Character.non_dyn_children.update(self.children or [])


    @classmethod
    def add_non_dynasty(cls, data: dict) -> list:
        cls.non_dyn_children = {str(member) for member in cls.non_dyn_children} - cls.all_id_num
        cls.non_dyn_spouse = {str(member) for member in cls.non_dyn_spouse} - cls.all_id_num
        cls.non_dyn_children = cls.non_dyn_children - cls.non_dyn_spouse

        non_members = []
        for non_member in cls.non_dyn_children:
            character = Character(non_member, data['characters'][non_member], data,dyn_flag=False)
            non_members.append(character)
        for non_member in cls.non_dyn_spouse:
            character = Character(non_member, data['characters'][non_member], data,dyn_flag=False, non_dyn_spouse= True)
            non_members.append(character)


        return non_members
    def spouse_no_kids(self):

        for spouse in self.spouse:

            if str(spouse) in Character.all_id_num:

                if (self.sex == 'Female' and {"husband": str(spouse), "wife": self.id_num}
                        not in Character.child_to_parents.values() and [str(spouse), self.id_num]
                        not in Character.marriage_to_csv):
                    Character.marriage_to_csv.append([str(spouse), self.id_num])

                elif (self.sex == 'Male' and {"husband": self.id_num, "wife": str(spouse)}
                      not in Character.child_to_parents.values() and [self.id_num, str(spouse)]
                        not in Character.marriage_to_csv):
                    Character.marriage_to_csv.append([self.id_num, str(spouse)])

    @classmethod
    def add_marriage_id(cls):
        for marriage in cls.marriage_to_csv:
            marriage.insert(0,f'm{cls.family_counter}')
            cls.family_counter += 1
        return

    @classmethod
    def add_parents_note(cls):

        # Match spouse pairs with children. Prepping the marriage and family rows for csv
        for child, parents in cls.child_to_parents.items():
            parent_pair = f'{parents['husband']} {parents['wife']}'

            if parent_pair not in cls.families:
                marriage_id = f"m{cls.family_counter}"
                cls.families[parent_pair] = {
                    "marriage": marriage_id,
                    "husband": parents['husband'],
                    "wife": parents['wife'],
                    "child": []
                }
                cls.family_counter += 1
            cls.families[parent_pair]["child"].append(child)

        for parents, family_info in cls.families.items():
            cls.marriage_to_csv.append([family_info['marriage'],family_info['husband'],family_info['wife']])
            for child in family_info['child']:
                cls.families_to_csv.append([family_info['marriage'], child])

    def local_first(self, loc_data: dict):
        self.first_name = loc_data.get(self.first_name, self.first_name)

    def local_dynasty(self, data: dict, loc_data: dict):
        if self.dynasty_house:
            original_name = data['dynasties'][str(self.dynasty_house)]
            if loc_name := loc_data.get(original_name.get('name')):
                self.dynasty_house = loc_name
            elif key_name := original_name.get('key'):
                if 'house' in key_name:
                    self.dynasty_house = (key_name.split('_')[1]).title()
                else:
                    self.dynasty_house = (key_name.replace('_', ' ')).title()
            elif loc_name := original_name.get('localized_name'):
                self.dynasty_house = loc_name

    def local_title(self, data: dict, loc_data: dict):
        if self.titles:
            original_name = data['landed_titles'][str(self.titles[0])]['key']
            title_name = self.title_rank(original_name)
            if original_name in loc_data:
                self.titles = f'{title_name} of {loc_data[original_name]}'
            else:
                self.titles = f'{title_name} of {data['landed_titles'][str(self.titles[0])]['name']}'

    @staticmethod
    def title_rank( title: str):

        # Helper function for local titles to convert letters to title.
        rankings = {'b': 'Baron', 'c': 'Count', 'd': 'Duke',
                    'k': 'King', 'e': 'Emperor', 'x': 'Leader'}
        return rankings[title.split('_', 1)[0]]

    def local_traits(self, trait_data: dict):
        if self.traits:
            self.traits = [
                trait_data[str(trait)]
                for trait in self.traits
                if str(trait) in trait_data
            ]

        if self.recessive_traits:
            self.recessive_traits = [
                trait_data[str(trait)]
                for trait in self.recessive_traits
                if str(trait) in trait_data
            ]

    def local_faith(self, data: dict, loc_data: dict):
        if self.faith:
            og_faith = (data['religion'][str(self.faith)].get('name') or
                        data['religion'][str(self.faith)].get('template'))
            if og_faith in loc_data:
                self.faith = loc_data[og_faith]
            else:
                self.faith = og_faith

    def local_culture(self, data:dict , loc_data:dict):
        if self.culture:
            og_culture = data['culture'][str(self.culture)]['name']
            if og_culture in loc_data:
                self.culture = loc_data[og_culture]
            else:
                self.culture = og_culture

    def post_process(self):

        # Processing person data for csv. Creating a note section that you can view in Gramps
        self.traits = ', '.join(self.traits) if self.traits else None
        self.recessive_traits = ', '.join(self.recessive_traits) if self.recessive_traits else None
        self.birth = self.birth.replace('.', '-')
        self.death_data = self.death_data.replace('.', '-') if self.death_data else None
        self.skill = ', '.join(self.skill)
        self.note = (f'ID: {self.id_num}\nName: {self.first_name}\nHouse: {self.dynasty_house}\n'
                     f'Titles: {self.titles}\nBirth: {self.birth}\nDeath: {self.death_data}\nCause of Death: {self.death_reason}\n'
                     f'Skills: {self.skill}\nTraits: {self.traits}\nRecessive Traits: {self.recessive_traits}\n'
                     f'Faith: {self.faith}\nCulture: {self.culture}\nSex: {self.sex}\nOrientation: {self.orientation}\n'
                     )

    def local_all(self, data, loc_data):

        # Running each localization steps, followed by preparing the person rows for csv.
        self.local_first(loc_data)
        self.local_dynasty(data, loc_data)
        self.local_title(data, loc_data)
        self.local_traits(loc_data)
        self.local_faith(data, loc_data)
        self.local_culture(data, loc_data)
        self.post_process()

        Character.person_to_csv.append( [
            self.id_num,
            self.dynasty_house,
            self.first_name,
            self.sex,
            self.birth,
            self.death_data,
            self.titles,
            self.note
        ])

    @classmethod
    def to_csv(cls, csv_path: str):

        person_header = ['person', 'surname', 'given', 'gender', 'birth date', 'death date', 'title', 'note']
        marriage_header = ['marriage', 'husband', 'wife']
        family_header = ['family', 'child']

        csv_path = Path(csv_path)
        with csv_path.open('w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(person_header)

            for person in cls.person_to_csv:
                writer.writerow(person)

            writer.writerow([''] * 8)

            writer.writerow(marriage_header)
            for marriage in cls.marriage_to_csv:
                writer.writerow(marriage)

            writer.writerow([''] * 8)

            writer.writerow(family_header)
            for family in cls.families_to_csv:
                writer.writerow(family)
    @classmethod
    def reset_data(cls):
        cls.non_dyn_children.clear()
        cls.non_dyn_spouse.clear()
        cls.all_id_num.clear()
        cls.child_to_parents.clear()
        cls.families.clear()
        cls.family_counter = 1
        cls.person_to_csv.clear()
        cls.marriage_to_csv.clear()
        cls.families_to_csv.clear()

# _______________________________________OTHER FUNCTIONS__________________________________________________________#

def find_related_houses(id_num: str, data: dict) -> list:

    # finds cadet houses and adds them to the house list
    main_house = data['characters'][id_num]['dynasty_house']
    all_house=[main_house] + [int(key) for key, values in data['dynasties'].items()
                    if safe_get(values,'parent_dynasty_house',default=[]) == main_house]

    return all_house


def char_main(data: dict, yaml_data: dict, main_id: str, csv_path: str):

    Character.reset_data()

    house_list = find_related_houses(main_id, data)
    history = []

    # Loop through characters in JSON and put them in a list of Character objects/instances
    for id_num, info in data['characters'].items():
        dynasty_house = safe_get(info, "dynasty_house", default='None')
        if dynasty_house in house_list:
            character = Character(id_num, info, data)
            history.append(character)
    # add dyn spouses with no kids marriage for csv.
    for hist in history:
        hist.spouse_no_kids()

    non_member = Character.add_non_dynasty(data)
    history.extend(non_member)
    Character.add_marriage_id()


    Character.add_parents_note()
    # Performs all localization and provides a count
    for count,hist in enumerate(history):
        hist.local_all(data, yaml_data)
        print(f'{count+1}/{len(history)} Characters Processed')

    Character.to_csv(csv_path)