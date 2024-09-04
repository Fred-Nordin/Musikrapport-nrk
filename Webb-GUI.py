import re
import csv
import os
from collections import defaultdict
from fpdf import FPDF
from flask import Flask, request, render_template, send_file, redirect, url_for
from io import BytesIO

app = Flask(__name__)


# Funktion för att bearbeta filen, samma som tidigare
def process_file(file_content):
    text = file_content.decode('utf-8')

    # Extrahera ljudklippen från texten
    clips = re.findall(r'(\d+)\s+(\d+)\s+(.+?)\s+(\d+:\d+:\d+):\d+\s+(\d+:\d+:\d+):\d+', text)

    # Håll reda på summan av längder för varje ljudklipp
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

    return result


# Route för att visa formulär och resultat
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part", 400

        file = request.files["file"]
        if file.filename == "":
            return "No selected file", 400

        result = process_file(file.read())
        return render_template("index.html", result=result)

    return render_template("index.html", result=None)


# Route för att spara som CSV
@app.route("/save_csv", methods=["POST"])
def save_csv():
    result = request.form.getlist('result[]')
    csv_output = BytesIO()

    writer = csv.writer(csv_output)
    writer.writerow(['Ljudfil', 'Längd'])
    for row in result:
        writer.writerow(row.split(','))

    csv_output.seek(0)
    return send_file(csv_output, mimetype='text/csv', as_attachment=True, download_name='output.csv')


# Route för att spara som PDF
@app.route("/save_pdf", methods=["POST"])
def save_pdf():
    result = request.form.getlist('result[]')
    pdf_output = BytesIO()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Musikrapport", ln=True, align='C')

    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    pdf.cell(100, 10, txt="Ljudfil", border=1)
    pdf.cell(40, 10, txt="Längd", border=1)
    pdf.ln()

    for row in result:
        ljudfil, längd = row.split(',')
        pdf.cell(100, 10, txt=ljudfil, border=1)
        pdf.cell(40, 10, txt=längd, border=1)
        pdf.ln()

    pdf.output(pdf_output)
    pdf_output.seek(0)
    return send_file(pdf_output, mimetype='application/pdf', as_attachment=True, download_name='output.pdf')


if __name__ == "__main__":
    app.run(debug=True)
