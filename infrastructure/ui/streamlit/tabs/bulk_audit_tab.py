import streamlit as st
from streamlit_tree_select import tree_select

from application.contracts.bulk_audit_service import BulkAuditService
from application.dtos import SingleFormComparisonResultDTO
from infrastructure.ui.streamlit.ui_utils import build_tree_from_results, _

def build_tab_bulk_audit(bulk_audit_service: BulkAuditService):
    st.header(_("Bulk Audit of CHT Forms"))
    if 'bulk_audit_result' not in st.session_state:
        st.session_state.bulk_audit_result = None

    def clear_audit_results():
        st.session_state.bulk_audit_result = None

    audit_country = st.selectbox(_("Select country to audit"), options=["MALI", "RCI"], on_change=clear_audit_results, key="refactor_audit_country_selector")

    if st.button(_("Run Full Audit"), key="refactor_run_full_audit"):
        with st.spinner(f"Running full audit for {audit_country}... This may take several minutes."):
            try:
                st.session_state.bulk_audit_result = bulk_audit_service.perform_audit(audit_country)
            except Exception as e:
                st.error(f"An error occurred during the audit: {e}")
    
    if st.session_state.bulk_audit_result:
        result_dto = st.session_state.bulk_audit_result
        st.subheader("Audit Summary")
        
        critical_forms_set = set()
        if result_dto.compared_forms:
            for form in result_dto.compared_forms:
                is_critical = False
                if any(rg.handling_method == 'NOT_FOUND' or rg.not_found_elements for rg in form.repeat_groups): is_critical = True
                if any(not dbg.view_found or dbg.not_found_elements for dbg in form.db_doc_groups): is_critical = True
                if not is_critical:
                    for item in form.not_found_elements:
                        if not item.json_path.startswith('$.inputs') and 'prescription_summary' not in item.json_path and not (audit_country == 'RCI' and item.element_name.endswith('_bm')):
                            is_critical = True; break
                if is_critical: critical_forms_set.add(form.form_id)
        
        critical_discrepancies_count = len(critical_forms_set) + len(result_dto.missing_views)
        total_audited_count = len(result_dto.compared_forms) + len(result_dto.missing_views) + len(result_dto.missing_xlsforms) + len(result_dto.invalid_xlsforms)
        ok_forms_count = total_audited_count - critical_discrepancies_count - len(result_dto.missing_xlsforms) - len(result_dto.invalid_xlsforms)

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: st.metric("OK Forms", value=ok_forms_count)
        with m2: st.metric("Forms with Discrepancies", value=critical_discrepancies_count)
        with m3: st.metric("XLSForms Missing in GitHub", value=len(result_dto.missing_xlsforms))
        with m4: st.metric("Invalid XLSForms (cannot be parsed)", value=len(result_dto.invalid_xlsforms))
        with m5: st.metric("Forms without a SQL View", value=len(result_dto.missing_views))

        for category, forms in [("XLSForms Missing in GitHub (master)", result_dto.missing_xlsforms), ("Invalid XLSForms (Failed to Parse)", result_dto.invalid_xlsforms), ("Forms without a SQL View", result_dto.missing_views)]:
            if forms:
                with st.expander(category):
                    for form_id in forms: st.error(f"- `{form_id}`")

        st.subheader("Detailed Comparison Results")
        all_audited_forms = result_dto.compared_forms + [SingleFormComparisonResultDTO(form_id=f) for f in result_dto.missing_views]

        for form_result in sorted(all_audited_forms, key=lambda x: x.form_id):
            if form_result.form_id in result_dto.missing_views: continue

            critical, inputs, prescription, bm = [], [], [], []
            for item in form_result.not_found_elements:
                if item.json_path.startswith('$.inputs'): inputs.append(item)
                elif 'prescription_summary' in item.json_path: prescription.append(item)
                elif audit_country == 'RCI' and item.element_name.endswith('_bm'): bm.append(item)
                else: critical.append(item)
            
            has_critical = bool(critical) or any(rg.handling_method == 'NOT_FOUND' or rg.not_found_elements for rg in form_result.repeat_groups) or any(not dbg.view_found or dbg.not_found_elements for dbg in form_result.db_doc_groups)
            has_any_issue = bool(form_result.not_found_elements or any(rg.handling_method == 'NOT_FOUND' or rg.not_found_elements for rg in form_result.repeat_groups) or any(not dbg.view_found or dbg.not_found_elements for dbg in form_result.db_doc_groups))

            with st.expander(f"{( '❌' if has_critical else '✅' )} {form_result.form_id}", expanded=has_any_issue):
                if not has_any_issue:
                    st.success("All form fields, repeats, and db-docs have corresponding SQL views and all elements are present.")
                
                # --- Main Body Results ---
                if critical:
                    st.write("Critical fields missing from main form:"); tree_select(build_tree_from_results(critical, icon="❌"), key=f"tree_critical_{form_result.form_id}")
                if inputs:
                    st.write("Non-critical missing fields (inputs group):"); tree_select(build_tree_from_results(inputs, icon="ℹ️"), key=f"tree_inputs_{form_result.form_id}")
                if prescription:
                    st.write("Non-critical missing fields (prescription_summary):"); tree_select(build_tree_from_results(prescription, icon="ℹ️"), key=f"tree_presc_{form_result.form_id}")
                if bm:
                    st.write("Non-critical missing fields (`_bm` for RCI):"); tree_select(build_tree_from_results(bm, icon="ℹ️"), key=f"tree_bm_{form_result.form_id}")

                # --- Repeat Group Results (Always Displayed) ---
                if form_result.repeat_groups:
                    st.divider(); st.subheader("Repeat Group Audits")
                    for res in form_result.repeat_groups:
                        if res.handling_method == 'NOT_FOUND':
                            st.error(f"❌ No view or ARRAY pattern found for repeat: `{res.repeat_group_name}`")
                            tree_select(build_tree_from_results(res.elements, icon="➡️"), key=f"tree_repeat_missing_{form_result.form_id}_{res.repeat_group_name}")
                        elif res.not_found_elements:
                            st.warning(f"⚠️ Handled as `{res.handling_method}` for `{res.repeat_group_name}`, but elements are missing:")
                            tree_select(build_tree_from_results(res.not_found_elements, icon="➡️"), key=f"tree_repeat_found_{form_result.form_id}_{res.repeat_group_name}")
                        else:
                            st.success(f"✅ Handled as `{res.handling_method}` for `{res.repeat_group_name}` and all elements are present.")
                
                # --- DB-Doc Group Results (Always Displayed) ---
                if form_result.db_doc_groups:
                    st.divider(); st.subheader("DB-Doc Group Audits")
                    for res in form_result.db_doc_groups:
                        if not res.view_found:
                            st.error(f"❌ View NOT found for db-doc group: `{res.group_name}`")
                            tree_select(build_tree_from_results(res.elements, icon="➡️"), key=f"tree_dbdoc_missing_{form_result.form_id}_{res.group_name}")
                        elif res.not_found_elements:
                            st.warning(f"⚠️ View found for `{res.group_name}`, but elements are missing:")
                            tree_select(build_tree_from_results(res.not_found_elements, icon="➡️"), key=f"tree_dbdoc_found_{form_result.form_id}_{res.group_name}")
                        else:
                            st.success(f"✅ View found for db-doc group: `{res.group_name}` and all elements are present.")
