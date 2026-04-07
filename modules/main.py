from data_manager import load_all_data
import prescripteurs, categories_examens, examens, decades, transactions, statistiques
from datetime import datetime

# ══════════════════════════════════════════════
#  PALETTE ANSI  (correspondance design app.py)
# ══════════════════════════════════════════════
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    # Accents (bleu / cyan — var(--accent) / var(--accent-2))
    ACCENT  = "\033[38;2;59;130;246m"       # #3b82f6
    ACCENT2 = "\033[38;2;6;182;212m"        # #06b6d4

    # Texte (var(--text-primary/secondary/muted))
    PRIMARY   = "\033[38;2;241;245;249m"    # #f1f5f9
    SECONDARY = "\033[38;2;148;163;184m"    # #94a3b8
    MUTED     = "\033[38;2;71;85;105m"      # #475569

    # Statuts
    SUCCESS = "\033[38;2;16;185;129m"       # #10b981
    WARNING = "\033[38;2;245;158;11m"       # #f59e0b
    DANGER  = "\033[38;2;239;68;68m"        # #ef4444

    # Fond sombre simulé (block de texte)
    BG_SURFACE = "\033[48;2;17;24;39m"      # #111827

# ══════════════════════════════════════════════
#  COMPOSANTS UI
# ══════════════════════════════════════════════

def line(char="─", width=54, color=C.MUTED):
    print(f"{color}{char * width}{C.RESET}")

def header_splash():
    """Splash screen — equiv. sidebar logo + main-header"""
    now = datetime.now()
    print()
    line("═", 54, C.ACCENT)
    print(
        f"{C.ACCENT}  🔬  {C.BOLD}{C.PRIMARY}STARLAB{C.RESET}"
        f"{C.SECONDARY}  ·  Gestion Financière du Laboratoire{C.RESET}"
    )
    print(
        f"{C.MUTED}     by BE CORP  ·  CMA NKOMO  ·  "
        f"v1.0  ·  {now.strftime('%d/%m/%Y  %H:%M')}{C.RESET}"
    )
    line("═", 54, C.ACCENT)
    print()

def section_header(title: str, subtitle: str = ""):
    """Equiv. display_header() — barre accent en haut de page"""
    print()
    line("─", 54, C.ACCENT2)
    print(f"{C.ACCENT2}  {C.BOLD}{title}{C.RESET}")
    if subtitle:
        print(f"{C.MUTED}  {subtitle}{C.RESET}")
    line("─", 54, C.ACCENT2)

def menu_box(items: dict):
    """
    Affiche un menu stylisé.
    items = { "1": ("icône label", "description") }
    """
    print()
    for key, (label, desc) in items.items():
        key_fmt  = f"{C.ACCENT}{C.BOLD}  {key:>2}{C.RESET}"
        lab_fmt  = f"{C.PRIMARY}{label}{C.RESET}"
        desc_fmt = f"{C.MUTED}— {desc}{C.RESET}" if desc else ""
        print(f"{key_fmt}  {lab_fmt}  {desc_fmt}")
    print()

def prompt_choice(hint: str = "Votre choix") -> str:
    return input(f"{C.ACCENT2}▸ {C.SECONDARY}{hint} : {C.RESET}").strip()

def ok(msg: str):
    print(f"\n{C.SUCCESS}✔  {C.PRIMARY}{msg}{C.RESET}")

def warn(msg: str):
    print(f"\n{C.WARNING}⚠  {C.PRIMARY}{msg}{C.RESET}")

def err(msg: str):
    print(f"\n{C.DANGER}✖  {C.PRIMARY}{msg}{C.RESET}")

def status_bar():
    """Barre de statut bas — equiv. sidebar-info-box"""
    print(
        f"\n{C.MUTED}● {C.SUCCESS}Système opérationnel{C.MUTED}  ·  "
        f"STARLAB v1.0  ·  © BE CORP 2026{C.RESET}\n"
    )

# ══════════════════════════════════════════════
#  MENU PRINCIPAL
# ══════════════════════════════════════════════

MENU_ITEMS = {
    "1": ("👤  Prescripteurs",       "Gestion des prescripteurs"),
    "2": ("📂  Catégories",          "Catégories d'examens"),
    "3": ("🧪  Examens",             "Catalogue des examens"),
    "4": ("📅  Décades",             "Gestion des périodes"),
    "5": ("💰  Transactions",        "Enregistrer un examen réalisé"),
    "6": ("📊  Statistiques",        "Rapports financiers"),
    "7": ("📋  Données",             "Lister toutes les données"),
    "0": ("🚪  Quitter",             ""),
}

def menu_principal():
    data = load_all_data()
    header_splash()

    while True:
        section_header("🎯 Menu Principal", "Sélectionnez une section")
        menu_box(MENU_ITEMS)
        status_bar()

        choix = prompt_choice()

        if choix == "1":
            section_header("👤 Prescripteurs", "Gestion des prescripteurs")
            prescripteurs.list_prescripteurs()
            prescripteurs.add_prescripteur()

        elif choix == "2":
            section_header("📂 Catégories", "Catégories d'examens")
            categories_examens.list_categories()
            categories_examens.add_categorie()

        elif choix == "3":
            section_header("🧪 Examens", "Catalogue des examens")
            examens.list_examens()
            examens.add_examen()

        elif choix == "4":
            section_header("📅 Décades", "Gestion des périodes")
            decades.list_decades()
            rep = prompt_choice("Générer les décades pour une année ? (o/n)")
            if rep.lower() == "o":
                decades.generate_decades_for_year()
            else:
                warn("Opération annulée.")

        elif choix == "5":
            section_header("💰 Transactions", "Enregistrement d'un examen réalisé")
            transactions.add_transaction()

        elif choix == "6":
            section_header("📊 Statistiques Financières", "Rapports et analyses")
            statistiques.afficher_statistiques()

        elif choix == "7":
            section_header("📋 Données complètes", "Export JSON")
            ok("Consultez le fichier  data/starlab_data.json  pour les données brutes.")

        elif choix == "0":
            print()
            line("═", 54, C.ACCENT)
            print(f"{C.ACCENT}  👋  {C.PRIMARY}Au revoir !  {C.SECONDARY}À bientôt au laboratoire STARLAB.{C.RESET}")
            line("═", 54, C.ACCENT)
            print()
            break

        else:
            err(f"Option « {choix} » invalide. Veuillez choisir parmi les options affichées.")

if __name__ == "__main__":
    menu_principal()