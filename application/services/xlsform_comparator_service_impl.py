import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from application.contracts.xlsform_comparator_service import XLSFormComparatorService
from application.dtos import XLSFormComparisonResultDTO, ModifiedElementDTO
from domain.contracts.rich_xlsform_repository import RichXLSFormRepository
from domain.contracts.semantic_comparator_repository import SemanticComparatorRepository

class XLSFormComparatorServiceImpl(XLSFormComparatorService):
    """
    Concrete implementation of the XLSFormComparatorService.
    """
    def __init__(self, xlsform_repo: RichXLSFormRepository, semantic_repo: SemanticComparatorRepository):
        self._xlsform_repo = xlsform_repo
        self._semantic_repo = semantic_repo

    def compare_forms(
        self, 
        old_form_content: bytes, 
        new_form_content: bytes, 
        exclude_notes: bool, 
        exclude_inputs: bool, 
        exclude_prescription: bool,
        use_title_matching: bool,
        use_formula_matching: bool
    ) -> XLSFormComparisonResultDTO:
        
        old_elements = self._xlsform_repo.get_rich_elements_from_file(old_form_content)
        new_elements = self._xlsform_repo.get_rich_elements_from_file(new_form_content)

        # --- Filtering Logic ---
        if exclude_notes:
            old_elements = [el for el in old_elements if el.odk_type != 'note']
            new_elements = [el for el in new_elements if el.odk_type != 'note']
        if exclude_inputs:
            old_elements = [el for el in old_elements if not (el.json_path and el.json_path.startswith('$.inputs'))]
            new_elements = [el for el in new_elements if not (el.json_path and el.json_path.startswith('$.inputs'))]
        if exclude_prescription:
            old_elements = [el for el in old_elements if not (el.json_path and 'prescription_summary' in el.json_path)]
            new_elements = [el for el in new_elements if not (el.json_path and 'prescription_summary' in el.json_path)]

        # --- Comparison Logic ---
        old_elements_map = {el.path: el for el in old_elements if not el.group}
        new_elements_map = {el.path: el for el in new_elements if not el.group}

        unchanged = []
        modified = []
        
        # Layer 1: Match by identical path
        for path, old_el in list(old_elements_map.items()):
            if path in new_elements_map:
                new_el = new_elements_map[path]
                reason = ""
                if old_el.titles != new_el.titles: reason += "Reworded "
                if old_el.calculation != new_el.calculation: reason += "Calculation Changed"
                
                if reason:
                    modified.append(ModifiedElementDTO(old_el, new_el, reason.strip()))
                else:
                    unchanged.append((old_el, new_el))
                
                del old_elements_map[path]
                del new_elements_map[path]

        # Layer 2: Match by identical name
        old_by_name = {el.question_name: el for el in old_elements_map.values()}
        new_by_name = {el.question_name: el for el in new_elements_map.values()}
        for name, old_el in list(old_by_name.items()):
            if name in new_by_name:
                new_el = new_by_name[name]
                modified.append(ModifiedElementDTO(old_el, new_el, "Moved"))
                del old_elements_map[old_el.path]
                del new_elements_map[new_el.path]

        # Layer 3: Differentiated Semantic Matching (conditional on UI flags)
        if use_title_matching or use_formula_matching:
            for old_path, old_el in list(old_elements_map.items()):
                best_match = None
                match_reason = ""

                for new_path, new_el in new_elements_map.items():
                    # Case 1: For 'calculate' questions, compare formulas if enabled
                    if use_formula_matching and old_el.odk_type == 'calculate' and new_el.odk_type == 'calculate':
                        if self._semantic_repo.are_formulas_semantically_similar(old_el.calculation, new_el.calculation):
                            best_match = new_el
                            match_reason = "Reworded (Formula Match)"
                            break
                    # Case 2: For other questions, compare titles if enabled
                    elif use_title_matching and old_el.odk_type != 'calculate' and new_el.odk_type != 'calculate':
                        if self._semantic_repo.are_titles_semantically_similar(old_el.titles.get('fr'), new_el.titles.get('fr')):
                            best_match = new_el
                            match_reason = "Reworded (Title Match)"
                            break
                
                if best_match:
                    modified.append(ModifiedElementDTO(old_el, best_match, match_reason))
                    del old_elements_map[old_el.path]
                    del new_elements_map[best_match.path]

        return XLSFormComparisonResultDTO(
            unchanged_elements=unchanged,
            modified_elements=modified,
            new_elements=list(new_elements_map.values()),
            deleted_elements=list(old_elements_map.values())
        )
