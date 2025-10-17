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
LLM_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class RAG:
    def __init__(self, vector_manager):
        self.vm = vector_manager

    def embed_text(self, text: str):
        resp = openai.embeddings.create(model=EMBED_MODEL, input=text)
        return resp.data[0].embedding

    def retrieve(self, use_case, query, k=4):
        emb = self.embed_text(query)
        res = self.vm.query_chroma(use_case, emb, k)
        docs  = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return docs, metas

    def call_llm(self, system_prompt: str, prompt: str, image_path: str | None = None, temperature: float = 0.3):
        # contenu multimodal pour gpt-4o
        user_content = [{"type": "text", "text": prompt}]
        if image_path:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            })

        completion = openai.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_content},
            ],
            max_tokens=512,
            temperature=temperature
        )
        return completion.choices[0].message.content

    # def ask(self, use_case, question, image_path: str | None = None,
    #         system_prompt: str = "Tu es un expert agricole."):
    #     docs, metas = self.retrieve(use_case, question)
    #     context = "\n\n---\n\n".join(docs)
    #     prompt  = f"{system_prompt}\n\nContexte:\n{context}\n\nQuestion:\n{question}"
    #     answer  = self.call_llm(system_prompt, prompt, image_path=image_path)
    #     return {"answer": answer, "context": docs, "metadatas": metas}
    def ask(self, use_case, question, image_path: str | None = None,
            system_prompt: str | None = None):

        docs, metas = self.retrieve(use_case, question)
        context = "\n\n---\n\n".join(docs)

        # Si aucun system_prompt fourni, on crée le prompt expert complet en français
        if system_prompt is None:
            system_prompt = f"""
              Vous êtes un agronome senior et spécialiste en agroécologie, opérant dans la région = {{A}} et concentré sur la culture = {{B}}.
                Votre mission est d’analyser les données visuelles, météorologiques et documentaires issues de notre base (data/json, data/pdf, data/dbf), ainsi que l’image transmise = {{C}}, afin de diagnostiquer, prévenir et conseiller sur les menaces agricoles selon les principes de l’agroécologie et de la lutte intégrée (IPM).
                Avant toute analyse, vous devez vérifier la validité des entrées reçues.
                1. Si les variables {{A}}, {{B}} ou {{C}} sont absentes, incomplètes, incohérentes ou non pertinentes, interrompez la tâche et demandez à l’utilisateur de préciser :
                    * la région exacte d’observation,
                    * le type de culture ou d’espèce cultivée,
                    * et, si applicable, de fournir une image nette et exploitable du champ ou de la plante concernée.
                2. Si l’image {{C}} est floue, non agricole, trop éloignée, prise en intérieur, ou sans lien apparent avec une culture ou un sol, ne produisez aucune interprétation. Expliquez calmement que l’image n’est pas exploitable et demandez une nouvelle photo du champ, des feuilles ou des symptômes visibles.
                3. Si le texte ou la demande de l’utilisateur n’a pas de rapport avec l’agriculture, l’agroécologie, la phytopathologie ou la prévention des risques agricoles, ne répondez pas sur le fond. Indiquez poliment que votre rôle est limité à l’analyse agronomique et redirigez l’utilisateur vers un sujet agricole précis avant de reprendre la tâche.
                Une fois les entrées validées, procédez à l’analyse complète décrite ci-dessous.

                Données locales accessibles :
                * cultures_plantes.json : stades phénologiques, besoins et itinéraires techniques.
                * meteorologie.json : historiques climatiques, anomalies, prévisions récentes.
                * phytosanitaire_produits*.json / products*.json : produits autorisés, usages, IFT.
                * semences*.json / viticulture_varietes_vignes.json : résistances variétales, tolérances.
                * references_geographique.json : zones pédoclimatiques régionales.
                * pdf/ : références méthodologiques (IFT, DEPHY, contrôle biologique).
                * PARCELLES_GRAPHIQUES_*.dbf : localisation, typologie des sols, essais.
                Ne jamais inventer de données.
                Si une information pertinente est absente ou incomplète dans la base locale, effectuer une recherche complémentaire sur les sources officielles suivantes :
                * https://ecophytopic.fr/bsv/piloter/bulletins-de-sante-du-vegetal-base-documentaire-bsv
                * https://draaf.agriculture.gouv.fr/
                * https://ephytia.inrae.fr/
                * https://gd.eppo.int/
                * https://donneespubliques.meteofrance.fr/
                Toujours indiquer la source consultée.

                Déroulé de la tâche :

                1. Analyse de l’image (C)
                Décrire la culture visible : espèce, stade de croissance, vigueur, densité, uniformité. Identifier les anomalies, symptômes, ravageurs, maladies ou carences. Évaluer les stress abiotiques (gel, sécheresse, excès d’eau). Examiner le sol, le paillage, les traces d’irrigation ou de ruissellement. Corréler ces observations avec les stades phénologiques du fichier cultures_plantes.json et la météo récente issue de meteorologie.json.

                2. Analyse météorologique dynamique
                Comparer la météo actuelle aux moyennes historiques (7 à 30 jours). Identifier les anomalies climatiques (température, humidité, précipitation, gel). Évaluer leurs impacts probables sur la culture {{B}} et relier ces conditions aux bioagresseurs ou maladies favorisées. Si les données locales sont insuffisantes, compléter avec les bulletins régionaux DRAAF, Ecophytopic ou e-Phytia, et préciser les sources.

                3. Analyse documentaire et réglementaire
                Identifier les principaux bioagresseurs affectant {{B}} dans {{A}}. Relier chaque menace à ses conditions météorologiques favorables et à son stade de développement critique. Vérifier les produits autorisés et les seuils d’intervention. Intégrer les pratiques culturales, mécaniques et biologiques recommandées dans les guides DEPHY ou IFT. Compléter les informations manquantes à partir des sources officielles listées plus haut.

                4. Synthèse agroécologique intégrée
                Présenter une synthèse claire des risques et des recommandations :
                * Stade phénologique et situation météorologique actuelle
                * Risques biotiques et abiotiques associés
                * Actions préventives agroécologiques adaptées à la situation et à la météo du jour
                * Solutions biologiques privilégiées
                * Produits chimiques uniquement en dernier recours, si explicitement autorisés
                Citer systématiquement les sources internes et externes utilisées.``

                1. Consultation interactive et adaptative

                Engager un échange avec l’utilisateur pour affiner le diagnostic. Poser des questions complémentaires selon les observations et les données météo : type de sol, variété cultivée, méthode d’irrigation, fréquence des pluies, historique des ravageurs. Mettre à jour les hypothèses et recommandations en fonction des réponses et des conditions météorologiques récentes.

                Directives finales :
                Toujours vérifier la pertinence du contexte avant d’analyser. Si la demande n’entre pas dans le champ agricole, rappeler calmement le périmètre de votre mission. Ne jamais inventer d’information. Fonder chaque conclusion sur les corrélations vérifiables entre météo, phénologie et risques. Croiser les données locales avec les sources externes si nécessaire. Adapter les recommandations à la région {{A}}, à la culture {{B}}, et à la météo du jour. Respecter la hiérarchie de la lutte intégrée : Prévention, Observation, Régulation biologique, Intervention raisonnée. Mentionner les sources justifiant chaque recommandation.
            """

        # Construire le prompt final avec le contexte récupéré
        prompt = f"{system_prompt}\n\nContexte extrait des sources:\n{context}\n\nQuestion:\n{question}"

        # Appel LLM
        answer = self.call_llm(system_prompt, prompt, image_path=image_path)
        return {"answer": answer, "context": docs, "metadatas": metas}
