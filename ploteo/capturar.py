#!/usr/bin/env python3
import os
import re
import time
import numpy as np
import pyperclip
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.interpolate import griddata

OUTPUT_FILE = "datos_seiscomp.csv"

def inicializar_csv():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(",Fecha_Hora,Latitud,Longitud,Prof.,Mag.,Tipo_mag.,Analista,Event_id,phases\n")
    print("[INFO] CSV reiniciado con éxito.")

def plotear_evento(fecha, lat, lon, prof, mag, event_id):
    """
    Genera ventanas sismotectónicas locales con background real 
    y la curva exacta de subducción (híbrido .tmp / .xyz global).
    """
    print(f"[GRAFICADOR] Cargando contexto sismotectónico local para {event_id}...")
    
    # Configuración de estilo
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    fig = plt.figure(figsize=(14, 6.5))
    fig.suptitle(f"NewPT - Evento: {event_id}\nFecha: {fecha} | {texto_magnitud} | Profundidad: {prof} km", 
                 fontsize=12, fontweight='bold', y=0.96)
    
    size = float(mag) * 60
    RANGO_ANCHURA = 2.5 # Grados alrededor del sismo para encuadrar la ventana

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

    # =========================================================================
    # 2. SELECCIÓN INTELIGENTE Y CARGA DE SUBDUCCIÓN Y TOPOGRAFÍA
    # =========================================================================
    lon_slab, prof_slab = [], []
    lon_topo, alt_topo = [], []
    usando_global = False
    mejor_perfil_id = None
    distancia_minima = float('inf')
    datos_perfil_elegido = []

    # 1. Escaneo dinámico de los perfiles locales para encontrar el más cercano
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
                            l_val = float(partes[2])   # Longitud Real
                            lat_val = float(partes[3])  # Latitud Real
                            
                            # Si es NaN, significa que está en la superficie/fosa (0 km de profundidad)
                            if 'nan' in partes[6].lower():
                                p_val = 0.0
                            else:
                                p_val = abs(float(partes[6])) # Profundidad Real
                                
                            puntos_perfil.append((l_val, lat_val, p_val))
                
                if puntos_perfil:
                    for (l_p, lat_p, p_p) in puntos_perfil:
                        dist = np.sqrt((lon - l_p)**2 + (lat - lat_p)**2)
                        if dist < distancia_minima:
                            distancia_minima = dist
                            mejor_perfil_id = p_id
                            datos_perfil_elegido = puntos_perfil
            except Exception:
                pass

    # 2. Si hay un perfil local óptimo, cargamos Slab y Topo
    if mejor_perfil_id and distancia_minima < 1.5:
        str_perfil = f"P{mejor_perfil_id:02d}"
        print(f"[SLAB/TOPO] Perfil óptimo detectado: {str_perfil} (Dist: {distancia_minima:.2f}°)")
        
        # Filtrar y guardar el Slab descartando NaNs para evitar el escalón
        for (l_val, lat_val, p_val) in datos_perfil_elegido:
            if (lon - 4.5 <= l_val <= lon + 4.5) and p_val is not None and p_val != 0.0:
                lon_slab.append(l_val)
                prof_slab.append(p_val)
                
        if lon_slab:
            lon_slab, prof_slab = zip(*sorted(zip(lon_slab, prof_slab)))
            lon_slab, prof_slab = list(lon_slab), list(prof_slab)

        # Cargar archivo de Topografía correspondiente
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
                                lon_topo.append(l_val)
                                alt_topo.append(alt_val)
                if lon_topo:
                    lon_topo, alt_topo = zip(*sorted(zip(lon_topo, alt_topo)))
                    lon_topo, alt_topo = list(lon_topo), list(alt_topo)
            except Exception as e:
                print(f"[Aviso] No se pudo cargar la topografía local: {e}")
        
    else:
        # 3. RESPALDO GLOBAL (Solo Slab2 XYZ en caso de estar fuera de rango)
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
    # 3. CONSTRUCCIÓN GRÁFICA - PLOT 1: VISTA EN PLANTA
    # =========================================================================
    ax_planta = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
    ax_planta.coastlines(resolution='50m', color='#1a1a1a', linewidth=1.2, zorder=2)
    ax_planta.add_feature(cfeature.BORDERS.with_scale('50m'), edgecolor='#555555', linestyle='--', linewidth=0.8, zorder=2)
    ax_planta.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#f7f7f4', zorder=1)
    ax_planta.add_feature(cfeature.OCEAN.with_scale('50m'), facecolor='#eef5fa', zorder=1)

    if lon_b:
        ax_planta.scatter(lon_b, lat_b, color='gray', alpha=0.3, s=4, marker='.', zorder=3, transform=ccrs.PlateCarree())

    ax_planta.scatter(lon, lat, s=size, color='#ff3333', alpha=0.9, edgecolors='black', 
                      linewidth=1.5, zorder=5, transform=ccrs.PlateCarree(), label="Epicentro Actual")
    
    ax_planta.set_extent([lon - RANGO_ANCHURA, lon + RANGO_ANCHURA, lat - RANGO_ANCHURA, lat + RANGO_ANCHURA], crs=ccrs.PlateCarree())
    gl = ax_planta.gridlines(draw_labels=True, linestyle=':', alpha=0.6, color='gray', zorder=4)
    gl.top_labels, gl.right_labels = False, False
    #ax_planta.set_title("Vista en Planta (Contexto Local)", fontsize=11, fontweight='bold', pad=10)
    ax_planta.set_title("Vista en Planta", fontsize=11, fontweight='bold', pad=10)

    # =========================================================================
    # 4. CONSTRUCCIÓN GRÁFICA - PLOT 2: VISTA EN PERFIL (W - E)
    # =========================================================================
    ax_perfil = fig.add_subplot(1, 2, 2)
    
    # 1. Graficar Sismicidad Histórica de Fondo
    if lon_b:
        ax_perfil.scatter(lon_b, prof_b, color='gray', alpha=0.3, s=6, marker='.', zorder=1, label="Sismicidad Histórica")

    # 2. Graficar la línea de la subducción (Contacto de Placas)
    if lon_slab and prof_slab:
        label_linea = "Contacto (Slab2 Global)" if usando_global else f"Contacto Placas ({str_perfil})"
        ax_perfil.plot(lon_slab, prof_slab, color='black', linestyle='-', lw=2.2, 
                       zorder=3, label=label_linea)

    # 3. Graficar la línea de la topografía/batimetría superficial
    if lon_topo and alt_topo:
        ax_perfil.plot(lon_topo, alt_topo, color='black', linestyle='-', lw=1.2, 
                       zorder=5, label="Topografía/Batimetría")

    # 4. Graficar el Sismo de Turno (Hipocentro Real)
    ax_perfil.scatter(lon, prof, s=size, color='#ff3333', alpha=0.9, edgecolors='black', linewidths=1.5, zorder=10, label="Hipocentro")
    
    # 5. Configurar Título Único Dinámico
    if lon_slab:
        #tipo_origen = "Slab2 Global" if usando_global else "Local"
        tipo_origen = "Slab2 Global" if usando_global else ""
        #titulo_perfil = f"Perfil Perpendicular ({str_perfil} - {tipo_origen})"
        titulo_perfil = f"Perfil Perpendicular ({str_perfil})"
    else:
        titulo_perfil = f"Perfil Perpendicular ({str_perfil} - Sin Datos)"
        
    ax_perfil.set_title(titulo_perfil, fontsize=11, fontweight='bold', pad=10)
    
    # 6. Configurar Ejes y Límites (Encuadre natural de la curva)
    ax_perfil.set_xlabel("Longitud", fontsize=9, fontweight='bold', labelpad=8)
    ax_perfil.set_ylabel("Profundidad (km)", fontsize=9, fontweight='bold', labelpad=8)
    ax_perfil.tick_params(axis='both', labelsize=8)
    
    # El gráfico se encuadra donde empieza la sismicidad y el modelo real del slab
    if lon_slab:
        limite_izquierdo = lon_slab[0]
    else:
        limite_izquierdo = lon - RANGO_ANCHURA
        
    ax_perfil.set_xlim(limite_izquierdo, lon + RANGO_ANCHURA)
    
    prof_max_grafico = max(200, float(prof) + 50)
    ax_perfil.set_ylim(bottom=prof_max_grafico, top=-10) 
    
    # Suavizar la grilla interna
    ax_perfil.grid(True, linestyle=':', alpha=0.4, color='gray', zorder=0)

    # 7. CONFIGURACIÓN DE LEYENDA EXTERIOR HORIZONTAL (Parámetros corregidos para evitar conflictos)
    ax_perfil.legend(
        loc='upper center', 
        bbox_to_anchor=(0.5, -0.15),  # Mueve la caja hacia abajo, fuera del marco del perfil
        ncol=3,                       # Distribuye los elementos horizontalmente en 3 columnas
        fontsize=8,                   # Letra limpia y pequeña que no estorba
        frameon=True, 
        facecolor='#f9f9f9', 
        edgecolor='gray'              # Removido linewidth conflictivo de aquí
    )

    # Ajustar márgenes globales contemplando el espacio de la leyenda externa
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()
    print("[GRAFICADOR] Ventana cerrada por el operador. Volviendo al modo escucha...\n")

