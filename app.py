from flask import Flask, render_template, request
import random
import pandas as pd
import os

app = Flask(__name__)

class Medicamento:
    def __init__(self, nombre, duracion_maxima):
        self.nombre = nombre
        self.duracion_maxima = duracion_maxima

def get_aptitud(ruta, medicamento):
    tiempo_total = 0
    for i in range(len(ruta) - 1):
        if len(ruta[i]) != 2 or len(ruta[i + 1]) != 2:
            print(f"Ruta inválida: {ruta}")
            return float('inf')
        
        x1, y1 = ruta[i]
        x2, y2 = ruta[i + 1]
        tiempo_total += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5  # Distancia euclidiana

    return tiempo_total if tiempo_total <= medicamento.duracion_maxima else float('inf')

def algoritmo_genetico(distribuidor, farmacias, medicamento):
    poblacion = []
    for _ in range(100):
        ruta = [distribuidor] + random.sample(farmacias, len(farmacias))
        poblacion.append(ruta)

    valores_aptitud = [get_aptitud(ruta, medicamento) for ruta in poblacion]
    mejor_ruta = poblacion[valores_aptitud.index(min(valores_aptitud))]
    
    return mejor_ruta, min(valores_aptitud)

def cargar_distribuidores():
    archivo = 'data/distribuidores.csv'
    print(f"Intentando cargar el archivo: {archivo}")
    if not os.path.exists(archivo):
        print(f"Error: El archivo {archivo} no se encuentra.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(archivo)
        return df
    except Exception as e:
        print(f"Error al cargar distribuidores: {e}")
        return pd.DataFrame()

@app.route('/')
def index():
    df_distribuidores = cargar_distribuidores()
    if df_distribuidores.empty:
        return render_template('index.html', distribuidores=[], error="No se pudieron cargar los distribuidores.")

    distribuidores = df_distribuidores['Nombre'].tolist()
    return render_template('index.html', distribuidores=distribuidores)

@app.route('/calcular_ruta', methods=['POST'])
def calcular_ruta():
    nombre_medicamento = request.form['medicamento']
    duracion_maxima = int(request.form['duracion_maxima'])
    nombre_distribuidor = request.form['ubicacion_distribuidor']
    farmacias_raw = request.form['ubicaciones_farmacias'].strip().splitlines()

    medicamento = Medicamento(nombre=nombre_medicamento, duracion_maxima=duracion_maxima)

    df_distribuidores = cargar_distribuidores()
    distribuidor_data = df_distribuidores[df_distribuidores['Nombre'] == nombre_distribuidor]

    if distribuidor_data.empty:
        return "Error: El distribuidor no se encontro."

    distribuidor_coords = (distribuidor_data['Latitud'].values[0], distribuidor_data['Longitud'].values[0])

    farmacias_coords = []
    for farmacia in farmacias_raw:
        try:
            coords = tuple(map(float, farmacia.split(',')))
            if len(coords) != 2:
                return "Error: Cada farmacia debe tener dos coordenadas (lat,long)."
            farmacias_coords.append(coords)
        except ValueError:
            return "Error: Coordenadas fuera de formato(lat,long)."

    ruta_optima, tiempo_total = algoritmo_genetico(distribuidor_coords, farmacias_coords, medicamento)

    return render_template('resultado.html', ruta=ruta_optima, tiempo=tiempo_total, distribuidor=distribuidor_coords)

if __name__ == '__main__':
    app.run(debug=True)
