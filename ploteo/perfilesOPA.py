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
from tqdm import tqdm  # Librería para la barra de progreso
import webbrowser

# lineas agregadas para eliminar warnings
from PIL import Image
Image.MAX_IMAGE_PIXELS = None  # Esto desactiva el límite de seguridad
from matplotlib.offsetbox import AnchoredText

import warnings
import matplotlib
# Silenciar todos los avisos
warnings.filterwarnings("ignore")

from pathlib import Path
from crea_mapa import *
from lee_catalogo import *

# Configura el idioma a español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') 
except:
    locale.setlocale(locale.LC_TIME, 'es-es')

def tamanio_magnitud(mag):
    tamanio = (mag/1.2)**4.1
    return tamanio

def proyectar_dicc(recta, diccionario, distmin=1):
    if diccionario.empty:
        return diccionario.copy()
        
    a, b = recta  # a = pendiente (m), b = intercepto (c + suma_c)
    
    # Extrae las coordenadas explícitas
    x_sismos = diccionario['lon'].to_numpy()
    y_sismos = diccionario['lat'].to_numpy()
    
    # Calcula la distancia perpendicular absoluta a la recta: ax - y + b = 0
    # Usa np.atleast_1d para asegurar compatibilidad si el DataFrame tiene un solo sismo
    dist = np.abs(a * x_sismos - y_sismos + b) / np.sqrt(a**2 + 1)
    
    # Crea la máscara de filtrado
    condicion = (dist <= distmin) & (diccionario['lon'] >= -90)
    
    return diccionario[condicion].copy()

# Argumentos y carga de datos
catalogo = sys.argv[2] 
df_catalogo = lee_catalogo(catalogo)
df_sensibles = df_catalogo.loc[(df_catalogo['sensible'] == True)]
df_nosensibles = df_catalogo.loc[(df_catalogo['sensible'] == False)]

# Catalogo base para el background
arch_base = "base_2023_2026.dat"

if os.path.exists(arch_base):
    df_base = lee_catalogo(arch_base)
    print(f"\n[DEBUG BASE] Total sismos cargados: {len(df_base)}")
    if not df_base.empty:
        print(f"[DEBUG BASE] Primeras coordenadas -> Lat: {df_base['lat'].iloc[0]}, Lon: {df_base['lon'].iloc[0]}")
else:
    df_base = pd.DataFrame()

# Definir la base de rutas
base_dir = Path("./figuras_turno")
sub_dir = sys.argv[3].split('/')[-1] 
ruta_final = base_dir / sub_dir

# Crea la carpeta y sus padres si no existen
ruta_final.mkdir(parents=True, exist_ok=True)

arch_slab = "./grillas/sam_slab2_dep_02.23.18.xyz"
arch_topo = "./grillas/topochile30.xyz"

tamanio_sensibles = tamanio_magnitud(df_sensibles['mag'])
tamanio_nosensibles = tamanio_magnitud(df_nosensibles['mag'])

min_mag = np.min(df_catalogo['mag'])
max_mag = np.max(df_catalogo['mag'])

# Definición de puntos para perfiles
pto1 = (-72, -19)
pto2 = (-68.4, -18)
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
dfs_rectas = []
dfs_base = []

# PROYECCIÓN DE DATOS
for i in tqdm(range(len(str_rectas)), 
              desc="Proyectando perfiles", 
              bar_format='{desc}: {percentage:3.0f}% |{bar}| {remaining}', 
              colour='#808080'):

    x = lista_x[i]
    xmin, xmax = x[0], x[-1]
    y = m * x + c + suma_c[i]
    lineas.append((x,y))
    recta = (m, c + suma_c[i])

    df = proyectar_dicc(recta, df_catalogo, distmin=1.0)
    dfs_rectas.append(df)

    if not df_base.empty:
        # Se proyecta la base una sola vez por perfil aquí con un distmin adecuado (ej: 1.5 o 2.5 si se requiere más ancho)
        df_b = proyectar_dicc(recta, df_base, distmin=2.5)
        dfs_base.append(df_b) 
    else:
        dfs_base.append(pd.DataFrame())

    largo = (xmax - xmin) * 111.111
    angulo = 90 - np.degrees(np.arctan(m))
    
    if not( Path("grillas/slab%s.tmp"%(str_rectas[i] )).is_file()):
        ejecutable1 = "gmt project %s -C%s/%s -A%s -Fpqrsxyz -W-1.8/1.8 -S -Q -L0/%s -Vn > grillas/slab%s.tmp"%(arch_slab, xmin, y[0], angulo, largo, str_rectas[i])
        os.system(ejecutable1)
        
    if not( Path("grillas/topo%s.tmp"%(str_rectas[i] )).is_file()):
        ejecutable2 = "gmt project %s -C%s/%s -A%s -Fpqrsxyz -W-1.8/1.8 -S -Q -L0/%s -Vn > grillas/topo%s.tmp"%(arch_topo, xmin, y[0], angulo, largo, str_rectas[i])
        os.system(ejecutable2)

