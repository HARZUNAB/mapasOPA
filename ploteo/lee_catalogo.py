import random
import numpy as np
import pandas as pd 

def lee_catalogo(archivo, sensibles=False):

    # La idea de esta función es que estandarice la lectura del catálogo, y que lo que
    # se cambie sea lo que está acá adentro y no se toque el resto del codigo

    # CORRECCIÓN DE COLUMNAS FORMATO CORRECTO (.dat)
    # Ahora la columna 2 es LATITUD y la columna 3 es LONGITUD
    lat_sismos = np.loadtxt(archivo, usecols=[2])
    lon_sismos = np.loadtxt(archivo, usecols=[3])
    prof_sismos = np.loadtxt(archivo, usecols=[4])
    mag_sismos = np.loadtxt(archivo, usecols=[5])
    typemag_sismos = np.loadtxt(archivo, usecols=[6], dtype="str")
    sensibles_sismos = np.loadtxt(archivo, usecols=[7], dtype="str")
    
    fechas = []

    with open(archivo, "r") as f:
        lineas = f.readlines()

    sensible = np.full(len(lineas), True, dtype=bool)

    for i in range(len(lineas)):
        linea = lineas[i].strip().split()
        fechas.append(linea[0] + ' ' + linea[1])
        # Mapeo de sismo sensible ("S" o "N")
        sensible[i] = True if sensibles_sismos[i] == "S" else False

    data = {
        'fecha': fechas,
        'lon': lon_sismos, 
        'lat': lat_sismos, 
        'prof': prof_sismos,
        'mag': mag_sismos, 
        'type_mag': typemag_sismos, 
        'sensible': sensible
    }

    df = pd.DataFrame(data)

    if sensibles:
        df['sensible'] = np.loadtxt(archivo, usecols=[-1]) 

    return df

