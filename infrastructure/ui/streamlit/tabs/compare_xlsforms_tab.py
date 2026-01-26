import streamlit as st

from application.contracts.xlsform_comparator_service import XLSFormComparatorService
from infrastructure.ui.streamlit.ui_utils import _

def build_tab_compare_xlsforms(xlsform_comparator_service: XLSFormComparatorService):
    st.header(_("Compare Two Versions of an XLSForm"))

    if 'xls_comparison_result' not in st.session_state:
        st.session_state.xls_comparison_result = None

    def clear_xls_comparison_results():
        st.session_state.xls_comparison_result = None

    c1, c2 = st.columns(2)
    with c1:
        old_xls_file = st.file_uploader("Upload Old XLSForm", type=["xlsx"], key="refactor_old_xls_uploader", on_change=clear_xls_comparison_results)
    with c2:
        new_xls_file = st.file_uploader("Upload New XLSForm", type=["xlsx"], key="refactor_new_xls_uploader", on_change=clear_xls_comparison_results)

    st.divider()

    st.write("Exclusion Options:")
    opt1, opt2, opt3 = st.columns(3)
    with opt1:
        exclude_notes = st.checkbox("Exclude 'note' types", value=True, key="refactor_exclude_notes")
    with opt2:
        exclude_inputs = st.checkbox("Exclude 'inputs' group", value=True, key="refactor_exclude_inputs")
    with opt3:
        exclude_prescription = st.checkbox("Exclude 'prescription_summary' group", value=True, key="refactor_exclude_prescription")
    
    st.write("Semantic Matching Options (requires AI - may incur costs):")
    ai_opt1, ai_opt2 = st.columns(2)
    with ai_opt1:
        use_title_matching = st.checkbox("Use AI for title matching", value=False, key="refactor_use_title_matching")
    with ai_opt2:
        use_formula_matching = st.checkbox("Use AI for formula matching", value=False, key="refactor_use_formula_matching")


    if st.button("Compare XLSForms", key="refactor_compare_xlsforms_button"):
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
