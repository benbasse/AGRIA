import os
import json
import hashlib
import textwrap
from PyPDF2 import PdfReader
from docx import Document
from app.vector_store import VectorStoreManager
from app.rag import RAG

# === CONFIG ===
CHROMA_DIR = "./chroma_db"
DATA_DIR = "./data"
MAX_CHUNK_CHARS = 2000  # Taille max par chunk pour embeddings

vm = VectorStoreManager({"CHROMA_PERSIST_DIR": CHROMA_DIR})
rag = RAG(vm)

# === UTILITAIRES ===
def chunk_text(text, max_length=MAX_CHUNK_CHARS):
    return textwrap.wrap(text, max_length)

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_text_from_pdf(path):
    text = ""
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        print(f"Erreur lecture PDF {path}: {e}")
    return text

def extract_text_from_docx(path):
    text = ""
    try:
        doc = Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        print(f"Erreur lecture DOCX {path}: {e}")
    return text

def extract_text_from_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur lecture JSON {path}: {e}")
        return ""

def extract_text_from_txt(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Erreur lecture TXT {path}: {e}")
        return ""

def read_file_content(path):
    ext = path.split(".")[-1].lower()
    if ext == "pdf":
        return extract_text_from_pdf(path), "pdf_sources"
    elif ext == "docx":
        return extract_text_from_docx(path), "docx_sources"
    elif ext == "json":
        return extract_text_from_json(path), "json_sources"
    elif ext == "txt":
        return extract_text_from_txt(path), "txt_sources"
    else:
        return "", None

# === VERIFICATION D'EXISTANCE DU FICHIER ===
def already_ingested(collection_name, file_hash_value):
    collection = vm.client.get_or_create_collection(collection_name)
    try:
        res = collection.query(
            query_embeddings=[[0]*rag.embed_text("test").__len__()],  # embedding dummy de la bonne dimension
            n_results=1,
            include=["metadatas"]
        )
        for meta in res["metadatas"][0]:
            if meta.get("hash") == file_hash_value:
                return True
    except Exception as e:
        # si dimension mismatch, on ignore et créons une nouvelle collection
        return False
    return False

# === AJOUT DANS CHROMA AVEC VERIF DIMENSION ===
def add_to_chroma(collection_name, text, source_path):
    hash_value = file_hash(source_path)

    # Vérifie si le fichier est déjà ingéré
    if already_ingested(collection_name, hash_value):
        print(f"⚠️ {source_path} déjà ingéré, skipped")
        return

    # Vérifie la dimension de la collection
    collection = vm.client.get_or_create_collection(collection_name)
    try:
        existing = collection.get()
        if "embedding_function" in existing and existing["embedding_function"] is not None:
            dim_expected = existing["embedding_function"]["dimension"]
        else:
            dim_expected = rag.embed_text("test").__len__()
    except Exception:
        dim_expected = rag.embed_text("test").__len__()

    # Compare la dimension actuelle vs embeddings du modèle
    current_dim = rag.embed_text("test").__len__()
    if current_dim != dim_expected:
        # Crée une nouvelle collection pour éviter le conflit
        collection_name = f"{collection_name}_v2"
        print(f"⚠️ Dimension mismatch détectée, création de la collection {collection_name}")
        collection = vm.client.get_or_create_collection(collection_name)

    chunks = chunk_text(text, MAX_CHUNK_CHARS)
    print(f"📦 {len(chunks)} chunks créés pour {source_path}")

    for i, chunk in enumerate(chunks):
        try:
            embedding = rag.embed_text(chunk)
            vm.add_documents_chroma(
                collection_name,
                ids=[f"{os.path.basename(source_path)}_{i}"],
                documents=[chunk],
                metadatas=[{
                    "source": os.path.basename(source_path),
                    "chunk_index": i,
                    "hash": hash_value
                }],
                embeddings=[embedding]
            )
        except Exception as e:
            print(f"❌ Erreur sur {source_path} chunk {i}: {e}")

# === PIPELINE PRINCIPAL ===
def process_directory():
    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            path = os.path.join(root, file)
            text, collection = read_file_content(path)
            if text.strip() and collection:
                print(f"➡ Traitement de {file} dans collection {collection}")
                add_to_chroma(collection, text, path)
            else:
                print(f"⚠️ Aucun texte extrait ou format non supporté pour {file}")

if __name__ == "__main__":
    process_directory()
    print("✅ Ingestion terminée !")
