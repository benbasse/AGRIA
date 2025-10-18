# 🎯 Format JSON V2 - Diagnostic Nuancé et Recommandations Priorisées

## 📋 Vue d'ensemble

La version 2 du format JSON AGRIA est conçue pour fournir des **diagnostics nuancés** avec **recommandations actionnables et sourcées**, conformément aux meilleures pratiques agronomiques.

## 🔑 Principes Fondamentaux

### 1. **Diagnostic Nuancé**
- ✅ Liste d'hypothèses pondérées (pas un seul diagnostic absolu)
- ✅ Probabilités explicites pour chaque hypothèse
- ✅ Niveau de gravité (élevé, modéré, faible)
- ✅ Facteurs favorables détaillés

### 2. **Recommandations Priorisées**
- ✅ **Actions urgentes** (0-24h) - Priorité 1-2
- ✅ **Actions recommandées** (24h-7j) - Priorité 3-5
- ✅ **Surveillance préventive** - Monitoring continu
- ✅ **Pratiques futures** - Saison prochaine

### 3. **Sources Systématiques**
- ✅ Source citée pour **chaque** recommandation
- ✅ Sources catégorisées (météo, phyto, instituts, réglementation)
- ✅ Références précises (page PDF, fichier JSON, URL)

### 4. **Approche Agroécologique**
- ✅ Hiérarchie IPM respectée
- ✅ Méthode identifiée pour chaque action
- ✅ Chimique uniquement en dernier recours

### 5. **Transparence**
- ✅ Niveau de confiance global
- ✅ Limites de l'analyse explicites
- ✅ Fiabilité des données évaluée

---

## 📊 Structure JSON Complète

```json
{
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
        "justification": "Symptômes huileux + humidité >85%",
        "facteurs_favorables": [
          "Humidité élevée (>85%) depuis 3 jours",
          "Température optimale (18-22°C)",
          "Stade sensible (floraison)"
        ],
        "sources": [
          "Ephytia.inrae.fr - Fiche Mildiou",
          "meteorologie.json"
        ]
      },
      {
        "rang": 2,
        "nom": "Carence en magnésium",
        "probabilite": 0.20,
        "niveau_gravite": "modéré",
        "justification": "Décoloration internervaire",
        "facteurs_favorables": ["Sol sableux"],
        "sources": ["phytosanitaire_culture.json"]
      }
    ],
    
    "diagnostic_principal": {
      "nom": "Mildiou de la vigne",
      "probabilite": 0.70,
      "synthese": "Forte probabilité de mildiou"
    },
    
    "risques_evolution": {
      "sans_intervention": "Extension rapide (72h), perte 30-50%",
      "delai_critique": "24-48 heures",
      "conditions_aggravantes": ["Pluie annoncée dans 48h"]
    }
  },
  
  "recommandations": {
    "actions_urgentes": [
      {
        "priorite": 1,
        "action": "Isoler et surveiller les zones touchées",
        "justification": "Limiter la propagation des spores",
        "delai": "Immédiat (0-24h)",
        "methode": "Agroécologique - Observation",
        "cout_estime": "Faible",
        "sources": ["Guide IPM - INRAE", "Ecophytopic.fr"]
      },
      {
        "priorite": 2,
        "action": "Effeuillage zone de grappes",
        "justification": "Améliorer aération",
        "delai": "24-48h",
        "methode": "Agroécologique - Mécanique",
        "cout_estime": "Moyen",
        "sources": ["IFV - Techniques culturales"]
      }
    ],
    
    "actions_recommandees": [
      {
        "priorite": 3,
        "action": "Bouillie bordelaise si aggravation",
        "justification": "Protection curative",
        "delai": "48-72h si extension confirmée",
        "methode": "Dernier recours - Chimique raisonné",
        "cout_estime": "Élevé",
        "sources": [
          "Manuel IFT Avril 2018.pdf - p.42",
          "phytosanitaire_produits.json"
        ]
      }
    ],
    
    "surveillance_preventive": [
      {
        "action": "Monitoring quotidien nouvelles taches",
        "frequence": "2 fois/jour pendant 7 jours",
        "indicateurs": [
          "Nouvelles taches huileuses",
          "Extension zones touchées",
          "Duvet blanc (sporulation)"
        ],
        "methode": "Agroécologique - Observation",
        "sources": ["BSV - Protocole surveillance"]
      }
    ],
    
    "pratiques_preventives_futures": {
      "culturelles": [
        {
          "pratique": "Enherbement inter-rang",
          "benefice": "Réduction humidité au sol",
          "periode": "Automne prochain",
          "source": "DEPHY EXPE"
        }
      ],
      "mecaniques": [
        {
          "pratique": "Palissage aéré",
          "benefice": "Meilleure circulation d'air",
          "periode": "Printemps",
          "source": "Chambre Agriculture"
        }
      ],
      "biologiques": [
        {
          "pratique": "Purin d'ortie préventif",
          "benefice": "Renforcement défenses naturelles",
          "periode": "Avant floraison",
          "source": "ITAB - Guide biocontrôle"
        }
      ]
    }
  },
  
  "contexte": {
    "situation_meteorologique": {
      "resume_recent": "Humidité 85-90% + T° 18-22°C",
      "anomalies_detectees": [
        "Humidité +20% vs normale",
        "Pluies +15mm en 5 jours"
      ],
      "previsions_72h": "Pluie modérée attendue",
      "impact_risque": "Conditions optimales mildiou"
    },
    "historique_parcelle": {
      "dernier_traitement": "Soufre - il y a 15j",
      "episodes_similaires": ["Juin 2023 - Mildiou confirmé"]
    }
  },
  
  "sources_et_fiabilite": {
    "sources_utilisees": {
      "meteorologie": ["meteorologie.json", "Météo France"],
      "phytosanitaire": [
        "Ephytia.inrae.fr",
        "phytosanitaire_produits.json",
        "Manuel IFT Avril 2018.pdf"
      ],
      "instituts": ["INRAE", "IFV", "DRAAF", "Ecophytopic.fr"],
      "reglementation": ["products-autorises.json"]
    },
    "fiabilite_analyse": {
      "qualite_image": "Bonne (symptômes visibles)",
      "coherence_donnees": "Élevée",
      "completude_contexte": "Partielle",
      "niveau_confiance_final": 0.75
    },
    "limites_analyse": [
      "Analyse basée sur image unique",
      "Historique cultural incomplet"
    ]
  },
  
  "metadonnees": {
    "version_modele": "gpt-4o-mini",
    "date_analyse": "2025-01-17T23:44:00Z",
    "region": "Bordeaux",
    "culture": "Vigne",
    "use_case": "diagnostic_phytosanitaire"
  }
}
```

