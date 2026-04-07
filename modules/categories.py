from .data_manager import load_data, save_data, get_next_id

def add_categorie(nom: str, description: str = ""):
    data = load_data()
    new_id = get_next_id(data["categories"])
    data["categories"].append({
        "id": new_id,
        "nom": nom.strip(),
        "description": description.strip()
    })
    save_data(data)
    return True

def update_categories(categories_list):
    data = load_data()
    data["categories"] = categories_list
    save_data(data)