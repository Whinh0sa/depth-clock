import tkinter as tk
import os

root = tk.Tk()
root.title("Tkinter Font Scaling Demo")
root.geometry("600x400")
canvas = tk.Canvas(root, width=600, height=400, bg='#2c3e50')
canvas.pack()

# Tkinter point-based font (buggy scaling based on OS DPI)
canvas.create_text(300, 100, text="Point Scaled Font (Buggy)", font=("Arial", 25, "bold"), fill="#e74c3c")
canvas.create_text(300, 150, text="font=('Arial', 25)", font=("Arial", 12), fill="#ecf0f1")

# Tkinter pixel-based font (fixed scaling, matches PIL)
canvas.create_text(300, 250, text="Pixel Scaled Font (Fixed)", font=("Arial", -25, "bold"), fill="#2ecc71")
canvas.create_text(300, 300, text="font=('Arial', -25)", font=("Arial", 12), fill="#ecf0f1")

root.update()
