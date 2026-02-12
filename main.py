from assistant import Assistant

def main():
    ai = Assistant()
    ai.speak("Bonjour, je suis votre assistant. Que puis-je faire pour vous ?")
    
    while ai.running:
        command = ai.listen()
        if command:
            ai.process_command(command)

if __name__ == "__main__":
    main()
