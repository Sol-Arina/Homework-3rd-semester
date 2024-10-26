#Задача 1 (10 баллов). 

#Напишите программу, которая будет автоматически 
#обрабатывать сырой корпус текстов. Что это должно быть:
#у нас есть некоторое количество текстовых файлов, 
#которые лежат рассортированными по папкам. 
#Вложенных подпапок может быть много. 
#мы хотим вытащить тексты из всех этих файлов, разобрать их (можно использовать парсер spacy или stanza) и позаписать в новой директории одноименные conllu. 
#Пользователь при старте программы указывает путь к главной директории исходных файлов и желаемое название папки с аутпутом. Мы должны: а) проверить, что директория с исходниками существует б) что пользователь не ввел название, в котором есть и подобные символы, которые запрещены системой в названиях файлов. 
#метод, который будет заниматься открыванием файлов и считыванием текста из них, должен не вываливать ошибку в случае, если у нас файл не в той кодировке, а только делать предупреждение и пропускать файл. 
#при этом должны вестись логи с именами пропущенных файлов. Логи записываем в errors.txt.
#естественно, все должно быть в классах. Примерная структура может быть такой:
#На дополнительный балл: изучите библиотеку argparse и используйте ее в своей программе таким образом, чтобы ее можно было вызывать с параметрами из консоли. То есть, в консоли пишете что-то типа: 
#    python mycorpusreader.py C:mycorpusraw output'''

import os
import re
import argparse
import spacy
from conllu import TokenList




class IsThisPathOk:
    '''проверка пути - дескриптор'''
    def __init__(self, inputpath=True):
        self.inputpath = inputpath
        self.path = None

    def __get__(self, instance, owner):
        return self.path
    
    def __set__(self, instance, value):
        wrongsymbols = re.compile(r'[<>:"/\\|?*]')
        if wrongsymbols.search(os.path.basename(value)):
            raise ValueError(f'введённый путь\'{os.path.basename(value)}\' содержит недопустимые символы!!')
        
        if self.inputpath:
            if not os.path.exists(value) or not os.path.isdir(value):
                raise FileNotFoundError(f'директория \'{value}\' не существует')
        
        if not self.inputpath:
            os.makedirs(value, exist_ok=True) # если такой директории нет, сделаем её

        self.path = value


class CorpusCreator:
    '''corpus creator'''
    fromdirectory = IsThisPathOk()
    todirectory = IsThisPathOk()
    def __init__(self, fromdirectory, todirectory):
        self.nlp = spacy.load('ru_core_news_md')
        self.fromdirectory = fromdirectory
        self.todirectory = todirectory
        self.log = os.path.join(self.todirectory, 'error_log.txt')
        
    def openfile(self, pathtofile):
        'открываем файл и логируем ошибки кодировки в error_log.txt'
        try:
            with open(pathtofile, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(self.log, 'a', encoding='utf-8') as log:
                log.write(f'Не удалось открыть файл {pathtofile}: с кодировкой что-то не так..\n')
            return None
        
    def parse(self, text):
        '''разбираем текст'''
        doc = self.nlp(text)
        sentences = []
        for sent in doc.sents:
            tokens = []
            for token in sent:
                tokens.append({
                    'id': token.i + 1,
                    'form': token.text,
                    'lemma': token.lemma_,
                    'upostag': token.pos_,
                    'xpostag': '_',
                    'feats': token.morph.to_dict(),
                    'head': token.head.i + 1 if token.head != token else 0,
                    'deprel': token.dep_,
                    'deps': '_',
                    'misc': '_'})
            sentences.append(TokenList(tokens))  
        return sentences
        
    def writefile(self, sentences, todirectory):
        '''запись в файл'''
        with open(todirectory, 'w', encoding='utf-8') as f:
            for sentence in sentences:
                f.write(sentence.serialize()) 
                f.write('\n') 
    
    def process(self):
        '''метод, который запускает все действие'''
        for dirpath, _, filenames in os.walk(self.fromdirectory): # главная директория, папки, файлы
            for filename in filenames:
                if filename.endswith('.txt'):
                    filepath = os.path.join(dirpath, filename)
                    text = self.openfile(filepath)
                    if text:
                        sentences = self.parse(text)
                        relativepath = os.path.relpath(filepath, self.fromdirectory) # не конечный путь
                        outpath = os.path.join(self.todirectory, os.path.splitext(relativepath)[0] + '.conllu')
                        os.makedirs(os.path.dirname(outpath), exist_ok=True)
                        
                        self.writefile(sentences, outpath)
                        print(f'обработанный файл {filepath} находится в {outpath}')


class Program:
    '''главная программа'''
    def __init__(self):
        self.args = None

    def parseargs(self):
        '''парсим аргументы'''
        parser = argparse.ArgumentParser(description='обработка сырого корпуса')
        parser.add_argument('fromdirectory', type=str, help='путь к директории с исходными файлами')
        parser.add_argument('todirectory', type=str, help='путь для места, где сохранить обработанные файлы')
        self.args = parser.parse_args()

    def run(self):
        '''обработка корпуса'''
        self.parseargs()
        cc = CorpusCreator(self.args.fromdirectory, self.args.todirectory)
        cc.process()


if __name__ == '__main__':
    program = Program()
    program.run()        