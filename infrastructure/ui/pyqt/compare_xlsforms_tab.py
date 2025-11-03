import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QCheckBox, QLabel, QTextEdit, QFileDialog, QGroupBox, QMessageBox, QApplication)
from PyQt6.QtCore import Qt

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from application.contracts.xlsform_comparator_service import XLSFormComparatorService
from application.dtos import XLSFormComparisonResultDTO, ModifiedElementDTO

class CompareXLSFormsTab(QWidget):
    def __init__(self, xlsform_comparator_service: XLSFormComparatorService, parent=None):
        super().__init__(parent)
        self.xlsform_comparator_service = xlsform_comparator_service
        self.old_xls_path = None
        self.new_xls_path = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- File Upload Section ---
        file_group_box = QGroupBox("XLSForm Files")
        file_layout = QVBoxLayout()

        # Old XLSForm
        old_xls_layout = QHBoxLayout()
        self.old_xls_label = QLabel("Old XLSForm: No file selected")
        btn_upload_old = QPushButton("Upload Old XLSForm")
        btn_upload_old.clicked.connect(self.upload_old_xlsform)
        old_xls_layout.addWidget(self.old_xls_label)
        old_xls_layout.addWidget(btn_upload_old)
        file_layout.addLayout(old_xls_layout)

        # New XLSForm
        new_xls_layout = QHBoxLayout()
        self.new_xls_label = QLabel("New XLSForm: No file selected")
        btn_upload_new = QPushButton("Upload New XLSForm")
        btn_upload_new.clicked.connect(self.upload_new_xlsform)
        new_xls_layout.addWidget(self.new_xls_label)
        new_xls_layout.addWidget(btn_upload_new)
        file_layout.addLayout(new_xls_layout)

        file_group_box.setLayout(file_layout)
        main_layout.addWidget(file_group_box)

        # --- Options Section ---
        options_group_box = QGroupBox("Comparison Options")
        options_layout = QVBoxLayout()

        # Exclusion Options
        exclusion_layout = QHBoxLayout()
        self.chk_exclude_notes = QCheckBox("Exclude 'note' types")
        self.chk_exclude_notes.setChecked(True)
        self.chk_exclude_inputs = QCheckBox("Exclude 'inputs' group")
        self.chk_exclude_inputs.setChecked(True)
        self.chk_exclude_prescription = QCheckBox("Exclude 'prescription_summary' group")
        self.chk_exclude_prescription.setChecked(True)
        exclusion_layout.addWidget(self.chk_exclude_notes)
        exclusion_layout.addWidget(self.chk_exclude_inputs)
        exclusion_layout.addWidget(self.chk_exclude_prescription)
        options_layout.addWidget(QLabel("Exclusion Options:"))
        options_layout.addLayout(exclusion_layout)

        # Semantic Matching Options
        semantic_layout = QHBoxLayout()
        self.chk_use_title_matching = QCheckBox("Use AI for title matching")
        self.chk_use_title_matching.setChecked(False)
        self.chk_use_formula_matching = QCheckBox("Use AI for formula matching")
        self.chk_use_formula_matching.setChecked(False)
        semantic_layout.addWidget(self.chk_use_title_matching)
        semantic_layout.addWidget(self.chk_use_formula_matching)
        options_layout.addWidget(QLabel("Semantic Matching Options (requires AI - may incur costs):"))
        options_layout.addLayout(semantic_layout)

        options_group_box.setLayout(options_layout)
        main_layout.addWidget(options_group_box)

        # --- Compare Button ---
        btn_compare = QPushButton("Compare XLSForms")
        btn_compare.clicked.connect(self.compare_xlsforms)
        main_layout.addWidget(btn_compare)

        # --- Results Display ---
        self.results_text_edit = QTextEdit()
        self.results_text_edit.setReadOnly(True)
        main_layout.addWidget(self.results_text_edit)

        self.setLayout(main_layout)

    def upload_old_xlsform(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Old XLSForm", "", "XLSForm Files (*.xlsx)")
        if file_path:
            self.old_xls_path = file_path
            self.old_xls_label.setText(f"Old XLSForm: {os.path.basename(file_path)}")

    def upload_new_xlsform(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select New XLSForm", "", "XLSForm Files (*.xlsx)")
        if file_path:
            self.new_xls_path = file_path
            self.new_xls_label.setText(f"New XLSForm: {os.path.basename(file_path)}")

    def compare_xlsforms(self):
        if not self.old_xls_path or not self.new_xls_path:
            QMessageBox.warning(self, "Missing Files", "Please select both Old and New XLSForm files.")
            return

        try:
            with open(self.old_xls_path, "rb") as f:
                old_content = f.read()
            with open(self.new_xls_path, "rb") as f:
                new_content = f.read()

            exclude_notes = self.chk_exclude_notes.isChecked()
            exclude_inputs = self.chk_exclude_inputs.isChecked()
            exclude_prescription = self.chk_exclude_prescription.isChecked()
            use_title_matching = self.chk_use_title_matching.isChecked()
            use_formula_matching = self.chk_use_formula_matching.isChecked()

            self.results_text_edit.setText("Comparing... Please wait.")
            QApplication.processEvents() # Update UI to show message

            result: XLSFormComparisonResultDTO = self.xlsform_comparator_service.compare_forms(
                old_form_content=old_content,
                new_form_content=new_content,
                exclude_notes=exclude_notes,
                exclude_inputs=exclude_inputs,
                exclude_prescription=exclude_prescription,
                use_title_matching=use_title_matching,
                use_formula_matching=use_formula_matching
            )
            self.display_results(result)

        except Exception as e:
            QMessageBox.critical(self, "Comparison Error", f"An error occurred during comparison: {e}")
            self.results_text_edit.setText(f"Error: {e}")

    def display_results(self, result: XLSFormComparisonResultDTO):
        report = []
        report.append("--- XLSForm Comparison Report ---")
        report.append(f"Total Unchanged: {len(result.unchanged_elements)}")
        report.append(f"Total Modified: {len(result.modified_elements)}")
        report.append(f"Total New: {len(result.new_elements)}")
        report.append(f"Total Deleted: {len(result.deleted_elements)}")
        report.append("\n")

        if result.modified_elements:
            report.append("--- Modified Elements ---")
            for item in result.modified_elements:
                report.append(f"- Name: {item.old_element.question_name}")
                report.append(f"  Reason: {item.reason}")
                report.append(f"  Old Path: {item.old_element.path}")
                report.append(f"  New Path: {item.new_element.path}")
            report.append("\n")

        if result.new_elements:
            report.append("--- New Elements ---")
            for item in result.new_elements:
                report.append(f"- Path: {item.path} (Name: {item.question_name})")
            report.append("\n")

        if result.deleted_elements:
            report.append("--- Deleted Elements ---")
            for item in result.deleted_elements:
                report.append(f"- Path: {item.path} (Name: {item.question_name})")
            report.append("\n")

        if result.unchanged_elements:
            report.append("--- Unchanged Elements ---")
            for item in result.unchanged_elements:
                report.append(f"- Path: {item[0].path} (Name: {item[0].question_name})")
            report.append("\n")

        self.results_text_edit.setText("\n".join(report))
