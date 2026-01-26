from dataclasses import dataclass, field
from typing import List, Tuple

# We need to import the new RichCHTElement for type hinting
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from domain.entities.RichCHTElement import RichCHTElement

@dataclass(frozen=True)
class FoundReferenceDTO:
    """Data Transfer Object for a found reference."""
    element_name: str
    json_path: str
    count: int
    lines: List[int]

@dataclass(frozen=True)
class NotFoundElementDTO:
    """Data Transfer Object for an element not found in the SQL."""
    element_name: str
    json_path: str

@dataclass(frozen=True)
class ComparisonResultDTO:
    """Data Transfer Object for the XLSForm vs SQL comparison result."""
    founds: List[FoundReferenceDTO] = field(default_factory=list)
    not_founds: List[NotFoundElementDTO] = field(default_factory=list)
    not_found_bm_elements: List[NotFoundElementDTO] = field(default_factory=list)

@dataclass(frozen=True)
class CommitDTO:
    """Data Transfer Object for a single commit in a file's history."""
    sha: str
    author: str
    date: str
    message: str

@dataclass(frozen=True)
class WorkflowRunDTO:
    """Data Transfer Object for a single GitHub Actions workflow run."""
    id: int
    name: str
    display_title: str
    head_branch: str
    head_sha: str
    status: str
    conclusion: str
    actor_login: str
    actor_avatar: str
    created_at: str
    html_url: str

@dataclass(frozen=True)
class SingleFormComparisonResultDTO:
    """DTO for the result of a single form's audit where discrepancies were found."""
    form_id: str
    not_found_elements: List[NotFoundElementDTO] = field(default_factory=list)

@dataclass(frozen=True)
class BulkAuditResultDTO:
    """DTO for the result of a full bulk audit."""
    compared_forms: List[SingleFormComparisonResultDTO] = field(default_factory=list)
    missing_xlsforms: List[str] = field(default_factory=list)
    missing_views: List[str] = field(default_factory=list)

# --- DTOs for XLSForm vs XLSForm Comparison ---
@dataclass(frozen=True)
class ModifiedElementDTO:
    """DTO for an element that was modified between two XLSForm versions."""
    old_element: RichCHTElement
    new_element: RichCHTElement
    reason: str # e.g., "Moved", "Reworded", "Calculation Changed"

@dataclass(frozen=True)
class XLSFormComparisonResultDTO:
    """DTO for the result of comparing two XLSForms."""
    unchanged_elements: List[Tuple[RichCHTElement, RichCHTElement]] = field(default_factory=list)
    modified_elements: List[ModifiedElementDTO] = field(default_factory=list)
    new_elements: List[RichCHTElement] = field(default_factory=list)
    deleted_elements: List[RichCHTElement] = field(default_factory=list)

# --- New DTOs for Data Catalog Feature ---

@dataclass(frozen=True)
class ParsedColumnDTO:
    """Represents a single column parsed from a SQL view."""
    column_name: str
    json_path: str
    sql_type: str

@dataclass(frozen=False) # Changed to mutable to allow for enrichment
class DataCatalogRowDTO:
    """Represents a single row in the final data catalog output."""
    formview_name: str
    xlsform_name: str
    column_name: str
    sql_type: str
    json_path: str
    odk_type: str
    calculation: str = "" # New field
    label_fr: str = ""
    label_en: str = ""
    label_bm: str = ""

@dataclass(frozen=False) # Changed to mutable to allow for enrichment
class DataCatalogResultDTO:
    """Holds the complete list of generated data catalog rows."""
    catalog_rows: List[DataCatalogRowDTO]
