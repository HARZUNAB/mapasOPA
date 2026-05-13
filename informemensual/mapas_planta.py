import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.patches as mpatches
import os
import sys
from datetime import datetime
import locale

fecha = sys.argv[3]
fecha_str = str(fecha)
objeto_fecha = datetime.strptime(fecha_str, "%Y%m")
# %B es el nombre completo del mes, %Y es el año de 4 dígitos
resultado = objeto_fecha.strftime("%B %Y")

# Configura el idioma a español (en Windows suele ser 'es-es' o 'Spanish')
# En Linux/Mac suele ser 'es_ES.UTF-8'
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') 
except:
    locale.setlocale(locale.LC_TIME, 'es-es')

fecha_trans = objeto_fecha.strftime("%B %Y").capitalize()

# lineas agregadas para eliminar warnings
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Esto desactiva el límite de seguridad
import warnings
import matplotlib
from PIL import Image
# Silenciar todos los avisos
warnings.filterwarnings("ignore")
Image.MAX_IMAGE_PIXELS = None

from crea_mapa import *
from lee_catalogo import *

def tamanio_magnitud(mag):
    tamanio = (mag/1.2)**4.1
    return tamanio

catalogo = sys.argv[2]
df_catalogo = lee_catalogo(catalogo)
df_mayor5 = df_catalogo.loc[df_catalogo['mag'] >= 5.0].copy()
df_mayor5 = df_mayor5.sort_values(by='mag', ascending=False)
#df_catalogo_sobre5 = df_catalogo.loc[df_catalogo['mag'] >= 5.0].reset_index(drop=True)
df_sensibles = df_catalogo.loc[(df_catalogo['sensible'] == True)]
df_sensibles_reg = df_sensibles.sort_values(by='mag', ascending=False)
df_nosensibles = df_catalogo.loc[(df_catalogo['sensible'] == False)]
df_sens_m5 = df_mayor5.loc[df_mayor5['sensible'] == True]
df_nosens_m5 = df_mayor5.loc[df_mayor5['sensible'] == False]

carpeta_fig = "./figuras/"
nombre_carpeta = catalogo.split('.')[0]
carpeta_fig += catalogo.split('.')[0] + "/"

if not os.path.exists(carpeta_fig):
    print('Creando carpeta...')
    os.makedirs(carpeta_fig)

###############################################################################
# Tratamiento inicial de los datos y contadores
tamanio = tamanio_magnitud(df_catalogo['mag'])
tamanio_sensibles = tamanio_magnitud(df_sensibles['mag'])
tamanio_nosensibles = tamanio_magnitud(df_nosensibles['mag'])

min_mag = np.min(df_catalogo['mag'])
max_mag = np.max(df_catalogo['mag'])
min_prof = np.min(df_catalogo['prof'])
max_prof = np.max(df_catalogo['prof'])

mag2 = 0
mag3 = 0
mag4 = 0
mag5 = 0
mag6 = 0
mag7 = 0
sensibles = 0

for j in range(len(df_catalogo['mag'])):
    mag = df_catalogo['mag'][j]

    if mag>=2 and mag<3:
        mag2+=1
    elif mag>=3 and mag<4:
        mag3+=1
    elif mag>=4 and mag<5:
        mag4+=1
    elif mag>=5 and mag<6:
        mag5+=1
    elif mag>=6 and mag<7:
        mag6+=1

    if df_catalogo['sensible'][j]:
        sensibles+=1

print("La minima magnitud fue %s y la maxima fue %s"%(min_mag, max_mag))
print("La minima profundidad fue %s km y la maxima fue %s km"%(min_prof, max_prof))
print("Hubo %s sismos con magnitud entre 2 y 3"%(mag2))
print("Hubo %s sismos con magnitud entre 3 y 4"%(mag3))
print("Hubo %s sismos con magnitud entre 4 y 5"%(mag4))
print("Hubo %s sismos con magnitud entre 5 y 6"%(mag5))
print("Hubo %s sismos con magnitud entre 6 y 7"%(mag6))

print("\nHubo %s sismos percibidos de un total de %s"%(sensibles, len(df_catalogo['mag'])))

print("Generando mapas...")
print("Al finalizar proceso revise carpeta ./figuras/", os.path.basename(os.path.normpath(carpeta_fig.strip())), sep="")

