import sqlite3
import os

# Путь к базе данных в папке instance относительно корня проекта
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(base_dir, 'instance', 'medical_db.sqlite')

# Подключаемся к базе данных
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Добавляем столбец note
cursor.execute("ALTER TABLE employee ADD COLUMN note VARCHAR(200)")

# Сохраняем изменения
conn.commit()
conn.close()

print("Столбец 'note' успешно добавлен в таблицу 'employee'!")