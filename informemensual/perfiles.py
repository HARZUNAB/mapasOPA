#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.patches as mpatches
import cartopy
import matplotlib.dates as mdates
import pandas as pd
import datetime
from datetime import datetime
import sys, os
import locale
from pathlib import Path

# lineas agregadas para eliminar warnings
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Esto desactiva el límite de seguridad
#from mpl_toolkits.axes_grid.anchored_artists import AnchoredText
# se cambia linea anterior por la siguiente que es para versiones antiguas
from matplotlib.offsetbox import AnchoredText

import warnings
import matplotlib
from PIL import Image
# Silenciar todos los avisos
warnings.filterwarnings("ignore")
Image.MAX_IMAGE_PIXELS = None

from pathlib import Path
from crea_mapa import *
from lee_catalogo import *

fecha = sys.argv[3]

fecha_str = str(fecha)

# objeto datetime (especificando el formato AñoMes)
objeto_fecha = datetime.strptime(fecha_str, "%Y%m")

# Formateo a texto
# %B es el nombre completo del mes, %Y es el año de 4 dígitos
resultado = objeto_fecha.strftime("%B %Y")

# Configura el idioma a español
# En Linux suele ser 'es_ES.UTF-8'
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') 
except:
    locale.setlocale(locale.LC_TIME, 'es-es')

fecha_trans = objeto_fecha.strftime("%B %Y").capitalize()

def tamanio_magnitud(mag):
    tamanio = (mag/1.2)**4.1
    return tamanio

def proyectar_prof(recta, longitudes, latitudes, profundidades, error_lon=[], error_lat=[], error_prof=[],dist_min=0.8):
    # recta = tupla con pendiente y coef posicion
    # a x + b = y
    a, b = recta
    long_project = []
    prof_project = []
    lat_project = []
    errlon_project=[]
    errlat_project=[]
    errprof_project=[]
    for i in range(len(longitudes)):
        distancia = np.abs(a * longitudes[i] - latitudes[i] + b) / np.sqrt(a**2 + 1)
        if distancia <= dist_min:
            long_project.append(longitudes[i])
            prof_project.append(profundidades[i])
            lat_project.append(latitudes[i])

            if error_lon:
                errlon_project.append(error_lon[i])
            if error_lat:
                errlat_project.append(error_lat[i])
            if error_prof:
                errprof_project.append(error_prof[i])

    return long_project, lat_project, prof_project,

def proyectar_dicc(recta, diccionario, distmin=1):
    # recta = tupla con pendiente y coef posicion
    # a x + b = y
    a, b = recta
    out_dicc = pd.DataFrame(columns=diccionario.columns)

    for index, row in  diccionario.iterrows():
        dist = np.abs(a * row['lon'] - row['lat'] + b) / np.sqrt(a**2 + 1)

        if dist <= distmin:
            if row['lon']< -90: continue
            #out_dicc = out_dicc.append(row, ignore_index=True)
            out_dicc = pd.concat([out_dicc, pd.DataFrame([row])], ignore_index=True)
    return out_dicc

catalogo = sys.argv[2] # ----- Aparece 2 y no 1. ??
df_catalogo = lee_catalogo(catalogo)
df_sensibles = df_catalogo.loc[(df_catalogo['sensible'] == True)]
df_nosensibles = df_catalogo.loc[(df_catalogo['sensible'] == False)]

# =========================================================================
# RUTAS DINÁMICAS PARA EL CATÁLOGO BASE BACKGROUND
# =========================================================================
DIRECTORIO_SCRIPT = Path(__file__).resolve().parent
CARPETA_GRILLAS = DIRECTORIO_SCRIPT / "grillas"

# Definimos el nombre del archivo base
NOMBRE_BASE = "base_2025.dat"

# 1. Intentamos buscarlo en el directorio actual desde donde se corre
arch_base = Path(NOMBRE_BASE)

# 2. Si no está ahí, lo buscamos dinámicamente en la carpeta raíz del script
if not arch_base.exists():
    arch_base = DIRECTORIO_SCRIPT / NOMBRE_BASE

# Carga de catálogo base asistida por Path
if arch_base.exists():
    df_base = lee_catalogo(str(arch_base))
else:
    df_base = pd.DataFrame()  # DataFrame vacío si no existe en ningún lado

carpeta_fig = "./figuras/"
nombre_carpeta = catalogo.split('.')[0]
carpeta_fig += catalogo.split('.')[0] + "/"

