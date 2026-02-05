from dependency_injector import containers, providers

from infrastructure.logging.cloud_run_logger import CloudRunLogger
from infrastructure.repositories.github_repository import GitHubRepository
from infrastructure.repositories.github_actions_repository import GitHubActionsRepository
from infrastructure.repositories.bigquery_repository import BigQueryRepository
from infrastructure.repositories.cloud_function_xform_api_repository import CloudFunctionXFormApiRepository
from infrastructure.repositories.http_cht_app_repository import HttpCHTAppRepository
from infrastructure.repositories.vertex_ai_semantic_comparator import VertexAISemanticComparator
from infrastructure.repositories.pandas_xlsform_repository import PandasXLSFormRepository
from infrastructure.repositories.pandas_rich_xlsform_repository import PandasRichXLSFormRepository
from infrastructure.repositories.regex_sql_parser_repository import RegexSQLParserRepository
from application.services.form_comparator_service_impl import FormComparatorServiceImpl
from application.services.xlsform_comparator_service_impl import XLSFormComparatorServiceImpl
from application.services.bulk_audit_service_impl import BulkAuditServiceImpl
from application.services.data_catalog_service_impl import DataCatalogServiceImpl
from application.services.data_catalog_enrichment_service_impl import DataCatalogEnrichmentServiceImpl
from domain.services.cht_path_interpreter import CHTPathInterpreter
from infrastructure.ui.streamlit.app import build_ui as build_streamlit_ui
from infrastructure.ui.pyqt.app import build_ui as build_pyqt_ui
from infrastructure.ui.cli.main import build_ui as build_cli_ui

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    form_context_config = providers.Configuration()

    logger = providers.Factory(CloudRunLogger)
    code_repository = providers.Factory(GitHubRepository, owner=config.repositories.code_repository.args.owner, repo_name=config.repositories.code_repository.args.repo_name, logger=logger)
    cicd_repository = providers.Factory(GitHubActionsRepository, owner=config.repositories.cicd_repository.args.owner, repo_name=config.repositories.cicd_repository.args.repo_name, logger=logger)
    data_warehouse_repository = providers.Factory(BigQueryRepository, logger=logger)
    xform_api_repository = providers.Factory(CloudFunctionXFormApiRepository, logger=logger)
    cht_app_repository = providers.Factory(HttpCHTAppRepository, logger=logger)
    semantic_comparator_repository = providers.Factory(VertexAISemanticComparator, logger=logger)
    xlsform_repository = providers.Factory(PandasXLSFormRepository)
    rich_xlsform_repository = providers.Factory(PandasRichXLSFormRepository)
    sql_parser_repository = providers.Factory(RegexSQLParserRepository)

    cht_path_interpreter = providers.Factory(CHTPathInterpreter)

    form_comparator_service = providers.Factory(FormComparatorServiceImpl, xlsform_repository=xlsform_repository, dw_repository=data_warehouse_repository)
    xlsform_comparator_service = providers.Factory(XLSFormComparatorServiceImpl, xlsform_repo=rich_xlsform_repository, semantic_repo=semantic_comparator_repository)
    bulk_audit_service = providers.Factory(BulkAuditServiceImpl, cht_app_repo=cht_app_repository, code_repo=code_repository, dw_repo=data_warehouse_repository, xlsform_repo=xlsform_repository, logger=logger)
    data_catalog_service = providers.Factory(DataCatalogServiceImpl, cht_app_repo=cht_app_repository, code_repo=code_repository, dw_repo=data_warehouse_repository, xlsform_repo=rich_xlsform_repository, sql_parser_repo=sql_parser_repository, logger=logger)
    data_catalog_enrichment_service = providers.Factory(DataCatalogEnrichmentServiceImpl, semantic_repo=semantic_comparator_repository, code_repo=code_repository, xlsform_repo=rich_xlsform_repository, path_interpreter_factory=cht_path_interpreter.provider, form_context_config=form_context_config, logger=logger)

    build_ui = providers.Selector(
        config.ui.interface,
        streamlit=providers.Callable(
            build_streamlit_ui,
            comparator_service=form_comparator_service,
            bulk_audit_service=bulk_audit_service,
            xlsform_comparator_service=xlsform_comparator_service,
            data_catalog_service=data_catalog_service,
            data_catalog_enrichment_service=data_catalog_enrichment_service,
            code_repository=code_repository,
            cicd_repository=cicd_repository,
            data_warehouse_repository=data_warehouse_repository,
            xform_api_repository=xform_api_repository
        ),
        pyqt=providers.Callable(
            build_pyqt_ui,
            comparator_service=form_comparator_service,
            bulk_audit_service=bulk_audit_service,
            xlsform_comparator_service=xlsform_comparator_service,
            code_repository=code_repository,
            cicd_repository=cicd_repository,
            data_warehouse_repository=data_warehouse_repository,
            xform_api_repository=xform_api_repository
        ),
        cli=providers.Callable(
            build_cli_ui,
            form_comparator_service=form_comparator_service,
            bulk_audit_service=bulk_audit_service,
            xlsform_comparator_service=xlsform_comparator_service,
            data_catalog_service=data_catalog_service,
            data_catalog_enrichment_service=data_catalog_enrichment_service,
            code_repository=code_repository,
            cicd_repository=cicd_repository,
            data_warehouse_repository=data_warehouse_repository,
            xform_api_repository=xform_api_repository
        )
    )
