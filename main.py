import sys
import os
import shutil
import configparser
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QMessageBox, QFileDialog, QLabel,
    QPushButton, QInputDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QWidget
)
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt
from PyQt5 import uic
import psycopg2
import random
from psycopg2 import sql

# --- Константы ---
RESOURCES = "resources"
ICON_PATH = os.path.join(RESOURCES, "Icon.png")
LOGO_PATH = os.path.join(RESOURCES, "Icon.jpg")
PLACEHOLDER_PATH = os.path.join(RESOURCES, "picture.png")
COLOR_MAIN_BG = "#FFFFFF"
COLOR_ADD_BG = "#7FFF00"
COLOR_ACCENT = "#00FA9A"
COLOR_HIGH_DISCOUNT = "#2E8B57"
COLOR_OUT_OF_STOCK = "#ADD8E6"

# Глобальные переменные
current_user = {"fio": "Гость", "role": "guest"}

# --- Настройки подключения к БД ---
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

_db = config["database"] if config.has_section("database") else {}
DB_CONFIG = {
    "host": _db.get("host", "localhost"),
    "database": _db.get("name", "magazin_obuv"),
    "user": _db.get("user", "postgres"),
    "password": _db.get("password", ""),
    "port": int(_db.get("port", "5432")),
}
# --- Функции для работы с БД ---
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        QMessageBox.critical(None, "Ошибка БД", f"Не удалось подключиться к базе данных:\n{e}")
        return None

def fetch_all_products():
    conn = get_db_connection()
    if not conn:
        return []
    products = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tovar_id, tovar_article, tovar_name, tovar_category, tovar_information, 
                       tovar_creator, tovar_deliveryman, tovar_cost, tovar_ednica, tovar_count, tovar_sale, tovar_picture
                FROM tovar
                ORDER BY tovar_id;
            """)
            rows = cur.fetchall()
            for row in rows:
                product = {
                    "id": row[0],
                    "artikul": row[1],
                    "name": row[2],
                    "category": row[3],
                    "description": row[4],
                    "manufacturer": row[5],
                    "supplier": row[6],
                    "price": float(row[7]),
                    "unit": row[8],
                    "quantity": int(row[9]),
                    "discount": int(row[10]),
                    "image_path": row[11] if row[11] else PLACEHOLDER_PATH
                }
                products.append(product)
    except Exception as e:
        QMessageBox.warning(None, "Ошибка БД", f"Ошибка при загрузке товаров:\n{e}")
    finally:
        conn.close()
    return products

def fetch_product_by_id(product_id):
    conn = get_db_connection()
    if not conn:
        return None
    product = None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tovar_id, tovar_article, tovar_name, tovar_category, tovar_information, 
                       tovar_creator, tovar_deliveryman, tovar_cost, tovar_ednica, tovar_count, tovar_sale, tovar_picture
                FROM tovar
                WHERE tovar_id = %s;
            """, (product_id,))
            row = cur.fetchone()
            if row:
                product = {
                    "id": row[0],
                    "artikul": row[1],
                    "name": row[2],
                    "category": row[3],
                    "description": row[4],
                    "manufacturer": row[5],
                    "supplier": row[6],
                    "price": float(row[7]),
                    "unit": row[8],
                    "quantity": int(row[9]),
                    "discount": int(row[10]),
                    "image_path": row[11] if row[11] else PLACEHOLDER_PATH
                }
    except Exception as e:
        QMessageBox.warning(None, "Ошибка БД", f"Ошибка при загрузке товара:\n{e}")
    finally:
        conn.close()
    return product

