from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QTableWidget, QTableWidgetItem,
                             QPushButton, QHeaderView, QDialog, QLineEdit,
                             QMessageBox, QProgressBar, QFrame, QAbstractItemView)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QPainter
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
import db_methods


class BudgetTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_limit_id = None
        self.initUI()
        self.refresh_data()

    def initUI(self):
        main_layout = QVBoxLayout(self)

        # Выбор периода
        self.create_period_selector(main_layout)

        # Таблица бюджетных лимитов
        self.create_budget_table(main_layout)

        # Кнопки управления
        self.create_buttons_panel(main_layout)

        # График внизу
        self.create_bottom_panel(main_layout)

    def create_period_selector(self, layout):
        period_layout = QHBoxLayout()

        period_label = QLabel("Период:")
        period_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        period_layout.addWidget(period_label)

        self.period_combo = QComboBox()

        # Добавляем месяцы на год вперед и назад
        today = QDate.currentDate()
        for i in range(-12, 13):
            date = today.addMonths(i)
            month_name = date.toString("MMMM yyyy")
            month_value = date.toString("yyyy-MM-01")
            self.period_combo.addItem(month_name, month_value)

        # Устанавливаем текущий месяц
        current_month = today.toString("yyyy-MM-01")
        index = self.period_combo.findData(current_month)
        if index >= 0:
            self.period_combo.setCurrentIndex(index)

        self.period_combo.currentTextChanged.connect(self.refresh_data)
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()

        layout.addLayout(period_layout)

    def create_budget_table(self, layout):
        self.budget_table = QTableWidget()
        self.budget_table.setColumnCount(5)
        self.budget_table.setHorizontalHeaderLabels([
            "Категория", "Лимит", "Потрачено", "Остаток", "Прогресс"
        ])

        self.budget_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.budget_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.budget_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.budget_table.itemSelectionChanged.connect(self.on_row_selected)

        layout.addWidget(self.budget_table)

    def create_buttons_panel(self, layout):
        buttons_layout = QHBoxLayout()

        self.add_btn = QPushButton("+")
        self.add_btn.setStyleSheet("""
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold; """)
        self.add_btn.clicked.connect(self.show_add_dialog)
        buttons_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setStyleSheet("""
                background-color: #ffc107;
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold; """)
        self.edit_btn.clicked.connect(self.show_edit_dialog)
        buttons_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setStyleSheet("""
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold; """)
        self.delete_btn.clicked.connect(self.delete_limit)
        buttons_layout.addWidget(self.delete_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def create_bottom_panel(self, layout):
        bottom_layout = QHBoxLayout()

        chart_frame = QFrame()
        chart_layout = QVBoxLayout(chart_frame)

        chart_label = QLabel("Лимиты и расходы по ним")
        chart_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_layout.addWidget(chart_label)

        self.bar_chart_view = QChartView()
        self.bar_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.bar_chart_view.setMinimumSize(400, 300)
        chart_layout.addWidget(self.bar_chart_view)

        bottom_layout.addWidget(chart_frame)

        layout.addLayout(bottom_layout)

    def refresh_data(self):
        """ Обновление данных на вкладке """
        selected_month = self.period_combo.currentData()
        if not selected_month:
            return

        budget_limits = db_methods.db_manager.get_budget_limits(selected_month)

        self.budget_table.setRowCount(0)  # очищаем таблицу

        # Заполняем таблицу
        for row, limit in enumerate(budget_limits):
            self.budget_table.insertRow(row)
            # Категория
            category_item = QTableWidgetItem(limit.get('category_name', 'Неизвестно'))
            # Сохраняем ID лимита в первый элемент строки
            category_item.setData(Qt.ItemDataRole.UserRole, limit.get('id'))
            self.budget_table.setItem(row, 0, category_item)
            # Лимит
            limit_amount = limit.get('limit_amount', 0)
            limit_item = QTableWidgetItem(f"{limit_amount:.2f} ₽")
            self.budget_table.setItem(row, 1, limit_item)
            # Потрачено
            spent = limit.get('spent_amount', 0)
            spent_item = QTableWidgetItem(f"{spent:.2f} ₽")
            self.budget_table.setItem(row, 2, spent_item)
            # Остаток
            remaining = limit_amount - spent
            remaining_item = QTableWidgetItem(f"{remaining:.2f} ₽")
            if remaining < 0:
                remaining_item.setForeground(QColor("#dc3545"))  # Красный если превышен лимит
            self.budget_table.setItem(row, 3, remaining_item)
            # Прогресс-бар
            progress_widget = QWidget()
            progress_layout = QHBoxLayout(progress_widget)
            progress_bar = QProgressBar()

            # Считаем процент использования
            if limit_amount > 0:
                percent = min((spent / limit_amount) * 100, 100)
            else:
                percent = 100 if spent > 0 else 0

            progress_bar.setValue(int(percent))

            # Цвет прогресс-бара в зависимости от процента
            if percent < 70:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #28a745; }")
            elif percent < 90:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ffc107; }")
            else:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #dc3545; }")

            progress_layout.addWidget(progress_bar)
            progress_layout.setContentsMargins(2, 2, 2, 2)
            self.budget_table.setCellWidget(row, 4, progress_widget)

        # Обновляем график
        self.update_bar_chart(budget_limits)

    def update_bar_chart(self, budget_limits):
        """ Обновление графика лимитов и расходов """
        if not budget_limits:
            # Если нет данных
            chart = QChart()
            chart.setTitle("Нет установленных лимитов")
            self.bar_chart_view.setChart(chart)
            return

        # Наборы данных для столбцов
        limit_set = QBarSet("Лимит")
        limit_set.setColor(QColor("#495057"))

        spent_set = QBarSet("Потрачено")
        spent_set.setColor(QColor("#adb5bd"))

        categories = []

        # Заполняем данные
        for limit in budget_limits:
            limit_amount = limit.get('limit_amount', 0)
            spent_amount = limit.get('spent_amount', 0)
            category_name = limit.get('category_name', 'Неизвестно')

            limit_set.append(limit_amount)
            spent_set.append(spent_amount)
            categories.append(category_name)

        # Создаем серию столбцов
        series = QBarSeries()
        series.append(limit_set)
        series.append(spent_set)

        # Создаем и настраиваем график
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        # Настраиваем оси
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Рубли")
        axis_y.setLabelFormat("%.0f")
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        # Настраиваем легенду
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.bar_chart_view.setChart(chart)

    def on_row_selected(self):
        """ Обработка выбора строки в таблице """
        selected_items = self.budget_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            # Получаем ID лимита из первого элемента строки
            category_item = self.budget_table.item(row, 0)
            if category_item:
                self.selected_limit_id = category_item.data(Qt.ItemDataRole.UserRole)
                self.edit_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
        else:
            self.selected_limit_id = None
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def show_add_dialog(self):
        """ Диалог добавления лимита """
        selected_month = self.period_combo.currentData()
        dialog = BudgetLimitDialog(self, selected_month)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()

    def show_edit_dialog(self):
        """ Диалог редактирования лимита """
        if not self.selected_limit_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите лимит для редактирования')
            return

        selected_month = self.period_combo.currentData()

        # Находим данные выбранного лимита
        budget_limits = db_methods.db_manager.get_budget_limits(selected_month)
        limit_data = None
        for limit in budget_limits:
            if limit.get('id') == self.selected_limit_id:
                limit_data = limit
                break

        if limit_data:
            dialog = BudgetLimitDialog(self, selected_month, limit_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_data()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось найти данные лимита')

    def delete_limit(self):
        """ Удаление лимита """
        if not self.selected_limit_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите лимит для удаления')
            return

        # Спрашиваем подтверждение
        reply = QMessageBox.question(self, 'Подтверждение удаления',
                                     'Вы уверены, что хотите удалить этот лимит?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success = db_methods.db_manager.delete_budget_limit(self.selected_limit_id)
            if success:
                QMessageBox.information(self, 'Успех', 'Лимит удален')
                self.selected_limit_id = None
                self.refresh_data()
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось удалить лимит')


class BudgetLimitDialog(QDialog):
    """ Диалоговое окно для добавления/редактирования бюджетного лимита """
    def __init__(self, parent=None, month_year=None, limit_data=None):
        super().__init__(parent)
        self.month_year = month_year
        self.limit_data = limit_data
        self.setModal(True)

        if not limit_data:
            self.setWindowTitle("Добавить лимит")
        else:
            self.setWindowTitle("Редактировать лимит")

        self.initUI()
        self.load_limit_data()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Выбор категории
        category_layout = QHBoxLayout()
        category_label = QLabel("Категория:")
        self.category_combo = QComboBox()

        # Заполняем только категории расходов
        categories = db_methods.db_manager.get_categories('expense')
        print(f"Загружено категорий: {len(categories)}")
        for category in categories:
            self.category_combo.addItem(category['name'], category['id'])

        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)

        # Поле ввода лимита
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Лимит:")
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_edit)
        layout.addLayout(amount_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()

        cancel_btn = QPushButton("Отменить")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        action_btn = QPushButton("Добавить" if not self.limit_data else "Изменить")
        action_btn.clicked.connect(self.save_limit)
        buttons_layout.addWidget(action_btn)

        layout.addLayout(buttons_layout)

    def load_limit_data(self):
        """ Заполняем поля для редактирования """
        if not self.limit_data:
            return

        # Устанавливаем категорию
        category_id = self.limit_data.get('category_id')
        if category_id:
            index = self.category_combo.findData(category_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            else:
                print(f"Категория с ID {category_id} не найдена в комбобоксе")

        # Устанавливаем сумму лимита
        limit_amount = self.limit_data.get('limit_amount')
        if limit_amount is not None:
            self.amount_edit.setText(f"{limit_amount:.2f}")

    def save_limit(self):
        """ Сохраняем лимит в БД """
        category_id = self.category_combo.currentData()
        amount_text = self.amount_edit.text().strip()

        # Проверяем сумму
        try:
            amount = float(amount_text)
            if amount <= 0:
                QMessageBox.warning(self, 'Ошибка', 'Лимит должен быть больше 0')
                return
        except ValueError:
            QMessageBox.warning(self, 'Ошибка', 'Введите корректную сумму')
            return

        # Проверяем категорию
        if not category_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите категорию')
            return

        # Сохраняем в базу данных
        if not self.limit_data:
            success = db_methods.db_manager.add_budget_limit(
                category_id, amount, self.month_year)
        else:
            if hasattr(db_methods.db_manager, 'update_budget_limit'):
                success = db_methods.db_manager.update_budget_limit(
                        self.limit_data['id'], category_id, amount, self.month_year)
            else:
                db_methods.db_manager.delete_budget_limit(self.limit_data['id'])
                success = db_methods.db_manager.add_budget_limit(
                    category_id, amount, self.month_year)

        if success:
            self.accept()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось сохранить лимит')