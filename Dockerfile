# Étape 1 : Image de base
FROM python:3.10-slim

# Étape 2 : Définir le dossier de travail
WORKDIR /app

# Étape 3 : Copier les fichiers
COPY . .

# Étape 4 : Installer les dépendances système pour audio + PDF + Whisper
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Étape 5 : Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Étape 6 : Définir la variable d’environnement pour FastAPI
ENV PYTHONUNBUFFERED=1

# Étape 7 : Exposer le port FastAPI
EXPOSE 8000

# Étape 8 : Lancer le serveur
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
