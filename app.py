import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Correcteur XML Boehringer", page_icon="🔧")

st.title("🔧 Correcteur XML Boehringer")
st.markdown("---")

# Charger les données localement pour l'instant
@st.cache_data
def load_data():
    """Charge les données CSV en dur pour tester"""
    data = {
        'Numéro de commande': ['000054', '000646'],
        'Code agence': ['LV2-LV2', 'LV2-LV2'],
        'Statut': ['N2 - Niveau 2 (4B +)', 'N1 - Niveau 1 (2A / 4A)'],
        'Classification': ['04B - 225', '03B - 195 Equipe'],
        'HRBP': ['Gabrielle Humbert', 'Houria Gherras']
    }
    return pd.DataFrame(data)

# Interface en deux colonnes
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Données")
    df = load_data()
    st.success(f"✅ {len(df)} commandes")
    st.dataframe(df)

with col2:
    st.subheader("📄 Upload XML")
    
    uploaded_file = st.file_uploader("Choisir un fichier XML", type=['xml'])
    
    if uploaded_file is not None:
        if st.button("Corriger"):
            try:
                # Lire le XML
                xml_content = uploaded_file.read()
                root = ET.fromstring(xml_content)
                
                # Chercher le numéro de commande (simple)
                num_cmd = None
                for elem in root.iter():
                    if 'order' in elem.tag.lower() or 'command' in elem.tag.lower():
                        if elem.text and elem.text.strip().isdigit():
                            num_cmd = elem.text.strip().zfill(6)
                            break
                
                if num_cmd:
                    st.success(f"Numéro trouvé: {num_cmd}")
                    
                    # Chercher dans les données
                    if num_cmd in df['Numéro de commande'].values:
                        st.success("✅ Commande trouvée dans les données")
                        
                        # Ajouter les balises (simplifié)
                        pos_char = root.find(".//PositionCharacteristics")
                        if pos_char is None:
                            pos_char = ET.SubElement(root, "PositionCharacteristics")
                        
                        # Télécharger le résultat
                        xml_str = ET.tostring(root, encoding='unicode')
                        st.download_button(
                            label="📥 Télécharger XML corrigé",
                            data=xml_str,
                            file_name=f"corrected_{uploaded_file.name}",
                            mime="application/xml"
                        )
                    else:
                        st.warning("Commande non trouvée dans les données")
                else:
                    st.error("Numéro de commande non trouvé dans le XML")
                    
            except Exception as e:
                st.error(f"Erreur: {str(e)}")
