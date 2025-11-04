import sqlite3
from datetime import date
from os.path import curdir
from typing import List, Dict


class DatabaseManager:
    def __init__(self, db: str = "finance_manager.db"):
        self.db = db

    def connection(self):
        """ Соединение с БД """
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        return conn

    def get_categories(self, category_type: str = None):
        try:
            with self.connection() as conn:
                query = "SELECT * FROM Categories"
                params = []
                if category_type:
                    query += " WHERE category_type = ?"
                    params.append(category_type)
                query += " ORDER BY name"
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:  # Обрабатываем возможные ошибки
            print(f"Ошибка при получении категорий: {e}")  # Выводим сообщение об ошибке
            return []  # Возвращаем пустой список в случае ошибки

    # Методы для работы с операциями
    def add_operation(self, amount: float, category_id: int, operation_date: str, description: str = ""):
        """ Добавление новой операции """
        try:
            with self.connection() as conn:
                cursor = conn.execute("SELECT category_type FROM Categories WHERE id = ?", (category_id,))
                result = cursor.fetchone()
                operation_type = result['category_type']
                cursor = conn.execute("""
                    INSERT INTO Operations (operation_date, category_id, description, amount, operation_type)
                    VALUES (?, ?, ?, ?, ?)""", (operation_date, category_id, description, amount, operation_type))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при добавлении операции: {e}")
            return False

    def get_all_operations(self, filter_type: str = "all"):
        """ Получение всех операций с фильтрацией (все по умол.) """
        try:
            query = """SELECT 
                            Operations.id,
                            Operations.operation_date as date,
                            Categories.name as category_name,
                            Categories.category_type as category_type,
                            Operations.description,
                            Operations.amount,
                            Operations.operation_type
                       FROM Operations
                       JOIN Categories ON Operations.category_id = Categories.id"""

            if filter_type == "income":
                query += " AND Operations.operation_type = 'income'"
            elif filter_type == "expense":
                query += " AND Operations.operation_type = 'expense'"

            query += " ORDER BY Operations.operation_date DESC"

            with self.connection() as conn:
                cursor = conn.execute(query)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка при загрузке операций: {e}")
            return []

    def delete_operation(self, operation_id: int):
        """ Удаление операции по ID """
        try:
            with self.connection() as conn:
                conn.execute("DELETE FROM Operations WHERE id = ?", (operation_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при удалении операции: {e}")
            return False

    # Методы для аналитики
    def get_financial_summary(self, start_date: str, end_date: str):
        """ Получение финансовой сводки за период """
        try:
            with self.connection() as conn:
                # Считаем доходы
                income_cursor = conn.execute("""SELECT COALESCE(SUM(amount), 0) as total_income 
                                          FROM Operations 
                                          WHERE operation_type = 'income' AND operation_date BETWEEN ? AND ?""",
                                             (start_date, end_date))
                total_income = income_cursor.fetchone()['total_income']

                # Считаем расходы
                expense_cursor = conn.execute("""SELECT COALESCE(SUM(amount), 0) as total_expense 
                                          FROM Operations 
                                          WHERE operation_type = 'expense' AND operation_date BETWEEN ? AND ?""",
                                              (start_date, end_date))
                total_expense = expense_cursor.fetchone()['total_expense']

                return {
                    'income': total_income,
                    'expense': total_expense,
                    'balance': total_income - total_expense
                }
        except Exception as e:
            print(f"Ошибка при получении финансовой сводки: {e}")
            return {'income': 0, 'expense': 0, 'balance': 0}

    def get_expense_statistics(self, start_date: str, end_date: str):
        """ Получение статистики расходов по категориям"""
        try:
            with self.connection() as conn:
                cursor = conn.execute("""
                    SELECT Categories.id, Categories.name, SUM(Operations.amount) as total
                    FROM Operations
                    JOIN Categories ON Operations.category_id = Categories.id
                    WHERE Operations.operation_type = 'expense' AND Operations.operation_date BETWEEN ? AND ?
                    GROUP BY Categories.id, Categories.name
                    HAVING total > 0
                    ORDER BY total DESC""", (start_date, end_date))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка при получении статистики расходов: {e}")
            return []

    def get_income_expense_by_period(self, start_date: str, end_date: str, group_by: str = 'day'):
        """ Получение данных для графика доходов/расходов"""
        try:
            if group_by == 'day':
                group_format = "strftime('%Y-%m-%d', operation_date)"
            else:  # month
                group_format = "strftime('%Y-%m', operation_date)"

            with self.connection() as conn:
                cursor = conn.execute(f"""
                    SELECT 
                        {group_format} as period,
                        SUM(CASE WHEN operation_type = 'income' THEN amount ELSE 0 END) as income,
                        SUM(CASE WHEN operation_type = 'expense' THEN amount ELSE 0 END) as expense
                    FROM Operations
                    WHERE operation_date BETWEEN ? AND ?
                    GROUP BY period
                    ORDER BY period""", (start_date, end_date))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка при получении данных для графика: {e}")
            return []

    # Методы для работы с бюджетом
    def add_budget_limit(self, category_id: int, amount: float, month_year: str):
        """ Добавление лимита бюджета для категории"""
        try:
            # Преобразуем дату начала и конца месяца
            start_date = month_year
            year, month, _ = month_year.split('-')
            end_date = f"{year}-{month}-{self.get_days_in_month(int(year), int(month))}"

            with self.connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO Budget_limits (category_id, amount, period_type, start_date, end_date)
                    VALUES (?, ?, 'month', ?, ?)""",
                                      (category_id, amount, start_date, end_date))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при добавлении лимита: {e}")
            return False

    def get_days_in_month(self, year: int, month: int):
        """ Узнаем сколько дней в месяце"""
        if month == 12:
            return 31
        return (date(year, month + 1, 1) - date(year, month, 1)).days

    def get_budget_limits(self, month_year: str):
        """ Получение всех бюджетных лимитов для месяца"""
        try:
            start_date = month_year
            year, month, _ = month_year.split('-')
            end_date = f"{year}-{month}-{self.get_days_in_month(int(year), int(month))}"

            with self.connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        Budget_limits.id,
                        Budget_limits.category_id,
                        Budget_limits.amount as limit_amount,
                        Categories.name as category_name,
                        COALESCE((
                            SELECT SUM(Operations.amount) 
                            FROM Operations 
                            WHERE Operations.category_id = Budget_limits.category_id 
                            AND Operations.operation_date BETWEEN Budget_limits.start_date AND Budget_limits.end_date
                        ), 0) as spent_amount
                    FROM Budget_limits
                    JOIN Categories ON Budget_limits.category_id = Categories.id
                    WHERE Budget_limits.start_date = ? AND Budget_limits.end_date = ?
                    ORDER BY Categories.name
                """, (start_date, end_date))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Ошибка при получении бюджетных лимитов: {e}")
            return []

    def delete_budget_limit(self, limit_id: int):
        """ Удаление бюджетного лимита"""
        try:
            with self.connection() as conn:
                conn.execute("DELETE FROM Budget_limits WHERE id = ?", (limit_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при удалении лимита: {e}")
            return False


# Создаем один объект для работы с базой данных во всей программе
db_manager = DatabaseManager()