
from PyQt6.QtWidgets import QMainWindow, QTabWidget

# Import all application services (these will be injected)
from application.contracts.form_comparator_service import FormComparatorService
from application.contracts.bulk_audit_service import BulkAuditService
from application.contracts.xlsform_comparator_service import XLSFormComparatorService
from domain.contracts.code_repository import CodeRepository
from domain.contracts.cicd_repository import CICDRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.xform_api_repository import XFormApiRepository

# Import the actual tab widgets
from infrastructure.ui.pyqt.sql_comparator_tab import SQLComparatorTab
from infrastructure.ui.pyqt.deploy_history_tab import DeployHistoryTab
from infrastructure.ui.pyqt.generate_sql_tab import GenerateSQLTab
from infrastructure.ui.pyqt.bulk_audit_tab import BulkAuditTab
from infrastructure.ui.pyqt.compare_xlsforms_tab import CompareXLSFormsTab

class MainWindow(QMainWindow):
    def __init__(
        self,
        comparator_service: FormComparatorService,
        bulk_audit_service: BulkAuditService,
        xlsform_comparator_service: XLSFormComparatorService,
        code_repository: CodeRepository,
        cicd_repository: CICDRepository,
        data_warehouse_repository: DataWarehouseRepository,
        xform_api_repository: XFormApiRepository
    ):
        super().__init__()

        self.setWindowTitle("XLSForm Data Source Tools (PyQt)")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # --- Create and Add Actual Tabs ---
        # Tab 1: XLSForm SQL Comparator
        sql_comparator_tab = SQLComparatorTab(comparator_service=comparator_service)
        self.tab_widget.addTab(sql_comparator_tab, "XLSForm SQL Comparator")

        # Tab 2: XLSForm Deploy History
        deploy_history_tab = DeployHistoryTab(cicd_repository=cicd_repository)
        self.tab_widget.addTab(deploy_history_tab, "XLSForm Deploy History")

        # Tab 3: Generate XForm SQL
        generate_sql_tab = GenerateSQLTab(xform_api_repository=xform_api_repository)
        self.tab_widget.addTab(generate_sql_tab, "Generate XForm SQL")

        # Tab 4: Bulk Audit
        bulk_audit_tab = BulkAuditTab(bulk_audit_service=bulk_audit_service)
        self.tab_widget.addTab(bulk_audit_tab, "Bulk Audit")

        # Tab 5: Compare Two XLSForms
        compare_xlsforms_tab = CompareXLSFormsTab(xlsform_comparator_service=xlsform_comparator_service)
        self.tab_widget.addTab(compare_xlsforms_tab, "Compare Two XLSForms")

        # Store services for later use by individual tabs (when they are implemented)
        # This is no longer strictly necessary as services are passed directly to tabs
        # but keeping it for potential future main window level logic.
        self.services = {
            "comparator_service": comparator_service,
            "bulk_audit_service": bulk_audit_service,
            "xlsform_comparator_service": xlsform_comparator_service,
            "code_repository": code_repository,
            "cicd_repository": cicd_repository,
            "data_warehouse_repository": data_warehouse_repository,
            "xform_api_repository": xform_api_repository
        }
