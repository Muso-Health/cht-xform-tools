import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QComboBox, QTextEdit, QApplication, QMessageBox)
from PyQt6.QtCore import Qt, QCoreApplication # Import QCoreApplication for CursorShape

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from domain.contracts.xform_api_repository import XFormApiRepository

class GenerateSQLTab(QWidget):
    def __init__(self, xform_api_repository: XFormApiRepository, parent=None):
        super().__init__(parent)
        self.xform_api_repository = xform_api_repository
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- Header ---
        main_layout.addWidget(QLabel("<h2>Generate XForm SQL</h2>"))

        # --- Country Selection ---
        country_layout = QHBoxLayout()
        country_layout.addWidget(QLabel("Select country:"))
        self.country_combo = QComboBox()
        self.country_combo.addItems(["MALI", "RCI"])
        country_layout.addWidget(self.country_combo)
        country_layout.addStretch(1) # Push combo to left
        main_layout.addLayout(country_layout)

        # --- XForm Name Input ---
        form_name_layout = QHBoxLayout()
        form_name_layout.addWidget(QLabel("Enter XForm name:"))
        self.form_name_input = QLineEdit()
        self.form_name_input.setPlaceholderText("e.g., patient_registration")
        form_name_layout.addWidget(self.form_name_input)
        main_layout.addLayout(form_name_layout)

        # --- Fetch SQL Button ---
        self.btn_fetch_sql = QPushButton("Fetch Generated SQL")
        self.btn_fetch_sql.clicked.connect(self.fetch_generated_sql)
        main_layout.addWidget(self.btn_fetch_sql)

        # --- Results Display ---
        main_layout.addWidget(QLabel("<h3>Generated SQL:</h3>"))
        self.sql_output_editor = QTextEdit()
        self.sql_output_editor.setReadOnly(True)
        self.sql_output_editor.setPlaceholderText("Generated SQL will appear here...")
        main_layout.addWidget(self.sql_output_editor)

        main_layout.addStretch(1) # Push content to top
        self.setLayout(main_layout)

    def fetch_generated_sql(self):
        country = self.country_combo.currentText()
        form_name = self.form_name_input.text().strip()

        if not form_name:
            QMessageBox.warning(self, "Missing Input", "Please enter an XForm name.")
            return

        # Show loading state
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor) # Corrected: Use Qt.CursorShape.WaitCursor
        self.sql_output_editor.setText("Generating SQL... Please wait.")
        QApplication.processEvents() # Update UI to show message

        try:
            generated_sql = self.xform_api_repository.get_bigquery_extraction_sql(country, form_name)
            self.sql_output_editor.setText(generated_sql)
            QMessageBox.information(self, "Success", "SQL generated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
            self.sql_output_editor.setText(f"Error generating SQL: {e}")
        finally:
            QApplication.restoreOverrideCursor() # Restore cursor
