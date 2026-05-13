import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import datetime
import sys
import os
import matplotlib.ticker as ticker
from lee_catalogo import *
import locale
#from datetime import datetime

# lineas agregadas para eliminar warnings
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Esto desactiva el límite de seguridad
import warnings
import matplotlib
from PIL import Image
# Silenciar todos los avisos
warnings.filterwarnings("ignore")
Image.MAX_IMAGE_PIXELS = None

fecha = sys.argv[3]
fecha_str = str(fecha)
objeto_fecha = datetime.datetime.strptime(fecha_str, "%Y%m")
# %B es el nombre completo del mes, %Y es el año de 4 dígitos
resultado = objeto_fecha.strftime("%B %Y")

# Configura el idioma a español
# En Linux suele ser 'es_ES.UTF-8'
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') 
except:
    locale.setlocale(locale.LC_TIME, 'es-es')

fecha_trans = objeto_fecha.strftime("%B %Y").capitalize()

##############################################################################
## INFO
## Este codigo se pone en distintos escenarios dado un cierto catalogo de
## sismos, y realiza plots de magnitud versus tiempo en base a eso
## Los escenarios pueden ser:
## - si la cantidad de días es mayor a 1 menor o igual a 7: es una semana nomas
##            -> plots diarios y uno semanal
## - Si es mayor a 7 pero menor a 60:
##            -> plots por cada semana
## - Si es mayor a 60
##            -> plots por cada mes
## - Si es un dia o menos
##            -> plots por cada hora
##############################################################################

catalogo = sys.argv[2]
N_mapas = int(sys.argv[4])
df_catalogo = lee_catalogo(catalogo)
df_sensibles = df_catalogo.loc[(df_catalogo['sensible'] == True)]
df_nosensibles = df_catalogo.loc[(df_catalogo['sensible'] == False)]

carpeta_fig = "./figuras/"
nombre_carpeta = catalogo.split('.')[0]
carpeta_fig += catalogo.split('.')[0] + "/"

if not os.path.exists(carpeta_fig):
    os.makedirs(carpeta_fig)

fmt = '%Y-%m-%d %H:%M:%S'
t = [datetime.datetime.strptime(df_catalogo['fecha'][i], fmt) for i in range(len(df_catalogo['fecha']))]
diferencia_t = max(t) - min(t)

t_sensibles = [datetime.datetime.strptime(fecha, fmt) for fecha in df_sensibles['fecha']]
t_nosensibles = [datetime.datetime.strptime(fecha, fmt) for fecha in df_nosensibles['fecha']]
# Condiciones

t_ini = min(t)
t_ventana = diferencia_t/N_mapas
t_fin = t_ini + t_ventana

