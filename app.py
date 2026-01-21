from flask import Flask, render_template, request, send_file
import pdfplumber
from io import BytesIO
import requests
import os
from dotenv import load_dotenv  # ← Importa dotenv

# === CARICA VARIABILI D'AMBIENTE ===
load_dotenv()  # ← Carica il file .env

# === CONFIGURAZIONE API CEREBRAS ===
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")  # ← Leggi la variabile
CEREBRAS_ENDPOINT = "https://api.cerebras.ai/v1/chat/completions"

# === APP FLASK ===
app = Flask(__name__)

# === Funzione per estrarre testo dal PDF ===
def estrai_testo(pdf_file):
    testo = ""
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            testo += pagina.extract_text() + "\n"
    return testo

# === Funzione per riassumere testo tramite Cerebras ===
def riassumi_testo(testo, lunghezza="breve"):
    prompt = f"Riassumi questo testo in modo {lunghezza}:\n\n{testo}"

    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama3.1-8b",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        response = requests.post(CEREBRAS_ENDPOINT, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Errore API Cerebras: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Errore durante la chiamata API: {str(e)}"

# === Rotta principale ===
@app.route("/", methods=["GET", "POST"])
def index():
    testo_pdf = ""
    riassunto = ""
    if request.method == "POST":
        if "pdf_file" in request.files:
            pdf_file = request.files["pdf_file"]
            testo_pdf = estrai_testo(pdf_file)
            lunghezza = request.form.get("lunghezza", "breve")
            riassunto = riassumi_testo(testo_pdf, lunghezza)
    return render_template("index.html", testo_pdf=testo_pdf, riassunto=riassunto)

# === Rotta per scaricare il riassunto ===
@app.route("/download", methods=["POST"])
def download():
    riassunto = request.form.get("riassunto", "")
    if riassunto:
        buffer = BytesIO()
        buffer.write(riassunto.encode('utf-8'))
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="riassunto.txt", mimetype="text/plain")
    return "Nessun riassunto disponibile."

# === Avvio app ===
if __name__ == "__main__":
    app.run(debug=True)