import streamlit as st
import os
from typing import List, Dict, Any
from datetime import datetime

from streamlit_ace import st_ace
from streamlit_tree_select import tree_select

from application.contracts.form_comparator_service import FormComparatorService
from application.contracts.bulk_audit_service import BulkAuditService
from application.contracts.xlsform_comparator_service import XLSFormComparatorService
from domain.contracts.code_repository import CodeRepository
from domain.contracts.cicd_repository import CICDRepository
from domain.contracts.data_warehouse_repository import DataWarehouseRepository
from domain.contracts.xform_api_repository import XFormApiRepository
from application.dtos import FoundReferenceDTO, NotFoundElementDTO, SingleFormComparisonResultDTO

# --- Internationalization Setup ---
import gettext
import locale

DOMAIN = 'streamlit_app'
UI_DIR = os.path.dirname(__file__)
LOCALE_DIR = os.path.join(UI_DIR, 'locale')

_ = lambda s: s

try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    pass

try:
    lang = gettext.translation(DOMAIN, localedir=LOCALE_DIR, languages=['en'], fallback=True)
    lang.install()
    _ = lang.gettext
except Exception as e:
    print(f"Warning: Could not initialize gettext translations. Using fallback. Error: {e}")

# --- End Internationalization Setup ---

def build_tree_from_results(results: List[Any], icon: str) -> List[Dict[str, Any]]:
    tree = {}
    for item in results:
        path_parts = item.json_path.split('.')
        current_level = tree
        current_path_list = []
        for i, part in enumerate(path_parts):
            current_path_list.append(part)
            current_path = '.'.join(current_path_list)
            if i == len(path_parts) - 1:
                label = f"{part} ({item.json_path})"
                if isinstance(item, FoundReferenceDTO):
                    label += f" - Found {item.count} times on lines: {item.lines}"
                current_level[part] = {"label": label, "value": item.json_path, "icon": icon}
            else:
                if part not in current_level:
                    current_level[part] = {"label": part, "value": current_path, "_children": {}}
                current_level = current_level[part]["_children"]

    def dict_to_list(node: Dict[str, Any]) -> List[Dict[str, Any]]:
        res = []
        for key, value in node.items():
            if key == "_children": continue
            child_nodes = value.get("_children", {})
            new_node = {"label": value["label"], "value": value["value"]}
            if "icon" in value: new_node["icon"] = value["icon"]
            if child_nodes: new_node["children"] = dict_to_list(child_nodes)
            res.append(new_node)
        return res

    return dict_to_list(tree)

