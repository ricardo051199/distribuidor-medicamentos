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
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c 


def get_aptitud(ruta, medicamento):
    distancia_total = 0
    tiempo_total = 0
    if not isinstance(ruta, list):
        return 0

    for i in range(len(ruta) - 1):
        if not isinstance(ruta[i], dict) or "coords" not in ruta[i]:
            return 0
        
        farmacia1 = ruta[i]
        farmacia2 = ruta[i + 1]

        lat1, lon1 = farmacia1["coords"]
        lat2, lon2 = farmacia2["coords"]

        distancia_total += haversine(lat1, lon1, lat2, lon2)

        tiempo_total += calcular_tiempo(distancia_total)

    return distancia_total


def calcular_tiempo(distancia_total):
    velocidad_promedio = 50
    tiempo_total = distancia_total / velocidad_promedio
    return tiempo_total

def generar_poblacion_inicial(distribuidor_coords, farmacias_coords):
    rutas = []
    for _ in range(10):
        ruta = [{"nombre": "Distribuidor", "coords": distribuidor_coords}] + \
               [{"nombre": farmacia["nombre"], "coords": farmacia["coords"]} for farmacia in farmacias_coords]
        rutas.append(ruta)
    return rutas

def seleccionar_individuo(poblacion, aptitudes):
    total_aptitud = sum(aptitudes)
    probabilidad_seleccion = [aptitud / total_aptitud for aptitud in aptitudes]
    return poblacion[random.choices(range(len(poblacion)), probabilidad_seleccion)[0]]

def cruzar(padre1, padre2):
    punto_cruce = random.randint(1, len(padre1) - 1)
    hijo = padre1[:punto_cruce] + padre2[punto_cruce:]
    return hijo

def mutar(individuo, tasa_mutacion=0.1):
    if random.random() < tasa_mutacion:
        i, j = random.sample(range(1, len(individuo)), 2)
        individuo[i], individuo[j] = individuo[j], individuo[i]
    
    return individuo

def evaluar_ruta(ruta, medicamento):
    return get_aptitud(ruta, medicamento)


def algoritmo_genetico(distribuidor_coords, farmacias_coords, medicamento, generaciones=100, tasa_mutacion=0.1):
    poblacion = generar_poblacion_inicial(distribuidor_coords, farmacias_coords)

    for _ in range(generaciones):
        aptitudes = [evaluar_ruta(ruta, medicamento) for ruta in poblacion]
        nueva_poblacion = []
        while len(nueva_poblacion) < len(poblacion):
            padre1 = seleccionar_individuo(poblacion, aptitudes)
            padre2 = seleccionar_individuo(poblacion, aptitudes)
            hijo = cruzar(padre1, padre2)
            hijo = mutar(hijo, tasa_mutacion)
            nueva_poblacion.append(hijo)
        poblacion = nueva_poblacion
    
    aptitudes = [evaluar_ruta(ruta, medicamento) for ruta in poblacion]
    mejor_ruta = poblacion[aptitudes.index(min(aptitudes))]
    
    tiempo_total = calcular_tiempo(sum(aptitudes))
    distancia_total = sum([get_aptitud(ruta, medicamento) for ruta in mejor_ruta])
    
    return mejor_ruta, (tiempo_total, distancia_total)

def cargar_distribuidores():
    archivo = 'data/distribuidores.csv'
    if not os.path.exists(archivo):
        return pd.DataFrame() 
    df = pd.read_csv(archivo)
    return df

@app.route('/')
def index():
    df_distribuidores = cargar_distribuidores()
    if df_distribuidores.empty:
        return render_template('index.html', distribuidores=[], error="No se pudieron cargar los distribuidores.")

    distribuidores = df_distribuidores['Nombre'].tolist()
    return render_template('index.html', distribuidores=distribuidores, )

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
            parts = farmacia.split(' - ')
            nombre = parts[0].strip()
            coords_str = parts[1].split('coords: ')[-1].strip().rstrip('.')
            coords = tuple(map(float, coords_str.strip('[]').replace(' ', '').split(',')))

            if len(coords) != 2:
                return f"Error: Cada farmacia debe tener dos coordenadas (lat,long). Farmacia: {nombre}, Coordenadas: {coords}"

            farmacias_coords.append({"nombre": nombre, "coords": coords})

        except ValueError as e:
            return f"Error de formato: {e}. Farmacia: {farmacia}"

    ruta_optima, (tiempo_total, distancia_total) = algoritmo_genetico(distribuidor_coords, farmacias_coords, medicamento)

    tiempo_total = round(tiempo_total, 2)
    distancia_total = round(distancia_total, 2)

    ruta_optima_con_nombres = [{"nombre": farmacia["nombre"], "coords": farmacia["coords"]} for farmacia in ruta_optima]

    return render_template('ruta.html', ruta=ruta_optima_con_nombres, tiempo=tiempo_total, distancia=distancia_total, distribuidor=distribuidor_coords)

if __name__ == '__main__':
    app.run(debug=True)
