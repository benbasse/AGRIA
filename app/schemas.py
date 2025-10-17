# app/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


# ===== DIAGNOSTIC =====

class HypotheseDiagnosticSchema(BaseModel):
    """Hypothèse de diagnostic avec probabilité et gravité"""
    rang: int = Field(default=1, ge=1)
    nom: str = Field(default="Analyse en cours")
    probabilite: float = Field(default=0.0, ge=0.0, le=1.0)
    niveau_gravite: str = Field(default="indéterminé")  # élevé, modéré, faible
    justification: str = Field(default="Données insuffisantes")
    facteurs_favorables: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)

    @field_validator('probabilite')
    @classmethod
    def validate_probabilite(cls, v):
        if not 0.0 <= v <= 1.0:
            return 0.0
        return v


class DiagnosticPrincipalSchema(BaseModel):
    """Diagnostic principal (hypothèse la plus probable)"""
    nom: str = Field(default="Indéterminé")
    probabilite: float = Field(default=0.0, ge=0.0, le=1.0)
    synthese: str = Field(default="Analyse en cours")


class RisquesEvolutionSchema(BaseModel):
    """Risques d'évolution si pas d'intervention"""
    sans_intervention: str = Field(default="Non évalué")
    delai_critique: str = Field(default="Non déterminé")
    conditions_aggravantes: List[str] = Field(default_factory=list)


class DiagnosticSchema(BaseModel):
    """Section diagnostic complète"""
    niveau_confiance_global: float = Field(default=0.0, ge=0.0, le=1.0)
    stade_phenologique: str = Field(default="Non déterminé")
    date_analyse: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    hypotheses_diagnostiques: List[HypotheseDiagnosticSchema] = Field(default_factory=list)
    diagnostic_principal: DiagnosticPrincipalSchema = Field(default_factory=DiagnosticPrincipalSchema)
    risques_evolution: RisquesEvolutionSchema = Field(default_factory=RisquesEvolutionSchema)

    @field_validator('niveau_confiance_global')
    @classmethod
    def validate_confiance(cls, v):
        if not 0.0 <= v <= 1.0:
            return 0.0
        return v


# ===== RECOMMANDATIONS =====

class ActionSchema(BaseModel):
    """Schéma pour une action recommandée"""
    priorite: int = Field(default=1, ge=1)
    action: str = Field(default="")
    justification: str = Field(default="")
    delai: str = Field(default="")
    methode: str = Field(default="")  # Agroécologique, Mécanique, Chimique, etc.
    cout_estime: str = Field(default="Non évalué")  # Faible, Moyen, Élevé
    sources: List[str] = Field(default_factory=list)


class ActionChimiqueSchema(ActionSchema):
    """Action chimique avec informations supplémentaires"""
    dose: Optional[str] = Field(default=None)
    conditions_application: List[str] = Field(default_factory=list)


class ActionSurveillanceSchema(BaseModel):
    """Action de surveillance préventive"""
    action: str = Field(default="")
    frequence: str = Field(default="")
    indicateurs: List[str] = Field(default_factory=list)
    methode: str = Field(default="")
    sources: List[str] = Field(default_factory=list)


class PratiqueFutureSchema(BaseModel):
    """Pratique préventive pour le futur"""
    pratique: str = Field(default="")
    benefice: str = Field(default="")
    periode: str = Field(default="")
    source: str = Field(default="")


class PratiquesPreventivesFuturesSchema(BaseModel):
    """Pratiques préventives à mettre en place"""
    culturelles: List[PratiqueFutureSchema] = Field(default_factory=list)
    mecaniques: List[PratiqueFutureSchema] = Field(default_factory=list)
    biologiques: List[PratiqueFutureSchema] = Field(default_factory=list)


class RecommandationsSchema(BaseModel):
    """Section recommandations complète"""
    actions_urgentes: List[ActionSchema] = Field(default_factory=list)
    actions_recommandees: List[ActionSchema] = Field(default_factory=list)
    surveillance_preventive: List[ActionSurveillanceSchema] = Field(default_factory=list)
    pratiques_preventives_futures: PratiquesPreventivesFuturesSchema = Field(default_factory=PratiquesPreventivesFuturesSchema)


# ===== CONTEXTE =====

class SituationMeteorologiqueSchema(BaseModel):
    """Situation météorologique détaillée"""
    resume_recent: str = Field(default="Données météorologiques non disponibles")
    anomalies_detectees: List[str] = Field(default_factory=list)
    previsions_72h: str = Field(default="Non disponible")
    impact_risque: str = Field(default="Non évalué")


