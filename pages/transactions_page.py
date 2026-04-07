import streamlit as st
import pandas as pd
from modules.data_manager import load_data, save_data, get_next_id
from datetime import datetime
import time

# ====================== MODALS ======================
@st.dialog("➕ Nouvelle Transaction")
def modal_add_transaction():
    """
    Fenêtre modale pour l'ajout de transactions au panier temporaire.
    """
    data = load_data()
    if "temp_transactions" not in st.session_state: 
        st.session_state.temp_transactions = []
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            pres_options = {p["nom"]: p["id"] for p in data["prescripteurs"]}
            if not pres_options:
                st.error("Aucun prescripteur disponible.")
                return
            pres_sel = st.selectbox("👤 Prescripteur", list(pres_options.keys()))
            
            dec_options = {f"{d['periode']} - {d['mois']} {d['annee']}": d["id"] for d in data["decades"]}
            if not dec_options:
                st.error("Aucune décade disponible.")
                return
            dec_sel = st.selectbox("📅 Décade de facturation", list(dec_options.keys()), 
                                   index=len(dec_options)-1 if dec_options else 0)
            
        with col2:
            ex_options = {f"{e['nom']} ({e['prix']:,.0f} FCFA)": e["id"] for e in data["examens"]}
            if not ex_options:
                st.error("Aucun examen disponible.")
                return
            ex_sel = st.selectbox("🧪 Type d'Examen", list(ex_options.keys()))
            
            q_payee = st.number_input("Quantité PAYÉE", min_value=0, step=1, value=1)
            q_gratuite = st.number_input("Quantité GRATUITE", min_value=0, step=1, value=0)

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🛒 Ajouter au panier", type="primary", use_container_width=True):
            if q_payee == 0 and q_gratuite == 0:
                st.error("Veuillez saisir au moins une quantité (payée ou gratuite).")
            else:
                ex_id = ex_options[ex_sel]
                ex_obj = next(e for e in data["examens"] if e["id"] == ex_id)
                
                st.session_state.temp_transactions.append({
                    "prescripteur_id": pres_options[pres_sel], 
                    "Prescripteur": pres_sel,
                    "examen_id": ex_id, 
                    "Examen": ex_obj["nom"],
                    "decade_id": dec_options[dec_sel], 
                    "Décade": dec_sel,
                    "Payé": int(q_payee), 
                    "Gratuit": int(q_gratuite),
                    "Montant": int(q_payee * ex_obj["prix"])
                })
                st.toast(f"Ajouté : {ex_obj['nom']}", icon="🛒")
                st.rerun()

@st.dialog("✏️ Modifier Transaction")
def modal_edit_transaction(trans_id):
    """
    Fenêtre modale pour modifier une transaction déjà enregistrée dans l'historique.
    """
    data = load_data()
    t_idx = next(i for i, t in enumerate(data["transactions"]) if t["id"] == trans_id)
    t = data["transactions"][t_idx]
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            pres_options = {p["nom"]: p["id"] for p in data["prescripteurs"]}
            pres_name = next((k for k, v in pres_options.items() if v == t["prescripteur_id"]), list(pres_options.keys())[0])
            new_pres = st.selectbox("Prescripteur", list(pres_options.keys()), 
                                    index=list(pres_options.keys()).index(pres_name))
            
            dec_options = {f"{d['periode']} - {d['mois']} {d['annee']}": d["id"] for d in data["decades"]}
            dec_name = next((k for k, v in dec_options.items() if v == t["decade_id"]), list(dec_options.keys())[0])
            new_dec = st.selectbox("Décade", list(dec_options.keys()), 
                                    index=list(dec_options.keys()).index(dec_name))
            
        with col2:
            ex_options = {f"{e['nom']} ({e['prix']:,.0f} FCFA)": e["id"] for e in data["examens"]}
            ex_name = next((k for k, v in ex_options.items() if v == t["examen_id"]), list(ex_options.keys())[0])
            new_ex = st.selectbox("Examen", list(ex_options.keys()), 
                                   index=list(ex_options.keys()).index(ex_name))
            
            new_p = st.number_input("Qté Payée", value=int(t["quantite_payee"]), min_value=0)
            new_g = st.number_input("Qté Gratuite", value=int(t["quantite_gratuite"]), min_value=0)

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 Enregistrer les modifications", type="primary", use_container_width=True):
            data["transactions"][t_idx].update({
                "prescripteur_id": pres_options[new_pres], 
                "examen_id": ex_options[new_ex],
                "decade_id": dec_options[new_dec], 
                "quantite_payee": int(new_p), 
                "quantite_gratuite": int(new_g)
            })
            save_data(data)
            st.toast("✅ Transaction mise à jour !", icon="💾")
            time.sleep(0.5)
            st.rerun()

