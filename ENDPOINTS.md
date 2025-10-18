# 📡 Documentation des Endpoints API AGRIA

## Vue d'ensemble

L'API AGRIA propose 3 endpoints principaux avec des formats de réponse adaptés à chaque usage.

---

## 🔍 1. `/upload-image` - Diagnostic Phytosanitaire Complet

### **Usage**
Analyse d'image agricole avec diagnostic structuré, recommandations priorisées et sources.

### **Méthode**
`POST`

### **Paramètres**
- `use_case` (string, obligatoire) - Type de culture (ex: "viticulture", "maraichage")
- `file` (file, obligatoire) - Image à analyser (JPG, PNG)
- `question` (string, optionnel) - Question spécifique sur l'image

### **Format de Réponse**

```json
{
  "status": "ok",
  "caption": {
    "diagnostic": {
      "niveau_confiance_global": 0.75,
      "stade_phenologique": "Floraison",
      "date_analyse": "2025-01-17",
      "hypotheses_diagnostiques": [
        {
          "rang": 1,
          "nom": "Mildiou de la vigne",
          "probabilite": 0.70,
          "niveau_gravite": "élevé",
          "justification": "Symptômes huileux + humidité élevée",
          "facteurs_favorables": ["Humidité >85%", "T° 18-22°C"],
          "sources": ["Ephytia.inrae.fr", "meteorologie.json"]
        }
      ],
      "diagnostic_principal": {
        "nom": "Mildiou de la vigne",
        "probabilite": 0.70,
        "synthese": "Forte probabilité de mildiou"
      },
      "risques_evolution": {
        "sans_intervention": "Extension rapide (72h)",
        "delai_critique": "24-48 heures",
        "conditions_aggravantes": ["Pluie annoncée"]
      }
    },
    "recommandations": {
      "actions_urgentes": [
        {
          "priorite": 1,
          "action": "Isoler zones touchées",
          "justification": "Limiter propagation",
          "delai": "0-24h",
          "methode": "Agroécologique - Observation",
          "cout_estime": "Faible",
          "sources": ["Guide IPM - INRAE"]
        }
      ],
      "actions_recommandees": [...],
      "surveillance_preventive": [...],
      "pratiques_preventives_futures": {
        "culturelles": [...],
        "mecaniques": [...],
        "biologiques": [...]
      }
    },
    "contexte": {
      "situation_meteorologique": {
        "resume_recent": "Humidité élevée",
        "anomalies_detectees": ["Humidité +20%"],
        "previsions_72h": "Pluie modérée",
        "impact_risque": "Conditions favorables mildiou"
      },
      "historique_parcelle": {
        "dernier_traitement": "Soufre - il y a 15j",
        "episodes_similaires": ["Juin 2023"]
      }
    },
    "sources_et_fiabilite": {
      "sources_utilisees": {
        "meteorologie": ["meteorologie.json"],
        "phytosanitaire": ["Ephytia.inrae.fr"],
        "instituts": ["INRAE", "IFV"],
        "reglementation": []
      },
      "fiabilite_analyse": {
        "qualite_image": "Bonne",
        "coherence_donnees": "Élevée",
        "completude_contexte": "Partielle",
        "niveau_confiance_final": 0.75
      },
      "limites_analyse": ["Image unique", "Historique incomplet"]
    }
  },
  "file_id": "uuid-1234-5678"
}
```

### **Exemple cURL**

```bash
curl -X POST "http://localhost:8000/upload-image" \
  -F "use_case=viticulture" \
  -F "file=@vigne.jpg" \
  -F "question=Analyse cette vigne"
```

---

## 💬 2. `/ask` - Conversation Naturelle

### **Usage**
Question/réponse en langage naturel sans image. Idéal pour des conseils généraux, explications, etc.

### **Méthode**
`POST`

### **Paramètres**
- `use_case` (string, obligatoire) - Type de culture
- `question` (string, obligatoire) - Question de l'agriculteur