for i in range(N_mapas):
    f = plt.figure(figsize=(10,5))
    ax = plt.subplot()
    #ax.set_title( "Mapa %d" %(i+1) )
    #ax.set_title( "Distribucion de sismos (M>=2.5) %d" %(i+1))
    # Título dinámico: Nombre del mapa + Fecha (ej: Diciembre 2026)
    titulo_completo = f"Distribución de sismos (M>=2.5) - Gráfico {i+1}"#\n{fecha_trans}"

    ax.set_title(titulo_completo, 
                fontsize=10, 
                fontweight='bold', 
                pad=20,          # Espacio extra para que no choque con el mapa
                loc='center')    # Centrado

    ax.set_ylabel('Magnitud')
    t_f = t_ini.strftime("%Y-%m-%d  %H:%M:%S")
    t_t = t_fin.strftime("%Y-%m-%d  %H:%M:%S")
    ax.set_xlabel("Datos desde   %s   hasta   %s   "%(t_f, t_t))
    
    plt.grid(linestyle='--')
    plt.gcf().autofmt_xdate()

    #Festival de IFs
    if t_ventana.days < 10:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:00"))
    elif t_ventana.days < 30:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:00"))
    elif t_ventana.days/30 < 12*5:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:00"))
    else: 
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Fija límites exactos
    ax.set_xlim(t_ini, t_fin)

    # Convierte bordes a formato numérico
    t_ini_num = mdates.date2num(t_ini)
    t_fin_num = mdates.date2num(t_fin)

    # Crea localizadores intermedios automáticos (ej: 6 etiquetas en total)
    # Usamos MaxNLocator para que busque puntos "bonitos" entre los límites
    from matplotlib.ticker import MaxNLocator
    n_ticks = 8 
    intermedios = MaxNLocator(nbins=n_ticks).tick_values(t_ini_num, t_fin_num)

    # Combina y filtrar para que no se amontonen en los bordes
    umbral = (t_fin_num - t_ini_num) * 0.1  # 10% de margen para no pisar el texto
    valid_intermedios = [t for t in intermedios if t > (t_ini_num + umbral) and t < (t_fin_num - umbral)]

    # Aplica la lista final
    ax.set_xticks([t_ini_num] + valid_intermedios + [t_fin_num])

    # Formato de etiquetas
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))
    plt.xticks(rotation=45, ha='right')
 
    for j in range(len(t)):
        if t[j]>=t_ini and t[j]<t_fin:
            if  df_catalogo['sensible'][j]:
                plt.scatter(t[j], df_catalogo['mag'][j], c='tomato')
            else:
                plt.scatter(t[j], df_catalogo['mag'][j], c='teal')

    ax.set_xlim(t_ini, t_fin)
    #ax.margins(x=0)

    # Fija límite inferior exacto
    # El límite superior lo dejamos dinámico según el sismo más grande + un margen
    ax.set_ylim(bottom=2.4, top=df_catalogo['mag'].max() + 0.5)

    # Elimina márgenes internos automáticos de Matplotlib
    ax.margins(x=0)

    nombre_imagen = 'grafico_%d.png' %(i+1)
    f.savefig(carpeta_fig + nombre_imagen, dpi=300, bbox_inches='tight')
    t_ini = t_fin
    t_fin = t_ini + t_ventana
        
    
    
plt.close('all')

print("Gráfico distribución sismicidad generado ✅")