###############################################################################
# Mapas en planta:
# 1. Definición de límites
limites_mapas_y = [(-24.5, -16), (-32.5, -24), (-40.5, -32),
                   (-48.5, -40), (-56.5, -48), (-33.0, -31.5)]
limites_mapas_x = [(-74, -65.5),  (-76, -67.5), (-77., -69),
                   (-79,-70.5), (-76,-66),(-72.5,-71)]
nuevos_limites_y = []
nuevos_limites_x = []

for i in range(len(limites_mapas_x)):
    latmin, latmax = limites_mapas_y[i]
    lonmin, lonmax = limites_mapas_x[i]
    sismos_dentro = 0 #si encuentra un sismo sale del loop
    for j in range(len(df_catalogo['lon'])):
        if df_catalogo['lon'][j] >= lonmin and df_catalogo['lon'][j] <= lonmax:
            if df_catalogo['lat'][j] >= latmin and df_catalogo['lat'][j] <= latmax:
                sismos_dentro = 1
                break
    if sismos_dentro:
        nuevos_limites_y.append(limites_mapas_y[i])
        nuevos_limites_x.append(limites_mapas_x[i])

limites_mapas_y = nuevos_limites_y
limites_mapas_x = nuevos_limites_x

# 2. Plots en un loop
for i in range(len(limites_mapas_x)):
    latmin, latmax = limites_mapas_y[i]
    lonmin, lonmax = limites_mapas_x[i]
    nombre_imagen = "mapaplanta_" + str(i) + '.png'

    # crear mapa region i
    f = plt.figure(figsize=(8,7))
    ax0 = plt.axes(projection = ccrs.PlateCarree())
    plotMap(ax0, lonmin, lonmax, latmin, latmax, rios=False, ciudades=True)
    ax0.scatter(df_sensibles['lon'], df_sensibles['lat'],  marker='o',
                s=tamanio_sensibles, c='tomato', linewidth=.4,
                edgecolors='k', label="Percib.")
    ax0.scatter(df_nosensibles['lon'], df_nosensibles['lat'],  marker='o',
                s=tamanio_nosensibles, c='teal', linewidth=.4,
                edgecolors='k', label="No Percib.1")

    # Leyenda magnitudes
    pws = np.arange(int(min_mag),int(round(max_mag))+1)
    for pw in pws:
        plt.scatter([], [], s=tamanio_magnitud(pw), c="w",label=str(pw),
                    linewidth=1, edgecolors='k', alpha=0.6)

    h, l = plt.gca().get_legend_handles_labels()
    h = h[2:] + h[0:2]
    l = l[2:] + l[0:2]

    # 1. Creamos la leyenda con un espaciado equilibrado
    lgd = plt.legend(h, l, 
                        labelspacing=1.2,    # Espacio vertical entre filas
                        handletextpad=1,   # Distancia entre círculo y texto
                        borderpad=1,       
                        prop={'size': 8},    # Tamaño de fuente legible pero pequeño
                        frameon=True, 
                        framealpha=0.6, 
                        edgecolor="k", 
                        facecolor="w",
                        bbox_to_anchor=(0.01, 0.99),
                        loc='upper left')
    
    lgd.set_title('Magnitud',prop={'size':10})
    # guardar mapa_i
    plt.tight_layout()
    f.savefig(carpeta_fig + nombre_imagen, dpi=300, bbox_inches='tight')
    #bbox_extra_artists=(lgd,), bbox_inches='tight')#, transparent=True)
plt.close('all')

# 3. Plot Chile
f = plt.figure(figsize=(6,15))
ax0 = plt.axes(projection = ccrs.PlateCarree())
plotMap(ax0, -79, -65.5, -56.5, -16, rios=False, ciudades=False)
ax0.scatter(df_sensibles['lon'], df_sensibles['lat'],  marker='o',
            s=tamanio_sensibles, c='tomato', zorder=20, linewidth=.4,
            edgecolors='k', label="Percib.")
ax0.scatter(df_nosensibles['lon'], df_nosensibles['lat'],  marker='o',
            s=tamanio_nosensibles, c='teal', zorder=18, linewidth=.4,
            edgecolors='k', label="No Percib.2")

