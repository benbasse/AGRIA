# 🔍 Validation d'Image - Système de Pré-Diagnostic

## Vue d'ensemble

Avant d'effectuer un diagnostic phytosanitaire complet, le système valide que l'image fournie correspond bien au `use_case` demandé. Cela évite les analyses inutiles et améliore la pertinence des diagnostics.

---

## 🎯 Objectifs

1. **Vérifier que l'image est agricole** (pas une photo de chat, de voiture, etc.)
2. **Vérifier la correspondance avec le use_case** (vigne pour viticulture, tomate pour maraîchage, etc.)
3. **Détecter les cas où l'image peut alerter** même si différente (ravageur commun, maladie transmissible)
4. **Retourner un message clair** si l'image n'est pas exploitable

---

## 🔄 Flux de Validation

```
┌─────────────────────┐
│  Image uploadée     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│ Validation préalable        │
│ (_validate_image_for_usecase)│
└──────────┬──────────────────┘
           │
           ├─── ❌ Non agricole ────────────┐
           │                                 │
           ├─── ❌ Mauvais use_case ────────┤
           │    (ne peut pas alerter)       │
           │                                 │
           ├─── ⚠️ Mauvais use_case ────────┤
           │    (PEUT alerter)              │
           │                                 │
           └─── ✅ Valide ─────────────────┤
                                            │
                                            ▼
                              ┌──────────────────────┐
                              │ Retour format simple │
                              │ {"status": "ok",     │
                              │  "caption": {        │
                              │    "answer": "..."   │
                              │  }}                  │
                              └──────────────────────┘
                                            │
                                            ▼
                              ┌──────────────────────┐
                              │ Diagnostic complet   │
                              │ (format structuré)   │
                              └──────────────────────┘
```

---

## 📊 Cas de Validation

### **Cas 1: Image Non Agricole** ❌

**Exemple:** Photo de chat, voiture, intérieur de maison

**Réponse:**
```json
{
  "status": "ok",
  "caption": {
    "answer": "❌ Cette image ne semble pas être une image agricole. Veuillez fournir une photo de culture, plante ou sol agricole."
  }
}
```

---

### **Cas 2: Mauvais Use_case (ne peut pas alerter)** ❌

**Exemple:** 
- Use_case: `viticulture`
- Image: Tomates

**Réponse:**
```json
{
  "status": "ok",
  "caption": {
    "answer": "❌ Cette image montre une culture de type 'tomate' qui ne correspond pas au use_case 'viticulture'. Les tomates et la vigne n'ont pas de problèmes phytosanitaires communs.\n\nVeuillez fournir une image correspondant à votre use_case."
  }
}
```

---

### **Cas 3: Mauvais Use_case (PEUT alerter)** ⚠️

**Exemple:**
- Use_case: `viticulture`
- Image: Pommier avec pucerons (ravageur commun)

**Réponse:**
```json
{
  "status": "ok",
  "caption": {
    "diagnostic": {
      "niveau_confiance_global": 0.65,
      "stade_phenologique": "Croissance",
      "hypotheses_diagnostiques": [
        {
          "rang": 1,
          "nom": "Pucerons",
          "probabilite": 0.70,
          "niveau_gravite": "modéré",
          "justification": "Présence de pucerons sur pommier. Attention: ce ravageur peut aussi affecter la vigne.",
          "facteurs_favorables": ["Ravageur polyphage"],
          "sources": ["Ephytia.inrae.fr"]
        }
      ],
      "diagnostic_principal": {
        "nom": "Pucerons",
        "probabilite": 0.70,
        "synthese": "⚠️ Image de pommier détectée (use_case: viticulture). Analyse effectuée car les pucerons sont un ravageur commun."
      }
    },
    ...
  }
}
```

**Diagnostic complet effectué** car le problème peut alerter sur le use_case.

---

### **Cas 4: Image Valide** ✅

**Exemple:**
- Use_case: `viticulture`
- Image: Vigne avec symptômes

**Réponse:**
```json
{
  "status": "ok",
  "caption": {
    "diagnostic": {
      "niveau_confiance_global": 0.85,
      "stade_phenologique": "Floraison",
      "hypotheses_diagnostiques": [...]
    },
    ...
  }
}
```

**Diagnostic complet normal.**

---

## 🧠 Logique de Décision

### **Validation LLM**

Le système utilise GPT-4o-mini pour analyser l'image et retourner:

```json
{
  "is_agricultural": true/false,
  "detected_culture": "nom de la culture",
  "matches_usecase": true/false,
  "can_alert": true/false,
  "reason": "explication"
}
```

