from .data_manager import load_data, save_data, get_next_id
from datetime import datetime

def get_next_patient_number_for_date(date=None):
    """
    Génère le prochain numéro d'ordre patient pour une date spécifique.
    Format: simple compteur qui repart à 1 chaque jour (1, 2, 3...)
    
    Parameters:
    - date: datetime.date ou string au format YYYY-MM-DD. Si None, utilise la date du jour
    """
    data = load_data()
    
    if date is None:
        today = datetime.now().strftime("%Y-%m-%d")
    else:
        if hasattr(date, 'strftime'):
            today = date.strftime("%Y-%m-%d")
        else:
            today = str(date)
    
    # Compter les patients enregistrés à cette date
    patients_this_day = [p for p in data.get("patients", []) 
                        if p.get("date_jour", "") == today]
    
    next_num = len(patients_this_day) + 1
    return next_num

def get_next_patient_number():
    """
    Génère le prochain numéro d'ordre patient pour la journée en cours.
    Format: simple compteur qui repart à 1 chaque jour (1, 2, 3...)
    """
    return get_next_patient_number_for_date(None)

def add_patient(sexe: str, age: int, date_enregistrement=None):
    """
    Ajoute un nouveau patient dans la base
    
    Parameters:
    - sexe: 'F' ou 'M'
    - age: int (âge en années)
    - date_enregistrement: datetime.date ou string (optionnel). 
                           Si None, utilise la date du jour
    """
    data = load_data()
    
    if "patients" not in data:
        data["patients"] = []
    
    # Déterminer la date d'enregistrement
    if date_enregistrement is None:
        enregistrement_date = datetime.now()
        date_jour = enregistrement_date.strftime("%Y-%m-%d")
        date_enregistrement_str = enregistrement_date.strftime("%Y-%m-%d %H:%M:%S")
    else:
        # Convertir la date si nécessaire
        if hasattr(date_enregistrement, 'strftime'):
            enregistrement_date = date_enregistrement
        elif isinstance(date_enregistrement, str):
            # Essayer de parser la string
            try:
                enregistrement_date = datetime.strptime(date_enregistrement, "%Y-%m-%d")
            except:
                enregistrement_date = datetime.now()
        else:
            enregistrement_date = datetime.now()
        
        date_jour = enregistrement_date.strftime("%Y-%m-%d")
        # L'heure est fixée à minuit pour les enregistrements rétroactifs
        date_enregistrement_str = f"{date_jour} 00:00:00"
    
    patient_id = get_next_id(data["patients"])
    numero_ordre = get_next_patient_number_for_date(date_jour)
    
    new_patient = {
        "id": patient_id,
        "numero_ordre": numero_ordre,
        "sexe": sexe.upper(),
        "age": age,
        "date_enregistrement": date_enregistrement_str,
        "date_jour": date_jour,
        "is_imported": False  # Flag pour identifier les patients importés
    }
    
    data["patients"].append(new_patient)
    save_data(data)
    
    return new_patient

def get_current_decade():
    """
    Détermine la décade actuelle en fonction de la date du jour
    """
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    for decade in data["decades"]:
        if decade["date_debut"] <= today <= decade["date_fin"]:
            return decade
    
    return None

def get_decade_for_date(date):
    """
    Détermine la décade correspondant à une date spécifique
    
    Parameters:
    - date: datetime.date ou string au format YYYY-MM-DD
    """
    data = load_data()
    
    if hasattr(date, 'strftime'):
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = str(date)
    
    for decade in data["decades"]:
        if decade["date_debut"] <= date_str <= decade["date_fin"]:
            return decade
    
    return None

def get_today_patients():
    """
    Récupère la liste des patients enregistrés aujourd'hui
    """
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    return [p for p in data.get("patients", []) 
            if p.get("date_jour") == today]

def get_patients_for_date(date):
    """
    Récupère la liste des patients enregistrés à une date spécifique
    
    Parameters:
    - date: datetime.date ou string au format YYYY-MM-DD
    """
    data = load_data()
    
    if hasattr(date, 'strftime'):
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = str(date)
    
    return [p for p in data.get("patients", []) 
            if p.get("date_jour") == date_str]

def get_patient_by_number_and_date(numero_ordre, date):
    """
    Récupère un patient par son numéro d'ordre et sa date
    
    Parameters:
    - numero_ordre: int
    - date: datetime.date ou string au format YYYY-MM-DD
    """
    patients = get_patients_for_date(date)
    
    for patient in patients:
        if patient.get("numero_ordre") == numero_ordre:
            return patient
    
    return None