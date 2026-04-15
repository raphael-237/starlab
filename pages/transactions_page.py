import streamlit as st
import pandas as pd
from modules.data_manager import load_data, save_data
from modules.patient_manager import add_patient, get_current_decade, get_next_patient_number, get_today_patients, get_next_patient_number_for_date, get_patients_for_date, get_decade_for_date
from modules.transaction_manager import add_transaction_group
from datetime import datetime
import time
import io
import re
from unicodedata import normalize

def reset_wizard():
    """Réinitialise complètement le wizard"""
    st.session_state.wizard_step = 1
    st.session_state.temp_patient = {}
    st.session_state.temp_examens = []
    st.session_state.prescripteur_selected = None
    st.session_state.last_exam_key = 0
    st.session_state.wizard_active = False
    st.session_state.custom_date = datetime.now().date()
    st.session_state.use_custom_date = False

def get_decade_from_date(annee: int, mois: int, jour: int):
    """
    Trouve la décade correspondant à une date donnée
    """
    data = load_data()
    date_str = f"{annee}-{mois:02d}-{jour:02d}"
    
    for decade in data["decades"]:
        if decade["date_debut"] <= date_str <= decade["date_fin"]:
            return decade
    return None

def parse_age(age_str):
    """
    Parse l'âge depuis différents formats:
    - "30 Ans" -> 30
    - "30 ans" -> 30
    - "30" -> 30
    - "11 mois" -> 0 (car moins d'un an)
    - "1 an" -> 1
    - "20 Ans, 6 mois" -> 20
    - "15 ans 3 mois" -> 15
    - "2 semaines" -> 0
    - "1 semaine" -> 0
    - "3 jours" -> 0
    """
    if age_str is None or pd.isna(age_str):
        return None
    
    age_str = str(age_str).strip().lower()
    
    # Vérifier si c'est en semaines ou jours (moins d'un an)
    if any(unit in age_str for unit in ['semaine', 'sem', 'jour', 'jr']):
        return 0
    
    # Extraire les années
    # Pattern pour trouver un nombre suivi de 'an' ou 'ans'
    year_pattern = r'(\d+)\s*(?:an|ans|année|années)'
    year_match = re.search(year_pattern, age_str)
    
    if year_match:
        return int(year_match.group(1))
    
    # Si pas d'années trouvées, chercher juste un nombre (si pas de mention de mois)
    if 'mois' not in age_str:
        # Chercher un nombre simple
        simple_number = re.search(r'(\d+)', age_str)
        if simple_number:
            return int(simple_number.group(1))
    
    # Si c'est uniquement des mois, retourner 0
    month_pattern = r'(\d+)\s*(?:mois|moi)'
    if re.search(month_pattern, age_str) and 'an' not in age_str:
        return 0
    
    return None

def parse_sexe(sexe_str):
    """
    Parse le sexe depuis différents formats:
    - "F", "Féminin", "FEMME", "FEMININ" -> "F"
    - "M", "Masculin", "HOMME", "MASCULIN" -> "M"
    """
    if sexe_str is None or pd.isna(sexe_str):
        return None
    
    sexe_str = str(sexe_str).strip().upper()
    
    if sexe_str in ['F', 'FEMININ', 'FEMME', 'FÉMININ']:
        return "F"
    elif sexe_str in ['M', 'MASCULIN', 'HOMME']:
        return "M"
    else:
        return None

def safe_int(value, default=None):
    """Convertit une valeur en entier de manière sécurisée"""
    if pd.isna(value):
        return default
    try:
        if isinstance(value, str):
            value = value.strip()
            # Enlever les espaces et caractères non numériques (sauf le signe moins)
            value = re.sub(r'[^\d-]', '', value)
            if value == '' or value == '-':
                return default
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_str(value, default=""):
    """Convertit une valeur en chaîne de manière sécurisée"""
    if pd.isna(value):
        return default
    return str(value).strip()

def has_any_data(row):
    """
    Vérifie si une ligne contient au moins une cellule avec des données
    """
    for cell in row:
        if pd.notna(cell) and str(cell).strip() and str(cell).strip() not in ['', 'nan', 'NaN', 'None']:
            return True
    return False

def find_data_rows(df, start_row=0):
    """
    Trouve toutes les lignes contenant des données (au moins une cellule non vide)
    Retourne la liste des indices des lignes avec données
    """
    data_rows = []
    for idx in range(start_row, len(df)):
        row = df.iloc[idx]
        if has_any_data(row):
            data_rows.append(idx)
    return data_rows

