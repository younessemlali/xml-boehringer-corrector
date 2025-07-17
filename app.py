import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="Correcteur XML Boehringer", page_icon="🔧", layout="wide")

# En-tête avec explication
st.title("🔧 Correcteur XML Boehringer")
st.markdown("""
### 📋 Comment ça marche ?

Cette application corrige automatiquement les fichiers XML de contrats Boehringer en :
1. **Détectant** le numéro de commande dans vos fichiers XML
2. **Recherchant** les informations correspondantes dans la base de données
3. **Ajoutant ou corrigeant** les balises manquantes :
   - `PositionStatus` : Le statut du poste (N1, N2, etc.)
   - `PositionLevel` : La classification du poste
   - `PositionCoefficient` : Le nom du HRBP responsable
""")
st.markdown("---")

# Charger les données depuis GitHub
@st.cache_data(ttl=300)
def load_data_from_github():
    try:
        url = "https://raw.githubusercontent.com/younessemlali/xml-boehringer-corrector/main/commandes.csv"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            
            # Debug : afficher les colonnes trouvées
            print(f"Colonnes trouvées: {list(df.columns)}")
            
            # Chercher la colonne numéro de commande (flexible)
            num_col = None
            for col in df.columns:
                if 'num' in col.lower() and 'commande' in col.lower():
                    num_col = col
                    break
            
            # S'assurer que les numéros gardent leurs zéros
            if num_col:
                df[num_col] = df[num_col].astype(str).str.zfill(6)
                
            return df, None
        else:
            return None, f"Erreur HTTP {response.status_code}"
    except Exception as e:
        return None, f"Erreur: {str(e)}"

# Fonction pour parser un XML
def parse_xml_content(xml_content):
    """Parse le contenu XML et retourne la racine"""
    try:
        if isinstance(xml_content, bytes):
            xml_content = xml_content.decode('utf-8')
        root = ET.fromstring(xml_content)
        return root, None
    except Exception as e:
        return None, str(e)

# Fonction pour trouver le numéro de commande
def find_order_number(root):
    """Recherche le numéro de commande dans le XML"""
    search_paths = [
        ("OrderNumber", ".//OrderNumber"),
        ("CommandNumber", ".//CommandNumber"),
        ("NumeroCommande", ".//NumeroCommande"),
        ("ContractNumber", ".//ContractNumber"),
        ("Reference", ".//Reference")
    ]
    
    for tag_name, path in search_paths:
        elem = root.find(path)
        if elem is not None and elem.text:
            return elem.text.strip().zfill(6), tag_name
    
    # Recherche dans les attributs si pas trouvé dans les éléments
    for elem in root.iter():
        for attr in ['orderNumber', 'commandNumber', 'numero', 'ref']:
            if attr in elem.attrib:
                return elem.attrib[attr].strip().zfill(6), f"@{attr}"
    
    return None, None

# Fonction pour corriger un XML
def correct_xml(root, commande_data):
    """Applique les corrections au XML"""
    corrections = []
    
    # Trouver ou créer PositionCharacteristics
    pos_char = root.find(".//PositionCharacteristics")
    if pos_char is None:
        pos_char = ET.SubElement(root, "PositionCharacteristics")
        corrections.append("Création de la section PositionCharacteristics")
    
    # PositionStatus
    pos_status = pos_char.find("PositionStatus")
    if pos_status is None:
        pos_status = ET.SubElement(pos_char, "PositionStatus")
        corrections.append("Ajout de PositionStatus")
    
    code_elem = pos_status.find("Code")
    if code_elem is None:
        code_elem = ET.SubElement(pos_status, "Code")
    code_elem.text = commande_data['Statut'].split()[0]
    
    desc_elem = pos_status.find("Description")
    if desc_elem is None:
        desc_elem = ET.SubElement(pos_status, "Description")
    desc_elem.text = commande_data['Statut']
    
    # PositionLevel
    pos_level = pos_char.find("PositionLevel")
    if pos_level is None:
        pos_level = ET.SubElement(pos_char, "PositionLevel")
        corrections.append("Ajout de PositionLevel")
    pos_level.text = commande_data['Classification']
    
    # PositionCoefficient
    pos_coef = pos_char.find("PositionCoefficient")
    if pos_coef is None:
        pos_coef = ET.SubElement(pos_char, "PositionCoefficient")
        corrections.append("Ajout de PositionCoefficient")
    pos_coef.text = commande_data['HRBP']
    
    return corrections

