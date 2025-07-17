import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import requests
from io import StringIO

st.set_page_config(page_title="Correcteur XML Boehringer", page_icon="🔧", layout="wide")

# En-tête avec explication
st.title("🔧 Correcteur XML Boehringer")
st.markdown("""
### 📋 Comment ça marche ?

Cette application corrige automatiquement les fichiers XML de contrats Boehringer en :
1. **Détectant** le numéro de commande dans votre fichier XML
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
            # S'assurer que les numéros gardent leurs zéros
            if 'Numéro de commande' in df.columns:
                df['Numéro de commande'] = df['Numéro de commande'].astype(str).str.zfill(6)
            return df, None
        else:
            return None, f"Erreur HTTP {response.status_code}"
    except Exception as e:
        return None, f"Erreur: {str(e)}"

# Interface en deux colonnes
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Base de données des commandes")
    
    df, error = load_data_from_github()
    
    if error:
        st.error(error)
        # Données de secours
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
    
    # Afficher TOUTES les colonnes importantes
    columns_to_show = ['Numéro de commande', 'Statut', 'Classification', 'HRBP', 'Code agence']
    available_columns = [col for col in columns_to_show if col in df.columns]
    
    # Afficher le dataframe complet sans limitation de hauteur
    st.dataframe(
        df[available_columns],
        use_container_width=True,
        hide_index=True
    )
    
    # Explication des numéros
    with st.expander("ℹ️ À propos des numéros de commande"):
        st.markdown("""
        **Format des numéros :**
        - Les numéros sont sur 6 chiffres avec des zéros devant
        - Exemple : `000054`, `000646`
        - Ces numéros doivent correspondre exactement à ceux dans vos fichiers XML
        
        **Commandes disponibles :**
        """)
        for num in df['Numéro de commande'].unique():
            row = df[df['Numéro de commande'] == num].iloc[0]
            st.write(f"- **{num}** : {row['HRBP']} - {row['Statut']}")

with col2:
    st.subheader("📄 Correction des fichiers XML")
    
    # Exemple de XML attendu
    with st.expander("📝 Exemple de structure XML attendue"):
        st.code("""<?xml version="1.0" encoding="UTF-8"?>
<Contract>
    <OrderNumber>000054</OrderNumber>
    <!-- ou -->
    <CommandNumber>000054</CommandNumber>
    <!-- ou toute balise contenant le numéro -->
    
    <PositionCharacteristics>
        <!-- Les balises suivantes seront ajoutées/corrigées -->
    </PositionCharacteristics>
</Contract>""", language="xml")
    
    uploaded_file = st.file_uploader(
        "Choisir un fichier XML",
        type=['xml'],
        help="Le fichier doit contenir un numéro de commande (000054, 000646, etc.)"
    )
    
    if uploaded_file is not None:
        st.info(f"📎 Fichier sélectionné : {uploaded_file.name}")
        
        if st.button("🚀 Analyser et corriger", type="primary"):
            try:
                # Lire et parser le XML
                xml_content = uploaded_file.read()
                root = ET.fromstring(xml_content)
                
                st.markdown("### 🔍 Analyse du fichier")
                
                # Recherche du numéro de commande
                num_cmd = None
                found_in = None
                
                # Recherche dans différents endroits
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
                        num_cmd = elem.text.strip().zfill(6)
                        found_in = tag_name
                        break
                
                if num_cmd:
                    st.success(f"✅ Numéro de commande trouvé : **{num_cmd}** (dans la balise `{found_in}`)")
                    
                    # Recherche dans la base
                    if num_cmd in df['Numéro de commande'].values:
                        commande = df[df['Numéro de commande'] == num_cmd].iloc[0]
                        
                        st.markdown("### 📝 Données à appliquer")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Statut", commande['Statut'])
                            st.metric("Classification", commande['Classification'])
                        with col_b:
                            st.metric("HRBP", commande['HRBP'])
                            st.metric("Code agence", commande['Code agence'])
                        
                        # Corrections
                        st.markdown("### 🔧 Corrections effectuées")
                        corrections = []
                        
                        # Trouver ou créer PositionCharacteristics
                        pos_char = root.find(".//PositionCharacteristics")
                        if pos_char is None:
                            pos_char = ET.SubElement(root, "PositionCharacteristics")
                            corrections.append("✅ Création de la section `PositionCharacteristics`")
                        
                        # Ajouter/modifier PositionStatus
                        pos_status = pos_char.find("PositionStatus")
                        if pos_status is None:
                            pos_status = ET.SubElement(pos_char, "PositionStatus")
                            corrections.append("✅ Ajout de `PositionStatus`")
                        
                        code_elem = pos_status.find("Code")
                        if code_elem is None:
                            code_elem = ET.SubElement(pos_status, "Code")
                        code_elem.text = commande['Statut'].split()[0]  # Ex: "N2"
                        
                        desc_elem = pos_status.find("Description")
                        if desc_elem is None:
                            desc_elem = ET.SubElement(pos_status, "Description")
                        desc_elem.text = commande['Statut']
                        
                        # Ajouter/modifier PositionLevel
                        pos_level = pos_char.find("PositionLevel")
                        if pos_level is None:
                            pos_level = ET.SubElement(pos_char, "PositionLevel")
                            corrections.append("✅ Ajout de `PositionLevel`")
                        pos_level.text = commande['Classification']
                        
                        # Ajouter/modifier PositionCoefficient
                        pos_coef = pos_char.find("PositionCoefficient")
                        if pos_coef is None:
                            pos_coef = ET.SubElement(pos_char, "PositionCoefficient")
                            corrections.append("✅ Ajout de `PositionCoefficient`")
                        pos_coef.text = commande['HRBP']
                        
                        if corrections:
                            for correction in corrections:
                                st.write(correction)
                        else:
                            st.info("ℹ️ Toutes les balises étaient déjà présentes, valeurs mises à jour")
                        
                        # Générer le XML corrigé
                        xml_str = ET.tostring(root, encoding='unicode', method='xml')
                        
                        # Bouton de téléchargement
                        st.markdown("### 💾 Téléchargement")
                        st.download_button(
                            label="📥 Télécharger le XML corrigé",
                            data=xml_str,
                            file_name=f"corrected_{uploaded_file.name}",
                            mime="application/xml",
                            type="primary"
                        )
                        
                        # Aperçu du résultat
                        with st.expander("👁️ Aperçu du XML corrigé"):
                            st.code(xml_str[:1000] + "..." if len(xml_str) > 1000 else xml_str, language="xml")
                            
                    else:
                        st.error(f"""
                        ❌ La commande **{num_cmd}** n'existe pas dans la base de données.
                        
                        **Commandes disponibles :** {', '.join(df['Numéro de commande'].unique())}
                        """)
                else:
                    st.error("""
                    ❌ Aucun numéro de commande trouvé dans le fichier XML.
                    
                    Assurez-vous que votre fichier contient une balise comme :
                    - `<OrderNumber>000054</OrderNumber>`
                    - `<CommandNumber>000646</CommandNumber>`
                    - Ou similaire...
                    """)
                    
            except ET.ParseError as e:
                st.error(f"❌ Erreur de parsing XML : {str(e)}")
            except Exception as e:
                st.error(f"❌ Erreur inattendue : {str(e)}")

# Pied de page
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>
    💡 Astuce : Les données sont synchronisées automatiquement depuis Google Sheets toutes les 15 minutes<br>
    🔄 Dernière mise à jour : Actualiser la page pour voir les dernières données
    </small>
</div>
""", unsafe_allow_html=True)