# Leyenda magnitudes
pws = np.arange(int(min_mag),int(round(max_mag))+1)
for pw in pws:
    plt.scatter([], [], s=tamanio_magnitud(pw), c="w",label=str(pw),
                linewidth=1, edgecolors='k', alpha=0.6)

h, l = plt.gca().get_legend_handles_labels()
h = h[2:] + h[0:2]
l = l[2:] + l[0:2]

# Titulo del mapa
#titulo_completo = f"SISMICIDAD DE CHILE  {fecha_trans}\nCentro Sismológico Nacional - Universidad de Chile"
titulo_completo = f"SISMICIDAD DE CHILE \nCentro Sismológico Nacional - Universidad de Chile"

# 0.5 es el centro horizontal, 1.05 es un poco arriba del mapa
ax0.text(0.5, 1.05, titulo_completo, 
         transform=ax0.transAxes, 
         fontsize=11, fontweight='bold', 
         ha='center', va='bottom')

# Agrega línea justo debajo
# Los valores [0.3, 0.7] definen que la línea va del 30% al 70% del ancho del mapa
ax0.plot([0.2, 0.8], [1.04, 1.04], 
         transform=ax0.transAxes, 
         color='black', lw=1.5, 
         clip_on=False)

# Leyenda con un espaciado equilibrado
lgd = plt.legend(h, l, 
                     labelspacing=1.2,    # Espacio vertical entre filas
                     handletextpad=1,   # Distancia entre círculo y texto
                     borderpad=1,       
                     prop={'size': 8},    # Tamaño de fuente legible pero pequeño
                     frameon=True, 
                     framealpha=0.6, 
                     edgecolor="k", 
                     facecolor="w",
                     #bbox_to_anchor=(0.33, 0.98))
                     bbox_to_anchor=(0.01, 0.99),
                     loc='upper left')

lgd.set_title('Magnitud',prop={'size':10})

f.savefig(carpeta_fig + "Chileplanta.png", format='png', dpi=300,
          bbox_inches='tight')

# Percibidos por region
# Plot Chile
f = plt.figure(figsize=(6,15))
ax0 = plt.axes(projection = ccrs.PlateCarree())
plotMap(ax0, -79, -65.5, -56.5, -16, rios=False, ciudades=False)

# Define tamaño fijo para todos los puntos
TAMANIO_FIJO = 40 

# Graficar Percibidos con tamaño fijo
ax0.scatter(df_sensibles_reg['lon'], df_sensibles_reg['lat'], 
            s=TAMANIO_FIJO, 
            c='tomato', 
            zorder=20, 
            linewidth=.4, 
            edgecolors='k', 
            label="Percib.")

h, l = ax0.get_legend_handles_labels()

# título del mapa
#titulo_completo = f"SISMICIDAD DE CHILE  {fecha_trans}\nCentro Sismológico Nacional - Universidad de Chile\nPercibidos por región"
titulo_completo = f"SISMICIDAD DE CHILE \nCentro Sismológico Nacional - Universidad de Chile\nPercibidos por región"

# 0.5 es el centro horizontal, 1.05 es un poco arriba del mapa
ax0.text(0.5, 1.05, titulo_completo, 
         transform=ax0.transAxes, 
         fontsize=11, fontweight='bold', 
         ha='center', va='bottom')

# Agrega línea justo debajo
# Los valores [0.3, 0.7] definen que la línea va del 30% al 70% del ancho del mapa
ax0.plot([0.2, 0.8], [1.04, 1.04], 
         transform=ax0.transAxes, 
         color='black', lw=1.5, 
         clip_on=False)

lgd = plt.legend(h, l, 
                 labelspacing=1.2,
                 prop={'size': 9},
                 frameon=True, 
                 bbox_to_anchor=(0.01, 0.99),
                 loc='upper left')

# Fuerza que los iconos de la leyenda tengan el tamaño fijo
for handle in lgd.legendHandles:
    handle._sizes = [TAMANIO_FIJO]

f.savefig(carpeta_fig + "Percibidosregion.png", format='png', dpi=300,
          bbox_inches='tight')

