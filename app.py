import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
from io import StringIO, BytesIO
import json
from datetime import datetime
import zipfile

# Configuration
GITHUB_REPO = "younessemlali/xml-boehringer-corrector"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main"

# Configuration de la page
st.set_page_config(
    page_title="Correcteur XML Boehringer",
    page_icon="🔧",
    layout="wide"
)

# CSS personnalisé
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton > button {
        background-color: #0068c9;
        color: white;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Titre et description
st.title("🔧 Correcteur XML Boehringer")
st.markdown("---")
st.markdown("""
Cette application corrige automatiquement les fichiers XML de contrats en ajoutant ou modifiant 
les balises manquantes basées sur les données des commandes.
""")

# Fonction pour charger les données depuis GitHub
@st.cache_data(ttl=300)  # Cache pendant 5 minutes
def load_data_from_github():
    """Charge les données CSV depuis GitHub"""
    try:
        # Essayer d'abord le CSV
        csv_url = f"{GITHUB_RAW_URL}/commandes.csv"
        response = requests.get(csv_url)
        
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            # S'assurer que le numéro de commande est en string avec zéros
            if 'Numéro de commande' in df.columns:
                df['Numéro de commande'] = df['Numéro de commande'].astype(str).str.zfill(6)
            return df, None
        else:
            return None, f"Erreur lors du chargement du CSV: {response.status_code}"
            
    except Exception as e:
        return None, f"Erreur: {str(e)}"

# Fonction pour parser le XML
def parse_xml(xml_content):
    """Parse le contenu XML et retourne l'arbre et la racine"""
    try:
        # Essayer de parser comme string
        if isinstance(xml_content, bytes):
            xml_content = xml_content.decode('utf-8')
        
        # Parser le XML
        root = ET.fromstring(xml_content)
        return ET.ElementTree(root), root, None
    except Exception as e:
        return None, None, f"Erreur lors du parsing XML: {str(e)}"

# Fonction pour extraire le numéro de commande du XML
def extract_command_number(root):
    """Extrait le numéro de commande du XML"""
    # Chercher dans différents endroits possibles
    possible_paths = [
        ".//OrderNumber",
        ".//CommandNumber",
        ".//NumeroCommande",
        ".//ContractNumber",
        ".//Reference",
        ".//*[@type='order']",
        ".//*[@type='commande']"
    ]
    
    for path in possible_paths:
        elem = root.find(path)
        if elem is not None and elem.text:
            # Formater avec zéros si nécessaire
            return elem.text.strip().zfill(6)
    
    # Si pas trouvé, chercher dans les attributs
    for elem in root.iter():
        for attr in ['orderNumber', 'commandNumber', 'numero', 'ref']:
            if attr in elem.attrib:
                return elem.attrib[attr].strip().zfill(6)
    
    return None

# Fonction pour corriger le XML
def correct_xml(tree, root, commande_data):
    """Corrige le XML en ajoutant/modifiant les balises nécessaires"""
    corrections = []
    
    # Trouver ou créer PositionCharacteristics
    pos_char = root.find(".//PositionCharacteristics")
    if pos_char is None:
        # Créer la section si elle n'existe pas
        pos_char = ET.SubElement(root, "PositionCharacteristics")
        corrections.append("Création de la section PositionCharacteristics")
    
    # Mapping des champs
    field_mapping = {
        'PositionStatus': ('Statut', 'Code'),
        'PositionLevel': ('Classification', None),
        'PositionCoefficient': ('HRBP', None)
    }
    
    for xml_tag, (csv_field, sub_tag) in field_mapping.items():
        if csv_field in commande_data and pd.notna(commande_data[csv_field]):
            value = str(commande_data[csv_field])
            
            # Trouver ou créer l'élément
            elem = pos_char.find(f".//{xml_tag}")
            if elem is None:
                elem = ET.SubElement(pos_char, xml_tag)
                corrections.append(f"Ajout de la balise {xml_tag}")
            
            if sub_tag:
                # Pour PositionStatus, on a besoin d'un sous-élément Code
                code_elem = elem.find(sub_tag)
                if code_elem is None:
                    code_elem = ET.SubElement(elem, sub_tag)
                
                # Extraire le code (ex: "N2" de "N2 - Niveau 2 (4B +)")
                code_value = value.split(' ')[0] if ' ' in value else value
                code_elem.text = code_value
                
                # Ajouter la description si nécessaire
                desc_elem = elem.find("Description")
                if desc_elem is None:
                    desc_elem = ET.SubElement(elem, "Description")
                desc_elem.text = value
            else:
                # Pour les autres, mettre directement la valeur
                elem.text = value
                corrections.append(f"Mise à jour de {xml_tag}: {value}")
    
    return tree, corrections

# Interface principale
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Données des commandes")
    
    # Charger les données
    df, error = load_data_from_github()
    
    if error:
        st.error(error)
        st.stop()
    
    if df is not None and not df.empty:
        st.success(f"✅ {len(df)} commandes chargées")
        
        # Afficher un aperçu des données
        with st.expander("Voir les données", expanded=False):
            st.dataframe(df, height=200)
        
        # Statistiques
        st.markdown("**Statistiques:**")
        stats_cols = st.columns(2)
        with stats_cols[0]:
            st.metric("Total commandes", len(df))
            st.metric("Agences uniques", df['Code agence'].nunique() if 'Code agence' in df.columns else 0)
        with stats_cols[1]:
            st.metric("HRBP uniques", df['HRBP'].nunique() if 'HRBP' in df.columns else 0)
            st.metric("Dernière mise à jour", datetime.now().strftime("%H:%M"))
    else:
        st.warning("Aucune donnée trouvée")

with col2:
    st.subheader("📄 Correction des fichiers XML")
    
    # Upload de fichiers
    uploaded_files = st.file_uploader(
        "Déposez vos fichiers XML ici",
        type=['xml'],
        accept_multiple_files=True,
        help="Vous pouvez sélectionner plusieurs fichiers XML à la fois"
    )
    
    if uploaded_files and df is not None:
        st.markdown(f"**{len(uploaded_files)} fichier(s) sélectionné(s)**")
        
        # Bouton de traitement
        if st.button("🚀 Corriger les fichiers", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            corrected_files = []
            
            for idx, uploaded_file in enumerate(uploaded_files):
                progress = (idx + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Traitement de {uploaded_file.name}...")
                
                # Lire le contenu du fichier
                xml_content = uploaded_file.read()
                
                # Parser le XML
                tree, root, error = parse_xml(xml_content)
                
                if error:
                    results.append({
                        'Fichier': uploaded_file.name,
                        'Statut': '❌ Erreur',
                        'Message': error,
                        'Corrections': 0
                    })
                    continue
                
                # Extraire le numéro de commande
                num_commande = extract_command_number(root)
                
                if not num_commande:
                    results.append({
                        'Fichier': uploaded_file.name,
                        'Statut': '⚠️ Attention',
                        'Message': 'Numéro de commande non trouvé dans le XML',
                        'Corrections': 0
                    })
                    continue
                
                # Chercher la commande dans les données
                commande_row = df[df['Numéro de commande'] == num_commande]
                
                if commande_row.empty:
                    results.append({
                        'Fichier': uploaded_file.name,
                        'Statut': '⚠️ Non trouvé',
                        'Message': f'Commande {num_commande} non trouvée dans les données',
                        'Corrections': 0
                    })
                    continue
                
                # Corriger le XML
                commande_data = commande_row.iloc[0].to_dict()
                tree_corrected, corrections = correct_xml(tree, root, commande_data)
                
                # Sauvegarder le XML corrigé
                xml_str = ET.tostring(root, encoding='unicode', method='xml')
                corrected_files.append({
                    'name': f"corrected_{uploaded_file.name}",
                    'content': xml_str
                })
                
                results.append({
                    'Fichier': uploaded_file.name,
                    'Statut': '✅ Corrigé',
                    'Message': f'Commande {num_commande}',
                    'Corrections': len(corrections)
                })
            
            # Effacer la barre de progression
            progress_bar.empty()
            status_text.empty()
            
            # Afficher les résultats
            st.markdown("### 📋 Résultats du traitement")
            
            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True)
            
            # Statistiques de traitement
            total_files = len(results)
            success_files = len([r for r in results if r['Statut'] == '✅ Corrigé'])
            total_corrections = sum([r['Corrections'] for r in results])
            
            metrics_cols = st.columns(3)
            with metrics_cols[0]:
                st.metric("Fichiers traités", total_files)
            with metrics_cols[1]:
                st.metric("Fichiers corrigés", success_files)
            with metrics_cols[2]:
                st.metric("Total corrections", total_corrections)
            
            # Téléchargement des fichiers corrigés
            if corrected_files:
                st.markdown("### 📥 Télécharger les fichiers corrigés")
                
                # Option 1: Télécharger individuellement
                with st.expander("Télécharger individuellement", expanded=False):
                    for file_data in corrected_files:
                        st.download_button(
                            label=f"📄 {file_data['name']}",
                            data=file_data['content'],
                            file_name=file_data['name'],
                            mime="application/xml"
                        )
                
                # Option 2: Télécharger en ZIP
                if len(corrected_files) > 1:
                    # Créer un ZIP
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for file_data in corrected_files:
                            zip_file.writestr(file_data['name'], file_data['content'])
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label="📦 Télécharger tous les fichiers (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"xml_corriges_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        type="primary"
                    )

# Pied de page
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Correcteur XML Boehringer v1.0 | Données synchronisées avec Google Sheets via GitHub</p>
</div>
""", unsafe_allow_html=True)
