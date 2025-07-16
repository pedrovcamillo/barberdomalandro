import os
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def enviar_whatsapp(mensagem, numero_destino):
    """
    Envia uma mensagem via WhatsApp usando Twilio.
    Exemplo de número: 'whatsapp:+5511987654321'
    """
    try:
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=mensagem,
            to=numero_destino
        )
        return message.sid
    except Exception as e:
        print("Erro ao enviar WhatsApp:", e)
        return None
