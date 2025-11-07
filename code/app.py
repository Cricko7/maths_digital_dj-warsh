from flask import Flask, request, render_template_string
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import networkx as nx
import io
import base64

app = Flask(__name__)



def dijkstra_path(matrix, start, end):
    G = nx.DiGraph()
    n = len(matrix)
    for i in range(n):
        for j in range(n):
            if i != j and matrix[i][j] > 0:
                G.add_edge(i, j, weight=matrix[i][j])
    path = nx.dijkstra_path(G, start, end, weight='weight')
    length = nx.dijkstra_path_length(G, start, end, weight='weight')
    return G, path, length



def plot_path_graph(G, path):
    import matplotlib.pyplot as plt
    import io, base64
    import networkx as nx

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(7, 7))

    # Цвета для узлов именно из path, чтобы длина совпадала с nodelist
    node_colors = []
    for node in path:
        if node == path[0]:
            node_colors.append('#43e77a')  # старт — зеленый
        elif node == path[-1]:
            node_colors.append('#f04040')  # финиш — красный
        else:
            node_colors.append('#ffa000')  # промежуточные — оранжевые

    # Отрисовываем узлы только из path и с цветами node_colors того же размера
    nx.draw_networkx_nodes(G, pos, nodelist=path, node_color=node_colors, node_size=600, alpha=0.92, linewidths=2)

    # Ребра кратчайшего пути
    nx.draw_networkx_edges(
        G, pos, edgelist=list(zip(path, path[1:])),
        width=4, edge_color="#7e9b13", arrows=True, arrowstyle='-|>', arrowsize=16, alpha=0.98
    )

    nx.draw_networkx_labels(G, pos, font_size=18, font_family='Arial', font_color="#212121")

    # Вес ребер по пути
    labels = nx.get_edge_attributes(G, 'weight')
    path_edges = list(zip(path, path[1:]))
    path_labels = {e: labels[e] for e in path_edges if e in labels}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=path_labels, font_color="#ffb347", font_size=14, label_pos=0.47)

    plt.axis('off')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=140)
    plt.close()
    buf.seek(0)

    return base64.b64encode(buf.read()).decode()





def warshall_reachability(matrix):
    n = len(matrix)
    reach = [row[:] for row in matrix]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
    return reach

def matrix_to_graph(matrix):
    G = nx.DiGraph()
    n = len(matrix)
    for i in range(n):
        for j in range(n):
            if matrix[i][j] and i != j:
                G.add_edge(i, j)
    return G

def plot_graph(graph, paths=None):
    pos = nx.kamada_kawai_layout(graph)
    plt.figure(figsize=(9, 9))
    nx.draw_networkx_nodes(graph, pos, node_color="#BF8E49FF", node_size=400, alpha=0.9)
    nx.draw_networkx_labels(graph, pos, font_size=16, font_family='Arial')

    edge_counts = {}
    for u, v in graph.edges():
        edge_counts[(u,v)] = edge_counts.get((u,v), 0) + 1
    
    drawn_edges = {}

    # Палитра оранжевых оттенков (можно добавить линейную смену прозрачности)
    colors = list(mcolors.LinearSegmentedColormap.from_list("", ["#000000", "#FF6F00"])(np.linspace(0,1,10)))

    for u, v in graph.edges():
        count = edge_counts[(u,v)]
        index = drawn_edges.get((u,v), 0)
        if count == 1:
            rad = 0
        else:
            step = 0.6 / (count - 1) if count > 1 else 0
            rad = -0.3 + step*index
        drawn_edges[(u,v)] = index + 1

        # Выбираем цвет из палитры, основанный на индексе
        color = colors[index % len(colors)]
        alpha = 0.7 - 0.07*index  # чуть уменьшаем прозрачность

        # Толщина рёбер с уменьшением по индексу
        width = max(2 - 0.3*index, 0.8)

        nx.draw_networkx_edges(
            graph, pos, edgelist=[(u,v)],
            arrowstyle='-|>', arrowsize=12,
            width=width,
            edge_color=color,
            alpha=alpha,
            connectionstyle=f"arc3,rad={rad}"
        )
    plt.axis('off')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=130)
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()



