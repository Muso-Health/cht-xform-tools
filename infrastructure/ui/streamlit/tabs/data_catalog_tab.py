import streamlit as st
import pandas as pd

from application.contracts.data_catalog_service import DataCatalogService
from application.contracts.data_catalog_enrichment_service import DataCatalogEnrichmentService
from infrastructure.ui.streamlit.ui_utils import _

def build_tab_data_catalog(
    data_catalog_service: DataCatalogService, 
    data_catalog_enrichment_service: DataCatalogEnrichmentService
):
    st.header("Data Catalog Generator")
    st.write("This tool generates a master mapping of all BigQuery columns to their original XLSForm labels.")

    if 'data_catalog_result' not in st.session_state:
        st.session_state.data_catalog_result = None

    country = st.selectbox("Select country to generate catalog for:", ["MALI", "RCI"], key="catalog_country")

    if st.button("Generate Data Catalog", key="generate_catalog_button"):
        with st.spinner(f"Generating catalog for {country}... This may take several minutes."):
            try:
                result_dto = data_catalog_service.generate_catalog(country)
                st.session_state.data_catalog_result = result_dto
                st.success("Data catalog generated successfully!")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state.data_catalog_result:
        result = st.session_state.data_catalog_result
        if result.catalog_rows:
            df = pd.DataFrame([row.__dict__ for row in result.catalog_rows])
            
            st.subheader("Generated Data Catalog")
            st.dataframe(df)

            # --- AI Enrichment Section ---
            st.divider()
            st.subheader("AI-Powered Description Generation")
            st.write("Enrich `calculate` fields that have empty descriptions.")

            form_options = ["All"] + sorted(df['formview_name'].unique())
            form_filter = st.selectbox("Filter by Form to Enrich:", form_options)

            enrich_mode = st.radio(
                "Enrichment Mode:",
                ("Fill missing descriptions only", "Overwrite all descriptions"),
                key="enrich_mode"
            )
            
            if st.button("Generate AI Descriptions", key="enrich_button"):
                mode_map = {
                    "Fill missing descriptions only": "fill",
                    "Overwrite all descriptions": "overwrite"
                }
                with st.spinner("Enriching catalog with AI descriptions... This may take time and incur costs."):
                    try:
                        enriched_result = data_catalog_enrichment_service.enrich_catalog(
                            catalog=st.session_state.data_catalog_result,
                            country_code=country,
                            mode=mode_map[enrich_mode],
                            form_filter=form_filter
                        )
                        st.session_state.data_catalog_result = enriched_result
                        st.success("Enrichment complete!")
                        # Rerun to update the dataframe with new descriptions
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"An error occurred during enrichment: {e}")

            # --- Download Button ---
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Catalog as CSV",
                data=csv,
                file_name=f"{country.lower()}_data_catalog.csv",
                mime="text/csv",
            )
        else:
            st.warning("No data catalog entries were generated. This might be due to missing forms or views.")
