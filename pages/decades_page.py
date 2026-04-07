import streamlit as st
import pandas as pd
from modules.data_manager import load_data, save_data, get_next_id
from datetime import datetime
import time

MOIS = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
PERIODES = ["1ère décade", "2ème décade", "3ème décade"]

# ====================== MODALS (DIALOGS) ======================
@st.dialog("🚀 Générer des Décades")
def modal_generate_decades():
    """
    Fenêtre modale pour la génération automatique des décades pour une année donnée.
    """
    st.markdown("##### Paramètres de génération")
    st.write("Le système va créer automatiquement les 36 périodes (décades) pour l'année choisie.")
    
    annee = st.number_input("Année à générer", value=datetime.now().year, min_value=2020, max_value=2050)
    
    data = load_data()
    annee_exist = any(d["annee"] == annee for d in data["decades"])
    
    if annee_exist:
        st.warning(f"⚠️ Les décades pour l'année {annee} sont déjà présentes dans la base de données.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 Lancer la génération automatique", type="primary", use_container_width=True):
        if annee_exist:
            st.error("Opération annulée : Cette année existe déjà.")
        else:
            from modules.decades import generate_decades
            count = generate_decades(int(annee))
            st.toast(f"✅ Succès : {count} décades ont été générées pour {annee} !", icon="🎉")
            time.sleep(0.5)
            st.rerun()

@st.dialog("🗑️ Supprimer une Année")
def modal_delete_year():
    """
    Fenêtre modale pour supprimer toutes les décades d'une année spécifique.
    """
    data = load_data()
    if not data["decades"]:
        st.info("Aucune donnée disponible à supprimer.")
        return
        
    annees_dispo = sorted(list(set(d["annee"] for d in data["decades"])))
    annee_del = st.selectbox("Sélectionner l'année à retirer", annees_dispo)
    
    # Vérification de sécurité (dépendances avec les transactions)
    decades_ids = [d["id"] for d in data["decades"] if d["annee"] == annee_del]
    used = any(t["decade_id"] in decades_ids for t in data["transactions"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if used:
        st.error(f"⚠️ Impossible de supprimer {annee_del} : des transactions financières sont liées à cette période.")
        if st.button("Fermer la fenêtre", use_container_width=True):
            st.rerun()
    else:
        st.warning(f"Attention : Cette action est irréversible. Toutes les décades de l'année {annee_del} seront supprimées.")
        if st.button(f"🔥 Confirmer la suppression de {annee_del}", type="secondary", use_container_width=True):
            data["decades"] = [d for d in data["decades"] if d["annee"] != annee_del]
            save_data(data)
            st.toast(f"✅ L'année {annee_del} a été retirée avec succès.", icon="🗑️")
            time.sleep(0.5)
            st.rerun()

def show():
    """
    Point d'entrée pour l'affichage de la page de gestion des décades (périodes temporelles).
    """
    data = load_data()
    
    # --- HEADER SECTION ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1.5])
    with c1:
        st.title("📅 Gestion des Décades")
        st.caption("Configurez les périodes temporelles pour la facturation et les rapports statistiques.")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 Générer", type="primary", use_container_width=True, help="Créer une nouvelle année"):
                modal_generate_decades()
        with col_btn2:
            if st.button("🗑️ Purger", type="secondary", use_container_width=True, help="Supprimer une année complète"):
                modal_delete_year()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- MAIN CONTENT ---
    st.markdown('<div class="card p-4 border-0 shadow-sm" style="border-radius: 16px;">', unsafe_allow_html=True)
    
    if data["decades"]:
        df = pd.DataFrame(data["decades"])
        
        # Filtres rapides de visualisation
        st.markdown("##### 🔍 Filtrage et Recherche")
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            annees = sorted(list(df["annee"].unique()), reverse=True)
            sel_annee = st.selectbox("Filtrer par année", annees, label_visibility="collapsed")
            df = df[df["annee"] == sel_annee]
            
        with col_f2:
            search = st.text_input("Rechercher un mois ou une période...", label_visibility="collapsed")
            if search:
                df = df[df['periode'].str.contains(search, case=False) | df['mois'].str.contains(search, case=False)]

        st.markdown("<br>", unsafe_allow_html=True)
        
        st.info("💡 Cliquez sur Détails pour voir les statistiques d'une décade.")
        
        # Affichage du tableau avec boutons
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 2, 1, 2, 2, 2])
            with col1:
                st.write(row['id'])
            with col2:
                st.write(row['periode'])
            with col3:
                st.write(row['mois'])
            with col4:
                st.write(row['annee'])
            with col5:
                st.write(row['date_debut'])
            with col6:
                st.write(row['date_fin'])
            with col7:
                if st.button("🔍 Détails", key=f"detail_{row['id']}"):
                    # Afficher les détails dans une modale ou changer de page
                    nb_trans = len([t for t in data["transactions"] if t["decade_id"] == row["id"]])
                    st.info(f"📊 {row['periode']} {row['mois']} {row['annee']} : {nb_trans} transaction(s)")
            st.divider()
    else:
        st.info("Aucune période n'est configurée. Utilisez le bouton 'Générer' pour initialiser le système.")
    
    st.markdown('</div>', unsafe_allow_html=True)