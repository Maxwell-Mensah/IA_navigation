import pyttsx3

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        print(f"ID: {voice.id}")
        print(f"Name: {voice.name}")
        print(f"Languages: {voice.languages}")
        print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
