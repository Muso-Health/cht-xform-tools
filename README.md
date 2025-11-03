# XLSForm Data Source Tools

This Streamlit application provides a suite of tools for developers and data analysts to audit, compare, and manage XLSForm data sources, particularly for CHT (Community Health Toolkit) applications.

## 1. Setup and Installation

### Prerequisites

1.  **Python 3.10+**
2.  **Environment Variables**: The application relies on environment variables for authentication. Create a `.env` file in the project root or set these in your shell:
    ```bash
    # For GitHub API access (required for most features)
    export GITHUB_PAT="your_github_personal_access_token"

    # For CHT API access (required for Bulk Audit)
    export CHT_MALI_USERNAME="your_mali_cht_username"
    export CHT_MALI_PASSWORD="your_mali_cht_password"
    export CHT_RCI_USERNAME="your_rci_cht_username"
    export CHT_RCI_PASSWORD="your_rci_cht_password"
    ```
3.  **Google Cloud Authentication**: For features involving BigQuery or Vertex AI, you must be authenticated with GCP.
    ```bash
    gcloud auth application-default login
    ```

### Installation

1.  Clone the repository.
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

From the project root directory, run:
```bash
streamlit run main.py
```

---

## 2. How to Use the Application (Features)

The application is organized into five main tabs:

### Tab 1: XLSForm SQL Comparator

-   **Purpose**: Compare the data fields from a single XLSForm against a corresponding BigQuery view or SQL file to find discrepancies.
-   **How to Use**: 
    1.  Select the country (MALI or RCI).
    2.  Provide the XLSForm by either uploading it or fetching it from GitHub by name.
    3.  Provide the SQL by either uploading a `.sql` file or fetching the view definition directly from BigQuery.
    4.  Click "Compare XLSForm and SQL".
-   **Results**: The results are categorized into "Found", "Not Found (Critical)", and non-critical sections like "Not Found `_bm` Elements" for RCI.

### Tab 2: XLSForm Deploy History

-   **Purpose**: View the recent production deployment history from GitHub Actions.
-   **How to Use**: Select the country (MALI or RCI) and click "Fetch Deploy History".

### Tab 3: Generate XForm SQL

-   **Purpose**: Generate the BigQuery extraction SQL for a given XForm using a backend Cloud Function.
-   **How to Use**: Select the country, enter the XForm name (without the `.xml` extension), and click "Fetch Generated SQL".

### Tab 4: Bulk Audit

-   **Purpose**: Run a comprehensive audit of all forms installed in a CHT instance against their corresponding XLSForms in GitHub and their views in BigQuery.
-   **How to Use**: Select the country and click "Run Full Audit". This may take several minutes.
-   **Results**: The summary provides a high-level overview with metrics. The detailed results show each form's status (✅ for OK, ❌ for discrepancies) and allow you to inspect any missing fields.

### Tab 5: Compare Two XLSForms

-   **Purpose**: Perform a detailed, semantic "diff" between two different versions of an XLSForm file to understand what has changed.
-   **How to Use**:
    1.  Upload the "Old" and "New" versions of the XLSForm file.
    2.  Select the comparison options:
        -   **Exclusion Options**: Check these to ignore common, non-critical changes (e.g., `note` types).
        -   **Semantic Matching**: Check these to use Vertex AI to find fields that were moved or reworded. This is powerful but may incur costs.
    3.  Click "Compare XLSForms".
-   **Results**: The report categorizes all changes into "Modified" (with a reason), "New", "Deleted", and "Unchanged" elements.

---

## 3. Testing the Application

The project uses `pytest` for testing. The tests are separated into fast **unit tests** (which run in isolation) and slow **integration tests** (which make real API calls).

### Setup

Install pytest:
```bash
pip install pytest
```

### Running Tests

All commands should be run from the project root directory.

**1. Run All Tests**

This runs all unit and integration tests. Requires all environment variables and authentication to be correctly configured.
```bash
pytest
```

**2. Run Only Fast Unit Tests (Recommended for Development)**

This is the most common command. It runs only the fast tests that do not require network access, providing quick feedback.
```bash
pytest -m "not integration"
```

**3. Run Only Slow Integration Tests**

This runs only the tests that make real API calls to GitHub and Google Cloud. Use this to verify connectivity and external API behavior.
```bash
pytest -m "integration"
```
