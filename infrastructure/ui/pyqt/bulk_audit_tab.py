from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class BulkAuditTab(QWidget):
    def __init__(self, bulk_audit_service, parent=None):
        super().__init__(parent)
        self.bulk_audit_service = bulk_audit_service # Store service for future use
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Bulk Audit Tab Content (Coming Soon)"))
        self.setLayout(layout)
