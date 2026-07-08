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
    fig.suptitle(f"Monitor de Turno - Evento: {event_id}\nFecha: {fecha} | M {mag} | Profundidad: {prof} km", 
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
    # 2. SELECCIÓN Y CARGA DE LA SUBDUCCIÓN (MÉTODO HÍBRIDO ACOTRADO)
    # =========================================================================
    pto1 = (-72, -19)
    pto2 = (-68.4, -18)
    
    # Rangos de longitud reales de las listas definidos en perfilesOPA.py
    lista_limites_lon = [
        (pto1[0], pto2[0] + 1),      # P01
        (pto1[0], pto2[0] + 1),      # P02
        (pto1[0], pto2[0] + 2),      # P03
        (pto1[0], pto2[0] + 2),      # P04
        (pto1[0] - 1, pto2[0] + 1),  # P05
        (pto1[0] - 1, pto2[0] + 1),  # P06
        (pto1[0] - 2, pto2[0] + 1),  # P07
        (pto1[0] - 2, pto2[0] + 1),  # P08
        (pto1[0] - 3, pto2[0]),      # P09
        (pto1[0] - 4, pto2[0] - 1),  # P010
        (pto1[0] - 4, pto2[0] - 1),  # P011
        (pto1[0] - 4, pto2[0] - 1),  # P012
        (pto1[0] - 5, pto2[0] - 2)   # P013
    ]

    m, c = np.polyfit([pto1[0], pto2[0]], [pto1[1], pto2[1]], 1)
    suma_c = [-1, -3, -5, -6, -8, -10, -12, -14, -16, -18, -20, -22, -24]
    str_rectas = ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P010", "P011", "P012", "P013"]

    distancias_a_perfiles = []
    
    for i in range(len(str_rectas)):
        # Verificar si la longitud del sismo está dentro del segmento del perfil (con margen de 1.5 grados)
        lon_min = lista_limites_lon[i][0] - 1.5
        lon_max = lista_limites_lon[i][1] + 1.5
        
        if lon_min <= lon <= lon_max:
            a_pend = m
            b_int = c + suma_c[i]
            dist = np.abs(a_pend * lon - lat + b_int) / np.sqrt(a_pend**2 + 1)
            distancias_a_perfiles.append((dist, i))
        else:
            # Si el sismo queda fuera del rango longitudinal físico del perfil, le asignamos distancia infinita
            distancias_a_perfiles.append((float('inf'), i))

    # Seleccionar el perfil válido más cercano
    distancias_validas = [d[0] for d in distancias_a_perfiles]
    idx_mejor_perfil = np.argmin(distancias_validas)
    
    # RESPALDO EXTRA: Si por alguna razón extrema todos dieron infinito, usamos la latitud clásica
    if distancias_validas[idx_mejor_perfil] == float('inf'):
        latitudes_perfiles = {1:-19.0, 2:-19.8, 3:-20.5, 4:-21.2, 5:-21.8, 6:-22.5, 7:-23.2, 8:-23.8, 9:-24.5, 10:-25.2, 11:-25.8, 12:-26.5, 13:-27.2}
        idx_mejor_perfil = min(latitudes_perfiles, key=lambda k: abs(latitudes_perfiles[k] - lat)) - 1

    str_perfil = str_rectas[idx_mejor_perfil]
    arch_slab_tmp = f"./grillas/slab{str_perfil}.tmp"
    lon_slab, prof_slab = [], []
    usando_global = False

    print(f"[DEBUG SLAB] Sismo en ({lat:.2f}, {lon:.2f}). Perfil óptimo asignado: {str_perfil}")

    # Intentar cargar el perfil precalculado (.tmp) asignado
    if os.path.exists(arch_slab_tmp):
        try:
            with open(arch_slab_tmp, 'r') as f:
                for linea in f:
                    if linea.startswith('#') or not linea.strip():
                        continue
                    partes = linea.strip().split()
                    
                    if len(partes) >= 7:
                        l_val = float(partes[2]) # Columna 2
                        if (lon - (RANGO_ANCHURA + 1.0) <= l_val <= lon + (RANGO_ANCHURA + 1.0)):
                            lon_slab.append(l_val)
                            prof_slab.append(abs(float(partes[6]))) # Columna 6
            if lon_slab:
                print(f"[SLAB] ¡Éxito! Graficando usando perfil precalculado: {str_perfil}")
            else:
                print(f"[Aviso] El archivo {arch_slab_tmp} existe pero no tiene puntos en el rango longitudinal del sismo.")
        except Exception as e:
            print(f"[Aviso] Error leyendo archivo de perfil {arch_slab_tmp}: {e}")
    else:
        print(f"[Aviso] El archivo de perfil NO EXISTE: {arch_slab_tmp}")

    # RESPALDO AUTOMÁTICO DESDE SLAB2 GLOBAL (.XYZ)
    if not lon_slab:
        arch_slab_xyz = "./grillas/sam_slab2_dep_02.23.18.xyz"
        if os.path.exists(arch_slab_xyz):
            try:
                print(f"[SLAB] Recurriendo a respaldo global (.xyz) para evitar gráfico vacío...")
                lon_slab_perfil = np.linspace(lon - RANGO_ANCHURA, lon + RANGO_ANCHURA, 100)
                puntos_slab = {}
                ANCHO_LAT = 0.5
                
                with open(arch_slab_xyz, 'r') as f:
                    for linea in f:
                        if linea.startswith('#') or not linea.strip():
                            continue
                        partes = linea.strip().split()
                        if len(partes) >= 3:
                            s_lon = float(partes[0])
                            if s_lon > 180:
                                s_lon -= 360
                                
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
                    prof_interp = np.interp(lon_slab_perfil, lons_ordenadas, profs_promedio, left=np.nan, right=np.nan)
                    
                    mask = ~np.isnan(prof_interp)
                    lon_slab = list(lon_slab_perfil[mask])
                    prof_slab = list(prof_interp[mask])
                    usando_global = True
                    print(f"[SLAB] Línea de subducción calculada desde grilla global.")
            except Exception as e:
                print(f"[Aviso] No se pudo procesar el Slab global: {e}")

    """
    # =========================================================================
    # 2. SELECCIÓN Y CARGA DE LA SUBDUCCIÓN (MÉTODO MATEMÁTICO REAL DE PERFILES OPA)
    # =========================================================================
    # Replicamos la geometría exacta de perfilesOPA.py
    pto1 = (-72, -19)
    pto2 = (-68.4, -18)
    m, c = np.polyfit([pto1[0], pto2[0]], [pto1[1], pto2[1]], 1)
    suma_c = [-1, -3, -5, -6, -8, -10, -12, -14, -16, -18, -20, -22, -24]
    str_rectas = ["P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P010", "P011", "P012", "P013"]

    # Calcular a qué recta pertenece el sismo por distancia perpendicular mínima
    distancias_a_perfiles = []
    for i in range(len(str_rectas)):
        a_pend = m
        b_int = c + suma_c[i]
        # Distancia perpendicular: |ax - y + b| / sqrt(a^2 + 1)
        dist = np.abs(a_pend * lon - lat + b_int) / np.sqrt(a_pend**2 + 1)
        distancias_a_perfiles.append(dist)

    # El índice del perfil con menor distancia matemática real
    idx_mejor_perfil = np.argmin(distancias_a_perfiles)
    str_perfil = str_rectas[idx_mejor_perfil]
    
    arch_slab_tmp = f"./grillas/slab{str_perfil}.tmp"
    lon_slab, prof_slab = [], []
    usando_global = False

    print(f"[DEBUG SLAB] Sismo en ({lat:.2f}, {lon:.2f}). Perfil matemático asignado: {str_perfil}")

    # Intentar cargar el perfil precalculado (.tmp) asignado
    if os.path.exists(arch_slab_tmp):
        try:
            with open(arch_slab_tmp, 'r') as f:
                for linea in f:
                    if linea.startswith('#') or not linea.strip():
                        continue
                    partes = linea.strip().split()
                    
                    if len(partes) >= 7:
                        l_val = float(partes[2]) # Columna 2 (Longitud proyectada en el perfil)
                        # Como el perfil local está acotado, ampliamos un poco la tolerancia de captura si es necesario
                        if (lon - (RANGO_ANCHURA + 1.0) <= l_val <= lon + (RANGO_ANCHURA + 1.0)):
                            lon_slab.append(l_val)
                            prof_slab.append(abs(float(partes[6]))) # Columna 6 (Profundidad)
            if lon_slab:
                print(f"[SLAB] ¡Éxito! Graficando usando perfil precalculado: {str_perfil}")
            else:
                print(f"[Aviso] El archivo {arch_slab_tmp} existe, pero sus puntos quedan fuera del rango longitudinal del sismo.")
        except Exception as e:
            print(f"[Aviso] Error leyendo archivo de perfil {arch_slab_tmp}: {e}")
    else:
        print(f"[Aviso] El archivo de perfil NO EXISTE: {arch_slab_tmp}")

    # RESPALDO AUTOMÁTICO: Si no se encontraron puntos válidos en el .tmp local, recurre a Slab2 global
    if not lon_slab:
        arch_slab_xyz = "./grillas/sam_slab2_dep_02.23.18.xyz"
        if os.path.exists(arch_slab_xyz):
            try:
                print(f"[SLAB] Recurriendo a respaldo: Escaneando Slab2 global (.xyz)...")
                lon_slab_perfil = np.linspace(lon - RANGO_ANCHURA, lon + RANGO_ANCHURA, 100)
                puntos_slab = {}
                ANCHO_LAT = 0.5
                
                with open(arch_slab_xyz, 'r') as f:
                    for linea in f:
                        if linea.startswith('#') or not linea.strip():
                            continue
                        partes = linea.strip().split()
                        if len(partes) >= 3:
                            s_lon = float(partes[0])
                            if s_lon > 180:
                                s_lon -= 360
                                
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
                    prof_interp = np.interp(lon_slab_perfil, lons_ordenadas, profs_promedio, left=np.nan, right=np.nan)
                    
                    mask = ~np.isnan(prof_interp)
                    lon_slab = list(lon_slab_perfil[mask])
                    prof_slab = list(prof_interp[mask])
                    usando_global = True
                    print(f"[SLAB] Línea de subducción calculada desde grilla global (.xyz).")
            except Exception as e:
                print(f"[Aviso] No se pudo procesar el Slab global: {e}")
    """

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
    ax_planta.set_title("Vista en Planta (Contexto Local)", fontsize=11, fontweight='bold', pad=10)

    # =========================================================================
    # 4. CONSTRUCCIÓN GRÁFICA - PLOT 2: VISTA EN PERFIL (W - E)
    # =========================================================================
    ax_perfil = fig.add_subplot(1, 2, 2)
    
    if lon_b:
        ax_perfil.scatter(lon_b, prof_b, color='gray', alpha=0.3, s=6, marker='.', zorder=1, label="Sismicidad Histórica")

    # Graficar la línea de contacto corregida usando str_perfil
    if lon_slab and prof_slab:
        label_linea = "Contacto Placas (Slab2 Global)" if usando_global else f"Contacto Placas (Perfil {str_perfil})"
        ax_perfil.plot(lon_slab, prof_slab, color='black', linestyle='-', linewidth=2.2, 
                       zorder=3, label=label_linea)
    
    """
    # Graficar la línea de contacto corregida
    if lon_slab and prof_slab:
        label_linea = "Contacto Placas (Slab2 Global)" if usando_global else f"Contacto Placas (Perfil P{perfil_id:02d})"
        ax_perfil.plot(lon_slab, prof_slab, color='black', linestyle='-', linewidth=2.2, 
                       zorder=3, label=label_linea)
    """
    ax_perfil.scatter(lon, prof, s=size, color='#ff3333', alpha=0.9, edgecolors='black', linewidth=1.5, zorder=5, label="Hipocentro Real")
    
    #ax_perfil.set_title("Perfil Corto Perpendicular (W - E)", fontsize=11, fontweight='bold', pad=10)
    
    # Forzar el despliegue del perfil asignado matemáticamente en el título
    if lon_slab:
        tipo_origen = "Slab2 Global" if usando_global else "Local"
        titulo_perfil = f"Perfil Corto Perpendicular W - E ({str_perfil} - {tipo_origen})"
    else:
        titulo_perfil = f"Perfil Corto Perpendicular W - E ({str_perfil} - Sin Datos)"
        
    ax_perfil.set_title(titulo_perfil, fontsize=11, fontweight='bold', pad=10)
    
    ax_perfil.set_xlabel("Longitud", fontsize=10, labelpad=8)
    ax_perfil.set_ylabel("Profundidad (km)", fontsize=10, labelpad=8)
    
    ax_perfil.set_xlim(lon - RANGO_ANCHURA, lon + RANGO_ANCHURA)
    prof_max_grafico = max(200, float(prof) + 50)
    ax_perfil.set_ylim(bottom=prof_max_grafico, top=-5) 
    
    ax_perfil.grid(True, linestyle=':', alpha=0.6, color='gray')
    ax_perfil.legend(loc="upper left", frameon=True, facecolor='white')

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.show()
    print("[GRAFICADOR] Ventana cerrada por el operador. Volviendo al modo escucha...\n")

# =========================================================================
# LOOP PRINCIPAL: ESCUCHA AUTOMÁTICA DEL PORTAPAPELES
# =========================================================================
if __name__ == "__main__":
    print("=== MONITOR SEISCOMP + MAPA BASE GEOGRÁFICO ===")
    print("Escuchando el portapapeles... Copia soluciones en SeisComP.")
    print("Cada nuevo evento abrirá automáticamente su planta con mapa y perfil.")
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
        print("\n[INFO] Monitor cerrado por el operador. ¡Buen turno!")
