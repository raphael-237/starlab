import streamlit as st
import pandas as pd
from modules.data_manager import load_data, save_data, get_next_id
import time

# ====================== MODALS ======================
@st.dialog("➕ Nouvel Examen")
def modal_add_examen():
    """
    Fenêtre modale pour ajouter un nouvel examen au catalogue.
    """
    data = load_data()
    
    with st.container():
        nom = st.text_input("Désignation de l'examen", placeholder="Ex: NFS, Glycémie...")
        prix = st.number_input("Prix de vente (FCFA)", min_value=0, step=500)
        
        cat_options = {c["nom"]: c["id"] for c in data["categories"]}
        if not cat_options:
            st.error("⚠️ Veuillez d'abord créer une catégorie.")
            return
        cat_name = st.selectbox("Sélectionner la catégorie", list(cat_options.keys()))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Ajouter au catalogue", type="primary", use_container_width=True):
            if nom.strip():
                data["examens"].append({
                    "id": get_next_id(data["examens"]),
                    "nom": nom.strip(),
                    "prix": int(prix),
                    "categorie_id": cat_options[cat_name]
                })
                save_data(data)
                st.toast(f"✅ L'examen '{nom}' a été ajouté avec succès !", icon="🧪")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Le nom de l'examen est requis.")

@st.dialog("✏️ Modifier l'Examen")
def modal_edit_examen(ex_id):
    """
    Fenêtre modale pour modifier les détails d'un examen existant.
    """
    data = load_data()
    selected = next(e for e in data["examens"] if e["id"] == ex_id)
    
    with st.container():
        new_nom = st.text_input("Désignation", value=selected["nom"])
        new_prix = st.number_input("Prix de vente (FCFA)", value=int(selected["prix"]), min_value=0, step=500)
        
        cat_options = {c["nom"]: c["id"] for c in data["categories"]}
        inv_cat = {v: k for k, v in cat_options.items()}
        current_cat_name = inv_cat.get(selected["categorie_id"], list(cat_options.keys())[0] if cat_options else "")
        
        if cat_options:
            new_cat = st.selectbox("Catégorie", list(cat_options.keys()), 
                                   index=list(cat_options.keys()).index(current_cat_name) if current_cat_name in cat_options else 0)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 Mettre à jour les informations", type="primary", use_container_width=True):
            if new_nom.strip():
                for e in data["examens"]:
                    if e["id"] == ex_id:
                        e["nom"] = new_nom.strip()
                        e["prix"] = int(new_prix)
                        if cat_options:
                            e["categorie_id"] = cat_options[new_cat]
                        break
                save_data(data)
                st.toast("✅ Examen mis à jour avec succès !", icon="💾")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Le nom ne peut pas être vide.")

@st.dialog("🗑️ Confirmer la suppression")
def modal_confirm_delete(ex_id, ex_nom):
    """
    Fenêtre modale de confirmation de suppression.
    """
    data = load_data()
    transactions_liees = [t for t in data["transactions"] if t["examen_id"] == ex_id]
    
    if transactions_liees:
        st.error(f"⚠️ Impossible de supprimer : {len(transactions_liees)} transaction(s) sont liées à cet examen.")
        if st.button("Fermer", use_container_width=True):
            st.rerun()
    else:
        st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer l'examen **{ex_nom}** ?")
        st.caption("Cette action est irréversible.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Annuler", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("✅ Confirmer la suppression", type="primary", use_container_width=True):
                data["examens"] = [e for e in data["examens"] if e["id"] != ex_id]
                save_data(data)
                st.toast(f"🗑️ L'examen '{ex_nom}' a été retiré du catalogue.", icon="✅")
                time.sleep(0.5)
                st.rerun()

def show():
    """
    Point d'entrée pour l'affichage de la page de gestion du catalogue d'examens.
    """
    data = load_data()
    
    # --- HEADER SECTION ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("🧪 Catalogue des Examens")
        st.caption("Gérez les types d'examens pratiqués et leurs tarifs.")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if not data["categories"]:
            st.warning("⚠️ Créez d'abord une catégorie avant d'ajouter des examens.")
        elif st.button("➕ Nouvel Examen", type="primary", use_container_width=True):
            modal_add_examen()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- MAIN CONTENT ---
    st.markdown('<div class="card p-4 border-0 shadow-sm" style="border-radius: 16px;">', unsafe_allow_html=True)
    
    if data["examens"]:
        df = pd.DataFrame(data["examens"])
        cat_dict = {c["id"]: c["nom"] for c in data["categories"]}
        df["Catégorie"] = df["categorie_id"].map(cat_dict)
        
        # Barre de recherche
        col_search, _ = st.columns([2, 1])
        with col_search:
            search = st.text_input("🔍 Rechercher un examen", placeholder="Nom de l'examen...", label_visibility="collapsed")
        
        df_filtered = df.copy()
        if search:
            df_filtered = df_filtered[df_filtered['nom'].str.contains(search, case=False)]

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Configuration des colonnes
        column_config = {
            "id": st.column_config.NumberColumn("ID", width="small", format="%d"),
            "nom": st.column_config.TextColumn("Désignation", width="large"),
            "Catégorie": st.column_config.TextColumn("Catégorie", width="medium"),
            "prix": st.column_config.NumberColumn("Prix (FCFA)", width="medium", format="%d"),
        }
        
        # Affichage du dataframe
        st.dataframe(
            df_filtered[["id", "nom", "Catégorie", "prix"]],
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
        
        st.markdown("---")
        st.caption("💡 Cliquez sur les boutons ci-dessous pour gérer un examen")
        
        # Affichage des boutons d'action
        for _, row in df_filtered.iterrows():
            col1, col2, col3, col4, col5 = st.columns([0.5, 3, 2, 1.5, 2])
            with col1:
                st.write(f"**#{row['id']}**")
            with col2:
                st.write(row['nom'])
            with col3:
                st.write(row['Catégorie'])
            with col4:
                st.write(f"{row['prix']:,.0f} FCFA")
            with col5:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✏️ Modifier", key=f"edit_{row['id']}"):
                        modal_edit_examen(row['id'])
                with btn_col2:
                    if st.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                        modal_confirm_delete(row['id'], row['nom'])
    else:
        st.info("📭 Le catalogue d'examens est actuellement vide.")
    
    st.markdown('</div>', unsafe_allow_html=True)