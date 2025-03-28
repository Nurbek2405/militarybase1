import sqlite3
import os

# Путь к базе данных в папке instance относительно корня проекта
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(base_dir, 'instance', 'medical_db.sqlite')

# Подключаемся к базе данных
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Проверяем, существует ли столбец note в таблице examination
cursor.execute("PRAGMA table_info(examination)")
columns = [info[1] for info in cursor.fetchall()]
if 'note' not in columns:
    # Добавляем столбец note в таблицу examination
    cursor.execute("ALTER TABLE examination ADD COLUMN note VARCHAR(200)")
    print("Столбец 'note' успешно добавлен в таблицу 'examination'!")
else:
    print("Столбец 'note' уже существует в таблице 'examination'.")

# Сохраняем изменения
conn.commit()
conn.close()