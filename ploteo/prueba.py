#!/usr/bin/env python3
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Configuración de prueba con los datos de tu evento real
event_id = "csn_sc62026ncnsc"
fecha = "2026-07-06 08:11:33"
mag = 4.2
prof = 340
lat = -22.61
lon = -66.83

# Estilo sismológico limpio
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig = plt.figure(figsize=(13, 6))
fig.suptitle(f"Foco Sísmico: {event_id}\nFecha/Hora: {fecha} | Magnitud: {mag} | Profundidad: {prof} km", 
             fontsize=12, fontweight='bold', y=0.96)

size = float(mag) * 50

# 1. PLANTA
ax_planta = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
ax_planta.coastlines(resolution='50m', color='#1a1a1a', linewidth=1.2, zorder=2)
ax_planta.add_feature(cfeature.BORDERS.with_scale('50m'), edgecolor='#555555', linestyle='--', linewidth=0.8, zorder=2)
ax_planta.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#f7f7f4', zorder=1)
ax_planta.add_feature(cfeature.OCEAN.with_scale('50m'), facecolor='#eef5fa', zorder=1)

ax_planta.scatter(lon, lat, s=size, color='#ff3333', alpha=0.9, edgecolors='black', 
                  linewidth=1.5, zorder=5, transform=ccrs.PlateCarree(), label="Epicentro")
ax_planta.set_extent([lon - 2.5, lon + 2.5, lat - 2.5, lat + 2.5], crs=ccrs.PlateCarree())

gl = ax_planta.gridlines(draw_labels=True, linestyle=':', alpha=0.6, color='gray', zorder=3)
gl.top_labels, gl.right_labels = False, False

ax_planta.set_title("Vista en Planta", fontsize=11, fontweight='bold', pad=10)
ax_planta.legend(loc="upper right")

# 2. PERFIL
ax_perfil = fig.add_subplot(1, 2, 2)
ax_perfil.scatter(lon, prof, s=size, color='#ff3333', alpha=0.8, edgecolors='black', linewidth=1.5, zorder=3)
ax_perfil.set_title("Perfil de Profundidad (W - E)", fontsize=11, fontweight='bold', pad=10)
ax_perfil.set_xlabel("Longitud", fontsize=10, labelpad=8)
ax_perfil.set_ylabel("Profundidad (km)", fontsize=10, labelpad=8)
ax_perfil.set_ylim(bottom=prof + 40, top=-5) 
ax_perfil.set_xlim(lon - 1.5, lon + 1.5)
ax_perfil.grid(True, linestyle=':', alpha=0.6, color='gray')

plt.tight_layout(rect=[0, 0, 1, 0.93])

# GUARDAR IMAGEN EN DISCO
output_image = "ejemplo_alta_calidad.png"
plt.savefig(output_image, dpi=150)
print(f"[✓] Imagen de prueba generada con éxito: '{output_image}'")