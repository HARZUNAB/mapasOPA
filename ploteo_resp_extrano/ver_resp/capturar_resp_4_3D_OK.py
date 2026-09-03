#!/usr/bin/env python3
import os
import sys
import re
import time
import numpy as np
#import pyperclip
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.patheffects
import csv 
from math import radians, cos, sin, asin, sqrt
import math
from adjustText import adjust_text

def ruta_datos():
    """
    Resuelve el directorio donde viven los datos de la instalación.
    Prioridad: variable de entorno NEWPT_DATA_DIR (definida por newpt.sh),
    luego el directorio del binario (PyInstaller) o el del script en desarrollo.
    """
    env = os.environ.get("NEWPT_DATA_DIR")
    if env:
        return env
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

DATOS_DIR = ruta_datos()
GR_DIR = os.path.join(DATOS_DIR, "grillas")
OUTPUT_FILE = os.path.join(DATOS_DIR, "datos_seiscomp.csv")
ARCHIVO_TMP = os.path.join(DATOS_DIR, "evento_data.txt")

def mostrar_avance(paso, total, mensaje):
    """
    Dibuja una barra de progreso en la terminal.
    """
    longitud_barra = 20
    porcentaje = int((paso / total) * 100)
    bloques = int((paso / total) * longitud_barra)
    rango_barra = "█" * bloques + "-" * (longitud_barra - bloques)
    
    sys.stdout.write(f"\r[NewPT] |{rango_barra}| {porcentaje}% - {mensaje}")
    sys.stdout.flush()

def calcular_distancia(lon1, lat1, lon2, lat2):
    # Radio de la Tierra en km
    R = 6371.0
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def obtener_rumbo(lon1, lat1, lon2, lat2):
    # Calcula el ángulo (bearing) entre dos puntos
    dLon = math.radians(lon2 - lon1)
    y = math.sin(dLon) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dLon)
    
    brng = (math.degrees(math.atan2(y, x)) + 360) % 360
    
    # Mapeo de ángulos a puntos cardinales
    direcciones = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
    return direcciones[round(brng / 45)]

def inicializar_csv():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(",Fecha_Hora,Latitud,Longitud,Prof.,Mag.,Tipo_mag.,Analista,Event_id,phases\n")
    print("[INFO] CSV reiniciado con éxito.")

