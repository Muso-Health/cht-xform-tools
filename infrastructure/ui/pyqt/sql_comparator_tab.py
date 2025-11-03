from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SQLComparatorTab(QWidget):
    def __init__(self, comparator_service, parent=None):
        super().__init__(parent)
        self.comparator_service = comparator_service # Store service for future use
        layout = QVBoxLayout()
        layout.addWidget(QLabel("XLSForm SQL Comparator Tab Content (Coming Soon)"))
        self.setLayout(layout)
