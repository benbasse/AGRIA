# app/main.py
import os, uuid, logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from app.vector_store import VectorStoreManager
from app.rag import RAG
import uuid, os, logging
from fastapi import HTTPException
from dotenv import load_dotenv
import openai
# from app.image_service import caption_image
caption_image = None 

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = FastAPI(title="AgriSense Backend")

config = {
    "CHROMA_PERSIST_DIR": os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
}
vm = VectorStoreManager(config)
rag = RAG(vm)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Hello from AgriSense API 🚀"}


@app.post("/upload-image")
async def upload_image(
    use_case: str = Form(...),
    file: UploadFile = File(...),
    question: str | None = Form(None)  # <-- obligatoirement ajouté
):
    try:
        # --- Sauvegarde du fichier ---
        file_id = str(uuid.uuid4())
        path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
        with open(path, "wb") as f:
            f.write(await file.read())

        # --- Question dynamique si l'utilisateur n'en fournit pas ---
        if not question:
            question = (
                f"Analyse cette image agricole fournie ({file.filename}) pour le use_case '{use_case}'. "
                "Décris le stade de croissance, les éventuels symptômes, anomalies, parasites, maladies, "
                "conditions du sol et propose des recommandations agroécologiques préventives. "
                "Fournis les résultats sous format JSON structuré comme défini dans le prompt expert."
            )

        # --- Appel du modèle ---
        analysis = rag.ask(
            use_case=use_case,
            question=question,
            image_path=path
        )
        caption = analysis["answer"]

        # --- Ajout de l'embed dans Chroma ---
        emb = rag.embed_text(caption)
        vm.add_documents_chroma(
            use_case,
            [file_id],
            [{"source": file.filename, "path": path}],
            [caption],
            [emb]
        )

        return {"status": "ok", "caption": caption, "file_id": file_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask(use_case: str = Form(...), question: str = Form(...)):
    res = rag.ask(use_case, question)
    return JSONResponse(res)

@app.post("/upload-audio")
async def upload_audio( 
    use_case: str = Form(...),
    file: UploadFile = File(...),
    question: str | None = Form(None)
):
    try:
        file_id = str(uuid.uuid4())
        audio_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
        with open(audio_path, "wb") as f:
            f.write(await file.read())

        # --- Étape 1: Transcription de l'audio ---
        # with open(audio_path, "rb") as audio_file:
        #     transcription = openai.Audio.transcriptions.create(
        #         model="whisper-1",
        #         file=audio_file,
        #         response_format="text"
        #     )

        # user_text = transcription.strip()

        with open(audio_path, "rb") as audio_file:
            transcription = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        user_text = transcription.text  # Récupération du texte transcrit
        print(f"🔊 Transcription reçue: {user_text}")

        # --- Étape 2: Définir la question ---
        if not question:
            question = user_text  # la voix devient la question du user

        # --- Étape 3: Appel du modèle RAG ---
        response = rag.ask(use_case=use_case, question=question)

        # --- Étape 4: Génération de la réponse audio ---               
        tts = openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=response["answer"]
        )
        with open(f"{file_id}_response.mp3", "wb") as f:
            f.write(tts.content)

        # --- Étape 5: Retour de la réponse ---
        return {
            "status": "ok",
            "user_text": user_text,
            "answer": response["answer"],
            "audio_response_path": f"{file_id}_response.mp3"
        }

        # return JSONResponse({
        #     "status": "ok",
        #     "user_text": user_text,
        #     "answer": response["answer"]
        # })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
