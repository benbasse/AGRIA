"""
Script de test pour vérifier l'intégration des bases de connaissances
dans le système RAG.
"""
import os
import sys
from dotenv import load_dotenv

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.vector_store import VectorStoreManager
from app.rag import RAG

load_dotenv()

def test_knowledge_base_loading():
    """Test le chargement des bases de connaissances"""
    print("=" * 60)
    print("TEST: Chargement des bases de connaissances")
    print("=" * 60)
    
    # Configuration
    config = {
        "CHROMA_PERSIST_DIR": os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    }
    
    # Initialiser le RAG
    vm = VectorStoreManager(config)
    rag = RAG(vm)
    
    # Vérifier que les bases sont chargées
    print(f"\n✅ Knowledge Base chargée: {len(rag.knowledge_base)} caractères")
    print(f"✅ Role Base chargée: {len(rag.role_base)} caractères")
    
    # Afficher un extrait de chaque base
    if rag.knowledge_base:
        print("\n📚 Extrait de Knowledge Base (100 premiers caractères):")
        print(rag.knowledge_base[:100] + "...")
    else:
        print("\n⚠️ Knowledge Base vide!")
    
    if rag.role_base:
        print("\n👤 Extrait de Role Base (100 premiers caractères):")
        print(rag.role_base[:100] + "...")
    else:
        print("\n⚠️ Role Base vide!")
    
    return rag

def test_simple_question(rag):
    """Test une question simple pour voir si les bases sont utilisées"""
    print("\n" + "=" * 60)
    print("TEST: Question simple avec bases de connaissances")
    print("=" * 60)
    
    question = "Quels sont les symptômes du mildiou sur la tomate?"
    use_case = "tomate"
    
    print(f"\n❓ Question: {question}")
    print(f"📦 Use case: {use_case}")
    
    try:
        response = rag.ask_simple(use_case, question)
        print(f"\n✅ Réponse reçue:")
        print("-" * 60)
        print(response.get("answer", "Pas de réponse"))
        print("-" * 60)
        
        # Vérifier si la réponse contient des éléments de la knowledge base
        answer = response.get("answer", "")
        keywords = ["mildiou", "Phytophthora", "taches", "humide", "feuilles"]
        found_keywords = [kw for kw in keywords if kw.lower() in answer.lower()]
        
        print(f"\n🔍 Mots-clés trouvés dans la réponse: {found_keywords}")
        
        if len(found_keywords) >= 2:
            print("✅ La base de connaissances semble être utilisée!")
        else:
            print("⚠️ La base de connaissances ne semble pas être utilisée efficacement")
            
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Fonction principale de test"""
    print("\n🚀 Démarrage des tests d'intégration des bases de connaissances\n")
    
    try:
        # Test 1: Chargement des bases
        rag = test_knowledge_base_loading()
        
        # Test 2: Question simple
        test_simple_question(rag)
        
        print("\n" + "=" * 60)
        print("✅ Tests terminés avec succès!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
