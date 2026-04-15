import calendar
from .data_manager import load_data, save_data, get_next_id

MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
PERIODES = ["1ère décade", "2ème décade", "3ème décade"]

def generate_decades(annee: int):
    """
    Génère les décades pour une année donnée
    Ne supprime pas les décades existantes, ajoute seulement celles qui manquent
    """
    data = load_data()
    
    # Créer un set des décades existantes pour éviter les doublons
    existing_decades = set()
    for d in data.get("decades", []):
        key = f"{d['annee']}_{d['mois']}_{d['periode']}"
        existing_decades.add(key)
    
    count = 0
    for m in range(1, 13):
        for p in range(3):
            periode = PERIODES[p]
            
            # Créer la clé unique pour cette décade
            key = f"{annee}_{MOIS[m-1]}_{periode}"
            
            # Vérifier si la décade existe déjà
            if key not in existing_decades:
                if p == 0:
                    debut = f"{annee}-{m:02d}-01"
                    fin = f"{annee}-{m:02d}-10"
                elif p == 1:
                    debut = f"{annee}-{m:02d}-11"
                    fin = f"{annee}-{m:02d}-20"
                else:
                    last_day = calendar.monthrange(annee, m)[1]
                    debut = f"{annee}-{m:02d}-21"
                    fin = f"{annee}-{m:02d}-{last_day}"
                
                new_id = get_next_id(data["decades"])
                data["decades"].append({
                    "id": new_id,
                    "periode": periode,
                    "mois": MOIS[m-1],
                    "annee": annee,
                    "date_debut": debut,
                    "date_fin": fin,
                    "est_active": True  # Marquer comme active
                })
                count += 1
                existing_decades.add(key)
    
    if count > 0:
        save_data(data)
    
    return count

def get_all_decades():
    """
    Retourne toutes les décades (passées, présentes et futures)
    """
    data = load_data()
    return sorted(data.get("decades", []), key=lambda x: x["date_debut"])

def get_decades_by_year(year: int):
    """
    Récupère toutes les décades pour une année spécifique
    """
    data = load_data()
    return [d for d in data["decades"] if d["annee"] == year]

def get_decades_by_month(year: int, month: int):
    """
    Récupère toutes les décades pour un mois spécifique
    """
    data = load_data()
    month_name = MOIS[month-1]
    return [d for d in data["decades"] if d["annee"] == year and d["mois"] == month_name]