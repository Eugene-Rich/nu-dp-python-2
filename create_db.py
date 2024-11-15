import os
import sqlite3

# Создание базы данных

directory_path = os.path.dirname(os.path.abspath(__file__))
dir_db = os.path.join(directory_path, "db", "bot_01.db")

connection = sqlite3.connect(dir_db)

connection.close()

