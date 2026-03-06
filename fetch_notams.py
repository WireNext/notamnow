import requests
import json
import re

# Usamos aeropuertos grandes para asegurar que SIEMPRE hay NOTAMs
REGIONES = {
    'EUROPA': '["LEMD","LEBL","EGLL","LFPG","EDDF"]',
    'USA': '["KJFK","KLAX","KORD"]'
}

def parse_coords(text):
    if not text: return None
    # Buscamos el patrón latitud/longitud (ej: 4030N00340W)
    match = re.search(r'(\d{4}[NS])\s*(\d{5}[EW])', text)
    if match:
        try:
            lat_s, lon_s = match.group(1), match.group(2)
            lat = int(lat_s[:2]) + int(lat_s[2:4])/60
            if 'S' in lat_s: lat = -lat
            lon = int(lon_s[:3]) + int(lon_s[3:5])/60
            if 'W' in lon_s: lon = -lon
            return [round(lon, 4), round(lat, 4)]
        except: return None
    return None

def process():
    all_features = []
    # IMPORTANTE: Añadimos un User-Agent para que la API no nos bloquee
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for nombre, codes in REGIONES.items():
        url = f"https://api.autorouter.aero/v1.0/notam?itemas={codes}"
        print(f"Intentando conectar con {nombre}...")
        
        try:
            r = requests.get(url, headers=headers, timeout=25)
            
            # Si la API responde pero no es un JSON, imprimimos el error para saber qué pasa
            if r.status_code != 200:
                print(f"Error de API {r.status_code}: Posible bloqueo o mantenimiento.")
                continue

            data = r.json()
            print(f"¡Conectado! Recibidos {len(data)} NOTAMs brutos.")
            
            for item in data:
                # Buscamos en itemq (línea Q) o iteme (texto descriptivo)
                coords = parse_coords(item.get('itemq', '')) or parse_coords(item.get('iteme', ''))
                
                if coords:
                    all_features.append({
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": coords},
                        "properties": {
                            "id": item.get('id', 'N/A'),
                            "text": item.get('iteme', 'No text'),
                            "radius": 5000 
                        }
                    })
        except Exception as e:
            print(f"Error crítico en {nombre}: {e}")

    # Guardar resultado
    output = {"type": "FeatureCollection", "features": all_features}
    with open('data/notams_global.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nFINALIZADO: {len(all_features)} NOTAMs geolocalizados guardados en JSON.")

if __name__ == "__main__":
    process()