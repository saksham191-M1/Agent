import tkinter as tk
from tkinter import messagebox
import threading
from .auth import verify_pin, verify_passphrase
from voice.input_engine import listen_once
import sys

class AuthWindow:
    def __init__(self, on_success):
        self.on_success = on_success
        self.root = tk.Tk()
        self.root.title("JARVIS - Authentication")
        self.root.geometry("320x400")
        self.root.configure(bg="#1e1e1e")
        self.root.resizable(False, False)
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        self.attempts = 0
        self.max_attempts = 3
        
        self.setup_ui()

    def setup_ui(self):
        title = tk.Label(self.root, text="🤖 J A R V I S", font=("Consolas", 20, "bold"), bg="#1e1e1e", fg="#00ffcc")
        title.pack(pady=20)
        
        lbl_voice = tk.Label(self.root, text="🎤 Speak to unlock", font=("Consolas", 12), bg="#1e1e1e", fg="white")
        lbl_voice.pack(pady=5)
        
        self.btn_mic = tk.Button(self.root, text="[ ● Mic ]", font=("Consolas", 14), bg="#333333", fg="white", 
                                 command=self.start_listening, relief=tk.FLAT, activebackground="#555555", activeforeground="white")
        self.btn_mic.pack(pady=10)
        
        self.status_label = tk.Label(self.root, text="(Say 'jarvis initialize')", font=("Consolas", 10), bg="#1e1e1e", fg="#aaaaaa")
        self.status_label.pack(pady=5)
        
        lbl_or = tk.Label(self.root, text="── or type PIN ──", font=("Consolas", 10), bg="#1e1e1e", fg="#aaaaaa")
        lbl_or.pack(pady=20)
        
        self.pin_entry = tk.Entry(self.root, show="*", font=("Consolas", 16), width=10, justify='center', bg="#333333", fg="white", insertbackground="white")
        self.pin_entry.pack(pady=10)
        self.pin_entry.bind('<Return>', lambda e: self.check_pin())
        
        btn_pin = tk.Button(self.root, text="Unlock", font=("Consolas", 12), bg="#333333", fg="white", 
                            command=self.check_pin, relief=tk.FLAT)
        btn_pin.pack(pady=5)

    def start_listening(self):
        self.btn_mic.config(state=tk.DISABLED, text="Listening...")
        self.status_label.config(text="Speak now...", fg="#00ffcc")
        threading.Thread(target=self._listen_thread, daemon=True).start()
        
    def _listen_thread(self):
        text = listen_once()
        self.root.after(0, self._handle_voice_result, text)
        
    def _handle_voice_result(self, text):
        self.btn_mic.config(state=tk.NORMAL, text="[ ● Mic ]")
        if not text:
            self.status_label.config(text="Didn't catch that.", fg="red")
            return
            
        self.status_label.config(text=f"Heard: {text}", fg="white")
        if verify_passphrase(text):
            self.success()
        else:
            self.fail()

    def check_pin(self):
        pin = self.pin_entry.get()
        if verify_pin(pin):
            self.success()
        else:
            self.pin_entry.delete(0, tk.END)
            self.fail()

    def success(self):
        self.root.destroy()
        self.on_success()

    def fail(self):
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            messagebox.showerror("Access Denied", "Too many failed attempts. Locking down.")
            self.root.destroy()
            sys.exit(1)
        else:
            self.status_label.config(text=f"Failed. Attempts left: {self.max_attempts - self.attempts}", fg="red")

    def run(self):
        self.root.mainloop()
