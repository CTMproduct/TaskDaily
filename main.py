import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

# ==================== CONFIGURACIÓN ====================
KOMMO_DOMAIN = "jefeoperaciones.kommo.com"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjgzMTA4MzZmNDA0Nzk2ZGEzMWM5YWJlNjQ2Njg4NWQxY2FlOWI1ZGY3N2QxYzViNmMxMTliMTdkZjkxN2NjYzgxNTQ4YmZhZTg4ZWNlYjIxIn0.eyJhdWQiOiJhM2VhZTQzYS1kZjc2LTQxYzAtYTViMS1jN2M5MzdkYjE0MmQiLCJqdGkiOiI4MzEwODM2ZjQwNDc5NmRhMzFjOWFiZTY0NjY4ODVkMWNhZTliNWRmNzdkMWM1YjZjMTE5YjE3ZGY5MTdjY2M4MTU0OGJmYWU4OGVjZWIyMSIsImlhdCI6MTc3NDUzNzcwMywibmJmIjoxNzc0NTM3NzAzLCJleHAiOjE4MDQyMDQ4MDAsInN1YiI6IjEzNTQxMzI3IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjM0ODk5NzM5LCJiYXNlX2RvbWFpbiI6ImtvbW1vLmNvbSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJwdXNoX25vdGlmaWNhdGlvbnMiLCJmaWxlcyIsImNybSIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiZWFiYTQxNGYtNGJjZS00ZjU2LWI0N2MtYWJlMzJkNDUxODM2IiwiYXBpX2RvbWFpbiI6ImFwaS1jLmtvbW1vLmNvbSJ9.Q67YTtyMEplMQYGIRwbCeDAyvV4TBCIdDl69tcOyBKJPpfWpyHEp4ei6lVNxAe6aQAxxHX3MLgckhoU-nzEsg4CmdMdxDvRCkTGTpMLQ8zO6R78PNib3QbP3NrieRyE3Q-0SyZA7Sgjw9UGuyRja91jYXH_1KjC1jGYXIzghgtaTubIpONwI4jzfgtFDvumVAyBkCo65WPAtw2hs5MAywaUwJHjU9moorD9rUU_reeTn7RU5dv4o-DLc2q8ktQ6Oqasr9AiYZGJPOCLs2HS0H8xqnz-pADcJZL16KBfzJdolbvbS4bewK1JU8qegKLRNFGyU7AJSliSW4vv2S90KBg"

FILTERS = {
    "pipeline_id": 11602219,
    "statuses": [89108039, 89108083, 89108087, 89108091, 89108095, 99452571]
}

SMTP_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email": "grupoiactm@gmail.com",
    "password": "vtsfkoildcayfwqf"
}

ASESOR_EMAILS = {
    "Sonia Hernandez": "gerenciacomercial@ctmenlinea.com.co",
    "Paula Orjuela": "asesor2@ctmenlinea.com.co",
    "Paola Cabrejo": "Jefe.operaciones@ctmenlinea.com.co",
    "Andres Rodriguez": "producto@ctmenlinea.com.co",
    "Gloria Caicedo": "Asesor2@ctmenlinea.com.co",
    "Mabel Hernandez": "gerencia@ctmenlinea.com.co",
    "No asignado": "keyaccountmanager@ctmenlinea.com.co",


}

COLOMBIA_TZ = pytz.timezone("America/Bogota")

# ==================== FUNCIONES ====================

