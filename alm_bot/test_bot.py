#!/usr/bin/env python3
"""
Prueba rápida del ALM Bot local.
Simula una conversación completa sin depender de Meta.
"""

from bot_engine import procesar_mensaje
from database import obtener_historial, obtener_leads
import asyncio

SIMULACION = [
    {"channel": "whatsapp", "sender_id": "test_001", "sender_name": "Carlos",
     "text": "Hola, vi su Instagram y me interesa saber cómo puedo conseguir más clientes para mi negocio"},
    {"channel": "whatsapp", "sender_id": "test_001", "sender_name": "Carlos",
     "text": "Tengo una peluquería en Formosa"},
    {"channel": "whatsapp", "sender_id": "test_001", "sender_name": "Carlos",
     "text": "Hoy solo tengo Instagram pero publico muy de vez en cuando"},
    {"channel": "whatsapp", "sender_id": "test_001", "sender_name": "Carlos",
     "text": "Mi mayor desafío es que vienen pocos clientes nuevos, los que tengo son los de siempre"},
]


async def main():
    # Forzar UTF-8 en Windows
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("==  ALM BOT - SIMULACION DE CONVERSACION ==")
    print("=" * 50)
    print()

    for i, msg in enumerate(SIMULACION):
        print(f"--- Mensaje {i+1} ---")
        print(f"[Cliente] {msg['sender_name']}: {msg['text']}")
        print()

        resultado = await procesar_mensaje(
            channel=msg["channel"],
            sender_id=msg["sender_id"],
            sender_name=msg["sender_name"],
            message_text=msg["text"],
        )

        print(f"[LEO] {resultado['response']}")
        print(f"   Intencion: {resultado['intent']}")
        print(f"   Enviado: {'OK' if resultado['sent'] else 'SIN API KEY'}")
        print()

    # Mostrar historial guardado
    print("=" * 50)
    print("HISTORIAL GUARDADO EN SQLITE:")
    print("-" * 50)
    historial = obtener_historial("test_001")
    for h in historial:
        print(f"  [{h['created_at']}] {h['intent']}")
        print(f"    Cliente: {h['message'][:80]}")
        print(f"    Leo:     {h['response'][:80]}")
        print()

    leads = obtener_leads()
    print(f"Leads registrados: {len(leads)}")
    for l in leads:
        print(f"  - {l['sender_name']} ({l['sender_id']}) -- {l['status']}")

    print()
    print("Simulacion completada")


if __name__ == "__main__":
    asyncio.run(main())
