import random
import numpy as np
import pandas as pd 

def lee_catalogo(archivo, sensibles=False):

    # La idea de esta función es que estandarice la lectura del catálogo, y que lo que
    # se cambie sea lo que está acá adentro y no se toque el resto del codigo
    #
    # Por ahora está adaptado pal selectpulento
    # Retorna un dataframe con todo lo necesario: lat, lon, prof, mag,
    # typemag (str), sensible(boolean)

    lon_sismos = np.loadtxt(archivo, usecols=[2])
    lat_sismos = np.loadtxt(archivo, usecols=[3])
    prof_sismos = np.loadtxt(archivo, usecols=[4])
    mag_sismos = np.loadtxt(archivo, usecols=[5])
    typemag_sismos = np.loadtxt(archivo, usecols=[6], dtype="str")
    sensibles_sismos = np.loadtxt(archivo, usecols=[7], dtype="str")
    
    fechas = []
    sensible = []

    f = open(archivo, "r")
    lineas = f.readlines()
    #print(lineas,'\n')
    f.close()

    sensible = np.full(len(lineas), True, dtype=bool)

    for i in range(len(lineas)):
        #print(i)
        linea = lineas[i].strip().split()
        #print(linea)
        fechas.append(linea[0] + ' ' + linea[1])
        # Voy a randomizar si son sensibles o no:
        sensible[i] = True if sensibles_sismos[i]=="S" else False

    data = {'fecha': fechas,'lon':lon_sismos, 'lat':lat_sismos, 'prof':prof_sismos,
            'mag':mag_sismos, 'type_mag':typemag_sismos, 'sensible':sensible}

    df = pd.DataFrame(data)

    #print("Leyendo catalogo")

    if sensibles:
        df['sensible'] = np.loadtxt(archivo, usecols=[-1]) #esto lo dejo como idea nomás

    return df
