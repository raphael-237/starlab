import streamlit as st
import pandas as pd
from modules.data_manager import load_data

def show():
    """
    Affiche le tableau de bord (Dashboard) principal avec les KPIs et graphiques.
    """
    data = load_data()
    
    # --- CSS SUPPLÉMENTAIRE POUR ACCUEIL ---
    st.markdown("""
    <style>
        .hero-section {
            background: linear-gradient(135deg, #0d6efd 0%, #0dcaf0 100%);
            padding: 50px 40px;
            border-radius: 16px;
            color: white;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(13, 110, 253, 0.25);
            position: relative;
            overflow: hidden;
        }
        
        .hero-section::after {
            content: "🔬";
            position: absolute;
            right: -20px;
            bottom: -40px;
            font-size: 200px;
            opacity: 0.1;
            transform: rotate(-15deg);
        }

        .hero-title { font-size: 2.8rem; font-weight: 800; margin-bottom: 8px; }
        .hero-sub { font-size: 1.15rem; opacity: 0.95; }

        /* KPI CARDS MODERNES */
        .kpi-card {
            background: white;
            padding: 24px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 20px rgba(0,0,0,0.08);
        }

        .kpi-label {
            font-size: 0.85rem;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }

        .kpi-value {
            font-size: 1.8rem;
            font-weight: 800;
            margin: 0;
        }
        
        /* TABLEAU ACTIVITE RECENTE */
        .activity-table-container {
            background: white;
            border-radius: 16px;
            padding: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        
        .activity-table-container h3 {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 20px;
            color: #1e293b;
        }
        
        /* Style pour le dataframe */
        .stDataFrame {
            border-radius: 12px !important;
            overflow: hidden !important;
        }
        
        /* Amélioration des boutons de navigation */
        div[data-testid="column"] button {
            border-radius: 12px !important;
            font-weight: 600 !important;
            padding: 0.6rem 1rem !important;
            transition: all 0.2s ease !important;
            border: 1px solid #e2e8f0 !important;
            background: white !important;
            color: #64748b !important;
        }
        
        div[data-testid="column"] button:hover {
            background: #f8fafc !important;
            border-color: #0d6efd !important;
            color: #0d6efd !important;
            transform: translateY(-2px);
        }
        
        div[data-testid="column"] button[data-testid="baseButton-secondary"] {
            background: white !important;
        }
        
        /* Style pour les boutons actifs */
        div[data-testid="column"] button[kind="primary"] {
            background: #0d6efd !important;
            color: white !important;
            border: none !important;
        }
        
        div[data-testid="column"] button[kind="primary"]:hover {
            background: #0b5ed7 !important;
            transform: translateY(-2px);
        }
    </style>
    """, unsafe_allow_html=True)

    # ====================== HERO ======================
    st.markdown("""
        <div class="hero-section">
            <h1 class="hero-title">BONJOUR Mme YARA</h1>
            <p class="hero-sub">Bienvenue sur STARLAB • Votre centre de contrôle financier du Laboratoire.</p>
        </div>
    """, unsafe_allow_html=True)

    # ====================== KPI CARDS ======================
    # Préparation des données pour les KPIs
    examens_dict = {e["id"]: e for e in data["examens"]}
    total_ca = sum(t["quantite_payee"] * examens_dict.get(t["examen_id"], {}).get("prix", 0) 
                   for t in data["transactions"])

    kpis = [
        {"label": "Chiffre d'Affaires", "value": f"{total_ca:,.0f} FCFA", "color": "#0d6efd"},
        {"label": "Transactions", "value": f"{len(data['transactions'])}", "color": "#0dcaf0"},
        {"label": "Prescripteurs", "value": f"{len(data['prescripteurs'])}", "color": "#198754"},
        {"label": "Examens", "value": f"{len(data['examens'])}", "color": "#ffc107"}
    ]

    cols = st.columns(4)
    for i, kpi in enumerate(kpis):
        with cols[i]:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">{kpi['label']}</div>
                    <div class="kpi-value" style="color: {kpi['color']};">{kpi['value']}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ====================== ACTIVITE RECENTE EN TABLEAU ======================
    st.markdown('<div class="activity-table-container">', unsafe_allow_html=True)
    st.subheader("🕒 Activité Récente")
    
    if data["transactions"]:
        # Récupération des 10 dernières transactions
        df_recent = pd.DataFrame(data["transactions"]).tail(10).iloc[::-1]
        
        # Création des dictionnaires pour les mappings
        pres_dict = {p["id"]: p["nom"] for p in data["prescripteurs"]}
        exam_dict = {e["id"]: e["nom"] for e in data["examens"]}
        decades_dict = {d["id"]: f"{d['mois']} {d['annee']}" for d in data["decades"]}
        
        # Ajout des colonnes lisibles
        df_recent["Prescripteur"] = df_recent["prescripteur_id"].map(pres_dict)
        df_recent["Examen"] = df_recent["examen_id"].map(exam_dict)
        df_recent["Décade"] = df_recent["decade_id"].map(decades_dict)
        df_recent["Quantité"] = df_recent["quantite_payee"]
        df_recent["Montant (FCFA)"] = df_recent.apply(
            lambda x: x["quantite_payee"] * examens_dict.get(x["examen_id"], {}).get("prix", 0), axis=1
        )
        
        # Sélection des colonnes à afficher
        display_df = df_recent[["Prescripteur", "Examen", "Décade", "Quantité", "Montant (FCFA)"]]
        
        # Formatage des montants
        display_df["Montant (FCFA)"] = display_df["Montant (FCFA)"].apply(lambda x: f"{x:,.0f}")
        
        # Affichage du tableau stylisé
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Prescripteur": st.column_config.TextColumn("Prescripteur", width="medium"),
                "Examen": st.column_config.TextColumn("Examen", width="medium"),
                "Décade": st.column_config.TextColumn("Décade", width="small"),
                "Quantité": st.column_config.NumberColumn("Quantité", width="small"),
                "Montant (FCFA)": st.column_config.TextColumn("Montant (FCFA)", width="medium"),
            }
        )
        
        # Ajout d'un résumé
        st.markdown(f"""
            <div style="margin-top: 15px; padding: 12px; background: #f8fafc; border-radius: 10px;">
                <small style="color: #64748b;">
                    📊 <strong>Total des transactions affichées :</strong> {len(df_recent)} dernières transactions
                </small>
            </div>
        """, unsafe_allow_html=True)
        
    else:
        st.info("Aucune transaction enregistrée pour le moment.")
    
    st.markdown('</div>', unsafe_allow_html=True)