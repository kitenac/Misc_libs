import pymorphy2

'''
Обновить словарь:
pip install -U pymorphy2-dicts-ru

Дока:
1. Обозначения граммем (род/падеж/число/...):
https://pymorphy2.readthedocs.io/en/stable/user/grammemes.html#grammeme-docs

'''

# !!! Achtung - экземпляр этого класса много ОП ест => не создавать >1 шт без необходимости
morph = pymorphy2.MorphAnalyzer()

''' Вспомогательная функция для оценки работы библиотеки 
    - видим все варианты слова 
    - граммемы i-го слова
    - результат изменения граммем для i-го слова - берём j-ый вариант
'''
def examine_word(word:str, i:int, j:int, gramems={'sing', 'masc','datv'}):
    analized_variants = morph.parse(word)[i] # выбрали вариант слова #i
    print(*morph.parse(word), sep='\n')
    print(f'\nГрамемы {i}-го слова {analized_variants.tag}\n')
    # Пробуем применить граммемы к выбранному слову
    try:
        print(analized_variants.inflect(gramems)[j])
    except:
        print(f'Одна из граммем {gramems} не поддерживается для выбранного варианта слова #{i} - попробуйте выбрать другой варимант слова, например #{i+1}\n\n')

# Просклонять текст в дательном падеже
def text_case(text:str):
    gramems={'datv'} # другие граммемы - см ссылку на доку выше
    ans = []
    for word in text.split():
        variant = morph.parse(word)[0]
        if variant.inflect(gramems) is None:  # Предлоги, союзы и пр. - без изменений
            ans.append(word)
        else:
            ans.append(variant.inflect(gramems)[0])

    print(' '.join(ans))

# Просклонять ФИО в дательном (datv) падеже
def FIO_case(FIO='Златова Эльвира Валериевна'):
    FIO = FIO.split(' ')
    surname, name, patronymic = FIO
    name = morph.parse(name)[0]
    gender = name.tag.gender    # Определяем род по имени

    # Ищем вариант разбора слова, который может быть в нужном роде
    def gender_fits(word: str, gender:str):
        for var in morph.parse(word):
            if gender == var.tag.gender:
                return var
        # если не нашлось - самое похожее возвращаем
        return morph.parse(word)[0] 
        
    # 'Surn sing' - спец тип - под фамилии - он правильнее склоняется
    def get_surname_type(surname:str, gender):
        for var in morph.parse(surname):
            # проверяем, что слово имеет тип фамилии и имеет нужный род
            if 'Surn sing' in var.tag.__str__() and gender in var.tag.__str__():
                return var
            
        # Если не получилось найти по типу-"фамилия" - то просто по роду возвращаем
        return gender_fits(surname, gender)

    gramems={'sing', 'datv'}
    # Подстраиваем фамилию под тип фамилии - "Surn sing", а отчество под род имени
    surname, patronymic = get_surname_type(surname, gender), gender_fits(patronymic, gender) 
    # Склоняем Ф,И,О
    FIO = [word.inflect(gramems)[0] for word in [surname, name, patronymic] ]
    # ФИО - с большой буквы
    FIO = [x.capitalize() for x in FIO] 
    print(' '.join(FIO))


if __name__ == '__main__':
    #examine_word('Асташев', 2, 0,{'sing', 'masc','datv'}) # 2-ой вариант поддерживает все граммемы, поэтому i=2 выставил
    #examine_word('Кочнов', 0, 0,{'sing', 'datv'})
    
    FIOs = [
        'Волчкова Ольга Александровна', 'Волчков Леонид Николаевич',
        'Августинопольский Денис Сергеевич', 'Августинопольская Светлана Анатольевна',
        'Ковалев Иван Юрьевич', 'Ковалева Надежда Александровна'
    ]

    print('Склоняем ФИО:')
    for fio in FIOs:
       FIO_case(fio)

    print('\nСклоняем часть предложения:')
    text = "Общество с ограниченной ответственностью ''Лотан''"
    text_case(text)
    

