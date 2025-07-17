# Correcteur XML Boehringer

Application Streamlit pour corriger automatiquement les fichiers XML de contrats Boehringer en ajoutant ou modifiant les balises manquantes basées sur les données des commandes.

## 🚀 Fonctionnalités

- **Chargement automatique** des données depuis GitHub (CSV)
- **Upload multiple** de fichiers XML
- **Correction automatique** des balises manquantes :
  - `PositionStatus` (avec Code et Description)
  - `PositionLevel` (Classification)
  - `PositionCoefficient` (HRBP)
- **Téléchargement** des fichiers corrigés (individuellement ou en ZIP)
- **Tableau de bord** avec statistiques et métriques

## 📋 Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)

## 🛠️ Installation

1. Cloner le repository :
```bash
git clone https://github.com/younessemlali/xml-boehringer-corrector.git
cd xml-boehringer-corrector
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## 🏃‍♂️ Utilisation

### Lancement local

```bash
streamlit run streamlit_app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

### Déploiement sur Streamlit Cloud

1. Créez un compte sur [Streamlit Cloud](https://streamlit.io/cloud)
2. Connectez votre repository GitHub
3. Déployez l'application

## 📊 Format des données

### CSV d'entrée (commandes.csv)

Le fichier CSV doit contenir les colonnes suivantes :
- `Numéro de commande` : Identifiant unique (format: 000XXX)
- `Code agence` : Code de l'agence
- `Statut` : Statut du poste (ex: "N2 - Niveau 2 (4B +)")
- `Classification` : Classification du poste (ex: "04B - 225")
- `HRBP` : Nom du HRBP
- `Date extraction` : Date d'extraction des données
- `Nom fichier source` : Nom du fichier HTML source

### XML à corriger

Les fichiers XML doivent contenir un numéro de commande identifiable dans l'une de ces balises :
- `<OrderNumber>`
- `<CommandNumber>`
- `<NumeroCommande>`
- `<ContractNumber>`
- `<Reference>`

## 🔧 Structure du projet

```
xml-boehringer-corrector/
├── streamlit_app.py      # Application principale
├── requirements.txt      # Dépendances Python
├── README.md            # Documentation
├── commandes.csv        # Données des commandes (généré automatiquement)
├── commandes.json       # Données au format JSON (optionnel)
└── .gitignore          # Fichiers à ignorer
```

## 🔄 Flux de données

1. **Google Apps Script #1** : Archive les emails dans Drive
2. **Google Apps Script #2** : Parse les HTML et pousse vers GitHub
3. **Application Streamlit** : Lit les données depuis GitHub et corrige les XML

## 📝 Exemple de correction

### XML avant :
```xml
<PositionCharacteristics>
    <PositionTitle>Technicien Animalier</PositionTitle>
    <Description>...</Description>
</PositionCharacteristics>
```

### XML après :
```xml
<PositionCharacteristics>
    <PositionTitle>Technicien Animalier</PositionTitle>
    <PositionStatus>
        <Code>N2</Code>
        <Description>N2 - Niveau 2 (4B +)</Description>
    </PositionStatus>
    <Description>...</Description>
    <PositionLevel>04B - 225</PositionLevel>
    <PositionCoefficient>Gabrielle Humbert</PositionCoefficient>
</PositionCharacteristics>
```

## 🐛 Dépannage

### L'application ne trouve pas les données
- Vérifiez que le fichier `commandes.csv` existe dans le repository
- Vérifiez que le repository est public ou que vous avez les droits d'accès

### Les numéros de commande ne correspondent pas
- Assurez-vous que les numéros dans le CSV ont le format avec zéros (000XXX)
- Vérifiez que le XML contient bien un numéro de commande

### Erreur de parsing XML
- Vérifiez que le fichier est un XML valide
- Assurez-vous que l'encoding est UTF-8

## 📧 Support

Pour toute question ou problème, créez une issue sur GitHub.

## 📄 License

Ce projet est sous licence privée Randstad.