#
def plotear_evento(fecha, lat, lon, prof, mag, event_id, texto_magnitud):
    """
    Genera ventanas sismotectónicas locales dinámicas integrando el archivo
    de relieve real NE2_LR_LC_SR_W_DR.tif para la vista en planta.
    """
    # === ETAPA 1: Iniciando lectura ===
    mostrar_avance(1, 4, "Filtrando sismicidad histórica...")
    
    # Configuración de estilo limpia
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    fig = plt.figure(figsize=(14, 6.5))
    #fig.suptitle("NewPT · Contexto Sismotectónico", 
    #             fontsize=13, fontweight='bold', y=0.985)
    fig.text(0.5, 0.95, f"{fecha} | {texto_magnitud} | Profundidad: {prof} km | {event_id}",
             ha='center', fontsize=9, color='#444444')
    try:
        fig.canvas.manager.set_window_title("NewPT · Contexto Sismotectónico")
    except Exception:
        pass
    
    size = 90 # tamaño del circulo representando al evento en los mapas
    RANGO_ANCHURA = 2.5 

    # =========================================================================
    # 1. CARGA EXPRESO DEL BACKGROUND SÍSMICO (Sismos grises)
    # =========================================================================
    arch_base = os.path.join(DATOS_DIR, "base_2023_2026.dat")
    lon_b, lat_b, prof_b = [], [], []
    if os.path.exists(arch_base):
        try:
            with open(arch_base, 'r') as f:
                for linea in f:
                    partes = linea.strip().split()
                    if len(partes) >= 5:
                        ln = float(partes[3]) 
                        lt = float(partes[2]) 
                        if (lon - RANGO_ANCHURA <= ln <= lon + RANGO_ANCHURA) and (lat - RANGO_ANCHURA <= lt <= lat + RANGO_ANCHURA):
                            lon_b.append(ln)
                            lat_b.append(lt)
                            prof_b.append(float(partes[4])) 
        except Exception as e:
            print(f"[Aviso] No se pudo cargar el background sísmico: {e}")

    # === ETAPA 2: Finalizó carga de catálogo, iniciamos búsqueda de grillas ===
    mostrar_avance(2, 4, "Buscando perfil óptimo de subducción (Slab)...")

    # =========================================================================
    # 2. SELECCIÓN INTELIGENTE Y CARGA DE SUBDUCCIÓN Y TOPOGRAFÍA (CORREGIDO)
    # =========================================================================
    lon_slab, prof_slab = [], []
    lon_topo, alt_topo = [], []
    usando_global = False
    mejor_perfil_nombre = None
    distancia_minima = float('inf')
    datos_perfil_elegido = []
    lat_min_perfil = float('inf')
    lat_max_perfil = float('-inf')

    # Variables de control para el cálculo del desfase (offset)
    lon_control_perfil = None

    nombres_perfil = []
    if os.path.isdir(GR_DIR):
        for nombre in os.listdir(GR_DIR):
            m = re.match(r'^slabP(\d+)\.tmp$', nombre)
            if m:
                nombres_perfil.append((int(m.group(1)), nombre))
    nombres_perfil.sort(key=lambda x: x[0])

    for p_id, nombre_arch in nombres_perfil:
        arch_test = os.path.join(GR_DIR, nombre_arch)
        try:
            puntos_perfil = []
            with open(arch_test, 'r') as f:
                for linea in f:
                    if linea.startswith('#') or not linea.strip():
                        continue
                    partes = linea.strip().split()
                    if len(partes) >= 7:
                        l_val = float(partes[2])
                        lat_val = float(partes[3])
                        if lat_val < lat_min_perfil:
                            lat_min_perfil = lat_val
                        if lat_val > lat_max_perfil:
                            lat_max_perfil = lat_val

                        if 'nan' in partes[6].lower():
                            p_val = 0.0
                        else:
                            p_val = abs(float(partes[6]))

                        puntos_perfil.append((l_val, lat_val, p_val))

            if puntos_perfil:
                for (l_p, lat_p, p_p) in puntos_perfil:
                    dist = np.sqrt((lon - l_p)**2 + (lat - lat_p)**2)
                    if dist < distancia_minima:
                        distancia_minima = dist
                        mejor_perfil_nombre = nombre_arch[4:-4]
                        datos_perfil_elegido = puntos_perfil
                        lon_control_perfil = l_p
        except Exception:
            pass

    if mejor_perfil_nombre and distancia_minima < 1.5 and datos_perfil_elegido:
        str_perfil = mejor_perfil_nombre
        #print(f"[SLAB/TOPO] Perfil óptimo detectado: {str_perfil} (Dist: {distancia_minima:.2f}°)")
        
        # Calculamos la corrección de desfase (delta_lon)
        delta_lon = lon - lon_control_perfil if lon_control_perfil is not None else 0.0
        
        for (l_val, lat_val, p_val) in datos_perfil_elegido:
            #if (lon - 4.5 <= l_val <= lon + 4.5) and p_val is not None and p_val != 0.0:
            if (lon - 6.0 <= l_val <= lon + 6.0) and p_val is not None and p_val != 0.0:
                lon_slab.append(l_val + delta_lon)
                prof_slab.append(p_val)
                
        if lon_slab:
            lon_slab, prof_slab = zip(*sorted(zip(lon_slab, prof_slab)))
            lon_slab, prof_slab = list(lon_slab), list(prof_slab)

        arch_topo_tmp = os.path.join(GR_DIR, f"topo{str_perfil}.tmp")
        if os.path.exists(arch_topo_tmp):
            try:
                with open(arch_topo_tmp, 'r') as f:
                    for linea in f:
                        if linea.startswith('#') or not linea.strip():
                            continue
                        partes = linea.strip().split()
                        if len(partes) >= 7 and 'nan' not in partes[6].lower():
                            l_val = float(partes[2])
                            alt_val = float(partes[6]) / 1000.0
                            
                            if (lon - 4.5 <= l_val <= lon + 4.5):
                                lon_topo.append(l_val + delta_lon)
                                alt_topo.append(alt_val)
                if lon_topo:
                    lon_topo, alt_topo = zip(*sorted(zip(lon_topo, alt_topo)))
                    lon_topo, alt_topo = list(lon_topo), list(alt_topo)
            except Exception as e:
                print(f"[Aviso] No se pudo cargar la topografía local: {e}")
        
    else:
        str_perfil = "Slab2_Global"
        ANCHO_LAT = 0.40
        try:
            print(f"[SLAB] Fuera de cobertura local. Generando corte y topografía desde grillas globales...")

            arch_slab_bin = os.path.join(GR_DIR, "slab2_global.npy")
            if os.path.exists(arch_slab_bin):
                data_slab = np.load(arch_slab_bin, mmap_mode='r')
                i0 = np.searchsorted(data_slab[:, 1], lat - ANCHO_LAT)
                i1 = np.searchsorted(data_slab[:, 1], lat + ANCHO_LAT, side='right')
                chunk_slab = data_slab[i0:i1]
                chunk_slab = chunk_slab[np.abs(chunk_slab[:, 0] - lon) <= RANGO_ANCHURA]
                if len(chunk_slab):
                    lons_bin = np.round(chunk_slab[:, 0], 1)
                    uniq, inv = np.unique(lons_bin, return_inverse=True)
                    profs_prom = np.zeros(len(uniq), dtype=np.float64)
                    np.add.at(profs_prom, inv, chunk_slab[:, 2])
                    profs_prom /= np.bincount(inv)
                    lon_slab_perfil = np.linspace(lon - RANGO_ANCHURA, lon + RANGO_ANCHURA, 100)
                    prof_interp = np.interp(lon_slab_perfil, uniq, profs_prom, left=np.nan, right=np.nan)
                    mask = ~np.isnan(prof_interp)
                    lon_slab = list(lon_slab_perfil[mask])
                    prof_slab = list(prof_interp[mask])
                    usando_global = True
            else:
                arch_slab_xyz = os.path.join(GR_DIR, "sam_slab2_dep_02.23.18.xyz")
                if os.path.exists(arch_slab_xyz):
                    puntos_slab = {}
                    with open(arch_slab_xyz, 'r') as f:
                        for linea in f:
                            if linea.startswith('#') or not linea.strip():
                                continue
                            partes = linea.strip().split(',')
                            if len(partes) >= 3 and 'nan' not in partes[2].lower():
                                s_lon = float(partes[0]) - 360 if float(partes[0]) > 180 else float(partes[0])
                                s_lat = float(partes[1])
                                s_prof = abs(float(partes[2]))
                                if (lat - ANCHO_LAT <= s_lat <= lat + ANCHO_LAT) and (lon - RANGO_ANCHURA <= s_lon <= lon + RANGO_ANCHURA):
                                    lon_bin = round(s_lon, 1)
                                    if lon_bin not in puntos_slab:
                                        puntos_slab[lon_bin] = []
                                    puntos_slab[lon_bin].append(s_prof)
                    if puntos_slab:
                        lons_ordenadas = sorted(puntos_slab.keys())
                        profs_promedio = [np.mean(puntos_slab[ln]) for ln in lons_ordenadas]
                        lon_slab_perfil = np.linspace(lon - RANGO_ANCHURA, lon + RANGO_ANCHURA, 100)
                        prof_interp = np.interp(lon_slab_perfil, lons_ordenadas, profs_promedio, left=np.nan, right=np.nan)
                        mask = ~np.isnan(prof_interp)
                        lon_slab = list(lon_slab_perfil[mask])
                        prof_slab = list(prof_interp[mask])
                        usando_global = True

            arch_topo_bin = os.path.join(GR_DIR, "topo_chile.npy")
            if os.path.exists(arch_topo_bin):
                data_topo = np.load(arch_topo_bin, mmap_mode='r')
                i0 = np.searchsorted(data_topo[:, 1], lat - ANCHO_LAT)
                i1 = np.searchsorted(data_topo[:, 1], lat + ANCHO_LAT, side='right')
                chunk_topo = data_topo[i0:i1]
                chunk_topo = chunk_topo[np.abs(chunk_topo[:, 0] - lon) <= RANGO_ANCHURA]
                if len(chunk_topo):
                    lons_bin = np.round(chunk_topo[:, 0], 1)
                    uniq, inv = np.unique(lons_bin, return_inverse=True)
                    alts_prom = np.zeros(len(uniq), dtype=np.float64)
                    np.add.at(alts_prom, inv, chunk_topo[:, 2] / 1000.0)
                    alts_prom /= np.bincount(inv)
                    lon_topo_perfil = np.linspace(lon - RANGO_ANCHURA, lon + RANGO_ANCHURA, 100)
                    alt_interp = np.interp(lon_topo_perfil, uniq, alts_prom, left=np.nan, right=np.nan)
                    mask_topo = ~np.isnan(alt_interp)
                    lon_topo = list(lon_topo_perfil[mask_topo])
                    alt_topo = list(alt_interp[mask_topo])
            else:
                arch_topo_xyz = os.path.join(GR_DIR, "topochile30.xyz")
                if os.path.exists(arch_topo_xyz):
                    puntos_topo = {}
                    with open(arch_topo_xyz, 'r') as f:
                        for linea in f:
                            if linea.startswith('#') or not linea.strip():
                                continue
                            partes = linea.strip().split()
                            if len(partes) >= 3:
                                t_lon = float(partes[0])
                                t_lat = float(partes[1])
                                t_alt = float(partes[2]) / 1000.0
                                if (lat - ANCHO_LAT <= t_lat <= lat + ANCHO_LAT) and (lon - RANGO_ANCHURA <= t_lon <= lon + RANGO_ANCHURA):
                                    lon_bin = round(t_lon, 1)
                                    if lon_bin not in puntos_topo:
                                        puntos_topo[lon_bin] = []
                                    puntos_topo[lon_bin].append(t_alt)
                    if puntos_topo:
                        lons_topo = sorted(puntos_topo.keys())
                        alts_promedio = [np.mean(puntos_topo[ln]) for ln in lons_topo]
                        lon_topo_perfil = np.linspace(lon - RANGO_ANCHURA, lon + RANGO_ANCHURA, 100)
                        alt_interp = np.interp(lon_topo_perfil, lons_topo, alts_promedio, left=np.nan, right=np.nan)
                        mask_topo = ~np.isnan(alt_interp)
                        lon_topo = list(lon_topo_perfil[mask_topo])
                        alt_topo = list(alt_interp[mask_topo])
        except Exception as e:
            print(f"[Aviso] Falló el procesamiento de respaldo global: {e}")

    # =========================================================================
    # 3. CONSTRUCCIÓN GRÁFICA - PLOT 1: VISTA EN PLANTA (RELIEVE TIF LOCAL)
    # =========================================================================
    ax_planta = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
    ax_planta.set_extent([lon - RANGO_ANCHURA, lon + RANGO_ANCHURA, lat - RANGO_ANCHURA, lat + RANGO_ANCHURA], crs=ccrs.PlateCarree())

    arch_tif = os.path.join(DATOS_DIR, "NE2_LR_LC_SR_W_DR.tif")
    if os.path.exists(arch_tif):
        try:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None  
            img = Image.open(arch_tif)
            ancho_img, alto_img = img.size
            x0 = int((lon - RANGO_ANCHURA + 180) / 360.0 * ancho_img)
            x1 = int((lon + RANGO_ANCHURA + 180) / 360.0 * ancho_img)
            y0 = int((90 - (lat + RANGO_ANCHURA)) / 180.0 * alto_img)
            y1 = int((90 - (lat - RANGO_ANCHURA)) / 180.0 * alto_img)
            x0 = max(0, min(ancho_img - 1, x0))
            x1 = max(x0 + 1, min(ancho_img, x1))
            y0 = max(0, min(alto_img - 1, y0))
            y1 = max(y0 + 1, min(alto_img, y1))
            img_recorte = img.crop((x0, y0, x1, y1)).resize((400, 400))
            ax_planta.imshow(img_recorte, origin='upper', 
                             extent=[lon - RANGO_ANCHURA, lon + RANGO_ANCHURA,
                                     lat - RANGO_ANCHURA, lat + RANGO_ANCHURA],
                             transform=ccrs.PlateCarree())
        except Exception as e:
            print(f"[Aviso] No se pudo proyectar el relieve .tif: {e}")
            ax_planta.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#f7f7f4', zorder=1)
            ax_planta.add_feature(cfeature.OCEAN.with_scale('50m'), facecolor='#edf4f9', zorder=1)
    else:
        ax_planta.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#f7f7f4', zorder=1)
        ax_planta.add_feature(cfeature.OCEAN.with_scale('50m'), facecolor='#edf4f9', zorder=1)

    ax_planta.coastlines(resolution='50m', color='#111111', linewidth=1.1, zorder=2)
    ax_planta.add_feature(cfeature.BORDERS.with_scale('50m'), edgecolor='#333333', linestyle=':', linewidth=0.8, zorder=2)

    if lon_b:
        ax_planta.scatter(lon_b, lat_b, color='#222222', alpha=0.25, s=3.5, marker='.', zorder=3, transform=ccrs.PlateCarree(), label="Sismicidad Histórica")

    ax_planta.scatter(lon, lat, s=size, color='#F7E284', alpha=0.95, edgecolors='black', 
                      linewidth=1.2, zorder=5, transform=ccrs.PlateCarree(), label="Epicentro")
    
    distancia_min = float('inf')
    localidad_cercana = "N/A"
    textos_mapa = []  

    if os.path.exists(os.path.join(DATOS_DIR, "localidades.csv")):
        with open(os.path.join(DATOS_DIR, "localidades.csv"), mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nombre = row['Nombre']
                lon_loc = float(row['Lon'])
                lat_loc = float(row['Lat'])
                
                d = calcular_distancia(lon, lat, lon_loc, lat_loc)
                if d < distancia_min:
                    distancia_min = d
                    localidad_cercana = nombre
                    rumbo = obtener_rumbo(float(row['Lon']), float(row['Lat']), lon, lat)
                
                if (lon - RANGO_ANCHURA <= lon_loc <= lon + RANGO_ANCHURA) and \
                   (lat - RANGO_ANCHURA <= lat_loc <= lat + RANGO_ANCHURA):
                    ax_planta.plot(lon_loc, lat_loc, 'o', color='black', markersize=3, 
                                   transform=ccrs.PlateCarree(), zorder=6)
                    
                    t = ax_planta.text(lon_loc, lat_loc, nombre, 
                                   fontsize=7, fontweight='bold', color='black',
                                   path_effects=[matplotlib.patheffects.withSimplePatchShadow()],
                                   transform=ccrs.PlateCarree(), zorder=7)
                    textos_mapa.append(t)

        if textos_mapa:
            adjust_text(textos_mapa, 
                        ax=ax_planta,
                        expand=(1.2, 1.4), 
                        arrowprops=dict(arrowstyle="-", color='black', lw=0.5, alpha=0.6))

        texto_ref = f"{distancia_min:.0f} km al {rumbo} de {localidad_cercana}"
        ax_planta.text(0.02, 0.02, texto_ref, transform=ax_planta.transAxes, 
                       fontsize=8, fontweight='bold', color='white',
                       bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', pad=4),
                       zorder=10)

    gl = ax_planta.gridlines(draw_labels=True, linestyle='--', alpha=0.5, color='#444444', zorder=4)
    gl.top_labels, gl.right_labels = False, False
    gl.xlabel_style = {'size': 8.5, 'weight': 'bold'}
    gl.ylabel_style = {'size': 8.5, 'weight': 'bold'}
    
    ax_planta.set_title("Vista en Planta", fontsize=11, fontweight='bold', pad=10)
    ax_planta.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2,
                     fontsize=8, frameon=True, facecolor='#f9f9f9', edgecolor='gray',
                     markerscale=0.75)

    # =========================================================================
    # 4. CONSTRUCCIÓN GRÁFICA - PLOT 2: VISTA EN PERFIL (W - E)
    # =========================================================================
    ax_perfil = fig.add_subplot(1, 2, 2)
    
    hay_datos_para_perfil = bool(lon_slab or lon_topo)
    if not hay_datos_para_perfil:
        ax_perfil.axis('off')
        if lat_min_perfil != float('inf'):
            texto_cobertura = (f"Sismo fuera de la cobertura de los perfiles locales\n"
                               #f"({abs(lat_max_perfil):.1f}°S - {abs(lat_min_perfil):.1f}°S)\n"
                               f"y de las grillas globales en esta zona")
        else:
            texto_cobertura = ("No se encontraron perfiles locales ni datos\n"
                               "de las grillas globales en esta zona")
        ax_perfil.text(0.5, 0.5, f"PERFIL NO DISPONIBLE\n\n{texto_cobertura}",
                       fontsize=12, fontweight='bold', color="#967E13",
                       ha='center', va='center', transform=ax_perfil.transAxes,
                       bbox=dict(facecolor='#ffe6e6', edgecolor='#967E13', alpha=0.8, boxstyle='round,pad=1'))
    else:
        if lon_b:
            ax_perfil.scatter(lon_b, prof_b, color='gray', alpha=0.3, s=6, marker='.', zorder=1, label="Sismicidad Histórica")

        if lon_slab and prof_slab:
            label_linea = "Contacto (Slab2 Global)" if usando_global else f"Contacto Placas ({str_perfil})"
            ax_perfil.plot(lon_slab, prof_slab, color='black', linestyle='-', lw=2.2, 
                           zorder=3, label=label_linea)

        if lon_topo and alt_topo:
            ax_perfil.plot(lon_topo, alt_topo, color='black', linestyle='-', lw=1.2, 
                           zorder=5, label="Topografía/Batimetría")

        ax_perfil.scatter(lon, prof, s=size, color='#F7E284', alpha=0.9, edgecolors='black', linewidths=1.5, zorder=10, label="Hipocentro")
        
        if lon_slab:
            titulo_perfil = f"Perfil Perpendicular ({str_perfil})"
        else:
            titulo_perfil = f"Perfil Perpendicular ({str_perfil} - Sin Datos)"
            
        ax_perfil.set_title(titulo_perfil, fontsize=11, fontweight='bold', pad=10)
        ax_perfil.set_xlabel("Longitud", fontsize=9, fontweight='bold', labelpad=8)
        ax_perfil.set_ylabel("Profundidad (km)", fontsize=9, fontweight='bold', labelpad=8)
        ax_perfil.tick_params(axis='both', labelsize=8)
        
        if lon_slab:
            limite_izquierdo = min(lon_slab[0], lon - 0.5)
        else:
            limite_izquierdo = lon - RANGO_ANCHURA
            
        #ax_perfil.set_xlim(limite_izquierdo, lon + RANGO_ANCHURA)
        
        # Definir un límite derecho dinámico basado en los datos reales del slab cargado
        if lon_slab:
            limite_izquierdo = min(lon_slab[0], lon - 0.5)
            limite_derecho = min(lon_slab[-1], lon + 1.8) # Recorta el vacío del Este de forma elegante
        else:
            limite_izquierdo = lon - RANGO_ANCHURA
            limite_derecho = lon + RANGO_ANCHURA

        ax_perfil.set_xlim(limite_izquierdo, limite_derecho)

        prof_max_grafico = max(200, float(prof) + 50)
        ax_perfil.set_ylim(bottom=prof_max_grafico, top=-10) 
        
        ax_perfil.grid(True, linestyle=':', alpha=0.4, color='gray', zorder=0)

        ax_perfil.legend(
            loc='upper center', 
            bbox_to_anchor=(0.5, -0.15),  
            ncol=3,                       
            fontsize=8,                   
            frameon=True, 
            facecolor='#f9f9f9', 
            edgecolor='gray',
            markerscale=0.75  
        )

    # === ETAPA 3: Renderizando las capas ===
    mostrar_avance(3, 4, "Proyectando mapas y relieve .tif...")
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # === ETAPA 4: Completado ===
    mostrar_avance(4, 4, "¡Listo! Abriendo interfaz gráfica.")
    print("\n") # Salto de línea crucial para que tus prints de abajo no pisen la barra

    # Ahora sí, se imprimen tus logs de consola nativos y se abre el mapa
    print(f"[GRAFICADOR] Cargando contexto sismotectónico para {event_id}...")
    if lon_slab:
        print(f"[SLAB/TOPO] Perfil óptimo detectado: {str_perfil} (Dist: {distancia_minima:.2f}°)")
    else:
        print(f"[SLAB] Fuera de cobertura local.")
        
    plt.show()
    print("[GRAFICADOR] Ventana cerrada por el operador. Volviendo al modo escucha...\n")


