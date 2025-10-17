# test_json_validation.py
"""
Script de test pour valider le système de parsing et validation JSON robuste.
"""
import json
from app.schemas import AnalyseAgricoleSchema, APIResponseSchema
from pydantic import ValidationError


def test_valid_json():
    """Test avec un JSON valide complet"""
    print("\n=== Test 1: JSON valide complet ===")
    
    valid_data = {
        "niveau_confiance": 0.85,
        "phenologie_actuelle": "Floraison",
        "situation_meteorologique": {
            "resume_recent": "Temps humide et chaud",
            "anomalies_detectees": ["Humidité élevée", "Température supérieure à la normale"],
            "risques_associes": ["Mildiou", "Oïdium"]
        },
        "analyse_historique": {
            "periode_comparee": "30_jours",
            "ecarts_moyens": {
                "temperature": "+2.5°C",
                "humidite": "+15%",
                "precipitations": "+25mm"
            },
            "episodes_similaires": ["Juin 2023", "Mai 2022"]
        },
        "hypotheses_probables": [
            {
                "nom": "Mildiou de la vigne",
                "probabilite": 0.72,
                "justification": "Symptômes huileux sur feuilles + humidité élevée + stade floraison",
                "sources": ["Ephytia.inrae.fr", "meteorologie.json"]
            },
            {
                "nom": "Carence magnésienne",
                "probabilite": 0.18,
                "justification": "Décoloration internervaire, sol sableux",
                "sources": ["phytosanitaire_culture.json"]
            }
        ],
        "pratiques_preventives": {
            "culturelles": ["Rotation des cultures", "Espacement des plants"],
            "mecaniques": ["Désherbage manuel", "Taille aérée"],
            "biologiques": ["Purin d'ortie", "Auxiliaires (coccinelles)"],
            "chimiques_en_dernier_recours": []
        },
        "risques_abiotiques": ["Stress hydrique", "Gel tardif"],
        "sources_utilisees": [
            "meteorologie.json",
            "phytosanitaire_produits.json",
            "Ephytia.inrae.fr"
        ]
    }
    
    try:
        schema = AnalyseAgricoleSchema(**valid_data)
        print("✅ Validation réussie!")
        print(f"Niveau de confiance: {schema.niveau_confiance}")
        print(f"Phénologie: {schema.phenologie_actuelle}")
        print(f"Nombre d'hypothèses: {len(schema.hypotheses_probables)}")
        return True
    except ValidationError as e:
        print(f"❌ Erreur de validation: {e}")
        return False


def test_partial_json():
    """Test avec un JSON partiel (valeurs par défaut)"""
    print("\n=== Test 2: JSON partiel avec valeurs par défaut ===")
    
    partial_data = {
        "niveau_confiance": 0.3,
        "phenologie_actuelle": "Stade indéterminé"
    }
    
    try:
        schema = AnalyseAgricoleSchema(**partial_data)
        print("✅ Validation réussie avec valeurs par défaut!")
        print(f"Niveau de confiance: {schema.niveau_confiance}")
        print(f"Hypothèses (défaut): {schema.hypotheses_probables}")
        print(f"Risques abiotiques (défaut): {schema.risques_abiotiques}")
        return True
    except ValidationError as e:
        print(f"❌ Erreur de validation: {e}")
        return False


def test_invalid_probability():
    """Test avec une probabilité invalide (> 1.0)"""
    print("\n=== Test 3: Probabilité invalide (auto-correction) ===")
    
    invalid_data = {
        "niveau_confiance": 1.5,  # Invalide, sera corrigé à 0.0
        "phenologie_actuelle": "Test",
        "hypotheses_probables": [
            {
                "nom": "Test",
                "probabilite": 2.0,  # Invalide, sera corrigé à 0.0
                "justification": "Test",
                "sources": []
            }
        ]
    }
    
    try:
        schema = AnalyseAgricoleSchema(**invalid_data)
        print("✅ Validation avec auto-correction!")
        print(f"Niveau de confiance corrigé: {schema.niveau_confiance}")
        print(f"Probabilité hypothèse corrigée: {schema.hypotheses_probables[0].probabilite}")
        return True
    except ValidationError as e:
        print(f"❌ Erreur de validation: {e}")
        return False


def test_api_response():
    """Test du schéma de réponse API complet"""
    print("\n=== Test 4: Schéma de réponse API complet ===")
    
    api_data = {
        "status": "ok",
        "caption": {
            "niveau_confiance": 0.75,
            "phenologie_actuelle": "Nouaison",
            "situation_meteorologique": {
                "resume_recent": "Conditions favorables",
                "anomalies_detectees": [],
                "risques_associes": []
            },
            "analyse_historique": {
                "periode_comparee": "30_jours",
                "ecarts_moyens": {
                    "temperature": "Normal",
                    "humidite": "Normal",
                    "precipitations": "Normal"
                },
                "episodes_similaires": []
            },
            "hypotheses_probables": [],
            "pratiques_preventives": {
                "culturelles": ["Surveillance régulière"],
                "mecaniques": [],
                "biologiques": [],
                "chimiques_en_dernier_recours": []
            },
            "risques_abiotiques": [],
            "sources_utilisees": ["meteorologie.json"]
        },
        "file_id": "test-uuid-1234"
    }
    
    try:
        response = APIResponseSchema(**api_data)
        print("✅ Validation du schéma API réussie!")
        print(f"Status: {response.status}")
        print(f"File ID: {response.file_id}")
        print(f"Caption niveau confiance: {response.caption.niveau_confiance}")
        
        # Test de sérialisation JSON
        json_output = response.model_dump_json(indent=2)
        print("\n📄 JSON sérialisé (extrait):")
        print(json_output[:200] + "...")
        return True
    except ValidationError as e:
        print(f"❌ Erreur de validation: {e}")
        return False


def test_empty_json():
    """Test avec un JSON vide (toutes valeurs par défaut)"""
    print("\n=== Test 5: JSON vide (fallback complet) ===")
    
    try:
        schema = AnalyseAgricoleSchema()
        print("✅ Création du schéma par défaut réussie!")
        print(f"Niveau de confiance par défaut: {schema.niveau_confiance}")
        print(f"Phénologie par défaut: {schema.phenologie_actuelle}")
        print(f"Météo par défaut: {schema.situation_meteorologique.resume_recent}")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Exécute tous les tests"""
    print("=" * 60)
    print("🧪 TESTS DE VALIDATION JSON ROBUSTE")
    print("=" * 60)
    
    tests = [
        test_valid_json,
        test_partial_json,
        test_invalid_probability,
        test_api_response,
        test_empty_json
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSULTATS: {sum(results)}/{len(results)} tests réussis")
    print("=" * 60)
    
    if all(results):
        print("✅ Tous les tests sont passés avec succès!")
        print("\n🔒 Le système de validation JSON est robuste et prêt pour la production.")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les schémas Pydantic.")


if __name__ == "__main__":
    main()