---

## 🎨 Avantages par Rapport à V1

| Aspect | V1 | V2 |
|--------|----|----|
| **Diagnostic** | Hypothèses simples | Hypothèses pondérées + rang + gravité |
| **Recommandations** | Par type (culturel/mécanique) | **Par urgence** (urgent/recommandé/surveillance) |
| **Sources** | Liste globale | **Par action** + catégorisées |
| **Actionnabilité** | Faible (générique) | **Forte** (délais + coûts + conditions) |
| **Agroécologie** | Implicite | **Explicite** (méthode identifiée) |
| **Transparence** | Niveau global | Global + **par hypothèse** + limites |

---

## 🔍 Détails des Sections

### **Section: diagnostic**

#### `hypotheses_diagnostiques[]`
- **rang**: Position dans l'ordre de probabilité (1 = plus probable)
- **probabilite**: Entre 0.0 et 1.0
- **niveau_gravite**: `"élevé"`, `"modéré"`, `"faible"`, `"indéterminé"`
- **facteurs_favorables**: Liste des conditions qui favorisent cette hypothèse

#### `diagnostic_principal`
Synthèse de l'hypothèse la plus probable pour affichage rapide.

#### `risques_evolution`
- **sans_intervention**: Que se passe-t-il si rien n'est fait?
- **delai_critique**: Temps avant aggravation critique
- **conditions_aggravantes**: Facteurs qui peuvent empirer la situation

---

### **Section: recommandations**

#### `actions_urgentes[]`
Actions à réaliser **immédiatement** (0-48h)
- **priorite**: 1-2
- **delai**: Format "0-24h", "24-48h"
- **methode**: Type d'approche (Agroécologique, Mécanique, Chimique, etc.)
- **cout_estime**: "Faible", "Moyen", "Élevé"

#### `actions_recommandees[]`
Actions à réaliser **à court/moyen terme** (48h-7j)
- **priorite**: 3-5

