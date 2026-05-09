"""Envío de mensajes a través de las APIs de Meta (WhatsApp / Instagram / Facebook)."""

import httpx
from config import (
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_ACCESS_TOKEN,
    INSTAGRAM_PAGE_ACCESS_TOKEN,
    FACEBOOK_PAGE_ACCESS_TOKEN,
    CEO_WHATSAPP_NUMBER,
    AGENCY_NAME,
    BOT_NAME,
)

API_VERSION = "v22.0"
GRAPH_URL = f"https://graph.facebook.com/{API_VERSION}"


async def enviar_whatsapp(to: str, texto: str) -> bool:
    """Envía un mensaje de texto por WhatsApp."""
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        return False
    url = f"{GRAPH_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"body": texto},
            },
        )
    return resp.is_success


async def notificar_ceo(sender_name: str, channel: str, ultimo_mensaje: str):
    """Envía alerta al CEO cuando hay un handoff."""
    if not CEO_WHATSAPP_NUMBER:
        return False
    texto = (
        f"🔔 *LEAD CALIENTE - {AGENCY_NAME}* 🦁\n\n"
        f"👤 *Nombre:* {sender_name}\n"
        f"📱 *Canal:* {channel}\n"
        f"💬 *Dijo:* \"{ultimo_mensaje[:200]}\"\n\n"
        f"✅ El lead está listo para hablar con el CEO."
    )
    return await enviar_whatsapp(CEO_WHATSAPP_NUMBER, texto)


async def enviar_instagram(ig_id: str, texto: str) -> bool:
    """Envía respuesta a un mensaje de Instagram."""
    if not INSTAGRAM_PAGE_ACCESS_TOKEN:
        return False
    url = f"{GRAPH_URL}/{ig_id}/messages"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            params={"access_token": INSTAGRAM_PAGE_ACCESS_TOKEN},
            json={"recipient": {"id": ig_id}, "message": {"text": texto}},
        )
    return resp.is_success


async def enviar_messenger(psid: str, texto: str) -> bool:
    """Envía respuesta por Facebook Messenger."""
    if not FACEBOOK_PAGE_ACCESS_TOKEN:
        return False
    url = f"{GRAPH_URL}/me/messages"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN},
            json={
                "recipient": {"id": psid},
                "message": {"text": texto},
            },
        )
    return resp.is_success