# Interface principale
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Base de données des commandes")
    
    df, error = load_data_from_github()
    
    if error:
        st.error(error)
        st.info("Utilisation des données de démonstration")
        data = {
            'Numéro de commande': ['000054', '000646'],
            'Code agence': ['LV2-LV2', 'LV2-LV2'],
            'Statut': ['N2 - Niveau 2 (4B +)', 'N1 - Niveau 1 (2A / 4A)'],
            'Classification': ['04B - 225', '03B - 195 Equipe'],
            'HRBP': ['Gabrielle Humbert', 'Houria Gherras']
        }
        df = pd.DataFrame(data)
    
    st.success(f"✅ {len(df)} commandes disponibles")
    
    # Afficher les données
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Informations sur les commandes
    with st.expander("ℹ️ Commandes disponibles"):
        # Vérifier le nom exact de la colonne
        num_col = None
        for col in df.columns:
            if 'num' in col.lower() and 'commande' in col.lower():
                num_col = col
                break
        
        if num_col:
            for num in df[num_col].unique():
                row = df[df[num_col] == num].iloc[0]
                hrbp = row.get('HRBP', 'N/A')
                statut = row.get('Statut', 'N/A')
                st.write(f"**{num}** → {hrbp} ({statut})")
        else:
            st.write("Colonnes disponibles:", list(df.columns))

