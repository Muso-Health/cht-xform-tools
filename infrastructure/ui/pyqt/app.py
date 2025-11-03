import sys
from PyQt6.QtWidgets import QApplication

# Import the MainWindow class
from infrastructure.ui.pyqt.main_window import MainWindow

# Import all application services (these will be injected)
from application.contracts.form_comparator_service import FormComparatorService
from application.contracts.bulk_audit_service import BulkAuditService
from application.contracts.xlsform_comparator_service import XLSFormComparatorService
from domain.contracts.code_repository import CodeRepository
from domain.contracts.cicd_repository import CICDRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.xform_api_repository import XFormApiRepository

def build_ui(
    comparator_service: FormComparatorService,
    bulk_audit_service: BulkAuditService,
    xlsform_comparator_service: XLSFormComparatorService,
    code_repository: CodeRepository,
    cicd_repository: CICDRepository,
    data_warehouse_repository: DataWarehouseRepository,
    xform_api_repository: XFormApiRepository
):
    """
    This function serves as the entry point for the PyQt user interface.
    It initializes the QApplication, creates the main window, and starts the event loop.
    """
    app = QApplication(sys.argv)

    main_window = MainWindow(
        comparator_service=comparator_service,
        bulk_audit_service=bulk_audit_service,
        xlsform_comparator_service=xlsform_comparator_service,
        code_repository=code_repository,
        cicd_repository=cicd_repository,
        data_warehouse_repository=data_warehouse_repository,
        xform_api_repository=xform_api_repository
    )
    main_window.show()

    sys.exit(app.exec())
