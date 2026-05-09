"""Motor del bot: orquesta la conversación entre el mensaje entrante y la respuesta."""

from database import guardar_mensaje, formatear_historial, upsert_lead
from groq_client import preguntar
from meta_client import enviar_whatsapp, enviar_instagram, enviar_messenger, notificar_ceo
from sheets_crm import guardar_conversacion, guardar_lead
from config import BOT_NAME


async def procesar_mensaje(channel: str, sender_id: str,
                           sender_name: str, message_text: str) -> dict:
    """
    Pipeline completo:
    1. Obtener historial → 2. Preguntar a Groq → 3. Guardar en DB
    4. Enviar respuesta → 5. Notificar CEO si handoff
    """
    if not message_text.strip():
        return {"status": "ignored", "reason": "mensaje vacío"}

    # 1. Historial
    historial = formatear_historial(sender_id)

    # 2. Groq
    resultado = await preguntar(message_text, historial)
    respuesta = resultado["response"]
    intent = resultado["intent"]

    # 3. Guardar en SQLite
    guardar_mensaje(sender_id, channel, sender_name, message_text, respuesta, intent)

    # 4. Guardar en Google Sheets (si está configurado)
    try:
        await guardar_conversacion(sender_id, channel, sender_name,
                                   message_text, respuesta, intent)
        await guardar_lead(sender_id, channel, sender_name)
    except Exception:
        pass

    # 5. Actualizar lead si tenemos datos de negocio/ciudad
    upsert_lead(sender_id, channel, sender_name)

    # 6. Enviar respuesta según canal
    enviado = False
    if channel == "whatsapp":
        enviado = await enviar_whatsapp(sender_id, respuesta)
    elif channel == "instagram":
        enviado = await enviar_instagram(sender_id, respuesta)
    elif channel in ("facebook", "messenger"):
        enviado = await enviar_messenger(sender_id, respuesta)

    # 7. Notificar CEO si handoff
    if intent == "HANDOFF":
        await notificar_ceo(sender_name, channel, message_text)

    return {
        "status": "ok",
        "intent": intent,
        "response": respuesta,
        "sent": enviado,
    }
