from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QDateEdit, QFrame)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
import db_methods
from datetime import datetime


class AnalyticsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        # Не обновляем данные сразу, ждем пока интерфейс создастся
        QTimer.singleShot(100, self.refresh_data)

    def initUI(self):
        main_layout = QHBoxLayout(self)

        # Левая панель с настройками
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # Правая панель с графиками
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 3)

    def create_left_panel(self):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                border: 2px solid #dee2e6;
                margin: 5px;
            }
        """)

        layout = QVBoxLayout(panel)

        period_label = QLabel("Период")
        period_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(period_label)

        # Выбор типа периода
        period_type_layout = QHBoxLayout()
        period_type_label = QLabel("Тип:")
        self.period_type_combo = QComboBox()
        self.period_type_combo.addItems(["За месяц", "За год"])
        self.period_type_combo.currentTextChanged.connect(self.on_period_type_changed)
        period_type_layout.addWidget(period_type_label)
        period_type_layout.addWidget(self.period_type_combo)
        period_type_layout.addStretch()
        layout.addLayout(period_type_layout)

        start_layout = QHBoxLayout()
        start_label = QLabel("с:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.dateChanged.connect(self.on_dates_changed)
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_date_edit)
        start_layout.addStretch()
        layout.addLayout(start_layout)

        end_layout = QHBoxLayout()
        end_label = QLabel("по:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.dateChanged.connect(self.on_dates_changed)
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_date_edit)
        end_layout.addStretch()
        layout.addLayout(end_layout)

        layout.addStretch()

        return panel

    def create_right_panel(self):
        panel = QFrame()
        layout = QVBoxLayout(panel)

        # График доходов и расходов
        chart_label = QLabel("Доходы и расходы по периодам")
        chart_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(chart_label)

        self.bar_chart_view = QChartView()
        layout.addWidget(self.bar_chart_view, 2)

        # Круговая диаграмма расходов
        pie_chart_label = QLabel("Распределение расходов")
        pie_chart_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        pie_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(pie_chart_label)

        pie_layout = QHBoxLayout()

        # Круговая диаграмма
        self.pie_chart_view = QChartView()
        self.pie_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.pie_chart_view.setMinimumSize(300, 300)
        pie_layout.addWidget(self.pie_chart_view)

        # Легенда справа
        self.categories_legend = QFrame()
        self.categories_legend.setMaximumWidth(200)
        pie_layout.addWidget(self.categories_legend)

        layout.addLayout(pie_layout, 1)

        return panel

    def on_period_type_changed(self):
        """ Обработка изменения типа периода """
        try:
            today = QDate.currentDate()
            if self.period_type_combo.currentText() == "За месяц":
                # Устанавливаем начало месяца
                start_date = today.addDays(1 - today.day())
                self.start_date_edit.setDate(start_date)
                self.end_date_edit.setDate(today)
            else:  # За год
                # Устанавливаем начало года
                start_date = QDate(today.year(), 1, 1)
                self.start_date_edit.setDate(start_date)
                self.end_date_edit.setDate(today)

            self.refresh_data()
        except Exception as e:
            print(f"Ошибка при изменении типа периода: {e}")

    def on_dates_changed(self):
        """ Обработка изменения дат """
        try:
            # Проверяем чтобы начальная дата не была больше конечной
            start_date = self.start_date_edit.date()
            end_date = self.end_date_edit.date()

            if start_date > end_date:
                self.start_date_edit.setDate(end_date)
                self.end_date_edit.setDate(start_date)
            else:
                self.refresh_data()
        except Exception as e:
            print(f"Ошибка при изменении дат: {e}")

    def refresh_data(self):
        """ Обновление данных на вкладке """
        try:
            start_date = self.start_date_edit.date().toString(Qt.DateFormat.ISODate)
            end_date = self.end_date_edit.date().toString(Qt.DateFormat.ISODate)
            self.update_bar_chart(start_date, end_date)
            self.update_pie_chart(start_date, end_date)
        except Exception as e:
            print(f"Ошибка при обновлении аналитики: {e}")

    def update_bar_chart(self, start_date, end_date):
        """ Обновление графика доходов/расходов """
        try:
            # Определяем как группировать данные
            if self.period_type_combo.currentText() == "За месяц":
                group_by = 'day'
            else:
                group_by = 'month'

            # Получаем данные для графика
            chart_data = db_methods.db_manager.get_income_expense_by_period(start_date, end_date, group_by)

            if not chart_data:
                # Если нет данных - показываем сообщение
                chart = QChart()
                chart.setTitle("Нет данных за выбранный период")
                self.bar_chart_view.setChart(chart)
                return

            # Создаем наборы данных для столбцов
            income_set = QBarSet("Доходы")
            income_set.setColor(QColor("#28a745"))

            expense_set = QBarSet("Расходы")
            expense_set.setColor(QColor("#dc3545"))

            categories = []

            # Заполняем данные
            for data in chart_data:
                income_set.append(data['income'])
                expense_set.append(data['expense'])

                if group_by == 'day':
                    # Форматируем дату для отображения
                    date_obj = datetime.strptime(data['period'], '%Y-%m-%d')
                    categories.append(date_obj.strftime('%d.%m'))
                else:
                    # Форматируем месяц для отображения
                    date_obj = datetime.strptime(data['period'], '%Y-%m')
                    categories.append(date_obj.strftime('%b %Y'))

            # Создаем серию столбцов
            series = QBarSeries()
            series.append(income_set)
            series.append(expense_set)

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
            axis_y.setLabelFormat("%.0f")
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_y)

            # Настраиваем легенду
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

            self.bar_chart_view.setChart(chart)
        except Exception as e:
            print(f"Ошибка при обновлении столбчатого графика: {e}")
            chart = QChart()
            chart.setTitle("Ошибка при загрузке данных")
            self.bar_chart_view.setChart(chart)

    def update_pie_chart(self, start_date, end_date):
        """ Обновление круговой диаграммы расходов"""
        try:
            # Получаем статистику расходов по категориям
            expense_stats = db_methods.db_manager.get_expense_statistics(start_date, end_date)

            if not expense_stats:
                # Если нет данных
                chart = QChart()
                chart.setTitle("Нет данных о расходах за выбранный период")
                self.pie_chart_view.setChart(chart)
                self.update_legend([])
                return

            # Создаем серию для круговой диаграммы
            series = QPieSeries()
            series.setHoleSize(0.0)

            # Цвета для категорий
            colors = [
                QColor("#ff6b6b"), QColor("#4ecdc4"), QColor("#45b7d1"),
                QColor("#96ceb4"), QColor("#feca57"), QColor("#ff9ff3"),
                QColor("#54a0ff"), QColor("#5f27cd"), QColor("#00d2d3")
            ]

            # Добавляем секции в диаграмму
            for i, stat in enumerate(expense_stats):
                slice = series.append(stat['name'], stat['total'])
                slice.setColor(colors[i % len(colors)])
                slice.setLabelVisible(False)  # убираем подписи на самой диаграмме

            # Создаем и настраиваем график
            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("")
            chart.legend().setVisible(False)

            self.pie_chart_view.setChart(chart)
            self.update_legend(expense_stats)
        except Exception as e:
            print(f"Ошибка при обновлении круговой диаграммы: {e}")
            chart = QChart()
            chart.setTitle("Ошибка при загрузке данных")
            self.pie_chart_view.setChart(chart)

    def update_legend(self, expense_stats):
        """ Обновление легенды категорий """
        try:
            # Очищаем старую легенду
            layout = self.categories_legend.layout()
            if layout:
                for i in reversed(range(layout.count())):
                    item = layout.itemAt(i)
                    if item.widget():
                        item.widget().setParent(None)
            else:
                layout = QVBoxLayout(self.categories_legend)

            if not expense_stats:
                no_data_label = QLabel("Нет данных")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(no_data_label)
                return

            # Находим категорию с самыми большими расходами
            max_expense = max(expense_stats, key=lambda x: x['total'])

            # Цвета для категорий
            colors = [
                QColor("#ff6b6b"), QColor("#4ecdc4"), QColor("#45b7d1"),
                QColor("#96ceb4"), QColor("#feca57"), QColor("#ff9ff3"),
                QColor("#54a0ff"), QColor("#5f27cd"), QColor("#00d2d3")
            ]

            # Добавляем элементы легенды
            for i, stat in enumerate(expense_stats):
                item_layout = QHBoxLayout()

                # Цветная точка
                color_label = QLabel("●")
                color_label.setStyleSheet(f"color: {colors[i % len(colors)].name()}; font-size: 20px;")

                # Название категории и сумма
                name_label = QLabel(f"{stat['name']}: {stat['total']:.2f} ₽")

                # Выделяем самую затратную категорию жирным шрифтом
                if stat['name'] == max_expense['name']:
                    name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                    name_label.setStyleSheet("color: #dc3545;")
                else:
                    name_label.setFont(QFont("Arial", 9))

                item_layout.addWidget(color_label)
                item_layout.addWidget(name_label)
                item_layout.addStretch()

                layout.addLayout(item_layout)

            layout.addStretch()
        except Exception as e:
            print(f"Ошибка при обновлении легенды: {e}")