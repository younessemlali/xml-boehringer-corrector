import streamlit as st

st.title("Test Application Boehringer")
st.write("Si vous voyez ce message, l'application fonctionne !")

# Test basique de lecture CSV
try:
    import pandas as pd
    import requests
    
    url = "https://raw.githubusercontent.com/younessemlali/xml-boehringer-corrector/main/commandes.csv"
    response = requests.get(url)
    
    if response.status_code == 200:
        st.success("✅ Connexion GitHub OK")
        
        # Lire le CSV
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        st.write(f"Nombre de commandes: {len(df)}")
        st.dataframe(df.head())
    else:
        st.error(f"Erreur: {response.status_code}")
        
except Exception as e:
    st.error(f"Erreur: {e}")
