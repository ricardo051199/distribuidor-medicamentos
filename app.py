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
    # Asegúrate de que las coordenadas sean flotantes
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

    # Radio de la Tierra en kilómetros
    R = 6371.0

    # Conversion de grados a radianes
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Fórmula de Haversine
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distancia en kilómetros


def get_aptitud(ruta, medicamento):
    # Verificar si ruta es una lista
    if not isinstance(ruta, list):
        print(f"Error: 'ruta' no es una lista, es de tipo {type(ruta)}")
        return 0  # O cualquier valor adecuado en caso de error
    
    distancia_total = 0
    tiempo_total = 0

    for i in range(len(ruta) - 1):
        print(f"Accediendo a ruta[{i}]: {ruta[i]}")

        # Verificar que cada elemento sea un diccionario con la clave 'coords'
        if not isinstance(ruta[i], dict) or "coords" not in ruta[i]:
            print(f"Error: ruta[{i}] no tiene la estructura esperada: {ruta[i]}")
            return 0
        
        # Obtener las coordenadas de las farmacias en la ruta
        farmacia1 = ruta[i]
        farmacia2 = ruta[i + 1]

        # Extraer las coordenadas directamente desde los diccionarios
        lat1, lon1 = farmacia1["coords"]
        lat2, lon2 = farmacia2["coords"]

        # Calcular la distancia usando Haversine
        distancia_total += haversine(lat1, lon1, lat2, lon2)

        # Aquí puedes agregar la lógica para el tiempo basado en la distancia o alguna otra fórmula
        tiempo_total += calcular_tiempo(distancia_total)  # Esta es una función ejemplo para el cálculo del tiempo.

    return distancia_total


def calcular_tiempo(distancia_total):
    # Suponiendo que la velocidad promedio es de 50 km/h
    velocidad_promedio = 50  # km/h
    tiempo_total = distancia_total / velocidad_promedio  # Tiempo en horas
    return tiempo_total  # O cualquier otro cálculo relacionado con la aptitud

def generar_poblacion_inicial(distribuidor_coords, farmacias_coords):
    rutas = []
    for _ in range(10):  # Población de ejemplo
        # La ruta debe estar formada por diccionarios con nombre y coordenadas
        ruta = [{"nombre": "Distribuidor", "coords": distribuidor_coords}] + \
               [{"nombre": farmacia["nombre"], "coords": farmacia["coords"]} for farmacia in farmacias_coords]
        rutas.append(ruta)
    return rutas

def algoritmo_genetico(distribuidor_coords, farmacias_coords, medicamento):
    # Población inicial de rutas
    poblacion = generar_poblacion_inicial(distribuidor_coords, farmacias_coords)

    # Calcular la aptitud de cada ruta
    valores_aptitud = [get_aptitud(ruta, medicamento) for ruta in poblacion]

    # Aquí puedes continuar con el algoritmo genético, usando las rutas que contienen tanto el nombre como las coordenadas
    # Este paso depende de cómo implementes los operadores genéticos (cruce, mutación, etc.)

    # Retornar la mejor ruta y sus valores asociados
    mejor_ruta = poblacion[valores_aptitud.index(min(valores_aptitud))]  # O el mejor basado en el criterio que elijas
    tiempo_total = calcular_tiempo(sum(valores_aptitud))  # Suponemos que el tiempo total depende de la distancia total
    distancia_total = sum([get_aptitud(ruta, medicamento) for ruta in mejor_ruta])  # O lo que sea más adecuado

    return mejor_ruta, (tiempo_total, distancia_total)


def cargar_distribuidores():
    archivo = 'data/distribuidores.csv'
    print(f"Intentando cargar el archivo: {archivo}")
    if not os.path.exists(archivo):
        print(f"Error: El archivo {archivo} no se encuentra.")
        return pd.DataFrame()
    df = pd.read_csv(archivo)
    print(df)  # Verificar que se ha cargado correctamente el CSV
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
            # Procesar la farmacia de forma correcta
            parts = farmacia.split(' - ')
            nombre = parts[0].strip()
            coords_str = parts[1].split('coords: ')[-1].strip().rstrip('.')
            coords = tuple(map(float, coords_str.strip('[]').replace(' ', '').split(',')))

            if len(coords) != 2:
                return f"Error: Cada farmacia debe tener dos coordenadas (lat,long). Farmacia: {nombre}, Coordenadas: {coords}"

            # Agregar a la lista de farmacias
            farmacias_coords.append({"nombre": nombre, "coords": coords})

        except ValueError as e:
            return f"Error de formato: {e}. Farmacia: {farmacia}"

    ruta_optima, (tiempo_total, distancia_total) = algoritmo_genetico(distribuidor_coords, farmacias_coords, medicamento)

    tiempo_total = round(tiempo_total, 2)
    distancia_total = round(distancia_total, 2)

    ruta_optima_con_nombres = [{"nombre": farmacia["nombre"], "coords": farmacia["coords"]} for farmacia in ruta_optima]

    print(ruta_optima_con_nombres)  # Verificar que se ha cargado correctamente el CSV

    return render_template('ruta.html', ruta=ruta_optima_con_nombres, tiempo=tiempo_total, distancia=distancia_total, distribuidor=distribuidor_coords)

if __name__ == '__main__':
    app.run(debug=True)
