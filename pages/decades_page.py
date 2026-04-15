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
    st.info("💡 Les décades existantes ne seront pas supprimées ou dupliquées.")
    
    annee = st.number_input("Année à générer", value=datetime.now().year, min_value=2020, max_value=2050)
    
    data = load_data()
    annee_exist = any(d["annee"] == annee for d in data["decades"])
    
    if annee_exist:
        st.warning(f"⚠️ Certaines décades pour l'année {annee} existent déjà. Seules celles manquantes seront ajoutées.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 Lancer la génération automatique", type="primary", use_container_width=True):
        from modules.decades import generate_decades
        count = generate_decades(int(annee))
        if count > 0:
            st.toast(f"✅ Succès : {count} nouvelles décades ont été générées pour {annee} !", icon="🎉")
        else:
            st.toast(f"ℹ️ Aucune nouvelle décade à ajouter pour {annee}. Toutes existent déjà.", icon="ℹ️")
        time.sleep(0.5)
        st.rerun()

@st.dialog("🗑️ Supprimer une Année")
def modal_delete_year():
    """
    Fenêtre modale pour supprimer toutes les décades d'une année spécifique.
    La suppression est bloquée si des transactions sont liées à ces décades.
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
    
    # Compter le nombre de transactions liées
    transactions_count = sum(1 for t in data["transactions"] if t["decade_id"] in decades_ids)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if used:
        st.error(f"⚠️ Impossible de supprimer {annee_del} : {transactions_count} transaction(s) financière(s) sont liées à cette période.")
        st.info("💡 Pour préserver l'intégrité des données, les décades associées à des transactions ne peuvent pas être supprimées.")
        if st.button("Fermer la fenêtre", use_container_width=True):
            st.rerun()
    else:
        st.warning(f"Attention : Cette action est irréversible. Toutes les décades de l'année {annee_del} seront supprimées.")
        st.caption(f"📊 {len(decades_ids)} décade(s) seront supprimées.")
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
            if st.button("🚀 Générer", type="primary", use_container_width=True, help="Ajouter une nouvelle année"):
                modal_generate_decades()
        with col_btn2:
            if st.button("🗑️ Purger", type="secondary", use_container_width=True, help="Supprimer une année complète (si aucune transaction liée)"):
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
            # Vérifier si la décade a des transactions
            nb_trans = len([t for t in data["transactions"] if t["decade_id"] == row["id"]])
            has_transactions = nb_trans > 0
            
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
                if st.button(f"🔍 Détails ({nb_trans})", key=f"detail_{row['id']}"):
                    st.info(f"📊 {row['periode']} {row['mois']} {row['annee']} : {nb_trans} transaction(s)")
            st.divider()
        
        # Afficher un résumé des statistiques
        st.markdown("---")
        st.markdown("### 📊 Statistiques des décades")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_decades = len(data["decades"])
            st.metric("📅 Total décades", total_decades)
        with col2:
            annees_dispo = sorted(list(set(d["annee"] for d in data["decades"])))
            st.metric("📆 Années disponibles", len(annees_dispo))
        with col3:
            decades_with_transactions = len(set(t["decade_id"] for t in data["transactions"]))
            st.metric("📋 Décades avec transactions", decades_with_transactions)
            
    else:
        st.info("Aucune période n'est configurée. Utilisez le bouton 'Générer' pour initialiser le système.")
    
    st.markdown('</div>', unsafe_allow_html=True)