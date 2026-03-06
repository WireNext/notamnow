import requests
import json
import re

# Definimos áreas rectangulares [lat_min, lon_min, lat_max, lon_max]
AREAS = {
    'EUROPA_OESTE': {'lamin': 34, 'lomin': -12, 'lamax': 60, 'lomax': 20},
    'USA_ESTE': {'lamin': 24, 'lomin': -85, 'lamax': 50, 'lomax': -65}
}

def parse_coords(text):
    if not text: return None
    # Buscamos el patrón clásico 4030N00340W o con espacios
    match = re.search(r'(\d{2,4}[NS])\s*(\d{3,5}[EW])', text)
    if match:
        try:
            lat_s, lon_s = match.group(1), match.group(2)
            # Limpiar letras y convertir a decimal
            lat_v = int(re.sub("[^0-9]", "", lat_s))
            lat = (lat_v // 100) + (lat_v % 100 / 60)
            if 'S' in lat_s: lat = -lat
            
            lon_v = int(re.sub("[^0-9]", "", lon_s))
            lon = (lon_v // 100) + (lon_v % 100 / 60)
            if 'W' in lon_s: lon = -lon
            return [round(lon, 4), round(lat, 4)]
        except: return None
    return None

def process():
    all_features = []
    # User-Agent para que parezca un navegador normal
    headers = {'User-Agent': 'Mozilla/5.0'}

    for nombre, coords in AREAS.items():
        print(f"Consultando OpenSky: {nombre}...")
        url = "https://opensky-network.org/api/notams"
        
        try:
            # Enviamos los parámetros de la caja de coordenadas
            r = requests.get(url, params=coords, headers=headers, timeout=20)
            
            if r.status_code == 200:
                data = r.json()
                print(f"¡Éxito! {len(data)} NOTAMs encontrados en {nombre}.")
                
                for item in data:
                    texto = item.get('text', '')
                    pos = parse_coords(texto)
                    
                    if pos:
                        all_features.append({
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": pos},
                            "properties": {
                                "id": item.get('icao24', 'N/A'), # ID de la zona
                                "text": texto,
                                "radius": 5000 # 5km por defecto
                            }
                        })
            else:
                print(f"Error {r.status_code} en OpenSky. Saltando...")
        except Exception as e:
            print(f"Error conexión: {e}")

    # Guardar GeoJSON final
    with open('data/notams_global.json', 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f, indent=2)
    
    print(f"FINALIZADO: {len(all_features)} NOTAMs con posición listos para el mapa.")

if __name__ == "__main__":
    process()