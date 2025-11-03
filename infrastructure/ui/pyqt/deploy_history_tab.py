from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class DeployHistoryTab(QWidget):
    def __init__(self, cicd_repository, parent=None):
        super().__init__(parent)
        self.cicd_repository = cicd_repository # Store service for future use
        layout = QVBoxLayout()
        layout.addWidget(QLabel("XLSForm Deploy History Tab Content (Coming Soon)"))
        self.setLayout(layout)
