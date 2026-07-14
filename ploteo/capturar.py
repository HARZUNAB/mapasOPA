#!/usr/bin/env python3
import os
import sys
import re
import time
import numpy as np
import pyperclip
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.patheffects
import csv 
from math import radians, cos, sin, asin, sqrt
import math
from adjustText import adjust_text

OUTPUT_FILE = "datos_seiscomp.csv"
# Obtener el directorio donde reside este script (capturar.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_TMP = os.path.join(BASE_DIR, "evento_data.txt")

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
    time.sleep(0.1) # Breve pausa para percibir visualmente el avance
    
    # Configuración de estilo limpia
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    fig = plt.figure(figsize=(14, 6.5))
    fig.suptitle(f"NewPT - Evento: {event_id}\nFecha: {fecha} | {texto_magnitud} | Profundidad: {prof} km", 
                 fontsize=12, fontweight='bold', y=0.96)
    
    size = 220
    RANGO_ANCHURA = 2.5 

    # =========================================================================
    # 1. CARGA EXPRESO DEL BACKGROUND SÍSMICO (Sismos grises)
    # =========================================================================
    arch_base = "base_2023_2026.dat"
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
    time.sleep(0.1)

    # =========================================================================
    # 2. SELECCIÓN INTELIGENTE Y CARGA DE SUBDUCCIÓN Y TOPOGRAFÍA (CORREGIDO)
    # =========================================================================
    lon_slab, prof_slab = [], []
    lon_topo, alt_topo = [], []
    usando_global = False
    mejor_perfil_id = None
    distancia_minima = float('inf')
    datos_perfil_elegido = []
    
    # Variables de control para el cálculo del desfase (offset)
    lon_control_perfil = None

    for p_id in range(1, 14):
        arch_test = f"./grillas/slabP{p_id:02d}.tmp"
        if os.path.exists(arch_test):
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
                            mejor_perfil_id = p_id
                            datos_perfil_elegido = puntos_perfil
                            lon_control_perfil = l_p
            except Exception:
                pass

    if mejor_perfil_id and distancia_minima < 1.5 and datos_perfil_elegido:
        str_perfil = f"P{mejor_perfil_id:02d}"
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

        arch_topo_tmp = f"./grillas/topo{str_perfil}.tmp"
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
        arch_slab_xyz = "./grillas/sam_slab2_dep_02.23.18.xyz"
        if os.path.exists(arch_slab_xyz):
            try:
                print(f"[SLAB] Fuera de cobertura local. Generando corte directo desde grilla global...")
                puntos_slab = {}
                ANCHO_LAT = 0.40
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
            except Exception as e:
                print(f"[Aviso] Falló el procesamiento de respaldo global: {e}")

    # =========================================================================
    # 3. CONSTRUCCIÓN GRÁFICA - PLOT 1: VISTA EN PLANTA (RELIEVE TIF LOCAL)
    # =========================================================================
    ax_planta = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
    ax_planta.set_extent([lon - RANGO_ANCHURA, lon + RANGO_ANCHURA, lat - RANGO_ANCHURA, lat + RANGO_ANCHURA], crs=ccrs.PlateCarree())

    arch_tif = "NE2_LR_LC_SR_W_DR.tif"
    if os.path.exists(arch_tif):
        try:
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None  
            img = Image.open(arch_tif)
            ax_planta.imshow(img, origin='upper', 
                             extent=[-180, 180, -90, 90], transform=ccrs.PlateCarree())
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
        ax_planta.scatter(lon_b, lat_b, color='#222222', alpha=0.25, s=3.5, marker='.', zorder=3, transform=ccrs.PlateCarree())

    ax_planta.scatter(lon, lat, s=size, color='#ff3333', alpha=0.95, edgecolors='black', 
                      linewidth=1.2, zorder=5, transform=ccrs.PlateCarree(), label="Epicentro Actual")
    
    distancia_min = float('inf')
    localidad_cercana = "N/A"
    textos_mapa = []  

    if os.path.exists("localidades.csv"):
        with open("localidades.csv", mode='r', encoding='utf-8') as f:
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

    # =========================================================================
    # 4. CONSTRUCCIÓN GRÁFICA - PLOT 2: VISTA EN PERFIL (W - E)
    # =========================================================================
    ax_perfil = fig.add_subplot(1, 2, 2)
    
    if not (-45.0 <= lat <= -18.0):
        ax_perfil.axis('off')
        ax_perfil.text(0.5, 0.5, "PERFIL NO DISPONIBLE\n\nSismo fuera de la cobertura\nde los perfiles locales (18°S - 45°S)", 
                       fontsize=12, fontweight='bold', color='#cc0000',
                       ha='center', va='center', transform=ax_perfil.transAxes,
                       bbox=dict(facecolor='#ffe6e6', edgecolor='#cc0000', alpha=0.8, boxstyle='round,pad=1'))
        
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

        ax_perfil.scatter(lon, prof, s=size, color='#ff3333', alpha=0.9, edgecolors='black', linewidths=1.5, zorder=10, label="Hipocentro")
        
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
    time.sleep(0.15)

    # === ETAPA 4: Completado ===
    mostrar_avance(4, 4, "¡Listo! Abriendo interfaz gráfica.")
    print("\n") # Salto de línea crucial para que tus prints de abajo no pisen la barra

    # Ahora sí, se imprimen tus logs de consola nativos y se abre el mapa
    print(f"[GRAFICADOR] Cargando contexto sismotectónico local para {event_id}...")
    if lon_slab:
        print(f"[SLAB/TOPO] Perfil óptimo detectado: {str_perfil} (Dist: {distancia_minima:.2f}°)")
    else:
        print(f"[SLAB] Fuera de cobertura local.")
        
    plt.show()
    print("[GRAFICADOR] Ventana cerrada por el operador. Volviendo al modo escucha...\n")
    
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
                
                #
                partes = texto_actual.split(';')
                if len(partes) >= 12:
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
                    
                    event_id = partes[-1].strip()
                   
                    plotear_evento(fecha, lat, lon, prof, mag, event_id, texto_magnitud)
                    
                    try:
                        os.remove(ARCHIVO_TMP)
                        print("[INFO] Archivo temporal eliminado. Cerrando programa.")
                    except OSError as e:
                        print(f"[Error] No se pudo eliminar el archivo temporal: {e}")
                else:
                    print("[Error] El formato de la línea en el archivo no es válido.")
            else:
                print("[Error] El archivo no contiene un evento válido (csn_).")
                
        except Exception as ex:
            print(f"[Error] Falló la lectura o el parseo del archivo: {ex}")
    else:
        print(f"[ERROR] No se encontró el archivo: {ARCHIVO_TMP}. Asegúrate de ejecutar newpt.sh")
