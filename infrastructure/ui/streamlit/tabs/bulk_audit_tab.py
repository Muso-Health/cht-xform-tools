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
                if any(rg.handling_method == 'NOT_FOUND' or rg.not_found_elements for rg in form.repeat_groups):
                    critical_forms_set.add(form.form_id)
                    continue
                for item in form.not_found_elements:
                    is_rci_bm = audit_country == 'RCI' and item.element_name.endswith('_bm')
                    is_inputs = item.json_path.startswith('$.inputs')
                    is_prescription = 'prescription_summary' in item.json_path
                    if not is_inputs and not is_prescription and not is_rci_bm:
                        critical_forms_set.add(form.form_id)
                        break
        
        critical_discrepancies_count = len(critical_forms_set) + len(result_dto.missing_views)
        total_audited_count = len(result_dto.compared_forms) + len(result_dto.missing_views) + len(result_dto.missing_xlsforms) + len(result_dto.invalid_xlsforms)
        ok_forms_count = total_audited_count - critical_discrepancies_count - len(result_dto.missing_xlsforms) - len(result_dto.invalid_xlsforms)

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1: st.metric("OK Forms", value=ok_forms_count)
        with m2: st.metric("Forms with Discrepancies", value=critical_discrepancies_count)
        with m3: st.metric("XLSForms Missing in GitHub", value=len(result_dto.missing_xlsforms))
        with m4: st.metric("Invalid XLSForms (cannot be parsed)", value=len(result_dto.invalid_xlsforms))
        with m5: st.metric("Forms without a SQL View", value=len(result_dto.missing_views))

        if result_dto.missing_xlsforms:
            with st.expander("XLSForms Missing in GitHub (master)"):
                for form_id in result_dto.missing_xlsforms: st.warning(f"- `{form_id}`")
        if result_dto.invalid_xlsforms:
            with st.expander("Invalid XLSForms (Failed to Parse)"):
                for form_id in result_dto.invalid_xlsforms: st.error(f"- `{form_id}`")
        if result_dto.missing_views:
            with st.expander("Forms without a SQL View"):
                for form_id in result_dto.missing_views: st.error(f"- `{form_id}`")

        st.subheader("Detailed Comparison Results")
        all_audited_forms = result_dto.compared_forms + [SingleFormComparisonResultDTO(form_id=f) for f in result_dto.missing_views]

        for form_result in sorted(all_audited_forms, key=lambda x: x.form_id):
            if form_result.form_id in result_dto.missing_views: continue

            critical_not_founds, inputs_not_founds, prescription_not_founds, bm_not_founds = [], [], [], []
            for item in form_result.not_found_elements:
                if item.json_path.startswith('$.inputs'): inputs_not_founds.append(item)
                elif 'prescription_summary' in item.json_path: prescription_not_founds.append(item)
                elif audit_country == 'RCI' and item.element_name.endswith('_bm'): bm_not_founds.append(item)
                else: critical_not_founds.append(item)
            
            has_critical_discrepancies = bool(critical_not_founds) or any(rg.handling_method == 'NOT_FOUND' or rg.not_found_elements for rg in form_result.repeat_groups)

            if not has_critical_discrepancies and not form_result.not_found_elements:
                 with st.expander(f"✅ {form_result.form_id} (OK)", expanded=False):
                    st.success("All form fields and repeat groups have corresponding SQL views and all elements are present.")
            else:
                with st.expander(f"{( '❌' if has_critical_discrepancies else '✅' )} {form_result.form_id}", expanded=True):
                    if critical_not_founds:
                        st.write("Critical fields missing from main form:")
                        tree_select(build_tree_from_results(critical_not_founds, icon="❌"), key=f"tree_critical_{form_result.form_id}")
                    if inputs_not_founds:
                        st.write("Non-critical missing fields (inputs group):")
                        tree_select(build_tree_from_results(inputs_not_founds, icon="ℹ️"), key=f"tree_inputs_{form_result.form_id}")
                    if prescription_not_founds:
                        st.write("Non-critical missing fields (prescription_summary group):")
                        tree_select(build_tree_from_results(prescription_not_founds, icon="ℹ️"), key=f"tree_presc_{form_result.form_id}")
                    if bm_not_founds:
                        st.write("Non-critical missing fields (`_bm` questions for RCI):")
                        tree_select(build_tree_from_results(bm_not_founds, icon="ℹ️"), key=f"tree_bm_{form_result.form_id}")

                    if form_result.repeat_groups:
                        st.divider()
                        st.subheader("Repeat Group Audits")
                        for repeat_result in form_result.repeat_groups:
                            if repeat_result.handling_method == 'NOT_FOUND':
                                st.error(f"❌ No SQL view or ARRAY pattern found for repeat group: `{repeat_result.repeat_group_name}`")
                                st.write("The following elements should be in a view:")
                                tree_select(build_tree_from_results(repeat_result.elements, icon="➡️"), key=f"tree_repeat_missing_{form_result.form_id}_{repeat_result.repeat_group_name}")
                            elif repeat_result.not_found_elements:
                                message = f"⚠️ Handled as `{repeat_result.handling_method}`, but some elements are missing for `{repeat_result.repeat_group_name}`:"
                                st.warning(message)
                                tree_select(build_tree_from_results(repeat_result.not_found_elements, icon="➡️"), key=f"tree_repeat_found_{form_result.form_id}_{repeat_result.repeat_group_name}")
                            else:
                                message = f"✅ Handled as `{repeat_result.handling_method}` for repeat group: `{repeat_result.repeat_group_name}` and all elements are present."
                                st.success(message)
