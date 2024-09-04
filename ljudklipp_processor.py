import re
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import csv
import os
from collections import defaultdict
from fpdf import FPDF

def process_file(file_path):
    print(f"Processing file: {file_path}")  # Debug message
    with open(file_path, 'r') as file:
        text = file.read()

    clips = re.findall(r'(\d+)\s+(\d+)\s+(.+?)\s+(\d+:\d+:\d+):\d+\s+(\d+:\d+:\d+):\d+', text)
    clip_durations = defaultdict(int)
    total_duration_sec = 0

    for clip in clips:
        clip_name = clip[2]
        if '.grp' in clip_name:
            continue

        start_tid = clip[3]
        slut_tid = clip[4]

        start_tider = start_tid.split(':')
        slut_tider = slut_tid.split(':')
        start_sec = int(start_tider[0]) * 3600 + int(start_tider[1]) * 60 + int(start_tider[2])
        slut_sec = int(slut_tider[0]) * 3600 + int(slut_tider[1]) * 60 + int(slut_tider[2])
        duration_sec = slut_sec - start_sec

        total_duration_sec += duration_sec

        ljudfil = clip_name.replace('_', ' ').replace('-', ' ')
        ljudfil = re.sub(r'(?<=\s)\d+(?=\.\w+$|\s*$)', '', ljudfil)
        ljudfil = re.sub(r'\.\w+$', '', ljudfil)
        ljudfil = re.sub(r'\bSTEMS\b.*', '', ljudfil)
        ljudfil = ' '.join(ljudfil.split())

        clip_durations[ljudfil] += duration_sec

    result = []
    for ljudfil, total_sec in clip_durations.items():
        duration_hours = total_sec // 3600
        duration_minutes = (total_sec % 3600) // 60
        duration_seconds = total_sec % 60
        duration_format = f"{duration_hours:02d}:{duration_minutes:02d}:{duration_seconds:02d}"
        result.append((ljudfil, duration_format))

    total_duration_hours = total_duration_sec // 3600
    total_duration_minutes = (total_duration_sec % 3600) // 60
    total_duration_seconds = total_duration_sec % 60
    total_duration_format = f"{total_duration_hours:02d}:{total_duration_minutes:02d}:{total_duration_seconds:02d}"
    result.append(("Total Duration", total_duration_format))

    print(f"Processed file with {len(result)} entries.")  # Debug message
    return result

def open_file():
    global file_path
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        result = process_file(file_path)
        for row in tree.get_children():
            tree.delete(row)
        for row in result:
            tree.insert("", "end", values=row)
        print(f"File opened: {file_path}")  # Debug message

def save_to_csv():
    if not file_path:
        print("No file selected")  # Debug message
        return
    save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not save_path:
        return
    result = process_file(file_path)

    with open(save_path, 'w', newline='') as csvfile:
        fieldnames = ['Ljudfil', 'Längd']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in result:
            writer.writerow({'Ljudfil': row[0], 'Längd': row[1]})
    print(f"CSV file saved: {save_path}")  # Debug message

def save_to_pdf():
    if not file_path:
        print("No file selected")  # Debug message
        return
    save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    if not save_path:
        return
    result = process_file(file_path)
    filename = os.path.basename(file_path).replace('.txt', '')

    max_width = max(len(row[0]) for row in result) * 2

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"{filename} - Musikrapport", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    pdf.cell(max_width, 10, txt="Ljudfil", border=1)
    pdf.cell(40, 10, txt="Längd", border=1)
    pdf.ln()

    for row in result:
        pdf.cell(max_width, 10, txt=row[0], border=1)
        pdf.cell(40, 10, txt=row[1], border=1)
        pdf.ln()

    pdf.output(save_path)
    print(f"PDF file saved: {save_path}")  # Debug message

def on_tree_click(event):
    global selected_column
    region = tree.identify("region", event.x, event.y)
    if region == "cell":
        column = tree.identify_column(event.x)
        selected_column = column

def copy_selection(event):
    selected_items = tree.selection()
    if not selected_items:
        return
    copied_text = ""
    for item in selected_items:
        values = tree.item(item, "values")
        col_index = int(selected_column.replace("#", "")) - 1
        copied_text += values[col_index] + "\n"
    root.clipboard_clear()
    root.clipboard_append(copied_text)

root = tk.Tk()
root.title("Ljudklipp Processor")
root.geometry("800x600")

frame = tk.Frame(root)
frame.pack(pady=10)

open_button = tk.Button(frame, text="Välj fil", command=open_file)
open_button.pack(side=tk.LEFT, padx=10)

save_button = tk.Button(frame, text="Spara till CSV", command=save_to_csv)
save_button.pack(side=tk.LEFT, padx=10)

pdf_button = tk.Button(frame, text="Spara till PDF", command=save_to_pdf)
pdf_button.pack(side=tk.LEFT, padx=10)

columns = ("ljudfil", "längd")
tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="extended")
tree.heading("ljudfil", text="Ljudfil")
tree.heading("längd", text="Längd")
tree.pack(expand=True, fill=tk.BOTH, pady=10)

tree.bind("<ButtonRelease-1>", on_tree_click)
root.bind("<Control-c>", copy_selection)

selected_column = "#1"
file_path = ""

root.mainloop()