def insert_product(product_data):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tovar (tovar_article, tovar_name, tovar_category, tovar_information, tovar_creator, 
                                   tovar_deliveryman, tovar_cost, tovar_ednica, tovar_count, tovar_sale, tovar_picture)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING tovar_id;
            """, (
                product_data["artikul"],
                product_data["name"],
                product_data["category"],
                product_data["description"],
                product_data["manufacturer"],
                product_data["supplier"],
                product_data["price"],
                product_data["unit"],
                product_data["quantity"],
                product_data["discount"],
                product_data["image_path"]
            ))
            new_id = cur.fetchone()[0]
            product_data["id"] = new_id
        conn.commit()
        return True
    except Exception as e:
        QMessageBox.warning(None, "Ошибка БД", f"Ошибка при добавлении товара:\n{e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_product(product_id, product_data):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE tovar
                SET tovar_article = %s, tovar_name = %s, tovar_category = %s, tovar_information = %s, tovar_creator = %s, 
                    tovar_deliveryman = %s, tovar_cost = %s, tovar_ednica = %s, tovar_count = %s, tovar_sale = %s, tovar_picture = %s
                WHERE tovar_id = %s;
            """, (
                product_data["artikul"],
                product_data["name"],
                product_data["category"],
                product_data["description"],
                product_data["manufacturer"],
                product_data["supplier"],
                product_data["price"],
                product_data["unit"],
                product_data["quantity"],
                product_data["discount"],
                product_data["image_path"],
                product_id
            ))
        conn.commit()
        return True
    except Exception as e:
        QMessageBox.warning(None, "Ошибка БД", f"Ошибка при обновлении товара:\n{e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_product(product_id):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM order_tovar WHERE tovar_id = %s;", (product_id,))
            count = cur.fetchone()[0]
            if count > 0:
                QMessageBox.warning(None, "Предупреждение", "Нельзя удалить товар, присутствующий в заказах.")
                return False
            cur.execute("DELETE FROM tovar WHERE tovar_id = %s;", (product_id,))
        conn.commit()
        return True
    except Exception as e:
        QMessageBox.critical(None, "Ошибка БД", f"Ошибка при удалении товара:\n{e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def fetch_all_orders():
    conn = get_db_connection()
    if not conn:
        return []
    orders = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.order_id, o.order_client_name, o.order_create_date, o.order_delivery_date, o.order_pvz_id_fk, 
                       o.order_code, o.order_status, p.pvz_address
                FROM orders o
                LEFT JOIN pvz p ON o.order_pvz_id_fk = p.pvz_id
                ORDER BY o.order_id;
            """)
            rows = cur.fetchall()
            for row in rows:
                order = {
                    "id": row[0],
                    "client_login": row[1],
                    "order_date": row[2],
                    "pickup_date": row[3],
                    "punkt_vydachi_id": row[4],
                    "pickup_code": row[5],
                    "status": row[6],
                    "pvz_address": row[7] or "Адрес не указан",
                    "items": []
                }
                cur.execute("""
                    SELECT t.tovar_id, t.tovar_name, t.tovar_cost, ot.count
                    FROM order_tovar ot
                    JOIN tovar t ON ot.tovar_id = t.tovar_id
                    WHERE ot.order_id = %s;
                """, (order["id"],))
                items = cur.fetchall()
                order["items"] = [
                    {
                        "product_id": item[0],
                        "name": item[1],
                        "price": float(item[2]),
                        "quantity": int(item[3])
                    }
                    for item in items
                ]
                orders.append(order)
    except Exception as e:
        QMessageBox.critical(None, "Ошибка БД", f"Ошибка при загрузке заказов:\n{e}")
    finally:
        conn.close()
    return orders

def fetch_order_by_id(order_id):
    conn = get_db_connection()
    if not conn:
        return None
    order = None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.order_id, o.order_client_name, o.order_create_date, o.order_delivery_date, o.order_pvz_id_fk, 
                       o.order_code, o.order_status
                FROM orders o
                WHERE o.order_id = %s;
            """, (order_id,))
            row = cur.fetchone()
            if row:
                order = {
                    "id": row[0],
                    "client_login": row[1],
                    "order_date": row[2],
                    "pickup_date": row[3],
                    "punkt_vydachi_id": row[4],
                    "pickup_code": row[5],
                    "status": row[6],
                    "items": []
                }
                cur.execute("""
                    SELECT t.tovar_id, t.tovar_name, t.tovar_cost, ot.count
                    FROM order_tovar ot
                    JOIN tovar t ON ot.tovar_id = t.tovar_id
                    WHERE ot.order_id = %s;
                """, (order["id"],))
                items = cur.fetchall()
                order["items"] = [
                    {
                        "product_id": item[0],
                        "name": item[1],
                        "price": float(item[2]),
                        "quantity": int(item[3])
                    }
                    for item in items
                ]
    except Exception as e:
        QMessageBox.critical(None, "Ошибка БД", f"Ошибка при загрузке заказа:\n{e}")
    finally:
        conn.close()
    return order

