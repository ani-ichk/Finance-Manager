import sqlite3

def init_database():
    conn = sqlite3.connect('finance_manager.db')
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS Categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        category_type TEXT NOT NULL CHECK (category_type IN ('income', 'expense')))""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        operation_date DATE NOT NULL,
                        category_id INTEGER NOT NULL,
                        description TEXT,
                        amount DECIMAL(10, 2) NOT NULL,
                        operation_type TEXT NOT NULL CHECK(operation_type IN ('income', 'expense')),
                        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS Budget_limits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category_id INTEGER NOT NULL,
                        amount DECIMAL(10, 2) NOT NULL,
                        period_type TEXT NOT NULL CHECK(period_type IN ('month', 'year')),
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE)""")

    default_categories = [
        ('Зарплата', 'income'),
        ('Премия', 'income'),
        ('Инвестиции', 'income'),
        ('Еда', 'expense'),
        ('Транспорт', 'expense'),
        ('Развлечения', 'expense'),
        ('Коммунальные услуги', 'expense'),
        ('Здоровье', 'expense'),
        ('Одежда', 'expense'),
        ('Образование', 'expense')]

    for name, category_type in default_categories:
        try:
            cursor.execute("""INSERT INTO Categories (name, category_type) VALUES (?, ?)""", (name, category_type))
        except sqlite3.IntegrityError:
            pass  # если категория уже есть - пропускаем

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()