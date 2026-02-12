import customtkinter as ctk
import threading
from assistant import Assistant

# Set theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AssistantGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Assistant IA")
        self.geometry("600x500")

        # Layout configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Chat area
        self.grid_rowconfigure(1, weight=0) # Text input area
        self.grid_rowconfigure(2, weight=0) # Button area

        # Chat Output Area
        self.chat_display = ctk.CTkTextbox(self, width=500, height=350, wrap="word", font=("Roboto", 14))
        self.chat_display.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        self.chat_display.insert("0.0", "IA: Bonjour ! Appuyez sur le bouton pour parler.\n\n")
        self.chat_display.configure(state="disabled") # Read-only initially

        # Text Input Area
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.text_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Tapez votre commande ici...", font=("Roboto", 14), height=40)
        self.text_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.text_entry.bind("<Return>", lambda e: self.send_text_command())

        self.send_button = ctk.CTkButton(self.input_frame, text="Envoyer", width=100, height=40, command=self.send_text_command)
        self.send_button.grid(row=0, column=1)

        # Listen Button
        self.listen_button = ctk.CTkButton(
            self, 
            text="🎙️ Écouter", 
            font=("Roboto", 16, "bold"),
            height=50,
            command=self.start_listening_thread,
            fg_color="#1f6aa5", 
            hover_color="#144870"
        )
        self.listen_button.grid(row=2, column=0, padx=20, pady=(5, 20), sticky="ew")

        # Assistant Instance
        self.assistant = Assistant(output_callback=self.update_chat)
        self.is_listening = False

    def update_chat(self, message):
        """Updates the text box safely."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", message + "\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def start_listening_thread(self):
        """Starts listening in a background thread to allow GUI updates."""
        if not self.is_listening:
            self.is_listening = True
            self.listen_button.configure(text="🛑 Écoute en cours...", fg_color="#a51f1f", hover_color="#701414")
            threading.Thread(target=self.run_listening_cycle, daemon=True).start()

    def send_text_command(self):
        """Sends a text command from the input field."""
        text = self.text_entry.get().strip()
        if not text:
            return
        self.text_entry.delete(0, "end")
        self.update_chat(f"Vous: {text}")
        threading.Thread(target=self._process_text, args=(text,), daemon=True).start()

    def _process_text(self, text):
        """Processes a text command in a background thread."""
        try:
            self.assistant.process_command(text.lower())
            if not self.assistant.running:
                self.after(500, self.destroy)
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.update_chat(f"Erreur: {error_msg}"))

    def run_listening_cycle(self):
        """Runs one cycle of listen -> process."""
        try:
            # 1. Listen
            text = self.assistant.listen()
            
            # Update GUI with user text if valid
            if text:
                self.after(0, lambda: self.update_chat(f"Vous: {text}"))
                
                # 2. Process
                self.assistant.process_command(text)

                if not self.assistant.running:
                    self.after(500, self.destroy)
            
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.update_chat(f"Erreur: {error_msg}"))
        finally:
            # Reset button state
            self.is_listening = False
            self.after(0, lambda: self.reset_button())

    def reset_button(self):
        self.listen_button.configure(text="🎙️ Écouter", fg_color="#1f6aa5", hover_color="#144870")

if __name__ == "__main__":
    app = AssistantGUI()
    app.mainloop()
