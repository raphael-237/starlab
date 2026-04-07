import streamlit as st
import pandas as pd
from modules.data_manager import load_data, save_data, get_next_id
import time

# ====================== MODALS (DIALOGS) ======================
@st.dialog("➕ Ajouter un Prescripteur")
def modal_add_prescripteur():
    """
    Fenêtre modale pour ajouter un nouveau prescripteur.
    """
    data = load_data()
    
    with st.container():
        nom_base = st.text_input("Nom du prescripteur", placeholder="Ex: Koné")
        est_medecin = st.checkbox("👨‍⚕️ Médecin", value=True)
        service = st.text_input("Service / Département", placeholder="Ex: Cardiologie...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Enregistrer", type="primary", use_container_width=True):
            if nom_base.strip() and service.strip():
                titre = "Dr." if est_medecin else "Mme."
                nom_complet = f"{titre} {nom_base.strip()}"
                
                data["prescripteurs"].append({
                    "id": get_next_id(data["prescripteurs"]),
                    "nom": nom_complet, 
                    "service": service.strip()
                })
                save_data(data)
                st.toast(f"✅ {nom_complet} ajouté avec succès !", icon="🎉")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Veuillez remplir tous les champs obligatoires.")

@st.dialog("✏️ Modifier le Prescripteur")
def modal_edit_prescripteur(pres_id):
    """
    Fenêtre modale pour modifier les informations d'un prescripteur existant.
    """
    data = load_data()
    selected = next(p for p in data["prescripteurs"] if p["id"] == pres_id)
    
    with st.container():
        new_nom = st.text_input("Nom complet", value=selected["nom"])
        new_service = st.text_input("Service", value=selected["service"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 Mettre à jour", type="primary", use_container_width=True):
            if new_nom.strip() and new_service.strip():
                for p in data["prescripteurs"]:
                    if p["id"] == pres_id:
                        p["nom"], p["service"] = new_nom.strip(), new_service.strip()
                        break
                save_data(data)
                st.toast("✅ Modifications enregistrées avec succès !", icon="💾")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Les champs ne peuvent pas être vides.")

@st.dialog("🗑️ Confirmer la suppression")
def modal_confirm_delete(pres_id, pres_nom):
    """
    Fenêtre modale de confirmation de suppression.
    """
    st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer **{pres_nom}** ?")
    st.caption("Cette action est irréversible.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Annuler", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("✅ Confirmer la suppression", type="primary", use_container_width=True):
            data = load_data()
            data["prescripteurs"] = [p for p in data["prescripteurs"] if p["id"] != pres_id]
            save_data(data)
            st.toast(f"🗑️ {pres_nom} a été supprimé.", icon="✅")
            time.sleep(0.5)
            st.rerun()

def show():
    """
    Point d'entrée pour l'affichage de la page de gestion des prescripteurs.
    """
    data = load_data()
    
    # Initialisation de l'état pour l'action sélectionnée
    if "selected_action_id" not in st.session_state:
        st.session_state.selected_action_id = None
    if "selected_action_type" not in st.session_state:
        st.session_state.selected_action_type = None
    
    # --- HEADER SECTION ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("👤 Prescripteurs")
        st.caption("Gérez le réseau médical et les services partenaires de STARLAB.")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Nouveau Prescripteur", type="primary", use_container_width=True):
            modal_add_prescripteur()
    st.markdown('</div>', unsafe_allow_html=True)

    # Traitement des actions
    if st.session_state.selected_action_id and st.session_state.selected_action_type:
        if st.session_state.selected_action_type == "edit":
            modal_edit_prescripteur(st.session_state.selected_action_id)
        elif st.session_state.selected_action_type == "delete":
            pres_nom = next((p["nom"] for p in data["prescripteurs"] if p["id"] == st.session_state.selected_action_id), "")
            modal_confirm_delete(st.session_state.selected_action_id, pres_nom)
        st.session_state.selected_action_id = None
        st.session_state.selected_action_type = None

    # --- MAIN CONTENT ---
    st.markdown('<div class="card p-4 border-0 shadow-sm" style="border-radius: 16px;">', unsafe_allow_html=True)
    df = pd.DataFrame(data["prescripteurs"])
    
    if not df.empty:
        # Barre de recherche
        col_search, col_placeholder = st.columns([2, 1])
        with col_search:
            search = st.text_input("🔍 Rechercher", placeholder="Nom ou service...", label_visibility="collapsed")
        
        df_filtered = df.copy()
        if search:
            df_filtered = df_filtered[df_filtered['nom'].str.contains(search, case=False) | 
                                      df_filtered['service'].str.contains(search, case=False)]

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Configuration des colonnes du dataframe
        column_config = {
            "id": st.column_config.NumberColumn("ID", width="small", format="%d"),
            "nom": st.column_config.TextColumn("Nom Complet", width="large"),
            "service": st.column_config.TextColumn("Service", width="medium"),
        }
        
        # Affichage du dataframe
        st.dataframe(
            df_filtered[["id", "nom", "service"]],
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
        
        st.markdown("---")
        st.caption("💡 Cliquez sur les boutons ci-dessous pour gérer un prescripteur")
        
        # Affichage des boutons d'action par ligne (plus compact)
        for _, row in df_filtered.iterrows():
            col1, col2, col3, col4 = st.columns([0.5, 3, 2, 1.5])
            with col1:
                st.write(f"**#{row['id']}**")
            with col2:
                st.write(row['nom'])
            with col3:
                st.write(row['service'])
            with col4:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✏️", key=f"edit_{row['id']}", help="Modifier"):
                        modal_edit_prescripteur(row['id'])
                with btn_col2:
                    if st.button("🗑️", key=f"del_{row['id']}", help="Supprimer"):
                        modal_confirm_delete(row['id'], row['nom'])
    else:
        st.info("📭 Aucun prescripteur n'a été enregistré pour le moment.")
    
    st.markdown('</div>', unsafe_allow_html=True)