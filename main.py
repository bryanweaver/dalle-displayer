import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from image_generator import ImageGenerator
import urllib
import io
from dotenv import load_dotenv
import settings

class App:
    def __init__(self, root):
        load_dotenv()
        self.root = root
        self.root.geometry("{}x{}".format(root.winfo_screenwidth(), root.winfo_screenheight()))
        self.root.title("DALL-E Image Generator")
        self.text_label = tk.Label(root, text="Enter Text:")
        self.text_label.pack()
        self.text_entry = tk.Entry(root)
        self.text_entry.pack()
        self.generate_button = tk.Button(root, text="Generate Image", command=self.generate_image)
        self.generate_button.pack()
    def generate_image(self):
        api_key = settings.API_KEY
        text = self.text_entry.get()
        try:
            image_generator = ImageGenerator(api_key)
            image_url = image_generator.generate_image(text)
            fd = urllib.request.urlopen(image_url)
            image_file = io.BytesIO(fd.read())
            image = Image.open(image_file)
            image = image.resize((root.winfo_screenwidth(), root.winfo_screenheight()))
            photo = ImageTk.PhotoImage(image)
            self.display_image(photo)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    def display_image(self, photo):
        image_label = tk.Label(root, image=photo)
        image_label.pack()
        image_label.image = photo
root = tk.Tk()
app = App(root)
root.mainloop()