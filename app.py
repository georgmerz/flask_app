import os
from flask import (Flask, redirect, render_template, request, send_from_directory, url_for, jsonify)
from werkzeug.utils import secure_filename
import docx
from openai import OpenAI
import json


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
client = OpenAI()

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def extract_text_from_docx(filepath):
    doc = docx.Document(filepath)
    return '\n'.join([para.text for para in doc.paragraphs])

def get_chatgpt_response(doc_text):

    medical_report_custom_function = [
    {
    "name": "fill_out_structured_template",
    "description": "Verarbeitet einen medizinischen Befund zu Pankreaskarzinomen und erstellt einen strukturierten Befund.",
    "parameters": {
        "type": "object",
        "properties": {
            "ct_pankcas_clininfo": {
                "type": "string",
                "description": "Klinische Angaben (z.B. Symptome, relevante Vorgeschichte)."
            },
            "ct_pankcas_Fragestellung": {
                "type": "string",
                "description": "Kurzbeschreibung der medizinischen Fragestellung des Befundes."
            },
            "ct_pankcas_comparison": {
                "type": "string",
                "description": "Gibt an, ob Vergleichsuntersuchungen vorliegen ('keine' oder 'vorliegend')."
            },
            "ct_pankcas_comparison_mod": {
                "type": "string",
                "description": "Typ der Vergleichsuntersuchung ('-', 'CT', 'MR')."
            },
            "ct_pankcas_comparison_date": {
                "type": "string",
                "description": "Datum der Vergleichsuntersuchung im Format 'YYYY-MM-DD' (nur ausfüllen, wenn Vergleichsuntersuchung vorliegt)."
            },
            "ct_pankcas_histo": {
                "type": "string",
                "description": "Status der Histologie ('-', 'ausstehend', 'nachgewiesen')."
            },
            "ct_pankcas_igg4": {
                "type": "string",
                "description": "IgG4-Status ('-', 'positiv', 'negativ')."
            },
            "ct_pankcas_quality": {
                "type": "string",
                "description": "Qualität der Bildgebung ('exzellent', 'mittel', 'schlecht')."
            },
            "ct_pankcas_parenchym": {
                "type": "string",
                "description": "Zustand des Pankreasparenchyms ('normal', 'lipotroph', 'ödematös', 'chron. Pankreatitis')."
            },
            "ct_pankcas_loc": {
                "type": "string",
                "description": "Tumorlokalisation ('-', 'Pankreaskopf', 'Pankreasschwanz', 'Pankreaskörper', 'Proc. uncinatus')."
            },
            "ct_pankcas_size_1": {
                "type": "number",
                "description": "Tumorgröße (Länge in cm)."
            },
            "ct_pankcas_size_2": {
                "type": "number",
                "description": "Tumorgröße (Breite in cm)."
            },
            "ct_pankcas_size_ima": {
                "type": "integer",
                "description": "Bildnummer der Tumorgröße."
            },
            "ct_pankcas_size_series": {
                "type": "integer",
                "description": "Seriennummer der Tumorgröße."
            },
            "ct_pankcas_tstage": {
                "type": "string",
                "description": "Tumorstadium nach TNM-Klassifikation ('-', 'T1: ≤ 2cm (T1a: ≤ 0,5 cm / T1b < 1 cm / T1c: ≤ 2 cm)', 'T2: ≤ 4 cm', 'T3: > 4 cm', 'T4: Gefäßinfiltration (>180°)')."
            },
            "ct_pankcas_tstage_ima": {
                "type": "integer",
                "description": "Bildnummer des Tumorstadiums."
            },
            "ct_pankcas_tstage_series": {
                "type": "integer",
                "description": "Seriennummer des Tumorstadiums."
            },
            "ct_pankcas_tstage_desc": {
                "type": "string",
                "description": "Beschreibung der Infiltration."
            },
            "ct_pankcas_enhance_art": {
                "type": "string",
                "description": "KM-Enhancement im arteriellen Phase ('-', 'hypodens', 'isodens', 'hyperdens')."
            },
            "ct_pankcas_enhance_ven": {
                "type": "string",
                "description": "KM-Enhancement im venösen Phase ('-', 'hypodens', 'isodens', 'hyperdens')."
            },
            "ct_pankcas_pancduct": {
                "type": "string",
                "description": "Ductus pancreaticus Zustand ('-', 'unauffällig', 'dilatiert')."
            },
            "ct_pankcas_pancduct_text": {
                "type": "string",
                "description": "Beschreibung des Ductus pancreaticus."
            },
            "ct_pankcas_dhc": {
                "type": "string",
                "description": "Zustand des Ductus hepatocholedochus ('-', 'unauffällig', 'dilatiert')."
            },
            "ct_pankcas_dhc_text": {
                "type": "string",
                "description": "Beschreibung des Ductus hepatocholedochus."
            },
            "ct_pankcas_aorta": {
                "type": "string",
                "description": "Befall der Aorta ('nein', '< 180°', '> 180°', '360°', 'Deformierung')."
            },
            "ct_pankcas_trcoeliacus": {
                "type": "string",
                "description": "Befall des Truncus coeliacus ('nein', '< 180°', '> 180°', '360°', 'Deformierung')."
            },
            "ct_pankcas_ahepcom": {
                "type": "string",
                "description": "Befall der A. hepatica communis ('nein', '< 180°', '> 180°', '360°', 'Deformierung')."
            },
            "ct_pankcas_vms": {
                "type": "string",
                "description": "Befall der V. mesenterica superior ('nein', '< 180°', '> 180°', '360°', 'Deformierung', '1. Jejunalast infiltriert')."
            },
            "ct_pankcas_vlien": {
                "type": "string",
                "description": "Befall der V. lienalis ('nein', '< 180°', '> 180°', '360°', 'Deformierung')."
            },
            "ct_pankcas_vport": {
                "type": "string",
                "description": "Befall der V. portae ('nein', '< 180°', '> 180°', '360°', 'Deformierung')."
            },
            "ct_pankcas_aszites": {
                "type": "string",
                "description": "Vorhandensein von Aszites ('nein', 'wenig', 'ausgeprägt')."
            },
            "ct_pankcas_aszites_text": {
                "type": "string",
                "description": "Beschreibung des Aszites."
            },
            "ct_pankcas_peritoneum": {
                "type": "string",
                "description": "Vorhandensein von peritonealen Implantaten ('nein', 'ja')."
            },
            "ct_pankcas_peritoneum_text": {
                "type": "string",
                "description": "Beschreibung der peritonealen Implantate."
            },
            "ct_pankcas_leber": {
                "type": "string",
                "description": "Zustand der Leber ('nein', 'Lebermetastasen', 'sonstiges')."
            },
            "ct_pankcas_leber_text": {
                "type": "string",
                "description": "Beschreibung des Leberzustands."
            },
            "ct_pankcas_milz": {
                "type": "string",
                "description": "Zustand der Milz ('unauffällig', 'auffällig')."
            },
            "ct_pankcas_milz_text": {
                "type": "string",
                "description": "Beschreibung der Milz (falls auffällig)."
            },
            "ct_pankcas_nieren": {
                "type": "string",
                "description": "Zustand der Nieren/Ureteren ('unauffällig', 'auffällig')."
            },
            "ct_pankcas_nieren_text": {
                "type": "string",
                "description": "Beschreibung der Nieren/Ureteren (falls auffällig)."
            },
            "ct_pankcas_nnieren": {
                "type": "string",
                "description": "Zustand der Nebennieren ('unauffällig', 'auffällig')."
            },
            "ct_pankcas_nnieren_text": {
                "type": "string",
                "description": "Beschreibung der Nebennieren (falls auffällig)."
            },
            "ct_pankcas_lymph": {
                "type": "string",
                "description": "Zustand der Lymphknoten ('unauffällig', 'auffällig')."
            },
            "ct_pankcas_lymph_text": {
                "type": "string",
                "description": "Beschreibung der Lymphknoten (falls auffällig)."
            },
            "ct_pankcas_darm": {
                "type": "string",
                "description": "Zustand des Darms ('unauffällig', 'auffällig')."
            },
            "ct_pankcas_darm_text": {
                "type": "string",
                "description": "Beschreibung des Darms (falls auffällig)."
            },
            "ct_pankcas_becken": {
                "type": "string",
                "description": "Zustand der Beckenorgane ('unauffällig', 'auffällig')."
            },
            "ct_pankcas_becken_text": {
                "type": "string",
                "description": "Beschreibung der Beckenorgane (falls auffällig)."
            },
            "ct_pankcas_knochen": {
                "type": "string",
                "description": "Zustand der Knochen ('unauffällig', 'auffällig')."
            },
            "ct_pankcas_knochen_text": {
                "type": "string",
                "description": "Beschreibung der Knochen (falls auffällig)."
            },
            "ct_pankcas_lunge": {
                "type": "string",
                "description": "Zustand der Lunge (sofern mit erfasst) ('unauffällig', 'auffällig')."
            },
            "ct_pankcas_lunge_text": {
                "type": "string",
                "description": "Beschreibung der Lunge (falls auffällig)."
            },
            "ct_pankcas_sonstiges": {
                "type": "string",
                "description": "Sonstige relevante Befunde."
            },
            "ct_pankcas_Beurteilung": {
                "type": "string",
                "description": "Gesamtbewertung nach Schema (z.B. 'V.a. Pankreas-Ca im ...')."
            },
            "ct_pankcas_TNM": {
                "type": "string",
                "description": "Gesamtbeurteilung nach TNM-Klassifikation."
            },
            "ct_pankcas_certainty": {
                "type": "string",
                "description": "Bewertungssicherheit ('-', '5 - sehr sicher', '4 - sicher', '3 - indifferent', '2 - unsicher', '1 - sehr unsicher')."
            }
        },
        "required": [
            "ct_pankcas_clininfo",
            "ct_pankcas_Fragestellung",
            "ct_pankcas_comparison",
            "ct_pankcas_comparison_mod",
            "ct_pankcas_comparison_date",
            "ct_pankcas_histo",
            "ct_pankcas_igg4",
            "ct_pankcas_quality",
            "ct_pankcas_parenchym",
            "ct_pankcas_loc",
            "ct_pankcas_size_1",
            "ct_pankcas_size_2",
            "ct_pankcas_size_ima",
            "ct_pankcas_size_series",
            "ct_pankcas_tstage",
            "ct_pankcas_tstage_ima",
            "ct_pankcas_tstage_series",
            "ct_pankcas_tstage_desc",
            "ct_pankcas_enhance_art",
            "ct_pankcas_enhance_ven",
            "ct_pankcas_pancduct",
            "ct_pankcas_pancduct_text",
            "ct_pankcas_dhc",
            "ct_pankcas_dhc_text",
            "ct_pankcas_aorta",
            "ct_pankcas_trcoeliacus",
            "ct_pankcas_ahepcom",
            "ct_pankcas_vms",
            "ct_pankcas_vlien",
            "ct_pankcas_vport",
            "ct_pankcas_aszites",
            "ct_pankcas_aszites_text",
            "ct_pankcas_peritoneum",
            "ct_pankcas_peritoneum_text",
            "ct_pankcas_leber",
            "ct_pankcas_leber_text",
            "ct_pankcas_milz",
            "ct_pankcas_milz_text",
            "ct_pankcas_nieren",
            "ct_pankcas_nieren_text",
            "ct_pankcas_nnieren",
            "ct_pankcas_nnieren_text",
            "ct_pankcas_lymph",
            "ct_pankcas_lymph_text",
            "ct_pankcas_darm",
            "ct_pankcas_darm_text",
            "ct_pankcas_becken",
            "ct_pankcas_becken_text",
            "ct_pankcas_knochen",
            "ct_pankcas_knochen_text",
            "ct_pankcas_lunge",
            "ct_pankcas_lunge_text",
            "ct_pankcas_sonstiges",
            "ct_pankcas_Beurteilung",
            "ct_pankcas_TNM",
            "ct_pankcas_certainty"
        ]
    }
}

]





    messages = [
        {"role": "system", "content": "Du bist ein Radiologe der einen Freitextbefund von einem möglichen Pankreaskarzinom in einen strukturierten Befund übersetzen will."},
        {"role": "user", "content": f"Das ist der Freitextbefund, den du in eine strukturiertes Format (JSon) mittels Function calling übersetzt werden sollst. ('strukturierte Befundung') \n\n{doc_text}.  Fülle alle Felder aus. Versuche dich dabei im Wortlaut an den Freitext zu halten. Bitte nur Aussagen machen die auch explizit im Befund stehen. Ansonsten gerne mit '-' antworten. Bitte Begründung bei Organen nur geben falls Auffällig."}
    ]
    

    response = client.chat.completions.create(
        model="gpt-4o",
        functions = medical_report_custom_function,
        function_call = 'auto',# force json format
        response_format={ "type": "json_object" },
        messages=messages
        
    )
   #response= response.choices[0].message.function_call.arguments
   # messages = [
   #     {"role": "system", "content": "Du bist ein Radiologe der einen Freitextbefund von einem möglichen Pankreaskarzinom in einen strukturierten Befund übersetzt hat."},
   #     {"role": "user", "content": f"Das ist der Freitextbefund, den du in eine strukturiertes Format (JSon) mittels Function calling übersetzt werden sollst. ('strukturierte Befundung') \n\n{doc_text}.  Das ist aktuell dein Ergebnis des JSON Befundes: \n\n{response}. Bitte versuche das Ergebnis zu verbessern und auf Konsistenzen zu prüfen. Ergebnis sollte wieder ein JSON sein."}
   # ]
    #response = client.chat.completions.create(
    #    model="gpt-4o",
    #    functions = medical_report_custom_function,
    #    function_call = 'auto',
    #    response_format={ "type": "json_object" },
    #    messages=messages
    #)


    return response.choices[0].message.function_call.arguments

