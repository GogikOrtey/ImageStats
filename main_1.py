import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QPushButton, QFileDialog, QScrollArea, QComboBox, QSpinBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ImageJsonViewer(QWidget):
    def __init__(self, folder):
        super().__init__()
        self.folder = folder
        self.images = [f for f in os.listdir(folder) if f.endswith(".png_st")]
        self.current_image = None
        self.json_data = {}

        self.setWindowTitle("Image + JSON Viewer")
        self.resize(1200, 800)

        # --- Главное расположение ---
        main_layout = QVBoxLayout(self)

        # Верхняя часть (изображение + JSON-редактор)
        top_layout = QHBoxLayout()

        # Центр: изображение
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(800, 600)

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
        save_button.clicked.connect(self.save_json)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.image_list)
        main_layout.addWidget(save_button)

        if self.images:
            self.load_image(self.images[0])

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
        # Удаляем старые поля
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Создаем новые поля
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
            self.form_layout.addRow(key, field)

    def save_json(self):
        for i in range(self.form_layout.count()):
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

    folder = QFileDialog.getExistingDirectory(None, "Выбери папку с изображениями и JSON")
    if folder:
        viewer = ImageJsonViewer(folder)
        viewer.show()
        sys.exit(app.exec())
