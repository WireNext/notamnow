import requests
import json
import re

# Reducimos a un par de regiones para probar rápido
REGIONES = {
    'EUROPA_TEST': '["LEMD","LEBL","EGLL","LFPG"]',
    'USA_TEST': '["KJFK","KLAX"]'
}

def parse_coords(text):
    if not text: return None
    # Este Regex busca cualquier combinación de 4-5 números seguidos de N/S y 4-5 de E/W
    # Ejemplos: 4030N00340W, 4030N 00340W, 40.5N 003.4W
    match = re.search(r'(\d{2,4}[NS])\s*(\d{3,5}[EW])', text)
    if match:
        try:
            lat_str = match.group(1)
            lon_str = match.group(2)
            
            # Extraer solo los números y convertir a decimal
            lat_val = int(re.sub("[^0-9]", "", lat_str))
            lat_deg = lat_val // 100 if lat_val > 99 else lat_val
            lat_min = lat_val % 100 if lat_val > 99 else 0
            lat = lat_deg + (lat_min / 60)
            if 'S' in lat_str: lat = -lat
            
            lon_val = int(re.sub("[^0-9]", "", lon_str))
            lon_deg = lon_val // 100 if lon_val > 99 else lon_val
            lon_min = lon_val % 100 if lon_val > 99 else 0
            lon = lon_deg + (lon_min / 60)
            if 'W' in lon_str: lon = -lon
            
            return [round(lon, 4), round(lat, 4)]
        except:
            return None
    return None

def process():
    all_features = []
    for nombre, codes in REGIONES.items():
        url = f"https://api.autorouter.aero/v1.0/notam?itemas={codes}"
        print(f"--- Consultando {nombre} ---")
        try:
            r = requests.get(url, timeout=20)
            data = r.json()
            
            # DEBUG: Imprimir el primer NOTAM para ver qué trae
            if len(data) > 0:
                print(f"Ejemplo de dato recibido: {data[0].get('itemq', 'No tiene itemq')}")
            
            for item in data:
                # Intentamos extraer de 'itemq' o 'iteme'
                coords = parse_coords(item.get('itemq', ''))
                if not coords:
                    coords = parse_coords(item.get('iteme', ''))
                
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
            print(f"Error: {e}")

    # Forzar la creación del archivo aunque esté vacío para no romper el push
    output = {"type": "FeatureCollection", "features": all_features}
    with open('data/notams_global.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nRESULTADO FINAL: {len(all_features)} NOTAMs encontrados.")

if __name__ == "__main__":
    process()