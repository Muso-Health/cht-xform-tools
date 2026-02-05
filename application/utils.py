# This file contains shared utility functions for the application layer.

# A centralized dictionary for main BigQuery view name exceptions.
_VIEW_NAME_EXCEPTIONS = {
    "MALI": {
        "patient_assessment": "formview_assessment",
        "patient_assessment_over_5": "formview_assessment_over_5",
        "referral_followup_under_5": "formview_referral_followup_under5",
        "treatment_followup": "formview_treatment_follow_up",
        "prenatal_followup": "formview_prenatal",
        "behavior_change": "formview_behaviour_change"
    },
    "RCI": {
        "patient_assessment": "formview_assessment",
        "patient_assessment_over_5": "formview_assessment_over_5",
        "referral_followup_under_5": "formview_referral_followup_under5",
        "treatment_followup": "formview_treatment_followup",
        "prenatal_followup": "formview_prenatal"
    }
}

# A centralized dictionary for repeat group BigQuery view name exceptions.
_REPEAT_GROUP_VIEW_NAME_EXCEPTIONS = {
    "supervision_with_chw_proccm":{
      "s_patient_evaluation_list":"formview_supervision_with_chw_proccm_evaluations"
    },
    "supervision_without_chw_proccm": {
        "pregnant_women_list": "formview_supervision_without_chw_proccm_pregnants",
        "s_free_care_audit_repeat":"formview_supervision_without_chw_proccm_services"
    }
}

# A centralized dictionary for db-doc group BigQuery view name exceptions.
# The key is the db-doc group name, which is unique across all forms.
_DB_DOC_GROUP_VIEW_NAME_EXCEPTIONS = {
    "prescription_summary": "formview_stock_prescription_summary"
}

def get_view_name(country_code: str, form_id: str) -> str:
    if not form_id: return ""
    country_exceptions = _VIEW_NAME_EXCEPTIONS.get(country_code.upper(), {})
    return country_exceptions.get(form_id, f"formview_{form_id}")

def get_repeat_group_view_name(form_id: str, repeat_group_name: str) -> str:
    if form_id in _REPEAT_GROUP_VIEW_NAME_EXCEPTIONS and repeat_group_name in _REPEAT_GROUP_VIEW_NAME_EXCEPTIONS[form_id]:
        return _REPEAT_GROUP_VIEW_NAME_EXCEPTIONS[form_id][repeat_group_name]
    return f"formview_{form_id}_{repeat_group_name}"

def get_db_doc_group_view_name(form_id: str, group_name: str) -> str:
    """
    Gets the correct BigQuery view name for a db-doc group, applying exceptions.
    The lookup is simpler because db-doc group names are unique.
    """
    if group_name in _DB_DOC_GROUP_VIEW_NAME_EXCEPTIONS:
        return _DB_DOC_GROUP_VIEW_NAME_EXCEPTIONS[group_name]
    return f"formview_{form_id}_{group_name}"
