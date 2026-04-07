import calendar
from .data_manager import load_data, save_data, get_next_id

MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
PERIODES = ["1ère décade", "2ème décade", "3ème décade"]

def generate_decades(annee: int):
    data = load_data()
    count = 0
    for m in range(1, 13):
        for p in range(3):
            periode = PERIODES[p]
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
                "date_fin": fin
            })
            count += 1
    save_data(data)
    return count