@app.route('/')
def index():
    print('Request for index page received')
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        print('No file part in the request')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        print('No selected file')
        return redirect(url_for('index'))
    
    if file and file.filename.endswith('.docx'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f'File {filename} saved successfully')
        
        # Extract text from DOCX file
        doc_text = extract_text_from_docx(filepath)
        
        # Get response from ChatGPT
        chatgpt_response = get_chatgpt_response(doc_text)
        print(chatgpt_response)
        # convert to json object not a string
        chatgpt_response = json.loads(chatgpt_response)








        
        return render_template('display.html', content=chatgpt_response)
    else:
        print('Invalid file type')
        return redirect(url_for('index'))


@app.route('/process_form', methods=['POST'])
def process_form():
    data = request.json
    print(data)
    # Process the data as needed
    
    return jsonify(data)



structured_scheme = """
Du bist ein Arzt der einen Freitextbefund in ein strukturiertes Format umwandeln soll.
Bitte übersetze den Befund in folgendes Schema:
wobei du den Wert value einsetzen musst aus den Befundtext:
{
  "resourceType": "Questionnaire",
  "title": "CT Pankreaskarzinom (solide)",
  "item": [
    {
      "text": "Klinische Angaben",
      "type": "string",
      "value": "Z.n. Akuter und chronischer Pankreatitis",
      "id": "ct_pankcas_clininfo"
    },
    {
      "text": "Fragestellung",
      "type": "string",
      "value": "Pankreaskarzinom? arteriell/ portalvenös",
      "id": "ct_pankcas_Fragestellung"
    },
    {
      "text": "Befund",
      "type": "group",
      "item": [
        {
          "text": "Vergleichsuntersuchung",
          "type": "choice",
          "answerOption": ["keine", "vorliegend"],
          "value": "vorliegend",
          "id": "ct_pankcas_comparison"
        },
        {
          "text": "Vergleichsuntersuchung Typ",
          "type": "choice",
          "answerOption": ["-", "CT", "MR"],
          "value": "CT",
          "id": "ct_pankcas_comparison_mod"
        },
        {
          "text": "Datum der Untersuchung",
          "type": "date",
          "value": "2023-10-18",
          "id": "ct_pankcas_comparison_date"
        },
        {
          "text": "Histologie",
          "type": "choice",
          "answerOption": ["-", "ausstehend", "nachgewiesen"],
          "value": "-",
          "id": "ct_pankcas_histo"
        },
        {
          "text": "IgG4",
          "type": "choice",
          "answerOption": ["-", "positiv", "negativ"],
          "value": "-",
          "id": "ct_pankcas_igg4"
        },
        {
          "text": "Bildqualität",
          "type": "choice",
          "answerOption": ["exzellent", "mittel", "schlecht"],
          "value": "exzellent",
          "id": "ct_pankcas_quality"
        },
        {
          "text": "Pankreasparenchym",
          "type": "choice",
          "answerOption": ["normal", "lipotroph", "ödematös", "chron. Pankreatitis"],
          "value": "chron. Pankreatitis",
          "id": "ct_pankcas_parenchym"
        },
        {
          "text": "Pankreaskarzinom",
          "type": "group",
          "item": [
            {
              "text": "Tumorlokalisation",
              "type": "choice",
              "answerOption": ["-", "Pankreaskopf", "Pankreasschwanz", "Pankreaskörper", "Proc. uncinatus"],
              "value": "-",
              "id": "ct_pankcas_loc"
            },
            {
              "text": "Tumorgröße",
              "type": "group",
              "item": [
                {
                  "text": "Länge (cm)",
                  "type": "integer",
                  "value": 0,
                  "id": "ct_pankcas_size_1"
                },
                {
                  "text": "Breite (cm)",
                  "type": "integer",
                  "value": 0,
                  "id": "ct_pankcas_size_2"
                },
                {
                  "text": "Bild Nummer",
                  "type": "integer",
                  "value": 0,
                  "id": "ct_pankcas_size_ima"
                },
                {
                  "text": "Serie Nummer",
                  "type": "integer",
                  "value": 0,
                  "id": "ct_pankcas_size_series"
                }
              ]
            },
            {
              "text": "Tumorinfiltration Nachbarorgane",
              "type": "choice",
              "answerOption": [
                "-",
                "T1: ≤ 2cm (T1a: ≤ 0,5 cm / T1b < 1 cm / T1c: ≤ 2 cm)",
                "T2: ≤ 4 cm",
                "T3: > 4 cm",
                "T4: Gefäßinfiltration (>180°)"
              ],
              "value": "-",
              "id": "ct_pankcas_tstage"
            },
            {
              "text": "Tumorinfiltration Bild Nummer",
              "type": "integer",
              "value": 0,
              "id": "ct_pankcas_tstage_ima"
            },
            {
              "text": "Tumorinfiltration Serien Nummer",
              "type": "integer",
              "value": 0,
              "id": "ct_pankcas_tstage_series"
            },
            {
              "text": "Infiltration Beschreibung",
              "type": "string",
              "value": "Keine Infiltration",
              "id": "ct_pankcas_tstage_desc"
            },
            {
              "text": "KM-Enhancement arteriell",
              "type": "choice",
              "answerOption": ["-", "hypodens", "isodens", "hyperdens"],
              "value": "-",
              "id": "ct_pankcas_enhance_art"
            },
            {
              "text": "KM-Enhancement venös",
              "type": "choice",
              "answerOption": ["-", "hypodens", "isodens", "hyperdens"],
              "value": "-",
              "id": "ct_pankcas_enhance_ven"
            }
          ]
        },
        {
          "text": "Gallenwege",
          "type": "group",
          "item": [
            {
              "text": "Ductus pancreaticus",
              "type": "choice",
              "answerOption": ["-", "unauffällig", "dilatiert"],
              "value": "unauffällig",
              "id": "ct_pankcas_pancduct"
            },
            {
              "text": "Ductus pancreaticus Beschreibung",
              "type": "string",
              "value": "Normal condition",
              "id": "ct_pankcas_pancduct_text"
            },
            {
              "text": "Ductus hepatocholedochus",
              "type": "choice",
              "answerOption": ["-", "unauffällig", "dilatiert"],
              "value": "unauffällig",
              "id": "ct_pankcas_dhc"
            },
            {
              "text": "Ductus hepatocholedochus Beschreibung",
              "type": "string",
              "value": "Normal condition",
              "id": "ct_pankcas_dhc_text"
            }
          ]
        },
        {
          "text": "Gefäßbezug (arteriell)",
          "type": "group",
          "item": [
            {
              "text": "Aorta",
              "type": "choice",
              "answerOption": ["nein", "< 180°", "> 180°", "360°", "Deformierung"],
              "value": "nein",
              "id": "ct_pankcas_aorta"
            },
            {
              "text": "Truncus coeliacus",
              "type": "choice",
              "answerOption": ["nein", "< 180°", "> 180°", "360°", "Deformierung"],
              "value": "nein",
              "id": "ct_pankcas_trcoeliacus"
            },
            {
              "text": "A. hepatica communis",
              "type": "choice",
              "answerOption": ["nein", "< 180°", "> 180°", "360°", "Deformierung"],
              "value": "nein",
              "id": "ct_pankcas_ahepcom"
            }
          ]
        },
        {
          "text": "Gefäßbezug (venös)",
          "type": "group",
          "item": [
            {
              "text": "V. mesenterica superior",
              "type": "choice",
              "answerOption": ["nein", "< 180°", "> 180°", "360°", "Deformierung", "1. Jejunalast infiltriert"],
              "value": "nein",
              "id": "ct_pankcas_vms"
            },
            {
              "text": "V. lienalis",
              "type": "choice",
              "answerOption": ["nein", "< 180°", "> 180°", "360°", "Deformierung"],
              "value": "nein",
              "id": "ct_pankcas_vlien"
            },
            {
              "text": "V. portae",
              "type": "choice",
              "answerOption": ["nein", "< 180°", "> 180°", "360°", "Deformierung"],
              "value": "nein",
              "id": "ct_pankcas_vport"
            }
          ]
        },
        {
          "text": "Abdomen",
          "type": "group",
          "item": [
            {
              "text": "Aszites",
              "type": "choice",
              "answerOption": ["nein", "wenig", "ausgeprägt"],
              "value": "nein",
              "id": "ct_pankcas_aszites"
            },
            {
              "text": "Aszites Beschreibung",
              "type": "string",
              "value": "Keine Aszites",
              "id": "ct_pankcas_aszites_text"
            },
            {
              "text": "Peritoneale Implantate",
              "type": "choice",
              "answerOption": ["nein", "ja"],
              "value": "nein",
              "id": "ct_pankcas_peritoneum"
            },
            {
              "text": "Peritoneale Implantate Beschreibung",
              "type": "string",
              "value": "keine Implantate",
              "id": "ct_pankcas_peritoneum_text"
            },
            {
              "text": "Leber",
              "type": "choice",
              "answerOption": ["nein", "Lebermetastasen", "sonstiges"],
              "value": "nein",
              "id": "ct_pankcas_leber"
            },
            {
              "text": "Leber Beschreibung",
              "type": "string",
              "value": "kein Befund",
              "id": "ct_pankcas_leber_text"
            },
            {
              "text": "Milz",
              "type": "choice",
              "answerOption": ["unauffällig", "auffällig"],
              "value": "unauffällig",
              "id": "ct_pankcas_milz"
            },
            {
              "text": "Milz Beschreibung",
              "type": "string",
              "value": "Normal",
              "id": "ct_pankcas_milz_text"
            },
            {
              "text": "Nieren / Ureteren",
              "type": "choice",
              "answerOption": ["unauffällig", "auffällig"],
              "value": "unauffällig",
              "id": "ct_pankcas_nieren"
            },
            {
              "text": "Nieren / Ureteren Beschreibung",
              "type": "string",
              "value": "Normal",
              "id": "ct_pankcas_nieren_text"
            },
            {
              "text": "Nebennieren",
              "type": "choice",
              "answerOption": ["unauffällig", "auffällig"],
              "value": "unauffällig",
              "id": "ct_pankcas_nnieren"
            },
            {
              "text": "Nebennieren Beschreibung",
              "type": "string",
              "value": "Normal",
              "id": "ct_pankcas_nnieren_text"
            },
            {
              "text": "Lymphknoten",
              "type": "choice",
              "answerOption": ["unauffällig", "auffällig"],
              "value": "auffällig",
              "id": "ct_pankcas_lymph"
            },
            {
              "text": "Lymphknoten Beschreibung",
              "type": "string",
              "value": "Normal",
              "id": "ct_pankcas_lymph_text"
            },
            {
              "text": "Darm",
              "type": "choice",
              "answerOption": ["unauffällig", "auffällig"],
              "value": "unauffällig",
              "id": "ct_pankcas_darm"
            },
            {
              "text": "Darm Beschreibung",
              "type": "string",
              "value": "keine Auffälligkeiten",
              "id": "ct_pankcas_darm_text"
            },
            {
              "text": "Beckenorgane",
              "type": "choice",
              "answerOption": ["unauffällig", "auffällig"],
              "value": "unauffällig",
              "id": "ct_pankcas_becken"
            },
            {
              "text": "Beckenorgane Beschreibung",
              "type": "string",
              "value": "keine Auffälligkeiten",
              "id": "ct_pankcas_becken_text"
            },
            {
              "text": "Knochen",
              "type": "choice",
              "answerOption": ["unauffällig", "auffällig"],
              "value": "unauffällig",
              "id": "ct_pankcas_knochen"
            },
            {
              "text": "Knochen Beschreibung",
              "type": "string",
              "value": "kein Befund",
              "id": "ct_pankcas_knochen_text"
            },
            {
              "text": "Lunge (soweit miterfasst)",
              "type": "choice",
              "answerOption": ["unauffällig", "auffällig"],
              "value": "unauffällig",
              "id": "ct_pankcas_lunge"
            },
            {
              "text": "Lunge Beschreibung",
              "type": "string",
              "value": "keine Auffälligkeiten",
              "id": "ct_pankcas_lunge_text"
            },
            {
              "text": "Sonstiges",
              "type": "string",
              "value": "Bekannte Sigmadivertikulose",
              "id": "ct_pankcas_sonstiges"
            }
          ]
        }
      ]
    },
    {
      "text": "Beurteilung",
      "type": "group",
      "item": [
        {
          "text": "Bewertung",
          "type": "string",
          "value": "Im Bereich des Übergangs des Corpus pancreatis zur Cauda pancreatis bei Z.n. rezidivierenden akuten (nekrotisierenden) Pankreatitiden und bekannter chronischer Pankreatitis narbige Veränderungen mit Verkalkungen linear im Bereich der im MR beschriebenen Raumforderung. CT-morphologisch erscheint der Befund zunächst nicht tumortypisch, sollte jedoch bei der MRT-Befundkonstellation einer chronischen Pankreatitis in 6 bzw. spätestens 12 Monaten mit einer MRT des Oberbauch mit KM kontrolliert werden.",
          "id": "ct_pankcas_Beurteilung"
        },
        {
          "text": "Insgesamt TNM",
          "type": "string",
          "value": "-",
          "id": "ct_pankcas_TNM"
        },
        {
          "text": "Bewertungssicherheit",
          "type": "choice",
          "answerOption": ["-", "5 - sehr sicher", "4 - sicher", "3 - indifferent", "2 - unsicher", "1 - sehr unsicher"],
          "value": "3 - indifferent",
          "id": "ct_pankcas_certainty"
        }
      ]
    }
  ]
}


"""




if __name__ == '__main__':
    app.run()
