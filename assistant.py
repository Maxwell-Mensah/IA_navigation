import os
import sys
from ctypes import *

# Suppress ALSA/Jack error messages
try:
    ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
    def py_error_handler(filename, line, function, err, fmt):
        pass
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
except Exception:
    pass

import subprocess
import webbrowser
import time
import glob
import tempfile
from urllib.parse import quote_plus
from thefuzz import process, fuzz
from llm_handler import LLMHandler

# Try to import speech dependencies, handle gracefully if missing
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    print("Module 'speech_recognition' manquant. Mode texte uniquement.")

# Try to import gTTS and pygame
try:
    from gtts import gTTS
    import pygame
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False
    print("gTTS ou pygame manquant. Voix haute qualité désactivée.")

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    print("Module 'pyttsx3' manquant. Sortie vocale désactivée.")

class Assistant:
    def __init__(self, output_callback=None):
        self.running = True
        self.output_callback = output_callback # Function to call for GUI output
        
        # Init Pygame Mixer logic
        self.use_gtts = HAS_GTTS
        if self.use_gtts:
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"Erreur init Audio: {e}")
                self.use_gtts = False

        if HAS_TTS:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 175) # Speed of speech
            except Exception as e:
                print(f"Erreur init TTS: {e}")
                self.engine = None
        else:
            self.engine = None
        
        if HAS_SPEECH_RECOGNITION:
            self.recognizer = sr.Recognizer()
            # Calibration at startup once to correct threshold
            try:
                with sr.Microphone() as source:
                    print("Calibrage du micro (silence svp)...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                    print("Calibrage terminé.")
            except Exception as e:
                print(f"Erreur calibrage: {e}")
        else:
            self.recognizer = None


        self.apps = self._load_installed_apps()
        self.llm = LLMHandler()

    def _load_installed_apps(self):
        """Scans for installed apps in .desktop files."""
        apps = {}
        # Default/Hardcoded overrides
        apps.update({
             "navigateur": "firefox",
             "firefox": "firefox",
             "chrome": "google-chrome",
             "calculatrice": "gnome-calculator",
             "éditeur": "gedit",
             "terminal": "gnome-terminal",
             "visual studio code": "code",
             "vs code": "code",
             "code": "code"
        })

        search_paths = [
            "/usr/share/applications",
            os.path.expanduser("~/.local/share/applications")
        ]
        
        for path in search_paths:
            if not os.path.exists(path):
                continue
                
            for filepath in glob.glob(os.path.join(path, "*.desktop")):
                try:
                    with open(filepath, "r", errors="ignore") as f:
                        content = f.read()
                        
                    name = None
                    name_fr = None
                    exec_cmd = None
                    no_display = False
                    
                    for line in content.splitlines():
                        if line.startswith("Name="):
                            name = line.split("=", 1)[1].strip()
                        elif line.startswith("Name[fr]="):
                            name_fr = line.split("=", 1)[1].strip()
                        elif line.startswith("Exec="):
                            exec_cmd = line.split("=", 1)[1].strip()
                        elif line.startswith("NoDisplay=true"):
                            no_display = True
                            
                            
                    if exec_cmd and not no_display:
                        # Clean up exec command
                        exec_cmd = exec_cmd.split()[0] # Take first part (ignore args like %U)
                        
                        # Use filename as a fallback/alias (e.g. windsurf.desktop -> windsurf)
                        base_name = os.path.splitext(os.path.basename(filepath))[0].lower()
                        apps[base_name] = exec_cmd

                        if name:
                            apps[name.lower()] = exec_cmd
                        if name_fr:
                            apps[name_fr.lower()] = exec_cmd
                            
                except Exception:
                    pass
        print(f"Applications chargées : {len(apps)}")
        return apps

    def speak(self, text):
        """Outputs text via gTTS (High Quality) or pyttsx3 (Fallback)."""
        print(f"IA: {text}")
        if self.output_callback:
            self.output_callback(f"IA: {text}")
        
        # Try gTTS first if available
        if self.use_gtts:
            try:
                tts = gTTS(text=text, lang='fr')
                filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "speech.mp3")
                # Unload previous music to release file lock
                pygame.mixer.music.unload()
                tts.save(filename)
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10) 
                time.sleep(0.5) # Anti-echo buffer
                return
            except Exception as e:
                print(f"Erreur gTTS (Internet HS ?): {e}")
                # Fallthrough to pyttsx3

        # Fallback
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
        
        time.sleep(0.5) # Anti-echo buffer

    def listen(self):
        """Listens for voice input or falls back to text."""
        if HAS_SPEECH_RECOGNITION:
            try:
                # Re-use recognizer settings, don't re-adjust every time
                with sr.Microphone() as source:
                    print("\n(Écoute...)")
                    # self.recognizer.adjust_for_ambient_noise(source) # MOVED TO INIT
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    print("(Traitement...)")
                    text = self.recognizer.recognize_google(audio, language="fr-FR")
                    print(f"Vous (Vocal): {text}")
                    return text.lower()
            except (ImportError, AttributeError, OSError) as e:
                # Catch missing PyAudio or no microphone
                print(f"Erreur Micro (PyAudio manquant ?): {e}")
                return self._text_input()
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                print("Je n'ai pas compris.")
                return ""
            except sr.RequestError as e:
                print(f"Erreur service vocal: {e}")
                return self._text_input()
            except Exception as e:
                print(f"Autre erreur vocal: {e}")
                return self._text_input()
        else:
            return self._text_input()

    def _text_input(self):
        try:
            return input("Vous (Texte): ").strip().lower()
        except EOFError:
            return "quitter"

    def open_app(self, app_name):
        """Legacy method retained but mostly replaced by process_command logic."""
        # Check against fuzzy apps now
        result = process.extractOne(app_name, list(self.apps.keys()))
        if result and result[1] > 70:
             best_match, score = result[0], result[1]
             cmd = self.apps[best_match]
             self.speak(f"Ouverture de {best_match}...")
             subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        else:
             self.speak(f"Application '{app_name}' non trouvée.")

    def play_youtube(self, query):
        """Plays the first YouTube video matching the query."""
        self.speak(f"Lecture de '{query}' sur YouTube...")
        try:
            # Use yt-dlp to get the first video URL from YouTube search
            # Use yt-dlp from the same venv as the running Python
            yt_dlp_path = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
            result = subprocess.run(
                [yt_dlp_path, f"ytsearch1:{query}", "--get-id", "--no-warnings"],
                capture_output=True, text=True, timeout=10
            )
            video_id = result.stdout.strip()
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        except Exception as e:
            print(f"Erreur yt-dlp: {e}")
            url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        webbrowser.open(url)

    def search_web(self, query):
        """Searches the web."""
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        if "youtube" in query:
             self.speak(f"Recherche de '{query}' sur YouTube...")
             clean_query = query.replace('youtube', '').strip()
             url = f"https://www.youtube.com/results?search_query={quote_plus(clean_query)}"
        else:
            self.speak(f"Recherche de '{query}' sur internet...")
        
        webbrowser.open(url)

    def process_command(self, command):
        """Interprets and executes the command using LLM."""
        if not command:
            return

        # Use LLM to understand intent
        intent = self.llm.predict_intent(command)
        print(f"DEBUG LLM: {intent}")
        
        action = intent.get("action")
        target = intent.get("target")
        search = intent.get("search")
        try:
            confidence = float(intent.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0

        if action == "quit" or action == "close":
            self.speak("Au revoir !")
            self.running = False
            return

        if action == "open" and target and self.apps:
            # Fuzzy match target against installed apps
            result = process.extractOne(target, list(self.apps.keys()))
            if result and result[1] > 50:
                best_match, score = result[0], result[1]
                app_cmd = self.apps[best_match]
                self.speak(f"Ouverture de {best_match}...")
                subprocess.Popen(app_cmd, shell=True, stderr=subprocess.PIPE)
            else:
                self.speak(f"Je n'ai pas trouvé l'application '{target}'.")
            return

        if action == "search" and search:
            self.search_web(search)
            return
        
        if action == "play":
            if search:
                self.play_youtube(search)
            return

        if action not in ("error", "unknown") and confidence >= 0.4:
            # LLM understood but action not handled above
            self.speak("Je ne sais pas encore faire cette action.")
            return

        # Fallback to legacy logic if LLM is unsure or errored
        
        # --- LEGACY FALLBACK LOGIC ---
        command = command.lower()

        # Stop words
        if "quitter" in command or "stop" in command:
            self.speak("Au revoir !")
            self.running = False
            return
        
        # 1. Identify Intent (Open vs Search)
        # We can use keywords or even fuzzy match against "intent sentences"
        
        # Simple keyword checks first for speed
        open_keywords = ["ouvre", "ouvrir", "lance", "lancer", "démarrer", "démarre", "start", "open"]
        search_keywords = ["cherche", "recherche", "trouve", "trouver", "google", "search"]
        
        # Check for web search specifically ("sur youtube", etc.)
        if "youtube" in command:
             self.search_web(command)
             return

        # Check for "Open" intent
        is_open = any(k in command for k in open_keywords)
        
        if is_open:
            # Extract potential app name by removing the keyword
            # This is naive; a better way is to fuzz match the whole command against "ouvre [APP]" patterns
            # but let's try matching the whole user string against known app names first if exact match fails.
            
            # Simple heuristic: remove the trigger word and use the rest as query
            target_app = command
            for k in open_keywords:
                target_app = target_app.replace(k, "").strip()
            
            # Fuzzy match against loaded apps
            result = process.extractOne(target_app, list(self.apps.keys()))
            
            if result and result[1] > 60: # Threshold
                best_match = result[0]
                app_cmd = self.apps[best_match]
                self.speak(f"Lancement de {best_match}...")
                subprocess.Popen(app_cmd, shell=True, stderr=subprocess.PIPE)
                return
            else:
                 self.speak(f"Je n'ai pas trouvé l'application proche de '{target_app}'.")
                 return

        # Check for "Search" intent
        if any(k in command for k in search_keywords):
            # Extract query
            query = command
            for k in search_keywords:
                 query = query.replace(k, "").strip()
            self.search_web(query)
            return

        # Default fallback
        self.speak("Je ne comprends pas. Essayez 'ouvre [app]' ou 'cherche [sujet]'.")