# Resolución del mallado del mapa 3D (grados por celda).
# A menor valor = más detalle, pero más lento al rotar (más triángulos).
#   0.1° -> ~13.900 triángulos (detallado, se nota lag)
#   0.2° -> ~3.600  triángulos (equilibrio recomendado)
#   0.3° -> ~1.600  triángulos (ligero)
# Si tu equipo aún siente el giro "traboso", sube el valor a 0.3.
RES_3D = 0.2


def _promediar_tris(x, y, z, res=RES_3D):
    """
    Agrupa puntos (x=lon, y=lat, z=altitud/profundidad) en celdas de 'res'
    grados y devuelve las coordenadas de las celdas con su valor promedio.
    Así la superficie 3D queda suave y liviana en vez de graficar miles
    de puntos.
    """
    xr = np.round(x / res) * res
    yr = np.round(y / res) * res
    combo = np.stack([xr, yr], axis=1)
    celdas, inv = np.unique(combo, axis=0, return_inverse=True)
    suma = np.zeros(len(celdas), dtype=np.float64)
    np.add.at(suma, inv, z)
    conteo = np.bincount(inv)
    return celdas[:, 0], celdas[:, 1], suma / np.maximum(conteo, 1)


def plotear_perfil_3d(lat, lon, prof, event_id, texto_magnitud):
    """
    Vista 3D del contexto sismotectónico: topografía sobre el nivel del mar,
    placa subductada sumergiéndose, sismicidad de fondo e hipocentro.
    Ventana interactiva: se rota con el mouse (matplotlib 3D).
    Se activa desde el LOOP PRINCIPAL con una única llamada comentable.
    """
    try:
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    except ImportError:
        print("[3D] mplot3d no está disponible en este entorno; omitiendo mapa 3D.")
        return

    RANGO_3D = 3.0  # caja de ±3° alrededor del evento

    def _recortar(data, col_lon, col_lat, col_z):
        mask = (np.abs(data[:, col_lat] - lat) <= RANGO_3D) & \
               (np.abs(data[:, col_lon] - lon) <= RANGO_3D)
        return data[mask]

    # --- TOPOGRAFÍA (m → km, positiva hacia arriba) ---
    topo = None
    arch_topo = os.path.join(GR_DIR, "topo_chile.npy")
    if os.path.exists(arch_topo):
        d = np.load(arch_topo, mmap_mode='r')
        chunk = _recortar(d, 0, 1, 2)
        if len(chunk):
            topo = _promediar_tris(chunk[:, 0], chunk[:, 1], chunk[:, 2] / 1000.0)

    # --- PLACA SUBDUCTADA (profundidad, negativa hacia abajo) ---
    slab = None
    arch_slab = os.path.join(GR_DIR, "slab2_global.npy")
    if os.path.exists(arch_slab):
        d = np.load(arch_slab, mmap_mode='r')
        chunk = _recortar(d, 0, 1, 2)
        if len(chunk):
            sx, sy, sz = _promediar_tris(chunk[:, 0], chunk[:, 1], chunk[:, 2])
            slab = (sx, sy, -sz)  # profundidad → negativa en el eje Z

    if topo is None and slab is None:
        print("[3D] Sin cobertura de grillas globales para este evento.")
        return

    # --- SISMICIDAD DE FONDO (catálogo histórico) ---
    arch_base = os.path.join(DATOS_DIR, "base_2023_2026.dat")
    lon_b, lat_b, prof_b = [], [], []
    if os.path.exists(arch_base):
        try:
            with open(arch_base, 'r') as f:
                for linea in f:
                    partes = linea.strip().split()
                    if len(partes) >= 5:
                        ln = float(partes[3])
                        lt = float(partes[2])
                        if (lon - RANGO_3D <= ln <= lon + RANGO_3D) and \
                           (lat - RANGO_3D <= lt <= lat + RANGO_3D):
                            lon_b.append(ln)
                            lat_b.append(lt)
                            prof_b.append(float(partes[4]))
        except Exception as e:
            print(f"[3D] Aviso: no se pudo cargar el background sísmico: {e}")

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor("white")

    if topo is not None and len(topo[0]):
        ax.plot_trisurf(topo[0], topo[1], topo[2],
                        cmap="terrain", linewidth=0,
                        antialiased=False, shade=False, alpha=0.9)
    if slab is not None and len(slab[0]):
        ax.plot_trisurf(slab[0], slab[1], slab[2],
                        cmap="hot", linewidth=0,
                        antialiased=False, shade=False, alpha=0.5)

    # --- SISMICIDAD DE FONDO (ocultamos la muy cercana al evento para que la
    # estrella del hipocentro no quede tapada) ---
    RADIO_LIMPIO = 0.35  # grados alrededor del hipocentro sin puntos grises
    if lon_b:
        lon_b_l = [ln for ln, lt in zip(lon_b, lat_b)
                   if (ln - lon) ** 2 + (lt - lat) ** 2 > RADIO_LIMPIO ** 2]
        lat_b_l = [lt for ln, lt in zip(lon_b, lat_b)
                   if (ln - lon) ** 2 + (lt - lat) ** 2 > RADIO_LIMPIO ** 2]
        prof_b_l = [p for ln, lt, p in zip(lon_b, lat_b, prof_b)
                    if (ln - lon) ** 2 + (lt - lat) ** 2 > RADIO_LIMPIO ** 2]
        ax.scatter(lon_b_l, lat_b_l, [-p for p in prof_b_l],
                   s=5, c="gray", alpha=0.5)

    # --- HIPOCENTRO: estrella dibujada con ax.plot() (Line3D). El marcador
    # "estrella" de ax.scatter() puede quedar oculto por el ordenamiento por
    # profundidad de matplotlib 3D sobre las superficies; con Line3D el
    # marcador se proyecta y se ve siempre. Halo blanco detrás para que
    # resalte sobre la sismicidad.
    ax.plot([lon], [lat], [-prof], marker='*', markersize=26, ls='',
            mfc='white', mec='white', zorder=12)
    ax.plot([lon], [lat], [-prof], marker='*', markersize=19, ls='',
            mfc='#ff2fd0', mec='black', mew=1.2, zorder=13)
    ax.plot([lon, lon], [lat, lat], [0.0, -prof],
            linestyle="--", linewidth=1.0, color="black", alpha=0.5)

    ax.set_xlabel("Longitud (°)")
    ax.set_ylabel("Latitud (°)")
    ax.set_zlabel("km (arriba (+) / profundidad (-))")
    ax.set_title(f"Perfil 3D — {event_id} ({texto_magnitud}, prof {prof} km)")
    ax.view_init(elev=30, azim=-60)

    fig.text(0.02, 0.02,
             "Cómo explorar:  ARRASTRA con el mouse para rotar  ·  "
             "rueda o desplaza para acercar/alejar",
             fontsize=9, style="italic",
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                       edgecolor="gray", alpha=0.9))

    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Patch(facecolor="#6fae4d", alpha=0.7, label="Topografía"),
        Patch(facecolor="#b13d2d", alpha=0.55, label="Placa subductada"),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markeredgecolor='gray', ls='', label="Sismicidad histórica"),
        Line2D([0], [0], marker='*', color='w', markerfacecolor="#6b0707",
               markeredgecolor='black', markersize=13, ls='',
               label=f"Hipocentro {texto_magnitud}"),
    ], loc="upper left", fontsize=9)

    plt.tight_layout()
    plt.show()
    print("[3D] Ventana 3D cerrada por el operador.\n")


