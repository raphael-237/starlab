import streamlit as st
import pandas as pd
from modules.data_manager import load_data, save_data
from modules.patient_manager import add_patient, get_current_decade, get_next_patient_number, get_today_patients
from modules.transaction_manager import add_transaction_group
from datetime import datetime
import time

def reset_wizard():
    """Réinitialise complètement le wizard"""
    st.session_state.wizard_step = 1
    st.session_state.temp_patient = {}
    st.session_state.temp_examens = []
    st.session_state.prescripteur_selected = None
    st.session_state.last_exam_key = 0
    st.session_state.wizard_active = False

def show():
    """
    Point d'entrée pour l'affichage de la page de saisie et d'historique des transactions
    """
    data = load_data()
    
    # Initialisation des variables de session pour le wizard
    if "wizard_active" not in st.session_state:
        st.session_state.wizard_active = False
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 1
    if "temp_patient" not in st.session_state:
        st.session_state.temp_patient = {}
    if "temp_examens" not in st.session_state:
        st.session_state.temp_examens = []
    if "prescripteur_selected" not in st.session_state:
        st.session_state.prescripteur_selected = None
    if "last_exam_key" not in st.session_state:
        st.session_state.last_exam_key = 0
    
    # --- HEADER SECTION ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("💰 Transactions Patient")
        st.caption("Enregistrez les prestations par patient et gérez l'historique financier")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if not st.session_state.wizard_active:
            if st.button("➕ Nouveau Patient", type="primary", use_container_width=True):
                if not data["prescripteurs"] or not data["examens"] or not data["decades"]:
                    st.error("Veuillez configurer les Prescripteurs, Examens et Décades avant de saisir.")
                else:
                    reset_wizard()
                    st.session_state.wizard_active = True
                    st.rerun()
        else:
            if st.button("❌ Annuler la saisie", type="secondary", use_container_width=True):
                reset_wizard()
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # --- FORMULAIRE WIZARD (affiché uniquement si actif) ---
    if st.session_state.wizard_active:
        st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px; border-left: 5px solid #2196F3 !important;">', unsafe_allow_html=True)
        
        # Indicateur d'étape
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.session_state.wizard_step == 1:
                st.markdown("### 📝 **Étape 1/2**")
                st.markdown("*Informations Patient*")
            else:
                st.markdown("### ✅ **Étape 1/2**")
                st.markdown("*Informations Patient*")
        with col2:
            if st.session_state.wizard_step == 2:
                st.markdown("### 📝 **Étape 2/2**")
                st.markdown("*Examens & Transaction*")
            else:
                st.markdown("### ⏳ **Étape 2/2**")
                st.markdown("*Examens & Transaction*")
        
        st.markdown("---")
        
        # ÉTAPE 1: Informations Patient
        if st.session_state.wizard_step == 1:
            st.markdown("### 👤 Informations du Patient")
            
            # Numéro d'ordre (auto-généré)
            next_number = get_next_patient_number()
            
            # Afficher le compteur du jour
            today_patients = get_today_patients()
            st.info(f"📋 **Patients enregistrés aujourd'hui** : {len(today_patients)}")
            st.success(f"🔢 **Numéro d'ordre patient** : `{next_number}`")
            
            col1, col2 = st.columns(2)
            with col1:
                sexe = st.radio("Sexe", ["F", "M"], horizontal=True, 
                              format_func=lambda x: "Féminin" if x == "F" else "Masculin")
            with col2:
                age = st.number_input("Âge (années)", min_value=0, max_value=150, value=30, step=1)
            
            st.markdown("---")
            
            # Aperçu des patients du jour (optionnel)
            if today_patients:
                with st.expander("📊 Voir les patients enregistrés aujourd'hui"):
                    for p in today_patients[-10:]:
                        st.write(f"**#{p['numero_ordre']}** - {p['sexe']} - {p['age']} ans "
                               f"({p['date_enregistrement'][:19]})")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ Annuler", use_container_width=True):
                    reset_wizard()
                    st.rerun()
            with col2:
                if st.button("Suivant ➡️", type="primary", use_container_width=True):
                    if age >= 0:
                        st.session_state.temp_patient = {
                            "sexe": sexe,
                            "age": age,
                            "numero_ordre": next_number
                        }
                        st.session_state.wizard_step = 2
                        st.rerun()
                    else:
                        st.error("Veuillez saisir un âge valide")
        
        # ÉTAPE 2: Examens et Transaction
        elif st.session_state.wizard_step == 2:
            st.markdown("### 🧪 Examens et Transaction")
            
            # Afficher le résumé patient
            st.success(f"**Patient n°** : #{st.session_state.temp_patient['numero_ordre']} | "
                      f"**Sexe** : {'Féminin' if st.session_state.temp_patient['sexe'] == 'F' else 'Masculin'} | "
                      f"**Âge** : {st.session_state.temp_patient['age']} ans")
            
            st.markdown("---")
            
            # Décade automatique
            current_decade = get_current_decade()
            if not current_decade:
                st.error("⚠️ Aucune décade trouvée pour la date du jour. Veuillez générer les décades.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Gérer les décades", use_container_width=True):
                        reset_wizard()
                        st.switch_page("pages/decades_page.py")
                with col2:
                    if st.button("❌ Annuler", use_container_width=True):
                        reset_wizard()
                        st.rerun()
                return
            
            st.info(f"📅 **Décade de facturation** : {current_decade['periode']} - "
                   f"{current_decade['mois']} {current_decade['annee']} "
                   f"({current_decade['date_debut']} au {current_decade['date_fin']})")
            
            # Sélection du prescripteur
            pres_options = {p["nom"]: p["id"] for p in data["prescripteurs"]}
            if not pres_options:
                st.error("Aucun prescripteur disponible.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Gérer les prescripteurs", use_container_width=True):
                        reset_wizard()
                        st.switch_page("pages/prescripteurs_page.py")
                with col2:
                    if st.button("❌ Annuler", use_container_width=True):
                        reset_wizard()
                        st.rerun()
                return
            
            # Sauvegarder le prescripteur sélectionné
            if st.session_state.prescripteur_selected is None:
                st.session_state.prescripteur_selected = list(pres_options.keys())[0]
            
            pres_sel = st.selectbox(
                "👤 Prescripteur", 
                list(pres_options.keys()),
                index=list(pres_options.keys()).index(st.session_state.prescripteur_selected) if st.session_state.prescripteur_selected in pres_options else 0,
                key="prescripteur_select"
            )
            st.session_state.prescripteur_selected = pres_sel
            
            st.markdown("---")
            st.markdown("#### 📋 Ajouter des examens au panier")
            
            # Formulaire d'ajout d'examen
            with st.container(border=True):
                st.markdown("**➕ Ajouter un examen**")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    ex_options = {f"{e['nom']} ({e['prix']:,.0f} FCFA)": e for e in data["examens"]}
                    if not ex_options:
                        st.error("Aucun examen disponible.")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Gérer les examens", use_container_width=True):
                                reset_wizard()
                                st.switch_page("pages/examens_page.py")
                        with col2:
                            if st.button("❌ Annuler", use_container_width=True):
                                reset_wizard()
                                st.rerun()
                        return
                    
                    ex_sel = st.selectbox(
                        "Type d'Examen", 
                        list(ex_options.keys()), 
                        key=f"ex_sel_{st.session_state.last_exam_key}"
                    )
                    selected_exam = ex_options[ex_sel]
                
                with col2:
                    q_payee = st.number_input("Quantité PAYÉE", min_value=0, value=1, step=1, key="q_payee")
                
                with col3:
                    q_gratuite = st.number_input("Quantité GRATUITE", min_value=0, value=0, step=1, key="q_gratuite")
                
                # Bouton Ajouter - reste dans le formulaire
                if st.button("🛒 Ajouter au panier", type="secondary", use_container_width=True):
                    if q_payee == 0 and q_gratuite == 0:
                        st.error("Veuillez saisir au moins une quantité")
                    else:
                        st.session_state.temp_examens.append({
                            "examen_id": selected_exam["id"],
                            "examen_nom": selected_exam["nom"],
                            "prix": selected_exam["prix"],
                            "quantite_payee": int(q_payee),
                            "quantite_gratuite": int(q_gratuite),
                            "montant": int(q_payee * selected_exam["prix"])
                        })
                        st.toast(f"✅ Ajouté : {selected_exam['nom']}", icon="🛒")
                        st.session_state.last_exam_key += 1
                        time.sleep(0.5)
                        st.rerun()
            
            st.markdown("---")
            
            # Affichage du panier
            if st.session_state.temp_examens:
                st.markdown("#### 🛒 Panier des examens")
                
                df_panier = pd.DataFrame(st.session_state.temp_examens)
                df_display = df_panier[["examen_nom", "quantite_payee", "quantite_gratuite", "montant"]]
                df_display.columns = ["Examen", "Payé", "Gratuit", "Montant (FCFA)"]
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                total_montant = sum(e["montant"] for e in st.session_state.temp_examens)
                st.metric("💰 Total à payer", f"{total_montant:,.0f} FCFA")
                
                # Options de suppression
                st.markdown("**🗑️ Gestion du panier**")
                col_del1, col_del2 = st.columns(2)
                
                with col_del1:
                    if len(st.session_state.temp_examens) > 0:
                        item_to_delete = st.selectbox(
                            "Sélectionner un examen à supprimer",
                            options=range(len(st.session_state.temp_examens)),
                            format_func=lambda x: f"{st.session_state.temp_examens[x]['examen_nom']} "
                                                 f"({st.session_state.temp_examens[x]['quantite_payee']} payé, "
                                                 f"{st.session_state.temp_examens[x]['quantite_gratuite']} gratuit)",
                            key="delete_select"
                        )
                        if st.button("🗑️ Supprimer cet examen", use_container_width=True):
                            del st.session_state.temp_examens[item_to_delete]
                            st.toast("Examen retiré du panier", icon="🗑️")
                            st.rerun()
                
                with col_del2:
                    if st.button("⚠️ Vider tout le panier", type="secondary", use_container_width=True):
                        st.session_state.temp_examens = []
                        st.toast("Panier vidé", icon="⚠️")
                        st.rerun()
            else:
                st.info("📭 Aucun examen dans le panier. Utilisez le formulaire ci-dessus pour ajouter des examens.")
            
            st.markdown("---")
            
            # Boutons de navigation
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("⬅️ Retour patient", use_container_width=True):
                    st.session_state.wizard_step = 1
                    st.rerun()
            
            with col2:
                if st.button("🔄 Nouveau patient", use_container_width=True):
                    reset_wizard()
                    st.rerun()
            
            with col3:
                if st.button("❌ Annuler", use_container_width=True):
                    reset_wizard()
                    st.rerun()
            
            with col4:
                if st.button("✅ ENREGISTRER", type="primary", use_container_width=True, 
                            disabled=len(st.session_state.temp_examens) == 0):
                    if not st.session_state.temp_examens:
                        st.error("Veuillez ajouter au moins un examen")
                    else:
                        # Créer le patient
                        new_patient = add_patient(
                            sexe=st.session_state.temp_patient["sexe"],
                            age=st.session_state.temp_patient["age"]
                        )
                        
                        # Préparer les examens
                        examens_list = [
                            {
                                "examen_id": e["examen_id"],
                                "quantite_payee": e["quantite_payee"],
                                "quantite_gratuite": e["quantite_gratuite"]
                            }
                            for e in st.session_state.temp_examens
                        ]
                        
                        # Enregistrer les transactions
                        transaction_ids = add_transaction_group(
                            patient_id=new_patient["id"],
                            prescripteur_id=pres_options[st.session_state.prescripteur_selected],
                            decade_id=current_decade["id"],
                            examens=examens_list
                        )
                        
                        st.success(f"✅ {len(transaction_ids)} examen(s) enregistré(s) pour le patient n°{new_patient['numero_ordre']}")
                        
                        # Proposer de continuer
                        st.markdown("---")
                        st.markdown("#### Que souhaitez-vous faire ensuite ?")
                        
                        col_next1, col_next2 = st.columns(2)
                        with col_next1:
                            if st.button("🔄 Nouveau patient", use_container_width=True, type="primary"):
                                reset_wizard()
                                st.rerun()
                        
                        with col_next2:
                            if st.button("📊 Voir l'historique", use_container_width=True):
                                reset_wizard()
                                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # --- STATISTIQUES RAPIDES ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    total_patients = len(data.get("patients", []))
    total_transactions = len(data["transactions"])
    total_montant = 0
    ex_dict = {e["id"]: e for e in data["examens"]}
    
    for t in data["transactions"]:
        ex = ex_dict.get(t["examen_id"])
        if ex:
            total_montant += t["quantite_payee"] * ex["prix"]
    
    with col1:
        st.metric("👥 Patients", total_patients)
    with col2:
        st.metric("📋 Transactions", total_transactions)
    with col3:
        st.metric("💰 Chiffre d'affaires", f"{total_montant:,.0f} FCFA")
    with col4:
        today = datetime.now().strftime("%Y-%m-%d")
        patients_auj = len([p for p in data.get("patients", []) if p.get("date_jour") == today])
        st.metric("📅 Patients aujourd'hui", patients_auj)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # --- HISTORIQUE DES TRANSACTIONS ---
    st.markdown('<div class="card p-4 border-0 shadow-sm" style="border-radius: 16px;">', unsafe_allow_html=True)
    st.subheader("📋 Historique des transactions")
    
    patients_dict = {p["id"]: p for p in data.get("patients", [])}
    ex_dict = {e["id"]: e for e in data["examens"]}
    pr_dict = {p["id"]: p["nom"] for p in data["prescripteurs"]}
    
    transactions_by_patient = {}
    for t in data["transactions"]:
        patient_id = t.get("patient_id")
        if patient_id:
            if patient_id not in transactions_by_patient:
                transactions_by_patient[patient_id] = []
            transactions_by_patient[patient_id].append(t)
    
    if transactions_by_patient:
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search = st.text_input("🔍 Rechercher", placeholder="Numéro patient, nom prescripteur ou examen...", label_visibility="collapsed")
        with col_filter:
            filter_date = st.selectbox("Filtrer par période", 
                                      ["Tous", "Aujourd'hui", "Cette semaine", "Ce mois"], 
                                      label_visibility="collapsed")
        
        sorted_patients = sorted(patients_dict.items(), 
                                key=lambda x: x[1].get("date_enregistrement", ""), 
                                reverse=True)
        
        for patient_id, patient in sorted_patients:
            if patient_id not in transactions_by_patient:
                continue
            
            transactions = transactions_by_patient[patient_id]
            
            show_patient = True
            if filter_date == "Aujourd'hui":
                today = datetime.now().strftime("%Y-%m-%d")
                if patient.get("date_jour") != today:
                    show_patient = False
            elif filter_date == "Cette semaine":
                today = datetime.now()
                week_start = today - pd.Timedelta(days=today.weekday())
                patient_date = datetime.strptime(patient["date_enregistrement"][:10], "%Y-%m-%d")
                if patient_date < week_start:
                    show_patient = False
            elif filter_date == "Ce mois":
                current_month = datetime.now().strftime("%Y-%m")
                if not patient["date_enregistrement"].startswith(current_month):
                    show_patient = False
            
            if not show_patient:
                continue
            
            total_patient = 0
            for t in transactions:
                ex = ex_dict.get(t["examen_id"])
                if ex:
                    total_patient += t["quantite_payee"] * ex["prix"]
            
            if search:
                search_lower = search.lower()
                patient_match = search_lower in str(patient["numero_ordre"])
                pres_match = any(search_lower in pr_dict.get(t["prescripteur_id"], "").lower() for t in transactions)
                ex_match = any(search_lower in ex_dict.get(t["examen_id"], {}).get("nom", "").lower() for t in transactions)
                show_patient = patient_match or pres_match or ex_match
            
            if show_patient:
                sex_icon = "👩" if patient["sexe"] == "F" else "👨"
                
                with st.expander(f"{sex_icon} Patient #{patient['numero_ordre']} - {patient['sexe']} - {patient['age']} ans - 💰 {total_patient:,.0f} FCFA"):
                    st.markdown("**Examens effectués :**")
                    
                    for t in transactions:
                        ex = ex_dict.get(t["examen_id"])
                        if ex:
                            col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1.5, 1.5])
                            with col1:
                                st.caption(f"#{t['id']}")
                            with col2:
                                st.write(pr_dict.get(t["prescripteur_id"], "Inconnu"))
                            with col3:
                                st.write(ex["nom"])
                            with col4:
                                st.write(f"Payé: {t['quantite_payee']} | Gratuit: {t['quantite_gratuite']}")
                            with col5:
                                montant = t["quantite_payee"] * ex["prix"]
                                st.write(f"{montant:,.0f} FCFA")
                            
                            # Boutons d'action inline
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button("✏️ Modifier", key=f"edit_{t['id']}", use_container_width=True):
                                    # TODO: Implémenter modification inline
                                    st.info("Fonctionnalité à venir")
                            with btn_col2:
                                if st.button("🗑️ Supprimer", key=f"del_{t['id']}", use_container_width=True):
                                    # TODO: Implémenter suppression avec confirmation
                                    st.info("Fonctionnalité à venir")
                    st.divider()
    else:
        st.info("📭 Aucune transaction n'a encore été enregistrée dans le système.")
    
    st.markdown('</div>', unsafe_allow_html=True)