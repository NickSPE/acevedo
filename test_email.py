"""
Script para probar el envío de emails
"""
import os
import sys
import django

# Configurar Django
sys.path.append('c:\\Users\\ZUZUKA\\AppIngRequisitos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FinGest.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    try:
        print("🔍 Testing email configuration...")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        result = send_mail(
            subject='Test Email - FinGest',
            message='Este es un email de prueba desde FinGest.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Enviar a nosotros mismos
            fail_silently=False,
        )
        
        print(f"✅ Email enviado exitosamente. Resultado: {result}")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"❌ Tipo: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email()
