def get_select_options(items, display_key="nom"):
    """Retourne un dictionnaire {affichage: id} pour les selectbox"""
    return {item.get(display_key, f"ID {item.get('id')}"): item["id"] for item in items}