with col2:
    st.subheader("📄 Correction des fichiers XML")
    
    # Upload multiple
    uploaded_files = st.file_uploader(
        "Choisir un ou plusieurs fichiers XML",
        type=['xml'],
        accept_multiple_files=True,
        help="Vous pouvez sélectionner plusieurs fichiers à la fois"
    )
    
    if uploaded_files:
        st.info(f"📎 {len(uploaded_files)} fichier(s) sélectionné(s)")
        
        # Afficher la liste des fichiers
        with st.expander("📋 Fichiers sélectionnés"):
            for file in uploaded_files:
                st.write(f"• {file.name}")
        
        if st.button("🚀 Analyser et corriger tous les fichiers", type="primary"):
            # Initialiser la barre de progression
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Variables pour les statistiques
            results = []
            corrected_files = []
            total_corrections = 0
            
            # Container pour les résultats
            results_container = st.container()
            
            # Traiter chaque fichier
            for idx, uploaded_file in enumerate(uploaded_files):
                # Mettre à jour la progression
                progress = (idx + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Traitement de {uploaded_file.name}... ({idx + 1}/{len(uploaded_files)})")
                
                # Résultat pour ce fichier
                file_result = {
                    'Fichier': uploaded_file.name,
                    'Statut': '',
                    'Numéro commande': '',
                    'Corrections': 0,
                    'Message': ''
                }
                
                try:
                    # Lire et parser le XML
                    xml_content = uploaded_file.read()
                    root, error = parse_xml_content(xml_content)
                    
                    if error:
                        file_result['Statut'] = '❌ Erreur'
                        file_result['Message'] = f"Erreur parsing: {error}"
                        results.append(file_result)
                        continue
                    
                    # Chercher le numéro de commande
                    num_cmd, found_in = find_order_number(root)
                    
                    if not num_cmd:
                        file_result['Statut'] = '⚠️ Non trouvé'
                        file_result['Message'] = "Numéro de commande introuvable"
                        results.append(file_result)
                        continue
                    
                    file_result['Numéro commande'] = num_cmd
                    
                    # Chercher dans la base de données
                    # Trouver la colonne numéro de commande
                    num_col = None
                    for col in df.columns:
                        if 'num' in col.lower() and 'commande' in col.lower():
                            num_col = col
                            break
                    
                    if num_col and num_cmd not in df[num_col].values:
                        file_result['Statut'] = '⚠️ Inconnu'
                        file_result['Message'] = f"Commande {num_cmd} absente de la base"
                        results.append(file_result)
                        continue
                    
                    # Appliquer les corrections
                    commande_data = df[df[num_col] == num_cmd].iloc[0].to_dict()
                    corrections = correct_xml(root, commande_data)
                    
                    file_result['Statut'] = '✅ Corrigé'
                    file_result['Corrections'] = len(corrections)
                    file_result['Message'] = f"Trouvé dans <{found_in}>"
                    total_corrections += len(corrections)
                    
                    # Sauvegarder le fichier corrigé
                    xml_str = ET.tostring(root, encoding='unicode', method='xml')
                    corrected_files.append({
                        'name': uploaded_file.name,
                        'content': xml_str,
                        'original_name': uploaded_file.name
                    })
                    
                except Exception as e:
                    file_result['Statut'] = '❌ Erreur'
                    file_result['Message'] = str(e)
                
                results.append(file_result)
            
            # Fin du traitement
            progress_bar.empty()
            status_text.empty()
            
            # Afficher les résultats
            st.markdown("### 📊 Résultats du traitement")
            
            # Statistiques globales
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            total_files = len(results)
            success_files = len([r for r in results if r['Statut'] == '✅ Corrigé'])
            error_files = len([r for r in results if '❌' in r['Statut']])
            warning_files = len([r for r in results if '⚠️' in r['Statut']])
            
            with col_stat1:
                st.metric("Total traités", total_files)
            with col_stat2:
                st.metric("Succès", success_files, delta=f"{success_files/total_files*100:.0f}%")
            with col_stat3:
                st.metric("Avertissements", warning_files)
            with col_stat4:
                st.metric("Corrections", total_corrections)
            
            # Tableau détaillé des résultats
            results_df = pd.DataFrame(results)
            st.dataframe(
                results_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Statut": st.column_config.TextColumn(width="small"),
                    "Corrections": st.column_config.NumberColumn(width="small")
                }
            )
            
            # Section de téléchargement
            if corrected_files:
                st.markdown("### 💾 Télécharger les fichiers corrigés")
                st.success(f"✅ {len(corrected_files)} fichier(s) prêt(s) au téléchargement")
                
                # Créer des colonnes pour organiser les boutons
                download_cols = st.columns(3)
                
                for idx, file_data in enumerate(corrected_files):
                    col_idx = idx % 3
                    with download_cols[col_idx]:
                        st.download_button(
                            label=f"📥 {file_data['original_name']}",
                            data=file_data['content'],
                            file_name=f"corrected_{file_data['name']}",
                            mime="application/xml",
                            key=f"download_{idx}"
                        )
                
                # Rapport de traitement
                with st.expander("📋 Rapport détaillé"):
                    st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Fichiers traités:** {total_files}")
                    st.write(f"**Réussis:** {success_files}")
                    st.write(f"**Corrections appliquées:** {total_corrections}")
                    st.write("\n**Détails par fichier:**")
                    for result in results:
                        if result['Statut'] == '✅ Corrigé':
                            st.write(f"- ✅ {result['Fichier']} - Commande {result['Numéro commande']} - {result['Corrections']} corrections")
                        else:
                            st.write(f"- {result['Statut']} {result['Fichier']} - {result['Message']}")

# Pied de page
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>
    💡 Les données sont synchronisées depuis Google Sheets via GitHub<br>
    🔄 Actualisez la page pour voir les dernières mises à jour
    </small>
</div>
""", unsafe_allow_html=True)
