from dependency_injector import containers, providers

# --- Import all concrete implementations ---
from infrastructure.logging.cloud_run_logger import CloudRunLogger
from infrastructure.repositories.github_repository import GitHubRepository
from infrastructure.repositories.github_actions_repository import GitHubActionsRepository
from infrastructure.repositories.bigquery_repository import BigQueryRepository
from infrastructure.repositories.cloud_function_xform_api_repository import CloudFunctionXFormApiRepository
from infrastructure.repositories.http_cht_app_repository import HttpCHTAppRepository
from infrastructure.repositories.vertex_ai_semantic_comparator import VertexAISemanticComparator
from infrastructure.repositories.pandas_xlsform_repository import PandasXLSFormRepository
from infrastructure.repositories.pandas_rich_xlsform_repository import PandasRichXLSFormRepository
from application.services.form_comparator_service_impl import FormComparatorServiceImpl
from application.services.xlsform_comparator_service_impl import XLSFormComparatorServiceImpl
from application.services.bulk_audit_service_impl import BulkAuditServiceImpl

# --- Import UI entry points ---
from infrastructure.ui.streamlit.app import build_ui as build_streamlit_ui
from infrastructure.ui.pyqt.app import build_ui as build_pyqt_ui

class Container(containers.DeclarativeContainer):
    """
    The main IoC container for the application.
    It defines the wiring for the application and reads configuration values.
    """
    config = providers.Configuration()

    # --- Repositories ---

    logger = providers.Factory(CloudRunLogger)

    code_repository = providers.Factory(
        GitHubRepository,
        owner=config.repositories.code_repository.args.owner,
        repo_name=config.repositories.code_repository.args.repo_name,
        logger=logger
    )

    cicd_repository = providers.Factory(
        GitHubActionsRepository,
        owner=config.repositories.cicd_repository.args.owner,
        repo_name=config.repositories.cicd_repository.args.repo_name,
        logger=logger
    )

    data_warehouse_repository = providers.Factory(
        BigQueryRepository,
        logger=logger
    )

    xform_api_repository = providers.Factory(
        CloudFunctionXFormApiRepository,
        logger=logger
    )

    cht_app_repository = providers.Factory(
        HttpCHTAppRepository,
        logger=logger
    )

    semantic_comparator_repository = providers.Factory(
        VertexAISemanticComparator,
        logger=logger
    )

    xlsform_repository = providers.Factory(PandasXLSFormRepository)

    rich_xlsform_repository = providers.Factory(PandasRichXLSFormRepository)

    # --- Services ---

    form_comparator_service = providers.Factory(
        FormComparatorServiceImpl,
        xlsform_repository=xlsform_repository
    )

    xlsform_comparator_service = providers.Factory(
        XLSFormComparatorServiceImpl,
        xlsform_repo=rich_xlsform_repository,
        semantic_repo=semantic_comparator_repository
    )

    bulk_audit_service = providers.Factory(
        BulkAuditServiceImpl,
        cht_app_repo=cht_app_repository,
        code_repo=code_repository,
        dw_repo=data_warehouse_repository,
        xlsform_repo=xlsform_repository,
        logger=logger
    )

    # --- UI Provider ---
    # This provider selects the UI entry point function based on the config file.
    build_ui = providers.Selector(
        config.ui.interface,
        streamlit=providers.Callable(build_streamlit_ui),
        pyqt=providers.Callable(build_pyqt_ui)
    )
