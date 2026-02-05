import gettext
import locale
import os
from typing import List, Dict, Any

from application.dtos import FoundReferenceDTO

# --- Internationalization Setup ---
DOMAIN = 'streamlit_app'
UI_DIR = os.path.dirname(__file__)
LOCALE_DIR = os.path.join(UI_DIR, 'locale')

_ = lambda s: s

try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    pass

try:
    lang = gettext.translation(DOMAIN, localedir=LOCALE_DIR, languages=['en'], fallback=True)
    lang.install()
    _ = lang.gettext
except Exception as e:
    print(f"Warning: Could not initialize gettext translations. Using fallback. Error: {e}")

# --- End Internationalization Setup ---


def build_tree_from_results(results: List[Any], icon: str) -> List[Dict[str, Any]]:
    tree = {}
    for item in results:
        # Defensive check for json_path attribute
        if not hasattr(item, 'json_path') or not item.json_path:
            continue

        # Start with the full, valid JSONPath
        full_path = item.json_path
        
        # Create a clean version for splitting, without the root '$'
        clean_path = full_path
        if clean_path.startswith('$.'):
            clean_path = clean_path[2:]
        elif clean_path.startswith('$'):
            clean_path = clean_path[1:]

        path_parts = clean_path.split('.')
        
        current_level = tree
        # Track the path parts to build the value for intermediate nodes
        current_path_for_value = []
        for i, part in enumerate(path_parts):
            current_path_for_value.append(part)

            # For the leaf node, use the original full path
            if i == len(path_parts) - 1:
                label = f"{part} ({item.json_path})"
                current_level[part] = {"label": label, "value": full_path, "icon": icon}
            # For intermediate nodes
            else:
                if part not in current_level:
                    # Construct a valid, partial JSONPath for the value (e.g., '$.inputs.user')
                    intermediate_value = '$.' + '.'.join(current_path_for_value)
                    current_level[part] = {"label": part, "value": intermediate_value, "_children": {}}
                    current_level = current_level[part]["_children"]
                else:
                    # If the part already exists, just move to the next level
                    if "_children" not in current_level[part]:
                         current_level[part]["_children"] = {}
                    current_level = current_level[part]["_children"]


    def dict_to_list(node: Dict[str, Any]) -> List[Dict[str, Any]]:
        res = []
        for key, value in node.items():
            if key == "_children": continue
            child_nodes = value.get("_children", {})
            new_node = {"label": value["label"], "value": value["value"]}
            if "icon" in value: new_node["icon"] = value["icon"]
            if child_nodes: new_node["children"] = dict_to_list(child_nodes)
            res.append(new_node)
        return res

    return dict_to_list(tree)
