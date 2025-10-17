# 🔒 Système de Validation JSON Strict - AGRIA

## Vue d'ensemble

Ce système garantit que l'API AGRIA retourne **toujours** un format JSON strict et validé, même en cas d'erreur du modèle LLM ou de parsing.

## 🎯 Objectif

Assurer la compatibilité avec les applications clientes qui dépendent d'un format JSON exact et immuable.

## 📋 Format de Réponse Garanti

### Structure Principale

```json
{
  "status": "ok",
  "caption": {
    "niveau_confiance": 0.0,
    "phenologie_actuelle": "string",
    "situation_meteorologique": {...},
    "analyse_historique": {...},
    "hypotheses_probables": [...],
    "pratiques_preventives": {...},
    "risques_abiotiques": [...],
    "sources_utilisees": [...]
  },
  "file_id": "uuid-string"
}
```

### Détails des Champs

#### `caption.situation_meteorologique`
```json
{
  "resume_recent": "string",
  "anomalies_detectees": ["string"],
  "risques_associes": ["string"]
}
```

#### `caption.analyse_historique`
```json
{
  "periode_comparee": "30_jours",
  "ecarts_moyens": {
    "temperature": "string",
    "humidite": "string",
    "precipitations": "string"
  },
  "episodes_similaires": ["string"]
}
```

#### `caption.hypotheses_probables[]`
```json
{
  "nom": "string",
  "probabilite": 0.0,  // Entre 0.0 et 1.0
  "justification": "string",
  "sources": ["string"]
}
```

#### `caption.pratiques_preventives`
```json
{
  "culturelles": ["string"],
  "mecaniques": ["string"],
  "biologiques": ["string"],
  "chimiques_en_dernier_recours": ["string"]
}
```

## 🛡️ Mécanismes de Sécurité

### 1. **Validation Pydantic Stricte**
- Tous les champs sont typés et validés
- Les valeurs par défaut sont définies pour chaque champ
- Les probabilités sont automatiquement bornées entre 0.0 et 1.0

### 2. **Parsing Robuste Multi-Stratégies**

Le système essaie plusieurs méthodes pour extraire le JSON:

1. **Parsing direct**: `json.loads(text)`
2. **Extraction par regex**: Cherche les accolades `{...}`
3. **Extraction de code blocks**: Cherche entre ` ```json ... ``` `

### 3. **Fallback Automatique**

En cas d'échec complet, le système retourne:

```json
{
  "status": "error",
  "caption": {
    "niveau_confiance": 0.0,
    "phenologie_actuelle": "Erreur lors de l'analyse: [détails]",
    "situation_meteorologique": {
      "resume_recent": "Données météorologiques non disponibles",
      "anomalies_detectees": [],
      "risques_associes": []
    },
    "analyse_historique": {
      "periode_comparee": "30_jours",
      "ecarts_moyens": {
        "temperature": "N/A",
        "humidite": "N/A",
        "precipitations": "N/A"
      },
      "episodes_similaires": []
    },
    "hypotheses_probables": [],
    "pratiques_preventives": {
      "culturelles": [],
      "mecaniques": [],
      "biologiques": [],
      "chimiques_en_dernier_recours": []
    },
    "risques_abiotiques": [],
    "sources_utilisees": ["Système de fallback"]
  },
  "file_id": null
}
```

### 4. **Force JSON via OpenAI API**

L'appel au LLM utilise:
```python
response_format={"type": "json_object"}
```

Cela force GPT-4o-mini à retourner uniquement du JSON valide.

## 🧪 Tests

Exécutez les tests de validation:

```bash
python test_json_validation.py
```

Les tests couvrent:
- ✅ JSON valide complet
- ✅ JSON partiel avec valeurs par défaut
- ✅ Auto-correction des probabilités invalides
- ✅ Schéma de réponse API complet
- ✅ Fallback avec JSON vide

## 📝 Utilisation

### Endpoint: `/upload-image`

**Requête:**
```bash
curl -X POST "http://localhost:8000/upload-image" \
  -F "use_case=viticulture" \
  -F "file=@image.jpg" \
  -F "question=Analyse cette vigne"
```

**Réponse garantie:**
- Type: `application/json`
- Schéma: `APIResponseSchema`
- Validation: Automatique via Pydantic

### Gestion des Erreurs

Le système **ne lève jamais d'exception HTTP 500** pour les erreurs de parsing JSON.

Au lieu de cela:
- `status: "error"` dans la réponse
- `caption` contient un objet de fallback valide
- `file_id: null`

## 🔧 Architecture

```
┌─────────────────┐
│   FastAPI       │
│   /upload-image │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   RAG.ask()     │
│   - retrieve    │
│   - call_llm    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ OpenAI GPT-4o-mini      │
│ response_format: json   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ _extract_json_from_text │
│ (3 stratégies)          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ _validate_and_fix_json  │
│ (Pydantic validation)   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ APIResponseSchema       │
│ (Réponse finale)        │
└─────────────────────────┘
```

## ⚠️ Contraintes Importantes

### **NE JAMAIS:**
- Modifier la structure du schéma `AnalyseAgricoleSchema` sans coordination avec les apps clientes
- Supprimer les valeurs par défaut des champs
- Retourner `null` pour `caption` (toujours un objet valide)

### **TOUJOURS:**
- Valider avec Pydantic avant de retourner
- Utiliser le fallback en cas d'erreur
- Logger les erreurs de parsing pour debugging

## 📊 Monitoring

Les logs incluent:
- ⚠️ Warnings pour les erreurs de validation JSON
- ❌ Errors pour les échecs d'appel LLM
- ℹ️ Info pour les fallbacks utilisés

Exemple:
```
WARNING:app.rag:Erreur de validation JSON: 1 validation error for AnalyseAgricoleSchema
ERROR:app.rag:Erreur lors de l'appel au LLM: API timeout
```

## 🚀 Déploiement

Le système est prêt pour la production avec:
- ✅ Validation stricte des types
- ✅ Gestion d'erreurs robuste
- ✅ Fallback automatique
- ✅ Tests de validation
- ✅ Documentation complète

## 📞 Support

En cas de problème avec le format JSON:
1. Vérifier les logs de l'application
2. Exécuter `test_json_validation.py`
3. Vérifier que `OPENAI_API_KEY` est configurée
4. Tester avec un exemple simple

---

**Version:** 1.0  
**Dernière mise à jour:** 2025-01-17  
**Mainteneur:** Équipe AGRIA