"""
# si la cantidad de días es mayor a 1:
if diferencia_t.hours > 1:

    # Pero si es menor o igual a 7: es una semana nomas -> plots diarios
    if diferencia_t.days <= 7:
        dia_plot = min(t)
        count = 0
        for i in range(diferencia_t.days + 1):
            # inicia la figura
            f = plt.figure(figsize=(8,5))
            ax = plt.subplot()

            ax.set_title(dia_plot.strftime('%Y-%m-%d'))
            ax.set_ylabel('Magnitud')

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            ax.set_xlim([dia_plot - datetime.timedelta(hours=1),
                         dia_plot + datetime.timedelta(hours=25)])
            plt.grid(linestyle='--')
            plt.gcf().autofmt_xdate()

            #for en el los datos, break si el dia es mayor, plot si no
            for j in range(count, len(t)):
                if t[j].day>dia_plot.day:
                    dia_plot=t[j]
                    break
                else:
                    if  df_catalogo['sensible'][j]:
                        plt.scatter(t[j], df_catalogo['mag'][j], c='tomato')
                    else:
                        plt.scatter(t[j], df_catalogo['mag'][j], c='teal')
                    count+=1
            nombre_imagen = dia_plot.strftime('%Y-%m-%d') + '.png'
            f.savefig(carpeta_fig + nombre_imagen, dpi=300, bbox_inches='tight')



# Si es mayor a 7 pero menor a 60: plots por cada semana
    elif diferencia_t.days > 7 and diferencia_t.days<=60:
        dia1_semana = min(t)
        cant_semanas = int(diferencia_t.days/7) + bool(diferencia_t.days%7)
        count = 0
        for i in range(cant_semanas):
            # inicia la figura
            f = plt.figure(figsize=(8,5))
            ax = plt.subplot()

            ax.set_title("Semana del " + dia1_semana.strftime('%d/%m'))
            ax.set_ylabel('Magnitud')

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m "))
            ax.set_xlim([dia1_semana - datetime.timedelta(hours=8),
                         dia1_semana + datetime.timedelta(days=7,hours=8)])
            plt.grid(linestyle='--')
            plt.gcf().autofmt_xdate()

            #for en el los datos, break si la semana es mayor, plot si no
            for j in range(count, len(t)):
                if t[j].day>dia1_semana.day+6:
                    dia1_semana+=datetime.timedelta(days=7)
                    break
                else:
                    if  df_catalogo['sensible'][j]:
                        plt.scatter(t[j], df_catalogo['mag'][j], c='tomato')
                    else:
                        plt.scatter(t[j], df_catalogo['mag'][j], c='teal')
                    count+=1
            nombre_imagen = "Semana_" + dia1_semana.strftime('%d-%m') + '.png'
            f.savefig(carpeta_fig + nombre_imagen, dpi=300, bbox_inches='tight')



    # Si es mayor a 60: plots por cada mes
    else:
        dia1_mes = min(t)
        diaultimo_mes = pd.Period(dia1_mes,freq='M').end_time.date()
        dia31_mes = datetime.datetime(diaultimo_mes.year, diaultimo_mes.month,
                                      diaultimo_mes.day)

        cant_meses = int(diferencia_t.days/30)
        count = 0
        for i in range(cant_meses):
            # inicia la figura
            f = plt.figure(figsize=(10,5))
            ax = plt.subplot()

            ax.set_title(dia1_mes.strftime('Mes %m del %Y'))
            ax.set_ylabel('Magnitud')

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m "))
            ax.set_xlim([dia1_mes - datetime.timedelta(hours=16),
                         dia31_mes + datetime.timedelta(hours=16)])
            plt.grid(linestyle='--')
            plt.gcf().autofmt_xdate()

            #for en el los datos, break si la semana es mayor, plot si no
            for j in range(count, len(t)):
                if t[j].month!=dia1_mes.month:
                    dia1_mes= dia31_mes + datetime.timedelta(days=1)
                    diaultimo_mes = pd.Period(dia1_mes,freq='M').end_time.date()
                    dia31_mes = datetime.datetime(diaultimo_mes.year,
                                                  diaultimo_mes.month,
                                                  diaultimo_mes.day)
                    break
                else:
                    if  df_catalogo['sensible'][j]:
                        plt.scatter(t[j], df_catalogo['mag'][j], c='tomato')
                    else:
                        plt.scatter(t[j], df_catalogo['mag'][j], c='teal')
                    count+=1

            nombre_imagen = dia1_mes.strftime('%Y-%m') + '.png'
            f.savefig(carpeta_fig + nombre_imagen, dpi=300, bbox_inches='tight')

# Si es un dia o menos:
else:
    hora_plot = datetime.datetime(min(t).year, min(t).month, min(t).day,
                                  min(t).hour)
    cant_horas = int(diferencia_t.seconds/3600) + bool(diferencia_t.seconds%3600)
    count = 0
    for i in range(cant_horas):
        # inicia la figura
        f = plt.figure(figsize=(8,5))
        ax = plt.subplot()
        ax.set_title(hora_plot.strftime('%Y-%m-%d %H:00'))
        ax.set_ylabel('Magnitud')

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.set_xlim([hora_plot - datetime.timedelta(minutes=5),


                     hora_plot + datetime.timedelta(minutes=65)])
        plt.grid(linestyle='--')
        plt.gcf().autofmt_xdate()

        #for en el los datos, break si el dia es mayor, plot si no
        for j in range(count, len(t)):
            if t[j].hour>hora_plot.hour or t[j].day>hora_plot.day:
                hora_plot=datetime.datetime(t[j].year, t[j].month,
                                            t[j].day, t[j].hour)
                break
            else:
                    if  df_catalogo['sensible'][j]:
                        plt.scatter(t[j], df_catalogo['mag'][j], c='tomato')
                    else:
                        plt.scatter(t[j], df_catalogo['mag'][j], c='teal')
                    count+=1

        nombre_imagen = hora_plot.strftime('%Y-%m-%d_%H:00') + '.png'
        f.savefig(carpeta_fig + nombre_imagen, dpi=300, bbox_inches='tight')


plt.close('all')
"""