# Sobre 5
# Plot Chile
# Filtrar los DataFrames para magnitudes >= 5.0
df_sens_m5 = df_sensibles[df_sensibles['mag'] >= 5.0]
df_nosens_m5 = df_nosensibles[df_nosensibles['mag'] >= 5.0]

# Unifica para obtener estadísticas
df_m5_total = pd.concat([df_sens_m5, df_nosens_m5])

#print(df_m5_total)

if not df_m5_total.empty:
    mag_max_m5 = df_m5_total['mag'].max()
    # Orden cronológico para que la numeración sea lógica (del primero al último del mes)
    df_m5_total = df_m5_total.sort_values(by='fecha').reset_index(drop=True)
    num_m5 = len(df_m5_total)
    
    f = plt.figure(figsize=(7, 15)) 
    ax0 = plt.axes(projection=ccrs.PlateCarree())
    plotMap(ax0, -92, -53.0, -64.0, -16, rios=False, ciudades=False)

    TAMANIO_FIJO = 45
    lista_detalles = [] 

    # Graficar y numera eventos con un id para identificarlo
    for i, row in df_m5_total.iterrows():
        id_evento = i + 1
        color_punto = 'tomato' if row['sensible'] else 'teal'
        
        # Epicentro
        ax0.scatter(row['lon'], row['lat'], marker='o', s=TAMANIO_FIJO, 
                    c=color_punto, zorder=20, linewidth=.4, edgecolors='k')

        # Número identificador (con pequeño desplazamiento para no quedar sobre el circulo)
        ax0.text(row['lon'] + 0.6, row['lat'], str(id_evento), 
                 fontsize=7, fontweight='bold', va='center', ha='left',
                 zorder=25, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0.1))

        # Formatea datos para la tabla
        try:
            fecha_utc = pd.to_datetime(row['fecha'], errors='coerce')
            hora_local = fecha_utc - pd.Timedelta(hours=4)
            fecha_fmt = hora_local.strftime('%d/%m %H:%M:%S')
        except:
            fecha_fmt = "S/F"
            
        info = f"{id_evento:2d}. | {fecha_fmt} | {row['mag']:.1f} {row['type_mag']}"
        lista_detalles.append(info)

    # Simbología de magnitudes (Círculos de referencia)
    pws = np.arange(5, int(round(max_mag)) + 1)
    for pw in pws:
        plt.scatter([], [], s=tamanio_magnitud(pw), c="w", label=str(pw),
                    linewidth=1, edgecolors='k', alpha=0.6)

    h, l = ax0.get_legend_handles_labels()
    # Reordena magnitudes primero, luego los dos estados (Percibido/No Percibido)
    h = h[2:] + h[0:2]
    l = l[2:] + l[0:2]

    # Título Principal
    titulo_m5 = (f"SISMICIDAD DE CHILE\n"
                 f"Eventos Magnitud ≥ 5.0 ({num_m5} sismos)\n"
                 f"Máxima magnitud del mes: M{mag_max_m5}")

    ax0.text(0.5, 1.05, titulo_m5, transform=ax0.transAxes, 
             fontsize=11, fontweight='bold', ha='center', va='bottom')
    ax0.plot([0.2, 0.8], [1.04, 1.04], transform=ax0.transAxes, color='black', lw=1.5, clip_on=False)

    #print('h', h)
    #print('l', l)

    # Asegurar que los puntos en la leyenda tengan el tamaño visual del mapa
    for handle in lgd.legendHandles:
        handle._sizes = [TAMANIO_FIJO]

    # Tabla de parámetros (Esquina inferior)
    # Si hay muchos sismos, la tabla se puede dividir para no tapar el mapa
    texto_leyenda = "DETALLE DE EVENTOS:\n" + "\n".join(lista_detalles)
    
    ax0.text(0.02, 0.02, texto_leyenda, 
             transform=ax0.transAxes, 
             fontsize=6, 
             family='monospace', # Fundamental para que las columnas se alineen
             linespacing=1.5,
             va='bottom', ha='left',
             zorder=30,
             bbox=dict(facecolor='white', alpha=0.9, edgecolor='black', linewidth=0.5, boxstyle='round,pad=0.5'))

    # Guardado
    ruta_m5 = os.path.join(carpeta_fig, "Sobre5.png")
    f.savefig(ruta_m5, format='png', dpi=300, bbox_inches='tight')
    plt.close(f)
    #print(f"✅ Mapa indexado generado con {num_m5} eventos.")
