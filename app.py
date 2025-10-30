from flask import Flask, render_template_string, request, send_file
import math
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Калькулятор плитного фундамента</title>
</head>
<body>
    <h2>Калькулятор плитного фундамента</h2>
    <form method="post">
        <label>Длина плиты (м): <input type="number" step="0.01" name="A" required></label><br>
        <label>Ширина плиты (м): <input type="number" step="0.01" name="B" required></label><br>
        <label>Толщина плиты (м): <input type="number" step="0.01" name="H" required></label><br>
        <label>Диаметр арматуры (мм): <input type="number" name="rebar_diameter" required></label><br>
        <label>Шаг сетки по X (м): <input type="number" step="0.01" name="grid_x" required></label><br>
        <label>Шаг сетки по Y (м): <input type="number" step="0.01" name="grid_y" required></label><br>
        <label>Цена бетона за м³ (руб): <input type="number" step="0.01" name="concrete_price" required></label><br>
        <label>Цена арматуры за кг (руб): <input type="number" step="0.01" name="steel_price" required></label><br>
        <label>Цена опалубки за м² (руб): <input type="number" step="0.01" name="formwork_price" required></label><br>
        <label>Процент запаса материалов (%): <input type="number" step="0.01" name="waste_factor" required></label><br>
        <button type="submit">Рассчитать</button>
    </form>
    {% if results %}
    <h3>Результаты расчета:</h3>
    <ul>
        <li>Объём бетона: {{ results.volume_bet }} м³</li>
        <li>Площадь опалубки: {{ results.area_formwork }} м²</li>
        <li>Длина арматуры: {{ results.length_rebar }} м</li>
        <li>Масса арматуры: {{ results.mass_rebar }} кг</li>
        <li>Стоимость бетона: {{ results.cost_concrete }} руб</li>
        <li>Стоимость арматуры: {{ results.cost_steel }} руб</li>
        <li>Стоимость опалубки: {{ results.cost_formwork }} руб</li>
        <li><strong>Итоговая стоимость: {{ results.cost_total }} руб</strong></li>
    </ul>
    <h4>Схема армирования:</h4>
    <img src="/sketch.png" alt="Схема армирования" style="max-width:100%;">
    {% endif %}
</body>
</html>
"""

def generate_sketch(A, B, grid_x, grid_y, filename='static/sketch.png'):
    fig, ax = plt.subplots(figsize=(10, 6))
    # сетка по X (вертикальные линии)
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
    return render_template_string(HTML_FORM, results=results)

@app.route('/sketch.png')
def sketch():
    return send_file('static/sketch.png', mimetype='image/png')

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
