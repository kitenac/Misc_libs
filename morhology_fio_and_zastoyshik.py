"""Module providing a function declension of member name and developer name"""
import logging
from petrovich.main import Petrovich
from petrovich.enums import Case, Gender
import pymorphy2
from collections import defaultdict


ANSWER_SEP = ';'  # ANSWER_SEP = ';' 


morph = pymorphy2.MorphAnalyzer() # morph analizer - costly instance - call it once if possible 

class ProbableGender:
    '''
    pymorhpy2 based gender detection (not 100% accurate, but close) and converting to other formats: petrovich, string
       ex: 
           gender = ProbableGender.get_str('Корова')
    '''
    gender: str # pymorhy2 gender: masc, femn, neut, None

    # get gender by pymorhy2 - sometimes gives bugs - so use only in case there`s no other option to get gender
    def __init__(self, word: str):
        # TODO: to increase accuracy - crawl through other given variants - morph.parse(word)[i]
        self.gender = morph.parse(word)[0].tag.gender 
    
    def as_str(self):
        '''
        same as  __str__, but named uniformly
        '''
        aliases = {'masc': 'муж', 'femn': 'жен', 'neut': 'муж',  'None': 'муж'}
        return aliases[self.gender.__str__()]
    
    def as_petrovich(self):
        '''
        gender - compatible to petrovich
        '''
        aliases = {'masc': Gender.MALE, 'femn': Gender.FEMALE, 'neut': Gender.MALE,  'None': Gender.MALE}
        return aliases[self.gender.__str__()]
    
    # Usable Methods
    @staticmethod
    def get_str(word:str):
        gender = ProbableGender(word)
        return gender.as_str()
    
    @staticmethod
    def get_petrovich(word:str):
        gender = ProbableGender(word)
        return gender.as_petrovich()
                


p = Petrovich()
def fio_cases(fio:str, passport: str) -> dict:
    """Находим все склонения ФИО словарём: {'imen', 'rod', 'dat', 'vin', 'tvor', 'pred'}"""
    # Вернуть Gender для petrovich исходя из паспортных данных
    def get_passport_gender(passport: str):
        try:
            idx = passport.split().index('пол') + 1
        except ValueError:
            print(' - Проблема определения пола - в паспортных данных отсутсвует пол, определяем его с помощью pymorphy2 по имени - может ошибиться с небольшой вероятностью')
            try:
                first_name = fio.split()[1]
                logging.warning('function FIO_cases:\n'
                          'GENDER DETERMINATION WARNING: GENDER IS NOT FOUND IN PASSPORT DATA'
                          r'- Now using pymorphy2 to detect gender by first_name (not 100% accurate, but close) ')
                return ProbableGender.get_petrovich(first_name)
            except IndexError:
                logging.error(f'function FIO_cases:\n can`t find first name due fio={fio}, accuracy of gender dection  drasticaly decreases :(')
                return Gender.MALE 

        gender = passport.split()[idx]
        if 'муж' in gender:
            return Gender.MALE
        if 'жен' in gender:
            return Gender.FEMALE
        logging.error('function FIO_cases:\n'
                      'GENDER DETERMINATION ERROR\n'
                      'gender: %s', gender)
        return None

    # helper - pymorhy2 for cases when petrovich is bad
    def morph_case(word:str, case: Case):
        # petrovich: 'GENITIVE': 0, 'DATIVE': 1, 'ACCUSATIVE': 2, 'INSTRUMENTAL': 3, 'PREPOSITIONAL': 4
        cases_map = ['gent', 'datv', 'accs', 'ablt', 'loct']
        return morph.parse(word)[0].inflect({cases_map[case]}).word.capitalize()


    def fio_case(fio:str, params=[Case.DATIVE, Gender.MALE])->str:
        """Cклонение при известном роде
        
        Комбинируем две библиотеки для склонений:
          petrovich - лажает с именами иногда 
           - например с "Ольга" - склоняет, как "Ольгы", 
          а pymorhy2 - с фамилиями 
            - "Кочнов", как "Кочна" склоняет

          поэтому для имени - pymorphy2, для осталього - petrovich
        """
        lastname, name, patronymic = fio.split()
        cased_name = morph_case(name, params[0]) 
        return f'{p.lastname(lastname, *params)} {cased_name} {p.middlename(patronymic, *params)}'

    # validate fio
    def is_fio():
        return len(fio.split()) == 3

    gender = get_passport_gender(passport)

    # 'GENITIVE': 0, 'DATIVE': 1, 'ACCUSATIVE': 2, 'INSTRUMENTAL': 3, 'PREPOSITIONAL': 4
    case_codes = ['rod', 'dat', 'vin', 'tvor', 'pred']
    cases = {'imen': fio}

    # casing
    if is_fio():
        for case, code in enumerate(case_codes):
            cases[code] = fio_case(fio, [case, gender])
    
    # save gicen form if it`s not fio
    else:
        for case, code in enumerate(case_codes):
            cases[code] = fio           


    # print(*cases.values(), sep='\n')
    return cases



def text_case(text:str, gramems={'datv'}):
    """Просклонять текст в дательном падеже.  gramems - граммемы(род/число/падеж/...) - см доку"""
    ans = []
    for word in text.split():
        variant = morph.parse(word)[0]
        if variant.inflect(gramems) is None:  # Предлоги, союзы и пр. - без изменений
            ans.append(word)
        else:
            ans.append(variant.inflect(gramems)[0])

    return ' '.join(ans).strip()


