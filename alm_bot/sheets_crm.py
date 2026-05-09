"""
Integración opcional con Google Sheets.

Si no hay credenciales configuradas, el bot funciona igual con SQLite local.
Google Sheets permite al CEO ver las conversaciones y leads online.
"""

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import GOOGLE_SHEETS_ID, GOOGLE_SERVICE_ACCOUNT_EMAIL, GOOGLE_PRIVATE_KEY

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _service():
    if not all([GOOGLE_SHEETS_ID, GOOGLE_SERVICE_ACCOUNT_EMAIL, GOOGLE_PRIVATE_KEY]):
        return None
    creds = service_account.Credentials.from_service_account_info(
        {
            "type": "service_account",
            "client_email": GOOGLE_SERVICE_ACCOUNT_EMAIL,
            "private_key": GOOGLE_PRIVATE_KEY,
            "token_uri": "https://oauth2.googleapis.com/token",
        },
        scopes=SCOPES,
    )
    return build("sheets", "v4", credentials=creds).spreadsheets()


async def inicializar_hojas():
    """Crea las hojas Conversaciones y Leads si no existen."""
    service = _service()
    if not service:
        print("ℹ️  Google Sheets no configurado — usando SQLite local.")
        return

    try:
        hoja = service.get(spreadsheetId=GOOGLE_SHEETS_ID).execute()
        titles = [s["properties"]["title"] for s in hoja.get("sheets", [])]

        _crear_si_no_existe(service, "Conversaciones",
                            [["sender_id", "channel", "sender_name",
                              "last_message", "last_response", "intent",
                              "status", "updated_at"]])
        _crear_si_no_existe(service, "Leads",
                            [["fecha", "nombre", "canal", "negocio",
                              "ciudad", "dolor_detectado", "estado", "notas"]])
        print("✅ Hojas de Google Sheets verificadas/creadas.")
    except Exception as e:
        print(f"⚠️  Error al conectar con Google Sheets: {e}")


def _crear_si_no_existe(service, titulo, headers):
    try:
        service.values().update(
            spreadsheetId=GOOGLE_SHEETS_ID,
            range=f"{titulo}!A1",
            valueInputOption="RAW",
            body={"values": headers},
        ).execute()
    except Exception:
        # La hoja no existe, la creamos
        body = {"requests": [{"addSheet": {"properties": {"title": titulo}}}]}
        try:
            service.batchUpdate(spreadsheetId=GOOGLE_SHEETS_ID, body=body).execute()
            service.values().update(
                spreadsheetId=GOOGLE_SHEETS_ID,
                range=f"{titulo}!A1",
                valueInputOption="RAW",
                body={"values": headers},
            ).execute()
        except Exception as e:
            print(f"  ⚠️  No se pudo crear hoja '{titulo}': {e}")


async def guardar_conversacion(sender_id, channel, sender_name,
                                last_message, last_response, intent):
    """Guarda un intercambio en la hoja Conversaciones."""
    service = _service()
    if not service:
        return
    from datetime import datetime
    try:
        service.values().append(
            spreadsheetId=GOOGLE_SHEETS_ID,
            range="Conversaciones!A:H",
            valueInputOption="RAW",
            body={"values": [[sender_id, channel, sender_name,
                              last_message, last_response, intent,
                              "HANDOFF" if intent == "HANDOFF" else "ACTIVO",
                              datetime.now().isoformat()]]},
        ).execute()
    except Exception:
        pass


async def guardar_lead(sender_id, channel, sender_name,
                        business="", city="", pain_point=""):
    """Guarda o actualiza un lead."""
    service = _service()
    if not service:
        return
    from datetime import datetime
    try:
        service.values().append(
            spreadsheetId=GOOGLE_SHEETS_ID,
            range="Leads!A:H",
            valueInputOption="RAW",
            body={"values": [[datetime.now().isoformat(), sender_name,
                              channel, business, city, pain_point,
                              "NUEVO", ""]]},
        ).execute()
    except Exception:
        pass