else:
    print("ℹ️ No se encontraron eventos de magnitud >= 5.0 para graficar.")

# 4. ANTÁRTICA
plot_antartica = False

for j in range(len(df_catalogo['lon'])):
    if df_catalogo['lon'][j] >= -64 and df_catalogo['lon'][j] <= -56:
        if df_catalogo['lat'][j] >= -64.8 and df_catalogo['lat'][j] <= -58:
            plot_antartica = True
            break

if plot_antartica:
    f = plt.figure(figsize=(8,8))
    ax0 = plt.axes(projection = ccrs.PlateCarree())
    plotMap(ax0, -64, -56, -64.8, -58, rios=False, ciudades=False)
    ax0.scatter(df_sensibles['lon'], df_sensibles['lat'],  marker='o',
                s=tamanio_sensibles, c='tomato', zorder=20, linewidth=.4,
                edgecolors='k', label="Percib.")
    ax0.scatter(df_nosensibles['lon'], df_nosensibles['lat'],  marker='o',
                s=tamanio_nosensibles, c='teal', zorder=18, linewidth=.4,
                edgecolors='k', label="No Percib.4")

    # Leyenda magnitudes
    pws = np.arange(int(min_mag),int(round(max_mag))+1)
    for pw in pws:
        plt.scatter([], [], s=tamanio_magnitud(pw), c="w",label=str(pw),
                    linewidth=1, edgecolors='k', alpha=0.6)

    h, l = plt.gca().get_legend_handles_labels()
    h = h[2:-1] + h[0:2]
    l = l[2:-1] + l[0:2]
    
    # leyenda con un espaciado equilibrado
    lgd = plt.legend(h, l, 
                     labelspacing=1.2,    # Espacio vertical entre filas
                     handletextpad=1.0,   # Distancia entre círculo y texto
                     borderpad=1.0,       
                     prop={'size': 8},    # Tamaño de fuente legible pero pequeño
                     frameon=True, 
                     framealpha=0.6, 
                     edgecolor="k", 
                     facecolor="w",
                     bbox_to_anchor=(0.01, 0.99),
                     loc='upper left')
                     #bbox_to_anchor=(0.20, 0.98))
    
    lgd.set_title('Magnitudes', prop={'size': 10})

    f.savefig(carpeta_fig + "Antartica_planta.png", format='png', dpi=300,
              bbox_inches='tight')

# Mapa INSULAR
plot_insular = False
for j in range(len(df_catalogo['lon'])):
    if df_catalogo['lon'][j] >= -110 and df_catalogo['lon'][j] <= -70:
        if df_catalogo['lat'][j] >= -47 and df_catalogo['lat'][j] <= -25:
            plot_insular = True
            break

if plot_insular:
    f = plt.figure(figsize=(8,8))
    ax0 = plt.axes(projection = ccrs.PlateCarree())
    plotMap(ax0, -110, -70, -47, -25, rios=False, ciudades=False)
    ax0.scatter(df_sensibles['lon'], df_sensibles['lat'],
                marker='o', s=tamanio_sensibles, c='tomato', zorder=20, linewidth=.4,
                edgecolors='k', label="Percib.")
    ax0.scatter(df_nosensibles['lon'], df_nosensibles['lat'],
             marker='o', s=tamanio_nosensibles, c='teal', zorder=18, linewidth=.4,
             edgecolors='k', label="No Percib.insular5")

    # Leyenda magnitudes
    pws = np.arange(int(min_mag),int(round(max_mag))+1)
    for pw in pws:
        plt.scatter([], [], s=tamanio_magnitud(pw), c="w",label=str(pw),
                    linewidth=1, edgecolors='k', alpha=0.6)
    h, l = plt.gca().get_legend_handles_labels()
    h = h[2:-1] + h[0:2]
    l = l[2:-1] + l[0:2]

    # leyenda con un espaciado equilibrado
    lgd = plt.legend(h, l, 
                     labelspacing=1.2,    # Espacio vertical entre filas
                     handletextpad=1,   # Distancia entre círculo y texto
                     borderpad=1,       
                     prop={'size': 8},    # Tamaño de fuente legible pero pequeño
                     frameon=True, 
                     framealpha=0.6, 
                     edgecolor="k", 
                     facecolor="w",
                     bbox_to_anchor=(0.01, 0.99),
                     loc='upper left')

    lgd.set_title('Magnitud',prop={'size':10})

    if plot_insular:
        ax0.add_patch(mpatches.Rectangle((-114, -30), 7, 6,
                      edgecolor = 'k', facecolor = 'none',
                      fill=True, lw=4))
    f.savefig(carpeta_fig + "Insular_planta.png", format='png', dpi=300,
              bbox_inches='tight')