def parsear_linea_evento(texto):
    """
    Parsea la línea de evento_data.txt escrita por la consulta (campos
    separados por ';'). Devuelve un dict con fecha, lat, lon, prof, mag,
    tipo_mag, texto_magnitud y event_id; None si la línea no es válida.
    """
    if not texto or "csn_" not in texto:
        return None

    partes = texto.split(';')
    if len(partes) < 12:
        return None

    fecha = partes[0].strip()

    # --- CONVERSIÓN SEGURA DE MAGNITUD ---
    try:
        mag = float(partes[3].strip())
        tipo_mag = partes[4].strip() if partes[4] else "M"
        texto_magnitud = f"{mag:.1f} {tipo_mag}"
    except (ValueError, IndexError, TypeError):
        mag = 0.0
        tipo_mag = partes[4].strip() if (len(partes) > 4 and partes[4]) else "M"
        texto_magnitud = f"M s/d ({tipo_mag})"  # "s/d" significa Sin Datos

    # --- PROCESAMIENTO DE COORDENADAS ---
    raw_lat = partes[8].strip()
    lat = float(raw_lat.split()[0])
    if 's' in raw_lat.lower():
        lat = -abs(lat)

    raw_lon = partes[9].strip()
    lon = float(raw_lon.split()[0])
    if 'w' in raw_lon.lower() or 'o' in raw_lon.lower():
        lon = -abs(lon)

    # --- CONVERSIÓN SEGURA DE PROFUNDIDAD ---
    raw_prof = partes[10].strip()
    try:
        prof = float(raw_prof.replace('km', '').strip())
    except (ValueError, IndexError):
        # Si la profundidad no es convertible (ej. se desfasó y leyó 'Moments'),
        # le asignamos un valor por defecto (ej. 10.0 km) para evitar que el script se caiga.
        print(f"[Aviso] No se pudo parsear la profundidad ('{raw_prof}'). Usando valor por defecto de 10 km.")
        prof = 10.0

    return {
        "fecha": fecha,
        "lat": lat,
        "lon": lon,
        "prof": prof,
        "mag": mag,
        "tipo_mag": tipo_mag,
        "texto_magnitud": texto_magnitud,
        "event_id": partes[-1].strip(),
    }