# PLOT PLANTA
print("Generando mapa de planta...")
f = plt.figure(figsize=(8,15))
ax = plt.axes(projection = ccrs.PlateCarree())
plotMap(ax, -79, -65.5, -56.5, -16, rios=False, ciudades=False)

if not df_sensibles.empty:
    ax.scatter(df_sensibles['lon'], df_sensibles['lat'], marker='o', s=tamanio_sensibles, c='tomato', linewidth=.4, edgecolors='k', label="Percib.", zorder=15)
if not df_nosensibles.empty:
    ax.scatter(df_nosensibles['lon'], df_nosensibles['lat'], marker='o', s=tamanio_nosensibles, c='teal', linewidth=.4, edgecolors='k', label="No Percib.", zorder=14)

pws = np.arange(int(min_mag), int(round(max_mag)) + 1)
for pw in pws:
    plt.scatter([], [], s=tamanio_magnitud(pw), c="w", label=str(pw), linewidth=1, edgecolors='k', alpha=0.6)

h, l = plt.gca().get_legend_handles_labels()
h, l = h[2:] + h[0:2], l[2:] + l[0:2]

titulo_completo = "SISMICIDAD DE CHILE \nCentro Sismológico Nacional - Universidad de Chile\nPerfiles"
ax.text(0.5, 1.05, titulo_completo, transform=ax.transAxes, fontsize=11, fontweight='bold', ha='center', va='bottom')
ax.plot([0.2, 0.8], [1.04, 1.04], transform=ax.transAxes, color='black', lw=1.5, clip_on=False)

lgd = plt.legend(h, l, labelspacing=1.2, handletextpad=1, borderpad=1, prop={'size': 8}, frameon=True, loc="best", framealpha=0.6, edgecolor="k", facecolor="w", bbox_to_anchor=(0.33, 0.98))
lgd.set_title('Magnitud', prop={'size':10})

for i in range(len(str_rectas)):
    ax.plot(lineas[i][0], lineas[i][1], 'k')
    ax.text(lineas[i][0][0]-1.1, lineas[i][1][0] - 0.2, str_rectas[i], zorder=17)

f.savefig(os.path.join(ruta_final, "Chileplanta_perfiles.png"), format='png', dpi=300, bbox_inches='tight')

# PLOT PERFILES
fig, axes_flat = plt.subplots(7, 2, figsize=(10,20))
axes = axes_flat.flatten()
TAMANIO_FIJO = 30  

for i in tqdm(range(len(str_rectas)), 
              desc="Generando subplots", 
              bar_format='{desc}: {percentage:3.0f}% |{bar}| {remaining}', 
              colour='#808080'):    
    ax = axes[i]
    df = dfs_rectas[i].copy().sort_values(by='mag', ascending=False)
    df_b = dfs_base[i]

    # Graficar background gris si existen datos
    if not df_b.empty:
        ax.scatter(df_b['lon'], -df_b['prof'], 
                   color='gray',      
                   alpha=0.4,         
                   s=5,               
                   marker='.',        
                   zorder=1)          

    df_sens = df[df['sensible'] == True]
    df_nosens = df[df['sensible'] == False]

    try:
        slab = np.loadtxt('grillas/slab%s.tmp'%(str_rectas[i]), usecols=[2,6])
        topo = np.loadtxt('grillas/topo%s.tmp'%(str_rectas[i]), usecols=[2,6])
        ax.plot(slab[:,0], slab[:,1], 'k', lw=1, zorder=5)
        ax.plot(topo[:,0], topo[:,1]/1000, 'k', lw=1, zorder=5)
        ax.set_xlim(min(slab[:,0]), max(slab[:,0]))
    except:
        pass 

    if not df_nosens.empty:
        ax.scatter(df_nosens['lon'], -df_nosens['prof'], color='teal', s=TAMANIO_FIJO, edgecolors='k', linewidths=0.2, alpha=0.8, zorder=10)
    if not df_sens.empty:
        ax.scatter(df_sens['lon'], -df_sens['prof'], color='tomato', s=TAMANIO_FIJO, edgecolors='k', linewidths=0.2, alpha=1.0, zorder=12)

    ax.set_ylim(-200, 10) 
    ax.grid(linestyle='--', alpha=0.4, zorder=0)
    if not i % 2: ax.set_ylabel('Prof. [km]')
    
    loc_at = 1 if str_rectas[i] in ['P03', 'P04'] else 4
    at = AnchoredText(str_rectas[i], prop=dict(size=14), frameon=True, loc=loc_at)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
    ax.add_artist(at)

axes[11].set_xlabel('Lon[°]')
axes[12].set_xlabel('Lon[°]')
fig.delaxes(axes[13])

print("Guardando imagen de perfiles")
fig.savefig(os.path.join(ruta_final, "Perfiles.png"), format='png', dpi=300, bbox_inches='tight')
plt.close('all')

ruta_absoluta = os.path.abspath(ruta_final)
print(f"Las imágenes se han guardado en el servidor de mapas en:\n{ruta_absoluta}")