# 5. ISLA DE PASCUA ??? v1   
plot_pascua1 = False
for j in range(len(df_catalogo['lon'])):
    if df_catalogo['lon'][j] >= -120 and df_catalogo['lon'][j] <= -80:
        if df_catalogo['lat'][j] >= -43 and df_catalogo['lat'][j] <= -20:
            plot_pascua1 = True
            break

plot_pascua2 = False
for j in range(len(df_catalogo['lon'])):
    if df_catalogo['lon'][j] >= -114 and df_catalogo['lon'][j] <= -107:
        if df_catalogo['lat'][j] >= -30 and df_catalogo['lat'][j] <= -24:
            plot_pascua2 = True
            break

if plot_pascua1:
    f = plt.figure(figsize=(8,8))
    ax0 = plt.axes(projection = ccrs.PlateCarree())
    plotMap(ax0, -120, -80, -43, -20, rios=False, ciudades=False)
    ax0.scatter(df_sensibles['lon'], df_sensibles['lat'],
                marker='o', s=tamanio_sensibles, c='tomato', zorder=20, linewidth=.4,
                edgecolors='k', label="Percib.")
    ax0.scatter(df_nosensibles['lon'], df_nosensibles['lat'],
             marker='o', s=tamanio_nosensibles, c='teal', zorder=18, linewidth=.4,
             edgecolors='k', label="No Percib.6")

    # Leyenda magnitudes
    pws = np.arange(int(min_mag),int(round(max_mag))+1)
    for pw in pws:
        plt.scatter([], [], s=tamanio_magnitud(pw), c="w",label=str(pw),
                    linewidth=1, edgecolors='k', alpha=0.6)
    h, l = plt.gca().get_legend_handles_labels()
    h = h[2:-1] + h[0:2]
    l = l[2:-1] + l[0:2]

    # leyenda con un espaciado equilibrado
    lgd = plt.legend(h, l, 
                     labelspacing=1.2,    # Espacio vertical entre filas
                     handletextpad=1,   # Distancia entre círculo y texto
                     borderpad=1,       
                     prop={'size': 8},    # Tamaño de fuente legible pero pequeño
                     frameon=True, 
                     framealpha=0.6, 
                     edgecolor="k", 
                     facecolor="w",
                     #bbox_to_anchor=(0.20, 0.98))
                     bbox_to_anchor=(0.01, 0.99),
                     loc='upper left')

    lgd.set_title('Magnitud',prop={'size':10})

    if plot_pascua2:
        ax0.add_patch(mpatches.Rectangle((-114, -30), 7, 6,
                      edgecolor = 'k', facecolor = 'none',
                      fill=True, lw=4))
    f.savefig(carpeta_fig + "Pascua_planta1.png", format='png', dpi=300,
              bbox_inches='tight')

if plot_pascua2:
    f = plt.figure(figsize=(8,8))
    ax0 = plt.axes(projection = ccrs.PlateCarree())
    plotMap(ax0, -114, -107, -30, -24, rios=False, ciudades=False)
    ax0.scatter(df_sensibles['lon'], df_sensibles['lat'],
                 marker='o', s=tamanio_sensibles, c='tomato', zorder=20, linewidth=.4,
                 edgecolors='k', label="Precib.")
    ax0.scatter(df_nosensibles['lon'], df_nosensibles['lat'],
             marker='o', s=tamanio_nosensibles, c='teal', zorder=18, linewidth=.4,
             edgecolors='k', label="No Percib.7")
    f.savefig(carpeta_fig + "Pascua_planta2.png", format='png', dpi=300,
              bbox_inches='tight')

plt.close('all')

print("Mapas planta generados ✅")