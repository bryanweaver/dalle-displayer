import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from image_generator import ImageGenerator
import urllib.request
import io
from dotenv import load_dotenv
import settings
import logging
import threading
import tkinter.filedialog as fd
import speech_recognition as sr

class App:
    def __init__(self, root):
        load_dotenv()
        self.root = root
        self.setup_ui()
        self.setup_voice_recognition()
        self.start_listening_thread()
        self.image_generator = ImageGenerator(settings.API_KEY)

    def reset_application(self):
        # Reset the application to its initial state
        self.text_var.set("")
        if self.image_label is not None:
            self.image_label.destroy()
            self.image_label = None
        self.start_listening_thread()  # Start listening for the wake word again

    def start_listening_thread(self):
        # Start a new thread for continuous listening
        thread = threading.Thread(target=self.listen_for_wake_word)
        thread.daemon = True
        thread.start()

    def listen_for_wake_word(self):
        while True:  # Continuous loop
            self.root.after(0, lambda: self.update_loading_label("Listening for wake word..."))
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, phrase_time_limit=2)  # Listen for 2 seconds

            # Process the captured audio
            try:
                text = self.recognizer.recognize_sphinx(audio)
                if "hello" in text.lower():  # Replace with your actual wake word
                    self.root.after(0, lambda: self.update_loading_label("Wake word detected. Listening for command..."))
                    self.start_speech_recognition()
                    break  # Exit the loop once the wake word is detected
                if "clear" in text.lower():
                    self.root.after(0, lambda: self.reset_application())
                    break
            except sr.UnknownValueError:
                pass  # Ignore if the wake word is not detected
            except sr.RequestError as e:
                self.root.after(0, lambda: self.update_loading_label(f"Error: {e}"))

    def setup_voice_recognition(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
    def start_speech_recognition(self):
        with self.microphone as source:
            self.update_loading_label("Say something!")
            # self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(source, timeout=5)  # 5 seconds silence timeout

            # Recognize speech using Sphinx
            try:
                text = self.recognizer.recognize_sphinx(audio)
                self.update_loading_label(f"I think you said: {text}")
                self.apply_text_to_ui(text)
            except sr.UnknownValueError:
                self.update_loading_label("Sphinx could not understand audio")
            except sr.RequestError as e:
                self.update_loading_label(f"Sphinx error; {e}")

    def update_loading_label(self, message):
        # Use after method to ensure this runs in the main thread
        self.root.after(0, lambda: self.loading_label.config(text=message))

    def apply_text_to_ui(self, text):
        self.text_var.set(text)
        self.generate_image()

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Save Image", command=lambda: self.save_image(self.selected_image))

    def setup_ui(self):
        window_width = 1792  # Set your desired window width
        window_height = 1000  # Full height of the screen

        self.selected_image = None
        self.create_context_menu()

        # Calculate x and y coordinates for the Tk root window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Center the window
        center_x = int((screen_width - window_width) / 2)
        top_y = int(screen_height * 0.0005)

        # Set the dimensions and position
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{top_y}")
        self.root.title("DALL-E Image Generator")

        # UI controls setup
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # set up download progress bar
        self.progress = ttk.Progressbar(self.control_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
        
        # Add a loading label
        self.loading_label = tk.Label(self.control_frame, text="")
        self.loading_label.pack(side=tk.BOTTOM, padx=5)

        # Create a StringVar instance for the text entry
        self.text_var = tk.StringVar()

        # Text Area
        self.entry_frame = tk.Frame(self.control_frame)
        self.entry_frame.pack(side=tk.BOTTOM, padx=5, pady=5)


        # Text label and entry
        self.text_label = tk.Label(self.entry_frame, text="Enter Text:")
        self.text_label.pack(in_=self.entry_frame, side=tk.LEFT, padx=5)
        self.text_entry = tk.Entry(self.entry_frame, width=100, textvariable=self.text_var)
        self.text_entry.pack(in_=self.entry_frame, side=tk.LEFT, padx=5, pady=5)
        self.text_entry.focus_set()

        # Generate button
        self.generate_button = tk.Button(self.entry_frame, text="Generate Image", command=self.generate_image)
        self.generate_button.pack(in_=self.entry_frame, padx=5)

        # Callback function to enable/disable the generate button
        def update_button_state(*args):
            text = self.text_var.get()
            if text:
                self.generate_button['state'] = 'normal'
            else:
                self.generate_button['state'] = 'disabled'

        # Trace changes in the text entry
        self.text_var.trace_add('write', update_button_state)

        # Set initial state of the generate button
        update_button_state()

        # Image display setup
        self.image_label = None

        # Bind the Enter key to the same command as the generate_button
        self.root.bind('<Return>', lambda event=None: self.generate_image())

    def display_image(self, photo, original_image):
        # Remove the previous image label if it exists
        if self.image_label is not None:
            self.image_label.destroy()
            self.image_label = None
        
        # Resize the image to fit the window
        screen_width = self.root.winfo_width()
        screen_height = self.root.winfo_height() - self.control_frame.winfo_height()

        # Resize the original image while maintaining aspect ratio
        original_image.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(original_image)

        # Create a label with the image
        self.image_label = tk.Label(self.root, image=photo)
        self.image_label.image = photo
        self.image_label.pack(side=tk.TOP, padx=5, pady=5)

         # Bind right-click event
        self.image_label.bind("<Button-3>", lambda event, img=original_image: self.on_right_click(event, img))

        self.selected_image = original_image
        # # Add a save button for the image
        # save_button = tk.Button(self.control_frame, text="Save Image", command=lambda: self.save_image(original_image))
        # save_button.pack(side=tk.TOP, pady=5)

        # Bind click event to the image to toggle control area visibility
        self.image_label.bind("<Button-1>", self.toggle_controls)
        self.start_listening_thread()

    def toggle_controls(self, event=None):
        # Check if the control frame is currently visible
        if self.control_frame.winfo_ismapped():
            self.control_frame.pack_forget()  # Hide if visible
        else:
            self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)  # Show if not visible

    def save_image(self, image):
        if self.selected_image:
            file_path = fd.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")])
            if file_path:
                self.selected_image.save(file_path)

    def generate_image(self):
        self.generate_button['state'] = 'disabled'
        self.progress.start(10)  # The number here is the delay between updates in milliseconds.
        text = self.text_entry.get()
        # Update the loading label in the main thread
        self.update_loading_label("Generating image... Please wait.")
        
        # Show and start the progress bar
        self.progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.progress.start(10)
        
        # Start a background thread for the image generation task
        thread = threading.Thread(target=self.generate_image_thread, args=(text,))
        thread.start()

    def generate_image_thread(self, text):
        try:
            image_url, error = self.image_generator.generate_image(text)
            if error:
                self.root.after(0, lambda: messagebox.showerror("Error", error))
            elif image_url:
                with urllib.request.urlopen(image_url) as fd:
                    image_file = io.BytesIO(fd.read())
                    image = Image.open(image_file)
                    photo = ImageTk.PhotoImage(image)
                    # Schedule the display_image method to run in the main thread
                    self.root.after(0, lambda: self.display_image(photo, image))
                    self.root.after(0, lambda: self.generate_button.config(state='normal'))
        except Exception as e:
            logging.error("Error in generating image: ", exc_info=True)
            messagebox.showerror("Error", str(e))
        finally:
            # Stop and hide the progress bar
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.progress.pack_forget)
            # Clear the loading label in the main thread
            self.root.after(0, self.loading_label.config, {"text": ""})
            self.root.after(0, lambda: self.control_frame.pack(side=tk.BOTTOM, fill=tk.X))

    def on_right_click(self, event, image):
        self.selected_image = image  # Store the reference to the clicked image
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    app = App(root)
    root.mainloop()