def insert_order(order_data):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders (order_article, order_create_date, order_delivery_date, order_pvz_id_fk, 
                                   order_client_name, order_code, order_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING order_id;
            """, (
                order_data["article_str"],
                order_data["order_date"],
                order_data["pickup_date"],
                order_data["punkt_vydachi_id"],
                order_data["client_login"],
                order_data["pickup_code"],
                order_data["status"]
            ))
            order_id = cur.fetchone()[0]
            for item in order_data["items"]:
                cur.execute("""
                    INSERT INTO order_tovar (order_id, tovar_id, count)
                    VALUES (%s, %s, %s);
                """, (
                    order_id,
                    item["product_id"],
                    item["quantity"]
                ))
        conn.commit()
        return True
    except Exception as e:
        QMessageBox.critical(None, "Ошибка БД", f"Ошибка при добавлении заказа:\n{e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_order(order_id, order_data):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE orders
                SET order_article = %s, order_create_date = %s, order_delivery_date = %s, order_pvz_id_fk = %s, 
                    order_client_name = %s, order_code = %s, order_status = %s
                WHERE order_id = %s;
            """, (
                order_data["article_str"],
                order_data["order_date"],
                order_data["pickup_date"],
                order_data["punkt_vydachi_id"],
                order_data["client_login"],
                order_data["pickup_code"],
                order_data["status"],
                order_id
            ))
            cur.execute("DELETE FROM order_tovar WHERE order_id = %s;", (order_id,))
            for item in order_data["items"]:
                cur.execute("""
                    INSERT INTO order_tovar (order_id, tovar_id, count)
                    VALUES (%s, %s, %s);
                """, (
                    order_id,
                    item["product_id"],
                    item["quantity"]
                ))
        conn.commit()
        return True
    except Exception as e:
        QMessageBox.critical(None, "Ошибка БД", f"Ошибка при обновлении заказа:\n{e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def authenticate_user(login, password):
    conn = get_db_connection()
    if not conn:
        return None
    user = None
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT user_name, user_role, user_login
                FROM client
                WHERE user_login = %s AND user_password = %s;
            """, (login, password))
            row = cur.fetchone()
            if row:
                user = {
                    "fio": row[0],
                    "role": row[1],
                    "login": row[2]
                }
    except Exception as e:
        QMessageBox.critical(None, "Ошибка БД", f"Ошибка при аутентификации:\n{e}")
    finally:
        conn.close()
    return user

def fetch_pickup_points():
    conn = get_db_connection()
    if not conn:
        return []
    points = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT pvz_id, pvz_address FROM pvz ORDER BY pvz_id;")
            rows = cur.fetchall()
            for row in rows:
                point = {
                    "id": row[0],
                    "address": row[1]
                }
                points.append(point)
    except Exception as e:
        QMessageBox.critical(None, "Ошибка БД", f"Ошибка при загрузке пунктов выдачи:\n{e}")
    finally:
        conn.close()
    return points


# --- НОВЫЙ OrdersViewWindow: загружаем из ui/view_orders.ui ---
class OrdersViewWindow(QMainWindow):
    def __init__(self, parent=None, is_admin=False, app=None):
        super().__init__(parent)
        self.app = app  # ← теперь app передаётся корректно
        self.is_admin = is_admin

        # Загружаем интерфейс из ui/view_orders.ui
        uic.loadUi("ui/view_orders.ui", self)
        self.setWindowTitle("Просмотр заказов Гит Проверка")

        self.orders = fetch_all_orders()
        self.current_index = 0

        # Подключаем стандартные кнопки
        self.prev_order.clicked.connect(self.prev_order_slot)
        self.next_order.clicked.connect(self.next_order_slot)
        self.go_main.clicked.connect(self.close)

        # Кнопка "Редактировать"
        self.edit_order_button = self.findChild(QPushButton, "edit_order_button")
        if self.edit_order_button:
            self.edit_order_button.setVisible(self.is_admin)
            self.edit_order_button.clicked.connect(self.edit_current_order)
        else:
            print("Внимание: кнопка 'edit_order_button' не найдена в UI")

        # Кнопка "Удалить"
        self.delete_order_button = self.findChild(QPushButton, "delete_order_button")
        if self.delete_order_button:
            self.delete_order_button.setVisible(self.is_admin)
            self.delete_order_button.clicked.connect(self.delete_current_order)
        else:
            print("Внимание: кнопка 'delete_order_button' не найдена в UI")

        # === ДОБАВЛЯЕМ КЛИК ПО ЦЕНТРАЛЬНОМУ ВИДЖЕТУ ===
        central_widget = self.findChild(QWidget, "centralwidget")
        if central_widget:
            central_widget.setCursor(Qt.PointingHandCursor)  # курсор-рука
            central_widget.mousePressEvent = self.on_info_click  # обработчик клика
        else:
            print("Внимание: centralwidget не найден в view_orders.ui")

        # Загрузка первого заказа или сообщения "нет заказов"
        if self.orders:
            self.load_order()
        else:
            self.show_no_orders()

    def on_info_click(self, event):
        if self.is_admin:
            self.edit_current_order()
        # Иначе — ничего не делаем (можно добавить подсказку, если нужно)

    # --- Новый метод: Удаление текущего заказа ---
    def delete_current_order(self):
        if not self.orders:
            QMessageBox.information(self, "Удаление заказа", "Нет заказов для удаления.")
            return

        current_order = self.orders[self.current_index]
        order_id = current_order["id"]

        # Запрос подтверждения
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить заказ №{order_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Вызов функции удаления из БД
            if self.delete_order_from_db(order_id):
                # Обновляем список заказов
                self.orders = fetch_all_orders()
                # Обновляем индекс (если заказов больше нет, то индекс сбрасывается)
                if len(self.orders) > 0:
                    # Если удалили последний заказ, переключаемся на предыдущий
                    if self.current_index >= len(self.orders):
                        self.current_index = len(self.orders) - 1
                    self.load_order()
                else:
                    # Если заказов больше нет
                    self.current_index = 0
                    self.show_no_orders()
                    QMessageBox.information(self, "Удаление заказа", "Заказ успешно удален. Список заказов пуст.")
            else:
                QMessageBox.critical(self, "Ошибка удаления", "Не удалось удалить заказ из базы данных.")

    # --- Вспомогательный метод для удаления заказа из БД ---
    def delete_order_from_db(self, order_id):
        conn = get_db_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cur:
                # Удаляем записи из связующей таблицы order_tovar
                cur.execute("DELETE FROM order_tovar WHERE order_id = %s;", (order_id,))
                # Удаляем сам заказ
                cur.execute("DELETE FROM orders WHERE order_id = %s;", (order_id,))
            conn.commit()
            return True
        except Exception as e:
            QMessageBox.critical(None, "Ошибка БД", f"Ошибка при удалении заказа:{e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def edit_current_order(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Редактирование", "Функция редактирования заказа будет реализована позже.")

    def load_order(self):
        o = self.orders[self.current_index]
        self.label_artikul.setText(f"Артикул: {o.get('pickup_code', '—')}")
        self.label_status.setText(f"Статус: {o.get('status', '—')}")
        self.label_pvz.setText(f"ПВЗ: {o.get('pvz_address', '—')}")
        self.label_date_order.setText(f"Дата заказа: {o.get('order_date', '—')}")
        delivery_date = o.get('pickup_date', '—')
        self.label_4.setText(f"{delivery_date}")

    def show_no_orders(self):
        self.label_artikul.setText("Артикул: —")
        self.label_status.setText("Статус: Нет заказов")
        self.label_pvz.setText("ПВЗ: —")
        self.label_date_order.setText("Дата заказа: —")
        self.label_4.setText("Дата доставки:—")

    def next_order_slot(self):
        if self.orders:
            self.current_index = (self.current_index + 1) % len(self.orders)
            self.load_order()

    def prev_order_slot(self):
        if self.orders:
            self.current_index = (self.current_index - 1) % len(self.orders)
            self.load_order()

    def closeEvent(self, event):
        if self.parent():
            self.parent().show()
        event.accept()


# --- Приложение ---
class ShoeApp(QApplication):
    def __init__(self, args):
        super().__init__(args)
        self.setApplicationName("Обувь")
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self.login_win = None
        self.main_win = None
        self.product_form = None
        self.order_form = None
        self.show_login()

    def show_login(self):
        if self.login_win is None:
            self.login_win = LoginWindow(self)
        self.login_win.show()
        if self.main_win:
            self.main_win.close()

    def show_main(self, user):
        global current_user
        current_user = user
        if self.main_win is None:
            self.main_win = MainWindow(self)
        else:
            self.main_win.update_user()
        self.main_win.show()
        if self.login_win:
            self.login_win.close()

    def open_product_form(self, product_id=None):
        if self.product_form is not None:
            QMessageBox.critical(self.main_win, "Ошибка", "Окно редактирования уже открыто.")
            return
        self.product_form = ProductForm(self, product_id)
        self.product_form.finished.connect(lambda code: self.on_product_closed())
        self.product_form.show()

    def on_product_closed(self):
        self.product_form = None
        if self.main_win:
            self.main_win.load_product()

    def open_order_form(self, order_id=None):
        if self.order_form is not None:
            QMessageBox.critical(self.main_win, "Ошибка", "Окно заказа уже открыто.")
            return
        self.order_form = OrderForm(self, order_id)
        self.order_form.finished.connect(lambda code: self.on_order_closed())
        self.order_form.show()

    def on_order_closed(self):
        self.order_form = None
        if self.main_win:
            self.main_win.load_product()


# --- LoginWindow ---
class LoginWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        uic.loadUi("ui/login_form.ui", self)
        self.setWindowTitle("Вход в систему — Магазин обуви")
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        try:
            self.meneger_login_botton.clicked.connect(self.attempt_login)
            self.guest.clicked.connect(self.guest_login)
        except Exception:
            pass
        try:
            pixmap = QPixmap(LOGO_PATH)
            if not pixmap.isNull():
                self.label_4.setPixmap(pixmap.scaled(151, 121, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            pass
        self.setFont(QFont("Times New Roman", 14))

    def attempt_login(self):
        login_text = self.login.text().strip()
        password_text = self.password.text().strip()
        if not login_text or not password_text:
            QMessageBox.critical(self, "Ошибка", "Введите логин и пароль")
            return
        user = authenticate_user(login_text, password_text)
        if user:
            self.app.show_main(user)
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный логин или пароль")

    def guest_login(self):
        self.app.show_main({"fio": "Гость", "role": "guest"})


# --- MainWindow ---
class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        uic.loadUi("ui/Main.ui", self)
        self.setWindowTitle("Обувь — Просмотр товара")
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self.current_index = 0
        self.products = []

        # Подключаем клик по описанию
        if hasattr(self, 'parametr'):
            self.parametr.mousePressEvent = self.on_product_info_click

        # ... остальные подключения кнопок (back_button, search и т.д.)

        # Подключаем клик по описанию
        if hasattr(self, 'parametr'):
            self.parametr.mousePressEvent = self.on_product_info_click
        try:
            self.back_button.clicked.connect(self.logout)
            self.search.clicked.connect(self.on_search_clicked)
            self.filter.clicked.connect(self.on_filter_clicked)
            self.add.clicked.connect(self.add_product)
            self.delet.clicked.connect(self.delete_product)
            self.pushButton_2.clicked.connect(self.view_orders)
            self.pushButton.clicked.connect(self.create_order)
            self.pushButton_3.clicked.connect(self.prev_product)
            self.pushButton_4.clicked.connect(self.next_product)
        except Exception:
            pass
        self.update_user()
        self.load_product()
        self.setFont(QFont("Times New Roman", 14))

    def closeEvent(self, event):
        self.app.show_login()
        event.accept()

    def update_user(self):
        try:
            self.fio_.setText(f"{current_user['fio']}")
        except Exception:
            pass
        role = current_user["role"]
        for widget in [self.search, self.filter]:
            widget.setVisible(role in ("Менеджер", "Администратор"))
        for widget in [self.add, self.delet, self.pushButton]:
            widget.setVisible(role == "Администратор")
        self.pushButton_2.setVisible(role in ("Менеджер", "Администратор"))

    def logout(self):
        self.app.show_login()

    def load_product(self):
        self.products = fetch_all_products()
        if not self.products:
            try:
                self.parametr.setText("Нет товаров")
                self.photo.clear()
                self.sale.setText("Скидка")
                self.sale.setStyleSheet("")
            except Exception:
                pass
            return
        idx = max(0, min(self.current_index, len(self.products) - 1))
        prod = self.products[idx]
        img_path = prod.get("image_path") or PLACEHOLDER_PATH
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            pixmap = QPixmap(PLACEHOLDER_PATH)
        try:
            self.photo.setPixmap(pixmap.scaled(self.photo.width(), self.photo.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            pass
        price_text = f"{prod['price']:.2f}"
        if prod.get("discount", 0) > 0:
            discounted = prod["price"] * (1 - prod["discount"] / 100.0)
            price_text = f"<s><span style='color:red'>{prod['price']:.2f}</span></s>  <span style='color:black'>{discounted:.2f}</span>"
        quantity_color = COLOR_OUT_OF_STOCK if prod['quantity'] <= 0 else "transparent"
        info = (
            f"<b>Артикул:</b> {prod['artikul']}<br>"
            f"<b>Категория товара:</b> {prod['category']}<br>"
            f"<b>Наименование товара:</b> {prod['name']}<br>"
            f"<b>Описание товара:</b> {prod['description']}<br>"
            f"<b>Производитель:</b> {prod['manufacturer']}<br>"
            f"<b>Поставщик:</b> {prod['supplier']}<br>"
            f"<b>Цена:</b> {price_text}<br>"
            f"<b>Единица измерения:</b> {prod['unit']}<br>"
            f"<span style='background-color:{quantity_color};'><b>Количество на складе:</b> {prod['quantity']}</span>"
        )
        self.parametr.setText(info)
        self.parametr.setTextFormat(Qt.RichText)
        discount = prod.get("discount", 0)
        if discount > 15:
            self.sale.setStyleSheet(f"background-color: {COLOR_HIGH_DISCOUNT}; color: white; font-weight: bold;")
        else:
            self.sale.setStyleSheet("")
        self.sale.setText(f"Скидка\n{discount:.1f}%")
    def on_product_info_click(self, event):

        if current_user["role"] == "Администратор":
            if self.products and 0 <= self.current_index < len(self.products):
                prod_id = self.products[self.current_index]["id"]
                self.app.open_product_form(product_id=prod_id)
        else:
            QMessageBox.information(self, "Доступ", "Редактировать товары может только администратор.")
    def next_product(self):
        if self.products:
            self.current_index = (self.current_index + 1) % len(self.products)
            self.load_product()

    def prev_product(self):
        if self.products:
            self.current_index = (self.current_index - 1) % len(self.products)
            self.load_product()

    def on_search_clicked(self):
        if current_user["role"] not in ("Менеджер", "Администратор"):
            QMessageBox.information(self, "Доступ", "Поиск доступен только менеджеру и администратору.")
            return
        text, ok = QInputDialog.getText(self, "Поиск", "Введите поисковый текст:")
        if not ok or not text.strip():
            return
        query = text.strip().lower()
        found = [p for p in self.products if query in p["name"].lower() or query in p["description"].lower()]
        if found:
            self.current_index = next(i for i, p in enumerate(self.products) if p["id"] == found[0]["id"])
            self.load_product()
            QMessageBox.information(self, "Найдено", f"Найден товар: {found[0]['name']}")
        else:
            QMessageBox.information(self, "Ничего не найдено", "Совпадений не обнаружено.")

    def on_filter_clicked(self):
        if current_user["role"] not in ("Менеджер", "Администратор"):
            QMessageBox.information(self, "Доступ", "Фильтрация доступна только менеджеру и администратору.")
            return
        suppliers = sorted({p.get("supplier", "") for p in self.products})
        suppliers.insert(0, "Все поставщики")
        supplier, ok = QInputDialog.getItem(self, "Фильтр", "Поставщик:", suppliers, 0, False)
        if not ok:
            return
        sort_choice, ok2 = QInputDialog.getItem(self, "Сортировка", "Сортировать по количеству:",
                                                ["Нет", "По возрастанию", "По убыванию"], 0, False)
        if not ok2:
            return
        filtered = [p for p in self.products if supplier == "Все поставщики" or p.get("supplier") == supplier]
        if sort_choice == "По возрастанию":
            filtered.sort(key=lambda x: x.get("quantity", 0))
        elif sort_choice == "По убыванию":
            filtered.sort(key=lambda x: x.get("quantity", 0), reverse=True)
        if filtered:
            self.current_index = next(i for i, p in enumerate(self.products) if p["id"] == filtered[0]["id"])
            self.load_product()
            QMessageBox.information(self, "Результат", f"Показан товар: {filtered[0]['name']}")
        else:
            QMessageBox.information(self, "Результат", "Нет товаров по заданным критериям.")

    def add_product(self):
        if current_user["role"] != "Администратор":
            QMessageBox.warning(self, "Доступ", "Добавлять товары может только администратор.")
            return
        self.app.open_product_form()

    def delete_product(self):
        if current_user["role"] != "Администратор":
            QMessageBox.warning(self, "Доступ", "Удалять товары может только администратор.")
            return
        if not self.products:
            return
        prod_id = self.products[self.current_index]["id"]
        reply = QMessageBox.question(self, "Подтверждение", "Удалить текущий товар?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if delete_product(prod_id):
                self.products = fetch_all_products()
                if self.current_index >= len(self.products):
                    self.current_index = max(0, len(self.products) - 1)
                self.load_product()
                QMessageBox.information(self, "Успех", "Товар удалён.")
            else:
                pass

    def view_orders(self):
        role = current_user["role"]
        if role not in ("Менеджер", "Администратор"):
            QMessageBox.information(self, "Доступ", "Просмотр заказов доступен только менеджеру и администратору.")
            return
        is_admin = (role == "Администратор")
        self.orders_window = OrdersViewWindow(parent=self, is_admin=is_admin, app=self.app)
        self.orders_window.show()
        self.hide()

    def create_order(self):
        if current_user["role"] != "Администратор":
            QMessageBox.warning(self, "Доступ", "Создавать заказы может только администратор.")
            return
        self.app.open_order_form()


# --- ProductForm ---
class ProductForm(QDialog):
    def __init__(self, app, product_id=None):
        super().__init__()
        self.app = app
        self.product_id = product_id
        uic.loadUi("ui/product_form.ui", self)
        title = "Добавление товара" if product_id is None else "Редактирование товара"
        self.setWindowTitle(title)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        try:
            self.pushButton.clicked.connect(self.select_image)
        except Exception:
            pass
        try:
            self.btn_save.clicked.connect(self.save)
            self.btn_cancel.clicked.connect(self.reject)
        except Exception:
            pass
        self.image_path = PLACEHOLDER_PATH
        try:
            if hasattr(self, "category_combo"):
                self.category_combo.addItems(["Спорт", "Зима", "Повседневные", "Детские"])
            if hasattr(self, "manufacturer_combo"):
                self.manufacturer_combo.addItems(["Nike", "Ecco", "Belle", "Adidas"])
        except Exception:
            pass
        if product_id is not None:
            prod = fetch_product_by_id(product_id)
            if prod:
                try:
                    self.id_label.setText(str(prod["id"]))
                except Exception:
                    pass
                self.image_path = prod.get("image_path", PLACEHOLDER_PATH)
                self.display_image()
                try:
                    self.name_edit.setText(prod["name"])
                except Exception:
                    pass
                try:
                    if hasattr(self, "category_combo") and prod["category"] in [self.category_combo.itemText(i) for i in
                                                                                range(self.category_combo.count())]:
                        self.category_combo.setCurrentText(prod["category"])
                except Exception:
                    pass
                try:
                    self.description_edit.setPlainText(prod["description"])
                except Exception:
                    pass
                try:
                    if hasattr(self, "manufacturer_combo") and prod["manufacturer"] in [
                        self.manufacturer_combo.itemText(i) for i in range(self.manufacturer_combo.count())]:
                        self.manufacturer_combo.setCurrentText(prod["manufacturer"])
                except Exception:
                    pass
                try:
                    self.supplier_edit.setText(prod["supplier"])
                except Exception:
                    pass
                try:
                    self.price_spin.setValue(float(prod["price"]))
                except Exception:
                    pass
                try:
                    self.unit_edit.setText(prod["unit"])
                except Exception:
                    pass
                try:
                    self.quantity_spin.setValue(int(prod["quantity"]))
                except Exception:
                    pass
                try:
                    self.discount_spin.setValue(float(prod["discount"]))
                except Exception:
                    pass
        else:
            try:
                self.id_label.setText("")
            except Exception:
                pass
        self.setFont(QFont("Times New Roman", 14))

    def display_image(self):
        pixmap = QPixmap(self.image_path)
        if pixmap.isNull():
            pixmap = QPixmap(PLACEHOLDER_PATH)
        try:
            w = self.image_label.width() or 300
            h = self.image_label.height() or 200
            self.image_label.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            self.image_label.setPixmap(pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "",
                                              "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            img = QPixmap(path)
            if img.isNull():
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить изображение.")
                return
            try:
                if not os.path.exists(RESOURCES):
                    os.makedirs(RESOURCES)
                base_name = os.path.basename(path)
                dest = os.path.join(RESOURCES, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{base_name}")
                shutil.copy(path, dest)
                self.image_path = dest
            except Exception:
                self.image_path = path
            self.display_image()

    def save(self):
        name = ""
        try:
            name = self.name_edit.text().strip()
        except Exception:
            pass
        if not name:
            QMessageBox.critical(self, "Ошибка", "Введите наименование.")
            return
        try:
            quantity_val = int(self.quantity_spin.value())
            if quantity_val < 0:
                QMessageBox.warning(self, "Предупреждение", "Количество не может быть отрицательным.")
                return
        except Exception:
            pass
        new_prod = {
            "artikul": str(self.id_label.text()) if self.id_label.text() else "",
            "name": name,
            "category": self.category_combo.currentText() if hasattr(self, "category_combo") else "",
            "description": self.description_edit.toPlainText().strip() if hasattr(self, "description_edit") else "",
            "manufacturer": self.manufacturer_combo.currentText() if hasattr(self, "manufacturer_combo") else "",
            "supplier": self.supplier_edit.text().strip() if hasattr(self, "supplier_edit") else "",
            "price": float(self.price_spin.value()) if hasattr(self, "price_spin") else 0.0,
            "unit": self.unit_edit.text().strip() if hasattr(self, "unit_edit") else "",
            "quantity": int(self.quantity_spin.value()) if hasattr(self, "quantity_spin") else 0,
            "discount": int(self.discount_spin.value()) if hasattr(self, "discount_spin") else 0,
            "image_path": self.image_path
        }
        success = False
        if self.product_id is None:
            success = insert_product(new_prod)
        else:
            success = update_product(self.product_id, new_prod)
        if success:
            QMessageBox.information(self, "Успех", "Товар сохранён.")
            self.accept()
        else:
            pass

    def closeEvent(self, event):
        self.reject()
        event.accept()


# --- OrderForm ---
# --- OrderForm ---
class OrderForm(QDialog):
    def __init__(self, app, order_id=None):
        super().__init__()
        self.app = app
        self.order_id = order_id
        uic.loadUi("ui/order_form.ui", self)
        title = "Новый заказ" if order_id is None else "Редактирование заказа"
        self.setWindowTitle(title)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        try:
            self.comboBoxArticle.clear()
            products = fetch_all_products()
            for p in products:
                self.comboBoxArticle.addItem(p["artikul"], p["id"])
        except Exception:
            pass
        # Исправленное имя виджета: lineEditPickupAddress вместо comboBoxPickupPoint
        try:
            self.lineEditPickupAddress.clear()
            pickup_points = fetch_pickup_points()
            for point in pickup_points:
                self.lineEditPickupAddress.addItem(point["address"], point["id"])
        except Exception:
            pass
        try:
            self.pushButton.clicked.connect(self.save)
            self.pushButtonCancel.clicked.connect(self.reject)
        except Exception:
            pass
        if order_id is not None:
            ord_obj = fetch_order_by_id(order_id)
            if ord_obj:
                try:
                    if ord_obj["items"]:
                        article_id = ord_obj["items"][0]["product_id"]
                        for i in range(self.comboBoxArticle.count()):
                            if self.comboBoxArticle.itemData(i) == article_id:
                                self.comboBoxArticle.setCurrentIndex(i)
                                break
                except Exception:
                    pass
                try:
                    status = ord_obj.get("status", "В обработке")
                    idx = self.comboBoxStatus.findText(status)
                    if idx >= 0:
                        self.comboBoxStatus.setCurrentIndex(idx)
                except Exception:
                    pass
                try:
                    self.lineEditPickupAddress.setText(ord_obj.get("pickup_code", ""))
                except Exception:
                    pass
                try:
                    dt_order = ord_obj.get("order_date")
                    if dt_order:
                        self.dateEdit.setDate(dt_order)
                    dt_pick = ord_obj.get("pickup_date")
                    if dt_pick:
                        self.dateEdit_2.setDate(dt_pick)
                except Exception:
                    pass
                # Исправленное имя виджета: lineEditPickupAddress вместо comboBoxPickupPoint
                try:
                    pvz_id = ord_obj.get("punkt_vydachi_id")
                    for i in range(self.lineEditPickupAddress.count()):
                        if self.lineEditPickupAddress.itemData(i) == pvz_id:
                            self.lineEditPickupAddress.setCurrentIndex(i)
                            break
                except Exception:
                    pass
        self.setFont(QFont("Times New Roman", 14))

    def save(self):
        idx = -1
        try:
            idx = self.comboBoxArticle.currentIndex()
        except Exception:
            pass
        if idx < 0:
            QMessageBox.critical(self, "Ошибка", "Выберите артикул.")
            return
        article_id = None
        try:
            article_id = self.comboBoxArticle.itemData(idx)
        except Exception:
            pass
        if article_id is None:
            QMessageBox.critical(self, "Ошибка", "Неверный артикул.")
            return
        status = self.comboBoxStatus.currentText() if hasattr(self, "comboBoxStatus") else "В обработке"
        pickup_code = random.randint(1000, 9999)
        try:
            order_date = self.dateEdit.date().toPyDate() if hasattr(self, "dateEdit") else datetime.now().date()
        except Exception:
            order_date = datetime.now().date()
        try:
            pickup_date = self.dateEdit_2.date().toPyDate() if hasattr(self, "dateEdit_2") else datetime.now().date()
        except Exception:
            pickup_date = datetime.now().date()
        # Исправленное имя виджета: lineEditPickupAddress вместо comboBoxPickupPoint
        punkt_vydachi_id = None
        try:
            punkt_vydachi_id = self.lineEditPickupAddress.itemData(self.lineEditPickupAddress.currentIndex())
        except Exception:
            pass
        if punkt_vydachi_id is None:
            QMessageBox.critical(self, "Ошибка", "Выберите адрес пункта выдачи.")
            return
        new_order = {
            "client_login": "1diph5e@tutanota.com",
            "order_date": order_date,
            "pickup_date": pickup_date,
            "punkt_vydachi_id": punkt_vydachi_id,
            "pickup_code": pickup_code,
            "status": status,
            "article_str": f"{article_id}, 1",
            "items": [
                {
                    "product_id": article_id,
                    "quantity": 1
                }
            ]
        }
        success = False
        if self.order_id is None:
            success = insert_order(new_order)
        else:
            success = update_order(self.order_id, new_order)
        if success:
            QMessageBox.information(self, "Успех", "Заказ сохранён.")
            self.accept()
        else:
            pass

    def closeEvent(self, event):
        self.reject()
        event.accept()


# --- Запуск приложения ---
if __name__ == "__main__":
    app = ShoeApp(sys.argv)
    sys.exit(app.exec_())