from flask import Flask, render_template, request
import random
import pandas as pd
import os
import math

app = Flask(__name__)

class Medicamento:
    def __init__(self, nombre, duracion_maxima):
        self.nombre = nombre
        self.duracion_maxima = duracion_maxima

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en kilómetros
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # Distancia en kilómetros

def get_aptitud(ruta, medicamento):
    tiempo_total = 0
    distancia_total = 0
    velocidad_promedio = 25  # Velocidad promedio en km/h para ciudad

    for i in range(len(ruta) - 1):
        if len(ruta[i]) != 2 or len(ruta[i + 1]) != 2:
            print(f"Ruta inválida: {ruta}")
            return float('inf'), float('inf')
        
        x1, y1 = ruta[i]
        x2, y2 = ruta[i + 1]
        distancia = haversine(x1, y1, x2, y2)  # Usar la fórmula de haversine
        tiempo_total += (distancia / velocidad_promedio) * 60  # Tiempo en minutos
        distancia_total += distancia  # Acumula la distancia total

    return tiempo_total if tiempo_total <= medicamento.duracion_maxima else float('inf'), distancia_total

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
        return "Error: El distribuidor no se encontró."

    distribuidor_coords = (distribuidor_data['Latitud'].values[0], distribuidor_data['Longitud'].values[0])

    farmacias_coords = []
    for farmacia in farmacias_raw:
        try:
            coords = tuple(map(float, farmacia.split(',')))
            if len(coords) != 2:
                return "Error: Cada farmacia debe tener dos coordenadas (lat,long)."
            farmacias_coords.append(coords)
        except ValueError:
            return "Error: Coordenadas fuera de formato (lat,long)."

    ruta_optima, (tiempo_total, distancia_total) = algoritmo_genetico(distribuidor_coords, farmacias_coords, medicamento)

    # Redondear tiempo total y distancia a 2 decimales
    tiempo_total = round(tiempo_total, 2)  # Tiempo en minutos
    distancia_total = round(distancia_total, 2)  # Distancia en kilómetros

    return render_template('ruta.html', ruta=ruta_optima, tiempo=tiempo_total, distancia=distancia_total, distribuidor=distribuidor_coords)

if __name__ == '__main__':
    app.run(debug=True)
