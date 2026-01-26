import streamlit as st

from application.contracts.form_comparator_service import FormComparatorService
from application.contracts.bulk_audit_service import BulkAuditService
from application.contracts.xlsform_comparator_service import XLSFormComparatorService
from application.contracts.data_catalog_service import DataCatalogService
from application.contracts.data_catalog_enrichment_service import DataCatalogEnrichmentService
from domain.contracts.code_repository import CodeRepository
from domain.contracts.cicd_repository import CICDRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.xform_api_repository import XFormApiRepository

from .ui_utils import _
from .tabs.sql_comparator_tab import build_tab_sql_comparator
from .tabs.deploy_history_tab import build_tab_deploy_history
from .tabs.generate_sql_tab import build_tab_generate_sql
from .tabs.bulk_audit_tab import build_tab_bulk_audit
from .tabs.compare_xlsforms_tab import build_tab_compare_xlsforms
from .tabs.data_catalog_tab import build_tab_data_catalog

def build_ui(
    comparator_service: FormComparatorService, 
    bulk_audit_service: BulkAuditService,
    xlsform_comparator_service: XLSFormComparatorService,
    data_catalog_service: DataCatalogService,
    data_catalog_enrichment_service: DataCatalogEnrichmentService,
    code_repository: CodeRepository, 
    cicd_repository: CICDRepository, 
    data_warehouse_repository: DataWarehouseRepository, 
    xform_api_repository: XFormApiRepository
):
    st.set_page_config(layout="wide")
    st.title(_("XLSForm Data Source Tools"))

    tab_titles = [
        _("XLSForm SQL Comparator"),
        _("XLSForm Deploy History"),
        _("Generate XForm SQL"),
        _("Bulk Audit"),
        _("Compare Two XLSForms"),
        _("Data Catalog Generator")
    ]
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_titles)

    with tab1:
        build_tab_sql_comparator(comparator_service, code_repository, data_warehouse_repository)
    with tab2:
        build_tab_deploy_history(cicd_repository)
    with tab3:
        build_tab_generate_sql(xform_api_repository)
    with tab4:
        build_tab_bulk_audit(bulk_audit_service)
    with tab5:
        build_tab_compare_xlsforms(xlsform_comparator_service)
    with tab6:
        build_tab_data_catalog(data_catalog_service, data_catalog_enrichment_service)