#### `surveillance_preventive[]`
Actions de **monitoring continu**
- **frequence**: "2 fois/jour", "Hebdomadaire", etc.
- **indicateurs**: Liste des signes à surveiller

#### `pratiques_preventives_futures`
Pratiques à mettre en place **saison prochaine**
- Groupées par type: culturelles, mécaniques, biologiques
- Chaque pratique a: pratique, bénéfice, période, source

---

### **Section: sources_et_fiabilite**

#### `sources_utilisees`
Sources catégorisées par type:
- **meteorologie**: Données météo
- **phytosanitaire**: Fiches maladies/ravageurs
- **instituts**: Organismes de recherche
- **reglementation**: Produits autorisés, IFT

#### `fiabilite_analyse`
- **qualite_image**: "Bonne", "Moyenne", "Faible", "Non évaluée"
- **coherence_donnees**: "Élevée", "Moyenne", "Faible"
- **completude_contexte**: "Complète", "Partielle", "Limitée"
- **niveau_confiance_final**: 0.0 à 1.0

#### `limites_analyse[]`
Liste explicite des limites de l'analyse

---

## 🛡️ Garanties de Validation

### **Validation Pydantic**
Tous les champs sont validés automatiquement:
- Probabilités bornées entre 0.0 et 1.0
- Valeurs par défaut pour tous les champs
- Types stricts (int, float, str, list)

### **Fallback Automatique**
En cas d'erreur, retour d'un objet valide avec:
- `niveau_confiance_global: 0.0`
- `limites_analyse: ["Erreur lors de l'analyse"]`
- Toutes les sections présentes (vides ou par défaut)

---

## 📱 Utilisation dans l'Application Cliente

### **Affichage du Diagnostic**
```javascript
// Afficher le diagnostic principal
const diagnostic = response.caption.diagnostic;
console.log(`Diagnostic: ${diagnostic.diagnostic_principal.nom}`);
console.log(`Confiance: ${diagnostic.diagnostic_principal.probabilite * 100}%`);

// Afficher toutes les hypothèses
diagnostic.hypotheses_diagnostiques.forEach(hyp => {
  console.log(`${hyp.rang}. ${hyp.nom} (${hyp.probabilite * 100}%)`);
});
```

### **Affichage des Actions Urgentes**
```javascript
const urgentes = response.caption.recommandations.actions_urgentes;
urgentes.forEach(action => {
  console.log(`[URGENT] ${action.action}`);
  console.log(`Délai: ${action.delai}`);
  console.log(`Source: ${action.sources.join(', ')}`);
});
```

### **Vérification de la Fiabilité**
```javascript
const fiabilite = response.caption.sources_et_fiabilite.fiabilite_analyse;
if (fiabilite.niveau_confiance_final < 0.5) {
  console.warn("⚠️ Analyse à faible confiance");
  console.log("Limites:", response.caption.sources_et_fiabilite.limites_analyse);
}
```

---

## ✅ Checklist de Validation

Avant d'utiliser la réponse, vérifier:

- [ ] `status === "ok"`
- [ ] `caption.diagnostic.niveau_confiance_global > 0`
- [ ] `caption.diagnostic.hypotheses_diagnostiques.length >= 1`
- [ ] Chaque action urgente a une `source`
- [ ] `caption.sources_et_fiabilite.limites_analyse` est consulté

---

## 🚀 Migration V1 → V2

### **Ancien format (V1)**
```json
{
  "niveau_confiance": 0.75,
  "hypotheses_probables": [...]
}
```

### **Nouveau format (V2)**
```json
{
  "diagnostic": {
    "niveau_confiance_global": 0.75,
    "hypotheses_diagnostiques": [...]
  }
}
```

### **Mapping des champs**

| V1 | V2 |
|----|-----|
| `niveau_confiance` | `diagnostic.niveau_confiance_global` |
| `phenologie_actuelle` | `diagnostic.stade_phenologique` |
| `hypotheses_probables` | `diagnostic.hypotheses_diagnostiques` |
| `pratiques_preventives` | `recommandations.pratiques_preventives_futures` |
| `sources_utilisees` | `sources_et_fiabilite.sources_utilisees` |

---

**Version:** 2.0  
**Date:** 2025-01-17  
**Auteur:** Équipe AGRIA  
**Compatibilité:** API AGRIA v1.0+
