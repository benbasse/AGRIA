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
import os, base64, json, re, logging
import openai
from dotenv import load_dotenv
from app.schemas import AnalyseAgricoleSchema
from pydantic import ValidationError

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("OPENAI_EMBEDDINGS", "text-embedding-3-large")
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class RAG:
    def __init__(self, vector_manager):
        self.vm = vector_manager
        self.logger = logging.getLogger(__name__)
        # Charger les bases de connaissances au démarrage
        self.knowledge_base = self._load_knowledge_base()
        self.role_base = self._load_role_base()

    def _load_knowledge_base(self) -> str:
        """
        Charge la base de connaissances depuis knowlegebase.md.
        Retourne le contenu formaté pour être intégré dans le prompt.
        """
        try:
            kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowlegebase.md")
            if os.path.exists(kb_path):
                with open(kb_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.logger.info(f"✅ Base de connaissances chargée depuis {kb_path}")
                return content
            else:
                self.logger.warning(f"⚠️ Fichier knowlegebase.md non trouvé à {kb_path}")
                return ""
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du chargement de knowlegebase.md: {e}")
            return ""

    def _load_role_base(self) -> str:
        """
        Charge la base de rôles depuis rolebase.md.
        Retourne le contenu formaté pour être intégré dans le prompt.
        """
        try:
            rb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rolebase.md")
            if os.path.exists(rb_path):
                with open(rb_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.logger.info(f"✅ Base de rôles chargée depuis {rb_path}")
                return content
            else:
                self.logger.warning(f"⚠️ Fichier rolebase.md non trouvé à {rb_path}")
                return ""
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du chargement de rolebase.md: {e}")
            return ""

    def _extract_json_from_text(self, text: str) -> dict:
        """
        Extrait le JSON d'un texte, même s'il est entouré de texte supplémentaire.
        Essaie plusieurs stratégies de parsing.
        """
        # Stratégie 1: Parser directement
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Stratégie 2: Chercher un objet JSON entre accolades
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Stratégie 3: Chercher entre ```json et ```
        code_block_pattern = r'```(?:json)?\s*({.*?})\s*```'
        code_matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        for match in code_matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Si aucune stratégie ne fonctionne, lever une erreur
        raise ValueError("Impossible d'extraire un JSON valide de la réponse")

    def _validate_and_fix_json(self, data: dict) -> AnalyseAgricoleSchema:
        """
        Valide et corrige le JSON selon le schéma AnalyseAgricoleSchema.
        Retourne un objet Pydantic validé.
        """
        try:
            # Validation stricte avec Pydantic
            return AnalyseAgricoleSchema(**data)
        except ValidationError as e:
            self.logger.warning(f"Erreur de validation JSON: {e}")
            # Retourner un schéma par défaut avec niveau de confiance 0
            return AnalyseAgricoleSchema()

    def _get_fallback_response(self, error_msg: str = "Erreur lors de l'analyse") -> AnalyseAgricoleSchema:
        """
        Retourne une réponse de fallback en cas d'erreur.
        """
        return AnalyseAgricoleSchema(
            niveau_confiance=0.0,
            phenologie_actuelle=f"Analyse impossible: {error_msg}",
            sources_utilisees=["Système de fallback"]
        )

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
    ) -> str:
        """
        Appelle le LLM avec support multimodal et force le format JSON.
        """
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

        try:
            completion = openai.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=2048,  # Augmenté pour le JSON complet
                temperature=temperature,
                response_format={"type": "json_object"}  # Force le format JSON
            )
            return completion.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Erreur lors de l'appel au LLM: {e}")
            raise

    # def ask(self, use_case, question, image_path: str | None = None,
    #         system_prompt: str = "Tu es un expert agricole."):
    #     docs, metas = self.retrieve(use_case, question)
    #     context = "\n\n---\n\n".join(docs)
    #     prompt  = f"{system_prompt}\n\nContexte:\n{context}\n\nQuestion:\n{question}"
    #     answer  = self.call_llm(system_prompt, prompt, image_path=image_path)
    #     return {"answer": answer, "context": docs, "metadatas": metas}
    def _validate_image_for_usecase(self, image_path: str, use_case: str) -> dict:
        """
        Valide que l'image correspond au use_case avant de faire le diagnostic complet.
        
        Returns:
            dict avec:
            - is_valid (bool): True si l'image correspond au use_case
            - can_alert (bool): True si l'image peut alerter sur le use_case même si différente
            - message (str): Message explicatif
            - detected_type (str): Type de culture détecté
        """
        try:
            # Encoder l'image en base64
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            
            # Prompt de validation
            validation_prompt = f"""
            Analysez cette image et déterminez:
            1. Est-ce une image agricole (culture, plante, sol agricole) ?
            2. Si oui, quel type de culture est visible ?
            3. Est-ce que cette culture correspond au use_case demandé: "{use_case}" ?
            4. Si la culture est différente, peut-elle quand même alerter sur des problèmes liés au use_case "{use_case}" (ex: ravageur commun, maladie transmissible) ?
            
            Répondez UNIQUEMENT avec un JSON dans ce format exact:
            {{
                "is_agricultural": true/false,
                "detected_culture": "nom de la culture détectée ou 'non-agricole'",
                "matches_usecase": true/false,
                "can_alert": true/false,
                "reason": "explication courte"
            }}
            """
            
            response = openai.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": validation_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            # Parser la réponse
            validation_text = response.choices[0].message.content.strip()
            validation_data = self._extract_json_from_text(validation_text)
            
            # Construire le résultat
            if not validation_data.get("is_agricultural", False):
                return {
                    "is_valid": False,
                    "can_alert": False,
                    "message": "❌ Cette image ne semble pas être une image agricole. Veuillez fournir une photo de culture, plante ou sol agricole.",
                    "detected_type": "non-agricole"
                }
            
            if not validation_data.get("matches_usecase", False):
                detected = validation_data.get("detected_culture", "inconnue")
                reason = validation_data.get("reason", "")
                can_alert = validation_data.get("can_alert", False)
                
                if can_alert:
                    # L'image peut alerter même si différente
                    return {
                        "is_valid": True,
                        "can_alert": True,
                        "message": f"⚠️ Image de {detected} détectée (use_case: {use_case}). Analyse possible car peut alerter. {reason}",
                        "detected_type": detected
                    }
                else:
                    # L'image ne correspond pas et ne peut pas alerter
                    return {
                        "is_valid": False,
                        "can_alert": False,
                        "message": f"❌ Cette image montre une culture de type '{detected}' qui ne correspond pas au use_case '{use_case}'. {reason}\n\nVeuillez fournir une image correspondant à votre use_case.",
                        "detected_type": detected
                    }
            
            # Image valide et correspond au use_case
            return {
                "is_valid": True,
                "can_alert": False,
                "message": "✅ Image valide",
                "detected_type": validation_data.get("detected_culture", use_case)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la validation de l'image: {e}")
            # En cas d'erreur, on laisse passer pour ne pas bloquer
            return {
                "is_valid": True,
                "can_alert": False,
                "message": "⚠️ Validation de l'image impossible, analyse effectuée",
                "detected_type": "unknown",
                "error": str(e)
            }

    def ask_simple(
        self,
        use_case,
        question,
        system_prompt: str | None = None,
    ):
        """
        Méthode pour les questions simples sans image.
        Retourne une réponse en langage naturel (pas de JSON structuré).
        """
        docs, metas = self.retrieve(use_case, question)
        context = "\n\n---\n\n".join(docs)

        # Prompt pour conversation naturelle
        if system_prompt is None:
            # Intégrer les bases de connaissances dans le prompt pour les questions simples
            kb_section = f"""
            
            === BASE DE CONNAISSANCES SPÉCIALISÉE ===
            Vous disposez d'une base de connaissances détaillée:
            
            {self.knowledge_base}
            
            === EXPERTISE PAR DOMAINE ===
            Vous avez accès à l'expertise de spécialistes:
            
            {self.role_base}
            
            Utilisez ces informations pour enrichir vos réponses.
            ============================================
            
            """ if self.knowledge_base or self.role_base else ""
            
            system_prompt = f"""
            Vous êtes un agronome expert et conseiller agricole spécialisé en agroécologie.
            Votre rôle est de répondre aux questions des agriculteurs de manière claire, pédagogique et pratique.
            
            {kb_section}
            
            DIRECTIVES:
            - Répondez en langage naturel et accessible
            - Citez vos sources quand c'est pertinent
            - Privilégiez les approches agroécologiques
            - Soyez précis et concret dans vos conseils
            - Si vous ne savez pas, dites-le honnêtement
            - N'inventez jamais de données
            - QUAND ON TE POSE UNE QUESTION, IL FAUT FOURNIR UNE COURTE REPONSE PAS DE GRAND POINT
            
            Utilisez le contexte fourni pour enrichir votre réponse.
            """
        
        # Construire le prompt
        prompt = f"{system_prompt}\n\nContexte extrait des sources:\n{context}\n\nQuestion de l'agriculteur:\n{question}\n\nRéponse:"
        
        try:
            # Appel LLM sans forcer le format JSON
            response = openai.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Contexte:\n{context}\n\nQuestion:\n{question}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content.strip()
            
            return {
                "answer": answer,
                "context": docs,
                "metadatas": metas
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'appel LLM simple: {e}")
            return {
                "answer": f"Désolé, une erreur s'est produite: {str(e)}",
                "context": [],
                "metadatas": [],
                "error": str(e)
            }

    def ask(
        self,
        use_case,
        question,
        image_path: str | None = None,
        system_prompt: str | None = None,
    ):
        # ÉTAPE 1: Validation préalable de l'image (si fournie)
        if image_path:
            validation_result = self._validate_image_for_usecase(image_path, use_case)
            
            # Si l'image n'est pas valide et ne peut pas alerter, retourner un message simple
            if not validation_result["is_valid"] and not validation_result["can_alert"]:
                return {
                    "answer": validation_result["message"],
                    "context": [],
                    "metadatas": [],
                    "image_validation": validation_result
                }

        docs, metas = self.retrieve(use_case, question)
        context = "\n\n---\n\n".join(docs)

        # Si aucun system_prompt fourni, on crée le prompt expert complet en français
        if system_prompt is None:
            # Intégrer les bases de connaissances dans le prompt système
            kb_section = f"""
            
            === BASE DE CONNAISSANCES SPÉCIALISÉE ===
            Vous disposez d'une base de connaissances détaillée sur les maladies, ravageurs et carences de la tomate:
            
            {self.knowledge_base}
            
            === EXPERTISE PAR DOMAINE ===
            Vous avez accès à l'expertise de spécialistes:
            
            {self.role_base}
            
            Utilisez ces informations pour enrichir votre diagnostic et vos recommandations.
            ============================================
            
            """ if self.knowledge_base or self.role_base else ""
            
            system_prompt = f"""
            Vous êtes un agronome senior et spécialiste en agroécologie. Votre mission est d'établir un diagnostic phytosanitaire NUANCÉ, ACTIONNABLE et SOURCÉ pour aider l'agriculteur à prendre des décisions éclairées.
            
            {kb_section}
            
            PRINCIPES FONDAMENTAUX:
            1. DIAGNOSTIC NUANCÉ: Présentez TOUJOURS plusieurs hypothèses pondérées (pas un seul diagnostic absolu)
            2. RECOMMANDATIONS PRIORISÉES: Classez par urgence (urgent/recommandé/surveillance)
            3. SOURCES SYSTÉMATIQUES: Citez la source pour CHAQUE recommandation
            4. APPROCHE AGROÉCOLOGIQUE: Privilégiez IPM (Prévention → Observation → Bio → Chimique en dernier recours)
            5. TRANSPARENCE: Indiquez clairement les limites et le niveau de confiance

            Avant toute analyse, vous devez procéder à une vérification stricte de la validité et de la cohérence des entrées.

            Étape 0 – Vérification de conformité des données

            Si {{A}}, {{B}} ou {{C}} sont absentes, incohérentes ou non pertinentes, interrompre la tâche et demander à l'utilisateur de préciser la région, la culture et, si applicable, de fournir une image nette et exploitable.

            Si {{C}} est floue, non agricole, trop éloignée, prise en intérieur ou sans lien apparent avec une culture ou un sol, refuser l'interprétation et demander une nouvelle photo.

            Si l'image montre une plante saine, mature ou sénescente, signaler qu'aucun symptôme pathologique n'est détecté et rappeler les bonnes pratiques de surveillance.

            Si la demande n'a pas de rapport avec l'agriculture, la phytopathologie ou la prévention des risques agricoles, refuser poliment (rôle limité à l'analyse agronomique).

            Étape 0-bis – Cas où le texte est présent mais pas la photo ({{C}} manquante)
            A. Contrôler la qualité du texte. Exiger au minimum : type de culture ({{B}}), stade phénologique, description des symptômes (localisation, couleur, texture, distribution), date d'observation, et contexte cultural (irrigation, fertilisation, météo récente).
            B. Si ces éléments sont partiels, poser jusqu'à trois questions de triage pour compléter :
            - Où se situent les symptômes (feuilles jeunes/anciennes, tiges, fruits, racines) ?
            - Quelle est la nature des lésions (poudreux, huileux, nécrosé, chlorotique, perforé) ?
            - Quel est le contexte récent (pluie, irrigation, gel, vent, fertilisation) ?
            C. Si après triage le texte reste trop vague, ne pas produire de diagnostic : donner uniquement des conseils préventifs généraux et demander une photo.
            D. Normaliser les termes ambigus (ex. "tache blanche farineuse" → "aspect poudreux"). Identifier et signaler les incohérences textuelles.
            E. Si le texte est structuré et cohérent, effectuer une analyse partielle en abaissant le niveau de confiance.

            Classification de la donnée image
            A : image agricole exploitable → poursuivre l'analyse
            B : image floue/non pertinente → refuser et demander nouvelle photo
            C : culture saine → signaler état normal
            D : plante mature/sénescente → préciser stade physiologique
            E : image hors domaine → refuser

            Mode de fonctionnement selon le niveau de confiance
            Niveau 3 : données complètes (A, B, C présents) → analyse complète
            Niveau 2 : données partielles (image claire + culture) ou texte-only structuré → analyse partielle
            Niveau 1 : texte vague malgré triage → conseils généraux et demande d'éléments manquants
            Niveau 0 : données invalides → interruption et demande de précisions

            Étape 1 – Analyse de l'image {{C}} (si présente)
            Décrire la culture visible, les anomalies, symptômes, ravageurs, maladies ou carences. Évaluer les stress abiotiques, le sol, la structure, le paillage, les traces d'irrigation. Vérifier la cohérence avec {{B}}. Si incohérence, suspendre et demander confirmation.

            Étape 2 – Analyse météorologique
            Comparer la météo actuelle aux moyennes historiques. Identifier les anomalies et leurs effets sur le risque biotique. Si les données locales manquent, utiliser les moyennes décennales régionales et indiquer qu'elles sont estimées. Si événements extrêmes détectés (gel, canicule, vent fort, pluie intense), émettre une alerte.

            Étape 3 – Diagnostic phytosanitaire et hypothèses
            Proposer une liste pondérée d'hypothèses avec niveau de confiance et justification. Exemple :
            - Mildiou : 0.72 (symptômes huileux + humidité élevée + stade floraison)
            - Carence magnésienne : 0.18 (décoloration internervaire, sol sableux)
            - Autre cause : 0.10
            Chaque hypothèse mentionne : conditions favorables, stade sensible, sources utilisées.

            Étape 4 – Recommandations agroécologiques
            Présenter un plan d'action priorisé :
            - Urgente : mesures immédiates (isolement, observation renforcée)
            - Recommandée : interventions douces à moyen terme
            - À surveiller : risque faible, observation continue
            Toujours respecter la hiérarchie IPM : Prévention → Observation → Régulation biologique → Intervention raisonnée.
            Privilégier les pratiques culturales, mécaniques et biologiques. Mentionner les produits autorisés seulement en dernier recours, avec source et IFT.

            Étape 5 – Consultation interactive
            Si les données sont insuffisantes, poser jusqu'à trois questions précises, puis réviser les hypothèses et recommandations selon les réponses. Ne jamais inventer de données.

            Étape 6 – Recommandations agroécologiques
            Fournir des conseils adaptés à {{A}} et {{B}}, tenant compte des conditions locales et de la météo du jour. Prioriser les pratiques préventives et durables. Éviter les interventions chimiques sauf en dernier recours, en justifiant chaque recommandation par des sources fiables.
            L'agriculteur est le responsable final des décisions prises sur le terrain, tu ne dois pas imposer un traitement.

            STRUCTURE JSON OBLIGATOIRE - Retournez EXACTEMENT cette structure:
            
            {{
              "diagnostic": {{
                "niveau_confiance_global": 0.75,
                "stade_phenologique": "Floraison",
                "date_analyse": "2025-01-17",
                "hypotheses_diagnostiques": [
                  {{
                    "rang": 1,
                    "nom": "Mildiou de la vigne",
                    "probabilite": 0.70,
                    "niveau_gravite": "élevé",
                    "justification": "Symptômes huileux sur feuilles + humidité >85% depuis 3 jours",
                    "facteurs_favorables": ["Humidité élevée (>85%)", "Température 18-22°C", "Stade floraison"],
                    "sources": ["Ephytia.inrae.fr - Fiche Mildiou", "meteorologie.json"]
                  }},
                  {{
                    "rang": 2,
                    "nom": "Carence magnésienne",
                    "probabilite": 0.20,
                    "niveau_gravite": "modéré",
                    "justification": "Décoloration internervaire",
                    "facteurs_favorables": ["Sol sableux"],
                    "sources": ["phytosanitaire_culture.json"]
                  }}
                ],
                "diagnostic_principal": {{
                  "nom": "Mildiou de la vigne",
                  "probabilite": 0.70,
                  "synthese": "Forte probabilité de mildiou en raison des conditions météo favorables"
                }},
                "risques_evolution": {{
                  "sans_intervention": "Extension rapide aux grappes (72h), perte 30-50%",
                  "delai_critique": "24-48 heures",
                  "conditions_aggravantes": ["Pluie annoncée dans 48h"]
                }}
              }},
              "recommandations": {{
                "actions_urgentes": [
                  {{
                    "priorite": 1,
                    "action": "Isoler et surveiller les zones touchées",
                    "justification": "Limiter la propagation des spores",
                    "delai": "Immédiat (0-24h)",
                    "methode": "Agroécologique - Observation",
                    "cout_estime": "Faible",
                    "sources": ["Guide IPM Viticulture - INRAE", "Ecophytopic.fr"]
                  }}
                ],
                "actions_recommandees": [
                  {{
                    "priorite": 3,
                    "action": "Application bouillie bordelaise si aggravation",
                    "justification": "Protection curative",
                    "delai": "48-72h si extension confirmée",
                    "methode": "Dernier recours - Chimique raisonné",
                    "cout_estime": "Élevé",
                    "sources": ["Manuel IFT Avril 2018.pdf - p.42", "phytosanitaire_produits.json"]
                  }}
                ],
                "surveillance_preventive": [
                  {{
                    "action": "Monitoring quotidien des nouvelles taches",
                    "frequence": "2 fois/jour pendant 7 jours",
                    "indicateurs": ["Nouvelles taches huileuses", "Extension zones touchées", "Duvet blanc"],
                    "methode": "Agroécologique - Observation",
                    "sources": ["BSV - Protocole surveillance"]
                  }}
                ],
                "pratiques_preventives_futures": {{
                  "culturelles": [
                    {{
                      "pratique": "Enherbement inter-rang",
                      "benefice": "Réduction humidité au sol",
                      "periode": "Automne prochain",
                      "source": "DEPHY EXPE - Méthodes contrôle biologique"
                    }}
                  ],
                  "mecaniques": [
                    {{
                      "pratique": "Palissage aéré",
                      "benefice": "Meilleure circulation d'air",
                      "periode": "Printemps",
                      "source": "Chambre Agriculture"
                    }}
                  ],
                  "biologiques": [
                    {{
                      "pratique": "Purin d'ortie préventif",
                      "benefice": "Renforcement défenses naturelles",
                      "periode": "Avant floraison",
                      "source": "ITAB - Guide biocontrôle"
                    }}
                  ]
                }}
              }},
              "contexte": {{
                "situation_meteorologique": {{
                  "resume_recent": "Humidité élevée (85-90%) + T° 18-22°C depuis 3 jours",
                  "anomalies_detectees": ["Humidité +20% vs normale", "Pluies +15mm en 5 jours"],
                  "previsions_72h": "Pluie modérée attendue",
                  "impact_risque": "Conditions optimales pour mildiou"
                }},
                "historique_parcelle": {{
                  "dernier_traitement": "Soufre (oïdium) - il y a 15 jours",
                  "episodes_similaires": ["Juin 2023 - Mildiou confirmé"]
                }}
              }},
              "sources_et_fiabilite": {{
                "sources_utilisees": {{
                  "meteorologie": ["meteorologie.json", "Météo France"],
                  "phytosanitaire": ["Ephytia.inrae.fr", "phytosanitaire_produits.json", "Manuel IFT Avril 2018.pdf"],
                  "instituts": ["INRAE", "IFV", "DRAAF", "Ecophytopic.fr"],
                  "reglementation": ["products-autorises.json"]
                }},
                "fiabilite_analyse": {{
                  "qualite_image": "Bonne (symptômes visibles)",
                  "coherence_donnees": "Élevée (météo + symptômes concordants)",
                  "completude_contexte": "Partielle (historique parcelle manquant)",
                  "niveau_confiance_final": 0.75
                }},
                "limites_analyse": ["Analyse basée sur image unique", "Historique cultural incomplet"]
              }}
            }}

            DIRECTIVES CRITIQUES:
            1. TOUJOURS fournir 2-3 hypothèses diagnostiques minimum (sauf si culture saine)
            2. TOUJOURS classer les recommandations par priorité (urgent 1-2, recommandé 3-5, surveillance)
            3. TOUJOURS citer la source EXACTE pour chaque action (nom du fichier, page PDF, URL)
            4. TOUJOURS respecter la hiérarchie IPM dans les recommandations
            5. TOUJOURS indiquer les limites de l'analyse dans "limites_analyse"
            6. Ne JAMAIS inventer de données - si manquantes, l'indiquer clairement
            7. Retourner UNIQUEMENT le JSON, sans texte avant/après, sans markdown
            """
        
        # Construire le prompt final avec le contexte récupéré
        prompt = f"{system_prompt}\n\nContexte extrait des sources:\n{context}\n\nQuestion:\n{question}\n\nRappel: Retournez UNIQUEMENT le JSON, rien d'autre."

        try:
            # Appel LLM
            raw_answer = self.call_llm(system_prompt, prompt, image_path=image_path)
            
            # Extraction et parsing du JSON
            json_data = self._extract_json_from_text(raw_answer)
            
            # Validation avec Pydantic
            validated_analysis = self._validate_and_fix_json(json_data)
            
            # Retour avec l'objet validé
            return {
                "answer": validated_analysis.model_dump(),  # Convertir en dict
                "context": docs,
                "metadatas": metas,
                "raw_response": raw_answer  # Pour debug si nécessaire
            }
            
        except ValueError as e:
            # Erreur d'extraction JSON
            self.logger.error(f"Impossible d'extraire le JSON: {e}")
            fallback = self._get_fallback_response(str(e))
            return {
                "answer": fallback.model_dump(),
                "context": docs,
                "metadatas": metas,
                "error": str(e)
            }
            
        except Exception as e:
            # Erreur générale
            self.logger.error(f"Erreur lors de l'analyse: {e}")
            fallback = self._get_fallback_response(str(e))
            return {
                "answer": fallback.model_dump(),
                "context": [],
                "metadatas": [],
                "error": str(e)
            }
