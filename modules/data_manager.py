import json
import os
from datetime import datetime

DATA_FILE = 'data/starlab_data.json'

def ensure_data_dir():
    os.makedirs('data', exist_ok=True)

def load_data():
    ensure_data_dir()
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Migration: ajouter la collection patients si elle n'existe pas
            if "patients" not in data:
                data["patients"] = []
            return data
    return {
        "prescripteurs": [],
        "categories": [],
        "examens": [],
        "decades": [],
        "patients": [],      # Nouvelle collection
        "transactions": []
    }

def save_data(data):
    ensure_data_dir()
    # Créer un backup avant de sauvegarder
    if os.path.exists(DATA_FILE):
        backup_dir = 'data/backups'
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f'starlab_data_backup_{timestamp}.json')
        import shutil
        shutil.copy2(DATA_FILE, backup_file)
        
        # Nettoyage des vieux backups (garder les 10 derniers)
        backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)])
        if len(backups) > 10:
            for b in backups[:-10]:
                os.remove(b)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_next_id(items):
    if not items:
        return 1
    return max(item.get('id', 0) for item in items) + 1