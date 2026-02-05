# This file contains shared utility functions for the application layer.

def convert_odk_path_to_json_path(odk_path: str, is_in_repeat: bool = False) -> str:
    """
    Converts an ODK-style path to a CHT-style JSONPath.
    Example (main body): /form/group/q -> $.fields.group.q
    Example (repeat): /form/repeat/q -> $.q
    """
    path_segments = odk_path.strip('/').split('/')
    
    if len(path_segments) <= 1:
        return '$'

    # For paths inside a repeat, the JSON path is relative to the repeat object
    if is_in_repeat:
        # Path is /repeat_name/group/q -> we want $.group.q
        relevant_segments = path_segments[1:]
        return '$.' + '.'.join(relevant_segments)

    # For the main form body
    form_id = path_segments[0]
    main_segments = path_segments[1:]
    
    # Handle the special 'inputs' group
    if main_segments and main_segments[0] == 'inputs':
        return '$.' + '.'.join(main_segments)
    else:
        return '$.fields.' + '.'.join(main_segments)

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
    "supervision_with_chw_proccm": {
        "s_patient_evaluation_list": "formview_supervision_with_chw_proccm_evaluations"
    },
    "supervision_without_chw_proccm": {
        "pregnant_women_list": "formview_supervision_without_chw_proccm_pregnants",
        "s_free_care_audit_repeat":"formview_supervision_without_chw_proccm_services"
    }
}

def get_view_name(country_code: str, form_id: str) -> str:
    """
    Gets the correct main BigQuery view name for a given form_id.
    """
    if not form_id:
        return ""
    country_exceptions = _VIEW_NAME_EXCEPTIONS.get(country_code.upper(), {})
    return country_exceptions.get(form_id, f"formview_{form_id}")

def get_repeat_group_view_name(form_id: str, repeat_group_name: str) -> str:
    """
    Gets the correct BigQuery view name for a repeat group.
    """
    if form_id in _REPEAT_GROUP_VIEW_NAME_EXCEPTIONS:
        if repeat_group_name in _REPEAT_GROUP_VIEW_NAME_EXCEPTIONS[form_id]:
            return _REPEAT_GROUP_VIEW_NAME_EXCEPTIONS[form_id][repeat_group_name]
    
    return f"formview_{form_id}_{repeat_group_name}"