if not os.path.exists(carpeta_fig):
    os.makedirs(carpeta_fig)

arch_slab = "./grillas/sam_slab2_dep_02.23.18.xyz"
arch_topo = "./grillas/topochile30.xyz"

tamanio = tamanio_magnitud(df_catalogo['mag'])
tamanio_sensibles = tamanio_magnitud(df_sensibles['mag'])
tamanio_nosensibles = tamanio_magnitud(df_nosensibles['mag'])

min_mag = np.min(df_catalogo['mag'])
max_mag = np.max(df_catalogo['mag'])

# FALTA: comprobar si existe la carpeta grillas y si no crearla 

pto1 = (-72, -19)
pto2 = (-68.4, -18)
x = np.linspace(pto1[0],pto2[0]+1)
lista_x = [np.linspace(pto1[0], pto2[0] + 1),
           np.linspace(pto1[0], pto2[0] + 1),
           np.linspace(pto1[0], pto2[0] + 2),
           np.linspace(pto1[0], pto2[0] + 2),
           np.linspace(pto1[0] - 1, pto2[0] + 1),
           np.linspace(pto1[0] - 1, pto2[0] + 1),
           np.linspace(pto1[0] - 2, pto2[0] + 1),
           np.linspace(pto1[0] - 2, pto2[0] + 1),
           np.linspace(pto1[0] - 3, pto2[0]),
           np.linspace(pto1[0] - 4, pto2[0] - 1),
           np.linspace(pto1[0] - 4, pto2[0] - 1),
           np.linspace(pto1[0] - 4, pto2[0] - 1),
           np.linspace(pto1[0] - 5, pto2[0] - 2)]

m, c = np.polyfit([pto1[0], pto2[0]], [pto1[1], pto2[1]], 1)
suma_c = [-1, -3, -5, -6, -8, -10, -12, -14, -16, -18, -20, -22, -24]

str_rectas = ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09",
              "P010", "P011", "P012", "P013" ]
lineas = []
rectas = []
dfs_rectas = []

dfs_base = []
for i in range(len(str_rectas)):
    x = lista_x[i]
    xmin, xmax = x[0], x[-1]
    y = m * x + c + suma_c[i]

    linea = (x,y)
    lineas.append(linea)

    recta = (m, c + suma_c[i])
    rectas.append(recta)

    ### aca proyectar datos base ###
    df = proyectar_dicc(recta, df_catalogo)
    dfs_rectas.append(df)

    # Proyecta catálogo base usando la misma recta
    if not df_base.empty:
        df_b = proyectar_dicc(recta, df_base)
        # Guarda dataframes en una lista nueva para usarlos luego
        dfs_base.append(df_b) 
    else:
        dfs_base.append(pd.DataFrame())

    largo = (xmax - xmin) * 111.111
    angulo = 90 - np.degrees(np.arctan(m))
    
    # RUTAS ABSOLUTAS DINÁMICAS PARA GMT
    # Aseguramos que la carpeta grillas exista donde reside el script
    CARPETA_GRILLAS = Path(__file__).resolve().parent / "grillas"
    CARPETA_GRILLAS.mkdir(parents=True, exist_ok=True)

    # Definimos los archivos temporales con rutas absolutas
    ruta_tmp_slab = CARPETA_GRILLAS / f"slab{str_rectas[i]}.tmp"
    ruta_tmp_topo = CARPETA_GRILLAS / f"topo{str_rectas[i]}.tmp"

    largo = (xmax - xmin) * 111.111
    angulo = 90 - np.degrees(np.arctan(m))
    
    if not ruta_tmp_slab.is_file():
        # Usamos str(ruta_tmp_slab) para pasarle a GMT la ubicación exacta y absoluta
        ejecutable1 = "gmt project %s -C%s/%s -A%s -Fpqrsxyz -W-1.8/1.8 -S -Q -L0/%s -Vn > %s" % (
            arch_slab, xmin, y[0], angulo, largo, str(ruta_tmp_slab)
        )
        os.system(ejecutable1)
        
    if not ruta_tmp_topo.is_file():
        # Usamos str(ruta_tmp_topo) para pasarle a GMT la ubicación exacta y absoluta
        ejecutable2 = "gmt project %s -C%s/%s -A%s -Fpqrsxyz -W-1.8/1.8 -S -Q -L0/%s -Vn > %s" % (
            arch_topo, xmin, y[0], angulo, largo, str(ruta_tmp_topo)
        )
        os.system(ejecutable2)

