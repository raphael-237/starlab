from .data_manager import load_data, save_data, get_next_id
from datetime import datetime

def add_transaction(examen_id: int, prescripteur_id: int, quantite_payee: int, quantite_gratuite: int, decade_id: int, patient_id: int = None):
    """
    Ajoute une transaction (avec ou sans patient associé)
    """
    data = load_data()
    new_id = get_next_id(data["transactions"])
    
    transaction = {
        "id": new_id,
        "examen_id": examen_id,
        "prescripteur_id": prescripteur_id,
        "quantite_payee": int(quantite_payee),
        "quantite_gratuite": int(quantite_gratuite),
        "decade_id": decade_id,
        "date_enregistrement": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Ajouter patient_id si fourni
    if patient_id is not None:
        transaction["patient_id"] = patient_id
    
    data["transactions"].append(transaction)
    save_data(data)
    return True

def add_transaction_group(patient_id: int, prescripteur_id: int, decade_id: int, examens: list):
    """
    Enregistre un groupe de transactions pour un même patient
    
    examens: list of dict [
        {"examen_id": int, "quantite_payee": int, "quantite_gratuite": int},
        ...
    ]
    """
    data = load_data()
    
    if "transactions" not in data:
        data["transactions"] = []
    
    group_id = get_next_id([t for t in data["transactions"] if t.get("group_id")])
    transaction_ids = []
    
    for examen in examens:
        new_id = get_next_id(data["transactions"])
        transaction = {
            "id": new_id,
            "group_id": group_id,
            "patient_id": patient_id,
            "prescripteur_id": prescripteur_id,
            "examen_id": examen["examen_id"],
            "quantite_payee": examen["quantite_payee"],
            "quantite_gratuite": examen["quantite_gratuite"],
            "decade_id": decade_id,
            "date_enregistrement": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        data["transactions"].append(transaction)
        transaction_ids.append(new_id)
    
    save_data(data)
    return transaction_ids

def get_patient_transactions(patient_id: int = None, group_id: int = None):
    """
    Récupère les transactions par patient ou par groupe
    """
    data = load_data()
    transactions = data.get("transactions", [])
    
    if patient_id:
        transactions = [t for t in transactions if t.get("patient_id") == patient_id]
    
    if group_id:
        transactions = [t for t in transactions if t.get("group_id") == group_id]
    
    return transactions

def get_transactions_with_details():
    """
    Récupère toutes les transactions avec les détails associés (patient, examen, prescripteur, décade)
    """
    data = load_data()
    
    # Créer des dictionnaires pour un accès rapide
    patients_dict = {p["id"]: p for p in data.get("patients", [])}
    examens_dict = {e["id"]: e for e in data["examens"]}
    prescripteurs_dict = {p["id"]: p["nom"] for p in data["prescripteurs"]}
    decades_dict = {d["id"]: d for d in data["decades"]}
    
    enriched_transactions = []
    for t in data["transactions"]:
        examen = examens_dict.get(t["examen_id"])
        if examen:
            enriched = {
                "id": t["id"],
                "group_id": t.get("group_id"),
                "patient": patients_dict.get(t.get("patient_id")),
                "prescripteur": prescripteurs_dict.get(t["prescripteur_id"], "Inconnu"),
                "examen_nom": examen["nom"],
                "examen_prix": examen["prix"],
                "quantite_payee": t["quantite_payee"],
                "quantite_gratuite": t["quantite_gratuite"],
                "montant": t["quantite_payee"] * examen["prix"],
                "decade": decades_dict.get(t["decade_id"]),
                "date_enregistrement": t["date_enregistrement"]
            }
            enriched_transactions.append(enriched)
    
    return enriched_transactions