IP адрес: 84.201.154.246
доменное имя: foodfram.zapto.org
email: super@yaya.ru
пароль: zoo36pq3

# ФУДГРАМ

Проектом «Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Для запуска api проекта необходимо:
- Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/corbuncul/foodgram.git
cd foodgram
```
- Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
source env/bin/activate
```
- Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
- Выполнить миграции:
```
python3 manage.py migrate
```
- Запустить проект:
```
python3 manage.py runserver
```

## Для запуска проекта вместе фронтендом необходимо:
- создать файл .env и внести в него следующие настройки:
```
POSTGRES_DB=<имя базы данных>
POSTGRES_USER=<пользователь базы данных>
POSTGRES_PASSWORD=<пароль пользователя базы данных>
DB_NAME=<имя базы данных>
DB_HOST=<имя контейнера с базой данных>
DB_PORT=<порт, на котором работает база данных>
SECRET_KEY=<секретный ключ джанго-проекта>
SERVER_IP=<IP-адрес сайта>
SERVER_DOMAIN=<Доменное имя сайта>
ALLOWED_HOSTS=127.0.0.1,localhost,<IP-адрес сайта>,<Доменное имя сайта>
DEBUG=<Режим отладки: True или False>
```
- запустить docker-compose:
командой:
```
docker compose up -d
```
- произвести миграции:
```
docker compose exec backend python manage.py migrate
```
- внести данные об ингредиентах в базу:
```
docker compose exec backend python manage.py importcsv .
```
- создать суперпользователя:
```
docker compose exec backend python manage.py createsuperuser
```
- внести данные об тегах через админ-панель по адресу
http://localhost:8000/admin/
