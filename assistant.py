import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import os
import threading
import time
import customtkinter as ctk
from PIL import Image
from AppOpener import open as open_app

# ==========================================
# 1. GLOBAL STATE & ENGINE SETUP
# ==========================================
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 170)

# Variables to control continuous note taking
is_recording_note = False
current_note_content = []

def speak(text):
    app_log.insert(ctk.END, f"MemoVoice: {text}\n")
    app_log.see(ctk.END)
    engine.say(text)
    engine.runAndWait()

# ==========================================
# 2. CORE LOGIC
# ==========================================
def process_command(command):
    command = command.lower()

    if "search" in command or "google" in command:
        query = command.replace("search", "").replace("google", "").strip()
        speak(f"Searching Google for {query}")
        webbrowser.open(f"https://www.google.com/search?q={query}")

    elif "open youtube" in command:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")

    elif "open" in command:
        app_name = command.replace("open", "").strip()
        speak(f"Opening {app_name}")
        try:
            open_app(app_name, match_closest=True)
        except Exception as e:
            speak(f"I couldn't find {app_name}")

    # NEW: Continuous Note Feature
    elif "make a note" in command or "write a note" in command:
        speak("What should the note say? Click the Stop Note button when you are finished.")
        start_continuous_note()

    else:
        speak("I am not sure how to do that yet.")

# ==========================================
# 3. VOICE RECORDING FUNCTIONS
# ==========================================
def listen_to_user(device_index, timeout=5, phrase_time_limit=10):
    """Used for standard, short commands."""
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True 
    try:
        with sr.Microphone(device_index=device_index) as source:
            app_log.insert(ctk.END, "\n[Listening for command...]\n")
            app_log.see(ctk.END)
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        app_log.insert(ctk.END, "[Processing...]\n")
        app_log.see(ctk.END)
        query = recognizer.recognize_google(audio)
        app_log.insert(ctk.END, f"You: {query}\n")
        app_log.see(ctk.END)
        return query
    except Exception:
        return None

def start_assistant():
    """Starts the standard command listener."""
    mic_index = available_mics.index(mic_dropdown.get())
    def run():
        speak("How can I help you?")
        command = listen_to_user(device_index=mic_index)
        if command:
            process_command(command)
    threading.Thread(target=run, daemon=True).start()

# --- NOTE TAKING LOGIC ---
def start_continuous_note():
    """Starts an infinite listening loop until the user clicks stop."""
    global is_recording_note, current_note_content
    is_recording_note = True
    current_note_content = []

    # Update UI to show Stop Button
    mic_button.pack_forget()
    stop_button.pack(pady=10)
    
    mic_index = available_mics.index(mic_dropdown.get())

    def record_loop():
        global is_recording_note
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        
        with sr.Microphone(device_index=mic_index) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            while is_recording_note:
                try:
                    app_log.insert(ctk.END, "[Recording Note... Speak now]\n")
                    app_log.see(ctk.END)
                    # Use shorter limits so it constantly appends sentences
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio)
                    current_note_content.append(text)
                    app_log.insert(ctk.END, f"Added: {text}\n")
                    app_log.see(ctk.END)
                except sr.WaitTimeoutError:
                    # No speech detected in the last 3 seconds, just loop again
                    continue
                except Exception:
                    pass

    threading.Thread(target=record_loop, daemon=True).start()

def stop_continuous_note():
    """Triggered by the Stop button. Saves the file."""
    global is_recording_note, current_note_content
    is_recording_note = False # Breaks the while loop above
    
    # Revert UI
    stop_button.pack_forget()
    mic_button.pack(pady=10)
    
    # Save the file
    if current_note_content:
        final_text = " ".join(current_note_content)
        if not os.path.exists("MyNotes"):
            os.makedirs("MyNotes")
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"MyNotes/note_{timestamp}.txt"
        
        try:
            with open(filename, "w") as f:
                f.write(final_text)
            app_log.insert(ctk.END, f"\nSYSTEM: Note saved to {filename}\n")
            speak("I have saved your note.")
        except Exception as e:
            speak("I had trouble saving the file.")
    else:
        speak("I didn't hear anything, so no note was saved.")

# ==========================================
# 4. FRONTEND UI (MemoVoice Redesign)
# ==========================================
ctk.set_appearance_mode("auto")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("500x700")
app.title("MEMOVOICE") # Changed to all caps

# Choose your professional font here
UI_FONT = "Century Gothic" # Alternatives: "Franklin Gothic Medium" or "Century Gothic"
CONSOLE_FONT = "Bahnschrift"

# 1. Header Frame (Logo and Title)
header_frame = ctk.CTkFrame(app, fg_color="transparent")
header_frame.pack(pady=(20, 10))

try:
    logo_image = ctk.CTkImage(Image.open("logo.png"), size=(50, 50))
    logo_label = ctk.CTkLabel(header_frame, image=logo_image, text="")
    logo_label.pack(side="left", padx=10)
except Exception:
    pass

# Title updated to uppercase and new font
title_label = ctk.CTkLabel(header_frame, text="MEMOVOICE", font=(UI_FONT, 32, "bold"))
title_label.pack(side="left")

# 2. Settings Frame (Mic Selection)
settings_frame = ctk.CTkFrame(app, corner_radius=10)
settings_frame.pack(pady=10, padx=20, fill="x")

available_mics = sr.Microphone.list_microphone_names()
if not available_mics:
    available_mics = ["NO MICROPHONES FOUND"]

mic_label = ctk.CTkLabel(settings_frame, text="AUDIO INPUT DEVICE", font=(UI_FONT, 12, "bold"))
mic_label.pack(pady=(10, 0))
mic_dropdown = ctk.CTkOptionMenu(settings_frame, values=available_mics, width=350, font=(UI_FONT, 12))
mic_dropdown.pack(pady=(5, 10))
mic_dropdown.set(available_mics[0]) 

# 3. Log Frame (Console)
log_frame = ctk.CTkFrame(app, corner_radius=10)
log_frame.pack(pady=10, padx=20, fill="both", expand=True)

app_log = ctk.CTkTextbox(log_frame, font=("Consolas", 14), fg_color="#1e1e1e", text_color="#d4d4d4")
app_log.pack(padx=10, pady=10, fill="both", expand=True)
app_log.insert(ctk.END, "SYSTEM INITIALIZED...\nREADY FOR COMMANDS.\n")

# 4. Controls Frame (Buttons)
controls_frame = ctk.CTkFrame(app, fg_color="transparent")
controls_frame.pack(pady=20)

mic_button = ctk.CTkButton(controls_frame, text="🎙️ SPEAK COMMAND", font=(CONSOLE_FONT, 16, "bold"), 
                           height=50, width=200, corner_radius=25, command=start_assistant)
mic_button.pack(pady=10)

stop_button = ctk.CTkButton(controls_frame, text="🛑 STOP NOTE", font=(UI_FONT, 16, "bold"), 
                            fg_color="#c0392b", hover_color="#922b21", height=50, width=200, 
                            corner_radius=25, command=stop_continuous_note)

app.mainloop()