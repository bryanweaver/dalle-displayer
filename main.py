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

    def setup_ui(self):
        window_width = 1792  # Set your desired window width
        window_height = 1000  # Full height of the screen

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
        self.text_label = tk.Label(self.control_frame, text="Enter Text:")
        self.text_label.pack(side=tk.LEFT, padx=5)
        self.text_entry = tk.Entry(self.control_frame, width=50)
        self.text_entry.pack(side=tk.LEFT, padx=5)

        # Generate button
        self.generate_button = tk.Button(self.control_frame, text="Generate Image", command=self.generate_image)
        self.generate_button.pack(side=tk.LEFT, padx=5)

        # Scrollable canvas setup
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))

        # Configure canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def display_image(self, photo, original_image):
        # Create a label with the image
        image_label = tk.Label(self.scrollable_frame, image=photo)
        image_label.image = photo
        image_label.pack(side=tk.TOP, padx=5, pady=5)

        # Scroll to the bottom of the canvas
        self.canvas.update_idletasks()  # Update the canvas to ensure it has the latest layout
        self.canvas.yview_moveto(1)  # 1 is the end of the scrollbar

        # Add a save button for the image
        save_button = tk.Button(self.control_frame, text="Save Image", command=lambda: self.save_image(original_image))
        save_button.pack(side=tk.TOP, pady=5)

    def save_image(self, image):
        file_path = fd.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")])
        if file_path:
            image.save(file_path)

    def generate_image(self):
        self.progress.start(10)  # The number here is the delay between updates in milliseconds.
        text = self.text_entry.get()
        # Update the loading label in the main thread
        self.loading_label.config(text="Generating image... Please wait.")
        
        # Show and start the progress bar
        self.progress.pack(side=tk.LEFT, padx=5, fill=tk.X)
        self.progress.start(10)
        
        # Start a background thread for the image generation task
        thread = threading.Thread(target=self.generate_image_thread, args=(text,))
        thread.start()


    def generate_image_thread(self, text):
        try:
            image_url = self.image_generator.generate_image(text)
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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    app = App(root)
    root.mainloop()
