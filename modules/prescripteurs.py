from .data_manager import load_data, save_data, get_next_id

def add_prescripteur(nom_complet: str, service: str):
    """Ajoute un prescripteur avec le titre déjà inclus (Dr. ou Mme.)"""
    data = load_data()
    new_id = get_next_id(data["prescripteurs"])
    
    data["prescripteurs"].append({
        "id": new_id,
        "nom": nom_complet.strip(),
        "service": service.strip()
    })
    save_data(data)
    return True

def update_prescripteurs(prescripteurs_list):
    data = load_data()
    data["prescripteurs"] = prescripteurs_list
    save_data(data)