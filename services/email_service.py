# myapp/services/email_service.py

import resend
import logging
from decouple import config
from django.conf import settings


# import from env vars
resend.api_key = config('RESEND_API_KEY')
logger = logging.getLogger(__name__)


def send_member_request_email(parent, person, request_type: str):
    if request_type == "verify":
        subject = f"Pedido de Validação — {person.first_name} {person.last_name}"
        body = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto;">
            <h2>Pedido de Validação de Membro</h2>
            <p>O Membro <strong>{person.first_name} {person.last_name}</strong> 
            do Clube <strong>{person.club.username}</strong> está à espera de validação.</p>
            <p>Aceda à sua conta para rever e responder ao pedido.</p>
        </div>
        """
    elif request_type == "exams":
        subject = f"Proposta de Exame — {person.first_name} {person.last_name}"
        body = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto;">
            <h2>Proposta de Exame</h2>
            <p>O Clube <strong>{person.club.username}</strong> enviou uma proposta de exame 
            para o Membro <strong>{person.first_name} {person.last_name}</strong>.</p>
            <p>Aceda à sua conta para rever e responder ao pedido.</p>
        </div>
        """
    else:
        logger.warning(f"send_member_request_email: unknown request_type '{request_type}'")
        return

    resend.Emails.send({
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [parent.email],
        "subject": subject,
        "html": body,
    })