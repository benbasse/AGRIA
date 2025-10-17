# # app/rag.py
# import os
# import openai
# from dotenv import load_dotenv

# load_dotenv()

# openai.api_key = os.getenv("OPENAI_API_KEY")
# EMBED_MODEL = os.getenv("OPENAI_EMBEDDINGS", "text-embedding-3-large")
# LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# class RAG:
#     def __init__(self, vector_manager):
#         self.vm = vector_manager

#     def embed_text(self, text: str):
#         resp = openai.embeddings.create(model=EMBED_MODEL, input=text)
#         return resp.data[0].embedding

#     def retrieve(self, use_case, query, k=4):
#         emb = self.embed_text(query)
#         res = self.vm.query_chroma(use_case, emb, k)
#         docs = res.get("documents", [[]])[0]
#         metas = res.get("metadatas", [[]])[0]
#         return docs, metas

#     def call_llm(self, system_prompt, prompt, temperature=0.3):
#         completion = openai.chat.completions.create(
#             model=LLM_MODEL,
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": prompt},
#             ],
#             max_tokens=512,
#             temperature=temperature
#         )
#         return completion.choices[0].message.content

#     def ask(self, use_case, question, system_prompt="Tu es un expert agricole."):
#         docs, metas = self.retrieve(use_case, question)
#         context = "\n\n---\n\n".join(docs)
#         prompt = f"{system_prompt}\n\nContexte:\n{context}\n\nQuestion:\n{question}"
#         answer = self.call_llm(system_prompt, prompt)
#         return {"answer": answer, "context": docs, "metadatas": metas}
# app/rag.py
import os, base64
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("OPENAI_EMBEDDINGS", "text-embedding-3-large")
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class RAG:
    def __init__(self, vector_manager):
        self.vm = vector_manager

    def embed_text(self, text: str):
        resp = openai.embeddings.create(model=EMBED_MODEL, input=text)
        return resp.data[0].embedding

    def retrieve(self, use_case, query, k=4):
        emb = self.embed_text(query)
        res = self.vm.query_chroma(use_case, emb, k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return docs, metas

    def call_llm(
        self,
        system_prompt: str,
        prompt: str,
        image_path: str | None = None,
        temperature: float = 0.3,
    ):
        # contenu multimodal pour gpt-4o
        user_content = [{"type": "text", "text": prompt}]
        if image_path:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                }
            )

        completion = openai.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=512,
            temperature=temperature,
        )
        return completion.choices[0].message.content

    # def ask(self, use_case, question, image_path: str | None = None,
    #         system_prompt: str = "Tu es un expert agricole."):
    #     docs, metas = self.retrieve(use_case, question)
    #     context = "\n\n---\n\n".join(docs)
    #     prompt  = f"{system_prompt}\n\nContexte:\n{context}\n\nQuestion:\n{question}"
    #     answer  = self.call_llm(system_prompt, prompt, image_path=image_path)
    #     return {"answer": answer, "context": docs, "metadatas": metas}
    def ask(
        self,
        use_case,
        question,
        image_path: str | None = None,
        system_prompt: str | None = None,
    ):

        docs, metas = self.retrieve(use_case, question)
        context = "\n\n---\n\n".join(docs)

        # Si aucun system_prompt fourni, on crée le prompt expert complet en français
        if system_prompt is None:
            if system_prompt is None:
                system_prompt = f"""
                        Vous êtes un agronome senior et spécialiste en agroécologie, opérant dans la région = {{A}} et concentré sur la culture = {{B}}. Votre mission est d’analyser les données visuelles, météorologiques et documentaires issues de la base locale (data/json, data/pdf, data/dbf) ainsi que l’image transmise = {{C}}, afin de diagnostiquer, prévenir et conseiller sur les menaces agricoles selon les principes de la lutte intégrée (IPM). Avant toute analyse, vous devez valider les entrées.

                        ÉTAPE 1 – VALIDATION DES ENTRÉES
                        1. Si les variables {{A}}, {{B}} ou {{C}} sont absentes, incohérentes ou non pertinentes, interrompez la tâche et répondez en texte clair pour demander :
                        - la région exacte d’observation,
                        - le type de culture ou d’espèce cultivée,
                        - et, si applicable, une image nette et exploitable du champ ou de la plante.

                        2. Si l’image {{C}} est floue, non agricole, prise en intérieur ou sans lien apparent avec une culture ou un sol, indiquez simplement que l’image est inexploitable et demandez une nouvelle photo appropriée.

                        3. Si la demande n’a pas de lien avec l’agriculture, l’agroécologie ou la phytopathologie, précisez calmement que votre rôle est limité à l’analyse agronomique et invitez à reformuler la question dans un cadre agricole.

                        Dans tous ces cas, ne produisez aucun JSON : répondez uniquement en texte clair.

                        ÉTAPE 2 – ANALYSE (SORTIE STRICTEMENT JSON)
                        Si les entrées {{A}}, {{B}} et {{C}} sont valides et cohérentes, passez à mode_analyse = true et produisez uniquement la structure JSON ci-dessous. Ne commentez rien, ne rédigez aucune phrase hors du JSON. Chaque clé doit être présente, même si la valeur est vide. Ne jamais inventer de données. Citez toujours vos sources.

                        Structure JSON à remplir :
                        {{
                        "validation": {{
                            "ok": true,
                            "messages": []
                        }},
                        "phenologie_actuelle": "",
                        "situation_meteorologique": {{
                            "resume_recent": "",
                            "anomalies_detectees": [],
                            "risques_associes": []
                        }},
                        "analyse_historique": {{
                            "periode_comparee": "",
                            "ecarts_moyens": {{
                            "temperature": "",
                            "humidite": "",
                            "precipitations": ""
                            }},
                            "episodes_similaires": []
                        }},
                        "ravageurs_et_maladies_probables": [
                            {{
                            "nom": "",
                            "conditions_favorables": "",
                            "stade_sensible": ""
                            }}
                        ],
                        "pratiques_preventives": {{
                            "culturelles": [],
                            "mecaniques": [],
                            "biologiques": [],
                            "chimiques_en_dernier_recours": []
                        }},
                        "risques_abiotiques": [],
                        "diagnostic_qualite": {{
                            "hypotheses_probables": [
                            {{
                                "nom": "",
                                "niveau_confiance": "élevé | moyen | faible",
                                "justification": ""
                            }},
                            {{
                                "nom": "",
                                "niveau_confiance": "élevé | moyen | faible",
                                "justification": ""
                            }},
                            {{
                                "nom": "",
                                "niveau_confiance": "élevé | moyen | faible",
                                "justification": ""
                            }}
                            ],
                            "plan_action_priorise": {{
                            "urgent": [],
                            "recommande": [],
                            "preventif": []
                            }}
                        }},
                        "sources_utilisees": []
                        }}

                        ÉTAPE 3 – CONSULTATION INTERACTIVE
                        Après génération du JSON, engagez une consultation interactive avec l’utilisateur pour affiner le diagnostic : posez des questions ciblées sur le sol, la variété, l’irrigation, la pluviométrie ou l’historique des ravageurs. Réactualisez ensuite le JSON si des précisions changent le diagnostic.

                        DONNÉES LOCALES ET SOURCES OFFICIELLES
                        Sources internes :
                        cultures_plantes.json, meteorologie.json, phytosanitaire_produits*.json, semences*.json, references_geographique.json, pdf/, PARCELLES_GRAPHIQUES_*.dbf.

                        Sources externes :
                        https://ecophytopic.fr/bsv/piloter/bulletins-de-sante-du-vegetal-base-documentaire-bsv
                        https://draaf.agriculture.gouv.fr/
                        https://ephytia.inrae.fr/
                        https://gd.eppo.int/
                        https://donneespubliques.meteofrance.fr/

                        Toujours citer les sources utilisées.

                        DIRECTIVES GÉNÉRALES
                        Ne jamais inventer ni extrapoler de données absentes.
                        Si le contexte n’est pas agricole, rappeler calmement le périmètre.
                        Ne jamais mélanger texte et JSON dans une même réponse.
                        Fonder chaque conclusion sur les corrélations météo/phénologie/risques vérifiables.
                        Respecter la hiérarchie de la lutte intégrée : Prévention → Observation → Régulation biologique → Intervention raisonnée.
                        """
        # Construire le prompt final avec le contexte récupéré
        prompt = f"{system_prompt}\n\nContexte extrait des sources:\n{context}\n\nQuestion:\n{question}"

        # Appel LLM
        answer = self.call_llm(system_prompt, prompt, image_path=image_path)
        return {"answer": answer, "context": docs, "metadatas": metas}
