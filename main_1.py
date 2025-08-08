import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QPushButton, QFileDialog, QScrollArea, QComboBox, QSpinBox
)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QBrush, QColor

sys.stdout.reconfigure(encoding='utf-8')

"""
Этот код реализует редактор для просмотра изображений, и json нотификаций для них
"""

class ImageJsonViewer(QWidget):
    def __init__(self, folder):
        super().__init__()
        self.folder = folder
        self.images = [f for f in os.listdir(folder) if f.endswith(".png_st")]
        self.current_image = None
        self.json_data = {}

        self.setWindowTitle("Image + JSON Viewer")
        self.resize(1200, 800)

        # --- Убираем системные нав элементы ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # убирает стандартную рамку окна
            Qt.WindowType.Window  # обычное окно без рамок
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # прозрачный фон окна

        # --- Свой фон для всего окна (в PaintEvent мы также рисуем фон) ---
        self.setStyleSheet("""
            QWidget { background-color: #000000; color: #FFFFFF; }
            QLabel { color: #FFFFFF; }
            QLineEdit, QComboBox, QSpinBox, QListWidget, QTextEdit {
                background-color: #1e1e1e;
                color: #FFFFFF;
                border: 1px solid #2e2e2e;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton {
                background-color: transparent;
                color: #FFFFFF;
                border: 1px solid #2e2e2e;
                padding: 6px 10px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.03); }
            QListWidget { background-color: transparent; }
            QListWidget::item { color: #FFFFFF; }
            QListWidget::item:selected { background-color: #303030; }
            QScrollArea { background-color: transparent; }
        """)

        # --- Создаём собственную шапку окна с кнопкой закрытия ---
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("""
            background-color: rgba(30, 30, 30, 240);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        # Заголовок в шапке
        self.title_label = QLabel("Image + JSON Viewer", self.title_bar)
        self.title_label.setStyleSheet("color: white; font-weight: bold;")
        title_layout.addWidget(self.title_label)

        # Спейсер, чтобы кнопка была справа
        title_layout.addStretch()

        # Кнопка закрытия окна
        self.close_button = QPushButton("✖", self.title_bar)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: red;
            }
        """)
        self.close_button.clicked.connect(self.close)
        title_layout.addWidget(self.close_button)

        # --- Главное расположение без учёта системного заголовка ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.main_layout.addWidget(self.title_bar)

        # Основной виджет с содержимым — обернём в QWidget для удобства стилей и управления
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)

        # Верхняя часть (изображение + JSON-редактор)
        top_layout = QHBoxLayout()

        # Центр: изображение
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(800, 600)
        self.image_label.setStyleSheet("background-color: black; border-radius: 8px;")

        # Справа: редактор JSON
        self.form_layout = QFormLayout()
        self.form_widget = QWidget()
        self.form_widget.setLayout(self.form_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.form_widget)

        top_layout.addWidget(self.image_label, 3)
        top_layout.addWidget(scroll, 2)

        # Нижняя панель — список изображений
        self.image_list = QListWidget()
        self.image_list.setFixedHeight(100)
        self.image_list.itemClicked.connect(self.on_image_selected)

        for img in self.images:
            self.image_list.addItem(QListWidgetItem(img))

        # Кнопка сохранить
        save_button = QPushButton("💾 Сохранить JSON")
        save_button.setFixedHeight(40)
        save_button.clicked.connect(self.save_json)

        self.content_layout.addLayout(top_layout)
        self.content_layout.addWidget(self.image_list)
        self.content_layout.addWidget(save_button)

        self.main_layout.addWidget(self.content_widget)

        if self.images:
            self.load_image(self.images[0])

        # Для перетаскивания окна мышью по шапке
        self.offset = None

    # Перетаскивание окна за шапку
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.title_bar.geometry().contains(event.pos()):
                self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.offset is not None:
            self.move(self.pos() + event.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.offset = None

    def load_image(self, filename):
        self.current_image = filename
        img_path = os.path.join(self.folder, filename)
        pixmap = QPixmap(img_path)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

        # Загружаем JSON
        json_path = os.path.splitext(img_path)[0] + ".json"
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
        else:
            self.json_data = {}

        # Перерисовываем форму
        self.update_form()

    def update_form(self):
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for key, value in self.json_data.items():
            if isinstance(value, str):
                field = QLineEdit(value)
            elif isinstance(value, int):
                field = QSpinBox()
                field.setValue(value)
            elif isinstance(value, float):
                field = QLineEdit(str(value))  # можно заменить на QDoubleSpinBox
            elif isinstance(value, list):
                field = QComboBox()
                for item in value:
                    field.addItem(str(item))
            else:
                field = QLineEdit(str(value))

            field.setObjectName(key)
            # Дополнительная настройка полей — чтобы гарантировать белый текст на тёмном фоне
            field.setStyleSheet("")
            self.form_layout.addRow(QLabel(key), field)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        # Фон — чёрный с прозрачностью и скруглённые углы
        color = QColor(0, 0, 0, 220)  # чёрный с прозрачностью
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 10, 10)  # радиус скругления 10

    def save_json(self):
        for i in range(self.form_layout.count()):
            # form_layout stores rows as (label, field) pairs; .itemAt(i) returns a QLayoutItem
            item = self.form_layout.itemAt(i).widget()
            if isinstance(item, QLineEdit):
                self.json_data[item.objectName()] = item.text()
            elif isinstance(item, QSpinBox):
                self.json_data[item.objectName()] = item.value()
            elif isinstance(item, QComboBox):
                self.json_data[item.objectName()] = item.currentText()

        json_path = os.path.join(self.folder, os.path.splitext(self.current_image)[0] + ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.json_data, f, ensure_ascii=False, indent=4)
        print(f"JSON сохранён: {json_path}")

    def on_image_selected(self, item):
        self.load_image(item.text())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Глобальная тёмная тема для приложения: фон — чёрный, весь текст — белый,
    # поля ввода и списки — тёмно-серые для удобства чтения.
    app.setStyleSheet("""
        QWidget { background-color: #000000; color: #FFFFFF; }
        QLabel { color: #FFFFFF; }
        QLineEdit, QComboBox, QSpinBox, QListWidget, QTextEdit {
            background-color: #1e1e1e;
            color: #FFFFFF;
            border: 1px solid #2e2e2e;
            border-radius: 6px;
            padding: 4px;
        }
        QPushButton {
            background-color: transparent;
            color: #FFFFFF;
            border: 1px solid #2e2e2e;
            padding: 6px 10px;
            border-radius: 6px;
        }
        QPushButton:hover { background-color: rgba(255,255,255,0.03); }
        QListWidget { background-color: transparent; }
        QListWidget::item { color: #FFFFFF; }
        QListWidget::item:selected { background-color: #303030; }
        QScrollArea { background-color: transparent; }
    """)

    folder = QFileDialog.getExistingDirectory(None, "Выбери папку с изображениями и JSON")
    if folder:
        viewer = ImageJsonViewer(folder)
        viewer.show()
        sys.exit(app.exec())
