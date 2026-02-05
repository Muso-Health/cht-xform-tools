import unittest
from unittest.mock import patch, MagicMock
from application.services.bulk_audit_service_impl import BulkAuditServiceImpl
from infrastructure.repositories.pandas_xlsform_repository import PandasXLSFormRepository
from infrastructure.repositories.github_repository import GitHubRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from infrastructure.repositories.http_cht_app_repository import HttpCHTAppRepository
from infrastructure.logging.dummy_logger import DummyLogger

class TestBulkAuditDbDoc(unittest.TestCase):

    @patch.object(HttpCHTAppRepository, 'get_installed_xform_ids')
    def test_parser_finds_db_doc_groups_in_stock_management(self, mock_get_installed_xform_ids):
        # 1. Isolate the test to the 'stock_management' form
        mock_get_installed_xform_ids.return_value = ["stock_management"]

        # 2. Initialize services and repositories
        logger = DummyLogger()
        
        # Use the real repositories for code fetching and parsing
        code_repo = GitHubRepository(owner="Muso-Health", repo_name="config-muso", logger=logger)
        xlsform_repo = PandasXLSFormRepository()
        
        cht_app_repo = HttpCHTAppRepository(logger)
        dw_repo = MagicMock(spec=DataWarehouseRepository)
        dw_repo.get_view_query.side_effect = FileNotFoundError

        # Instantiate the service with the real and mocked components
        bulk_audit_service = BulkAuditServiceImpl(
            cht_app_repo=cht_app_repo, 
            code_repo=code_repo, 
            dw_repo=dw_repo, 
            xlsform_repo=xlsform_repo, 
            logger=logger
        )

        # 3. Run the audit
        country_code = "MALI"
        audit_result = bulk_audit_service.perform_audit(country_code)

        # 4. Assert the results
        self.assertEqual(len(audit_result.compared_forms), 1, "The stock_management form should be processed.")
        
        stock_management_result = audit_result.compared_forms[0]
        self.assertEqual(stock_management_result.form_id, "stock_management")

        # The crucial assertion: Check that the parser found the THREE db-doc groups
        self.assertEqual(len(stock_management_result.db_doc_groups), 3, "Should find three db-doc groups in stock_management.")

        db_doc_group_names = {group.group_name for group in stock_management_result.db_doc_groups}
        self.assertIn("stock_distribution", db_doc_group_names)
        self.assertIn("stock_adjustment_req", db_doc_group_names)
        self.assertIn("stock_receipt", db_doc_group_names) # Corrected the third group name


if __name__ == '__main__':
    unittest.main()
