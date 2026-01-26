import streamlit as st
from streamlit_ace import st_ace

from domain.contracts.xform_api_repository import XFormApiRepository
from infrastructure.ui.streamlit.ui_utils import _

def build_tab_generate_sql(xform_api_repository: XFormApiRepository):
    st.header(_("Generate XForm SQL"))
    if 'generated_sql' not in st.session_state:
        st.session_state.generated_sql = None
    
    def clear_generated_sql():
        st.session_state.generated_sql = None

    gen_sql_country = st.selectbox(_("Select country"), options=["MALI", "RCI"], on_change=clear_generated_sql, key="refactor_gen_sql_country")
    gen_sql_form_name = st.text_input(_("Enter XForm name"), on_change=clear_generated_sql, key="refactor_gen_sql_form_name")

    if st.button(_("Fetch Generated SQL"), key="refactor_fetch_generated_sql"):
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
        editor_key = f"refactor_generated_sql_editor_{hash(st.session_state.generated_sql)}"
        st_ace(value=st.session_state.generated_sql, language="sql", theme="github", readonly=True, key=editor_key)
