# ShoeShop — система оформления заказов обуви

Учебный проект: десктопное приложение для просмотра каталога обуви
и оформления заказов.

## Возможности
- просмотр каталога моделей обуви с ценой, скидкой и наличием;
- сортировка, фильтрация и поиск товаров;
- оформление заказа авторизованным пользователем;
- управление заказами (менеджер и администратор).

## Требования
- Python 3.10+
- PostgreSQL 14+
- библиотеки из файла `requirements.txt`

## Установка и запуск
1. Клонировать репозиторий: `git clone https://github.com/veroni4ka2007/ShoeShop.git`
2. Создать окружение и установить зависимости:
   `python -m venv venv`, `venv\Scripts\activate`, `pip install -r requirements.txt`
3. Создать базу данных и загрузить скрипт `database/shoe_store.sql`.
4. Скопировать `config.ini.example` в `config.ini` и указать параметры подключения.
5. Запустить приложение: `python main.py`

## Настройка подключения к базе данных
Параметры подключения читаются из файла `config.ini`. В репозиторий попадает
только образец `config.ini.example`, а локальный `config.ini` исключён через
`.gitignore`, поэтому пароль не хранится в истории Git.

## ER-диаграмма базы данных

Файл `docs/ER-diagram.png` (PDF-версия — `docs/ER-diagram.pdf`).

Основные таблицы:
- `pvz` — пункты выдачи;
- `client` — пользователи приложения (логин, пароль, роль);
- `tovar` — товары;
- `orders` — заказы;
- `order_tovar` — состав заказа (связь «многие ко многим» между заказами и товарами).

Связи: `pvz` 1—* `orders`, `orders` 1—* `order_tovar`,
`tovar` 1—* `order_tovar`.

## Структура репозитория
- `main.py` — исходный код приложения;
- `database/shoe_store.sql` — скрипт базы данных с демонстрационными данными;
- `docs/ER-diagram.png` — ER-диаграмма (PDF-версия — `docs/ER-diagram.pdf`);
- `config.ini.example` — образец настроек подключения;
- `requirements.txt` — зависимости проекта.

## Запуск PostgreSQL через Docker Compose

### Предварительные требования
- Docker Desktop с Linux containers
- Docker Compose v2
- файлы `compose.yaml`, `.env.example`, `docker/db-check/`

### Создание `.env`
1. Скопируйте `.env.example` в `.env`.
2. Задайте свой локальный пароль в `POSTGRES_PASSWORD`.
3. При необходимости измените `POSTGRES_HOST_PORT` (по умолчанию `5433`).
4. Файл `.env` не коммитится (указан в `.gitignore`).

### Запуск сервисов
```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail=40 db
docker compose logs --tail=40 db-check
```

Сервис `db` (PostgreSQL 14) работает постоянно. Сервис `db-check` — одноразовая проверка подключения; статус `Exited (0)` после успешной проверки является нормальным.

### Импорт базы данных
```bash
docker compose cp database/shoe_store.sql db:/tmp/shoe_store.sql
docker compose exec db psql -v ON_ERROR_STOP=1 -U shoe_user -d shoe_store -f /tmp/shoe_store.sql
docker compose run --rm db-check
```

После импорта `db-check` должен показать положительное число таблиц (в учебной схеме — 5).

### Адрес подключения приложения
В локальном `config.ini` для PyQt5-приложения укажите:
- `host = localhost`
- `port = 5433` (или значение `POSTGRES_HOST_PORT`)
- `name = shoe_store`
- `user = shoe_user`
- `password` — тот же, что в `.env`

Сервис `db-check` внутри Compose подключается к `db:5432` по имени сервиса.

### Проверка и остановка
```bash
docker compose exec db pg_isready -U shoe_user -d shoe_store
docker compose run --rm db-check
docker compose stop
docker compose start
```

Не используйте `docker compose down -v` в рамках практики №12: постоянные тома настраиваются в практике №13.

## Автор
Кононова Вероника, группа ЩПКО-02-23
