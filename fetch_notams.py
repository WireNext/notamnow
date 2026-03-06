import requests
import json
import re
import math

# Definimos las regiones por prefijos ICAO
REGIONES = {
    'EUROPA_S': '["LE","LP","LI","LG","LF"]',
    'EUROPA_N': '["EG","ED","EB","EL","EK","ES"]',
    'USA_CANADA': '["K","C"]',
    'LATAM': '["SB","SA","SC","SP","SK","SV","MP","MS"]',
    'ASIA_PACIFICO': '["RC","RJ","RK","RP","YB","NZ"]',
    'ORIENTE_MEDIO': '["OB","OE","OM","OK","LL"]'
}

def dmsc_to_decimal(coord_str):
    """Convierte formato NOTAM (4030N00340W) a decimal."""
    try:
        lat_deg = int(coord_str[0:2])
        lat_min = int(coord_str[2:4])
        lat_dir = coord_str[4]
        lon_deg = int(coord_str[5:8])
        lon_min = int(coord_str[8:10])
        lon_dir = coord_str[10]
        
        lat = lat_deg + (lat_min / 60)
        if lat_dir == 'S': lat = -lat
        
        lon = lon_deg + (lon_min / 60)
        if lon_dir == 'W': lon = -lon
        return [lon, lat]
    except:
        return None

def process_notams():
    all_features = []
    
    for nombre, codes in REGIONES.items():
        print(f"Descargando {nombre}...")
        url = f"https://api.autorouter.aero/v1.0/notam?itemas={codes}"
        try:
            r = requests.get(url, timeout=20)
            data = r.json()
            
            for item in data:
                linea_q = item.get('itemq', '')
                texto = item.get('iteme', '')
                id_notam = item.get('id', 'N/A')
                
                # Buscamos coordenadas en la línea Q (ej: 4030N00340W005)
                match = re.search(r'(\d{10}[NS]\d{11}|[0-9]{5}[NS][0-9]{6})', linea_q)
                if not match: # Si no está en Q, buscamos en el texto
                    match = re.search(r'(\d{4}[NS]\d{5}[EW])', texto)
                
                if match:
                    coord_raw = match.group(1)
                    coords = dmsc_to_decimal(coord_raw)
                    
                    # Extraer radio (últimos 3 dígitos de la secuencia si existen)
                    radio_nm = 5 # Radio por defecto 5 Millas Náuticas
                    if len(coord_raw) > 11:
                        try: radio_nm = int(coord_raw[-3:])
                        except: pass

                    if coords:
                        all_features.append({
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": coords},
                            "properties": {
                                "id": id_notam,
                                "region": nombre,
                                "text": texto,
                                "radius": radio_nm * 1852 # Convertir a metros para Leaflet
                            }
                        })
        except Exception as e:
            print(f"Error en {nombre}: {e}")

    # Guardar todo en un solo archivo GeoJSON
    with open('data/notams_global.json', 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f)

if __name__ == "__main__":
    process_notams()