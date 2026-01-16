import pandas as pd  # 🧠 Bibliothèque pour manipuler des fichiers CSV facilement

# --- 1️⃣ Charger le fichier CSV LinkedIn ---
# Remplace le nom du fichier si nécessaire (il doit être dans le même dossier que ton script)
fichier_source = "Connections_from_LinkedIn.csv"

# On charge les données dans un DataFrame (une sorte de tableau intelligent)
df = pd.read_csv(fichier_source)

# --- 2️⃣ Inspection rapide du contenu ---
print("Aperçu du fichier :")
print(df.head())  # Affiche les 5 premières lignes pour vérification

# --- 3️⃣ Normalisation du texte ---
# On met toutes les colonnes en minuscules pour faciliter les comparaisons
df.columns = [col.lower().strip() for col in df.columns]

# On crée une colonne combinée pour chercher des mots-clés
df["profil_complet"] = df.apply(lambda x: " ".join(x.astype(str)).lower(), axis=1)

# --- 4️⃣ Exclusion des profils non-ciblés ---
# Mots-clés à exclure (étudiants, métiers du numérique, alternance, etc.)
mots_exclus = [
    "étudiant", "alternance", "stagiaire", "stage",
    "developer", "développeur", "frontend", "backend", "data",
    "designer", "ux", "ui", "web", "digital", "numérique", "informatique",
    "ai", "machine learning", "python", "tech", "dev", "it"
]

# Création d’un masque booléen : True = garder, False = exclure
df_filtre = df[~df["profil_complet"].str.contains("|".join(mots_exclus), case=False, na=False)]

# --- 5️⃣ Sauvegarde des résultats ---
fichier_resultat = "prospects_filtrés.csv"
df_filtre.to_csv(fichier_resultat, index=False, encoding="utf-8-sig")

# --- 6️⃣ Afficher le résultat ---
print(f"\n✅ Tri terminé ! {len(df_filtre)} contacts conservés sur {len(df)}.")
print(f"📁 Résultat enregistré dans : {fichier_resultat}")
