# app/main.py
import os, uuid, logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv
import openai
from app.vector_store import VectorStoreManager
from app.rag import RAG
from app.schemas import APIResponseSchema
# from app.image_service import caption_image
caption_image = None 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
load_dotenv()

app = FastAPI(title="AgriSense Backend")

# Gestionnaire d'erreurs de validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"❌ Erreur de validation 422:")
    logging.error(f"   URL: {request.url}")
    logging.error(f"   Méthode: {request.method}")
    logging.error(f"   Erreurs: {exc.errors()}")
    logging.error(f"   Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": str(exc.body),
            "message": "Erreur de validation - Vérifiez les paramètres de la requête"
        }
    )

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/upload-image", response_model=APIResponseSchema)
async def upload_image(
    use_case: str = Form(...),
    file: UploadFile = File(...),
    question: str | None = Form(None)
):
    """
    Upload et analyse d'une image agricole.
    Retourne un JSON strictement formaté selon le schéma APIResponseSchema.
    """
    logging.info(f"📥 Requête reçue - use_case: {use_case}, file: {file.filename if file else 'None'}, question: {question}")
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

        # --- Appel du modèle avec parsing robuste ---
        analysis = rag.ask(
            use_case=use_case,
            question=question,
            image_path=path
        )
        
        # L'objet 'answer' est déjà un dict validé par Pydantic
        caption_dict = analysis["answer"]
        
        # Conversion en string JSON pour l'embedding
        caption_str = str(caption_dict)

        # --- Ajout de l'embed dans Chroma ---
        try:
            emb = rag.embed_text(caption_str)
            vm.add_documents_chroma(
                use_case,
                [file_id],
                [{"source": file.filename, "path": path}],
                [caption_str],
                [emb]
            )
        except Exception as emb_error:
            logging.warning(f"Erreur lors de l'embedding: {emb_error}")

        # --- Validation finale avec Pydantic ---
        response = APIResponseSchema(
            status="ok",
            caption=caption_dict,
            file_id=file_id
        )
        
        return response

    except Exception as e:
        logging.error(f"Erreur dans /upload-image: {e}")
        # Retourner une réponse de fallback valide même en cas d'erreur
        from app.schemas import AnalyseAgricoleSchema
        fallback = AnalyseAgricoleSchema(
            niveau_confiance=0.0,
            phenologie_actuelle=f"Erreur lors de l'analyse: {str(e)}",
            sources_utilisees=["Système de fallback"]
        )
        return APIResponseSchema(
            status="error",
            caption=fallback,
            file_id=None
        )

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
