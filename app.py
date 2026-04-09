import streamlit as st
import os
import base64
from datetime import datetime

# ====================== UTILS ======================
def get_base64_of_bin_file(bin_file):
    """
    Encode un fichier binaire en base64 pour l'inclusion dans le HTML/CSS.
    :param bin_file: Chemin vers le fichier binaire.
    :return: Chaîne encodée en base64.
    """
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        return ""

# ====================== CONFIGURATION ======================
st.set_page_config(
    page_title="STARLAB - Gestion Financière",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====================== CSS & BOOTSTRAP ======================
def load_assets():
    """
    Charge Bootstrap CDN et injecte le CSS personnalisé pour une interface moderne.
    """
    # Bootstrap CDN
    st.markdown('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">', unsafe_allow_html=True)
    
    # CSS Personnalisé
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        :root {
            --primary-color: #0d6efd;
            --bg-light: #f8fafc;
            --surface: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.06);
            --radius: 12px;
        }

        .stApp {
            background-color: var(--bg-light);
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            color: var(--text-main);
        }

        /* Masquage des éléments par défaut de Streamlit */
        [data-testid="stSidebar"], [data-testid="collapsedControl"], header {
            display: none !important;
        }

        .block-container {
            padding-top: 100px !important;
            padding-bottom: 80px !important;
        }

        /* NAVBAR SUPERIEURE */
        .top-navbar {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 80px;
            background: var(--surface);
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 40px;
            z-index: 1001;
            box-shadow: var(--shadow-md);
        }

        .nav-brand-group {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .nav-logo {
            height: 45px;
            width: auto;
            border-radius: 8px;
        }

        .brand-text h1 {
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--primary-color);
            margin: 0;
            letter-spacing: -0.5px;
        }

        .brand-text p {
            font-size: 0.65rem;
            font-weight: 700;
            color: var(--text-muted);
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1.2px;
        }

        /* NAVIGATION HORIZONTALE */
        .nav-bar-container {
            position: fixed;
            top: 80px; left: 0; right: 0;
            background: var(--surface);
            padding: 10px 40px;
            border-bottom: 1px solid #e2e8f0;
            z-index: 1000;
            display: flex;
            overflow-x: auto;
            scrollbar-width: none;
        }
        
        .nav-bar-container::-webkit-scrollbar { display: none; }

        .nav-link-custom {
            padding: 10px 20px;
            margin-right: 8px;
            border-radius: var(--radius);
            font-weight: 600;
            font-size: 0.92rem;
            color: var(--text-muted);
            text-decoration: none;
            transition: all 0.2s ease;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
            background: transparent;
            border: none;
        }

        .nav-link-custom:hover {
            color: var(--primary-color);
            background: #f1f5f9;
        }

        .nav-link-custom.active {
            color: white;
            background: var(--primary-color);
            box-shadow: 0 4px 10px rgba(13, 110, 253, 0.2);
        }

        /* CARTES ET ELEMENTS UI */
        .stButton button {
            border-radius: var(--radius) !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.2rem !important;
            transition: all 0.2s ease !important;
        }
        
        .stDataFrame {
            border-radius: var(--radius) !important;
            overflow: hidden !important;
            border: 1px solid #e2e8f0 !important;
        }

        /* FOOTER */
        .custom-footer {
            position: fixed;
            bottom: 0; left: 0; right: 0;
            padding: 12px;
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(10px);
            border-top: 1px solid #e2e8f0;
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-muted);
            z-index: 1000;
        }
        
        /* Dialog overlay style */
        div[role="dialog"] {
            border-radius: 20px !important;
            padding: 20px !important;
        }
        
        /* Toast messages */
        .stToast {
            border-radius: 12px !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_ui_header():
    """
    Rendu de la barre supérieure (Logo + Nom) et de la barre de navigation.
    """
    # 1. Barre de Logo
    logo_path = "BE CORP.png"
    logo_b64 = get_base64_of_bin_file(logo_path)
    
    st.markdown(f"""
        <div class="top-navbar">
            <div class="nav-brand-group">
                <img src="data:image/png;base64,{logo_b64}" class="nav-logo">
                <div class="brand-text">
                    <h1>STARLAB</h1>
                    <p>Gestion Financière</p>
                </div>
            </div>
            <div class="d-flex align-items-center gap-3">
                <span class="badge rounded-pill bg-light text-primary border px-3 py-2">
                    📅 {datetime.now().strftime('%d %b %Y')}
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. Navigation - Toutes les pages incluant Accueil
    pages = [
        {"name": "🏠 Accueil", "key": "Accueil"},
        {"name": "👤 Prescripteurs", "key": "Prescripteurs"},
        {"name": "📂 Catégories", "key": "Catégories"},
        {"name": "🧪 Examens", "key": "Examens"},
        {"name": "📅 Décades", "key": "Décades"},
        {"name": "💰 Transactions", "key": "Transactions"},
        {"name": "📊 Statistiques Financières", "key": "Statistiques Financières"},
        {"name": "👨‍⚕️ Stats Prescripteurs", "key": "Statistiques par Prescripteur"}
    ]

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Accueil"

    # Affichage horizontal de la navigation
    cols = st.columns(len(pages))
    
    st.markdown('<div class="nav-bar-container">', unsafe_allow_html=True)
    
    with st.container():
        for i, page in enumerate(pages):
            is_active = st.session_state.current_page == page["key"]
            with cols[i]:
                if st.button(page["name"], key=f"nav_{i}", use_container_width=True, 
                             type="primary" if is_active else "secondary"):
                    st.session_state.current_page = page["key"]
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_footer():
    """
    Rendu du pied de page.
    """
    st.markdown(f"""
        <div class="custom-footer">
            © {datetime.now().year} <b>STARLAB</b> • créé par <span class="text-primary fw-bold">BE CORP</span>
        </div>
    """, unsafe_allow_html=True)

# ====================== MAIN ======================
def main():
    """
    Point d'entrée principal de l'application.
    """
    load_assets()
    render_ui_header()
    
    # Routage des pages
    selected = st.session_state.current_page
    
    # Conteneur principal pour le contenu de la page
    with st.container():
        if selected == "Accueil":
            from pages.accueil import show; show()
        elif selected == "Prescripteurs":
            from pages.prescripteurs_page import show; show()
        elif selected == "Catégories":
            from pages.categories_page import show; show()
        elif selected == "Examens":
            from pages.examens_page import show; show()
        elif selected == "Décades":
            from pages.decades_page import show; show()
        elif selected == "Transactions":
            from pages.transactions_page import show; show()
        elif selected == "Rapport Annuel":
            from pages.rapport_annuel_page import show; show()    
        elif selected == "Statistiques Financières":
            from pages.statistiques_page import show; show()
        elif selected == "Statistiques par Prescripteur":
            from pages.statistiques_prescripteur_page import show; show()

    render_footer()

if __name__ == "__main__":
    main()