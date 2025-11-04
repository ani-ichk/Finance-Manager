from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QStackedWidget, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from operations_tab import OperationsTab
from analytics_tab import AnalyticsTab
from budget_tab import BudgetTab
import db_methods
from datetime import date


class MainWindow(QMainWindow):
    data_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.initUI()

        # Подключаем сигнал ко всем вкладкам, чтобы они обновлялись при изменении данных
        self.data_updated.connect(self.update_balance_display)
        self.data_updated.connect(self.operations_tab.refresh_data)
        self.data_updated.connect(self.analytics_tab.refresh_data)
        self.data_updated.connect(self.budget_tab.refresh_data)

    def initUI(self):
        self.setWindowTitle("Финансовый менеджер")
        self.setGeometry(100, 100, 1000, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # левая панель с балансом и кнопками
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # правая панель с вкладками
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 3)

    def create_left_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                border: 2px solid #dee2e6;
            }
        """)

        layout = QVBoxLayout(panel)

        balance_label = QLabel("ТЕКУЩИЙ БАЛАНС")
        balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        balance_label.setFont(QFont("Segoe UI Black", 16, QFont.Weight.Bold))
        layout.addWidget(balance_label)

        # Сумма баланса
        self.balance_amount = QLabel("0.0 ₽")
        self.balance_amount.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.balance_amount.setFont(QFont("Segoe UI Black", 24, QFont.Weight.Bold))
        self.balance_amount.setStyleSheet("color: #28a745;")
        layout.addWidget(self.balance_amount)

        # Доходы
        income_layout = QHBoxLayout()
        income_label = QLabel("Доход:")
        income_label.setFont(QFont("Segoe UI Black", 12))
        self.income_amount = QLabel("0.0 ₽")
        self.income_amount.setFont(QFont("Segoe UI Black", 12, QFont.Weight.Bold))
        self.income_amount.setStyleSheet("color: #28a745;")
        income_layout.addWidget(income_label)
        income_layout.addWidget(self.income_amount)
        layout.addLayout(income_layout)

        # Расходы
        expense_layout = QHBoxLayout()
        expense_label = QLabel("Расход:")
        expense_label.setFont(QFont("Segoe UI Black", 12))
        self.expense_amount = QLabel("0.0 ₽")
        self.expense_amount.setFont(QFont("Segoe UI Black", 12, QFont.Weight.Bold))
        self.expense_amount.setStyleSheet("color: #dc3545;")
        expense_layout.addWidget(expense_label)
        expense_layout.addWidget(self.expense_amount)
        layout.addLayout(expense_layout)

        # Кнопки для переключения между вкладками
        self.create_tab_buttons(layout)
        layout.addStretch()

        self.update_balance_display()  # показываем текущий баланс

        return panel

    def create_tab_buttons(self, layout):
        self.operations_btn = QPushButton("Операции")
        self.operations_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.operations_btn.setStyleSheet("""
                background-color: #00557f;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                margin: 5px; """)
        self.operations_btn.clicked.connect(lambda: self.switch_tab(0))

        self.analytics_btn = QPushButton("Аналитика")
        self.analytics_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.analytics_btn.setStyleSheet("""
                background-color: #58839a;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                margin: 5px; """)
        self.analytics_btn.clicked.connect(lambda: self.switch_tab(1))

        self.budget_btn = QPushButton("Бюджет")
        self.budget_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.budget_btn.setStyleSheet("""
                background-color: #81858f;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 8px;
                margin: 5px; """)
        self.budget_btn.clicked.connect(lambda: self.switch_tab(2))

        layout.addWidget(self.operations_btn)
        layout.addWidget(self.analytics_btn)
        layout.addWidget(self.budget_btn)

    def create_right_panel(self):
        panel = QFrame()
        layout = QVBoxLayout(panel)

        self.stacked_widget = QStackedWidget()

        self.operations_tab = OperationsTab(self)
        self.analytics_tab = AnalyticsTab(self)
        self.budget_tab = BudgetTab(self)

        self.stacked_widget.addWidget(self.operations_tab)
        self.stacked_widget.addWidget(self.analytics_tab)
        self.stacked_widget.addWidget(self.budget_tab)

        layout.addWidget(self.stacked_widget)

        return panel

    def switch_tab(self, index):
        """ Изменение цветов кнопок при переключении на другую вкладку """
        self.stacked_widget.setCurrentIndex(index)

        # Сначала сбрасываем все кнопки к обычному состоянию
        self.operations_btn.setStyleSheet(
            self.operations_btn.styleSheet().replace("background-color: #0e294b;", "background-color: #00557f;"))
        self.analytics_btn.setStyleSheet(
            self.analytics_btn.styleSheet().replace("background-color: #0f6674;", "background-color: #58839a;"))
        self.budget_btn.setStyleSheet(
            self.budget_btn.styleSheet().replace("background-color: #3d4348", "background-color: #81858f;"))

        # Затем выделяем активную кнопку
        if index == 0:
            self.operations_btn.setStyleSheet("""
                    background-color: #0e294b; 
                    color: white; 
                    border: none; 
                    padding: 12px; 
                    border-radius: 8px; 
                    margin: 5px; """)
        elif index == 1:
            self.analytics_btn.setStyleSheet("""
                    background-color: #0f6674;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    margin: 5px; """)
        elif index == 2:
            self.budget_btn.setStyleSheet("""
                    background-color: #3d4348;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    margin: 5px; """)

    def update_balance_display(self):
        """ Обновляем отображение баланса """
        today = date.today()
        first_day = today.replace(day=1)  # первый день текущего месяца

        # Получаем статистику за текущий месяц
        summary = db_methods.db_manager.get_financial_summary(
            first_day.isoformat(),
            today.isoformat()
        )

        # Обновляем отображаемые значения
        self.balance_amount.setText(f"{summary['balance']:.2f} ₽")
        self.income_amount.setText(f"{summary['income']:.2f} ₽")
        self.expense_amount.setText(f"{summary['expense']:.2f} ₽")

        # Меняем цвет в зависимости от того положительный баланс или отрицательный
        if summary['balance'] >= 0:
            self.balance_amount.setStyleSheet("color: #28a745;")
        else:
            self.balance_amount.setStyleSheet("color: #dc3545;")

    def notify_data_updated(self):
        """ Отправляем сигнал, что данные обновились """
        self.data_updated.emit()  # отправляем сигнал об обновлении данных