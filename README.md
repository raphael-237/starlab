# 🔬 STARLAB - Système de Gestion Financière du Laboratoire

**Version : 1.0** | **© BE CORP 2026**

---

## 📋 Présentation

STARLAB est une application de gestion financière complète destinée aux laboratoires d'analyses médicales. Elle permet le suivi précis des examens réalisés, des prescripteurs et des revenus générés.

### Fonctionnalités principales

| Module | Description |
|--------|-------------|
| 👤 **Prescripteurs** | Gestion des médecins et prescripteurs (ajout, modification, suppression) |
| 📂 **Catégories** | Organisation des examens par catégories |
| 🧪 **Examens** | Catalogue des examens avec prix unitaires |
| 📅 **Décades** | Génération automatique des périodes (3 par mois, 36 par an) |
| 💰 **Transactions** | Enregistrement des examens payés et gratuits |
| 📊 **Statistiques** | Rapports financiers par décade, mois et année |
| 📎 **Export Excel** | Génération de rapports au format officiel du laboratoire |

---

## 🚀 Modes d'installation et d'exécution

### Option 1 : Application portable (Windows) - RECOMMANDÉE

**Aucune installation technique requise** - Idéal pour une utilisation sur poste de travail.

1. Téléchargez le fichier `STARLAB.exe`
2. Double-cliquez pour lancer l'application
3. Les données sont automatiquement sauvegardées dans le dossier `data/`

> ✅ **Avantages** : Pas d'installation de Python, pas de dépendances à gérer, prêt à l'emploi
> ⚠️ **Limitation** : Fonctionne uniquement sur Windows 10/11

**Création de l'exécutable portable :**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name STARLAB app.py