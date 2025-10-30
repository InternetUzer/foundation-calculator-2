from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
import math
import matplotlib.pyplot as plt
import os
import io
import json
from fpdf import FPDF

app = Flask(__name__)

# === Папки ===
os.makedirs('static', exist_ok=True)
os.makedirs('projects', exist_ok=True)

# === HTML шаблон перенесён в templates/index.html (см. ниже) ===

def generate_sketch(A, B, grid_x, grid_y, filename='static/sketch.png'):
    fig, ax = plt.subplots(figsize=(10, 6))
    x_lines = int(A / grid_x) + 1
    y_lines = int(B / grid_y) + 1
    for i in range(x_lines):
        x = i * grid_x
        ax.plot([x, x], [0, B], color='black', linewidth=0.5)
    for j in range(y_lines):
        y = j * grid_y
        ax.plot([0, A], [y, y], color='black', linewidth=0.5)
    ax.set_xlim(0, A)
    ax.set_ylim(0, B)
    ax.set_aspect('equal')
    ax.set_title('Схема армирования плиты')
    ax.set_xlabel('Длина (м)')
    ax.set_ylabel('Ширина (м)')
    ax.grid(True)
    plt.savefig(filename)
    plt.close()

def calculate_foundation(data):
    A = float(data['A'])
    B = float(data['B'])
    H = float(data['H'])
    d = float(data['rebar_diameter']) / 1000
    grid_x = float(data['grid_x'])
    grid_y = float(data['grid_y'])
    concrete_price = float(data['concrete_price'])
    steel_price = float(data['steel_price'])
    formwork_price = float(data['formwork_price'])
    waste_factor = float(data['waste_factor']) / 100

    volume_bet = A * B * H * (1 + waste_factor)
    area_formwork = A * B + 2 * (A + B) * H
    n_x = math.ceil(B / grid_x) + 1
    n_y = math.ceil(A / grid_y) + 1
    length_rebar = n_x * A + n_y * B
    mass_rebar = length_rebar * math.pi * (d**2) / 4 * 7850
    cost_concrete = volume_bet * concrete_price
    cost_steel = mass_rebar * steel_price
    cost_formwork = area_formwork * formwork_price
    cost_total = cost_concrete + cost_steel + cost_formwork

    generate_sketch(A, B, grid_x, grid_y)

    return {
        'A': A, 'B': B, 'H': H,
        'rebar_diameter': d * 1000,
        'grid_x': grid_x, 'grid_y': grid_y,
        'volume_bet': round(volume_bet, 2),
        'area_formwork': round(area_formwork, 2),
        'length_rebar': round(length_rebar, 2),
        'mass_rebar': round(mass_rebar, 2),
        'cost_concrete': round(cost_concrete, 2),
        'cost_steel': round(cost_steel, 2),
        'cost_formwork': round(cost_formwork, 2),
        'cost_total': round(cost_total, 2)
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST':
        results = calculate_foundation(request.form)
    return render_template('index.html', results=results)

@app.route('/sketch.png')
def sketch():
    return send_file('static/sketch.png', mimetype='image/png')

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    filename = data.get("name", "project") + ".json"
    filepath = os.path.join('projects', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({"status": "saved", "file": filename})

@app.route('/load/<filename>')
def load(filename):
    filepath = os.path.join('projects', filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    data = request.json
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Отчёт: Калькулятор плитного фундамента", ln=True)
    for k, v in data.items():
        pdf.cell(200, 10, txt=f"{k}: {v}", ln=True)
    img_path = 'static/sketch.png'
    if os.path.exists(img_path):
        pdf.image(img_path, x=10, y=None, w=180)
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return send_file(pdf_output, download_name="report.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
