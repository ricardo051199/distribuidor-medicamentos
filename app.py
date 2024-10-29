from flask import Flask, render_template, request
import random
import pandas as pd

app = Flask(__name__)

# Clase para representar un medicamento
class Medicamento:
    def __init__(self, nombre, duracion_maxima):
        self.nombre = nombre
        self.duracion_maxima = duracion_maxima

# Función para calcular la aptitud de una ruta
def get_aptitud(ruta, medicamento):
    tiempo_total = 0
    for i in range(len(ruta) - 1):
        x1, y1 = ruta[i]
        x2, y2 = ruta[i + 1]
        tiempo_total += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5  # Distancia euclidiana
    return tiempo_total if tiempo_total <= medicamento.duracion_maxima else float('inf')

# Algoritmo genético para encontrar la ruta óptima
def algoritmo_genetico(distribuidor, farmacias, medicamento):
    poblacion = []
    for _ in range(100):  # Genera 100 rutas aleatorias
        ruta = [distribuidor] + random.sample(farmacias, len(farmacias)) + [distribuidor]
        poblacion.append(ruta)

    # Evaluar la población y seleccionar la mejor ruta
    valores_aptitud = [get_aptitud(ruta, medicamento) for ruta in poblacion]
    mejor_ruta = poblacion[valores_aptitud.index(min(valores_aptitud))]
    return mejor_ruta, min(valores_aptitud)

# Cargar distribuidores desde el archivo CSV
def cargar_distribuidores():
    try:
        df = pd.read_csv('distribuidores.csv')
        return df
    except Exception as e:
        print(f"Error al cargar distribuidores: {e}")
        return pd.DataFrame()

@app.route('/')
def index():
    distribuidores = cargar_distribuidores()['Nombre'].tolist()
    return render_template('index.html', distribuidores=distribuidores)

@app.route('/calcular_ruta', methods=['POST'])
def calcular_ruta():
    nombre_medicamento = request.form['medicamento']
    duracion_maxima = int(request.form['duracion_maxima'])
    nombre_distribuidor = request.form['ubicacion_distribuidor']
    farmacias_raw = request.form['ubicaciones_farmacias'].strip().splitlines()

    medicamento = Medicamento(nombre=nombre_medicamento, duracion_maxima=duracion_maxima)

    # Obtener las coordenadas del distribuidor
    df_distribuidores = cargar_distribuidores()
    distribuidor_data = df_distribuidores[df_distribuidores['Nombre'] == nombre_distribuidor]
    distribuidor_coords = (distribuidor_data['Latitud'].values[0], distribuidor_data['Longitud'].values[0])

    # Convertir las ubicaciones de farmacias a coordenadas
    try:
        farmacias_coords = [tuple(map(float, farmacia.split(','))) for farmacia in farmacias_raw]
    except ValueError:
        return "Error: Asegúrate de que las coordenadas estén en el formato correcto (lat, long)."

    # Llamar al algoritmo genético
    ruta_optima, tiempo_total = algoritmo_genetico(distribuidor_coords, farmacias_coords, medicamento)

    return render_template('resultado.html', ruta=ruta_optima, tiempo=tiempo_total)

if __name__ == '__main__':
    app.run(debug=True)
