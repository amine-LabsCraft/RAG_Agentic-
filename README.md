# Agentic RAG Masterclass

Une application web d’apprentissage pour construire et comprendre un système de **RAG** (*Retrieval-Augmented Generation*) : on importe ses documents, puis on discute avec un modèle de langage capable d’y chercher du contexte avant de répondre.

Le projet est pensé comme un support de masterclass, mais il forme aussi une base d’application concrète : authentification, conversations persistantes, ingestion de documents, recherche vectorielle, réponses en streaming, configuration centralisée des fournisseurs IA et traçabilité optionnelle.

> **État actuel : modules 1 et 2 terminés.** Les formats actuellement pris en charge sont uniquement `.txt` et `.md`. Les fonctionnalités citées dans le PRD telles que PDF/DOCX, recherche hybride, reranking, Text-to-SQL, recherche web, sous-agents et déploiement sont prévues pour les modules suivants ; elles ne sont pas encore implémentées.

## Sommaire

- [Ce que fait l’application](#ce-que-fait-lapplication)
- [Vue d’ensemble technique](#vue-densemble-technique)
- [Prérequis](#prérequis)
- [Installation rapide](#installation-rapide)
- [Configurer Supabase](#configurer-supabase)
- [Configurer les variables d’environnement](#configurer-les-variables-denvironnement)
- [Premier démarrage et première configuration](#premier-démarrage-et-première-configuration)
- [Utiliser l’application](#utiliser-lapplication)
- [Comprendre le pipeline RAG](#comprendre-le-pipeline-rag)
- [Architecture et organisation du code](#architecture-et-organisation-du-code)
- [Référence API](#référence-api)
- [Commandes utiles](#commandes-utiles)
- [Validation et dépannage](#validation-et-dépannage)
- [Sécurité et passage en production](#sécurité-et-passage-en-production)
- [Feuille de route](#feuille-de-route)

## Ce que fait l’application

| Fonction | Comportement actuel |
| --- | --- |
| Comptes utilisateurs | Inscription et connexion par e-mail/mot de passe via Supabase Auth. |
| Conversations | Création, renommage automatique au premier message, lecture et suppression de fils de discussion. L’historique est stocké dans PostgreSQL. |
| Réponses IA | Réponses affichées progressivement grâce au streaming SSE (*Server-Sent Events*). |
| Documents | Import glisser-déposer ou sélection de plusieurs fichiers `.txt` / `.md`, jusqu’à 10 Mo par fichier. |
| Recherche RAG | Découpage, embeddings, recherche par similarité cosinus dans `pgvector`, puis injection des extraits trouvés dans la réponse. |
| Sources | Le modèle reçoit le nom du fichier et le score de similarité de chaque extrait afin de pouvoir citer les documents utilisés. |
| Suivi d’ingestion | États `pending`, `processing`, `completed` et `failed`, mis à jour en temps réel dans l’interface. |
| Configuration IA | Un administrateur configure le modèle de chat et le modèle d’embeddings depuis l’application. |
| Observabilité | Les appels OpenAI-compatibles peuvent être tracés dans LangSmith si une clé est configurée. |

## Vue d’ensemble technique

```text
Navigateur (React + Vite)
        │  Supabase Auth + JWT
        │  API HTTP / flux SSE
        ▼
Backend FastAPI
        ├── conversations et messages
        ├── ingestion asynchrone en arrière-plan
        ├── appels LLM / embeddings (API compatible OpenAI)
        └── outils : recherche dans les documents
        │
        ▼
Supabase
        ├── PostgreSQL + pgvector : fils, messages, documents, chunks
        ├── Storage privé : fichiers originaux
        ├── Auth : utilisateurs et jetons
        └── Realtime : évolution de l’état des documents
```

| Couche | Technologies |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, composants Radix/shadcn, React Router |
| Backend | Python, FastAPI, Pydantic, Uvicorn, SSE |
| Données | Supabase : PostgreSQL, `pgvector`, Auth, Storage et Realtime |
| IA | SDK OpenAI utilisé avec tout endpoint compatible OpenAI (OpenAI, OpenRouter, fournisseur auto-hébergé compatible…) |
| Observabilité | LangSmith, facultatif |

## Prérequis

Pour le parcours recommandé avec un projet Supabase distant :

- Windows avec **PowerShell** ; les scripts fournis ciblent cet environnement.
- Python **3.10 ou plus récent** (3.11 recommandé).
- Node.js **20 LTS ou plus récent** et npm.
- Un projet [Supabase](https://supabase.com/) avec accès aux clés API et, pour appliquer les migrations, le CLI Supabase.
- Une ou deux clés de fournisseur IA compatibles avec l’API OpenAI : une pour le chat et une pour les embeddings. Elles peuvent provenir du même fournisseur si celui-ci prend en charge les deux API.
- Facultatif : un compte LangSmith pour suivre les appels IA.

Pour une instance Supabase locale, il faut également Docker Desktop et le CLI Supabase. Cette option est utile pour expérimenter sans projet distant.

## Installation rapide

Les instructions suivantes démarrent l’application sur :

- Frontend : `http://localhost:5173`
- API backend : `http://localhost:8000`
- Santé de l’API : `http://localhost:8000/health`

### 1. Installer les dépendances backend

Depuis la racine du projet :

```powershell
Set-Location backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Set-Location ..
```

Le dossier d’environnement virtuel attendu par les scripts est `backend\venv`.

### 2. Installer les dépendances frontend

```powershell
Set-Location frontend
npm install
Set-Location ..
```

### 3. Créer la base Supabase et appliquer les migrations

Suivez [Configurer Supabase](#configurer-supabase) avant de démarrer : le backend ne peut pas se lancer sans ses variables Supabase, et l’application requiert les tables/migrations du dépôt.

### 4. Créer les fichiers d’environnement

Créez vos fichiers locaux à partir des modèles, puis complétez les valeurs selon [Configurer les variables d’environnement](#configurer-les-variables-denvironnement) :

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Les fichiers `.env` sont ignorés par Git : ne les versionnez jamais.

### 5. Démarrer les deux services

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

Deux fenêtres PowerShell s’ouvrent : une pour Uvicorn et une pour Vite. Ouvrez ensuite `http://localhost:5173`.

Le lanceur vérifie d’abord que les deux fichiers `.env` et les dépendances locales existent, puis démarre les services. Pour les contrôles automatiques disponibles localement :

```powershell
powershell -ExecutionPolicy Bypass -File .\test.ps1
```

Pour vérifier indépendamment le backend :

```powershell
curl.exe http://localhost:8000/health
```

La réponse attendue est :

```json
{"status":"ok"}
```

## Configurer Supabase

### Option A — Projet Supabase Cloud (recommandée)

1. Créez un projet dans Supabase.
2. Dans **Project Settings → API**, récupérez l’URL du projet, la clé `anon` et la clé `service_role`.
3. Authentifiez et liez le CLI au projet, depuis la racine du dépôt :

   ```powershell
   supabase login
   supabase link --project-ref <votre-project-ref>
   supabase db push
   ```

   Le `project-ref` est l’identifiant présent dans l’URL/les réglages du projet. `supabase db push` applique les migrations dans l’ordre, notamment les tables, les politiques RLS, le bucket privé `documents`, `pgvector`, Realtime et les réglages globaux.

4. Renseignez les valeurs obtenues dans les deux fichiers `.env` décrits ci-dessous.

### Option B — Supabase local

Depuis la racine du projet :

```powershell
supabase start
supabase db reset
supabase status
```

`supabase status` affiche l’URL locale, la clé `anon` et la clé `service_role` à copier dans les fichiers `.env`. `supabase db reset` recrée la base locale et rejoue les migrations du dossier `supabase/migrations`.

Pour arrêter les services locaux :

```powershell
supabase stop
```

### Ce que créent les migrations

| Élément | Rôle |
| --- | --- |
| `threads` | Conversations d’un utilisateur. |
| `messages` | Messages utilisateur et assistant rattachés à un fil. |
| `documents` | Métadonnées, chemin Storage et statut d’ingestion. |
| `chunks` | Extraits de texte, embeddings et métadonnées de recherche. |
| `user_profiles` | Indicateur `is_admin` utilisé pour protéger les réglages globaux. |
| `global_settings` | Ligne unique contenant les paramètres des fournisseurs IA. |
| bucket Storage `documents` | Fichiers originaux, non publics et organisés par utilisateur. |
| fonction `match_chunks` | Recherche vectorielle par similarité cosinus dans les chunks de l’utilisateur. |

Les tables métier sont protégées par des politiques **RLS** (*Row-Level Security*) afin de cloisonner les données par utilisateur lorsque Supabase est interrogé avec un jeton utilisateur.

## Configurer les variables d’environnement

### Backend : `backend/.env`

Créez le fichier suivant, puis remplacez chaque valeur entre chevrons :

```dotenv
# Supabase — ne jamais exposer la clé service_role dans le frontend
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<votre-cle-anon>
SUPABASE_SERVICE_ROLE_KEY=<votre-cle-service-role>

# Autorise Vite à appeler le backend. Le format est une liste JSON.
CORS_ORIGINS=["http://localhost:5173"]

# LangSmith est facultatif : laissez vide pour désactiver le tracing.
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=rag-masterclass

# Fortement recommandé : clé Fernet URL-safe de 32 octets pour chiffrer
# les clés de fournisseurs enregistrées dans global_settings.
SETTINGS_ENCRYPTION_KEY=<cle-fernet>
```

Les noms de variables sont conservés pour compatibilité avec le code actuel : vous pouvez y placer les clés Supabase récentes `sb_publishable_...` (à la place de `anon`) et `sb_secret_...` (à la place de `service_role`). La clé publishable va aussi dans `VITE_SUPABASE_ANON_KEY`; la clé secret reste strictement dans `backend/.env`.

Générez une clé Fernet locale avec :

```powershell
Set-Location backend
.\venv\Scripts\Activate.ps1
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
Set-Location ..
```

Conservez cette clé dans un gestionnaire de secrets. La remplacer rend illisibles les clés IA déjà chiffrées dans la base ; les supprimer ou les saisir à nouveau sera alors nécessaire.

### Frontend : `frontend/.env`

```dotenv
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<votre-cle-anon>
VITE_API_URL=http://localhost:8000
```

Les variables préfixées par `VITE_` sont intégrées au bundle navigateur. N’y placez donc jamais de clé secrète, et surtout jamais `SUPABASE_SERVICE_ROLE_KEY` ni une clé de fournisseur IA.

## Premier démarrage et première configuration

### 1. Créer un compte et désigner le premier administrateur

Après avoir lancé l’application, créez un compte depuis `http://localhost:5173/auth`. Le rôle administrateur est stocké dans `public.user_profiles`.

Depuis l’éditeur SQL Supabase, exécutez ensuite la requête suivante en remplaçant l’adresse e-mail :

```sql
UPDATE public.user_profiles
SET is_admin = true
WHERE user_id = (
  SELECT id FROM auth.users WHERE email = 'admin@votre-domaine.example'
);
```

Déconnectez-vous puis reconnectez-vous. Le menu utilisateur affichera alors **Settings**. Seul un administrateur peut modifier la configuration IA globale.

> Les migrations récentes révoquent tout ancien rôle administrateur attribué à un compte de démonstration. Attribuez toujours le premier rôle explicitement avec la requête ci-dessus.

### 2. Configurer le modèle de chat et les embeddings

Dans **Settings**, renseignez deux ensembles de paramètres :

| Champ | Modèle de chat | Modèle d’embeddings |
| --- | --- | --- |
| Model Name | Identifiant accepté par le fournisseur, par exemple `gpt-4o` ou `anthropic/claude-3.5-sonnet` | Identifiant d’embeddings, par exemple `text-embedding-3-small` |
| Base URL | Endpoint compatible OpenAI, par exemple `https://openrouter.ai/api/v1` | Endpoint compatible OpenAI qui expose `embeddings.create`, par exemple `https://api.openai.com/v1` |
| API Key | Clé du fournisseur de chat | Clé du fournisseur d’embeddings |
| Dimensions | — | Nombre de dimensions renvoyées par le modèle, par exemple `1536` |

Les clés sont masquées à la relecture. Avec `SETTINGS_ENCRYPTION_KEY`, elles sont également chiffrées avant stockage ; sans cette variable, elles sont stockées en clair dans `global_settings`.

**Important :** le projet utilise une configuration d’embeddings globale. Dès qu’un chunk existe, l’interface verrouille les réglages d’embeddings. Supprimez tous les documents avant de changer de modèle, d’endpoint, de clé ou de dimension ; cela évite de comparer des vecteurs incompatibles.

### 3. Vérifier le parcours complet

1. Créez une conversation et envoyez un message général : le modèle de chat doit répondre.
2. Allez dans **Documents** et importez un fichier `.txt` ou `.md` de moins de 10 Mo.
3. Attendez le statut `completed` et vérifiez le nombre de chunks.
4. Revenez au chat et posez une question dont la réponse se trouve dans le fichier.
5. Vérifiez que la réponse s’appuie sur les extraits et mentionne le nom du document lorsque le modèle utilise l’outil de recherche.

## Utiliser l’application

### Conversations

- **New Chat** crée un fil vide.
- Le titre du fil est automatiquement remplacé par les 50 premiers caractères environ du premier message.
- Sélectionnez un fil dans la barre latérale pour retrouver son historique.
- Le bouton carré pendant une réponse annule la lecture côté navigateur. Le message utilisateur a déjà été créé, et une réponse partielle peut dépendre du moment de l’annulation.
- La corbeille supprime le fil et ses messages associés.

### Documents

Les imports acceptent plusieurs fichiers, mais ils sont envoyés un par un. Pour chaque document, l’interface affiche :

| Statut | Signification | Action conseillée |
| --- | --- | --- |
| `pending` | Le fichier a été stocké et attend le traitement. | Attendre quelques instants. |
| `processing` | Le texte est découpé puis envoyé au fournisseur d’embeddings. | Garder le backend actif. |
| `completed` | Les chunks et leurs vecteurs sont disponibles pour la recherche. | Vous pouvez interroger le document. |
| `failed` | L’extraction, l’embedding ou le stockage a échoué. | Consultez le message affiché et les logs du backend. |

La suppression d’un document supprime son fichier Storage ainsi que ses chunks grâce à la suppression en cascade. Cette action est définitive dans l’application.

### Rôles

| Rôle | Droits |
| --- | --- |
| Utilisateur connecté | Gérer ses conversations et ses propres documents ; lire les réglages globaux non secrets. |
| Administrateur | Tous les droits utilisateur, plus modification du fournisseur de chat et d’embeddings. |

## Comprendre le pipeline RAG

### Ingestion

```text
Fichier .txt / .md
  → Storage Supabase privé
  → enregistrement `documents` (pending)
  → tâche FastAPI en arrière-plan (processing)
  → décodage UTF-8
  → découpage récursif
  → embeddings par lots de 50
  → table `chunks` + pgvector
  → document marqué completed
```

Le découpage est volontairement simple et sans framework externe : il vise **1 000 caractères** par chunk, avec un chevauchement de **200 caractères**. Il essaie successivement les séparateurs paragraphe, ligne, phrase puis espace. Le chevauchement préserve une partie du contexte d’un chunk à l’autre.

### Réponse augmentée

```text
Question utilisateur
  → historique complet du fil + prompt système
  → le LLM décide éventuellement d’appeler `search_documents`
  → embedding de la requête
  → `match_chunks` : top 5, similarité cosinus > 0,50, limitée à l’utilisateur
  → extraits formatés avec leurs noms de fichiers
  → nouvelle génération du LLM
  → texte envoyé progressivement au navigateur puis sauvegardé
```

Le modèle peut répondre sans recherche lorsqu’il estime qu’un document n’est pas pertinent. La recherche n’est donc pas forcée à chaque message. Au maximum trois tours d’appels d’outils sont autorisés par réponse pour éviter les boucles infinies.

### Quelques notions clés

| Notion | Dans ce projet |
| --- | --- |
| Embedding | Représentation numérique d’un texte. Des textes proches sémantiquement produisent des vecteurs proches. |
| Chunk | Portion de document indexée séparément, ce qui améliore la précision et limite le contexte envoyé au modèle. |
| Similarité cosinus | Mesure de proximité entre deux vecteurs ; ici elle sert à sélectionner les extraits les plus pertinents. |
| RAG | Le modèle n’est pas réentraîné : on lui fournit, au moment de répondre, des extraits récupérés depuis vos documents. |
| Streaming SSE | Le backend envoie de petits fragments de réponse au navigateur au fil de la génération. |

## Architecture et organisation du code

```text
RAG_Agentic/
├── frontend/                       # Application React
│   ├── src/pages/                  # Chat, Documents, Settings
│   ├── src/components/             # Interface, chat, auth, documents
│   ├── src/hooks/                  # Auth et abonnement Realtime
│   └── src/lib/                    # Clients Supabase et API backend
├── backend/                        # API FastAPI
│   ├── app/routers/                # Endpoints HTTP
│   ├── app/services/               # LLM, ingestion, embeddings, retrieval
│   ├── app/db/                     # Client Supabase server-side
│   ├── app/models/                 # Schémas Pydantic
│   ├── app/config.py               # Variables d’environnement
│   └── requirements.txt
├── supabase/
│   ├── migrations/                 # Schéma, RLS, Storage et RPC
│   ├── config.toml                 # Configuration Supabase locale
│   └── seed.sql
├── scripts/                        # Démarrage/arrêt PowerShell
├── .agent/validation/              # Scénarios de validation manuelle
├── PRD.md                          # Périmètre pédagogique et roadmap détaillée
├── PROGRESS.md                     # Avancement des modules
└── CLAUDE.md                       # Contexte et conventions de développement assisté
```

### Backend

| Zone | Responsabilité |
| --- | --- |
| `app/main.py` | Crée FastAPI, configure CORS, les routes et `/health`. |
| `app/dependencies.py` | Extrait l’utilisateur du JWT et vérifie le rôle administrateur. |
| `routers/threads.py` | CRUD des conversations. |
| `routers/chat.py` | Sauvegarde les messages, orchestre le streaming et la boucle d’outils. |
| `routers/documents.py` | Validation, upload Storage, liste et suppression des documents. |
| `routers/settings.py` | Réglages IA globaux, masquage/chiffrement de clés et contrôle administrateur. |
| `services/ingestion_service.py` | Extraction texte, chunking, embeddings et persistance. |
| `services/retrieval_service.py` | Appelle `match_chunks` après embedding de la requête. |
| `services/llm_service.py` | Construit les appels `chat.completions` et expose l’outil de recherche. |

### Frontend

| Zone | Responsabilité |
| --- | --- |
| `pages/ChatPage.tsx` | Layout de chat, sélection/création des fils. |
| `components/chat/ChatView.tsx` | Historique, Markdown, SSE, génération et annulation. |
| `pages/DocumentsPage.tsx` | Import et liste des documents. |
| `hooks/useRealtimeDocuments.ts` | Synchronise les changements de statut Supabase Realtime. |
| `pages/SettingsPage.tsx` | Écran réservé aux administrateurs. |
| `hooks/useAuth.ts` | Session Supabase et récupération du rôle depuis `/auth/me`. |

## Référence API

À l’exécution, la documentation interactive FastAPI est disponible à `http://localhost:8000/docs`.

Sauf `/health`, les routes nécessitent l’en-tête suivant :

```http
Authorization: Bearer <access-token-supabase>
```

| Méthode | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Vérifie que l’API répond. |
| `GET` | `/auth/me` | Retourne l’utilisateur connecté et `is_admin`. |
| `GET` | `/threads` | Liste les fils de l’utilisateur. |
| `POST` | `/threads` | Crée un fil ; corps facultatif : `{"title":"…"}`. |
| `GET` | `/threads/{thread_id}` | Lit un fil appartenant à l’utilisateur. |
| `PATCH` | `/threads/{thread_id}` | Renomme un fil. |
| `DELETE` | `/threads/{thread_id}` | Supprime un fil et ses messages. |
| `GET` | `/threads/{thread_id}/messages` | Liste les messages du fil. |
| `POST` | `/threads/{thread_id}/messages` | Envoie `{"content":"…"}` et retourne un flux SSE. |
| `POST` | `/documents/upload` | Importe un fichier multipart `.txt` ou `.md`. |
| `GET` | `/documents` | Liste les documents de l’utilisateur. |
| `DELETE` | `/documents/{document_id}` | Supprime le document, ses chunks et le fichier Storage. |
| `GET` | `/settings` | Lit les réglages globaux, clés masquées. |
| `PUT` | `/settings` | Met à jour les réglages ; administrateur requis. |

Le flux de chat émet des événements `text_delta`, `done` et, en cas de problème, `error`.

## Commandes utiles

Toutes les commandes suivantes s’exécutent depuis la racine du projet.

| Objectif | Commande |
| --- | --- |
| Démarrer frontend et backend | `powershell -File scripts\start-all.ps1` |
| Démarrage vérifié en une commande | `powershell -ExecutionPolicy Bypass -File .\run.ps1` |
| Démarrer seulement le backend | `powershell -File scripts\start-backend.ps1` |
| Démarrer seulement le frontend | `powershell -File scripts\start-frontend.ps1` |
| Arrêter les deux services | `powershell -File scripts\stop-all.ps1` |
| Redémarrer les deux services | `powershell -File scripts\restart-all.ps1` |
| Redémarrer le backend | `powershell -File scripts\restart-backend.ps1` |
| Redémarrer le frontend | `powershell -File scripts\restart-frontend.ps1` |
| Compiler le frontend | `Set-Location frontend; npm run build` |
| Linter le frontend | `Set-Location frontend; npm run lint` |
| Lancer toutes les vérifications locales | `powershell -ExecutionPolicy Bypass -File .\test.ps1` |
| Appliquer les migrations distantes | `supabase db push` |
| Recréer la base locale | `supabase db reset` |

Les scripts d’arrêt identifient les processus écoutant sur les ports `8000` et `5173`, puis arrêtent leur arbre de processus. Ils ne doivent donc être utilisés que si ces ports sont bien dédiés à cette application.

## Validation et dépannage

### Vérifications de base

```powershell
# API
curl.exe http://localhost:8000/health

# Build TypeScript + Vite
Set-Location frontend
npm run build
Set-Location ..
```

Des scénarios de validation API et interface sont documentés dans `.agent/validation/full-suite.md`. Ils couvrent notamment l’authentification, les fils, le streaming, l’import, la recherche RAG, l’isolation des données et les réglages. Il s’agit actuellement d’un guide de tests, pas d’une commande de tests automatisée unique.

### Problèmes fréquents

| Symptôme | Cause probable | Correctif |
| --- | --- | --- |
| Le backend échoue au démarrage avec des variables manquantes | `backend/.env` absent ou incomplet. | Vérifiez les trois variables Supabase et la syntaxe JSON de `CORS_ORIGINS`. |
| L’écran reste sur “Loading” ou l’authentification ne marche pas | Les variables `VITE_SUPABASE_*` sont incorrectes ou Vite n’a pas été redémarré. | Corrigez `frontend/.env`, puis redémarrez le frontend. |
| Le chat indique que le LLM n’est pas configuré | Aucun administrateur n’a renseigné une clé LLM valide. | Attribuez le rôle admin puis complétez **Settings**. |
| L’import passe à `failed` | Clé d’embeddings absente/invalide, texte non UTF-8, fournisseur incompatible ou erreur réseau. | Consultez l’erreur affichée et les logs Uvicorn ; vérifiez modèle, endpoint, clé et dimensions. |
| La recherche ne trouve rien | Aucun document terminé, question peu proche du contenu, ou score sous le seuil 0,50. | Attendez `completed`, reformulez la question et vérifiez que le document contient bien l’information. |
| Impossible de modifier les embeddings | Au moins un chunk existe dans la base. | Supprimez les documents, attendez la suppression des chunks, puis modifiez les réglages. |
| Erreur CORS dans le navigateur | L’URL du frontend n’est pas autorisée par le backend. | Ajoutez l’URL exacte dans `CORS_ORIGINS` sous forme de liste JSON puis redémarrez le backend. |
| Les statuts ne se mettent pas à jour en direct | Realtime ou la publication de `documents` n’est pas active. | Vérifiez que toutes les migrations ont été appliquées et rechargez la page. |
| Le port est déjà occupé | Un serveur précédent écoute encore sur 8000 ou 5173. | Lancez le script d’arrêt correspondant, ou libérez le port concerné. |

## Sécurité et passage en production

Cette application est une base pédagogique fonctionnelle, mais plusieurs points doivent être traités avant une exposition publique ou une charge importante.

1. **Vérification des JWT.** Le backend valide désormais chaque jeton auprès de Supabase avant d’en utiliser l’identité. Conservez ce contrôle côté serveur, testez régulièrement les jetons invalides/expirés et ne vous fiez jamais à des claims décodés sans vérification cryptographique.
2. **Clé `service_role`.** Elle contourne les politiques RLS : elle doit rester exclusivement sur le serveur, dans un gestionnaire de secrets, jamais dans le frontend ni dans les logs.
3. **Chiffrement des clés IA.** Définissez `SETTINGS_ENCRYPTION_KEY` et gérez-la comme un secret de production. La sauvegarde des clés dans l’interface ne remplace pas un coffre de secrets pour les environnements sensibles.
4. **Administrateurs.** Les migrations ne donnent plus de privilège à un compte de démonstration. Attribuez les rôles explicitement et auditez régulièrement `user_profiles`.
5. **Ingestion.** Le traitement est exécuté par `BackgroundTasks` dans le processus FastAPI. Il n’y a ni file durable, ni reprise automatique après redémarrage, ni antivirus, ni analyse de contenu. Utilisez une file de tâches et un stockage/scan adapté à la production.
6. **Performance vectorielle.** Les dimensions d’embeddings sont flexibles, ce qui a conduit à retirer l’index vectoriel fixe. Les recherches effectuent donc un scan séquentiel acceptable pour un volume modéré ; standardisez une dimension et créez un index HNSW/IVFFlat pour des corpus importants.
7. **Limites et observabilité.** Ajoutez limitation de débit, limites de contexte, logs structurés sans secrets, alertes, sauvegardes et suivi des coûts de modèles.
8. **Déploiement.** Configurez des URL CORS explicites, HTTPS, les redirections Supabase Auth, ainsi que des environnements distincts pour développement, préproduction et production.

## Feuille de route

Le [PRD](./PRD.md) décrit le parcours complet. L’état suivi dans [PROGRESS.md](./PROGRESS.md) confirme que les deux premiers modules sont terminés.

| Module | Sujet | État dans ce dépôt |
| --- | --- | --- |
| 1 | Shell applicatif, auth, chat, streaming, observabilité | Terminé |
| 2 | Retrieval propriétaire, ingestion `.txt`/`.md`, pgvector, Realtime, fournisseurs configurables | Terminé |
| 3 | Record manager et déduplication | À faire |
| 4 | Extraction et filtrage de métadonnées | À faire |
| 5 | PDF, DOCX, HTML, Markdown enrichi | À faire (`.md` texte simple déjà accepté) |
| 6 | Recherche hybride, RRF et reranking | À faire |
| 7 | Text-to-SQL et recherche web | À faire |
| 8 | Sous-agents et contexte isolé | À faire |
| 9 | Déploiement | À faire |

## Ressources du dépôt

- [PRD.md](./PRD.md) : vision, périmètre et contenu pédagogique de chaque module.
- [PROGRESS.md](./PROGRESS.md) : avancement et validations déjà réalisées.
- [CLAUDE.md](./CLAUDE.md) : conventions de travail pour les assistants de programmation et gestion des services Windows.
- `supabase/migrations/` : source de vérité du schéma de données.
- `.agent/plans/` : plans d’implémentation historiques.

---

Si vous contribuez au projet, gardez ce README synchronisé avec le comportement livré : mettez à jour les formats acceptés, les variables requises, les routes, les limites, la sécurité et le statut de la roadmap à chaque module ajouté.
