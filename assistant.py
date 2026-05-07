import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import os
import threading
import customtkinter as ctk
from AppOpener import open as open_app
import time

# ==========================================
# 1. INITIALIZE VOICE ENGINE
# ==========================================
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) 
engine.setProperty('rate', 170) 

def speak(text):
    """Makes the assistant talk and updates the UI."""
    app_log.insert(ctk.END, f"Assistant: {text}\n")
    app_log.see(ctk.END)
    engine.say(text)
    engine.runAndWait()

# ==========================================
# 2. CORE LOGIC & COMMAND PARSING
# ==========================================
import time # Add this at the very top with your other imports

# ==========================================
# 2. CORE LOGIC & COMMAND PARSING (FIXED)
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
            from AppOpener import open as open_app
            open_app(app_name, match_closest=True) 
        except Exception as e:
            speak(f"I couldn't find {app_name}")

    # FIXED: Taking a Note
    elif "make a note" in command or "write a note" in command:
        speak("What should the note say?")
        
        # Give the microphone a split second to reset after the assistant speaks
        time.sleep(0.5) 
        
        # Get the mic index from the dropdown
        selected_mic_name = mic_dropdown.get()
        mic_index = available_mics.index(selected_mic_name)
        
        note_content = listen_to_user(mic_index) 
        
        if note_content:
            # 1. Ensure a 'MyNotes' folder exists
            if not os.path.exists("MyNotes"):
                os.makedirs("MyNotes")
            
            # 2. Create filename with date/time
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"MyNotes/note_{timestamp}.txt"
            
            # 3. Write the file
            try:
                with open(filename, "w") as f:
                    f.write(note_content)
                app_log.insert(ctk.END, f"SYSTEM: File saved to {filename}\n")
                speak("I've saved that note for you.")
            except Exception as e:
                speak("I had trouble saving the file.")
                print(f"File Error: {e}")
        else:
            speak("I didn't hear any content, so I didn't save the note.")

    else:
        speak("I am not sure how to do that yet.")

def listen_to_user(device_index):
    recognizer = sr.Recognizer()
    # Increase sensitivity for better note-taking
    recognizer.dynamic_energy_threshold = True 
    
    try:
        with sr.Microphone(device_index=device_index) as source:
            app_log.insert(ctk.END, "\nListening...\n")
            app_log.see(ctk.END)
            # Adjusting for 1 second of silence before listening
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=20)

        app_log.insert(ctk.END, "Processing voice...\n")
        app_log.see(ctk.END)
        query = recognizer.recognize_google(audio)
        app_log.insert(ctk.END, f"You said: {query}\n")
        app_log.see(ctk.END)
        return query

    except Exception as e:
        # Don't speak the error, just return None so the loop can handle it
        print(f"Speech Recognition Error: {e}")
        return None
    
# ==========================================
# 3. THREADING & UI TRIGGER
# ==========================================
def start_assistant():
    """Gets the chosen mic and runs the listening process."""
    # Get the name from the dropdown and find its index in the original list
    selected_mic_name = mic_dropdown.get()
    mic_index = available_mics.index(selected_mic_name)
    
    def run():
        speak("How can I help you?")
        command = listen_to_user(device_index=mic_index)
        if command:
            process_command(command)
            
    threading.Thread(target=run).start()

# ==========================================
# 4. FRONTEND (CUSTOMTKINTER)
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("500x650") # Made the window slightly taller to fit the dropdown
app.title("AICC Voice Assistant")

# Get list of microphones
available_mics = sr.Microphone.list_microphone_names()
if not available_mics:
    available_mics = ["No Microphones Found"]

title_label = ctk.CTkLabel(app, text="Voice Assistant", font=("Arial", 24, "bold"))
title_label.pack(pady=20)

app_log = ctk.CTkTextbox(app, width=450, height=350, font=("Arial", 14))
app_log.pack(pady=10)
app_log.insert(ctk.END, "System Ready...\n")

# NEW: Microphone Selection Label & Dropdown
mic_label = ctk.CTkLabel(app, text="Select Microphone:", font=("Arial", 12))
mic_label.pack(pady=(10, 0))

mic_dropdown = ctk.CTkOptionMenu(app, values=available_mics, width=300)
mic_dropdown.pack(pady=5)
# Set default to the first mic in the list
mic_dropdown.set(available_mics[0]) 

mic_button = ctk.CTkButton(app, text="🎤 Speak Now", font=("Arial", 16, "bold"), height=50, command=start_assistant)
mic_button.pack(pady=20)

# Run the app
app.mainloop()