# =========================================================================
# LOOP PRINCIPAL (EJECUCIÓN ÚNICA)
# =========================================================================
if __name__ == "__main__":
    if os.path.exists(ARCHIVO_TMP):
        try:
            with open(ARCHIVO_TMP, 'r') as f:
                texto_actual = f.readline().strip()

            if texto_actual and "csn_" in texto_actual:
                print("[EVENTO SELECCIONADO] Procesando parámetros...")

            ev = parsear_linea_evento(texto_actual)

            if ev is not None:
                    try:
                        plotear_evento(ev["fecha"], ev["lat"], ev["lon"], ev["prof"],
                                       ev["mag"], ev["event_id"], ev["texto_magnitud"])
                    except Exception as e:
                        print(f"[Error] Falló la generación de mapas: {e}")

                    # ═══════════════════════════════════════════════════════════
                    # MAPA 3D — si enlentece la ejecución, comenta la línea de
                    # abajo (un solo '#') y el script sigue igual que siempre.
                    # ═══════════════════════════════════════════════════════════
                    plotear_perfil_3d(ev["lat"], ev["lon"], ev["prof"],
                                      ev["event_id"], ev["texto_magnitud"])

                    # El archivo temporal NO se elimina: cada consulta NewPT lo
                    # regenera (consulta_evento.py lo borra y reescribe al
                    # inicio), y dejarlo permite re-ejecutar este script.
                    print("[INFO] Procesamiento terminado. evento_data.txt queda disponible para re-ejecutar.")
            elif texto_actual and "csn_" in texto_actual:
                    print("[Error] El formato de la línea en el archivo no es válido.")
            else:
                print("[Error] El archivo no contiene un evento válido (csn_).")

        except Exception as ex:
            print(f"[Error] Falló la lectura o el parseo del archivo: {ex}")
    else:
        print(f"[ERROR] No se encontró el archivo: {ARCHIVO_TMP}. Asegúrate de ejecutar newpt.sh")
