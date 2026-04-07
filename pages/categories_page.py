import streamlit as st
import pandas as pd
from modules.data_manager import load_data, save_data, get_next_id
import time

# ====================== MODALS ======================
@st.dialog("➕ Nouvelle Catégorie")
def modal_add_categorie():
    """
    Fenêtre modale pour la création d'une nouvelle catégorie d'examens.
    """
    data = load_data()
    
    with st.container():
        nom = st.text_input("Nom de la catégorie", placeholder="Ex: Biochimie, Hématologie...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Créer la catégorie", type="primary", use_container_width=True):
            if nom.strip():
                data["categories"].append({
                    "id": get_next_id(data["categories"]), 
                    "nom": nom.strip()
                })
                save_data(data)
                st.toast(f"✅ Catégorie '{nom}' créée avec succès !", icon="📂")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Le nom de la catégorie est obligatoire.")

@st.dialog("✏️ Modifier la Catégorie")
def modal_edit_categorie(cat_id):
    """
    Fenêtre modale pour modifier le nom d'une catégorie existante.
    """
    data = load_data()
    selected = next(c for c in data["categories"] if c["id"] == cat_id)
    
    with st.container():
        new_nom = st.text_input("Nouveau nom de la catégorie", value=selected["nom"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 Enregistrer les modifications", type="primary", use_container_width=True):
            if new_nom.strip():
                for c in data["categories"]:
                    if c["id"] == cat_id:
                        c["nom"] = new_nom.strip()
                        break
                save_data(data)
                st.toast("✅ Catégorie mise à jour avec succès !", icon="💾")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Le nom ne peut pas être vide.")

@st.dialog("🗑️ Confirmer la suppression")
def modal_confirm_delete(cat_id, cat_nom):
    """
    Fenêtre modale de confirmation de suppression.
    """
    data = load_data()
    examens_lies = [e for e in data["examens"] if e["categorie_id"] == cat_id]
    
    if examens_lies:
        st.error(f"⚠️ Impossible de supprimer : {len(examens_lies)} examen(s) sont liés à cette catégorie.")
        if st.button("Fermer", use_container_width=True):
            st.rerun()
    else:
        st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer la catégorie **{cat_nom}** ?")
        st.caption("Cette action est irréversible.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Annuler", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("✅ Confirmer la suppression", type="primary", use_container_width=True):
                data["categories"] = [c for c in data["categories"] if c["id"] != cat_id]
                save_data(data)
                st.toast(f"🗑️ Catégorie '{cat_nom}' supprimée.", icon="✅")
                time.sleep(0.5)
                st.rerun()

def show():
    """
    Point d'entrée pour l'affichage de la page de gestion des catégories.
    """
    data = load_data()
    
    # --- HEADER SECTION ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("📂 Catégories")
        st.caption("Organisez votre catalogue d'examens par spécialités médicales.")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Nouvelle Catégorie", type="primary", use_container_width=True):
            modal_add_categorie()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- MAIN CONTENT ---
    st.markdown('<div class="card p-4 border-0 shadow-sm" style="border-radius: 16px;">', unsafe_allow_html=True)
    df = pd.DataFrame(data["categories"])
    
    if not df.empty:
        # Barre de recherche
        col_search, _ = st.columns([2, 1])
        with col_search:
            search = st.text_input("🔍 Rechercher une catégorie", placeholder="Nom de la catégorie...", label_visibility="collapsed")
        
        df_filtered = df.copy()
        if search:
            df_filtered = df_filtered[df_filtered['nom'].str.contains(search, case=False)]

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Configuration des colonnes
        column_config = {
            "id": st.column_config.NumberColumn("ID", width="small", format="%d"),
            "nom": st.column_config.TextColumn("Désignation", width="large"),
        }
        
        # Affichage du dataframe
        st.dataframe(
            df_filtered[["id", "nom"]],
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
        
        st.markdown("---")
        st.caption("💡 Cliquez sur les boutons ci-dessous pour gérer une catégorie")
        
        # Affichage des boutons d'action
        for _, row in df_filtered.iterrows():
            col1, col2, col3 = st.columns([0.5, 6, 2])
            with col1:
                st.write(f"**#{row['id']}**")
            with col2:
                st.write(row['nom'])
            with col3:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✏️ Modifier", key=f"edit_{row['id']}"):
                        modal_edit_categorie(row['id'])
                with btn_col2:
                    if st.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                        modal_confirm_delete(row['id'], row['nom'])
    else:
        st.info("📭 Aucune catégorie n'a encore été définie dans le système.")
    
    st.markdown('</div>', unsafe_allow_html=True)