@st.dialog("🗑️ Confirmer la suppression")
def modal_confirm_delete(trans_id, trans_ref):
    """
    Fenêtre modale de confirmation de suppression.
    """
    st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer la transaction **{trans_ref}** ?")
    st.caption("Cette action est irréversible.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Annuler", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("✅ Confirmer la suppression", type="primary", use_container_width=True):
            data = load_data()
            data["transactions"] = [t for t in data["transactions"] if t["id"] != trans_id]
            save_data(data)
            st.toast("🗑️ Transaction supprimée de l'historique.", icon="✅")
            time.sleep(0.5)
            st.rerun()

def show():
    """
    Point d'entrée pour l'affichage de la page de saisie et d'historique des transactions.
    """
    data = load_data()
    if "temp_transactions" not in st.session_state: 
        st.session_state.temp_transactions = []

    # --- HEADER SECTION ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("💰 Transactions")
        st.caption("Enregistrez les prestations et gérez l'historique financier du laboratoire.")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Nouvelle Saisie", type="primary", use_container_width=True):
            if not data["prescripteurs"] or not data["examens"] or not data["decades"]:
                st.error("Veuillez configurer les Prescripteurs, Examens et Décades avant de saisir.")
            else:
                modal_add_transaction()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- PANIER EN COURS (SI NON VIDE) ---
    if st.session_state.temp_transactions:
        st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px; border-left: 5px solid #ffc107 !important;">', unsafe_allow_html=True)
        st.subheader("🛒 Panier en attente de validation")
        
        df_p = pd.DataFrame(st.session_state.temp_transactions)
        st.dataframe(df_p[["Prescripteur", "Examen", "Décade", "Payé", "Gratuit", "Montant"]], 
                     use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        ca1, ca2 = st.columns(2)
        with ca1:
            if st.button("💾 Valider et enregistrer tout le panier", type="primary", use_container_width=True):
                nid = get_next_id(data["transactions"])
                for item in st.session_state.temp_transactions:
                    data["transactions"].append({
                        "id": nid, 
                        "examen_id": item["examen_id"], 
                        "prescripteur_id": item["prescripteur_id"],
                        "quantite_payee": item["Payé"], 
                        "quantite_gratuite": item["Gratuit"],
                        "decade_id": item["decade_id"], 
                        "date_enregistrement": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    nid += 1
                save_data(data)
                st.session_state.temp_transactions = []
                st.toast("🚀 Panier enregistré avec succès !", icon="✅")
                time.sleep(0.5)
                st.rerun()
        with ca2:
            if st.button("🗑️ Vider le panier", use_container_width=True, type="secondary"):
                st.session_state.temp_transactions = []
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- HISTORIQUE DATAGRID ---
    st.markdown('<div class="card p-4 border-0 shadow-sm" style="border-radius: 16px;">', unsafe_allow_html=True)
    st.subheader("📋 Historique des transactions")
    
    records = []
    ex_dict = {e["id"]: e for e in data["examens"]}
    pr_dict = {p["id"]: p["nom"] for p in data["prescripteurs"]}
    
    for t in data["transactions"]:
        ex = ex_dict.get(t["examen_id"])
        if ex:
            records.append({
                "ID": t["id"], 
                "Date": t["date_enregistrement"][:10],
                "Prescripteur": pr_dict.get(t["prescripteur_id"], "Inconnu"),
                "Examen": ex["nom"], 
                "Payé": t["quantite_payee"],
                "Montant": t["quantite_payee"] * ex["prix"]
            })
    
    df = pd.DataFrame(records)
    if not df.empty:
        # Barre de recherche
        col_search, _ = st.columns([2, 1])
        with col_search:
            search = st.text_input("🔍 Rechercher", placeholder="Prescripteur ou examen...", label_visibility="collapsed")
        
        df_filtered = df.copy()
        if search:
            df_filtered = df_filtered[df_filtered['Prescripteur'].str.contains(search, case=False) | 
                                      df_filtered['Examen'].str.contains(search, case=False)]

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Configuration des colonnes
        column_config = {
            "ID": st.column_config.NumberColumn("ID", width="small", format="%d"),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Prescripteur": st.column_config.TextColumn("Prescripteur", width="medium"),
            "Examen": st.column_config.TextColumn("Examen", width="large"),
            "Payé": st.column_config.NumberColumn("Qté Payée", width="small", format="%d"),
            "Montant": st.column_config.NumberColumn("Montant (FCFA)", width="medium", format="%d"),
        }
        
        # Affichage du dataframe trié
        st.dataframe(
            df_filtered[["ID", "Date", "Prescripteur", "Examen", "Payé", "Montant"]].sort_values(by="ID", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
        
        st.markdown("---")
        st.caption("💡 Cliquez sur les boutons ci-dessous pour gérer une transaction")
        
        # Affichage des boutons d'action
        for _, row in df_filtered.sort_values(by="ID", ascending=False).iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 1, 2, 2.5, 0.8, 1.5, 1.5])
            with col1:
                st.write(f"**#{row['ID']}**")
            with col2:
                st.write(row['Date'])
            with col3:
                st.write(row['Prescripteur'])
            with col4:
                st.write(row['Examen'])
            with col5:
                st.write(row['Payé'])
            with col6:
                st.write(f"{row['Montant']:,.0f}")
            with col7:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("✏️", key=f"edit_{row['ID']}", help="Modifier"):
                        modal_edit_transaction(row['ID'])
                with btn_col2:
                    if st.button("🗑️", key=f"del_{row['ID']}", help="Supprimer"):
                        modal_confirm_delete(row['ID'], f"{row['Examen']} - {row['Prescripteur']}")
    else:
        st.info("📭 Aucune transaction n'a encore été enregistrée dans le système.")
    
    st.markdown('</div>', unsafe_allow_html=True)