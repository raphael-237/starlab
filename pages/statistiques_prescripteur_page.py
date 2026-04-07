# pages/statistiques_prescripteur_page.py - VERSION DÉFINITIVE CORRIGÉE
import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from modules.data_manager import load_data
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
import os

def show():
    # --- CSS SPÉCIFIQUE STATS ---
    st.markdown("""
    <style>
        .card-stat {
            background: white;
            padding: 20px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        }
        .stat-label { font-size: 0.75rem; color: #64748b; font-weight: 700; text-transform: uppercase; }
        .stat-val { font-size: 1.5rem; font-weight: 800; color: #0f172a; display: block; margin-top: 5px; }
        .export-card {
            background: #f8fafc;
            padding: 20px;
            border-radius: 16px;
            border: 1px dashed #cbd5e1;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("👨‍⚕️ Stats Prescripteurs")
        st.caption("Performance et activité détaillée par prescripteur")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualiser", use_container_width=True):
            st.rerun()

    data = load_data()
    if not data["transactions"]:
        st.info("ℹ️ Aucune transaction enregistrée.")
        return

    # Chargement des données
    examens = {e["id"]: e for e in data["examens"]}
    prescripteurs = {p["id"]: p["nom"] for p in data["prescripteurs"]}
    decades = {d["id"]: d for d in data["decades"]}
    categories = {c["id"]: c["nom"] for c in data["categories"]}

    records = []
    for t in data["transactions"]:
        ex = examens.get(t["examen_id"])
        if not ex: continue
        dec = decades.get(t["decade_id"], {})
        pres_nom = prescripteurs.get(t["prescripteur_id"], "Inconnu")
        cat_nom = categories.get(ex.get("categorie_id"), "Autres")
        montant = t["quantite_payee"] * ex.get("prix", 0)

        records.append({
            "prescripteur": pres_nom,
            "examen": ex.get("nom", ""),
            "categorie": cat_nom,
            "decade": dec.get("periode", ""),
            "mois": dec.get("mois", ""),
            "annee": dec.get("annee", ""),
            "qte_payee": t["quantite_payee"],
            "qte_gratuite": t["quantite_gratuite"],
            "montant": montant
        })

    df_raw = pd.DataFrame(records)
    if df_raw.empty:
        st.info("Aucune transaction trouvée.")
        return

    # --- FILTRES MODERNES ---
    with st.expander("🔍 Options de filtrage", expanded=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            prescripteurs_list = sorted(df_raw["prescripteur"].unique())
            prescripteur_sel = st.selectbox("👤 Prescripteur", ["Tous les prescripteurs"] + prescripteurs_list)
        with f2:
            annee_list = sorted(df_raw["annee"].unique(), reverse=True)
            annee_sel = st.selectbox("📆 Année", ["Toutes"] + annee_list)
        with f3:
            mois_list = sorted(df_raw["mois"].unique())
            mois_sel = st.selectbox("📅 Mois", ["Tous"] + mois_list)

    df_filtered = df_raw.copy()
    if prescripteur_sel != "Tous les prescripteurs":
        df_filtered = df_filtered[df_filtered["prescripteur"] == prescripteur_sel]
    if annee_sel != "Toutes":
        df_filtered = df_filtered[df_filtered["annee"] == int(annee_sel)]
    if mois_sel != "Tous":
        df_filtered = df_filtered[df_filtered["mois"] == mois_sel]

    if df_filtered.empty:
        st.warning("Aucune donnée pour ces filtres.")
        return

    # --- KPI CARDS ---
    total_montant = df_filtered["montant"].sum()
    total_qte_payee = df_filtered["qte_payee"].sum()
    total_qte_gratuite = df_filtered["qte_gratuite"].sum()
    nb_prescripteurs = df_filtered["prescripteur"].nunique()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="card-stat"><span class="stat-label">Actifs</span><span class="stat-val">{nb_prescripteurs}</span></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="card-stat"><span class="stat-label">Payés</span><span class="stat-val">{int(total_qte_payee)}</span></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="card-stat"><span class="stat-label">Gratuits</span><span class="stat-val">{int(total_qte_gratuite)}</span></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="card-stat"><span class="stat-label">Total FCFA</span><span class="stat-val" style="color:#2563eb;">{total_montant:,.0f}</span></div>', unsafe_allow_html=True)

    # --- AFFICHAGE ET EXPORTS ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_tab, col_exp = st.columns([2, 1])
    
    with col_tab:
        st.subheader("📋 Récapitulatif par période")
        pivot_display = df_filtered.groupby(["prescripteur", "decade"])["montant"].sum().unstack(fill_value=0)
        st.dataframe(pivot_display, use_container_width=True)

    with col_exp:
        st.subheader("📎 Exports")
        st.markdown('<div class="export-card">', unsafe_allow_html=True)
        st.write("Rapports par prescripteur (Modèle institutionnel).")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📥 Télécharger EXCEL", type="primary", key="btn_xl_pres", use_container_width=True):
            export_prescripteur_excel(df_filtered, prescripteur_sel, mois_sel, annee_sel)
            st.toast("✅ Excel généré avec succès", icon="📊")
            
        st.markdown("<div style='margin:10px 0;'></div>", unsafe_allow_html=True)
        
        if st.button("📄 Télécharger WORD", type="secondary", key="btn_wd_pres", use_container_width=True):
            export_prescripteur_word(df_filtered, prescripteur_sel, mois_sel, annee_sel)
            st.toast("✅ Word généré avec succès", icon="📝")
        st.markdown('</div>', unsafe_allow_html=True)


# ====================== EXPORT EXCEL - VERSION ROBUSTE ======================
def export_prescripteur_excel(df, prescripteur_sel, mois_sel, annee_sel):
    """Export Excel - Version institutionnelle paysagée avec en-têtes officiels et tableau récapitulatif"""
    if df.empty:
        st.warning("Aucune donnée à exporter.")
        return

    # 🔧 STANDARDISATION DES COLONNES
    df_export = pd.DataFrame()
    mapping = {
        'prescripteur': ['prescripteur', 'PRESCRIPTEUR', 'Prescripteur', 'Nom'],
        'decade': ['decade', 'DECADE', 'Décade', 'periode'],
        'qte_payee': ['qte_payee', 'QTE_PAYEE', 'quantite_payee', 'Payé'],
        'qte_gratuite': ['qte_gratuite', 'QTE_GRATUITE', 'quantite_gratuite', 'Gratuit'],
        'montant': ['montant', 'MONTANT', 'Montant', 'Montant (FCFA)']
    }
    
    for target, options in mapping.items():
        found = False
        for opt in options:
            if opt in df.columns:
                df_export[target] = df[opt]
                found = True
                break
        if not found:
            if target == 'prescripteur': df_export[target] = df.index
            elif target == 'decade': df_export[target] = "Non spécifié"
            else: df_export[target] = 0

    wb = Workbook()
    ws = wb.active
    ws.title = "Statistiques"
    
    # Configuration Paysage
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToPage = True

    # Styles
    font_header = Font(name='Arial', size=9, bold=True)
    font_title = Font(name='Arial', size=14, bold=True)
    font_table_header = Font(name='Arial', size=10, bold=True)
    align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    align_left = Alignment(horizontal='left', vertical='center', wrap_text=True)
    align_right = Alignment(horizontal='right', vertical='center', wrap_text=True)
    border_thin = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    # 1) EN-TÊTE
    # A GAUCHE (FRANÇAIS)
    entete_fr = [
        "REPUBLIQUE DU CAMEROUN",
        "Paix –Travail –Patrie",
        "------------",
        "MINISTERE DE LA SANTE PUBLIQUE",
        "------------",
        "SECRETARIAT GENERAL",
        "------------",
        "DELEGATION REGIONALE DE LA SANTE",
        "PUBLIQUE DU CENTRE",
        "------------",
        "DISTRICT DE SANTE D’ODZA",
        "------------",
        "CENTRE MEDICAL D’ARRONDISSEMENT DE NKOMO",
        "TEL. : 671742644"
    ]
    for i, line in enumerate(entete_fr, 1):
        ws.cell(row=i, column=1, value=line).font = font_header
        ws.cell(row=i, column=1).alignment = align_center
    ws.merge_cells(start_row=1, start_column=1, end_row=14, end_column=3)

    # AU MILIEU (LOGO)
    logo_path = "logo.png"
    if os.path.exists(logo_path):
        try:
            img = XLImage(logo_path)
            img.width = 100
            img.height = 100
            ws.add_image(img, 'F3')
        except: pass

    # A DROITE (ANGLAIS)
    entete_en = [
        "REPUBLIC OF CAMEROON",
        "Peace-Work-Fatherland",
        "------------",
        "MINISTRY OF PUBLIC HEALTH",
        "------------",
        "SECRETARIAT GENERAL",
        "------------",
        "CENTER REGIONAL DELAGATION OF",
        "PUBLIC HEALTH",
        "-----------",
        "ODZA HEALTH DISTRICT",
        "-----------",
        "NKOMO SUB-DIVISIONAL MEDICAL CENTER"
    ]
    for i, line in enumerate(entete_en, 1):
        ws.cell(row=i, column=9, value=line).font = font_header
        ws.cell(row=i, column=9).alignment = align_center
    ws.merge_cells(start_row=1, start_column=9, end_row=14, end_column=11)

    # 2) TITRE
    title_row = 16
    ws.cell(row=title_row, column=1, value="COMPTE RENDU FINANCIER DES PRESCRIPTEURS AU SERVICE DU LABORATOIRE DU CMA DE NKOMO").font = font_title
    ws.cell(row=title_row, column=1).alignment = align_center
    ws.merge_cells(start_row=title_row, start_column=1, end_row=title_row, end_column=11)

    # 3) MOIS ET ANNÉE
    date_row = 17
    date_text = f"Mois : {mois_sel if mois_sel != 'Tous' else 'Tous les mois'} | Année : {annee_sel if annee_sel != 'Toutes' else 'Toutes les années'}"
    ws.cell(row=date_row, column=1, value=date_text).font = font_header
    ws.cell(row=date_row, column=1).alignment = align_center
    ws.merge_cells(start_row=date_row, start_column=1, end_row=date_row, end_column=11)

    # 4) TITRE DU PREMIER TABLEAU
    table_title_row = 19
    ws.cell(row=table_title_row, column=1, value="NOMBRE D'EXAMEN EFFECTUER").font = font_table_header
    ws.cell(row=table_title_row, column=1).alignment = align_left

    # 5) TABLEAU RÉCAPITULATIF (5 COLONNES x 4 LIGNES)
    # Calculs des données par décade
    dec_order = ["1ère décade", "2ème décade", "3ème décade"]
    stats_dec = {d: {"paye": 0, "gratuit": 0, "total": 0} for d in dec_order}
    
    for d in dec_order:
        mask = df_export["decade"] == d
        paye = int(df_export[mask]["qte_payee"].sum())
        grat = int(df_export[mask]["qte_gratuite"].sum())
        stats_dec[d]["paye"] = paye
        stats_dec[d]["gratuit"] = grat
        stats_dec[d]["total"] = paye + grat

    # Calcul Totaux Mensuels
    total_m_paye = sum(v["paye"] for v in stats_dec.values())
    total_m_grat = sum(v["gratuit"] for v in stats_dec.values())
    total_m_all = total_m_paye + total_m_grat

    # Construction du tableau (Start at row 20)
    start_r = 20
    # En-têtes de colonnes
    col_headers = ["", "1ere Decade (1-10)", "2eme Decade (11-20)", "3eme Decade (21-30)", "TOTAL Mensuel"]
    for c, text in enumerate(col_headers, 1):
        cell = ws.cell(row=start_r, column=c, value=text)
        cell.font = font_table_header
        cell.alignment = align_center
        cell.border = border_thin

    # Lignes de données
    row_labels = ["Payé", "Gratuit", "TOTAL"]
    for r_idx, label in enumerate(row_labels, 1):
        # Première colonne (Labels)
        ws.cell(row=start_r + r_idx, column=1, value=label).font = font_table_header
        ws.cell(row=start_r + r_idx, column=1).border = border_thin
        
        # Données pour chaque décade
        for c_idx, dec in enumerate(dec_order, 2):
            val = 0
            if label == "Payé": val = stats_dec[dec]["paye"]
            elif label == "Gratuit": val = stats_dec[dec]["gratuit"]
            elif label == "TOTAL": val = stats_dec[dec]["total"]
            
            cell = ws.cell(row=start_r + r_idx, column=c_idx, value=val)
            cell.alignment = align_center
            cell.border = border_thin
            
        # Dernière colonne (Total Mensuel)
        m_val = 0
        if label == "Payé": m_val = total_m_paye
        elif label == "Gratuit": m_val = total_m_grat
        elif label == "TOTAL": m_val = total_m_all
        
        cell = ws.cell(row=start_r + r_idx, column=5, value=m_val)
        cell.font = font_table_header
        cell.alignment = align_center
        cell.border = border_thin

    # 6) TABLEAU DÉTAILLÉ PAR PRESCRIPTEUR (En dessous)
    # (On garde la logique de votre ancien tableau mais on l'adapte au nouveau style)
    pres_table_start = start_r + 6
    ws.cell(row=pres_table_start, column=1, value="DÉTAILS PAR PRESCRIPTEUR").font = font_table_header
    
    # Pivot des données
    summary = df_export.groupby(["prescripteur", "decade"]).agg({
        "qte_payee": "sum",
        "qte_gratuite": "sum",
        "montant": "sum"
    }).reset_index()

    pivot_paye = summary.pivot_table(index="prescripteur", columns="decade", values="qte_payee", fill_value=0)
    pivot_gratuit = summary.pivot_table(index="prescripteur", columns="decade", values="qte_gratuite", fill_value=0)
    pivot_montant = summary.pivot_table(index="prescripteur", columns="decade", values="montant", fill_value=0)

    # En-têtes
    h_row = pres_table_start + 1
    headers = ["PRESCRIPTEUR", "1ère décade", "", "", "2ème décade", "", "", "3ème décade", "", "", "TOTAL", "", ""]
    sub_h = ["", "Payé", "Gratuit", "Montant", "Payé", "Gratuit", "Montant", "Payé", "Gratuit", "Montant", "Payé", "Gratuit", "Montant"]
    
    fill_blue = PatternFill(start_color="F0F4F8", end_color="F0F4F8", fill_type="solid")
    
    # 🔧 FIX: Écrire les valeurs AVANT de fusionner pour éviter l'erreur MergedCell
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=h_row, column=c, value=h)
        cell.font = font_table_header
        cell.alignment = align_center
        cell.border = border_thin
        cell.fill = fill_blue

    # Maintenant on fusionne les cellules qui doivent l'être
    for c, h in enumerate(headers, 1):
        if h and "décade" in str(h):
            ws.merge_cells(start_row=h_row, start_column=c, end_row=h_row, end_column=c+2)
        elif h == "TOTAL":
            ws.merge_cells(start_row=h_row, start_column=c, end_row=h_row, end_column=c+2)

    for c, s in enumerate(sub_h, 1):
        cell = ws.cell(row=h_row + 1, column=c, value=s)
        cell.font = font_table_header
        cell.alignment = align_center
        cell.border = border_thin
        cell.fill = fill_blue

    # Données
    curr_r = h_row + 2
    for pres in pivot_paye.index:
        ws.cell(row=curr_r, column=1, value=pres).border = border_thin
        c_idx = 2
        t_p, t_g, t_m = 0, 0, 0
        for dec in dec_order:
            p = int(pivot_paye.loc[pres, dec]) if dec in pivot_paye.columns else 0
            g = int(pivot_gratuit.loc[pres, dec]) if dec in pivot_gratuit.columns else 0
            m = int(pivot_montant.loc[pres, dec]) if dec in pivot_montant.columns else 0
            ws.cell(row=curr_r, column=c_idx, value=p if p > 0 else "").border = border_thin
            ws.cell(row=curr_r, column=c_idx+1, value=g if g > 0 else "").border = border_thin
            ws.cell(row=curr_r, column=c_idx+2, value=m if m > 0 else "").border = border_thin
            t_p += p; t_g += g; t_m += m
            c_idx += 3
        ws.cell(row=curr_r, column=11, value=t_p).border = border_thin
        ws.cell(row=curr_r, column=12, value=t_g).border = border_thin
        ws.cell(row=curr_r, column=13, value=t_m).border = border_thin
        curr_r += 1

    # Ajustement colonnes
    for col in ws.columns:
        max_l = 0
        for cell in col:
            try:
                if cell.value: max_l = max(max_l, len(str(cell.value)))
            except: pass
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_l + 2, 30)

    # Sauvegarde
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    st.success("✅ Rapport institutionnel Excel généré !")
    st.download_button(label="⬇️ Télécharger le Rapport Excel", data=output, 
                       file_name=f"RAPPORT_PRESCRIPTEURS_{mois_sel}_{annee_sel}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ====================== EXPORT WORD - VERSION ROBUSTE ======================
def export_prescripteur_word(df_source, mois_sel, annee_sel):
    """Génère le rapport Word avec Titre et Mois replacés correctement"""
    if df_source.empty:
        st.warning("Aucune donnée à exporter.")
        return

    # --- 1. PRÉPARATION ---
    df_work = df_source.copy()
    mask_kit = df_work['nom_examen'].str.contains('Kit|Prélèvement|PRELEVEMENT', case=False, na=False)
    df_kits = df_work[mask_kit]
    df_presc = df_work[~mask_kit].copy()

    df_presc['categorie'] = df_presc['prescripteur'].apply(
        lambda x: "INFIRMIERS" if str(x).startswith("Mme") else "MEDECINS"
    )
    
    dec_order = ["1ère décade", "2ème décade", "3ème décade"]
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    section.left_margin = section.right_margin = Inches(0.4)
    section.top_margin = Inches(0.4)

    # --- 2. EN-TÊTE ADMINISTRATIF ---
    header_table = doc.add_table(rows=1, cols=3)
    header_table.width = Inches(10)
    
    p_fr = header_table.cell(0, 0).paragraphs[0]
    p_fr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    txt_fr = ("REPUBLIQUE DU CAMEROUN\nPaix – Travail – Patrie\n------------\n"
              "MINISTERE DE LA SANTE PUBLIQUE\n------------\nSECRETARIAT GENERAL\n------------\n"
              "DELEGATION REGIONALE DE LA SANTE\nPUBLIQUE DU CENTRE\n------------\n"
              "DISTRICT DE SANTE D’ODZA\n------------\n"
              "CENTRE MEDICAL D’ARRONDISSEMENT DE NKOMO\nTEL. : 671742644")
    run_fr = p_fr.add_run(txt_fr)
    run_fr.bold = True; run_fr.font.size = Pt(7.5)

    if os.path.exists("logo.png"):
        logo_para = header_table.cell(0, 1).paragraphs[0]
        logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        logo_para.add_run().add_picture("logo.png", width=Inches(1.2))

    p_en = header_table.cell(0, 2).paragraphs[0]
    p_en.alignment = WD_ALIGN_PARAGRAPH.CENTER
    txt_en = ("REPUBLIC OF CAMEROON\nPeace-Work-Fatherland\n------------\n"
              "MINISTRY OF PUBLIC HEALTH\n------------\nSECRETARIAT GENERAL\n------------\n"
              "CENTER REGIONAL DELEGATION OF\nPUBLIC HEALTH\n------------\n"
              "ODZA HEALTH DISTRICT\n------------\n"
              "NKOMO SUB-DIVISIONAL MEDICAL CENTER")
    run_en = p_en.add_run(txt_en)
    run_en.bold = True; run_en.font.size = Pt(7.5)

    # --- 3. TITRE ET MOIS (AJOUTÉS ICI AVANT LE TABLEAU) ---
    doc.add_paragraph() # Espace après l'en-tête
    
    # Titre Principal
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title_para.add_run("COMPTE RENDU FINANCIER DES PRESCRIPTEURS AU SERVICE DU LABORATOIRE DU CMA DE NKOMO")
    run_title.bold = True
    run_title.underline = True
    run_title.font.size = Pt(13)

    # Mois et Année
    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_date = date_para.add_run(f"(MOIS DE {mois_sel.upper()} {annee_sel})")
    run_date.bold = True
    run_date.font.size = Pt(11)

    # --- 4. CALCULS COMBINÉS ---
    stats_decades = {dec: {"paye": 0, "gratuit": 0} for dec in dec_order}
    for dec in dec_order:
        d_df = df_presc[df_presc['decade'] == dec]
        stats_decades[dec]["paye"] = int(d_df['qte_payee'].sum())
        stats_decades[dec]["gratuit"] = int(d_df['qte_gratuite'].sum())

    # --- 5. TABLEAU : NOMBRE D'EXAMENS EFFECTUES ---
    doc.add_paragraph()
    title_ex = doc.add_paragraph("NOMBRE D'EXAMENS EFFECTUES")
    title_ex.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_ex.runs[0].bold = True; title_ex.runs[0].underline = True

    exam_table = doc.add_table(rows=2, cols=12)
    exam_table.style = 'Table Grid'
    
    # En-têtes décades
    eh1 = exam_table.rows[0].cells
    for i, d_lbl in enumerate(dec_order + ["TOTAL MENSUEL"]):
        eh1[i*3].merge(eh1[i*3+2]).text = d_lbl
        eh1[i*3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    sub_labels = ["Payé", "Gratuit", "TOTAL"] * 4
    for i, lbl in enumerate(sub_labels):
        cell_p = exam_table.rows[1].cells[i].paragraphs[0]
        cell_p.add_run(lbl).bold = True
        cell_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Remplissage des données
    row_val = exam_table.add_row().cells
    g_p, g_g = 0, 0
    for i, dec in enumerate(dec_order):
        p = stats_decades[dec]["paye"]
        g = stats_decades[dec]["gratuit"]
        row_val[i*3].text, row_val[i*3+1].text, row_val[i*3+2].text = str(p), str(g), str(p+g)
        g_p += p; g_g += g
    row_val[9].text, row_val[10].text, row_val[11].text = str(g_p), str(g_g), str(g_p+g_g)
    for c in row_val: 
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if c.text: c.paragraphs[0].runs[0].bold = True

    # --- 6. SECTION FINANCIÈRE DÉSAGRÉGÉE ---
    doc.add_paragraph()
    trans = doc.add_paragraph("RAPPORT FINANCIER DESAGREGE PAR CATEGORIE ET NOM DES PRESCRIPTEURS")
    trans.alignment = WD_ALIGN_PARAGRAPH.CENTER
    trans.runs[0].bold = True; trans.runs[0].underline = True
    doc.add_paragraph("(Nombre d'examens effectues et montants)").alignment = WD_ALIGN_PARAGRAPH.CENTER

    tot_med = {i: 0 for i in range(1, 13)}
    tot_inf = {i: 0 for i in range(1, 13)}
    tot_kit = {i: 0 for i in range(1, 13)}

    categories_to_show = [
        ("MEDECINS", "CATEGORIE DE PRESCRIPTEURS - MEDECINS"),
        ("INFIRMIERS", "CATEGORIE DE PRESCRIPTEURS - INFIRMIERS (SELON LES SERVICES)")
    ]

    for idx, (cat_id, cat_lbl) in enumerate(categories_to_show):
        if idx > 0: doc.add_paragraph() # Espace entre Med et Inf
        
        p_cat = doc.add_paragraph()
        run_cat = p_cat.add_run(cat_lbl)
        run_cat.bold = True; run_cat.underline = True
        
        table = doc.add_table(rows=2, cols=13)
        table.style = 'Table Grid'
        
        h1 = table.rows[0].cells
        h1[0].text = "NOM ET PRENOMS"
        for i, d_lbl in enumerate(dec_order + ["TOTAL MENSUEL"]):
            h1[1+(i*3)].merge(h1[3+(i*3)]).text = d_lbl
        
        h2 = table.rows[1].cells
        labels = ["Payé", "Gratuit", "Montant"] * 4
        for i, txt in enumerate(labels):
            h2[i+1].paragraphs[0].add_run(txt).bold = True

        df_cat = df_presc[df_presc['categorie'] == cat_id]
        if not df_cat.empty:
            summ = df_cat.groupby(["prescripteur", "decade"]).agg({"qte_payee":"sum", "qte_gratuite":"sum", "montant":"sum"}).reset_index()
            for presc in summ["prescripteur"].unique():
                r = table.add_row().cells
                r[0].text = str(presc)
                lp, lg, lm = 0, 0, 0
                for i, dec in enumerate(dec_order):
                    d = summ[(summ["prescripteur"]==presc) & (summ["decade"]==dec)]
                    p, g, m = int(d["qte_payee"].sum()), int(d["qte_gratuite"].sum()), int(d["montant"].sum())
                    r[1+(i*3)].text = str(p) if p>0 else ""
                    r[2+(i*3)].text = str(g) if g>0 else ""
                    r[3+(i*3)].text = f"{m:,}" if m>0 else ""
                    target = tot_med if cat_id == "MEDECINS" else tot_inf
                    target[1+(i*3)]+=p; target[2+(i*3)]+=g; target[3+(i*3)]+=m
                    lp+=p; lg+=g; lm+=m
                r[10].text, r[11].text, r[12].text = str(lp), str(lg), f"{lm:,}"
                target[10]+=lp; target[11]+=lg; target[12]+=lm

        # Ligne Sous-Total
        sr = table.add_row().cells
        sr[0].paragraphs[0].add_run(f"Sous-Total - {cat_id}").bold = True
        curr = tot_med if cat_id == "MEDECINS" else tot_inf
        for i in range(1, 13):
            val_txt = f"{curr[i]:,}" if i%3==0 else str(curr[i])
            sr[i].paragraphs[0].add_run(val_txt).bold = True

        if cat_id == "INFIRMIERS":
            for i, dec in enumerate(dec_order):
                dk = df_kits[df_kits['decade'] == dec]
                pk, gk, mk = int(dk['qte_payee'].sum()), int(dk['qte_gratuite'].sum()), int(dk['montant'].sum())
                tot_kit[1+(i*3)], tot_kit[2+(i*3)], tot_kit[3+(i*3)] = pk, gk, mk
                tot_kit[10]+=pk; tot_kit[11]+=gk; tot_kit[12]+=mk

            for lbl, vals in [("TOTAL GENERAL", {i: tot_med[i]+tot_inf[i] for i in range(1,13)}),
                              ("KIT PRELEVEMENT", tot_kit),
                              ("TOTAL GLOBAL", {i: tot_med[i]+tot_inf[i]+tot_kit[i] for i in range(1,13)})]:
                r = table.add_row().cells
                r[0].paragraphs[0].add_run(lbl).bold = True
                for i in range(1, 13):
                    v_txt = f"{vals[i]:,}" if i%3==0 else str(vals[i])
                    r[i].paragraphs[0].add_run(v_txt).bold = True

    # --- 7. SORTIE ---
    out = BytesIO(); doc.save(out); out.seek(0)
    return out

def show():
    # ... (Le reste de la fonction show() reste identique à votre code actuel)
    st.title("👨‍⚕️ Statistiques Financières")
    data = load_data()
    now = datetime.now()
    mois_fr = {1:"Janvier", 2:"Février", 3:"Mars", 4:"Avril", 5:"Mai", 6:"Juin", 
               7:"Juillet", 8:"Août", 9:"Septembre", 10:"Octobre", 11:"Novembre", 12:"Décembre"}
    nom_m, annee = mois_fr[now.month], now.year

    decades_m = [d for d in data.get("decades", []) if d.get("mois") == nom_m and d.get("annee") == annee]
    if not decades_m:
        st.error(f"Aucune décade pour {nom_m} {annee}.")
        return

    dec_ids = [d["id"] for d in decades_m]
    ex_dict = {e["id"]: e for e in data.get("examens", [])}
    pr_dict = {p["id"]: p.get("nom", "Inconnu") for p in data.get("prescripteurs", [])}
    dec_names = {d["id"]: d.get("periode", "Inconnue") for d in data.get("decades", [])}

    trans_list = []
    for t in data.get("transactions", []):
        if t.get("decade_id") in dec_ids:
            e = ex_dict.get(t["examen_id"], {})
            trans_list.append({
                "prescripteur": pr_dict.get(t["prescripteur_id"], "Inconnu"),
                "nom_examen": e.get("nom", "Inconnu"),
                "decade": dec_names.get(t["decade_id"], ""),
                "qte_payee": t.get("quantite_payee", 0),
                "qte_gratuite": t.get("quantite_gratuite", 0),
                "montant": t.get("quantite_payee", 0) * e.get("prix", 0)
            })

    df = pd.DataFrame(trans_list)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        if st.button("📄 Générer Rapport Word Officiel"):
            word = export_prescripteur_word(df, nom_m, annee)
            st.download_button("⬇️ Télécharger Word", word, f"Rapport_{nom_m}.docx")