#!/usr/bin/env python3
"""
Extrae datos REALES de Google Analytics y los envía a Telegram
Optimizado para ejecutarse en GitHub Actions
"""

import requests
import json
import os
from datetime import datetime, timedelta

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8981262533:AAHkqtjmSSJBVEkIGxK_2q8Flh6j__pvTgY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7799024484")

FISHZONE_PROPERTY_ID = "534868709"
ONEAGENCY_PROPERTY_ID = "538254745"

def load_tokens():
    if os.path.exists("ga_oauth_tokens.json"):
        try:
            with open("ga_oauth_tokens.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    tokens_path = os.path.join(
        os.path.expanduser("~"),
        "OneDrive", "Escritorio", "Proyectos Claude Code", "ga_oauth_tokens.json"
    )
    if os.path.exists(tokens_path):
        try:
            with open(tokens_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    print(f"❌ No se encontró ga_oauth_tokens.json")
    return None

def get_analytics_data(access_token, property_id):
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "dateRanges": [{"startDate": yesterday, "endDate": today}],
        "metrics": [
            {"name": "activeUsers"},
            {"name": "sessions"},
            {"name": "bounceRate"},
            {"name": "conversions"}
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("rows"):
                row = data["rows"][0]
                return {
                    "usuarios": row["metricValues"][0]["value"],
                    "sesiones": row["metricValues"][1]["value"],
                    "tasa_rebote": f"{float(row['metricValues'][2]['value']):.1f}%",
                    "conversiones": row["metricValues"][3]["value"]
                }
        else:
            print(f"Error en API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    return None

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")
        return False

def main():
    print("📊 Extrayendo analíticas de Google Analytics...")

    tokens = load_tokens()
    if not tokens:
        print("❌ No se pudieron cargar los tokens")
        return

    fishzone_access_token = tokens.get("fishzone", {}).get("access_token")
    oneagency_access_token = tokens.get("oneagency", {}).get("access_token")

    print("🎣 Extrayendo FishZone...")
    fishzone = get_analytics_data(fishzone_access_token, FISHZONE_PROPERTY_ID)

    print("🔗 Extrayendo One Agency...")
    oneagency = get_analytics_data(oneagency_access_token, ONEAGENCY_PROPERTY_ID)

    message = "📊 <b>ANALÍTICAS DIARIAS</b>\n\n"

    if fishzone:
        message += f"""🎣 <b>FishZone</b>
- Usuarios: {fishzone.get('usuarios', 'N/A')}
- Sesiones: {fishzone.get('sesiones', 'N/A')}
- Tasa rebote: {fishzone.get('tasa_rebote', 'N/A')}
- Conversiones: {fishzone.get('conversiones', 'N/A')}

"""
    else:
        message += "🎣 <b>FishZone</b>\n⚠️ No hay datos de FishZone por ahora\n\n"

    if oneagency:
        message += f"""🔗 <b>One Agency (one-agency.es)</b>
- Usuarios: {oneagency.get('usuarios', 'N/A')}
- Sesiones: {oneagency.get('sesiones', 'N/A')}
- Tasa rebote: {oneagency.get('tasa_rebote', 'N/A')}
- Conversiones: {oneagency.get('conversiones', 'N/A')}

"""
    else:
        message += "🔗 <b>One Agency</b>\n⚠️ Error en extracción\n\n"

    message += f"📈 <i>Reporte del {datetime.now().strftime('%Y-%m-%d %H:%M')} (GitHub Actions)</i>"

    print("\n📤 Enviando a Telegram...")
    if send_telegram(message):
        print("✅ Mensaje enviado a Telegram exitosamente!")
    else:
        print("❌ Error al enviar a Telegram")

if __name__ == "__main__":
    main()
