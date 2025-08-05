import json
import time
import requests
from datetime import datetime

# --- Configurações ---
API_URL = "https://api.flightradar24.com/common/v1/airport.json"
OUTPUT_FILE = "flight_schedule.json"
REFRESH_INTERVAL = 10  # Intervalo em segundos entre as coletas
AIRPORT_CODE = "cgh"   # Código do aeroporto (Congonhas)
LIMIT = 100            # Limite de voos por página

def get_current_timestamp():
    """Retorna o timestamp Unix atual."""
    return int(time.time())

def fetch_flight_data():
    """
    Busca os dados de voos diretamente da API do FlightRadar24.
    O token é opcional e a API parece funcionar sem ele.
    """
    print(f"Buscando dados para o aeroporto: {AIRPORT_CODE.upper()}")
    timestamp = get_current_timestamp()

    # Parâmetros para a requisição da API
    params = {
        "code": AIRPORT_CODE,
        "plugin[]": "schedule",
        "plugin-setting[schedule][mode]": "",
        "plugin-setting[schedule][timestamp]": timestamp,
        "page": 1,
        "limit": LIMIT,
    }

    try:
        # Adiciona um User-Agent para simular um navegador
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(API_URL, params=params, headers=headers)
        response.raise_for_status()  # Lança um erro para status 4xx ou 5xx
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP ao chamar a API: {http_err}")
        print(f"Corpo da resposta: {response.text}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    return None

def extract_and_save_flights(data):
    """Extrai os dados relevantes e salva em um arquivo JSON."""
    if not data:
        print("Nenhum dado recebido para processar.")
        return

    try:
        # Caminho para os dados de chegadas e partidas na resposta da API
        schedule_data = data["result"]["response"]["airport"]["pluginData"]["schedule"]
        arrivals = schedule_data.get("arrivals", {}).get("data", [])
        departures = schedule_data.get("departures", {}).get("data", [])

        output_data = {
            "airport": AIRPORT_CODE.upper(),
            "fetched_at_utc": datetime.utcnow().isoformat() + "Z",
            "arrivals": arrivals[:10],    # Pega os 10 primeiros
            "departures": departures[:10] # Pega os 10 primeiros
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)

        print(f"✅ Dados de {len(arrivals)} chegadas e {len(departures)} partidas salvos com sucesso em '{OUTPUT_FILE}'")

    except (KeyError, TypeError) as e:
        print(f"Erro ao extrair os dados do JSON. A estrutura da resposta pode ter mudado.")
        print(f"Detalhe do erro: {e}")

if __name__ == "__main__":
    #while True:
        print(f"\n--- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        flight_data = fetch_flight_data()
        extract_and_save_flights(flight_data)
      # print(f"Aguardando {REFRESH_INTERVAL} segundos para a próxima coleta...")
      # time.sleep(REFRESH_INTERVAL)