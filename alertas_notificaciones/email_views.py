from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import os
import glob
from django.conf import settings

@login_required
def ver_emails_enviados(request):
    """Vista para visualizar los emails enviados en formato web"""
    emails_path = getattr(settings, 'EMAIL_FILE_PATH', None)
    emails = []
    
    if emails_path and os.path.exists(emails_path):
        # Buscar todos los archivos de email
        email_files = glob.glob(os.path.join(emails_path, '*.log'))
        email_files.sort(reverse=True)  # Más recientes primero
        
        for file_path in email_files[:10]:  # Últimos 10 emails
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extraer información básica del email
                lines = content.split('\n')
                subject = ''
                to_email = ''
                date = ''
                html_content = ''
                
                for line in lines:
                    if line.startswith('Subject:'):
                        subject = line.replace('Subject:', '').strip()
                    elif line.startswith('To:'):
                        to_email = line.replace('To:', '').strip()
                    elif line.startswith('Date:'):
                        date = line.replace('Date:', '').strip()
                
                # Extraer contenido HTML
                if 'Content-Type: text/html' in content:
                    html_start = content.find('<!DOCTYPE html>')
                    if html_start > -1:
                        html_end = content.find('--===============', html_start)
                        if html_end > -1:
                            html_content = content[html_start:html_end].strip()
                
                emails.append({
                    'file': os.path.basename(file_path),
                    'subject': subject,
                    'to': to_email,
                    'date': date,
                    'html_content': html_content
                })
                
            except Exception as e:
                continue
    
    context = {
        'emails': emails,
        'total_emails': len(emails)
    }
    
    return render(request, 'alertas_notificaciones/ver_emails.html', context)


@login_required
def ver_email_completo(request, filename):
    """Vista para ver un email específico en formato HTML"""
    emails_path = getattr(settings, 'EMAIL_FILE_PATH', None)
    
    if not emails_path or not filename:
        return HttpResponse("Email no encontrado", status=404)
    
    file_path = os.path.join(emails_path, filename)
    
    if not os.path.exists(file_path):
        return HttpResponse("Archivo de email no encontrado", status=404)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer solo el contenido HTML
        if 'Content-Type: text/html' in content:
            html_start = content.find('<!DOCTYPE html>')
            if html_start > -1:
                html_end = content.find('--===============', html_start)
                if html_end > -1:
                    html_content = content[html_start:html_end].strip()
                    return HttpResponse(html_content, content_type='text/html')
        
        # Si no hay HTML, mostrar contenido texto
        return HttpResponse(f"<pre>{content}</pre>", content_type='text/html')
        
    except Exception as e:
        return HttpResponse(f"Error leyendo email: {str(e)}", status=500)
