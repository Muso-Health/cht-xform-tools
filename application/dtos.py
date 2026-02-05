from dataclasses import dataclass, field
from typing import List, Tuple, Literal

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from domain.entities.RichCHTElement import RichCHTElement
from domain.entities.CHTElement import CHTElement

HandlingMethod = Literal['ARRAY_IN_MAIN_VIEW', 'SEPARATE_VIEW', 'NOT_FOUND']

@dataclass(frozen=True)
class FoundReferenceDTO:
    element_name: str
    json_path: str
    count: int
    lines: List[int]

@dataclass(frozen=True)
class NotFoundElementDTO:
    element_name: str
    json_path: str

@dataclass(frozen=True)
class RepeatGroupAuditResultDTO:
    repeat_group_name: str
    handling_method: HandlingMethod
    elements: List[CHTElement]
    not_found_elements: List[NotFoundElementDTO] = field(default_factory=list)

@dataclass(frozen=True)
class DbDocGroupAuditResultDTO:
    """DTO for the audit result of a single db-doc group."""
    group_name: str
    view_found: bool
    elements: List[CHTElement]
    not_found_elements: List[NotFoundElementDTO] = field(default_factory=list)

@dataclass(frozen=True)
class SingleFormComparisonResultDTO:
    form_id: str
    not_found_elements: List[NotFoundElementDTO] = field(default_factory=list)
    repeat_groups: List[RepeatGroupAuditResultDTO] = field(default_factory=list)
    db_doc_groups: List[DbDocGroupAuditResultDTO] = field(default_factory=list)

@dataclass(frozen=True)
class BulkAuditResultDTO:
    compared_forms: List[SingleFormComparisonResultDTO] = field(default_factory=list)
    missing_xlsforms: List[str] = field(default_factory=list)
    invalid_xlsforms: List[str] = field(default_factory=list)
    missing_views: List[str] = field(default_factory=list)

# --- Other DTOs (unchanged) ---
@dataclass(frozen=True)
class ComparisonResultDTO:
    founds: List[FoundReferenceDTO] = field(default_factory=list)
    not_founds: List[NotFoundElementDTO] = field(default_factory=list)
    not_found_bm_elements: List[NotFoundElementDTO] = field(default_factory=list)
@dataclass(frozen=True)
class CommitDTO:
    sha: str; author: str; date: str; message: str
@dataclass(frozen=True)
class WorkflowRunDTO:
    id: int; name: str; display_title: str; head_branch: str; head_sha: str; status: str; conclusion: str; actor_login: str; actor_avatar: str; created_at: str; html_url: str
@dataclass(frozen=True)
class ModifiedElementDTO:
    old_element: RichCHTElement; new_element: RichCHTElement; reason: str
@dataclass(frozen=True)
class XLSFormComparisonResultDTO:
    unchanged_elements: List[Tuple[RichCHTElement, RichCHTElement]] = field(default_factory=list)
    modified_elements: List[ModifiedElementDTO] = field(default_factory=list)
    new_elements: List[RichCHTElement] = field(default_factory=list)
    deleted_elements: List[RichCHTElement] = field(default_factory=list)
@dataclass(frozen=True)
class ParsedColumnDTO:
    column_name: str; json_path: str; sql_type: str
@dataclass(frozen=False)
class DataCatalogRowDTO:
    formview_name: str; xlsform_name: str; column_name: str; sql_type: str; json_path: str; odk_type: str; calculation: str = ""; label_fr: str = ""; label_en: str = ""; label_bm: str = ""
@dataclass(frozen=False)
class DataCatalogResultDTO:
    catalog_rows: List[DataCatalogRowDTO]
