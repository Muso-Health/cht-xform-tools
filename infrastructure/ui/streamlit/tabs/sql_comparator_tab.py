import streamlit as st
from streamlit_ace import st_ace
from streamlit_tree_select import tree_select

from application.contracts.form_comparator_service import FormComparatorService
from domain.contracts.code_repository import CodeRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from infrastructure.ui.streamlit.ui_utils import build_tree_from_results, _
from application.utils import get_view_name  # Import the centralized utility

def build_tab_sql_comparator(
    comparator_service: FormComparatorService,
    code_repository: CodeRepository,
    data_warehouse_repository: DataWarehouseRepository
):
    if 'sql_content' not in st.session_state:
        st.session_state.sql_content = None
    if 'comparison_result' not in st.session_state:
        st.session_state.comparison_result = None

    def clear_comparator_results():
        st.session_state.comparison_result = None

    col1, col2 = st.columns([0.4, 0.6])

    with col1:
        st.header(_("Inputs"))
        st.subheader(_("XLSForm Source"))
        xls_source_option = st.radio("XLSForm Source", ["Upload File", "Fetch from GitHub"], horizontal=True, key="refactor_comparator_xls_source", on_change=clear_comparator_results, label_visibility="collapsed")
        
        uploaded_xls = None
        form_name_input = None
        country_options_map = {"MALI": "muso-mali/forms/app/", "RCI": "muso-cdi/forms/app/"}
        selected_country_label = st.selectbox(_("Select the country"), options=list(country_options_map.keys()), on_change=clear_comparator_results, key="refactor_comparator_country_selector")

        if xls_source_option == "Upload File":
            uploaded_xls = st.file_uploader(_("Upload your XLSForm (.xlsx)"), type=["xlsx"], key="refactor_comparator_xls_uploader", on_change=clear_comparator_results)
        else:
            form_name_input = st.text_input(_("Enter the XForm file name (without extension)"), on_change=clear_comparator_results, key="refactor_comparator_form_name")

        st.divider()

        st.subheader(_("SQL Source"))
        sql_input_option = st.radio("SQL Source", ["Upload File", "Fetch from BigQuery"], horizontal=True, key="refactor_comparator_sql_source", on_change=clear_comparator_results, label_visibility="collapsed")

        if sql_input_option == "Upload File":
            uploaded_sql_file = st.file_uploader(_("Upload your SQL file (.sql)"), type=["sql"], key="refactor_comparator_sql_uploader", on_change=clear_comparator_results)
            if uploaded_sql_file:
                st.session_state.sql_content = uploaded_sql_file.getvalue()
        else:
            default_bq_project = "musoitproducts"
            default_bq_dataset = "cht_mali_prod" if selected_country_label == "MALI" else "cht_rci_prod"
            default_bq_view = get_view_name(selected_country_label, form_name_input)
            
            bq_project_id = st.text_input("BigQuery Project ID", value=default_bq_project, key="refactor_comparator_bq_project", on_change=clear_comparator_results)
            bq_dataset_id = st.text_input("BigQuery Dataset ID", value=default_bq_dataset, key="refactor_comparator_bq_dataset", on_change=clear_comparator_results)
            bq_view_id = st.text_input("BigQuery View ID", value=default_bq_view, key="refactor_comparator_bq_view", on_change=clear_comparator_results)
            
            if st.button("Fetch View SQL", key="refactor_comparator_fetch_sql"):
                if all([bq_project_id, bq_dataset_id, bq_view_id]):
                    try:
                        st.info(f"Fetching view {bq_view_id}...")
                        view_query = data_warehouse_repository.get_view_query(bq_project_id, bq_dataset_id, bq_view_id)
                        st.session_state.sql_content = view_query.encode('utf-8')
                        st.success("Successfully fetched view.")
                    except Exception as e:
                        st.error(f"Failed to fetch from BigQuery: {e}")
                else:
                    st.warning("Please provide all BigQuery details.")

        st.divider()

        if st.button("Compare XLSForm and SQL", key="refactor_comparator_compare_button"):
            clear_comparator_results()
            xls_content = None
            if xls_source_option == "Upload File" and uploaded_xls:
                xls_content = uploaded_xls.getvalue()
            elif xls_source_option == "Fetch from GitHub" and form_name_input:
                try:
                    form_filename = f"{form_name_input}.xlsx"
                    path_prefix = country_options_map[selected_country_label]
                    full_file_path = f"{path_prefix}{form_filename}"
                    with st.spinner(f"Downloading {form_filename}..."):
                        xls_content = code_repository.download_file(branch="master", file_path=full_file_path)
                    st.success(f"Successfully downloaded {form_filename}.")
                except Exception as e:
                    st.error(f"Failed to download XLSForm: {e}")
            
            if xls_content and st.session_state.sql_content:
                with st.spinner("Running comparison..."):
                    try:
                        result_dto = comparator_service.compare_form_with_sql(xls_content, st.session_state.sql_content, selected_country_label)
                        st.session_state.comparison_result = result_dto
                    except Exception as e:
                        st.error(_("An error occurred during comparison: {error_message}").format(error_message=e))
            else:
                st.warning("Please ensure both an XLSForm and SQL content are provided/loaded before comparing.")

        if st.session_state.comparison_result:
            with st.expander("Comparison Results", expanded=True):
                result_dto = st.session_state.comparison_result
                
                # Categorize not_founds into critical and non-critical
                critical_not_founds = []
                inputs_not_founds = []
                prescription_not_founds = []
                
                for item in result_dto.not_founds:
                    is_inputs = item.json_path.startswith('$.inputs')
                    is_prescription = 'prescription_summary' in item.json_path
                    
                    if is_inputs:
                        inputs_not_founds.append(item)
                    elif is_prescription:
                        prescription_not_founds.append(item)
                    else:
                        critical_not_founds.append(item)

                if not result_dto.founds and not critical_not_founds and not inputs_not_founds and not prescription_not_founds and not result_dto.not_found_bm_elements:
                    st.success(_("No JSON paths found in the form to compare, or all paths are present in the SQL."))
                else:
                    if critical_not_founds:
                        st.subheader(_("Not Found (Critical)"))
                        critical_tree = build_tree_from_results(critical_not_founds, icon="❌")
                        tree_select(critical_tree, key="sql_comparator_critical_tree")
                    
                    if inputs_not_founds:
                        st.subheader(_("Not Found (Non-Critical: Inputs)"))
                        inputs_tree = build_tree_from_results(inputs_not_founds, icon="ℹ️")
                        tree_select(inputs_tree, key="sql_comparator_inputs_tree")

                    if prescription_not_founds:
                        st.subheader(_("Not Found (Non-Critical: Prescription)"))
                        prescription_tree = build_tree_from_results(prescription_not_founds, icon="ℹ️")
                        tree_select(prescription_tree, key="sql_comparator_prescription_tree")

                    if result_dto.not_found_bm_elements:
                        st.subheader(_("Not Found `_bm` Elements (RCI Only)"))
                        bm_tree = build_tree_from_results(result_dto.not_found_bm_elements, icon="ℹ️")
                        tree_select(bm_tree, key="sql_comparator_bm_tree")

                    if result_dto.founds:
                        st.subheader(_("Found in SQL"))
                        found_tree = build_tree_from_results(result_dto.founds, icon="✅")
                        tree_select(found_tree, key="sql_comparator_found_tree")

    with col2:
        st.header(_("SQL Content"))
        editor_value = ""
        editor_language = "text"
        editor_key = "refactor_sql_content_editor_empty"
        if st.session_state.sql_content:
            editor_value = st.session_state.sql_content.decode('utf-8')
            editor_language = "sql"
            editor_key = f"refactor_sql_content_editor_{hash(st.session_state.sql_content)}"
        else:
            editor_value = _("SQL content will appear here once loaded.")
        
        st_ace(
            value=editor_value,
            language=editor_language,
            theme="github",
            readonly=True,
            key=editor_key
        )
