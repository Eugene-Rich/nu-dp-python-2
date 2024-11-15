import sqlite3
import os

directory_path = os.path.dirname(os.path.abspath(__file__))
dir_db = os.path.join(directory_path, "db", "bot_01.db")

# Устанавливаем соединение с базой данных
connection = sqlite3.connect(dir_db)
cursor = connection.cursor()

# Создаем таблицу "Ответ сервера"
cursor.execute('''
CREATE TABLE IF NOT EXISTS ServerResponse (
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
userid INTEGER NOT NULL,
timereg INTEGER,
uinrequest INTEGER,
kolvotovaweb INTEGER,
nkgalle INTEGER)
''')

# Создаем таблицу "Многострочная часть"
cursor.execute('''
CREATE TABLE IF NOT EXISTS MultilinePart (
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
userid INTEGER NOT NULL,
timereg INTEGER,
uinrequest INTEGER,
nomstr INTEGER,              
naimtov TEXT,
uintov TEXT,
uinmag TEXT,
uingor TEXT,
ostatok INTEGER,
cena FLOAT,
glvnfoto TEXT,
opisanie TEXT)              
''')

# Создаем таблицу Users
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
userid INTEGER NOT NULL,
timereg INTEGER,
vcommand TEXT,
vibzn TEXT,
vib_uin TEXT
)
''')

# Сохраняем изменения и закрываем соединение
connection.commit()
connection.close()