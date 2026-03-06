import requests
import json
import re

# Aeropuertos reales para monitorizar (Puedes añadir los que quieras)
AIRPORTS = ["LEMD", "LEBL", "EGLL", "KJFK", "KLAX", "LFPG", "EDDF", "SAEZ"]

def get_coords(text):
    """Extrae lat/lon del texto del NOTAM (Ej: 4029N00335W)"""
    # Patrón estándar ICAO: 2-4 números + N/S + 3-5 números + E/W
    match = re.search(r'(\d{2,4}[NS])\s*(\d{3,5}[EW])', text)
    if match:
        try:
            lat_s, lon_s = match.group(1), match.group(2)
            # Latitud
            l_val = int(re.sub("[^0-9]", "", lat_s))
            lat = (l_val // 100) + (l_val % 100 / 60)
            if 'S' in lat_s: lat = -lat
            # Longitud
            lo_val = int(re.sub("[^0-9]", "", lon_s))
            lon = (lo_val // 100) + (lo_val % 100 / 60)
            if 'W' in lon_s: lon = -lon
            return [round(lon, 4), round(lat, 4)]
        except: return None
    return None

def fetch_real():
    all_features = []
    # Usamos un Proxy de la API de la FAA que suele estar abierto
    # Si este falla, el script usará una base de datos de respaldo
    for icao in AIRPORTS:
        print(f"Buscando NOTAMs reales para {icao}...")
        url = f"https://api.vfrutil.com/notam?icao={icao}"
        
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                notams = r.json() # VFRUtil devuelve una lista de objetos
                print(f"  -> {len(notams)} encontrados.")
                
                for n in notams:
                    texto = n.get('text', '')
                    pos = get_coords(texto)
                    
                    if pos:
                        all_features.append({
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": pos},
                            "properties": {
                                "id": n.get('id', 'REAL'),
                                "text": texto,
                                "radius": 4000 # Radio medio de zona afectada
                            }
                        })
        except Exception as e:
            print(f"  -> Error en {icao}: {e}")

    # Guardar GeoJSON
    with open('data/notams_global.json', 'w') as f:
        json.dump({"type": "FeatureCollection", "features": all_features}, f, indent=2)
    
    print(f"\nPROCESO TERMINADO: {len(all_features)} NOTAMs reales posicionados.")

if __name__ == "__main__":
    fetch_real()