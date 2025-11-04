from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QHeaderView, QDialog,
                             QLabel, QComboBox, QLineEdit, QDateEdit, QMessageBox,
                             QToolButton, QAbstractItemView)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
import db_methods


class OperationsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # ссылка на главное окно
        self.selected_operation_id = None  # ID выбранной операции для редактирования
        self.initUI()
        self.refresh_data()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Панель с кнопками
        self.create_toolbar(layout)

        # Таблица с операциями
        self.create_operations_table(layout)

        # Панель фильтрации
        self.create_filter_panel(layout)

    def create_toolbar(self, layout):
        toolbar_layout = QHBoxLayout()

        self.add_btn = QToolButton()
        self.add_btn.setText("+")
        self.add_btn.setToolTip("Добавить операцию")
        self.add_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.add_btn.setStyleSheet("""
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 40px;
                min-height: 40px; """)
        self.add_btn.clicked.connect(self.show_add_dialog)
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QToolButton()
        self.edit_btn.setText("✏️")
        self.edit_btn.setToolTip("Изменить операцию")
        self.edit_btn.setFont(QFont("Arial", 12))
        self.edit_btn.setStyleSheet("""
                background-color: #ffc107;
                color: black;
                border: none;
                border-radius: 8px;
                min-width: 40px;
                min-height: 40px; """)
        self.edit_btn.clicked.connect(self.show_edit_dialog)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QToolButton()
        self.delete_btn.setText("🗑️")
        self.delete_btn.setToolTip("Удалить операцию")
        self.delete_btn.setFont(QFont("Arial", 12))
        self.delete_btn.setStyleSheet("""
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 40px;
                min-height: 40px; """)
        self.delete_btn.clicked.connect(self.delete_operation)
        toolbar_layout.addWidget(self.delete_btn)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

    def create_operations_table(self, layout):
        self.operations_table = QTableWidget()
        self.operations_table.setColumnCount(5)  # 5 колонок
        self.operations_table.setHorizontalHeaderLabels([
            "Дата", "Категория", "Описание", "Сумма", "Тип"
        ])

        self.operations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.operations_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.operations_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Обработчик выбора строки
        self.operations_table.itemSelectionChanged.connect(self.on_row_selected)

        layout.addWidget(self.operations_table)

    def create_filter_panel(self, layout):
        filter_layout = QHBoxLayout()

        filter_label = QLabel("Фильтр:")
        filter_layout.addWidget(filter_label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Все операции", "Только доходы", "Только расходы"])
        self.filter_combo.currentTextChanged.connect(self.refresh_data)
        filter_layout.addWidget(self.filter_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

    def refresh_data(self):
        """ Обновление данных в таблице """
        filter_text = self.filter_combo.currentText()
        filter_type = "all"

        if filter_text == "Только доходы":
            filter_type = "income"
        elif filter_text == "Только расходы":
            filter_type = "expense"

        operations = db_methods.db_manager.get_all_operations(filter_type)
        self.operations_table.setRowCount(0)  # очищаем таблицу

        # Заполняем таблицу данными
        for row, operation in enumerate(operations):
            self.operations_table.insertRow(row)
            # Дата
            self.operations_table.setItem(row, 0, QTableWidgetItem(operation['date']))
            # Категория
            self.operations_table.setItem(row, 1, QTableWidgetItem(operation['category_name']))
            # Описание
            description = operation['description'] or ""
            self.operations_table.setItem(row, 2, QTableWidgetItem(description))
            # Сумма
            amount_item = QTableWidgetItem(f"{operation['amount']:.2f} ₽")
            self.operations_table.setItem(row, 3, amount_item)
            # Тип операции
            type_text = "Доход" if operation['category_type'] == 'income' else "Расход"
            type_item = QTableWidgetItem(type_text)

            if operation['category_type'] == 'income':
                type_item.setForeground(Qt.GlobalColor.green)
            else:
                type_item.setForeground(Qt.GlobalColor.red)

            self.operations_table.setItem(row, 4, type_item)

            # Сохраняем ID операции в ячейке (скрыто от пользователя)
            self.operations_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, operation['id'])

    def on_row_selected(self):
        """ Обработка выбора строки в таблице """
        selected_items = self.operations_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            # Достаем ID операции из скрытых данных
            self.selected_operation_id = self.operations_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            # Активируем кнопки редактирования и удаления
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def show_add_dialog(self):
        """ Диалог добавления операции """
        try:
            dialog = OperationDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_data()
                if self.parent:
                    self.parent.notify_data_updated()  # сообщаем главному окну об обновлении
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть диалог: {str(e)}')

    def show_edit_dialog(self):
        """ Диалог редактирования операции """
        if not self.selected_operation_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите операцию для редактирования')
            return

        # Находим операцию для редактирования
        operations = db_methods.db_manager.get_all_operations("all")
        operation = None
        for t in operations:
            if t['id'] == self.selected_operation_id:
                operation = t
                break

        if operation:
            dialog = OperationDialog(self, operation)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_data()
                if self.parent:
                    self.parent.notify_data_updated()

    def delete_operation(self):
        """ Удаление операции """
        if not self.selected_operation_id:
            QMessageBox.warning(self, 'Ошибка', 'Выберите операцию для удаления')
            return
        reply = QMessageBox.question(self, 'Подтверждение удаления',
                                     'Вы уверены, что хотите удалить эту операцию?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = db_methods.db_manager.delete_operation(self.selected_operation_id)
                if success:
                    QMessageBox.information(self, 'Успех', 'Операция удалена')
                    self.refresh_data()
                    if self.parent:
                        self.parent.notify_data_updated()
                else:
                    QMessageBox.warning(self, 'Ошибка', 'Не удалось удалить операцию')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при удалении: {str(e)}')


class OperationDialog(QDialog):
    """ Диалоговое окно для добавления/редактирования операции """
    def __init__(self, parent=None, operation=None):
        super().__init__(parent)
        self.operation = operation
        self.setModal(True)  # делаем окно модальным (блокирует главное окно)

        if not operation:
            self.setWindowTitle("Добавить операцию")
        else:
            self.setWindowTitle("Редактировать операцию")

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Поле для даты
        date_layout = QHBoxLayout()
        date_label = QLabel("Дата:")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)  # всплывающий календарь
        self.date_edit.setDate(QDate.currentDate())  # сегодняшняя дата по умолчанию
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)

        # Поле выбора категории
        category_layout = QHBoxLayout()
        category_label = QLabel("Категория:")
        self.category_combo = QComboBox()

        categories = db_methods.db_manager.get_categories()
        for category in categories:
            self.category_combo.addItem(category['name'], category['id'])

        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)

        # Поле описания
        description_layout = QHBoxLayout()
        description_label = QLabel("Описание:")
        self.description_edit = QLineEdit()
        description_layout.addWidget(description_label)
        description_layout.addWidget(self.description_edit)
        layout.addLayout(description_layout)

        # Поле суммы
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Сумма:")
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_edit)
        layout.addLayout(amount_layout)

        # Кнопки
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Отменить")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        action_btn = QPushButton("Добавить" if not self.operation else "Изменить")
        action_btn.clicked.connect(self.save_operation)
        button_layout.addWidget(action_btn)

        layout.addLayout(button_layout)

    def load_operation_data(self):
        """ Заполняем поля для редактирования """
        if not self.operation:
            return
        try:
            # Дата
            operation_date = QDate.fromString(self.operation['date'], Qt.DateFormat.ISODate)
            self.date_edit.setDate(operation_date)
            # Категория
            index = self.category_combo.findData(self.operation['category_id'])
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            # Описание
            self.description_edit.setText(self.operation['description'] or "")
            # Сумма
            self.amount_edit.setText(f"{self.operation['amount']:.2f}")
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить данные операции: {str(e)}')

    def save_operation(self):
        """ Сохранение операции в БД """
        try:
            # Получаем данные из полей
            date = self.date_edit.date().toString(Qt.DateFormat.ISODate)
            category_id = self.category_combo.currentData()
            description = self.description_edit.text().strip()
            amount_text = self.amount_edit.text().strip()

            # Проверяем сумму
            try:
                amount = float(amount_text)
                if amount <= 0:
                    QMessageBox.warning(self, 'Ошибка', 'Сумма должна быть больше 0')
                    return
            except ValueError:
                QMessageBox.warning(self, 'Ошибка', 'Введите корректную сумму')
                return

            # Проверяем категорию
            if not category_id:
                QMessageBox.warning(self, 'Ошибка', 'Выберите категорию')
                return

            # Сохраняем в базу данных
            if not self.operation:
                success = db_methods.db_manager.add_operation(
                    amount, category_id, date, description
                )
            else:
                # Для редактирования нужно сначала удалить старую операцию и создать новую
                db_methods.db_manager.delete_operation(self.operation['id'])
                success = db_methods.db_manager.add_operation(
                    amount, category_id, date, description
                )

            if success:
                self.accept()  # Закрываем диалог с успехом
            else:
                QMessageBox.warning(self, 'Ошибка', 'Не удалось сохранить операцию')

        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка: {str(e)}')