class HistoriqueParcelleSchema(BaseModel):
    """Historique de la parcelle"""
    dernier_traitement: str = Field(default="Non renseigné")
    episodes_similaires: List[str] = Field(default_factory=list)


class ContexteSchema(BaseModel):
    """Section contexte"""
    situation_meteorologique: SituationMeteorologiqueSchema = Field(default_factory=SituationMeteorologiqueSchema)
    historique_parcelle: HistoriqueParcelleSchema = Field(default_factory=HistoriqueParcelleSchema)


# ===== SOURCES ET FIABILITÉ =====

class SourcesUtiliseesSchema(BaseModel):
    """Sources utilisées par catégorie"""
    meteorologie: List[str] = Field(default_factory=list)
    phytosanitaire: List[str] = Field(default_factory=list)
    instituts: List[str] = Field(default_factory=list)
    reglementation: List[str] = Field(default_factory=list)


class FiabiliteAnalyseSchema(BaseModel):
    """Fiabilité de l'analyse"""
    qualite_image: str = Field(default="Non évaluée")
    coherence_donnees: str = Field(default="Non évaluée")
    completude_contexte: str = Field(default="Non évaluée")
    niveau_confiance_final: float = Field(default=0.0, ge=0.0, le=1.0)


class SourcesEtFiabiliteSchema(BaseModel):
    """Section sources et fiabilité"""
    sources_utilisees: SourcesUtiliseesSchema = Field(default_factory=SourcesUtiliseesSchema)
    fiabilite_analyse: FiabiliteAnalyseSchema = Field(default_factory=FiabiliteAnalyseSchema)
    limites_analyse: List[str] = Field(default_factory=list)


# ===== MÉTADONNÉES =====

class MetadonneesSchema(BaseModel):
    """Métadonnées de l'analyse"""
    version_modele: str = Field(default="gpt-4o-mini")
    date_analyse: str = Field(default_factory=lambda: datetime.now().isoformat())
    region: str = Field(default="Non spécifiée")
    culture: str = Field(default="Non spécifiée")
    use_case: str = Field(default="diagnostic_phytosanitaire")


# ===== SCHÉMA PRINCIPAL =====

class AnalyseAgricoleSchema(BaseModel):
    """Schéma principal pour l'analyse agricole complète - Structure améliorée"""
    diagnostic: DiagnosticSchema = Field(default_factory=DiagnosticSchema)
    recommandations: RecommandationsSchema = Field(default_factory=RecommandationsSchema)
    contexte: ContexteSchema = Field(default_factory=ContexteSchema)
    sources_et_fiabilite: SourcesEtFiabiliteSchema = Field(default_factory=SourcesEtFiabiliteSchema)
    # metadonnees: MetadonneesSchema = Field(default_factory=MetadonneesSchema)  # Supprimé

    class Config:
        """Configuration Pydantic"""
        json_schema_extra = {
            "example": {
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
                            "sources": ["Ephytia.inrae.fr"]
                        }
                    ],
                    "diagnostic_principal": {
                        "nom": "Mildiou de la vigne",
                        "probabilite": 0.70,
                        "synthese": "Forte probabilité de mildiou"
                    },
                    "risques_evolution": {
                        "sans_intervention": "Extension rapide",
                        "delai_critique": "24-48h",
                        "conditions_aggravantes": ["Pluie annoncée"]
                    }
                },
                "recommandations": {
                    "actions_urgentes": [
                        {
                            "priorite": 1,
                            "action": "Isoler les zones touchées",
                            "justification": "Limiter propagation",
                            "delai": "0-24h",
                            "methode": "Agroécologique",
                            "cout_estime": "Faible",
                            "sources": ["Guide IPM - INRAE"]
                        }
                    ],
                    "actions_recommandees": [],
                    "surveillance_preventive": [],
                    "pratiques_preventives_futures": {
                        "culturelles": [],
                        "mecaniques": [],
                        "biologiques": []
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
                        "instituts": ["INRAE"],
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
            }
        }


class APIResponseSchema(BaseModel):
    """Schéma pour la réponse API complète"""
    status: str = Field(default="ok")
    caption: AnalyseAgricoleSchema
    file_id: Optional[str] = Field(default=None)

    class Config:
        """Configuration Pydantic"""
        json_schema_extra = {
            "example": {
                "status": "ok",
                "caption": AnalyseAgricoleSchema.Config.json_schema_extra["example"],
                "file_id": "uuid-1234-5678"
            }
        }
