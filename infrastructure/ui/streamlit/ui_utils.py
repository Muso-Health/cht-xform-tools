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

        # Remove leading '$.' to create a cleaner tree structure
        clean_path = item.json_path.lstrip('$.')
        path_parts = clean_path.split('.')

        current_level = tree
        current_path_list = []
        for i, part in enumerate(path_parts):
            current_path_list.append(part)
            current_path = '.'.join(current_path_list)

            # For the leaf node
            if i == len(path_parts) - 1:
                label = f"{part} ({item.element_name})"
                current_level[part] = {"label": label, "value": item.json_path, "icon": icon}
            # For intermediate nodes
            else:
                if part not in current_level:
                    current_level[part] = {"label": part, "value": current_path, "_children": {}}
                # Handle cases where a path part might already exist as a leaf
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