html_template = '''
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Кратчайший путь (Дейкстра) | Транзитивное замыкание (Уоршелл)</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css">
<style>
  body {
    background-color: #121212;
    color: #FFA500;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
  h2, h5 { color: #FF8C00; }
  .container {
    background-color: #1E1E1E;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 0 15px #FF8C0055;
  }
  textarea.form-control, select.form-select { background-color: #222; color: #FFA500; border: 1px solid #FF8C00; }
  textarea.form-control::placeholder { color: #FFB84D; }
  button.btn-primary { background-color: #FF8C00; border: none; }
  button.btn-primary:hover { background-color: #ffa500; }
  button.btn-secondary { background-color: #333; border: none; color: #FFA500; }
  button.btn-secondary:hover { background-color: #444; color: #FF8C00; }
  .alert-info { background-color: #2A2A2A; border-color: #FF8C00; color: #FFA500; }
  .alert-danger { background-color: #440000; border-color: #FF4500; color: #FF6347; }
  img.img-fluid { border: 2px solid #FFA500; border-radius: 6px; }
  a, a:hover { color: #FFB84D; }
</style>
</head>
<body>
<div class="container mt-4">
  <h2>Анализ графа: Дейкстра и Уоршелл</h2>
  <form method="post" class="mb-3">
    <textarea name="matrix" class="form-control mb-3" rows="10"
      placeholder="Ваша матрица весов (через пробел, строки через Enter)">{{ matrix or '' }}</textarea>
    <div class="row mb-3">
      <div class="col">
        <input type="number" min="0" name="start" class="form-control" placeholder="Начальная вершина" value="{{ start or '' }}">
      </div>
      <div class="col">
        <input type="number" min="0" name="end" class="form-control" placeholder="Конечная вершина" value="{{ end or '' }}">
      </div>
    </div>
    <button type="submit" name="task" value="dijkstra" class="btn btn-primary">Искать кратчайший путь (Дейкстра)</button>
    <button type="submit" name="task" value="warshall" class="btn btn-secondary ms-2">Построить транзитивное замыкание</button>
  </form>
  {% if error %}
    <div class="alert alert-danger">{{ error }}</div>
  {% endif %}
  {% if path %}
    <div class="alert alert-info mb-2">
      <h5>Кратчайший путь:</h5>
      <strong>{{ path }}</strong>
      <div>Длина пути: <strong>{{ length }}</strong></div>
    </div>
    <h5>Визуализация пути:</h5>
    <img class="img-fluid border rounded" src="data:image/png;base64,{{ image }}">
  {% endif %}
  {% if result %}
    <div class="alert alert-info mt-4">
      <h5>Транзитивное замыкание:</h5>
      <pre class="bg-dark p-2 rounded border">{{ result }}</pre>
    </div>
    <h5>Граф достижимости:</h5>
    <img class="img-fluid border rounded" src="data:image/png;base64,{{ image }}">
  {% endif %}
  <div class="mt-4 small text-muted text-center">Created by Roman Stepanov. 2025.</div>
</div>
</body>
</html>

'''

@app.route('/', methods=['GET', 'POST'])
def index():
    matrix_str = ''
    result_str = ''
    img = None
    error_msg = None
    path_disp = ''
    length_disp = ''
    start = end = None
    task = None

    if request.method == 'POST':
        matrix_str = request.form.get('matrix', '')
        start_raw = request.form.get('start', '')
        end_raw = request.form.get('end', '')
        task = request.form.get('task', 'warshall')

        try:
            matrix = [
                [int(x) for x in line.strip().split()]
                for line in matrix_str.strip().split('\n') if line.strip()
            ]
            n = len(matrix)
            if any(len(row) != n for row in matrix):
                error_msg = 'Ошибка: матрица должна быть квадратной.'
            else:
                if task == 'warshall':
                    if any(x not in (0,1) for row in matrix for x in row):
                        error_msg = 'Для транзитивного замыкания матрица должна содержать только 0 и 1.'
                    else:
                        closure = warshall_reachability(matrix)
                        result_str = '\n'.join(' '.join(str(x) for x in row) for row in closure)
                        G = matrix_to_graph(closure)
                        if G.number_of_edges() == 0:
                            img = None
                            error_msg = 'В графе после замыкания нет ни одного ребра для визуализации.'
                        else:
                            img = plot_graph(G)
                elif task == 'dijkstra':
                    if not (start_raw.isdigit() and end_raw.isdigit()):
                        error_msg = 'Укажите корректно начальную и конечную вершины для Дейкстры.'
                    else:
                        start, end = int(start_raw), int(end_raw)
                        if not (0 <= start < n and 0 <= end < n):
                            error_msg = f'Вершины должны быть в диапазоне от 0 до {n-1}.'
                        else:
                            G, path, length = dijkstra_path(matrix, start, end)
                            img = plot_path_graph(G, path)
                            path_disp = ' ➔ '.join(map(str, path))
                            length_disp = length
        except Exception as e:
            error_msg = f'Ошибка обработки данных: {e}'

    return render_template_string(
        html_template,
        matrix=matrix_str,
        result=result_str,
        image=img,
        error=error_msg,
        path=path_disp,
        length=length_disp,
        start=start,
        end=end,
        task=task
    )


if __name__ == '__main__':
    app.run(debug=True)
