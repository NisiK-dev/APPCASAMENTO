import os
from twilio.rest import Client

# Configuração do Twilio
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def send_whatsapp_message(to_phone_number: str, message: str) -> dict:
    """
    Envia mensagem via WhatsApp usando Twilio
    
    Args:
        to_phone_number: Número de telefone no formato +5511999999999
        message: Mensagem a ser enviada
        
    Returns:
        dict: Resultado da operação com status e informações
    """
    try:
        # Verifica se as credenciais do Twilio estão configuradas
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
            return {
                'success': False,
                'error': 'Credenciais do Twilio não configuradas. Verifique TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN e TWILIO_PHONE_NUMBER.'
            }
        
        # Inicializa o cliente Twilio
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Formata o número de telefone para WhatsApp
        whatsapp_number = f"whatsapp:{to_phone_number}"
        twilio_whatsapp_number = f"whatsapp:{TWILIO_PHONE_NUMBER}"
        
        # Envia a mensagem
        message_instance = client.messages.create(
            body=message,
            from_=twilio_whatsapp_number,
            to=whatsapp_number
        )
        
        return {
            'success': True,
            'message_sid': message_instance.sid,
            'status': message_instance.status,
            'to': to_phone_number
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def send_bulk_whatsapp_messages(phone_numbers: list, message: str) -> dict:
    """
    Envia mensagens em lote via WhatsApp
    
    Args:
        phone_numbers: Lista de números de telefone
        message: Mensagem a ser enviada
        
    Returns:
        dict: Resultado da operação com estatísticas
    """
    results = {
        'total': len(phone_numbers),
        'successful': 0,
        'failed': 0,
        'results': []
    }
    
    for phone in phone_numbers:
        result = send_whatsapp_message(phone, message)
        results['results'].append({
            'phone': phone,
            'success': result['success'],
            'error': result.get('error', None)
        })
        
        if result['success']:
            results['successful'] += 1
        else:
            results['failed'] += 1
    
    return results

# Mensagens predefinidas para casamentos
WEDDING_MESSAGES = {
    'confirmation_reminder': """
🤍 Olá! Este é um lembrete gentil sobre nosso casamento.

📅 Data: {date}
⏰ Horário: {time}
📍 Local: {venue}

Por favor, confirme sua presença através do link: {rsvp_link}

Aguardamos você! 💕
""",
    
    'thank_you': """
🤍 Muito obrigado(a) por confirmar sua presença em nosso casamento!

📅 Data: {date}
⏰ Horário: {time}
📍 Local: {venue}

Estamos ansiosos para celebrar este momento especial com você! 💕
""",
    
    'venue_update': """
🤍 Informações importantes sobre nosso casamento:

📅 Data: {date}
⏰ Horário: {time}
📍 Local: {venue}
🗺️ Endereço: {address}

Não esqueça de confirmar sua presença! 💕
""",
    
    'gift_registry': """
🤍 Nosso casamento está chegando!

🎁 Criamos uma lista de presentes para facilitar. Confira em: {gift_link}

📅 Data: {date}
⏰ Horário: {time}

Sua presença já é nosso maior presente! 💕
"""
}

def get_wedding_message(message_type: str, **kwargs) -> str:
    """
    Retorna uma mensagem pré-formatada para casamentos
    
    Args:
        message_type: Tipo da mensagem (confirmation_reminder, thank_you, etc.)
        **kwargs: Variáveis para formatação da mensagem
        
    Returns:
        str: Mensagem formatada
    """
    template = WEDDING_MESSAGES.get(message_type, "")
    if template:
        return template.format(**kwargs)
    return ""