### **Format de Réponse**

```json
{
  "status": "ok",
  "caption": {
    "answer": "Le mildiou de la vigne est une maladie cryptogamique causée par Plasmopara viticola. Elle se développe particulièrement dans des conditions d'humidité élevée (>85%) et de températures comprises entre 18 et 25°C.\n\nSymptômes caractéristiques:\n- Taches huileuses sur les feuilles\n- Duvet blanc au revers des feuilles\n- Dessèchement des grappes\n\nPrévention agroécologique:\n1. Effeuillage pour améliorer l'aération\n2. Enherbement inter-rang pour réduire l'humidité\n3. Surveillance régulière dès le débourrement\n\nSources: Ephytia.inrae.fr, IFV - Guide pratique viticulture"
  }
}
```

### **Exemple cURL**

```bash
curl -X POST "http://localhost:8000/ask" \
  -F "use_case=viticulture" \
  -F "question=Quels sont les symptômes du mildiou?"
```

### **Exemple Python**

```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    data={
        "use_case": "viticulture",
        "question": "Comment prévenir le mildiou naturellement?"
    }
)

print(response.json()["caption"]["answer"])
```

---

## 🎙️ 3. `/upload-audio` - Analyse Audio

### **Usage**
Transcription audio + analyse (si implémenté avec Whisper).

### **Méthode**
`POST`

### **Paramètres**
- `use_case` (string, obligatoire)
- `file` (file, obligatoire) - Fichier audio
- `question` (string, optionnel)

### **Format de Réponse**

```json
{
  "status": "ok",
  "transcription": "Texte transcrit de l'audio",
  "analysis": "Analyse basée sur la transcription"
}
```

---

## 📊 Comparaison des Endpoints

| Endpoint | Usage | Format Réponse | Avec Image | Structuré |
|----------|-------|----------------|------------|-----------|
| `/upload-image` | Diagnostic complet | JSON structuré | ✅ Oui | ✅ Oui |
| `/ask` | Conversation | Texte naturel | ❌ Non | ❌ Non |
| `/upload-audio` | Transcription | Texte + analyse | ❌ Non | ⚠️ Partiel |

---

## 🔒 Gestion des Erreurs

### **Erreur 422 - Validation**

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "use_case"],
      "msg": "Field required"
    }
  ],
  "message": "Erreur de validation - Vérifiez les paramètres"
}
```

### **Erreur 500 - Serveur**

Les endpoints retournent toujours un JSON valide, même en cas d'erreur:

```json
{
  "status": "error",
  "caption": {
    "answer": "Erreur: [détails de l'erreur]"
  }
}
```

---

## 🚀 Démarrage Rapide

### **1. Démarrer le serveur**

```bash
uvicorn app.main:app --reload
```

### **2. Tester avec cURL**

```bash
# Test /ask
curl -X POST "http://localhost:8000/ask" \
  -F "use_case=viticulture" \
  -F "question=Comment traiter le mildiou?"

# Test /upload-image
curl -X POST "http://localhost:8000/upload-image" \
  -F "use_case=viticulture" \
  -F "file=@image.jpg"
```

### **3. Documentation interactive**

Accédez à `http://localhost:8000/docs` pour la documentation Swagger interactive.

---

## 📝 Notes Importantes

### **`/upload-image`**
- ✅ Retourne un diagnostic structuré avec hypothèses pondérées
- ✅ Recommandations priorisées par urgence
- ✅ Sources citées pour chaque action
- ✅ Approche agroécologique (IPM)
- ✅ Transparence sur les limites de l'analyse

### **`/ask`**
- ✅ Réponse en langage naturel (pas de JSON structuré)
- ✅ Idéal pour questions générales, conseils, explications
- ✅ Utilise le RAG pour enrichir la réponse
- ✅ Cite les sources quand pertinent
- ❌ Pas de diagnostic structuré

---

**Version:** 2.0  
**Date:** 2025-01-18  
**API:** AGRIA Backend
