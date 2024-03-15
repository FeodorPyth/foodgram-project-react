# Веб-приложение «Фудграм»
Информация для ревью, после удалю.
Адрес: https://foodgramspb.ddns.net/
Логин: admin@example.ru
Пароль: QWErty12345

## Описание проекта:
Foodgram — социальная сеть для публикации рецептов. В этом сервисе можно подписаться на других пользователей, добавлять понравившиеся блюда в избранное, а также выгружать список покупок.
Это полностью рабочий проект, который состоит из бэкенд-приложения на Django и фронтенд-приложения на React.

## СТЕК технологий:
* Python == 3.11.6
* Django == 3.2.16
* Django Rest Framework == 3.12.4
* Gunicorn == 20.1.0
* Nginx
* Docker
* PostgreSQL

## Особенности проекта:
- [x] Получено доменное имя через онлайн-сервис No-IP
- [x] На удаленный сервер был установлен Git, Docker
- [x] Был связан аккаунт на GitHub и на DockerHub с удаленным сервером
- [x] Были созданы образы для бэкенд, фронтенд приложений
- [x] Настроена совместная работа контейнеров бэкэнда и базы данных
- [x] Настроен веб-сервер Nginx для перенаправления запросов и работы со статикой проекта
- [x] Подключено шифрование запросов по протоколу HTTPS
- [x] Автоматизировано тестирование и деплой проекта Foodgram с помощью GitHub Actions

## Как установить проект локально:
Клонировать репозиторий и перейти в него в командной строке:

```sh
git clone git@github.com:FeodorPyth/foodgram-project-react.git
```

```sh
cd foodgram-project-react
```

Cоздать файл .env для хранения переменных окружения.
Перечень необходимых данных указан в файле .env.example:

```sh
touch .env
nano .env
```

## Создание Docker-образов:
Собрать Docker-образы:

```sh
cd frontend
docker build -t username/foodgram_frontend .
cd ../backend
docker build -t username/foodgram_backend .
cd ../gateway
docker build -t username/foodgram_gateway .
```

Отправить собранные образы на DockerHub:

```sh
docker push <имя_пользователя_на_DockerHub>/foodgram_frontend
docker push <имя_пользователя_на_DockerHub>/foodgram_backend
docker push <имя_пользователя_на_DockerHub>/foodgram_gateway
```

# Деплой проекта на удаленный сервер
## Подключение GitHub и DockerHub к удаленному серверу:
Проверка наличия установленного Git на удаленном сервере:

```sh
sudo apt update
git --version
```

Установить Git в ОС на удаленный сервер (при необходимости):

```sh
sudo apt install git
```

Установить Docker Compose в ОС на удаленный сервер (при необходимости):

```sh
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin
```

Сгенирировать пару SSH-ключей:

```sh
ssh-keygen
```

Сохранить открытый SSH-ключ в настройках GitHub:

```sh
cat .ssh/id_rsa.pub
```

Склонировать проект на удаленный сервер:

```sh
git clone git@github.com:FeodorPyth/foodgram-project-react.git
```

## Настройка проекта:
Запустить Docker Compose в режиме демона:

```sh
sudo docker compose up -d
```

Проверить, что все нужные контейнеры запущены:

```sh
sudo docker compose ps
```

Выполнить миграции, собрать статические файлы бэкенда и скопировать их в /backend_static/static/:

```sh
sudo docker compose exec backend python manage.py migrate
sudo docker compose exec backend python manage.py collectstatic
sudo docker compose exec backend cp -r /app/static/. /backend_static/static
sudo docker compose exec backend python manage.py load_csv
```

## Настройка Nginx на удаленном сервере:
Открыть конфиг Nginx:

```sh
sudo nano /etc/nginx/sites-enabled/default
```

Заполнить блок location:

```sh
location / {
        proxy_pass http://127.0.0.1:9090;
    }
```

Проверить конфигурацию и перезагрузить её командой:

```sh
sudo nginx -t
sudo systemctl reload nginx
```

# Автоматизация деплоя: CI/CD:
## Workflow для CI и CD:
Файл написанного workflow находится в директории:

```sh
foodgram-project-react/.github/workflows/main.yml
```

Установить значения переменных в GitHub Actions:

```sh
DOCKER_USERNAME                # имя пользователя в DockerHub
DOCKER_PASSWORD                # пароль пользователя в DockerHub
HOST                           # ip-адрес удаленного сервера
USER                           # имя пользователя на удаленном сервере
SSH_KEY                        # приватный ssh-ключ
SSH_PASSPHRASE                 # пароль для ssh-ключа
TELEGRAM_TO                    # id телеграм-аккаунта (можно узнать у @userinfobot)
TELEGRAM_TOKEN                 # токен бота (можно узнать у @BotFather)
```

## Автор:
[FeodorPyth](https://github.com/FeodorPyth)