#-----------------------Plot Chile-------------------------------------------------------------------------------------

f = plt.figure(figsize=(8,15))
ax = plt.axes(projection = ccrs.PlateCarree())

plotMap(ax, -79, -65.5, -56.5, -16, rios=False, ciudades=False)

if not tamanio_sensibles.empty:
    ax.scatter(df_sensibles['lon'], df_sensibles['lat'],  marker='o',
               s=tamanio_sensibles, c='tomato',  linewidth=.4,
               edgecolors='k', label="Percib.")
else:
    ax.scatter(df_sensibles['lon'], df_sensibles['lat'],  marker='',
               s=tamanio_sensibles, c='tomato',  linewidth=.4,
               edgecolors='k')
if not tamanio_nosensibles.empty:
    ax.scatter(df_nosensibles['lon'], df_nosensibles['lat'],  marker='o',
               s=tamanio_nosensibles, c='teal', linewidth=.4,
               edgecolors='k', label="No Percib.")
else:
    ax.scatter(df_nosensibles['lon'], df_nosensibles['lat'],  marker='',
               s=tamanio_nosensibles, c='teal', linewidth=.4,
               edgecolors='k')

# Leyenda magnitudes
pws = np.arange(int(min_mag),int(round(max_mag))+1)
for pw in pws:
    plt.scatter([], [], s=tamanio_magnitud(pw), c="w",label=str(pw),
                linewidth=1, edgecolors='k', alpha=0.6)

#----------------------------------------------------------------------------------

h, l = plt.gca().get_legend_handles_labels()
h = h[2:] + h[0:2]
l = l[2:] + l[0:2]

# Título:
#titulo_completo = f"SISMICIDAD DE CHILE  {fecha_trans}\nCentro Sismológico Nacional - Universidad de Chile\nPerfiles"
titulo_completo = f"SISMICIDAD DE CHILE \nCentro Sismológico Nacional - Universidad de Chile\nPerfiles"

# 0.5 es el centro horizontal, 1.05 es un poco arriba del mapa
ax.text(0.5, 1.05, titulo_completo, 
         transform=ax.transAxes, 
         fontsize=11, fontweight='bold', 
         ha='center', va='bottom')

# agrega línea justo debajo
# Los valores [0.3, 0.7] definen que la línea va del 30% al 70% del ancho del mapa
ax.plot([0.2, 0.8], [1.04, 1.04], 
         transform=ax.transAxes, 
         color='black', lw=1.5, 
         clip_on=False)

lgd = plt.legend(h, l, 
                     labelspacing=1.2,    # Espacio vertical entre filas
                     handletextpad=1,   # Distancia entre círculo y texto
                     borderpad=1,       
                     prop={'size': 8},    # Tamaño de fuente legible pero pequeño
                     frameon=True,
                     loc="best", 
                     framealpha=0.6, 
                     edgecolor="k", 
                     facecolor="w",
                     bbox_to_anchor=(0.33, 0.98))
                     
lgd.set_title('Magnitud',prop={'size':10})

for i in range(len(str_rectas)):
    ax.plot(lineas[i][0], lineas[i][1],'k', label='perfiles')
    ax.text(lineas[i][0][0]-1.1, lineas[i][1][0] - 0.2, str_rectas[i], zorder=17)

f.savefig(carpeta_fig + "Chileplanta_perfiles.png", format='png', dpi=300,
            bbox_inches='tight')

#-----------------------PLot de perfiles -----------------------------

fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6), (ax7, ax8), (ax9, ax10),
      (ax11, ax12), (ax13, ax14)) = plt.subplots(7, 2, figsize=(10,20))

axes = [ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9, ax10,
        ax11, ax12, ax13, ax14]

TAMANIO_FIJO = 30  # El tamaño que deseamos para el catálogo actual

