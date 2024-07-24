from petrovich.main import Petrovich
from petrovich.enums import Case, Gender
import pymorphy2
import sys

'''from natasha import (
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    Segmenter,
    Doc,
)

# Загрузка модели Natasha
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
morph_vocab = MorphVocab()
segmenter = Segmenter() 

def get_gender(text):
    # Создание объекта Doc и анализ текста
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)

    # Получение информации о роде слова
    for token in doc.tokens:
        print(token.feats['Gender'])'''
        



p = Petrovich()

# Находим все склонения ФИО словарём: {'imen', 'rod', 'dat', 'vin', 'tvor', 'pred'}
def FIO_cases(fio:str, passport: str) -> dict:

    # Вернуть Gender для petrovich исходя из паспортных данных
    def get_passport_gender(passport: str):
        idx = passport.split().index('пол') + 1
        if not idx:
            print('Ошибка определения пола - в паспортных данных отсутсвует пол')
            sys.exit()
        gender = passport.split()[idx]
        if 'муж' in gender:
            return Gender.MALE
        elif 'жен' in gender:
            return Gender.FEMALE
        else:
            print(f'Ошибка определения пола - {gender}')
            sys.exit()

    # склонение при известном роде 
    def FIO_case(fio:str, params=[Case.DATIVE, Gender.MALE])->str:
        lastname, name, patronymic = fio.split()
        return f'{p.lastname(lastname, *params)} {p.firstname(name, *params)} {p.middlename(patronymic, *params)}' 

    gender = get_passport_gender(passport)

    # 'GENITIVE': 0, 'DATIVE': 1, 'ACCUSATIVE': 2, 'INSTRUMENTAL': 3, 'PREPOSITIONAL': 4
    case_codes = ['rod', 'dat', 'vin', 'tvor', 'pred']
    cases = {'imen': fio}

    for case, code in enumerate(case_codes):
        cases[code] = FIO_case(fio, [case, gender])

    # print(*cases.values(), sep='\n')
    return cases


morph = pymorphy2.MorphAnalyzer()
# Просклонять текст в заданном падеже.  gramems - граммемы(род/число/падеж/...) - см доку 
def text_case(text:str, gramems={'datv'}): 
    ans = []
    for word in text.split():
        variant = morph.parse(word)[0]
        if variant.inflect(gramems) is None:  # Предлоги, союзы и пр. - без изменений
            ans.append(word)
        else:
            ans.append(variant.inflect(gramems)[0])

    return ' '.join(ans).strip()

# Просклонять название орг-ии во все возможные падежи
def developer_cases(developer_name:str):    
    # Возвращаем индекс - начало несклоняемой части (иногда часть текста не склоняется) 
    def fix_collisions(developer_name):
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


if __name__ == '__main__':
    member_name ='Кочнова Виталина Сергеевна'
    passport = '17.12.2075 года рождения, место рождения ПОС. НОВОСЛОБОДСК ДУМИНИЧСКОГО Р-НА КАЛУЖСКОЙ ОБЛ., гражданство РФ, пол женский, паспорт 7716 888888, выдан ОТДЕЛЕНИЕМ УФМС РОССИИ ПО Какой-то ОБЛАСТИ В Г. ЛЮДИНОВО, дата выдачи 28.07.2076 г., код подразделения 1337-037'

    cases = FIO_cases(member_name, passport)
    print(*cases.values(), sep='\n')

    developer_name = "Общество с ограниченной ответственностью ''Лотан''"#"ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО ''ПИК-СПЕЦИАЛИЗИРОВАННЫЙ ЗАСТРОЙЩИК''"
    cases = developer_cases(developer_name)
    print(*cases.values(), sep='\n')