def get_leads_pendientes():
    """Obtiene leads con tareas para HOY"""
    url = f"https://{KOMMO_DOMAIN}/api/v4/leads"
    
    status_filters = []
    for status in FILTERS["statuses"]:
        status_filters.append(f"filter[statuses][][pipeline_id]={FILTERS['pipeline_id']}")
        status_filters.append(f"filter[statuses][][status_id]={status}")
    
    now = datetime.now(COLOMBIA_TZ)
    today_start = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    today_end = int(now.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())
    
    query_params = (
        f"?limit=250"
        f"&filter[pipeline_id][]={FILTERS['pipeline_id']}"
        + "".join([f"&{s}" for s in status_filters])
        + f"&filter[closest_task_at][from]={today_start}"
        + f"&filter[closest_task_at][to]={today_end}"
        + "&with=contacts"
    )
    
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Accept": "application/json"}
    
    all_leads = []
    page = 1
    
    while True:
        response = requests.get(f"{url}{query_params}&page={page}", headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        leads = data.get("_embedded", {}).get("leads", [])
        if not leads:
            break
        all_leads.extend(leads)
        page += 1
    
    return all_leads

def get_tareas_caducadas_por_lead():
    """Obtiene todas las tareas caducadas NO completadas"""
    url = f"https://{KOMMO_DOMAIN}/api/v4/tasks"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Accept": "application/json"}
    
    ahora = datetime.now(COLOMBIA_TZ)
    timestamp_actual = int(ahora.timestamp())
    
    tareas_por_lead = defaultdict(list)
    page = 1
    
    while True:
        params = {
            "filter[is_completed]": 0,
            "filter[complete_till][to]": timestamp_actual,
            "filter[entity_type]": "leads",
            "limit": 250,
            "page": page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                break
            
            data = response.json()
            tasks = data.get("_embedded", {}).get("tasks", [])
            
            if not tasks:
                break
            
            for task in tasks:
                lead_id = task.get("entity_id")
                task_text = task.get("text", "").strip()
                complete_till = task.get("complete_till")
                
                if not lead_id:
                    continue
                
                if task_text and complete_till and complete_till < timestamp_actual:
                    tareas_por_lead[lead_id].append({
                        "text": task_text,
                        "complete_till": complete_till,
                        "id": task.get("id")
                    })
            
            if len(tasks) < 250:
                break
            page += 1
            
        except Exception as e:
            break
    
    return dict(tareas_por_lead)

def get_lead_completo(lead_id):
    url = f"https://{KOMMO_DOMAIN}/api/v4/leads/{lead_id}?with=contacts"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_contacto(contact_id):
    url = f"https://{KOMMO_DOMAIN}/api/v4/contacts/{contact_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_custom_field_by_id(data, field_id):
    """Extrae un campo personalizado por su ID, manejando None"""
    if not data or not isinstance(data, dict):
        return ""
    custom_fields = data.get("custom_fields_values", [])
    if not custom_fields:
        return ""
    for field in custom_fields:
        if field.get("field_id") == field_id:
            values = field.get("values", [])
            if values:
                return values[0].get("value", "")
    return ""

def get_asesor_from_lead(lead):
    """Obtiene el asesor directamente del lead (field_id 801410)"""
    if not lead or not isinstance(lead, dict):
        return ""
    return get_custom_field_by_id(lead, 801410)

def get_asesor_from_contact(contact):
    """Obtiene el asesor del contacto (field_id 801430)"""
    if not contact or not isinstance(contact, dict):
        return ""
    return get_custom_field_by_id(contact, 801430)

def get_asesor_final(lead, contact):
    """
    Obtiene el asesor priorizando:
    1. Contacto (field_id 801430)
    2. Lead (field_id 801410)
    3. "No asignado"
    Retorna (asesor, tiene_contacto_valido, tiene_asesor_en_contacto)
    """
    tiene_contacto_valido = False
    tiene_asesor_en_contacto = False
    asesor = "No asignado"
    
    # Verificar si tiene contacto válido
    if contact and isinstance(contact, dict):
        tiene_contacto_valido = True
        asesor_contacto = get_asesor_from_contact(contact)
        if asesor_contacto:
            tiene_asesor_en_contacto = True
            asesor = asesor_contacto
            return asesor, tiene_contacto_valido, tiene_asesor_en_contacto
    
    # Si no tiene asesor en contacto, intentar desde lead
    if lead:
        asesor_lead = get_asesor_from_lead(lead)
        if asesor_lead:
            asesor = asesor_lead
    
    return asesor, tiene_contacto_valido, tiene_asesor_en_contacto

def convert_timestamp_to_datetime(timestamp):
    if not timestamp:
        return ""
    try:
        if isinstance(timestamp, str) and timestamp.isdigit():
            timestamp = int(timestamp)
        fecha = datetime.fromtimestamp(timestamp, COLOMBIA_TZ)
        return fecha.strftime("%d/%m/%Y %H:%M")
    except:
        return str(timestamp)

def get_lead_additional_data(lead):
    if not lead:
        return {}
    datos = {}
    destino = get_custom_field_by_id(lead, 463682)
    if destino:
        datos["destino"] = destino
    fecha_inicio = get_custom_field_by_id(lead, 463686)
    if fecha_inicio:
        try:
            if isinstance(fecha_inicio, str) and fecha_inicio.isdigit():
                fecha = datetime.fromtimestamp(int(fecha_inicio), COLOMBIA_TZ)
                datos["fecha_inicio"] = fecha.strftime("%d/%m/%Y")
            else:
                datos["fecha_inicio"] = fecha_inicio
        except:
            datos["fecha_inicio"] = fecha_inicio
    fecha_salida = get_custom_field_by_id(lead, 801398)
    if fecha_salida:
        try:
            if isinstance(fecha_salida, str) and fecha_salida.isdigit():
                fecha = datetime.fromtimestamp(int(fecha_salida), COLOMBIA_TZ)
                datos["fecha_salida"] = fecha.strftime("%d/%m/%Y")
            else:
                datos["fecha_salida"] = fecha_salida
        except:
            datos["fecha_salida"] = fecha_salida
    return datos

def send_email(to_email, subject, body_html):
    msg = MIMEMultipart()
    msg["From"] = SMTP_CONFIG["email"]
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html"))
    
    try:
        with smtplib.SMTP(SMTP_CONFIG["smtp_server"], SMTP_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(SMTP_CONFIG["email"], SMTP_CONFIG["password"])
            server.send_message(msg)
        print(f"✅ Correo enviado a: {to_email}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_asesor_email(asesor_nombre):
    return ASESOR_EMAILS.get(asesor_nombre, ASESOR_EMAILS["No asignado"])

def generate_email_html(asesor, leads_pendientes, leads_caducados, leads_sin_contacto, fecha_hoy):
    fecha_formateada = fecha_hoy.strftime("%d/%m/%Y")
    hora_actual = fecha_hoy.strftime("%H:%M")
    
    # Función para generar el HTML de las filas de pendientes
    def generar_filas_pendientes():
        html = ""
        for i, lead in enumerate(leads_pendientes, 1):
            datos_extra = lead.get("datos_extra", {})
            fecha_tarea = convert_timestamp_to_datetime(lead.get("closest_task_at"))
            
            html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">{i}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                    <div style="font-weight: 600; color: #333;">{lead['name']}</div>
                    <div style="font-size: 11px; color: #999;">ID: {lead['id']}</div>
                    {f'<div style="font-size: 11px; color: #666; margin-top: 5px;">📍 {datos_extra.get("destino", "")}</div>' if datos_extra.get("destino") else ''}
                    <div style="font-size: 10px; color: #888; margin-top: 3px;">
                        {f'📅 Inicio: {datos_extra.get("fecha_inicio")}' if datos_extra.get("fecha_inicio") else ''}
                        {f' ✈️ Salida: {datos_extra.get("fecha_salida")}' if datos_extra.get("fecha_salida") else ''}
                    </div>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                    <span style="background-color: #E3F2FD; color: #1976D2; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;">
                        ⏰ Vence: {fecha_tarea}
                    </span>
                </td>
            </tr>
            """
        return html
    
    # Función para generar el HTML de las filas de caducadas
    def generar_filas_caducadas():
        html = ""
        for i, lead in enumerate(leads_caducados, 1):
            datos_extra = lead.get("datos_extra", {})
            
            tareas_html = ""
            for task in lead.get("tareas_caducadas", []):
                fecha_venc = convert_timestamp_to_datetime(task.get("complete_till"))
                tareas_html += f"""
                <div style="margin-bottom: 8px; padding: 6px; background-color: #fff5f5; border-radius: 4px;">
                    <div style="color: #c62828; font-size: 12px;">⚠️ {task['text']}</div>
                    <div style="color: #999; font-size: 10px;">Vencida: {fecha_venc}</div>
                </div>
                """
            
            html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">{i}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                    <div style="font-weight: 600; color: #333;">{lead['name']}</div>
                    <div style="font-size: 11px; color: #999;">ID: {lead['id']}</div>
                    {f'<div style="font-size: 11px; color: #666; margin-top: 5px;">📍 {datos_extra.get("destino", "")}</div>' if datos_extra.get("destino") else ''}
                    <div style="font-size: 10px; color: #888; margin-top: 3px;">
                        {f'📅 Inicio: {datos_extra.get("fecha_inicio")}' if datos_extra.get("fecha_inicio") else ''}
                        {f' ✈️ Salida: {datos_extra.get("fecha_salida")}' if datos_extra.get("fecha_salida") else ''}
                    </div>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{tareas_html}</td>
            </tr>
            """
        return html
    
    # Función para generar el HTML de las filas de sin contacto
    def generar_filas_sin_contacto():
        html = ""
        for i, lead in enumerate(leads_sin_contacto, 1):
            datos_extra = lead.get("datos_extra", {})
            motivo = lead.get("motivo", "")
            
            # Tareas combinadas (pendientes y caducadas)
            tareas_combinadas = []
            for task in lead.get("tareas_pendientes", []):
                fecha = convert_timestamp_to_datetime(task.get("complete_till"))
                tareas_combinadas.append(f'📌 {task["text"]} (Vence: {fecha})')
            for task in lead.get("tareas_caducadas", []):
                fecha = convert_timestamp_to_datetime(task.get("complete_till"))
                tareas_combinadas.append(f'⚠️ {task["text"]} (Vencida: {fecha})')
            
            tareas_html = ""
            for tarea in tareas_combinadas[:5]:  # Mostrar máximo 5 tareas
                tareas_html += f'<div style="font-size: 11px; margin-bottom: 4px;">{tarea}</div>'
            if len(tareas_combinadas) > 5:
                tareas_html += f'<div style="font-size: 10px; color: #999;">... y {len(tareas_combinadas) - 5} más</div>'
            
            # Color según el motivo
            bg_color = "#fff3e0" if "contacto" in motivo else "#fff8e1"
            border_color = "#ff9800" if "contacto" in motivo else "#ffc107"
            icono = "🔗" if "contacto" in motivo else "⚠️"
            
            html += f"""
            <tr style="background-color: {bg_color}; border-left: 3px solid {border_color};">
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0; text-align: center;">{i}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                    <div style="font-weight: 600; color: #333;">{lead['name']}</div>
                    <div style="font-size: 11px; color: #999;">ID: {lead['id']}</div>
                    <div style="font-size: 11px; color: #e65100; margin-top: 5px;">
                        {icono} {motivo}
                    </div>
                    {f'<div style="font-size: 11px; color: #666; margin-top: 5px;">📍 {datos_extra.get("destino", "")}</div>' if datos_extra.get("destino") else ''}
                    <div style="font-size: 10px; color: #888; margin-top: 3px;">
                        {f'📅 Inicio: {datos_extra.get("fecha_inicio")}' if datos_extra.get("fecha_inicio") else ''}
                        {f' ✈️ Salida: {datos_extra.get("fecha_salida")}' if datos_extra.get("fecha_salida") else ''}
                    </div>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">{tareas_html if tareas_html else '<span style="color: #999;">Sin tareas pendientes/caducadas</span>'}</td>
            </tr>
            """
        return html
    
    total_pendientes = len(leads_pendientes)
    total_caducados = len(leads_caducados)
    total_sin_contacto = len(leads_sin_contacto)
    total_tareas_caducadas = sum(len(l.get("tareas_caducadas", [])) for l in leads_caducados)
    
    # Sección de pendientes
    seccion_pendientes = ""
    if total_pendientes > 0:
        seccion_pendientes = f"""
        <div style="margin-bottom: 30px;">
            <h3 style="color: #1976D2; margin: 0 0 15px 0; padding-bottom: 8px; border-bottom: 2px solid #1976D2;">
                📌 Tareas Pendientes para Hoy ({total_pendientes})
            </h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #E3F2FD;">
                        <th style="padding: 12px; text-align: center; font-weight: 600; color: #1565C0;">#</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #1565C0;">Lead / Información</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #1565C0;">Tarea</th>
                    </tr>
                </thead>
                <tbody>
                    {generar_filas_pendientes()}
                </tbody>
            </table>
        </div>
        """
    
    # Sección de caducadas
    seccion_caducadas = ""
    if total_caducados > 0:
        seccion_caducadas = f"""
        <div style="margin-bottom: 30px;">
            <h3 style="color: #c62828; margin: 0 0 15px 0; padding-bottom: 8px; border-bottom: 2px solid #c62828;">
                ⚠️ Tareas Caducadas ({total_caducados} leads - {total_tareas_caducadas} tareas)
            </h3>
            <div style="background-color: #FFEBEE; padding: 12px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #c62828;">
                <div style="color: #c62828; font-weight: 500;">⚠️ Atención Prioritaria</div>
                <div style="color: #666; font-size: 12px;">Estas tareas están vencidas y requieren acción inmediata.</div>
            </div>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #FFCDD2;">
                        <th style="padding: 12px; text-align: center; font-weight: 600; color: #c62828;">#</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #c62828;">Lead / Información</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #c62828;">Tareas Vencidas</th>
                    </tr>
                </thead>
                <tbody>
                    {generar_filas_caducadas()}
                </tbody>
            </table>
        </div>
        """
    
    # Sección de sin contacto o sin asesor en contacto
    seccion_sin_contacto = ""
    if total_sin_contacto > 0:
        seccion_sin_contacto = f"""
        <div style="margin-bottom: 30px;">
            <h3 style="color: #ff9800; margin: 0 0 15px 0; padding-bottom: 8px; border-bottom: 2px solid #ff9800;">
                🔗 Leads sin Contacto o sin Asignación en Contacto ({total_sin_contacto})
            </h3>
            <div style="background-color: #FFF3E0; padding: 12px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #ff9800;">
                <div style="color: #e65100; font-weight: 500;">📌 Importante</div>
                <div style="color: #666; font-size: 12px;">Estos leads no tienen un contacto asociado o el contacto no tiene el campo "Usuario asignado" completado. El asesor mostrado es el asignado directamente en el lead.</div>
            </div>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #FFE0B2;">
                        <th style="padding: 12px; text-align: center; font-weight: 600; color: #e65100;">#</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #e65100;">Lead / Información</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #e65100;">Tareas</th>
                    </tr>
                </thead>
                <tbody>
                    {generar_filas_sin_contacto()}
                </tbody>
            </table>
        </div>
        """
    
    # Si no hay nada
    if not seccion_pendientes and not seccion_caducadas and not seccion_sin_contacto:
        seccion_vacia = """
        <div style="text-align: center; padding: 40px; background-color: #f5f5f5; border-radius: 8px;">
            <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
            <div style="color: #666;">No hay tareas pendientes ni caducadas</div>
            <div style="color: #999; font-size: 12px; margin-top: 5px;">¡Excelente trabajo!</div>
        </div>
        """
    else:
        seccion_vacia = ""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte de Tareas - {fecha_formateada}</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            body {{
                font-family: 'Inter', Arial, sans-serif;
                line-height: 1.5;
                margin: 0;
                padding: 0;
                background-color: #f5f7fa;
            }}
            .container {{
                max-width: 950px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .header p {{
                margin: 8px 0 0;
                opacity: 0.9;
                font-size: 14px;
            }}
            .content {{
                padding: 30px;
            }}
            .saludo {{
                margin-bottom: 25px;
            }}
            .saludo h2 {{
                margin: 0 0 5px;
                color: #333;
                font-size: 20px;
            }}
            .saludo p {{
                margin: 0;
                color: #666;
                font-size: 14px;
            }}
            .resumen {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 30px;
                display: flex;
                justify-content: space-around;
                text-align: center;
                flex-wrap: wrap;
            }}
            .resumen-item {{
                flex: 1;
                min-width: 100px;
            }}
            .resumen-numero {{
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 5px;
            }}
            .resumen-label {{
                font-size: 11px;
                opacity: 0.9;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 11px;
                color: #999;
                border-top: 1px solid #e0e0e0;
            }}
            @media (max-width: 600px) {{
                .resumen-item {{
                    min-width: 80px;
                }}
                .resumen-numero {{
                    font-size: 20px;
                }}
                .content {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Reporte de Tareas</h1>
                <p>{fecha_formateada} • {hora_actual}</p>
            </div>
            
            <div class="content">
                <div class="saludo">
                    <h2>Hola, {asesor}</h2>
                    <p>Este es tu resumen diario de tareas pendientes y vencidas.</p>
                </div>
                
                <div class="resumen">
                    <div class="resumen-item">
                        <div class="resumen-numero">{total_pendientes}</div>
                        <div class="resumen-label">Tareas Pendientes Hoy</div>
                    </div>
                    <div class="resumen-item">
                        <div class="resumen-numero">{total_caducados}</div>
                        <div class="resumen-label">Leads con Tareas Vencidas</div>
                    </div>
                    <div class="resumen-item">
                        <div class="resumen-numero">{total_tareas_caducadas}</div>
                        <div class="resumen-label">Total Tareas Vencidas</div>
                    </div>
                    <div class="resumen-item">
                        <div class="resumen-numero">{total_sin_contacto}</div>
                        <div class="resumen-label">Leads sin Contacto/Asignación</div>
                    </div>
                </div>
                
                {seccion_pendientes}
                {seccion_caducadas}
                {seccion_sin_contacto}
                {seccion_vacia}
            </div>
            
            <div class="footer">
                <p>📌 Las tareas pendientes deben completarse hoy.<br>
                ⚠️ Las tareas vencidas requieren atención prioritaria.<br>
                🔗 Los leads sin contacto necesitan ser vinculados a un contacto y verificar el campo "Usuario asignado".</p>
                <p style="margin-top: 10px;">Este es un correo automático generado por el sistema de gestión de leads.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

# ==================== MAIN ====================

def main():
    print("=" * 60)
    print("=== AUTOMATIZACIÓN DE LEADS ===")
    ahora = datetime.now(COLOMBIA_TZ)
    print(f"Fecha: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Obtener leads con tareas para HOY
    print("\n1. Buscando leads con tareas PENDIENTES...")
    leads_pendientes_raw = get_leads_pendientes()
    print(f"   Encontrados: {len(leads_pendientes_raw)}")
    
    # 2. Obtener todas las tareas caducadas
    print("\n2. Buscando tareas CADUCADAS...")
    tareas_caducadas_por_lead = get_tareas_caducadas_por_lead()
    print(f"   Leads con tareas caducadas: {len(tareas_caducadas_por_lead)}")
    
    # 3. Procesar y agrupar por asesor
    pendientes_por_asesor = defaultdict(list)
    caducados_por_asesor = defaultdict(list)
    sin_contacto_por_asesor = defaultdict(list)
    
    # Procesar leads pendientes
    print("\n3. Procesando leads pendientes...")
    for lead in leads_pendientes_raw:
        try:
            contact = None
            contacts = lead.get("_embedded", {}).get("contacts", [])
            if contacts:
                contact = get_contacto(contacts[0].get("id"))
            
            # Obtener asesor y estado del contacto
            asesor, tiene_contacto, tiene_asesor_contacto = get_asesor_final(lead, contact)
            
            datos_extra = get_lead_additional_data(lead)
            
            lead_info = {
                "id": lead.get("id"),
                "name": lead.get("name", "Sin nombre"),
                "closest_task_at": lead.get("closest_task_at"),
                "datos_extra": datos_extra
            }
            
            # Verificar si tiene problemas de contacto
            if not tiene_contacto:
                motivo = "⚠️ No tiene contacto asociado"
                lead_info["motivo"] = motivo
                sin_contacto_por_asesor[asesor].append(lead_info)
            elif not tiene_asesor_contacto:
                motivo = "🔗 Tiene contacto pero no tiene 'Usuario asignado' en el contacto"
                lead_info["motivo"] = motivo
                sin_contacto_por_asesor[asesor].append(lead_info)
            else:
                pendientes_por_asesor[asesor].append(lead_info)
            
            print(f"   📌 {lead.get('name', 'Sin nombre')[:35]} -> {asesor}" + (" (sin contacto)" if not tiene_contacto else " (sin asesor en contacto)" if not tiene_asesor_contacto else ""))
        except Exception as e:
            print(f"   ❌ Error procesando lead pendiente: {e}")
            continue
    
    # Procesar leads caducados
    print("\n4. Procesando leads caducados...")
    for lead_id, tareas in tareas_caducadas_por_lead.items():
        try:
            lead = get_lead_completo(lead_id)
            if not lead:
                print(f"   ⚠️ Lead {lead_id} no encontrado")
                continue

            if lead.get("pipeline_id") != FILTERS["pipeline_id"]:
                continue

            contact = None
            contacts = lead.get("_embedded", {}).get("contacts", [])
            if contacts:
                contact = get_contacto(contacts[0].get("id"))
            
            # Obtener asesor y estado del contacto
            asesor, tiene_contacto, tiene_asesor_contacto = get_asesor_final(lead, contact)
            datos_extra = get_lead_additional_data(lead)
            
            lead_info = {
                "id": lead_id,
                "name": lead.get("name", "Sin nombre"),
                "tareas_caducadas": tareas,
                "datos_extra": datos_extra
            }
            
            # Verificar si tiene problemas de contacto
            if not tiene_contacto:
                motivo = "⚠️ No tiene contacto asociado"
                lead_info["motivo"] = motivo
                sin_contacto_por_asesor[asesor].append(lead_info)
            elif not tiene_asesor_contacto:
                motivo = "🔗 Tiene contacto pero no tiene 'Usuario asignado' en el contacto"
                lead_info["motivo"] = motivo
                sin_contacto_por_asesor[asesor].append(lead_info)
            else:
                caducados_por_asesor[asesor].append(lead_info)
            
            print(f"   ⚠️ {lead.get('name', 'Sin nombre')[:35]} -> {asesor} ({len(tareas)} tareas)" + (" (sin contacto)" if not tiene_contacto else " (sin asesor en contacto)" if not tiene_asesor_contacto else ""))
        except Exception as e:
            print(f"   ❌ Error procesando lead caducado {lead_id}: {e}")
            continue
    
    # 5. Enviar correos
    todos_asesores = set(pendientes_por_asesor.keys()) | set(caducados_por_asesor.keys()) | set(sin_contacto_por_asesor.keys())
    
    print(f"\n5. Enviando correos a {len(todos_asesores)} asesores...")
    
    for asesor in todos_asesores:
        try:
            pendientes = pendientes_por_asesor.get(asesor, [])
            caducados = caducados_por_asesor.get(asesor, [])
            sin_contacto = sin_contacto_por_asesor.get(asesor, [])
            
            if not pendientes and not caducados and not sin_contacto:
                continue
            
            email = get_asesor_email(asesor)
            subject = f"📋 Reporte de Tareas - {ahora.strftime('%d/%m/%Y')} - {asesor}"
            
            total_caducadas = sum(len(l.get("tareas_caducadas", [])) for l in caducados)
            
            print(f"\n   📧 {asesor} -> {email}")
            print(f"      Pendientes: {len(pendientes)} leads")
            print(f"      Caducados: {len(caducados)} leads ({total_caducadas} tareas)")
            print(f"      Sin contacto/asignación: {len(sin_contacto)} leads")
            
            body = generate_email_html(asesor, pendientes, caducados, sin_contacto, ahora)
            send_email(email, subject, body)
        except Exception as e:
            print(f"   ❌ Error enviando correo a {asesor}: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("✅ COMPLETADO")

if __name__ == "__main__":
    main()