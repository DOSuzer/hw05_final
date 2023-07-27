# PostIT
### Описание проекта:
Сайт социальной сети PostIT для публикации дневников. Реализовано создание постов, их редактирование, прикрепление изображений к постам, комментарии, подписки участников друг на друга. Используется пагинация, кэширование главной страницы. Использована библиотека Unittest для тестирования работы сайта.
### Технологии:
Python, Django, Django ORM, Unittest, SQLite, HTML, Git
### Запуск проекта:
- Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/DOSuzer/postit_final.git
cd postit_final
```
- Создать и активировать виртуальное окружение:
```
python -m venv venv 
source venv/bin/activate (Mac, Linux)
source venv/scripts/activate (Windows)
```
- Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip 
pip install -r requirements.txt
```
- Перейти в рабочую папку и выполнить миграции:
```
cd yatube
python manage.py migrate
```
- Запустить сервер:
```
python manage.py runserver
```
