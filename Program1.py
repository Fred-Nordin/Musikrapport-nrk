import re
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import csv
import os
from collections import defaultdict
from fpdf import FPDF


def process_file(file_path):
    # Läs in textfilen
    with open(file_path, 'r') as file:
        text = file.read()

    # Extrahera ljudklippen från texten
    clips = re.findall(r'(\d+)\s+(\d+)\s+(.+?)\s+(\d+:\d+:\d+):\d+\s+(\d+:\d+:\d+):\d+', text)

    # Håll reda på summan av längder för varje ljudklipp
    clip_durations = defaultdict(int)
    total_duration_sec = 0

    for clip in clips:
        clip_name = clip[2]

        # Skip clips with '.grp' in the name
        if '.grp' in clip_name:
            continue

        start_tid = clip[3]
        slut_tid = clip[4]

        # Beräkna längden i sekunder
        start_tider = start_tid.split(':')
        slut_tider = slut_tid.split(':')
        start_sec = int(start_tider[0]) * 3600 + int(start_tider[1]) * 60 + int(start_tider[2])
        slut_sec = int(slut_tider[0]) * 3600 + int(slut_tider[1]) * 60 + int(slut_tider[2])
        duration_sec = slut_sec - start_sec

        # Lägg till till den totala längden
        total_duration_sec += duration_sec

        # Bearbeta ljudfilens namn
        ljudfil = clip_name.replace('_', ' ').replace('-', ' ')
        ljudfil = re.sub(r'(?<=\s)\d+(?=\.\w+$|\s*$)', '',
                         ljudfil)  # Ta bort siffror före punkten efter ett mellanslag eller vid slutet av strängen
        ljudfil = re.sub(r'\.\w+$', '', ljudfil)  # Ta bort punkten och allt som följer efter den
        ljudfil = re.sub(r'\bSTEMS\b.*', '', ljudfil)  # Ta bort ordet STEMS och allt efter
        ljudfil = ' '.join(ljudfil.split())  # Ta bort överflödiga mellanslag

        # Lägg till längden till den aktuella ljudfilens totala längd
        clip_durations[ljudfil] += duration_sec

    result = []
    for ljudfil, total_sec in clip_durations.items():
        # Konvertera den totala längden till formatet "HH:MM:SS"
        duration_hours = total_sec // 3600
        duration_minutes = (total_sec % 3600) // 60
        duration_seconds = total_sec % 60
        duration_format = f"{duration_hours:02d}:{duration_minutes:02d}:{duration_seconds:02d}"

        result.append((ljudfil, duration_format))

    # Lägg till total längd för alla ljudklipp
    total_duration_hours = total_duration_sec // 3600
    total_duration_minutes = (total_duration_sec % 3600) // 60
    total_duration_seconds = total_duration_sec % 60
    total_duration_format = f"{total_duration_hours:02d}:{total_duration_minutes:02d}:{total_duration_seconds:02d}"

    result.append(("Total Duration", total_duration_format))

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

    # Save as CSV
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

    # Calculate the width of column A
    max_width = max(len(row[0]) for row in result) * 2  # Adjust factor as needed

    # Save as PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"{filename} - Musikrapport", ln=True, align='C')

    pdf.ln(10)

    # Column headers
    pdf.set_font("Arial", size=10)
    pdf.cell(max_width, 10, txt="Ljudfil", border=1)
    pdf.cell(40, 10, txt="Längd", border=1)
    pdf.ln()

    # Add rows
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


# Create the main window
root = tk.Tk()
root.title("Ljudklipp Processor")

# Set the size of the window
root.geometry("800x600")

# Create a frame for the file selection
frame = tk.Frame(root)
frame.pack(pady=10)

# Add a button to open the file dialog
open_button = tk.Button(frame, text="Välj fil", command=open_file)
open_button.pack(side=tk.LEFT, padx=10)

# Add a button to save the output to a CSV file
save_button = tk.Button(frame, text="Spara till CSV", command=save_to_csv)
save_button.pack(side=tk.LEFT, padx=10)

# Add a button to save the output to a PDF file
pdf_button = tk.Button(frame, text="Spara till PDF", command=save_to_pdf)
pdf_button.pack(side=tk.LEFT, padx=10)

# Create a treeview widget to display the output
columns = ("ljudfil", "längd")
tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="extended")
tree.heading("ljudfil", text="Ljudfil")
tree.heading("längd", text="Längd")
tree.pack(expand=True, fill=tk.BOTH, pady=10)

# Bind the treeview click event to track the selected column
tree.bind("<ButtonRelease-1>", on_tree_click)

# Bind the Ctrl+C shortcut to the copy function
root.bind("<Control-c>", copy_selection)

# Initialize the selected column
selected_column = "#1"

# Initialize the file path
file_path = ""

# Run the main event loop
root.mainloop()
