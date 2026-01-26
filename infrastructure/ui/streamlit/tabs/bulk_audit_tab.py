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
                result = bulk_audit_service.perform_audit(audit_country)
                st.session_state.bulk_audit_result = result
            except Exception as e:
                st.error(f"An error occurred during the audit: {e}")
    
    if st.session_state.bulk_audit_result:
        result_dto = st.session_state.bulk_audit_result
        st.subheader("Audit Summary")
        
        critical_forms_set = set()
        if result_dto.compared_forms:
            for form in result_dto.compared_forms:
                for item in form.not_found_elements:
                    is_rci_bm = audit_country == 'RCI' and item.element_name.endswith('_bm')
                    is_inputs = item.json_path.startswith('$.inputs')
                    is_prescription = 'prescription_summary' in item.json_path
                    if not is_inputs and not is_prescription and not is_rci_bm:
                        critical_forms_set.add(form.form_id)
                        break 

        critical_discrepancies_count = len(critical_forms_set)
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

            critical_not_founds = []
            inputs_not_founds = []
            prescription_not_founds = []
            bm_not_founds = []

            for item in form_result.not_found_elements:
                is_rci_bm = audit_country == 'RCI' and item.element_name.endswith('_bm')
                is_inputs = item.json_path.startswith('$.inputs')
                is_prescription = 'prescription_summary' in item.json_path

                if is_inputs:
                    inputs_not_founds.append(item)
                elif is_prescription:
                    prescription_not_founds.append(item)
                elif is_rci_bm:
                    bm_not_founds.append(item)
                else:
                    critical_not_founds.append(item)
            
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
                            if tree:
                                tree_select(tree, key=f"refactor_audit_tree_ok_inputs_{form_result.form_id}")
                        if prescription_not_founds:
                            st.write("Missing fields (prescription_summary group):")
                            tree = build_tree_from_results(prescription_not_founds, icon="ℹ️")
                            if tree:
                                tree_select(tree, key=f"refactor_audit_tree_ok_presc_{form_result.form_id}")
                        if bm_not_founds:
                            st.write("Missing fields (`_bm` questions for RCI):")
                            tree = build_tree_from_results(bm_not_founds, icon="ℹ️")
                            if tree:
                                tree_select(tree, key=f"refactor_audit_tree_ok_bm_{form_result.form_id}")
            else:
                with st.expander(f"❌ {form_result.form_id} (Discrepancies Found)"):
                    if critical_not_founds:
                        st.write("Critical fields missing from BigQuery view:")
                        critical_tree = build_tree_from_results(critical_not_founds, icon="❌")
                        if critical_tree:
                            tree_select(critical_tree, key=f"refactor_audit_tree_critical_{form_result.form_id}")
                    
                    if inputs_not_founds:
                        st.write("Non-critical missing fields (inputs group):")
                        non_critical_tree = build_tree_from_results(inputs_not_founds, icon="ℹ️")
                        if non_critical_tree:
                            tree_select(non_critical_tree, key=f"refactor_audit_tree_non_critical_inputs_{form_result.form_id}")
                    
                    if prescription_not_founds:
                        st.write("Non-critical missing fields (prescription_summary group):")
                        non_critical_tree = build_tree_from_results(prescription_not_founds, icon="ℹ️")
                        if non_critical_tree:
                            tree_select(non_critical_tree, key=f"refactor_audit_tree_non_critical_presc_{form_result.form_id}")
                    
                    if bm_not_founds:
                        st.write("Non-critical missing fields (`_bm` questions for RCI):")
                        non_critical_tree = build_tree_from_results(bm_not_founds, icon="ℹ️")
                        if non_critical_tree:
                            tree_select(non_critical_tree, key=f"refactor_audit_tree_non_critical_bm_{form_result.form_id}")