# =========================================================================
# LOOP PRINCIPAL: ESCUCHA AUTOMÁTICA DEL PORTAPAPELES
# =========================================================================
if __name__ == "__main__":
    print("=== CAPTURA DE DATOS DE SEISCOMP ===")
    print("Escuchando el portapapeles... Copia solucion desde scolv.")
    print("Al copiar solución se ploteará en planta y perfil.")
    print("Para cerrar el programa, presiona Ctrl + C en esta terminal.\n")
    
    try:
        pyperclip.copy("")
    except Exception as e:
        print(f"[Error] No se pudo inicializar pyperclip: {e}")
        sys.exit(1)

    ultimo_texto = ""
    
    try:
        while True:
            try:
                texto_actual = pyperclip.paste().strip()
            except Exception:
                time.sleep(0.5)
                continue
                
            if texto_actual and texto_actual != ultimo_texto and "csn_" in texto_actual:
                ultimo_texto = texto_actual
                print("[EVENTO DETECTADO] Procesando parámetros del portapapeles...")
                
                try:
                    partes = texto_actual.split(';')
                    if len(partes) >= 12:
                        fecha = partes[0].strip()
                        mag = float(partes[3].strip())
                        tipo_mag = partes[4]
                        texto_magnitud = f"{partes[3]} {tipo_mag}"

                        raw_lat = partes[8].strip()
                        lat = float(raw_lat.split()[0])
                        if 's' in raw_lat.lower():
                            lat = -abs(lat)
                            
                        raw_lon = partes[9].strip()
                        lon = float(raw_lon.split()[0])
                        if 'w' in raw_lon.lower() or 'o' in raw_lon.lower():
                            lon = -abs(lon)
                            
                        raw_prof = partes[10].strip()
                        prof = float(raw_prof.replace('km', '').strip())
                        
                        event_id = partes[-1].strip()
                        
                        plotear_evento(fecha, lat, lon, prof, mag, event_id)
                    else:
                        print("[Error] El formato de la línea copiada no tiene las columnas esperadas.")
                except Exception as ex:
                    print(f"[Error] Falló el parseo de la línea de SeisComP: {ex}")
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n[INFO] NewPT cerrado por el operador")
