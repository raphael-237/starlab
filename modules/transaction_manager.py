from .data_manager import load_data, save_data, get_next_id
from datetime import datetime

def add_transaction(examen_id: int, prescripteur_id: int, quantite_payee: int, quantite_gratuite: int, decade_id: int, patient_id: int = None, prix_unitaire_applique: float = None, discount_percent: float = 0):
    """
    Ajoute une transaction (avec ou sans patient associé)
    
    Args:
        prix_unitaire_applique: Prix unitaire après réduction (optionnel)
        discount_percent: Pourcentage de réduction appliqué
    """
    data = load_data()
    new_id = get_next_id(data["transactions"])
    
    # Récupérer le prix de base de l'examen
    examen = next((e for e in data["examens"] if e["id"] == examen_id), None)
    if not examen:
        return False
    
    prix_base = examen["prix"]
    
    # Déterminer le prix unitaire à appliquer
    if prix_unitaire_applique is not None:
        prix_unitaire = prix_unitaire_applique
    elif discount_percent > 0:
        prix_unitaire = prix_base * (1 - discount_percent / 100)
        prix_unitaire = round(prix_unitaire)
    else:
        prix_unitaire = prix_base
    
    montant = quantite_payee * prix_unitaire
    
    transaction = {
        "id": new_id,
        "examen_id": examen_id,
        "prescripteur_id": prescripteur_id,
        "quantite_payee": int(quantite_payee),
        "quantite_gratuite": int(quantite_gratuite),
        "decade_id": decade_id,
        "prix_base": prix_base,
        "prix_unitaire": prix_unitaire,
        "discount_percent": discount_percent,
        "montant": montant,
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
        {
            "examen_id": int, 
            "quantite_payee": int, 
            "quantite_gratuite": int,
            "prix_unitaire_applique": float (optionnel),
            "discount_percent": float (optionnel)
        },
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
        
        # Récupérer le prix de base de l'examen
        examen_info = next((e for e in data["examens"] if e["id"] == examen["examen_id"]), None)
        prix_base = examen_info["prix"] if examen_info else 0
        
        # Déterminer le prix unitaire
        prix_unitaire = examen.get("prix_unitaire_applique")
        discount_percent = examen.get("discount_percent", 0)
        
        if prix_unitaire is None and discount_percent > 0:
            prix_unitaire = prix_base * (1 - discount_percent / 100)
            prix_unitaire = round(prix_unitaire)
        elif prix_unitaire is None:
            prix_unitaire = prix_base
        
        montant = examen["quantite_payee"] * prix_unitaire
        
        transaction = {
            "id": new_id,
            "group_id": group_id,
            "patient_id": patient_id,
            "prescripteur_id": prescripteur_id,
            "examen_id": examen["examen_id"],
            "quantite_payee": examen["quantite_payee"],
            "quantite_gratuite": examen["quantite_gratuite"],
            "decade_id": decade_id,
            "prix_base": prix_base,
            "prix_unitaire": prix_unitaire,
            "discount_percent": discount_percent,
            "montant": montant,
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
            # Utiliser le prix unitaire stocké ou le prix de base
            prix_affiche = t.get("prix_unitaire", examen["prix"])
            discount = t.get("discount_percent", 0)
            
            enriched = {
                "id": t["id"],
                "group_id": t.get("group_id"),
                "patient": patients_dict.get(t.get("patient_id")),
                "prescripteur": prescripteurs_dict.get(t["prescripteur_id"], "Inconnu"),
                "examen_nom": examen["nom"],
                "examen_prix_base": examen["prix"],
                "examen_prix_applique": prix_affiche,
                "discount_percent": discount,
                "quantite_payee": t["quantite_payee"],
                "quantite_gratuite": t["quantite_gratuite"],
                "montant": t.get("montant", t["quantite_payee"] * prix_affiche),
                "decade": decades_dict.get(t["decade_id"]),
                "date_enregistrement": t["date_enregistrement"]
            }
            enriched_transactions.append(enriched)
    
    return enriched_transactions

def get_transaction(transaction_id: int):
    """
    Récupère une transaction par son ID
    """
    data = load_data()
    for t in data["transactions"]:
        if t["id"] == transaction_id:
            return t
    return None

def update_transaction(transaction_id: int, **kwargs):
    """
    Met à jour une transaction
    """
    data = load_data()
    for i, t in enumerate(data["transactions"]):
        if t["id"] == transaction_id:
            for key, value in kwargs.items():
                if key in t:
                    t[key] = value
            # Recalculer le montant si nécessaire
            if "quantite_payee" in kwargs or "prix_unitaire" in kwargs:
                quantite = t.get("quantite_payee", 0)
                prix = t.get("prix_unitaire", 0)
                t["montant"] = quantite * prix
            save_data(data)
            return True
    return False

def delete_transaction(transaction_id: int):
    """
    Supprime une transaction
    """
    data = load_data()
    original_count = len(data["transactions"])
    data["transactions"] = [t for t in data["transactions"] if t["id"] != transaction_id]
    
    if len(data["transactions"]) < original_count:
        save_data(data)
        return True
    return False