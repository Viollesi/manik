# Manik Bot

Telegram-бот для записи клиентов на маникюр. Проект будет включать клиентский
интерфейс записи, админку мастера, управление услугами, расписанием и
напоминаниями.

## Текущий статус

Сейчас добавлен только базовый каркас Python-проекта. Бизнес-логика,
Telegram handlers, SQLAlchemy-модели, миграции и Docker Compose будут добавлены
отдельными этапами.

## Локальная разработка

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy
```

## Конфигурация

Скопируйте `.env.example` в `.env` и заполните значения перед запуском будущего
бота.

```bash
cp .env.example .env
```

## Запуск через Docker Compose

Соберите и запустите инфраструктуру:

```bash
docker compose up --build
```

Команда поднимает контейнер приложения, PostgreSQL и Redis. На текущем этапе
приложение запускает только placeholder-entrypoint и завершает работу без
подключения к Telegram, базе данных или Redis.

Остановить контейнеры можно так:

```bash
docker compose down
```

Если нужно удалить сохраненные данные PostgreSQL и Redis:

```bash
docker compose down -v
```