def import_transactions_from_file(uploaded_file):
    """
    Importe les transactions depuis un fichier Excel
    """
    from modules.data_manager import get_next_id
    
    data = load_data()
    
    # Dictionnaire de conversion des noms de mois
    mois_map = {
        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
        'juillet': 7, 'août': 8, 'aout': 8, 'septembre': 9, 'octobre': 10, 
        'novembre': 11, 'décembre': 12, 'decembre': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        'janv': 1, 'fevr': 2, 'févr': 2, 'avr': 4, 'juin': 6, 'juil': 7,
        'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    # Dictionnaire des abréviations d'examens (abrégé -> nom complet normalisé)
    exam_abbreviations = {
        'chlam': 'chlamydia',
        'creat': 'creatinine',
        'crp': 'crp',
        'nfs': 'nfs',
        'ge': 'ge',
        'pcv': 'pcv',
        'lav': 'lav',
        'bw': 'bw',
        'iono': 'ionogramme',
        'combi': 'combi11',
        'combi11': 'combi11',
        'gsrh': 'gsrh',
        'aslo': 'aslo',
        'hbs': 'hbs',
        'hcv': 'hcv',
        'hpylori': 'hpylori',
        'tord': 'tord',
        'wid al': 'widal',
        'widal': 'widal',
        'uree': 'uree',
        'glycemie': 'glycemie',
        'glycémie': 'glycemie',
        'bilirubine': 'bilirubine',
        'electrophorese': 'electrophorese',
        'électrophorèse': 'electrophorese',
        'kaliemie': 'kaliemie',
        'calcemie': 'calcemie',
        'toxoplasmose': 'toxoplasmose',
        'rubéole': 'rubeole',
        'rubiole': 'rubeole',
        'chlamydia': 'chlamydia',
        'selles': 'selle koap',
        'selle': 'selle koap',
        'sell es': 'selle koap'
    }
    
    # Lire le fichier Excel
    try:
        df = pd.read_excel(uploaded_file, header=None)
    except Exception as e:
        return False, f"Erreur de lecture du fichier: {str(e)}"
    
    # Vérifier le nombre de colonnes
    if df.shape[1] < 10:
        return False, f"Le fichier doit contenir 10 colonnes. {df.shape[1]} colonne(s) détectée(s)."
    
    # Détecter l'en-tête
    start_row = 0
    if len(df) > 0:
        first_row_value = str(df.iloc[0, 0]).lower().strip() if pd.notna(df.iloc[0, 0]) else ""
        header_keywords = ['annee', 'année', 'year', 'mois', 'month', 'jour', 'day', 
                           'numero', 'number', 'age', 'âge', 'sexe', 'prescripteur', 'examen', 'kit']
        if any(keyword in first_row_value for keyword in header_keywords):
            start_row = 1
    
    # Trouver toutes les lignes avec des données (au moins une cellule non vide)
    data_rows = find_data_rows(df, start_row)
    
    if not data_rows:
        return False, "Aucune ligne avec des données trouvée dans le fichier."
    
    # Créer la liste des lignes à traiter
    rows_to_process = [(idx, df.iloc[idx]) for idx in data_rows]
    
    # Dictionnaires existants (normalisés)
    examens_dict = {}
    for e in data["examens"]:
        nom_normalized = e["nom"].lower().strip()
        examens_dict[nom_normalized] = e
        # Ajouter sans accents
        nom_sans_accent = normalize('NFKD', nom_normalized).encode('ASCII', 'ignore').decode('ASCII')
        if nom_sans_accent != nom_normalized:
            examens_dict[nom_sans_accent] = e
    
    prescripteurs_dict = {}
    for p in data["prescripteurs"]:
        nom_normalized = p["nom"].lower().strip()
        prescripteurs_dict[nom_normalized] = p["id"]
        nom_sans_accent = normalize('NFKD', nom_normalized).encode('ASCII', 'ignore').decode('ASCII')
        if nom_sans_accent != nom_normalized:
            prescripteurs_dict[nom_sans_accent] = p["id"]
    
    if not examens_dict:
        return False, "Aucun examen trouvé dans la base de données."
    
    # Statistiques
    stats = {
        "total": len(rows_to_process),
        "success": 0,
        "errors": [],
        "warnings": [],
        "patients_created": 0,
        "transactions_created": 0,
        "prescripteurs_created": 0,
        "imported_ids": {"patients": [], "transactions": []},
        "preview_data": []  # Pour stocker les données d'aperçu
    }
    
    # Fonction pour normaliser un texte
    def normalize_text(text):
        if not text:
            return ""
        text = str(text).lower().strip()
        text = normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    # Fonction pour parser la quantité de kit
    def parse_kit_quantity(kit_value):
        if pd.isna(kit_value):
            return 0
        
        kit_str = str(kit_value).strip().lower()
        
        if kit_str == '/' or kit_str == '' or kit_str == 'nan':
            return 0
        
        numbers = re.findall(r'(\d+)', kit_str)
        if numbers:
            return int(numbers[0])
        
        if any(word in kit_str for word in ['kit', 'oui', 'x', 'preleve', 'prélevé']):
            return 1
        
        return 0
    
    # Fonction pour normaliser et résoudre les abréviations d'examens
    def resolve_exam_name(exam_name):
        if not exam_name:
            return None
        
        exam_normalized = normalize_text(exam_name)
        
        for abbr, full_name in exam_abbreviations.items():
            if exam_normalized == abbr or exam_normalized in abbr or abbr in exam_normalized:
                return full_name
        
        if len(exam_normalized.split()) == 1:
            for abbr, full_name in exam_abbreviations.items():
                if abbr in exam_normalized or exam_normalized in abbr:
                    return full_name
        
        return exam_normalized
    
    # Fonction pour trouver l'examen correspondant
    def find_matching_exam(exam_name):
        if not exam_name:
            return None, None
        
        resolved_name = resolve_exam_name(exam_name)
        if not resolved_name:
            return None, None
        
        exam_normalized = resolved_name
        
        if exam_normalized in examens_dict:
            return examens_dict[exam_normalized]["id"], examens_dict[exam_normalized]["prix"]
        
        for db_name, exam_data in examens_dict.items():
            db_normalized = normalize_text(db_name)
            if exam_normalized in db_normalized or db_normalized in exam_normalized:
                return exam_data["id"], exam_data["prix"]
        
        exam_words = set(exam_normalized.split())
        for db_name, exam_data in examens_dict.items():
            db_normalized = normalize_text(db_name)
            db_words = set(db_normalized.split())
            common = exam_words.intersection(db_words)
            if common:
                ratio = len(common) / max(len(exam_words), len(db_words))
                if ratio >= 0.3:
                    return exam_data["id"], exam_data["prix"]
        
        return None, None
    
    # Fonction pour splitter les examens multiples
    def split_multiple_exams(exam_string):
        if not exam_string:
            return []
        
        exam_string = str(exam_string)
        
        for sep in [';', '|', '/', ' et ', ' + ', ' & ']:
            exam_string = exam_string.replace(sep, ',')
        
        parts = [p.strip() for p in exam_string.split(',') if p.strip()]
        
        if len(parts) == 1 and ' ' in parts[0]:
            exam_keywords = list(exam_abbreviations.keys()) + ['nfs', 'ge', 'crp', 'pcv', 'lav', 'bw', 'iono', 'combi', 'combi11']
            words = parts[0].split()
            result = []
            current = []
            
            for word in words:
                word_clean = normalize_text(word)
                current.append(word)
                current_clean = ' '.join(current)
                
                if any(kw in word_clean for kw in exam_keywords) or len(current_clean) > 10:
                    result.append(' '.join(current))
                    current = []
            
            if current:
                result.append(' '.join(current))
            return result
        
        return parts
    
    # Fonction pour le prescripteur
    def find_or_create_prescripteur(pres_nom):
        if not pres_nom:
            return None
        
        pres_normalized = normalize_text(pres_nom)
        
        if pres_normalized in prescripteurs_dict:
            return prescripteurs_dict[pres_normalized]
        
        for db_name, db_id in prescripteurs_dict.items():
            db_normalized = normalize_text(db_name)
            if pres_normalized in db_normalized or db_normalized in pres_normalized:
                stats["warnings"].append(f"Prescripteur '{pres_nom}' correspond à '{db_name}'")
                return db_id
        
        new_id = get_next_id(data["prescripteurs"])
        nom_formate = pres_nom.strip().title()
        new_pres = {"id": new_id, "nom": nom_formate, "service": "Importé"}
        data["prescripteurs"].append(new_pres)
        prescripteurs_dict[pres_normalized] = new_id
        stats["prescripteurs_created"] += 1
        stats["warnings"].append(f"Prescripteur '{nom_formate}' créé automatiquement")
        return new_id
    
    # Grouper par patient
    patients_groups = {}
    
    for original_idx, row in rows_to_process:
        line_num = original_idx + 1
        
        try:
            # Extraire les valeurs
            annee = safe_int(row[0])
            mois_raw = row[1]
            jour = safe_int(row[2])
            numero_ordre = safe_int(row[3])
            age_raw = safe_str(row[4])
            sexe_raw = safe_str(row[5])
            prescripteur_nom = safe_str(row[6])
            examens_raw = safe_str(row[7])
            kit_raw = row[8]
            examens_gratuits_raw = safe_str(row[9])
            
            # Validations
            if annee is None or annee < 1900 or annee > 2100:
                stats["errors"].append(f"Ligne {line_num}: Année invalide")
                continue
            
            # Parser le mois
            mois = None
            if pd.notna(mois_raw):
                mois_str = str(mois_raw).strip()
                try:
                    mois = int(float(mois_str))
                    if not (1 <= mois <= 12):
                        mois = None
                except:
                    mois_normalized = normalize_text(mois_str)
                    mois = mois_map.get(mois_normalized)
            
            if mois is None:
                stats["errors"].append(f"Ligne {line_num}: Mois invalide")
                continue
            
            if jour is None or jour < 1 or jour > 31:
                stats["errors"].append(f"Ligne {line_num}: Jour invalide")
                continue
            
            if numero_ordre is None or numero_ordre < 0:
                stats["errors"].append(f"Ligne {line_num}: Numéro d'ordre invalide")
                continue
            
            age = parse_age(age_raw)
            if age is None:
                stats["errors"].append(f"Ligne {line_num}: Âge invalide")
                continue
            
            sexe = parse_sexe(sexe_raw)
            if sexe is None:
                stats["errors"].append(f"Ligne {line_num}: Sexe invalide")
                continue
            
            if not prescripteur_nom:
                stats["errors"].append(f"Ligne {line_num}: Prescripteur manquant")
                continue
            
            if not examens_raw and not examens_gratuits_raw:
                stats["errors"].append(f"Ligne {line_num}: Aucun examen spécifié")
                continue
            
            # Trouver le prescripteur
            prescripteur_id = find_or_create_prescripteur(prescripteur_nom)
            if prescripteur_id is None:
                stats["errors"].append(f"Ligne {line_num}: Impossible de créer/trouver le prescripteur")
                continue
            
            # Parser la quantité de kit
            kit_quantity = parse_kit_quantity(kit_raw)
            if kit_quantity > 0:
                stats["warnings"].append(f"Ligne {line_num}: {kit_quantity} kit(s) de prélèvement enregistré(s)")
            
            # Splitter les examens
            exam_list = split_multiple_exams(examens_raw)
            exam_gratuit_list = split_multiple_exams(examens_gratuits_raw) if examens_gratuits_raw else []
            
            # Trouver la décade
            decade = get_decade_from_date(annee, mois, jour)
            if not decade:
                stats["errors"].append(f"Ligne {line_num}: Décade non trouvée")
                continue
            
            # Pour chaque examen payant
            examens_trouves = []
            for exam_name in exam_list:
                if not exam_name:
                    continue
                
                examen_id, examen_prix = find_matching_exam(exam_name)
                if examen_id is None:
                    stats["errors"].append(f"Ligne {line_num}: Examen payant '{exam_name}' non trouvé")
                else:
                    examens_trouves.append({
                        "examen_id": examen_id,
                        "quantite_payee": 1,
                        "quantite_gratuite": 0
                    })
            
            # Pour chaque examen gratuit
            for exam_name in exam_gratuit_list:
                if not exam_name:
                    continue
                
                examen_id, examen_prix = find_matching_exam(exam_name)
                if examen_id is None:
                    stats["errors"].append(f"Ligne {line_num}: Examen gratuit '{exam_name}' non trouvé")
                else:
                    examens_trouves.append({
                        "examen_id": examen_id,
                        "quantite_payee": 0,
                        "quantite_gratuite": 1
                    })
            
            # Ajouter le kit
            if kit_quantity > 0:
                kit_examen_id, _ = find_matching_exam("kit prelevement")
                if kit_examen_id:
                    examens_trouves.append({
                        "examen_id": kit_examen_id,
                        "quantite_payee": kit_quantity,
                        "quantite_gratuite": 0
                    })
            
            if not examens_trouves:
                stats["errors"].append(f"Ligne {line_num}: Aucun examen valide trouvé")
                continue
            
            # Clé patient
            patient_key = f"{annee}-{mois:02d}-{jour:02d}_{numero_ordre}"
            
            if patient_key not in patients_groups:
                patients_groups[patient_key] = {
                    "date": f"{annee}-{mois:02d}-{jour:02d}",
                    "numero_ordre": numero_ordre,
                    "age": age,
                    "sexe": sexe,
                    "prescripteur_id": prescripteur_id,
                    "decade_id": decade["id"],
                    "examens": []
                }
            
            patients_groups[patient_key]["examens"].extend(examens_trouves)
            
            # Ajouter aux données d'aperçu
            for exam in examens_trouves:
                stats["preview_data"].append({
                    "date": f"{annee}-{mois:02d}-{jour:02d}",
                    "numero_ordre": numero_ordre,
                    "age": age,
                    "sexe": sexe,
                    "prescripteur": prescripteur_nom,
                    "examen": exam.get("examen_nom", "Examen"),
                    "quantite_payee": exam["quantite_payee"],
                    "quantite_gratuite": exam["quantite_gratuite"]
                })
            
        except Exception as e:
            stats["errors"].append(f"Ligne {line_num}: Erreur - {str(e)}")
    
    # Sauvegarder les nouveaux prescripteurs
    if stats["prescripteurs_created"] > 0:
        save_data(data)
    
    # Enregistrer les patients et transactions
    for patient_key, patient_data in patients_groups.items():
        try:
            current_data = load_data()
            
            patient_date = datetime.strptime(patient_data["date"], "%Y-%m-%d").date()
            
            # Vérifier si le patient existe déjà
            existing_patient = None
            for p in current_data.get("patients", []):
                if p.get("date_jour") == patient_data["date"] and p.get("numero_ordre") == patient_data["numero_ordre"]:
                    existing_patient = p
                    break
            
            if existing_patient:
                patient_id = existing_patient["id"]
            else:
                new_patient = add_patient(
                    sexe=patient_data["sexe"], 
                    age=patient_data["age"],
                    date_enregistrement=patient_date
                )
                current_data = load_data()
                patient_id = new_patient["id"]
                stats["patients_created"] += 1
            
            stats["imported_ids"]["patients"].append(patient_id)
            
            # Enregistrer les transactions
            transaction_ids = add_transaction_group(
                patient_id=patient_id,
                prescripteur_id=patient_data["prescripteur_id"],
                decade_id=patient_data["decade_id"],
                examens=patient_data["examens"]
            )
            
            stats["transactions_created"] += len(transaction_ids)
            stats["imported_ids"]["transactions"].extend(transaction_ids)
            stats["success"] += 1
            
        except Exception as e:
            stats["errors"].append(f"Patient {patient_data['numero_ordre']}: Erreur - {str(e)}")
    
    # Sauvegarder les IDs
    if stats["success"] > 0:
        if "imported_data_ids" not in st.session_state:
            st.session_state.imported_data_ids = {"patients": [], "transactions": []}
        st.session_state.imported_data_ids["patients"].extend(stats["imported_ids"]["patients"])
        st.session_state.imported_data_ids["transactions"].extend(stats["imported_ids"]["transactions"])
    
    return True, stats

def delete_all_imported_data():
    """
    Supprime toutes les données marquées comme importées
    """
    data = load_data()
    
    if "imported_data_ids" not in st.session_state:
        return 0, 0
    
    # Compter avant suppression
    patients_to_delete = st.session_state.imported_data_ids.get("patients", [])
    transactions_to_delete = st.session_state.imported_data_ids.get("transactions", [])
    
    # Supprimer les patients importés
    original_patient_count = len(data.get("patients", []))
    data["patients"] = [p for p in data.get("patients", []) if p["id"] not in patients_to_delete]
    deleted_patients = original_patient_count - len(data["patients"])
    
    # Supprimer les transactions importées
    original_transaction_count = len(data["transactions"])
    data["transactions"] = [t for t in data["transactions"] if t["id"] not in transactions_to_delete]
    deleted_transactions = original_transaction_count - len(data["transactions"])
    
    # Sauvegarder les modifications
    save_data(data)
    
    # Réinitialiser les IDs importés
    st.session_state.imported_data_ids = {
        "patients": [],
        "transactions": []
    }
    
    return deleted_patients, deleted_transactions

@st.dialog("📤 Importer des transactions")
def modal_import_transactions():
    """
    Fenêtre modale pour l'importation de transactions depuis un fichier
    """
    st.markdown("### 📤 Importation de transactions")
    st.markdown("Téléchargez un fichier Excel avec les colonnes suivantes:")
    
    # Afficher le format attendu
    with st.expander("📋 Format du fichier attendu"):
        st.markdown("""
        | Colonne | Description | Exemple |
        |---------|-------------|---------|
        | 1 | Année | 2024 |
        | 2 | Mois | 4 |
        | 3 | Jour | 8 |
        | 4 | Numéro d'ordre patient | 1 |
        | 5 | Âge (supporte: "30 Ans", "11 mois", "20 ans", "15 ans 3 mois", "2 semaines", "1 semaine", "3 jours") | 30 Ans |
        | 6 | Sexe (F/M, Féminin/Masculin) | F |
        | 7 | Prescripteur | Dr Ndombi |
        | 8 | Examens payants | NFS, GE |
        | 9 | Kit de prélèvement | Kit |
        | 10 | Examens gratuits | CRP, GLYCEMIE |
        """)
        st.info("💡 **Note**: La première ligne peut contenir des en-têtes - elle sera automatiquement ignorée.")
        st.info("📝 **Format de l'âge**: Supporte '30 Ans', '11 mois', '20 ans', '15 ans 3 mois', '2 semaines', '1 semaine', '3 jours'. Les semaines/jours/mois seuls sont convertis à 0 an.")
        st.info("🎁 **Examens gratuits**: Les examens dans la colonne 10 sont automatiquement comptés comme quantité gratuite.")
    
    uploaded_file = st.file_uploader(
        "Choisir un fichier Excel (.xlsx, .xls)",
        type=["xlsx", "xls"],
        key="import_file_uploader",
        help="Le fichier doit contenir exactement 10 colonnes"
    )
    
    if uploaded_file is not None:
        # Aperçu du fichier
        try:
            df_preview = pd.read_excel(uploaded_file, header=None, nrows=5)
            st.markdown("### 📄 Aperçu du fichier (5 premières lignes)")
            st.dataframe(df_preview, use_container_width=True)
        except Exception as e:
            st.error(f"Impossible de lire l'aperçu: {str(e)}")
        
        # Variables de session pour stocker l'état de l'importation
        if "import_pending" not in st.session_state:
            st.session_state.import_pending = False
        if "import_stats" not in st.session_state:
            st.session_state.import_stats = None
        if "import_file" not in st.session_state:
            st.session_state.import_file = None
        
        # Bouton pour analyser/lancer l'importation
        if not st.session_state.import_pending:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ Annuler", key="btn_cancel_import", type="secondary", use_container_width=True):
                    st.session_state.import_pending = False
                    st.session_state.import_stats = None
                    st.session_state.import_file = None
                    st.rerun()
            with col2:
                if st.button("📥 Lancer l'importation", key="btn_start_import", type="primary", use_container_width=True):
                    with st.spinner("Analyse et préparation de l'importation..."):
                        success, result = import_transactions_from_file(uploaded_file)
                        if success:
                            st.session_state.import_pending = True
                            st.session_state.import_stats = result
                            st.session_state.import_file = uploaded_file
                            st.rerun()
                        else:
                            st.error(f"❌ Erreur: {result}")
        else:
            # Afficher les résultats de l'analyse
            stats = st.session_state.import_stats
            
            if stats:
                st.markdown("### 📊 Aperçu des données à importer")
                
                # Afficher les statistiques
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📄 Lignes traitées", stats["total"])
                with col2:
                    st.metric("👥 Patients à créer", stats["success"])
                with col3:
                    st.metric("📋 Transactions", stats["transactions_created"])
                with col4:
                    st.metric("👤 Prescripteurs", stats["prescripteurs_created"])
                
                # Afficher le tableau des données
                if stats["preview_data"]:
                    df_preview_data = pd.DataFrame(stats["preview_data"])
                    st.dataframe(df_preview_data, use_container_width=True)
                
                # Afficher les avertissements
                if stats["warnings"]:
                    with st.expander(f"⚠️ {len(stats['warnings'])} avertissement(s)"):
                        for warning in stats["warnings"]:
                            st.warning(warning)
                
                # Afficher les erreurs
                if stats["errors"]:
                    with st.expander(f"❌ {len(stats['errors'])} erreur(s)"):
                        for error in stats["errors"]:
                            st.error(error)
                    st.error("❌ Des erreurs ont été détectées. Veuillez corriger le fichier avant d'importer.")
                    
                    # Bouton pour réinitialiser
                    if st.button("🔄 Réinitialiser", key="btn_reset_import", use_container_width=True):
                        st.session_state.import_pending = False
                        st.session_state.import_stats = None
                        st.session_state.import_file = None
                        st.rerun()
                else:
                    st.success("✅ Aucune erreur détectée. Le fichier est prêt à être importé.")
                    
                    st.markdown("---")
                    st.markdown("### ⚠️ Confirmation d'importation")
                    st.warning("⚠️ Attention: Cette action est irréversible. Une fois confirmée, les données seront définitivement ajoutées à la base.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("❌ Annuler", key="btn_cancel_final", type="secondary", use_container_width=True):
                            st.session_state.import_pending = False
                            st.session_state.import_stats = None
                            st.session_state.import_file = None
                            st.rerun()
                    with col2:
                        if st.button("✅ Valider l'importation", key="btn_confirm_final", type="primary", use_container_width=True):
                            # Les données sont déjà sauvegardées dans import_transactions_from_file
                            st.success("✅ Importation terminée avec succès!")
                            
                            # Afficher les résultats finaux
                            st.markdown("### 📊 Résultats finaux")
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("👥 Patients créés", stats["patients_created"])
                            with col_b:
                                st.metric("📋 Transactions créées", stats["transactions_created"])
                            with col_c:
                                st.metric("👤 Prescripteurs créés", stats["prescripteurs_created"])
                            
                            st.markdown("---")
                            if st.button("Fermer", key="btn_close_final", use_container_width=True):
                                # Nettoyer et fermer
                                st.session_state.import_pending = False
                                st.session_state.import_stats = None
                                st.session_state.import_file = None
                                st.rerun()
    
    st.markdown("---")
    if st.button("❌ Fermer", key="btn_close_modal", use_container_width=True):
        st.session_state.import_pending = False
        st.session_state.import_stats = None
        st.session_state.import_file = None
        st.rerun()

@st.dialog("⚠️ Supprimer toutes les données importées")
def modal_delete_imported_data():
    """
    Fenêtre modale de confirmation pour supprimer toutes les données importées
    """
    st.warning("⚠️ Êtes-vous sûr de vouloir supprimer TOUTES les données importées ?")
    st.caption("Cette action supprimera tous les patients et transactions qui ont été importés via Excel.")
    st.caption("Cette action est irréversible.")
    
    # Afficher un aperçu de ce qui va être supprimé
    if "imported_data_ids" in st.session_state:
        patients_count = len(st.session_state.imported_data_ids.get("patients", []))
        transactions_count = len(st.session_state.imported_data_ids.get("transactions", []))
        
        if patients_count > 0 or transactions_count > 0:
            st.info(f"📊 Données concernées: {patients_count} patient(s) et {transactions_count} transaction(s)")
        else:
            st.info("📊 Aucune donnée importée à supprimer.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Annuler", key="btn_cancel_delete", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("✅ Confirmer la suppression", key="btn_confirm_delete", type="primary", use_container_width=True):
            deleted_patients, deleted_transactions = delete_all_imported_data()
            st.success(f"✅ {deleted_patients} patient(s) et {deleted_transactions} transaction(s) supprimés avec succès!")
            time.sleep(1.5)
            st.rerun()

def show():
    """
    Point d'entrée pour l'affichage de la page de saisie et d'historique des transactions
    """
    data = load_data()
    
    # Initialisation des variables de session pour le wizard
    if "wizard_active" not in st.session_state:
        st.session_state.wizard_active = False
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
    if "temp_patient" not in st.session_state:
        st.session_state.temp_patient = {}
    if "temp_examens" not in st.session_state:
        st.session_state.temp_examens = []
    if "prescripteur_selected" not in st.session_state:
        st.session_state.prescripteur_selected = None
    if "last_exam_key" not in st.session_state:
        st.session_state.last_exam_key = 0
    if "imported_data_ids" not in st.session_state:
        st.session_state.imported_data_ids = {
            "patients": [],
            "transactions": []
        }
    if "custom_date" not in st.session_state:
        st.session_state.custom_date = datetime.now().date()
    if "use_custom_date" not in st.session_state:
        st.session_state.use_custom_date = False
    if "import_pending" not in st.session_state:
        st.session_state.import_pending = False
    if "import_stats" not in st.session_state:
        st.session_state.import_stats = None
    if "import_file" not in st.session_state:
        st.session_state.import_file = None
    
    # --- HEADER SECTION ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    
    # Calculer le nombre de données importées
    imported_patients_count = len(st.session_state.imported_data_ids.get("patients", []))
    has_imported_data = imported_patients_count > 0
    
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.title("💰 Transactions Patient")
        st.caption("Enregistrez les prestations par patient et gérez l'historique financier")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if not st.session_state.wizard_active:
            if st.button("➕ Nouveau Patient", key="btn_new_patient", type="primary", use_container_width=True):
                if not data["prescripteurs"] or not data["examens"] or not data["decades"]:
                    st.error("Veuillez configurer les Prescripteurs, Examens et Décades avant de saisir.")
                else:
                    reset_wizard()
                    st.session_state.wizard_active = True
                    st.rerun()
        else:
            if st.button("❌ Annuler la saisie", key="btn_cancel_wizard", type="secondary", use_container_width=True):
                reset_wizard()
                st.rerun()
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📤 Importer Excel", key="btn_import_excel", type="secondary", use_container_width=True):
            modal_import_transactions()
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        if has_imported_data:
            if st.button("🗑️ Supprimer imports", key="btn_delete_imports", type="secondary", use_container_width=True):
                modal_delete_imported_data()
        else:
            st.button("🗑️ Supprimer imports", key="btn_delete_imports_disabled", type="secondary", use_container_width=True, disabled=True, 
                     help="Aucune donnée importée à supprimer")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Afficher un badge si des données importées existent
    if has_imported_data:
        st.info(f"ℹ️ {imported_patients_count} patient(s) importé(s) sont présents dans la base. Utilisez le bouton 'Supprimer imports' pour les retirer.")
    
    # --- FORMULAIRE WIZARD (affiché uniquement si actif) ---
    if st.session_state.wizard_active:
        st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px; border-left: 5px solid #2196F3 !important;">', unsafe_allow_html=True)
        
        # Indicateur d'étape
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.session_state.wizard_step == 1:
                st.markdown("### 📝 **Étape 1/2**")
                st.markdown("*Informations Patient*")
            else:
                st.markdown("### ✅ **Étape 1/2**")
                st.markdown("*Informations Patient*")
        with col2:
            if st.session_state.wizard_step == 2:
                st.markdown("### 📝 **Étape 2/2**")
                st.markdown("*Examens & Transaction*")
            else:
                st.markdown("### ⏳ **Étape 2/2**")
                st.markdown("*Examens & Transaction*")
        
        st.markdown("---")
        
        # ÉTAPE 1: Informations Patient
        if st.session_state.wizard_step == 1:
            st.markdown("### 👤 Informations du Patient")
            
            # Sélecteur de date personnalisée
            st.markdown("#### 📅 Date d'enregistrement")
            
            use_custom_date = st.checkbox(
                "📆 Utiliser une date différente", 
                value=st.session_state.use_custom_date,
                key="chk_use_custom_date",
                help="Cochez pour enregistrer des transactions rétroactives (ex: du 1er Avril)"
            )
            st.session_state.use_custom_date = use_custom_date
            
            if use_custom_date:
                custom_date = st.date_input(
                    "Date de l'enregistrement",
                    value=st.session_state.custom_date,
                    max_value=datetime.now().date(),
                    key="date_custom",
                    help="Sélectionnez la date à laquelle la transaction a été réellement effectuée"
                )
                st.session_state.custom_date = custom_date
                date_for_number = custom_date
                
                # Avertissement si date dans le futur
                if custom_date > datetime.now().date():
                    st.error("⚠️ La date ne peut pas être dans le futur!")
                elif custom_date < datetime.now().date():
                    st.info(f"📅 Enregistrement rétroactif au {custom_date.strftime('%d/%m/%Y')}")
            else:
                date_for_number = datetime.now().date()
                st.session_state.custom_date = date_for_number
                st.caption(f"📅 Date d'enregistrement: {date_for_number.strftime('%d/%m/%Y')}")
            
            st.markdown("---")
            
            # Calculer le numéro d'ordre en fonction de la date choisie
            next_number = get_next_patient_number_for_date(date_for_number)
            
            # Afficher le compteur du jour pour la date choisie
            patients_this_day = get_patients_for_date(date_for_number)
            st.info(f"📋 **Patients enregistrés le {date_for_number.strftime('%d/%m/%Y')}** : {len(patients_this_day)}")
            st.success(f"🔢 **Numéro d'ordre patient** : `{next_number}`")
            
            col1, col2 = st.columns(2)
            with col1:
                sexe = st.radio("Sexe", ["F", "M"], key="radio_sexe", horizontal=True, 
                              format_func=lambda x: "Féminin" if x == "F" else "Masculin")
            with col2:
                age = st.number_input("Âge (années)", key="input_age", min_value=0, max_value=150, value=30, step=1)
            
            st.markdown("---")
            
            # Aperçu des patients du jour (pour la date choisie)
            if patients_this_day:
                with st.expander(f"📊 Voir les patients enregistrés le {date_for_number.strftime('%d/%m/%Y')}"):
                    for p in patients_this_day[-10:]:
                        st.write(f"**#{p['numero_ordre']}** - {p['sexe']} - {p['age']} ans "
                               f"({p['date_enregistrement'][:19]})")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ Annuler", key="btn_cancel_step1", use_container_width=True):
                    reset_wizard()
                    st.rerun()
            with col2:
                if st.button("Suivant ➡️", key="btn_next_step1", type="primary", use_container_width=True):
                    if age >= 0:
                        # Stocker la date personnalisée dans temp_patient
                        st.session_state.temp_patient = {
                            "sexe": sexe,
                            "age": age,
                            "numero_ordre": next_number,
                            "date_enregistrement": date_for_number
                        }
                        st.session_state.wizard_step = 2
                        st.rerun()
                    else:
                        st.error("Veuillez saisir un âge valide")
        
        # ÉTAPE 2: Examens et Transaction
        elif st.session_state.wizard_step == 2:
            st.markdown("### 🧪 Examens et Transaction")
            
            # Récupérer la date du patient
            patient_date = st.session_state.temp_patient.get('date_enregistrement', datetime.now().date())
            
            # Afficher le résumé patient avec la date
            st.success(f"**Patient n°** : #{st.session_state.temp_patient['numero_ordre']} | "
                      f"**Sexe** : {'Féminin' if st.session_state.temp_patient['sexe'] == 'F' else 'Masculin'} | "
                      f"**Âge** : {st.session_state.temp_patient['age']} ans | "
                      f"**Date** : {patient_date.strftime('%d/%m/%Y') if hasattr(patient_date, 'strftime') else patient_date}")
            
            st.markdown("---")
            
            # Décade basée sur la date du patient (pas la date du jour)
            if hasattr(patient_date, 'strftime'):
                current_decade = get_decade_for_date(patient_date)
            else:
                current_decade = get_current_decade()
            
            if not current_decade:
                st.error(f"⚠️ Aucune décade trouvée pour la date {patient_date}. Veuillez générer les décades.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Gérer les décades", key="btn_manage_decades", use_container_width=True):
                        reset_wizard()
                        st.switch_page("pages/decades_page.py")
                with col2:
                    if st.button("❌ Annuler", key="btn_cancel_step2", use_container_width=True):
                        reset_wizard()
                        st.rerun()
                return
            
            st.info(f"📅 **Décade de facturation** : {current_decade['periode']} - "
                   f"{current_decade['mois']} {current_decade['annee']} "
                   f"({current_decade['date_debut']} au {current_decade['date_fin']})")
            
            # Sélection du prescripteur
            pres_options = {p["nom"]: p["id"] for p in data["prescripteurs"]}
            if not pres_options:
                st.error("Aucun prescripteur disponible.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Gérer les prescripteurs", key="btn_manage_prescripteurs", use_container_width=True):
                        reset_wizard()
                        st.switch_page("pages/prescripteurs_page.py")
                with col2:
                    if st.button("❌ Annuler", key="btn_cancel_no_pres", use_container_width=True):
                        reset_wizard()
                        st.rerun()
                return
            
            # Sauvegarder le prescripteur sélectionné
            if st.session_state.prescripteur_selected is None:
                st.session_state.prescripteur_selected = list(pres_options.keys())[0]
            
            pres_sel = st.selectbox(
                "👤 Prescripteur", 
                list(pres_options.keys()),
                index=list(pres_options.keys()).index(st.session_state.prescripteur_selected) if st.session_state.prescripteur_selected in pres_options else 0,
                key="prescripteur_select"
            )
            st.session_state.prescripteur_selected = pres_sel
            
            st.markdown("---")
            st.markdown("#### 📋 Ajouter des examens au panier")
            
            # Formulaire d'ajout d'examen
            with st.container(border=True):
                st.markdown("**➕ Ajouter un examen**")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    ex_options = {f"{e['nom']} ({e['prix']:,.0f} FCFA)": e for e in data["examens"]}
                    if not ex_options:
                        st.error("Aucun examen disponible.")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Gérer les examens", key="btn_manage_examens", use_container_width=True):
                                reset_wizard()
                                st.switch_page("pages/examens_page.py")
                        with col2:
                            if st.button("❌ Annuler", key="btn_cancel_no_exam", use_container_width=True):
                                reset_wizard()
                                st.rerun()
                        return
                    
                    ex_sel = st.selectbox(
                        "Type d'Examen", 
                        list(ex_options.keys()), 
                        key=f"ex_sel_{st.session_state.last_exam_key}"
                    )
                    selected_exam = ex_options[ex_sel]
                
                with col2:
                    q_payee = st.number_input("Quantité PAYÉE", min_value=0, value=1, step=1, key="q_payee")
                
                with col3:
                    q_gratuite = st.number_input("Quantité GRATUITE", min_value=0, value=0, step=1, key="q_gratuite")
                
                # Bouton Ajouter - reste dans le formulaire
                if st.button("🛒 Ajouter au panier", key="btn_add_to_cart", type="secondary", use_container_width=True):
                    if q_payee == 0 and q_gratuite == 0:
                        st.error("Veuillez saisir au moins une quantité")
                    else:
                        st.session_state.temp_examens.append({
                            "examen_id": selected_exam["id"],
                            "examen_nom": selected_exam["nom"],
                            "prix": selected_exam["prix"],
                            "quantite_payee": int(q_payee),
                            "quantite_gratuite": int(q_gratuite),
                            "montant": int(q_payee * selected_exam["prix"])
                        })
                        st.toast(f"✅ Ajouté : {selected_exam['nom']}", icon="🛒")
                        st.session_state.last_exam_key += 1
                        time.sleep(0.5)
                        st.rerun()
            
            st.markdown("---")
            
            # Affichage du panier
            if st.session_state.temp_examens:
                st.markdown("#### 🛒 Panier des examens")
                
                df_panier = pd.DataFrame(st.session_state.temp_examens)
                df_display = df_panier[["examen_nom", "quantite_payee", "quantite_gratuite", "montant"]]
                df_display.columns = ["Examen", "Payé", "Gratuit", "Montant (FCFA)"]
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                total_montant = sum(e["montant"] for e in st.session_state.temp_examens)
                st.metric("💰 Total à payer", f"{total_montant:,.0f} FCFA")
                
                # Options de suppression
                st.markdown("**🗑️ Gestion du panier**")
                col_del1, col_del2 = st.columns(2)
                
                with col_del1:
                    if len(st.session_state.temp_examens) > 0:
                        item_to_delete = st.selectbox(
                            "Sélectionner un examen à supprimer",
                            options=range(len(st.session_state.temp_examens)),
                            format_func=lambda x: f"{st.session_state.temp_examens[x]['examen_nom']} "
                                                 f"({st.session_state.temp_examens[x]['quantite_payee']} payé, "
                                                 f"{st.session_state.temp_examens[x]['quantite_gratuite']} gratuit)",
                            key="delete_select"
                        )
                        if st.button("🗑️ Supprimer cet examen", key="btn_delete_exam", use_container_width=True):
                            del st.session_state.temp_examens[item_to_delete]
                            st.toast("Examen retiré du panier", icon="🗑️")
                            st.rerun()
                
                with col_del2:
                    if st.button("⚠️ Vider tout le panier", key="btn_clear_cart", type="secondary", use_container_width=True):
                        st.session_state.temp_examens = []
                        st.toast("Panier vidé", icon="⚠️")
                        st.rerun()
            else:
                st.info("📭 Aucun examen dans le panier. Utilisez le formulaire ci-dessus pour ajouter des examens.")
            
            st.markdown("---")
            
            # Boutons de navigation
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("⬅️ Retour patient", key="btn_back_patient", use_container_width=True):
                    st.session_state.wizard_step = 1
                    st.rerun()
            
            with col2:
                if st.button("🔄 Nouveau patient", key="btn_new_patient_wizard", use_container_width=True):
                    reset_wizard()
                    st.rerun()
            
            with col3:
                if st.button("❌ Annuler", key="btn_cancel_wizard2", use_container_width=True):
                    reset_wizard()
                    st.rerun()
            
            with col4:
                if st.button("✅ ENREGISTRER", key="btn_save_transaction", type="primary", use_container_width=True, 
                            disabled=len(st.session_state.temp_examens) == 0):
                    if not st.session_state.temp_examens:
                        st.error("Veuillez ajouter au moins un examen")
                    else:
                        # Créer le patient avec la date personnalisée
                        patient_date = st.session_state.temp_patient.get('date_enregistrement')
                        new_patient = add_patient(
                            sexe=st.session_state.temp_patient["sexe"],
                            age=st.session_state.temp_patient["age"],
                            date_enregistrement=patient_date
                        )
                        
                        # Préparer les examens
                        examens_list = [
                            {
                                "examen_id": e["examen_id"],
                                "quantite_payee": e["quantite_payee"],
                                "quantite_gratuite": e["quantite_gratuite"]
                            }
                            for e in st.session_state.temp_examens
                        ]
                        
                        # Enregistrer les transactions
                        transaction_ids = add_transaction_group(
                            patient_id=new_patient["id"],
                            prescripteur_id=pres_options[st.session_state.prescripteur_selected],
                            decade_id=current_decade["id"],
                            examens=examens_list
                        )
                        
                        st.success(f"✅ {len(transaction_ids)} examen(s) enregistré(s) pour le patient n°{new_patient['numero_ordre']} "
                                  f"(date: {patient_date.strftime('%d/%m/%Y') if hasattr(patient_date, 'strftime') else patient_date})")
                        
                        # Proposer de continuer
                        st.markdown("---")
                        st.markdown("#### Que souhaitez-vous faire ensuite ?")
                        
                        col_next1, col_next2 = st.columns(2)
                        with col_next1:
                            if st.button("🔄 Nouveau patient", key="btn_next_new_patient", use_container_width=True, type="primary"):
                                reset_wizard()
                                st.rerun()
                        
                        with col_next2:
                            if st.button("📊 Voir l'historique", key="btn_view_history", use_container_width=True):
                                reset_wizard()
                                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # --- STATISTIQUES RAPIDES ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    total_patients = len(data.get("patients", []))
    total_transactions = len(data["transactions"])
    total_montant = 0
    ex_dict = {e["id"]: e for e in data["examens"]}
    
    for t in data["transactions"]:
        ex = ex_dict.get(t["examen_id"])
        if ex:
            total_montant += t["quantite_payee"] * ex["prix"]
    
    with col1:
        st.metric("👥 Patients", total_patients)
    with col2:
        st.metric("📋 Transactions", total_transactions)
    with col3:
        st.metric("💰 Chiffre d'affaires", f"{total_montant:,.0f} FCFA")
    with col4:
        today = datetime.now().strftime("%Y-%m-%d")
        patients_auj = len([p for p in data.get("patients", []) if p.get("date_jour") == today])
        st.metric("📅 Patients aujourd'hui", patients_auj)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # --- HISTORIQUE DES TRANSACTIONS ---
    st.markdown('<div class="card p-4 border-0 shadow-sm" style="border-radius: 16px;">', unsafe_allow_html=True)
    st.subheader("📋 Historique des transactions")
    
    patients_dict = {p["id"]: p for p in data.get("patients", [])}
    ex_dict = {e["id"]: e for e in data["examens"]}
    pr_dict = {p["id"]: p["nom"] for p in data["prescripteurs"]}
    
    transactions_by_patient = {}
    for t in data["transactions"]:
        patient_id = t.get("patient_id")
        if patient_id:
            if patient_id not in transactions_by_patient:
                transactions_by_patient[patient_id] = []
            transactions_by_patient[patient_id].append(t)
    
    if transactions_by_patient:
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search = st.text_input("🔍 Rechercher", key="search_input", placeholder="Numéro patient, nom prescripteur ou examen...", label_visibility="collapsed")
        with col_filter:
            filter_date = st.selectbox("Filtrer par période", ["Tous", "Aujourd'hui", "Cette semaine", "Ce mois"], key="filter_date", label_visibility="collapsed")
        
        sorted_patients = sorted(patients_dict.items(), 
                                key=lambda x: x[1].get("date_enregistrement", ""), 
                                reverse=True)
        
        for patient_id, patient in sorted_patients:
            if patient_id not in transactions_by_patient:
                continue
            
            transactions = transactions_by_patient[patient_id]
            
            show_patient = True
            if filter_date == "Aujourd'hui":
                today = datetime.now().strftime("%Y-%m-%d")
                if patient.get("date_jour") != today:
                    show_patient = False
            elif filter_date == "Cette semaine":
                today = datetime.now()
                week_start = today - pd.Timedelta(days=today.weekday())
                patient_date = datetime.strptime(patient["date_enregistrement"][:10], "%Y-%m-%d")
                if patient_date < week_start:
                    show_patient = False
            elif filter_date == "Ce mois":
                current_month = datetime.now().strftime("%Y-%m")
                if not patient["date_enregistrement"].startswith(current_month):
                    show_patient = False
            
            if not show_patient:
                continue
            
            total_patient = 0
            for t in transactions:
                ex = ex_dict.get(t["examen_id"])
                if ex:
                    total_patient += t["quantite_payee"] * ex["prix"]
            
            if search:
                search_lower = search.lower()
                patient_match = search_lower in str(patient["numero_ordre"])
                pres_match = any(search_lower in pr_dict.get(t["prescripteur_id"], "").lower() for t in transactions)
                ex_match = any(search_lower in ex_dict.get(t["examen_id"], {}).get("nom", "").lower() for t in transactions)
                show_patient = patient_match or pres_match or ex_match
            
            if show_patient:
                # Ajouter un badge "Importé" si le patient vient d'un import
                is_imported = patient.get("is_imported", False)
                import_badge = " 📥" if is_imported else ""
                sex_icon = "👩" if patient["sexe"] == "F" else "👨"
                
                # Afficher la date dans l'expandeur
                patient_date = patient.get("date_jour", "Date inconnue")
                
                with st.expander(f"{sex_icon} Patient #{patient['numero_ordre']}{import_badge} - {patient['sexe']} - {patient['age']} ans - 📅 {patient_date} - 💰 {total_patient:,.0f} FCFA"):
                    st.markdown("**Examens effectués :**")
                    
                    for t in transactions:
                        ex = ex_dict.get(t["examen_id"])
                        if ex:
                            col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1.5, 1.5])
                            with col1:
                                st.caption(f"#{t['id']}")
                            with col2:
                                st.write(pr_dict.get(t["prescripteur_id"], "Inconnu"))
                            with col3:
                                st.write(ex["nom"])
                            with col4:
                                st.write(f"Payé: {t['quantite_payee']} | Gratuit: {t['quantite_gratuite']}")
                            with col5:
                                montant = t["quantite_payee"] * ex["prix"]
                                st.write(f"{montant:,.0f} FCFA")
                            
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button("✏️ Modifier", key=f"edit_{t['id']}", use_container_width=True):
                                    st.info("Fonctionnalité à venir")
                            with btn_col2:
                                if st.button("🗑️ Supprimer", key=f"del_{t['id']}", use_container_width=True):
                                    st.info("Fonctionnalité à venir")
                    st.divider()
    else:
        st.info("📭 Aucune transaction n'a encore été enregistrée dans le système.")
    
    st.markdown('</div>', unsafe_allow_html=True)