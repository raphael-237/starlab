# pages/statistiques_page.py
import streamlit as st
import pandas as pd
from io import BytesIO
from modules.data_manager import load_data
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
import os

def show():
    """
    Affiche la page des statistiques financières globales.
    Permet de filtrer par période et d'exporter les rapports officiels.
    """
    # --- CSS SPÉCIFIQUE STATS ---
    st.markdown("""
    <style>
        .card-stat {
            background: white;
            padding: 24px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }
        .stat-label { font-size: 0.8rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-val { font-size: 1.8rem; font-weight: 800; color: #0f172a; display: block; margin-top: 5px; }
        
        .export-section {
            background: #f8fafc;
            padding: 24px;
            border-radius: 16px;
            border: 1px dashed #cbd5e1;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- HEADER SECTION ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("📊 Statistiques Financières")
        st.caption("Analysez les performances globales et générez les rapports institutionnels.")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualiser les données", use_container_width=True):
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    data = load_data()
    if not data["transactions"]:
        st.info("ℹ️ Aucune transaction n'a encore été enregistrée pour générer des statistiques.")
        return

    # Préparation des données avec mapping
    ex_dict = {e["id"]: e for e in data["examens"]}
    cat_dict = {c["id"]: c["nom"] for c in data["categories"]}
    dec_dict = {d["id"]: d for d in data["decades"]}

    records = []
    for t in data["transactions"]:
        ex = ex_dict.get(t["examen_id"])
        if not ex: continue
        
        nom_examen = ex["nom"]
        nom_categorie = cat_dict.get(ex.get("categorie_id"), "Autres")
        
        # Filtre d'exclusion des "kits" (Instruction spécifique)
        if "kit" in nom_categorie.lower() or "kit" in nom_examen.lower():
            continue
            
        dec = dec_dict.get(t["decade_id"], {})
        records.append({
            "Catégorie": nom_categorie,
            "NOM DE L'EXAMEN": nom_examen,
            "Décade": dec.get("periode", ""),
            "Mois": dec.get("mois", ""),
            "Année": dec.get("annee", ""),
            "Quantité Payée": t["quantite_payee"],
            "Quantité Gratuite": t["quantite_gratuite"],
            "Montant (FCFA)": t["quantite_payee"] * ex.get("prix", 0)
        })

    df = pd.DataFrame(records)
    if df.empty:
        st.warning("⚠️ Aucune donnée disponible après filtrage (Kits exclus).")
        return

    # --- FILTRES DE PÉRIODE ---
    st.markdown('<div class="card p-4 border-0 shadow-sm mb-4" style="border-radius: 16px;">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1, 1, 1])
    with f1:
        annee_sel = st.selectbox("� Année fiscale", sorted(df["Année"].unique(), reverse=True))
    with f2:
        mois_sel = st.selectbox("📅 Mois d'analyse", sorted(df[df["Année"] == annee_sel]["Mois"].unique()))
    with f3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.success(f"Période sélectionnée : **{mois_sel} {annee_sel}**")
    st.markdown('</div>', unsafe_allow_html=True)

    df_filtered = df[(df["Mois"] == mois_sel) & (df["Année"] == annee_sel)]

    if df_filtered.empty:
        st.info(f"Aucune donnée pour {mois_sel} {annee_sel}.")
        return

    # --- INDICATEURS CLÉS (KPI) ---
    total_m = df_filtered["Montant (FCFA)"].sum()
    total_p = df_filtered["Quantité Payée"].sum()
    total_g = df_filtered["Quantité Gratuite"].sum()

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f"""
            <div class="card-stat">
                <span class="stat-label">Chiffre d'Affaires</span>
                <span class="stat-val" style="color: #0d6efd;">{total_m:,.0f} FCFA</span>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
            <div class="card-stat">
                <span class="stat-label">Examens Payés</span>
                <span class="stat-val">{int(total_p)}</span>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class="card-stat">
                <span class="stat-label">Examens Gratuits</span>
                <span class="stat-val" style="color: #64748b;">{int(total_g)}</span>
            </div>
        """, unsafe_allow_html=True)

    # --- TABLEAU ET EXPORT ---
    st.markdown('<div class="card p-4 border-0 shadow-sm" style="border-radius: 16px;">', unsafe_allow_html=True)
    col_table, col_exports = st.columns([2, 1], gap="large")
    
    with col_table:
        st.subheader("📋 Récapitulatif détaillé")
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    with col_exports:
        st.subheader("📎 Rapport Officiel")
        st.markdown("""
            <div class="export-section">
                <p class="text-muted small">Générez le document Word au format institutionnel (paysage, en-têtes officiels).</p>
        """, unsafe_allow_html=True)
        
        if st.button("📄 Générer le Rapport Word", type="primary", use_container_width=True):
            export_to_word(df_filtered, mois_sel, annee_sel)
            st.toast("✅ Rapport généré avec succès !", icon="📝")
            
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ====================== FONCTION EXPORT WORD ======================
def export_to_word(df, mois_sel, annee_sel):
    """
    Génère et propose au téléchargement un document Word formaté selon les standards institutionnels.
    """
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Inches(11.69), Inches(8.27)
    section.left_margin = section.right_margin = section.top_margin = section.bottom_margin = Inches(0.4)

    # 1) En-tête bilingue
    header_table = doc.add_table(rows=1, cols=3); header_table.width = Inches(10.5)
    
    def fill_header(cell, lines):
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for line in lines:
            run = p.add_run(line + "\n"); run.bold = True; run.font.size = Pt(7)

    fill_header(header_table.cell(0, 0), [
        "REPUBLIQUE DU CAMEROUN", "Paix – Travail – Patrie", "------------",
        "MINISTERE DE LA SANTE PUBLIQUE", "------------",
        "SECRETARIAT GENERAL", "------------",
        "DELEGATION REGIONALE DE LA SANTE", "PUBLIQUE DU CENTRE", "------------",
        "DISTRICT DE SANTE D’ODZA", "------------",
        "CENTRE MEDICAL D’ARRONDISSEMENT DE NKOMO", "TEL. : 671742644"
    ])
    
    c_logo = header_table.cell(0, 1); p_logo = c_logo.paragraphs[0]; p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if os.path.exists("logo.png"):
        p_logo.add_run().add_picture("logo.png", width=Inches(1.2))
    p_logo.add_run("\nCSU").bold = True

    fill_header(header_table.cell(0, 2), [
        "REPUBLIC OF CAMEROON", "Peace-Work-Fatherland", "------------",
        "MINISTRY OF PUBLIC HEALTH", "------------",
        "SECRETARIAT GENERAL", "------------",
        "CENTER REGIONAL DELEGATION OF", "PUBLIC HEALTH", "-----------",
        "ODZA HEALTH DISTRICT", "-----------",
        "NKOMO SUB-DIVISIONAL MEDICAL CENTER"
    ])

    # 2) Titre du document
    doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_t = t.add_run("STATISTIQUE FINANCIER DU LABORATOIRE DU CMA DE NKOMO")
    run_t.bold = True; run_t.underline = True; run_t.font.size = Pt(13)
    
    st_title = doc.add_paragraph()
    st_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_st = st_title.add_run(f"(MOIS DE {mois_sel.upper()} {annee_sel})")
    run_st.bold = True

    # 3) Tableau de données (13 colonnes)
    table = doc.add_table(rows=2, cols=13); table.style = 'Table Grid'
    h = table.rows[0].cells
    h[0].text = "NOM DE L'EXAMEN"
    h[1].text = "1ère décade"; h[4].text = "2ème décade"; h[7].text = "3ème décade"; h[10].text = "TOTAL"
    for i in [1, 4, 7, 10]: h[i].merge(h[i+2])

    sh = table.rows[1].cells
    lbls = ["Payé", "Gratuit", "Montant"]
    for i in range(4):
        for j, txt in enumerate(lbls): sh[1 + (i*3) + j].text = txt

    for row in table.rows[:2]:
        for cell in row.cells:
            if cell.text:
                p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.runs[0]; r.bold = True; r.font.size = Pt(8)

    # 4) Remplissage par catégories
    grand_totals = [0] * 12
    categories = sorted(df['Catégorie'].unique())

    for cat in categories:
        row_cat = table.add_row().cells
        row_cat[0].text = cat.upper()
        row_cat[0].merge(row_cat[12])
        p_cat = row_cat[0].paragraphs[0]; p_cat.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_cat = p_cat.runs[0]; run_cat.bold = True; run_cat.font.size = Pt(9)

        df_cat = df[df['Catégorie'] == cat]
        examens = sorted(df_cat["NOM DE L'EXAMEN"].unique())
        cat_sums = [0]*9 

        for exam in examens:
            rc = table.add_row().cells
            rc[0].text = exam
            ex_tp, ex_tg, ex_tm = 0, 0, 0
            dec_cfg = [("1ère décade", 1), ("2ème décade", 4), ("3ème décade", 7)]
            for idx_d, (d_name, col_start) in enumerate(dec_cfg):
                d_df = df_cat[(df_cat["NOM DE L'EXAMEN"] == exam) & (df_cat["Décade"] == d_name)]
                p, g, m = d_df["Quantité Payée"].sum(), d_df["Quantité Gratuite"].sum(), d_df["Montant (FCFA)"].sum()
                rc[col_start].text = str(int(p)) if p > 0 else ""
                rc[col_start+1].text = str(int(g)) if g > 0 else ""
                rc[col_start+2].text = f"{int(m):,}" if m > 0 else ""
                ex_tp += p; ex_tg += g; ex_tm += m
                cat_sums[idx_d*3] += p; cat_sums[idx_d*3+1] += g; cat_sums[idx_d*3+2] += m

            rc[10].text, rc[11].text, rc[12].text = str(int(ex_tp)), str(int(ex_tg)), f"{int(ex_tm):,}"
            for cell in rc: 
                p = cell.paragraphs[0]
                if p.runs: p.runs[0].font.size = Pt(8)
                if cell != rc[0]: p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Sous-totaux par catégorie
        rst = table.add_row().cells
        rst[0].text = f"Sous-Total {cat}"
        c_p, c_g, c_m = (cat_sums[0]+cat_sums[3]+cat_sums[6]), (cat_sums[1]+cat_sums[4]+cat_sums[7]), (cat_sums[2]+cat_sums[5]+cat_sums[8])
        all_v = cat_sums + [c_p, c_g, c_m]
        for i, val in enumerate(all_v):
            rst[1+i].text = f"{int(val):,}" if i%3==2 else str(int(val))
            grand_totals[i] += val
        for cell in rst:
            p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0] if p.runs else p.add_run(cell.text)
            run.bold = True; run.font.size = Pt(8)

    # 5) Total Général
    rtot = table.add_row().cells; rtot[0].text = "TOTAL GÉNÉRAL"
    for i, val in enumerate(grand_totals):
        rtot[1+i].text = f"{int(val):,}" if i%3==2 else str(int(val))
        p = rtot[1+i].paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.runs[0] if p.runs else p.add_run(rtot[1+i].text); run.bold = True; run.font.size = Pt(8)

    # Sauvegarde et téléchargement
    output = BytesIO(); doc.save(output); output.seek(0)
    st.download_button("⬇️ Télécharger le Rapport Word Officiel", output, 
                       file_name=f"RAPPORT_LABO_{mois_sel.upper()}_{annee_sel}.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")