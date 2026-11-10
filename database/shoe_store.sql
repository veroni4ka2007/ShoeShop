-- Учебная база данных «Магазин обуви»
-- СУБД: PostgreSQL 14+
-- Скрипт создаёт схему и демонстрационные данные для приложения main.py.
-- Учётные записи пользователей добавляются администратором отдельно:
-- пароли в репозиторий не включаются.

DROP TABLE IF EXISTS order_tovar;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS tovar;
DROP TABLE IF EXISTS client;
DROP TABLE IF EXISTS pvz;

CREATE TABLE pvz (
    pvz_id      SERIAL PRIMARY KEY,
    pvz_address VARCHAR(200) NOT NULL
);

CREATE TABLE client (
    user_login    VARCHAR(50) PRIMARY KEY,
    user_password VARCHAR(100) NOT NULL,
    user_name     VARCHAR(100) NOT NULL,
    user_role     VARCHAR(30)  NOT NULL
        CHECK (user_role IN ('Администратор', 'Менеджер', 'Гость'))
);

CREATE TABLE tovar (
    tovar_id          SERIAL PRIMARY KEY,
    tovar_article     VARCHAR(20)  NOT NULL UNIQUE,
    tovar_name        VARCHAR(150) NOT NULL,
    tovar_category    VARCHAR(100),
    tovar_information TEXT,
    tovar_creator     VARCHAR(100),
    tovar_deliveryman VARCHAR(100),
    tovar_cost        NUMERIC(10, 2) NOT NULL DEFAULT 0,
    tovar_ednica      VARCHAR(20),
    tovar_count       INTEGER NOT NULL DEFAULT 0 CHECK (tovar_count >= 0),
    tovar_sale        INTEGER NOT NULL DEFAULT 0 CHECK (tovar_sale BETWEEN 0 AND 100),
    tovar_picture     TEXT
);

CREATE TABLE orders (
    order_id            SERIAL PRIMARY KEY,
    order_article       VARCHAR(20) NOT NULL UNIQUE,
    order_create_date   DATE NOT NULL,
    order_delivery_date DATE,
    order_pvz_id_fk     INTEGER REFERENCES pvz (pvz_id),
    order_client_name   VARCHAR(100) NOT NULL,
    order_code          VARCHAR(20),
    order_status        VARCHAR(50) NOT NULL DEFAULT 'Новый'
);

CREATE TABLE order_tovar (
    order_id INTEGER NOT NULL REFERENCES orders (order_id) ON DELETE CASCADE,
    tovar_id INTEGER NOT NULL REFERENCES tovar (tovar_id),
    count    INTEGER NOT NULL DEFAULT 1 CHECK (count > 0),
    PRIMARY KEY (order_id, tovar_id)
);

INSERT INTO pvz (pvz_address) VALUES
    ('г. Москва, ул. Ленина, д. 10'),
    ('г. Москва, пр-т Мира, д. 25');

INSERT INTO tovar (tovar_article, tovar_name, tovar_category, tovar_information,
                   tovar_creator, tovar_deliveryman, tovar_cost, tovar_ednica,
                   tovar_count, tovar_sale, tovar_picture) VALUES
    ('ART-001', 'Кроссовки Run Fast', 'Кроссовки',
     'Лёгкие беговые кроссовки для ежедневных тренировок.',
     'RunFast', 'ООО «Спортопт»', 5490.00, 'пара', 12, 15, 'resources/picture.png'),
    ('ART-002', 'Туфли Classic', 'Туфли',
     'Классические кожаные туфли для делового стиля.',
     'ClassicShoes', 'ООО «ОбувьТорг»', 7290.00, 'пара', 4, 0, 'resources/picture.png'),
    ('ART-003', 'Ботинки Winter', 'Ботинки',
     'Утеплённые ботинки для холодной погоды.',
     'WinterLine', 'ООО «ОбувьТорг»', 8990.00, 'пара', 0, 20, 'resources/picture.png'),
    ('ART-004', 'Сандалии Summer', 'Сандалии',
     'Летние сандалии с регулируемыми ремешками.',
     'SummerStep', 'ИП Смирнов А. А.', 2590.00, 'пара', 7, 10, 'resources/picture.png');

INSERT INTO orders (order_article, order_create_date, order_delivery_date,
                    order_pvz_id_fk, order_client_name, order_code, order_status) VALUES
    ('ORD-001', DATE '2026-11-01', DATE '2026-11-05', 1, 'Иванов Иван Иванович', '482913', 'Новый');

INSERT INTO order_tovar (order_id, tovar_id, count) VALUES
    (1, 1, 2),
    (1, 3, 1);
