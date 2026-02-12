# 🤖 Assistant IA Vocal

Assistant intelligent pour Linux qui permet de contrôler son ordinateur par la voix ou le clavier.

## Fonctionnalités

- **Commande vocale** — Parlez à votre assistant via le microphone
- **Commande texte** — Tapez vos commandes dans le terminal ou la GUI
- **Ouverture d'applications** — "Ouvre Firefox", "Lance VS Code", "Démarre le terminal"
- **Recherche web** — "Cherche des recettes de pizza", "Recherche Python tutoriel"
- **Lecture YouTube** — "Joue Adriano", "Mets de la musique"
- **Compréhension intelligente** — Utilise Groq (LLama 3.1) pour comprendre vos intentions
- **Fallback par mots-clés** — Fonctionne même si l'API est indisponible
- **Interface graphique** — GUI moderne avec CustomTkinter (thème sombre)

## Prérequis

- **Python 3.10+**
- **Linux** (testé sur Ubuntu)
- Un **microphone** (optionnel, fallback texte disponible)
- Une **clé API Groq** gratuite → [console.groq.com/keys](https://console.groq.com/keys)

## Installation

```bash
# Cloner le repo
git clone https://github.com/Maxwell-Mensah/IA_navigation.git
cd IA_navigation

# Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les clés API
cp .env.example .env
# Éditer .env et ajouter votre clé GROQ_API_KEY
```

## Utilisation

### Mode console (terminal)
```bash
python main.py
```

### Mode GUI (interface graphique)
```bash
python gui.py
```

## Commandes exemples

| Commande | Action |
|---|---|
| "Ouvre Firefox" | Lance le navigateur Firefox |
| "Lance VS Code" | Ouvre Visual Studio Code |
| "Cherche Python tutoriel" | Recherche Google |
| "Joue Adriano" | Lance la vidéo YouTube |
| "Quitter" / "Stop" | Arrête l'assistant |

## Architecture

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée mode console |
| `gui.py` | Interface graphique CustomTkinter |
| `assistant.py` | Logique principale (écoute, parole, commandes) |
| `llm_handler.py` | Interface avec l'API Groq (LLama 3.1) |

## Technologies

- **Groq API** — LLM cloud gratuit et ultra-rapide (LLama 3.1 8B)
- **SpeechRecognition** — Reconnaissance vocale (Google Speech API)
- **gTTS + Pygame** — Synthèse vocale haute qualité
- **pyttsx3** — Synthèse vocale offline (fallback)
- **CustomTkinter** — Interface graphique moderne
- **thefuzz** — Fuzzy matching pour les noms d'applications
- **yt-dlp** — Recherche et lecture directe de vidéos YouTube
