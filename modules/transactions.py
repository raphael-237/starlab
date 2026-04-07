from .data_manager import load_data, save_data, get_next_id
from datetime import datetime

def add_transaction(examen_id: int, prescripteur_id: int, quantite_payee: int, quantite_gratuite: int, decade_id: int):
    data = load_data()
    new_id = get_next_id(data["transactions"])
    data["transactions"].append({
        "id": new_id,
        "examen_id": examen_id,
        "prescripteur_id": prescripteur_id,
        "quantite_payee": int(quantite_payee),
        "quantite_gratuite": int(quantite_gratuite),
        "decade_id": decade_id,
        "date_enregistrement": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_data(data)
    return True