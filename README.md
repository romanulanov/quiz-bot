# Викторины

[Бот тг](https://t.me/agihaerbasddcrvbasbot). [Бот вк](https://vk.com/club224989418).
Для начала работы бота вк отправьте ему сообщение.

## Установка 

Установите [python3](https://realpython.com/installing-python/).

## Репозиторий

Клонируйте репозиторий в папку с проектом. 
```bush 
git clone https://github.com/romanulanov/quiz-bot.git
```

## Виртуальное окружение

В терминале перейдите в папку с репозиторием и создайте виртуальное окружение
```bush 
python3 -m venv venv
```

### Активация виртуального окружения 

```bush
source venv/bin/activate
```

### Установка библиотек

Установите библиотеки с помощью файла requirements.txt
```bush 
pip3 install -r requirements.txt
```

#### Запись токена Telegram

Создайте файл .env. Создайте бота с помощью (BotFather)[https://t.me/botfather] и запишите токен телеграм бота в env:
```bush
echo TELEGRAM_BOT_TOKEN=ваш токен > .env
```

#### Запись токена VK

Создайте группу вконтакте и разрешите сообщения в настройках группы. Добавьте токен в env:
```bush
echo VK_TOKEN=ваш токен >> .env
```

### Redis

Зарегистрируйтесь на [Redis](https://redis.com/). Добавьте данные БД в env:

```bush
echo REDIS_HOST=ваш REDIS_HOST >> .env
echo REDIS_PORT=ваш REDIS_PORT >> .env
echo REDIS_PASSWORD=ваш REDIS_PASSWORD >> .env
```

## Запуск

### Запуск ботов
Из директории с проектом выполните команды и передайте в параметры папку с вопросами.

По умолчанию вопросы хронятся в директории questions
```bush
python3 quiz.py ./questions/ 
```

Запуск бота в телеграм:
```bush
python3 tg_bot.py
```

Запуск бота VK:
```bush
python3 vk_bot.py
```

## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
