from .data_manager import load_data, save_data, get_next_id
from datetime import datetime

def add_examen(nom: str, categorie_id: int, prix: float):
    data = load_data()
    new_id = get_next_id(data["examens"])
    data["examens"].append({
        "id": new_id,
        "nom": nom.strip(),
        "categorie_id": categorie_id,
        "prix": float(prix),
        "add_date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_data(data)
    return True

def update_examens(examens_list):
    data = load_data()
    data["examens"] = examens_list
    save_data(data)