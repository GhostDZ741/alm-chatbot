#!/usr/bin/env python3
"""
Asistente de deploy — configura todo para subir ALM Bot a la nube gratis.
Ejecutá: python deploy_helper.py
"""

import os
import sys
import json
import shutil
from pathlib import Path
from config import BASE_DIR, ENV_PATH

CHECKLIST_FILE = BASE_DIR / "deploy_status.json"


def main():
    print("🦁  ASISTENTE DE DEPLOY - ALM CHATBOT")
    print("=========================================")
    print()

    estado = cargar_estado()

    print("1) ¿Qué necesitás para tener el bot 24/7 gratis?")
    print("   ─────────────────────────────────────────────")
    print("   El bot funciona así:")
    print()
    print("   Cliente → WhatsApp/IG/FB → Meta → Render.com → Groq AI → Responde")
    print("                                              → SQLite/Sheets 📊")
    print("                                              → CEO WhatsApp 📱")
    print()
    print("   Hosting: Render.com (free tier, nunca se apaga con UptimeRobot)")
    print("   IA: Groq Llama 3.3 70B (gratis, 30 req/min)")
    print("   CRM: SQLite local + Google Sheets (opcional)")
    print()

    # ── Paso 1: Groq ──
    print("═" * 45)
    print("PASO 1: Groq API Key (gratis, sin tarjeta)")
    print("─" * 45)
    if tiene_clave("GROQ_API_KEY"):
        print("   ✅ Ya configurada")
    else:
        print("   1. Andá a https://console.groq.com")
        print("   2. Creá cuenta gratis (Google login)"
              "")
        print("   3. API Keys → Create API Key")
        print("   4. Copiá la key que empieza con gsk_...")
        print()
        key = input("   Pegá tu API Key de Groq (o Enter para después): ").strip()
        if key.startswith("gsk_"):
            set_env("GROQ_API_KEY", key)
            print("   ✅ Guardada!")
        else:
            print("   ⏭  Podés hacerlo después editando alm_bot/.env")

    # ── Paso 2: Meta Developers ──
    print()
    print("═" * 45)
    print("PASO 2: Meta App (WhatsApp API)")
    print("─" * 45)
    if tiene_clave("WHATSAPP_PHONE_NUMBER_ID"):
        print("   ✅ WhatsApp ya configurado")
    else:
        print("   1. Andá a https://developers.facebook.com")
        print("   2. My Apps → Create App → Business")
        print("   3. En WhatsApp → Getting Started:")
        print("      - Phone number ID (está al lado del número de prueba)")
        print("      - Temporary access token (botón Generate Token)")
        print("   4. Envialos cuando los tengas")
        print()

    # ── Paso 3: Google Sheets (opcional) ──
    print()
    print("═" * 45)
    print("PASO 3: Google Sheets (opcional — para ver leads online)")
    print("─" * 45)
    if tiene_clave("GOOGLE_SHEETS_ID"):
        print("   ✅ Google Sheets ya configurado")
    else:
        print("   1. https://console.cloud.google.com → Nuevo proyecto")
        print("   2. Biblioteca → habilitar Google Sheets API + Google Drive API")
        print("   3. Crear credencial → Cuenta de servicio → descargar JSON")
        print("   4. Crear Google Sheet → compartir con client_email del JSON")
        print("   5. Copiar Sheet ID (de la URL entre /d/ y /edit)")
        print("   ⏭  Opcional — el bot funciona igual sin Sheets")

    # ── Paso 4: Render.com ──
    print()
    print("═" * 45)
    print("PASO 4: Deploy a Render.com (gratis, 24/7)")
    print("─" * 45)
    print("   Cuando tengas las API keys, te ayudo a:")
    print("   1. Crear cuenta en https://render.com (con GitHub)")
    print("   2. Crear repo en GitHub y pushear el código")
    print("   3. Conectar Render con el repo")
    print("   4. Configurar las variables de entorno")
    print("   5. El bot queda online automáticamente 🌐")
    print()

    # ── Paso 5: UptimeRobot ──
    print("═" * 45)
    print("PASO 5: UptimeRobot (mantiene el bot despierto 24/7)")
    print("─" * 45)
    print("   Render apaga el free tier a los 15 min sin uso.")
    print("   UptimeRobot le pega cada 5 min → nunca se apaga.")
    print("   1. https://uptimerobot.com → cuenta gratis")
    print("   2. Add Monitor → HTTP → https://tu-app.onrender.com/health")
    print("   ✅ Listo, 24/7 sin pagar")
    print()

    # ── Resumen ──
    print("═" * 45)
    print("RESUMEN")
    print("─" * 45)
    status = [
        ("Groq API", "✅" if tiene_clave("GROQ_API_KEY") else "⬜ Pendiente"),
        ("WhatsApp API", "✅" if tiene_clave("WHATSAPP_PHONE_NUMBER_ID") else "⬜ Pendiente"),
        ("Google Sheets", "✅" if tiene_clave("GOOGLE_SHEETS_ID") else "⬜ Opcional"),
        ("Render.com", "⬜ Pendiente (al final)"),
        ("UptimeRobot", "⬜ Pendiente (al final)"),
    ]
    for nombre, check in status:
        print(f"   {check}  {nombre}")

    guardar_estado(estado)
    print()
    print("📁  Proyecto listo en:", BASE_DIR)
    print("▶️  Para probar local:  python main.py")
    print("🌐  http://localhost:8000")


# ── Helpers ───────────────────────────────────────────────

def tiene_clave(key: str) -> bool:
    return bool(os.getenv(key, "") or leer_env(key))


def leer_env(key: str) -> str:
    if not ENV_PATH.exists():
        return ""
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return ""


def set_env(key: str, value: str):
    lines = []
    replaced = False
    if ENV_PATH.exists():
        with open(ENV_PATH) as f:
            lines = f.readlines()
    with open(ENV_PATH, "w") as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f"{key}={value}\n")
                replaced = True
            else:
                f.write(line)
        if not replaced:
            f.write(f"{key}={value}\n")
    # Recargar en variable de entorno
    os.environ[key] = value


def cargar_estado() -> dict:
    if CHECKLIST_FILE.exists():
        with open(CHECKLIST_FILE) as f:
            return json.load(f)
    return {}


def guardar_estado(estado: dict):
    with open(CHECKLIST_FILE, "w") as f:
        json.dump(estado, f, indent=2)


if __name__ == "__main__":
    main()