### **Critères "can_alert"**

Une image peut alerter si:
- ✅ Ravageur polyphage (pucerons, cochenilles, etc.)
- ✅ Maladie transmissible entre cultures
- ✅ Problème de sol commun
- ✅ Condition météo défavorable visible
- ❌ Culture totalement différente sans lien

**Exemples:**
- Pucerons sur pommier → **PEUT** alerter pour viticulture
- Mildiou sur tomate → **PEUT** alerter pour viticulture (même famille de maladies)
- Blé avec rouille → **NE PEUT PAS** alerter pour viticulture (cultures trop différentes)

---

## 🛠️ Implémentation Technique

### **Méthode: `_validate_image_for_usecase()`**

```python
def _validate_image_for_usecase(self, image_path: str, use_case: str) -> dict:
    """
    Valide que l'image correspond au use_case.
    
    Returns:
        {
            "is_valid": bool,
            "can_alert": bool,
            "message": str,
            "detected_type": str
        }
    """
```

### **Intégration dans `ask()`**

```python
def ask(self, use_case, question, image_path=None, system_prompt=None):
    # ÉTAPE 1: Validation préalable
    if image_path:
        validation = self._validate_image_for_usecase(image_path, use_case)
        
        if not validation["is_valid"] and not validation["can_alert"]:
            # Retour simple
            return {
                "answer": validation["message"],
                "context": [],
                "metadatas": []
            }
    
    # ÉTAPE 2: Diagnostic complet (si valide ou peut alerter)
    ...
```

---

## 📝 Gestion dans l'Endpoint

### **`/upload-image`**

```python
@app.post("/upload-image", response_model=Union[APIResponseSchema, SimpleAPIResponseSchema])
async def upload_image(...):
    analysis = rag.ask(use_case, question, image_path=path)
    
    # Si validation échoue, analysis["answer"] est une string
    if isinstance(analysis["answer"], str):
        return SimpleAPIResponseSchema(
            status="ok",
            caption=SimpleAnswerSchema(answer=analysis["answer"])
        )
    
    # Sinon, diagnostic complet
    return APIResponseSchema(
        status="ok",
        caption=analysis["answer"],
        file_id=file_id
    )
```

---

## 🧪 Tests

### **Test 1: Image non agricole**

```bash
curl -X POST "http://localhost:8000/upload-image" \
  -F "use_case=viticulture" \
  -F "file=@chat.jpg"
```

**Attendu:**
```json
{
  "status": "ok",
  "caption": {
    "answer": "❌ Cette image ne semble pas être une image agricole..."
  }
}
```

---

### **Test 2: Mauvais use_case**

```bash
curl -X POST "http://localhost:8000/upload-image" \
  -F "use_case=viticulture" \
  -F "file=@tomate.jpg"
```

**Attendu:**
```json
{
  "status": "ok",
  "caption": {
    "answer": "❌ Cette image montre une culture de type 'tomate'..."
  }
}
```

---

### **Test 3: Image valide**

```bash
curl -X POST "http://localhost:8000/upload-image" \
  -F "use_case=viticulture" \
  -F "file=@vigne.jpg"
```

**Attendu:** Diagnostic complet (format structuré)

---

## ⚙️ Configuration

### **Paramètres de Validation**

- **Model:** `gpt-4o-mini` (rapide et économique)
- **Max tokens:** 300 (suffisant pour la validation)
- **Temperature:** 0.3 (précision maximale)

### **Gestion d'Erreurs**

En cas d'erreur de validation (API timeout, etc.), le système **laisse passer** l'image pour ne pas bloquer l'utilisateur:

```python
except Exception as e:
    return {
        "is_valid": True,  # On laisse passer
        "can_alert": False,
        "message": "⚠️ Validation impossible, analyse effectuée",
        "error": str(e)
    }
```

---

## 📊 Avantages

✅ **Économie de tokens** - Évite les diagnostics inutiles  
✅ **Meilleure UX** - Messages clairs si image invalide  
✅ **Flexibilité** - Permet les alertes inter-cultures  
✅ **Robustesse** - Fallback en cas d'erreur  
✅ **Traçabilité** - Logs de validation

---

## 🔮 Améliorations Futures

1. **Cache de validation** - Éviter de re-valider la même image
2. **Validation multi-critères** - Qualité, netteté, angle, etc.
3. **Suggestions** - "Votre image semble être une tomate, voulez-vous changer le use_case?"
4. **Statistiques** - Taux de rejet par use_case

---

**Version:** 1.0  
**Date:** 2025-01-18  
**Auteur:** Équipe AGRIA
