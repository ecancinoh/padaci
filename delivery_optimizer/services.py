import os
import requests
from django.conf import settings
from clients.models import Cliente

def call_gemini_api(clients, num_vehicles, days_of_week, strategy="light"):
    api_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
    # Construir prompt en lenguaje natural
    dias = ', '.join(days_of_week)
    clientes_txt = '\n'.join([
        f"- Cliente {c.id}: lat {c.latitud}, lng {c.longitud}" for c in clients
    ])
    prompt = (
        f"Eres un optimizador de rutas de reparto. Tengo {num_vehicles} vehículos y los siguientes clientes con coordenadas:\n"
        f"{clientes_txt}\n"
        f"Quiero repartir los días: {dias}.\n"
        f"Dame una propuesta de asignación de clientes a vehículos para el día {dias.split(',')[0]}, en formato JSON, para una optimización {strategy}. "
        f"El JSON debe tener la forma: {{'vehiculo_1': [id_cliente1, id_cliente2, ...], ...}}. Explica brevemente tu razonamiento."
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    response = requests.post(url, json=data, timeout=60)
    response.raise_for_status()
    result = response.json()
    # Extraer respuesta de Gemini
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        text = str(result)
    # Buscar JSON en la respuesta
    import re, json as pyjson
    json_match = re.search(r'\{[\s\S]+\}', text)
    assignments = {}
    if json_match:
        try:
            assignments = pyjson.loads(json_match.group())
        except Exception:
            assignments = {}
    # Buscar explicación
    explicacion = text.split('}', 1)[-1].strip() if '}' in text else text
    return {
        "assignments": assignments,
        "explanation": explicacion,
        "vehicles_needed": num_vehicles,
    }