def build_ui(
    comparator_service: FormComparatorService, 
    bulk_audit_service: BulkAuditService,
    xlsform_comparator_service: XLSFormComparatorService,
    code_repository: CodeRepository, 
    cicd_repository: CICDRepository, 
    data_warehouse_repository: DataWarehouseRepository, 
    xform_api_repository: XFormApiRepository
):
    st.set_page_config(layout="wide")
    st.title(_("XLSForm Data Source Tools"))

    tab1, tab2, tab3, tab4, tab5 = st.tabs([_("XLSForm SQL Comparator"), _("XLSForm Deploy History"), _("Generate XForm SQL"), _("Bulk Audit"), _("Compare Two XLSForms")])

    # --- TAB 1: XLSForm SQL Comparator ---
    with tab1:
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
            xls_source_option = st.radio("XLSForm Source", ["Upload File", "Fetch from GitHub"], horizontal=True, key="comparator_xls_source", on_change=clear_comparator_results, label_visibility="collapsed")
            
            uploaded_xls = None
            form_name_input = None
            country_options_map = {"MALI": "muso-mali/forms/app/", "RCI": "muso-cdi/forms/app/"}
            selected_country_label = st.selectbox(_("Select the country"), options=list(country_options_map.keys()), on_change=clear_comparator_results, key="comparator_country_selector")

            if xls_source_option == "Upload File":
                uploaded_xls = st.file_uploader(_("Upload your XLSForm (.xlsx)"), type=["xlsx"], key="comparator_xls_uploader", on_change=clear_comparator_results)
            else:
                form_name_input = st.text_input(_("Enter the XForm file name (without extension)"), on_change=clear_comparator_results, key="comparator_form_name")

            st.divider()

            st.subheader(_("SQL Source"))
            sql_input_option = st.radio("SQL Source", ["Upload File", "Fetch from BigQuery"], horizontal=True, key="comparator_sql_source", on_change=clear_comparator_results, label_visibility="collapsed")

            if sql_input_option == "Upload File":
                uploaded_sql_file = st.file_uploader(_("Upload your SQL file (.sql)"), type=["sql"], key="comparator_sql_uploader", on_change=clear_comparator_results)
                if uploaded_sql_file:
                    st.session_state.sql_content = uploaded_sql_file.getvalue()
            else:
                default_bq_project = "musoitproducts"
                default_bq_dataset = "cht_mali_prod" if selected_country_label == "MALI" else "cht_rci_prod"
                default_bq_view = f"formview_{form_name_input}" if form_name_input else ""
                bq_project_id = st.text_input("BigQuery Project ID", value=default_bq_project, key="comparator_bq_project", on_change=clear_comparator_results)
                bq_dataset_id = st.text_input("BigQuery Dataset ID", value=default_bq_dataset, key="comparator_bq_dataset", on_change=clear_comparator_results)
                bq_view_id = st.text_input("BigQuery View ID", value=default_bq_view, key="comparator_bq_view", on_change=clear_comparator_results)
                if st.button("Fetch View SQL", key="comparator_fetch_sql"):
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

            if st.button("Compare XLSForm and SQL", key="comparator_compare_button"):
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
                    if not result_dto.founds and not result_dto.not_founds and not result_dto.not_found_bm_elements:
                        st.success(_("No JSON paths found in the form to compare."))
                    else:
                        if result_dto.not_founds:
                            st.subheader(_("Not Found (Critical)"))
                            not_found_tree = build_tree_from_results(result_dto.not_founds, icon="❌")
                            tree_select(not_found_tree)
                        if result_dto.not_found_bm_elements:
                            st.subheader(_("Not Found `_bm` Elements (RCI Only)"))
                            bm_tree = build_tree_from_results(result_dto.not_found_bm_elements, icon="ℹ️")
                            tree_select(bm_tree)
                        if result_dto.founds:
                            st.subheader(_("Found in SQL"))
                            found_tree = build_tree_from_results(result_dto.founds, icon="✅")
                            tree_select(found_tree)

        with col2:
            st.header(_("SQL Content"))
            editor_value = ""
            editor_language = "text"
            editor_key = "sql_content_editor_empty"
            if st.session_state.sql_content:
                editor_value = st.session_state.sql_content.decode('utf-8')
                editor_language = "sql"
                editor_key = f"sql_content_editor_{hash(st.session_state.sql_content)}"
            else:
                editor_value = _("SQL content will appear here once loaded.")
            
            st_ace(
                value=editor_value,
                language=editor_language,
                theme="github",
                readonly=True,
                key=editor_key
            )

    # --- TAB 2: XLSForm Deploy History ---
    with tab2:
        st.header(_("XLSForm Deploy History"))
        if 'deploy_history' not in st.session_state:
            st.session_state.deploy_history = None

        def clear_deploy_history():
            st.session_state.deploy_history = None

        history_country_label = st.selectbox(_("Select country for deploy history"), options=["MALI", "RCI"], on_change=clear_deploy_history, key="history_country_selector")

        if st.button(_("Fetch Deploy History"), key="fetch_deploy_history"):
            filter_string = "production_muso" if history_country_label == "MALI" else "production_cdi"
            with st.spinner(f"Fetching deployment history for {history_country_label}..."):
                try:
                    all_runs = cicd_repository.get_workflow_runs()
                    filtered_runs = [run for run in all_runs if filter_string in run.display_title]
                    sorted_runs = sorted(filtered_runs, key=lambda run: datetime.fromisoformat(run.created_at.replace('Z', '+00:00')), reverse=True)
                    st.session_state.deploy_history = sorted_runs
                except Exception as e:
                    st.error(f"Failed to fetch deploy history: {e}")

        if st.session_state.deploy_history:
            st.subheader(f"Production Deployments for {history_country_label}")
            for run in st.session_state.deploy_history:
                with st.container(key=f"run_container_{run.id}"):
                    date_obj = datetime.fromisoformat(run.created_at.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S UTC")
                    c1, c2 = st.columns([0.7, 0.3])
                    with c1:
                        st.markdown(f"[{run.display_title}]({run.html_url})", unsafe_allow_html=True)
                        st.caption(f"{run.head_branch} @ {run.head_sha[:7]}")
                    with c2:
                        st.markdown(f"**{run.status.title()} / {run.conclusion.title()}**")
                        st.caption(formatted_date)
                    st.divider()

    # --- TAB 3: Generate XForm SQL ---
    with tab3:
        st.header(_("Generate XForm SQL"))
        if 'generated_sql' not in st.session_state:
            st.session_state.generated_sql = None
        
        def clear_generated_sql():
            st.session_state.generated_sql = None

        gen_sql_country = st.selectbox(_("Select country"), options=["MALI", "RCI"], on_change=clear_generated_sql, key="gen_sql_country")
        gen_sql_form_name = st.text_input(_("Enter XForm name"), on_change=clear_generated_sql, key="gen_sql_form_name")

        if st.button(_("Fetch Generated SQL"), key="fetch_generated_sql"):
            if gen_sql_country and gen_sql_form_name:
                with st.spinner(f"Generating SQL for {gen_sql_form_name} in {gen_sql_country}..."):
                    try:
                        generated_sql = xform_api_repository.get_bigquery_extraction_sql(gen_sql_country, gen_sql_form_name)
                        st.session_state.generated_sql = generated_sql
                    except Exception as e:
                        st.error(f"Failed to generate SQL: {e}")
            else:
                st.warning("Please provide both a country and an XForm name.")

        if st.session_state.generated_sql:
            st.subheader(f"Generated SQL for {gen_sql_form_name}")
            editor_key = f"generated_sql_editor_{hash(st.session_state.generated_sql)}"
            st_ace(value=st.session_state.generated_sql, language="sql", theme="github", readonly=True, key=editor_key)

    # --- TAB 4: Bulk Audit ---
    with tab4:
        st.header(_("Bulk Audit of CHT Forms"))
        if 'bulk_audit_result' not in st.session_state:
            st.session_state.bulk_audit_result = None

        def clear_audit_results():
            st.session_state.bulk_audit_result = None

        audit_country = st.selectbox(_("Select country to audit"), options=["MALI", "RCI"], on_change=clear_audit_results, key="audit_country_selector")

        if st.button(_("Run Full Audit"), key="run_full_audit"):
            with st.spinner(f"Running full audit for {audit_country}... This may take several minutes."):
                try:
                    result = bulk_audit_service.perform_audit(audit_country)
                    st.session_state.bulk_audit_result = result
                except Exception as e:
                    st.error(f"An error occurred during the audit: {e}")
        
        if st.session_state.bulk_audit_result:
            result_dto = st.session_state.bulk_audit_result
            st.subheader("Audit Summary")
            
            critical_forms = {form.form_id for form in result_dto.compared_forms if any(item for item in form.not_found_elements if not item.json_path.startswith('$.inputs') and 'prescription_summary' not in item.json_path and not (audit_country == 'RCI' and item.element_name.endswith('_bm')))}
            critical_discrepancies_count = len(critical_forms)
            total_audited_count = len(result_dto.compared_forms) + len(result_dto.missing_views)
            ok_forms_count = total_audited_count - critical_discrepancies_count

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Forms with No Critical Discrepancies", value=ok_forms_count)
            with m2:
                st.metric("Forms with Critical Discrepancies", value=critical_discrepancies_count)
            with m3:
                st.metric("XLSForms Missing in GitHub (master)", value=len(result_dto.missing_xlsforms))
            with m4:
                st.metric("XForms without a SQL View", value=len(result_dto.missing_views))


            if result_dto.missing_xlsforms:
                with st.expander("XLSForms Missing in GitHub (master)"):
                    for form_id in result_dto.missing_xlsforms:
                        st.warning(f"- `{form_id}`")
            
            if result_dto.missing_views:
                with st.expander("XForms without a SQL View"):
                    for form_id in result_dto.missing_views:
                        st.error(f"- `{form_id}`")

            st.subheader("Detailed Comparison Results")
            all_audited_forms = result_dto.compared_forms + [SingleFormComparisonResultDTO(form_id=f) for f in result_dto.missing_views]

            for form_result in sorted(all_audited_forms, key=lambda x: x.form_id):
                if form_result.form_id in result_dto.missing_views:
                    continue

                critical_not_founds = [item for item in form_result.not_found_elements if not item.json_path.startswith('$.inputs') and 'prescription_summary' not in item.json_path and not (audit_country == 'RCI' and item.element_name.endswith('_bm'))]
                inputs_not_founds = [item for item in form_result.not_found_elements if item.json_path.startswith('$.inputs')]
                prescription_not_founds = [item for item in form_result.not_found_elements if 'prescription_summary' in item.json_path]
                bm_not_founds = [item for item in form_result.not_found_elements if audit_country == 'RCI' and item.element_name.endswith('_bm')]
                has_critical_discrepancies = bool(critical_not_founds)

                if not has_critical_discrepancies:
                    with st.expander(f"✅ {form_result.form_id} (OK)"):
                        if not form_result.not_found_elements:
                            st.success("All form fields are present in the BigQuery view.")
                        else:
                            st.info("All missing fields are non-critical.")
                            if inputs_not_founds:
                                st.write("Missing fields (inputs group):")
                                tree = build_tree_from_results(inputs_not_founds, icon="ℹ️")
                                tree_select(tree, key=f"audit_tree_ok_inputs_{form_result.form_id}")
                            if prescription_not_founds:
                                st.write("Missing fields (prescription_summary group):")
                                tree = build_tree_from_results(prescription_not_founds, icon="ℹ️")
                                tree_select(tree, key=f"audit_tree_ok_presc_{form_result.form_id}")
                            if bm_not_founds:
                                st.write("Missing fields (`_bm` questions for RCI):")
                                tree = build_tree_from_results(bm_not_founds, icon="ℹ️")
                                tree_select(tree, key=f"audit_tree_ok_bm_{form_result.form_id}")
                else:
                    with st.expander(f"❌ {form_result.form_id} (Discrepancies Found)"):
                        if critical_not_founds:
                            st.write("Critical fields missing from BigQuery view:")
                            critical_tree = build_tree_from_results(critical_not_founds, icon="❌")
                            tree_select(critical_tree, key=f"audit_tree_critical_{form_result.form_id}")
                        
                        if inputs_not_founds:
                            st.write("Non-critical missing fields (inputs group):")
                            non_critical_tree = build_tree_from_results(inputs_not_founds, icon="ℹ️")
                            tree_select(non_critical_tree, key=f"audit_tree_non_critical_inputs_{form_result.form_id}")
                        
                        if prescription_not_founds:
                            st.write("Non-critical missing fields (prescription_summary group):")
                            non_critical_tree = build_tree_from_results(prescription_not_founds, icon="ℹ️")
                            tree_select(non_critical_tree, key=f"audit_tree_non_critical_presc_{form_result.form_id}")
                        
                        if bm_not_founds:
                            st.write("Non-critical missing fields (`_bm` questions for RCI):")
                            non_critical_tree = build_tree_from_results(bm_not_founds, icon="ℹ️")
                            tree_select(non_critical_tree, key=f"audit_tree_non_critical_bm_{form_result.form_id}")

    # --- TAB 5: Compare Two XLSForms ---
    with tab5:
        st.header(_("Compare Two Versions of an XLSForm"))

        if 'xls_comparison_result' not in st.session_state:
            st.session_state.xls_comparison_result = None

        def clear_xls_comparison_results():
            st.session_state.xls_comparison_result = None

        c1, c2 = st.columns(2)
        with c1:
            old_xls_file = st.file_uploader("Upload Old XLSForm", type=["xlsx"], key="old_xls_uploader", on_change=clear_xls_comparison_results)
        with c2:
            new_xls_file = st.file_uploader("Upload New XLSForm", type=["xlsx"], key="new_xls_uploader", on_change=clear_xls_comparison_results)

        st.divider()

        st.write("Exclusion Options:")
        opt1, opt2, opt3 = st.columns(3)
        with opt1:
            exclude_notes = st.checkbox("Exclude 'note' types", value=True, key="exclude_notes")
        with opt2:
            exclude_inputs = st.checkbox("Exclude 'inputs' group", value=True, key="exclude_inputs")
        with opt3:
            exclude_prescription = st.checkbox("Exclude 'prescription_summary' group", value=True, key="exclude_prescription")
        
        st.write("Semantic Matching Options (requires AI - may incur costs):")
        ai_opt1, ai_opt2 = st.columns(2)
        with ai_opt1:
            use_title_matching = st.checkbox("Use AI for title matching", value=False, key="use_title_matching")
        with ai_opt2:
            use_formula_matching = st.checkbox("Use AI for formula matching", value=False, key="use_formula_matching")


        if st.button("Compare XLSForms", key="compare_xlsforms_button"):
            if old_xls_file and new_xls_file:
                with st.spinner("Comparing XLSForms..."):
                    try:
                        old_content = old_xls_file.getvalue()
                        new_content = new_xls_file.getvalue()
                        result = xlsform_comparator_service.compare_forms(
                            old_form_content=old_content, 
                            new_form_content=new_content,
                            exclude_notes=exclude_notes,
                            exclude_inputs=exclude_inputs,
                            exclude_prescription=exclude_prescription,
                            use_title_matching=use_title_matching,
                            use_formula_matching=use_formula_matching
                        )
                        st.session_state.xls_comparison_result = result
                    except Exception as e:
                        st.error(f"An error occurred during comparison: {e}")
            else:
                st.warning("Please upload both XLSForm files to compare.")

        if st.session_state.xls_comparison_result:
            result = st.session_state.xls_comparison_result
            st.subheader("Comparison Report")

            if result.modified_elements:
                with st.expander(f"📝 Modified Elements ({len(result.modified_elements)})", expanded=True):
                    for item in result.modified_elements:
                        st.markdown(f"**`{item.old_element.question_name}`** - Reason: `{item.reason}`")
                        st.code(f"Old Path: {item.old_element.path}\nNew Path: {item.new_element.path}", language="text")
                        st.divider()

            if result.new_elements:
                with st.expander(f"➕ New Elements ({len(result.new_elements)})", expanded=True):
                    for item in result.new_elements:
                        st.success(f"- `{item.path}` ({item.json_path})")

            if result.deleted_elements:
                with st.expander(f"➖ Deleted Elements ({len(result.deleted_elements)})", expanded=True):
                    for item in result.deleted_elements:
                        st.error(f"- `{item.path}` ({item.json_path})")

            if result.unchanged_elements:
                with st.expander(f"✅ Unchanged Elements ({len(result.unchanged_elements)})"):
                    for item in result.unchanged_elements:
                        st.success(f"- `{item[0].path}` ({item[0].json_path})")