def developer_cases(developer_name:str):
    """Просклонять название орг-ии во все возможные формы"""
    def fix_collisions(developer_name):
        """Возвращаем индекс - начало несклоняемой части (иногда часть текста не склоняется)"""
        # src: ОПФ для застройщиков - https://studfile.net/preview/2854680/page:6/
        # например "с": для "Общество с ограниченной ответственностью" - склоняется только "Общество"
        # "на": для "Товарищество на вере" - только Товарищество
        casuses = ('с', 'на')
        developer_name = ' '.join(developer_name.split()) # убираем повторяющиеся пробелы

        for x in casuses:
            # смотрим есть ли поблемный союз/предлог в строке и если есть - его индекс в строке находим
            if x in developer_name.split():
                idx = 0
                for i, part in enumerate(developer_name.split()):
                    if part == x: # дошли уже до проблемного места и индекс посчитан
                        break
                    idx += len(part) + 1 # +1 - т.к. пробел тоже даёт смещение
                return idx

        # Случай, когда в орг.прав.форме нет проблемных союзов/предлогов
        # например: ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО ''ПИК-СПЕЦИАЛИЗИРОВАННЫЙ ЗАСТРОЙЩИК''
        idx = developer_name.find("'")
        if not idx:
            idx = developer_name.find('"')
        return idx

    # org_form - склоняемая часть, name - имя орг-ии - не склоняется
    idx = fix_collisions(developer_name)
    org_form, name = developer_name[:idx].strip(), developer_name[idx:]

    # Падежи
    cases = {'imen': developer_name}
    case_codes  = ('rod',  'dat',  'vin',  'tvor', 'pred') # ключи для падежей
    morph_codes = ('gent', 'datv', 'accs', 'ablt', 'loct') # соот-ие коды падежей, известные анализатору pymorphy2
    # Сконяем по всем  подежам
    for i, case in enumerate(case_codes):
        cases[case] = f'{text_case(org_form, {morph_codes[i]}).capitalize()} {name}'
    return cases

    
    

# fio_cases()`s adapter for bot`s output - can case string with multiple fios:
#  examples of bots output: 'fio', '???', 'fio;fio', '???;fio', 'fio;???'  
def adaptive_fio_cases(member_fios:str='', passports:str='')->dict:
    fios = member_fios.split(ANSWER_SEP)
    passports = passports.split(ANSWER_SEP)

    # force each fio to have it`s own passport even if it wasn`t given
    def equalize(passports):
        if len(fios) == len(passports):
            return passports     
        elif len(fios) < len(passports):
            return passports[:len(fios)]
        elif len(fios) > len(passports):
            return passports + [f'пол {ProbableGender.get_str(fios[i])}' for i in range( len(passports), len(fios))]

    passports = equalize(passports)
    #print(f'passports: + {passports} {len(passports)} {len(fios)}')

    cases_groups = [fio_cases(fio, passports[i]) for i, fio in enumerate(fios)]  # list of all possible cases for each particular fio 
    cases_keys = cases_groups[0].keys() # keys of all cases
    conncat_cases = defaultdict(lambda: []) # result dictionary of concatinated cases forms

    # collect cases 
    for case in cases_keys:
        # itterate over cases_groups
        for cases in cases_groups:
            conncat_cases[case].append(cases[case]) 
    # concatinate `em with sep for answers
    for case in cases_keys:
        conncat_cases[case] = ANSWER_SEP.join(conncat_cases[case])

    return dict(conncat_cases)

if __name__ == '__main__':
    member_name ='Авдеева Ольга Викторовна'
    passport = '17.12.2075 года рождения, место рождения ПОС. НОВОСЛОБОДСК ДУМИНИЧСКОГО Р-НА КАЛУЖСКОЙ ОБЛ., гражданство РФ, пол женский, паспорт 7716 888888, выдан ОТДЕЛЕНИЕМ УФМС РОССИИ ПО Какой-то ОБЛАСТИ В Г. ЛЮДИНОВО, дата выдачи 28.07.2076 г., код подразделения 1337-037'

    cases = fio_cases(member_name, passport)
    #print(*cases.values(), sep='\n')

    # Bug with petrovich:
    # print(p.firstname('Ольга', Case.GENITIVE, Gender.FEMALE))

    developer_name = "Общество с ограниченной ответственностью ''Лотан''"#"ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО ''ПИК-СПЕЦИАЛИЗИРОВАННЫЙ ЗАСТРОЙЩИК''"
    cases = developer_cases(developer_name)
    #print(*cases.values(), sep='\n')

    #print(ProbableGender.get_petrovich('!!!'))
    # check if all strange(with ??? or ) fios cased correctly bu ad
    tricky_names = ['Одинарная Вариация Викторовна', '???;???', '!!!,WTF', 'Двойная Ольга Викторовна;Двойной Виктор Сергеевич', 'Беглов Иннокентий Петрович;???', '???;Чубайз Виктор Иванович']
    
    for member_names in tricky_names:
        cases = adaptive_fio_cases(member_names, passports='')
        print(*cases.values(), sep='\n')
    

    

    