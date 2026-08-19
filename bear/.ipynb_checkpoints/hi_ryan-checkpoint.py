import tkinter as tk
from PIL import Image, ImageTk
import random

def shake(event):
    # Move the image to a random nearby position
    x = random.randint(-10, 10)
    y = random.randint(-10, 10)
    canvas.move(img_obj, x, y)

root = tk.Tk()
root.title("Shaking Image")

# Load image
image = Image.open("bear.jpg")   # Replace with your file
photo = ImageTk.PhotoImage(image)

canvas = tk.Canvas(root, width=image.width, height=image.height)
canvas.pack()

# Display image
img_obj = canvas.create_image(0, 0, anchor="nw", image=photo)

# Bind click event
canvas.bind("<Button-1>", shake)

root.mainloop()