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


class App:
    def __init__(self, root):
        load_dotenv()
        self.root = root
        self.setup_ui()
        self.image_generator = ImageGenerator(settings.API_KEY)

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

        # Text label and entry
        self.entry_frame = tk.Frame(self.control_frame)
        self.entry_frame.pack(side=tk.BOTTOM, padx=5, pady=5)

        self.text_label = tk.Label(self.entry_frame, text="Enter Text:")
        self.text_label.pack(in_=self.entry_frame, side=tk.LEFT, padx=5)
        self.text_entry = tk.Entry(self.entry_frame, width=100)
        self.text_entry.pack(in_=self.entry_frame, side=tk.LEFT, padx=5, pady=5)

        # Generate button
        self.generate_button = tk.Button(self.entry_frame, text="Generate Image", command=self.generate_image)
        self.generate_button.pack(in_=self.entry_frame, padx=5)

        # Image display setup
        self.image_label = None


    def display_image(self, photo, original_image):
        # Remove the previous image label if it exists
        if self.image_label is not None:
            self.image_label.destroy()
            self.image_label = None
        
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

    def save_image(self, image):
        if self.selected_image:
            file_path = fd.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")])
            if file_path:
                self.selected_image.save(file_path)

    def generate_image(self):
        self.progress.start(10)  # The number here is the delay between updates in milliseconds.
        text = self.text_entry.get()
        # Update the loading label in the main thread
        self.loading_label.config(text="Generating image... Please wait.")
        
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
        except Exception as e:
            logging.error("Error in generating image: ", exc_info=True)
            messagebox.showerror("Error", str(e))
        finally:
            # Stop and hide the progress bar
            self.root.after(0, self.progress.stop)
            self.root.after(0, self.progress.pack_forget)
            # Clear the loading label in the main thread
            self.root.after(0, self.loading_label.config, {"text": ""})

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
