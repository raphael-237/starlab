from .data_manager import load_data
import pandas as pd
from collections import defaultdict

def get_statistiques_dataframe():
    data = load_data()
    if not data["transactions"]:
        return pd.DataFrame()

    examens = {e["id"]: e for e in data["examens"]}
    prescripteurs = {p["id"]: p["nom"] for p in data["prescripteurs"]}
    decades = {d["id"]: f"{d['periode']} - {d['mois']} {d['annee']}" for d in data["decades"]}
    categories = {c["id"]: c["nom"] for c in data["categories"]}

    records = []
    for t in data["transactions"]:
        ex = examens.get(t["examen_id"])
        if not ex:
            continue
        montant = t["quantite_payee"] * ex["prix"]
        records.append({
            "Décade": decades.get(t["decade_id"], "Inconnue"),
            "Examen": ex.get("nom", "?"),
            "Catégorie": categories.get(ex.get("categorie_id"), "?"),
            "Prescripteur": prescripteurs.get(t["prescripteur_id"], "?"),
            "Payé": t["quantite_payee"],
            "Gratuit": t["quantite_gratuite"],
            "Montant (FCFA)": round(montant, 2)
        })

    return pd.DataFrame(records)