for i in range(len(str_rectas)):
    ax = axes[i]
    
    # obtiene y ordena el catálogo actual para este perfil
    # se usa .copy() para evitar warnings de Pandas y ordena por magnitud
    df = dfs_rectas[i].copy()
    df = df.sort_values(by='mag', ascending=False)

    #print(df)
    
    # obtiene el catálogo base
    df_b = dfs_base[i]

    # plotea catalogo base (fondo) ---> background ? 
    if not df_b.empty:
        ax.scatter(df_b['lon'], -df_b['prof'], color='lightgrey', 
                   alpha=0.3, s=10, zorder=1, label='Base')

    # filtra catalogo actual
    # Aseguramos que el filtro sea sobre el df ya proyectado y ordenado
    df_sens = df[df['sensible'] == True]
    df_nosens = df[df['sensible'] == False]

    #print('percibidos')
    #print(df_sens)
    #print('no percibidos')
    #print(df_nosens)

    """
    # plotea elemento geograficos
    try:
        slab = np.loadtxt('grillas/slab%s.tmp'%(str_rectas[i]), usecols=[2,6])
        topo = np.loadtxt('grillas/topo%s.tmp'%(str_rectas[i]), usecols=[2,6])
        ax.plot(slab[:,0], slab[:,1], 'k', lw=1, zorder=5)
        ax.plot(topo[:,0], topo[:,1]/1000, 'k', lw=1, zorder=5)
        ax.set_xlim(min(slab[:,0]), max(slab[:,0]))
    except:
        pass # Por si falta algún archivo de grilla
    """

    # =========================================================================
    # RUTA DINÁMICA DE GRILLAS GMT (.tmp)
    # =========================================================================
    # Redefinimos la ruta de la carpeta para que el bucle de ploteo la conozca
    CARPETA_GRILLAS = Path(__file__).resolve().parent / "grillas"

    # Construye la ruta absoluta hacia los archivos temporales de forma segura
    ruta_slab_tmp = CARPETA_GRILLAS / f"slab{str_rectas[i]}.tmp"
    ruta_topo_tmp = CARPETA_GRILLAS / f"topo{str_rectas[i]}.tmp"

    slab = None
    topo = None

    # Carga de Slab de forma segura si el archivo físico existe
    if ruta_slab_tmp.exists():
        try:
            slab = np.loadtxt(str(ruta_slab_tmp), usecols=[2, 6])
        except Exception as e:
            print(f"⚠️ Error al leer las columnas de slab en {ruta_slab_tmp.name}: {e}")

    # Carga de Topografía de forma segura si el archivo físico existe
    if ruta_topo_tmp.exists():
        try:
            topo = np.loadtxt(str(ruta_topo_tmp), usecols=[2, 6])
        except Exception as e:
            print(f"⚠️ Error al leer las columnas de topografía en {ruta_topo_tmp.name}: {e}")

    # Grafica las líneas de las grillas solo si se cargaron correctamente en memoria
    if slab is not None:
        ax.plot(slab[:, 0], slab[:, 1], 'k', lw=1, zorder=5)
        ax.set_xlim(min(slab[:, 0]), max(slab[:, 0]))
        
    if topo is not None:
        ax.plot(topo[:, 0], topo[:, 1] / 1000, 'k', lw=1, zorder=5)

    # plotea catalogo actual (encima)
    # grafica no percibidos
    if not df_nosens.empty:
        ax.scatter(df_nosens['lon'], -df_nosens['prof'], color='teal', 
                   s=TAMANIO_FIJO, edgecolors='k', linewidths=0.2, 
                   alpha=0.8, zorder=10)
    
    # grafica percibidos
    if not df_sens.empty:
        ax.scatter(df_sens['lon'], -df_sens['prof'], color='tomato', 
                   s=TAMANIO_FIJO, edgecolors='k', linewidths=0.2, 
                   alpha=1.0, zorder=12)

    # ajusta eje y estetica
    ax.set_ylim(-200, 10) # ajuste para eliminar espacio en el margen inferior
    ax.grid(linestyle='--', alpha=0.4, zorder=0)

    if not i%2: 
        ax.set_ylabel('Prof. [km]')
    
    at = AnchoredText(str_rectas[i], prop=dict(size=14), frameon=True, loc=4)
    if str_rectas[i]=='P03' or str_rectas[i]=='P04':
        at = AnchoredText(str_rectas[i], prop=dict(size=14), frameon=True,
                        loc=1)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
    ax.add_artist(at)

ax12.set_xlabel('Lon[°]')
ax13.set_xlabel('Lon[°]')
fig.delaxes(ax14)

fig.savefig(carpeta_fig + "Perfiles.png", format='png', dpi=300,
            bbox_inches='tight')
plt.close('all')

print("Mapas perfiles generados ✅")
