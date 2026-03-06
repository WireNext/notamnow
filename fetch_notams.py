import requests
import json
import re

# Prefijos ICAO para barrer el mundo
REGIONES = {
    'EUROPA': '["LE","LP","LI","LG","LF","EG","ED","EB","EK"]',
    'USA_CAN': '["K","C"]',
    'LATAM': '["SB","SA","SC","SP","SK","SV"]',
    'ASIA_PAC': '["RC","RJ","RK","RP","YB"]'
}

def parse_any_coord(text):
    """Busca coordenadas en formatos: 4030N00340W, 4030N 00340W, o 40.5 -3.4"""
    # 1. Formato estándar NOTAM: 4030N00340W (11 caracteres)
    match = re.search(r'(\d{4}[NS])\s*(\d{5}[EW])', text)
    if match:
        lat_str, lon_str = match.group(1), match.group(2)
        lat = int(lat_str[:2]) + int(lat_str[2:4])/60
        if 'S' in lat_str: lat = -lat
        lon = int(lon_str[:3]) + int(lon_str[3:5])/60
        if 'W' in lon_str: lon = -lon
        return [round(lon, 4), round(lat, 4)]
    
    # 2. Formato alternativo con espacios o puntos
    match = re.search(r'(\d{2})°?(\d{2})\'?([NS])\s*(\d{3})°?(\d{2})\'?([EW])', text)
    if match:
        lat = int(match.group(1)) + int(match.group(2))/60
        if match.group(3) == 'S': lat = -lat
        lon = int(match.group(4)) + int(match.group(5))/60
        if match.group(6) == 'W': lon = -lon
        return [round(lon, 4), round(lat, 4)]
        
    return None

def process():
    all_features = []
    for nombre, codes in REGIONES.items():
        print(f"Consultando {nombre}...")
        url = f"https://api.autorouter.aero/v1.0/notam?itemas={codes}"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code != 200: continue
            
            data = r.json()
            for item in data:
                # Prioridad 1: Línea Q (el estándar oficial)
                coords = parse_any_coord(item.get('itemq', ''))
                
                # Prioridad 2: Si Q falla, buscamos en el texto (Item E)
                if not coords:
                    coords = parse_any_coord(item.get('iteme', ''))
                
                if coords:
                    all_features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": coords},
                        "properties": {
                            "id": item.get('id', 'N/A'),
                            "region": nombre,
                            "text": item.get('iteme', 'Sin texto'),
                            "radius": 5000 # 5km por defecto si no hay radio
                        }
                    })
        except Exception as e:
            print(f"Error en {nombre}: {e}")

    # Guardar el JSON (asegúrate de que la carpeta data existe)
    with open('data/notams_global.json', 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f, indent=2)
    print(f"Proceso finalizado. Se han encontrado {len(all_features)} NOTAMs con posición.")

if __name__ == "__main__":
    process()