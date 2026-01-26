import streamlit as st
from datetime import datetime

from domain.contracts.cicd_repository import CICDRepository
from infrastructure.ui.streamlit.ui_utils import _

def build_tab_deploy_history(cicd_repository: CICDRepository):
    st.header(_("XLSForm Deploy History"))
    if 'deploy_history' not in st.session_state:
        st.session_state.deploy_history = None

    def clear_deploy_history():
        st.session_state.deploy_history = None

    history_country_label = st.selectbox(_("Select country for deploy history"), options=["MALI", "RCI"], on_change=clear_deploy_history, key="refactor_history_country_selector")

    if st.button(_("Fetch Deploy History"), key="refactor_fetch_deploy_history"):
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
            with st.container(key=f"refactor_run_container_{run.id}"):
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
