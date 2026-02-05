import streamlit as st
from streamlit_ace import st_ace
from streamlit_tree_select import tree_select

from application.contracts.form_comparator_service import FormComparatorService
from domain.contracts.code_repository import CodeRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from infrastructure.ui.streamlit.ui_utils import build_tree_from_results, _
from application.utils import get_view_name

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

        default_bq_project = "musoitproducts"
        default_bq_dataset = "cht_mali_prod" if selected_country_label == "MALI" else "cht_rci_prod"
        default_bq_view = get_view_name(selected_country_label, form_name_input)
        
        bq_project_id = st.text_input("BigQuery Project ID", value=default_bq_project, key="refactor_comparator_bq_project")
        bq_dataset_id = st.text_input("BigQuery Dataset ID", value=default_bq_dataset, key="refactor_comparator_bq_dataset")
        
        if sql_input_option == "Upload File":
            uploaded_sql_file = st.file_uploader(_("Upload your SQL file (.sql)"), type=["sql"], key="refactor_comparator_sql_uploader", on_change=clear_comparator_results)
            if uploaded_sql_file:
                st.session_state.sql_content = uploaded_sql_file.getvalue()
        else:
            bq_view_id = st.text_input("BigQuery View ID", value=default_bq_view, key="refactor_comparator_bq_view")
            if st.button("Fetch View SQL", key="refactor_comparator_fetch_sql"):
                if all([bq_project_id, bq_dataset_id, bq_view_id]):
                    with st.spinner(f"Fetching view {bq_view_id}..."):
                        try:
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
                with st.spinner("Running comparison... This may take a moment if fetching related views."):
                    try:
                        st.session_state.comparison_result = comparator_service.compare_form_with_sql(
                            xls_content, st.session_state.sql_content, selected_country_label, form_name_input, bq_project_id, bq_dataset_id
                        )
                    except Exception as e:
                        st.error(_("An error occurred during comparison: {error_message}").format(error_message=e))
            else:
                st.warning("Please ensure both an XLSForm and SQL content are provided/loaded before comparing.")

        if st.session_state.comparison_result:
            result = st.session_state.comparison_result
            with st.expander("Comparison Results", expanded=True):
                st.subheader("Main Form Body")
                main_res = result.main_body_comparison
                if not main_res.founds and not main_res.not_founds and not main_res.not_found_bm_elements:
                    st.success("All main body elements are present in the SQL.")
                if main_res.not_founds:
                    st.write("Not Found (Critical):"); tree_select(build_tree_from_results(main_res.not_founds, icon="❌"), key="sql_comp_main_critical")
                if main_res.not_found_bm_elements:
                    st.write("Not Found `_bm` Elements (RCI Only):"); tree_select(build_tree_from_results(main_res.not_found_bm_elements, icon="ℹ️"), key="sql_comp_main_bm")
                if main_res.founds:
                    st.write("Found in SQL:"); tree_select(build_tree_from_results(main_res.founds, icon="✅"), key="sql_comp_main_found")

                if result.repeat_group_comparisons:
                    st.divider(); st.subheader("Repeat Group Audits")
                    for res in result.repeat_group_comparisons:
                        if res.handling_method == 'NOT_FOUND':
                            st.error(f"❌ View NOT found for repeat group: `{res.repeat_group_name}`")
                        elif res.comparison.not_founds:
                            st.warning(f"⚠️ Handled as `{res.handling_method}` for `{res.repeat_group_name}`, but elements are missing:")
                            tree_select(build_tree_from_results(res.comparison.not_founds, icon="➡️"), key=f"sql_comp_repeat_notfound_{res.repeat_group_name}")
                        else:
                            st.success(f"✅ Handled as `{res.handling_method}` for `{res.repeat_group_name}` and all elements are present.")
                            if res.comparison.founds:
                                with st.expander("Show found elements"):
                                    tree_select(build_tree_from_results(res.comparison.founds, icon="✅"), key=f"sql_comp_repeat_found_{res.repeat_group_name}")

                if result.db_doc_group_comparisons:
                    st.divider(); st.subheader("DB-Doc Group Audits")
                    for res in result.db_doc_group_comparisons:
                        if not res.view_found:
                            st.error(f"❌ View NOT found for db-doc group: `{res.group_name}`")
                        elif res.comparison.not_founds:
                            st.warning(f"⚠️ View found for `{res.group_name}`, but elements are missing:")
                            tree_select(build_tree_from_results(res.comparison.not_founds, icon="➡️"), key=f"sql_comp_dbdoc_notfound_{res.group_name}")
                        else:
                            st.success(f"✅ All elements for db-doc group `{res.group_name}` are present in its SQL view.")
                            if res.comparison.founds:
                                with st.expander("Show found elements"):
                                    tree_select(build_tree_from_results(res.comparison.founds, icon="✅"), key=f"sql_comp_dbdoc_found_{res.group_name}")

    with col2:
        st.header(_("SQL Content"))
        editor_value = _("SQL content will appear here once loaded.")
        if st.session_state.sql_content:
            editor_value = st.session_state.sql_content.decode('utf-8')
        st_ace(value=editor_value, language="sql", theme="github", readonly=True, key=f"sql_content_editor_{hash(st.session_state.sql_content)}")
