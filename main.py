import requests
import json
import os
import csv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from dotenv import load_dotenv
import time

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de la aplicación
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_uri = os.getenv('REDIRECT_URI')
authorization_code = os.getenv('AUTHORIZATION_CODE')
token_file = 'tokens.json'

# Función para guardar tokens en un archivo
def save_tokens(access_token, refresh_token):
    tokens = {
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    with open(token_file, 'w') as file:
        json.dump(tokens, file)

# Función para cargar tokens desde un archivo
def load_tokens():
    if os.path.exists(token_file):
        with open(token_file, 'r') as file:
            return json.load(file)
    return None

# Función para obtener un nuevo token usando el código de autorización
def get_new_tokens(authorization_code):
    token_url = 'https://id.twitch.tv/oauth2/token'
    response = requests.post(token_url, {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': authorization_code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri
    })

    if response.status_code == 200:
        tokens = response.json()
        save_tokens(tokens['access_token'], tokens['refresh_token'])
        return tokens['access_token']
    else:
        print("Error al obtener el token de acceso:", response.json())
        return None

# Función para renovar el token de acceso usando el refresh token
def refresh_access_token(refresh_token):
    token_url = 'https://id.twitch.tv/oauth2/token'
    response = requests.post(token_url, {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    })

    if response.status_code == 200:
        new_tokens = response.json()
        save_tokens(new_tokens['access_token'], new_tokens['refresh_token'])
        return new_tokens['access_token']
    else:
        print("Error al renovar el token de acceso:", response.json())
        return None

# Función para obtener el token de acceso, renovándolo si es necesario
def get_access_token():
    tokens = load_tokens()
    if tokens:
        return refresh_access_token(tokens['refresh_token'])
    else:
        return get_new_tokens(authorization_code)

# Obtener el token de acceso
access_token = get_access_token()

if access_token:
    print(f'Access Token: {access_token}')

    # Configurar los encabezados de la solicitud con el token de acceso
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }

    # Obtener el ID de usuario basado en tu nombre de usuario
    twitch_username = 'patriciofernandezia'
    url = f'https://api.twitch.tv/helix/users?login={twitch_username}'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user_info = response.json()
        user_id = user_info['data'][0]['id']  # Aquí obtienes tu ID de usuario
        print(f'User ID: {user_id}')

        # Ahora que tienes el ID de usuario, solicita la lista de suscriptores
        url = f'https://api.twitch.tv/helix/subscriptions?broadcaster_id={user_id}'
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            # Imprimir la lista de suscriptores
            data = response.json()['data']
            print("Lista de suscriptores:", data)

            # Guardar los datos en un archivo CSV (opcional)
            csv_filename = 'suscriptores.csv'
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Escribir los encabezados
                writer.writerow(['User ID', 'User Name', 'User Login', 'Plan Name', 'Tier', 'Is Gift', 'Gifter Name'])

                # Escribir los datos de los suscriptores
                for subscriber in data:
                    writer.writerow([
                        subscriber['user_id'],
                        subscriber['user_name'],
                        subscriber['user_login'],
                        subscriber['plan_name'],
                        subscriber['tier'],
                        subscriber['is_gift'],
                        subscriber.get('gifter_name', '')
                    ])

            print(f"La lista de suscriptores se ha guardado en '{csv_filename}'.")

            # Leer la plantilla HTML desde un archivo externo
            template_html_filename = 'template.html'  # Asegúrate de que este archivo esté en el mismo directorio que este script

            with open(template_html_filename, 'r', encoding='utf-8') as file:
                html_template = file.read()

            # Generar el contenido de las filas de la tabla
            for subscriber in data:
                # Contar cuántas veces el nombre del suscriptor aparece como gifter_name
                gift_count = sum(1 for other_subscriber in data if other_subscriber.get('gifter_name') == subscriber['user_name'])
                # Añadir el campo 'gift_count' al suscriptor actual
                subscriber['gift_count'] = gift_count

            # Ordenar los suscriptores por 'gift_count' de mayor a menor
            sorted_data = sorted(data, key=lambda x: x['gift_count'], reverse=True)

            # Asignar medallas usando iconos de Iconify
            if sorted_data:
                sorted_data[0]['medal'] = '<span class="iconify" data-icon="emojione:1st-place-medal" style="color: #ffd700;"></span>'  # Medalla de oro
                for i in range(1, len(sorted_data)):
                    if sorted_data[i]['gift_count'] > 0:
                        sorted_data[i]['medal'] = '<span class="iconify" data-icon="emojione:2nd-place-medal" style="color: #c0c0c0;"></span>'  # Medalla de plata
                    else:
                        sorted_data[i]['medal'] = '<span class="iconify" data-icon="emojione:3rd-place-medal" style="color: #cd7f32;"></span>'  # Medalla de bronce

            # Generar las filas HTML con la medalla como primera columna
            rows_html = "\n".join([
                f"<tr>"
                f"<td class='py-3 px-6 text-left'>{subscriber['medal']}</td>"
                f"<td class='py-3 px-6 text-left'>{subscriber['user_name']}</td>"
                f"<td class='py-3 px-6 text-left'>{subscriber['tier']}</td>"
                f"<td class='py-3 px-6 text-left'>{subscriber['gift_count']}</td>"
                f"</tr>"
                for subscriber in sorted_data
            ])

            # Reemplazar el placeholder en la plantilla HTML con las filas generadas
            html_content = html_template.replace("<!-- PLACEHOLDER -->", rows_html)

            # Guardar el contenido en un archivo HTML
            output_html_filename = 'index_con_placeholder.html'

            with open(output_html_filename, 'w', encoding='utf-8') as file:
                file.write(html_content)

            print(f"Archivo HTML generado: {output_html_filename}")

            # Configurar Selenium para abrir el archivo HTML y hacer una captura de pantalla usando Firefox
            firefox_options = Options()
            firefox_options.headless = True  # Ejecuta el navegador en modo headless (sin interfaz gráfica)

            # Iniciar el navegador Firefox
            driver = webdriver.Firefox(options=firefox_options)

            # Obtener la ruta absoluta del archivo HTML
            html_file_path = os.path.abspath(output_html_filename)

            # Abrir el archivo HTML generado
            driver.get(f'file:///{html_file_path}')

            # Esperar un momento para asegurarse de que la página se haya cargado completamente
            time.sleep(5)  # Aumentar el tiempo de espera si es necesario

            # Tomar una captura de pantalla
            screenshot_filename = 'screenshot.png'
            driver.save_screenshot(screenshot_filename)

            print(f"Captura de pantalla guardada como: {screenshot_filename}")

            # Cerrar el navegador
            driver.quit()

        else:
            print("Error al obtener la lista de suscriptores:", response.json())
    else:
        print("Error al obtener el ID de usuario:", response.json())
