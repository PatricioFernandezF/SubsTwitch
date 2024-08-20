import requests
import json
import os
import csv
import random
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium import webdriver
from dotenv import load_dotenv
import time

# Cargar las variables de entorno desde el archivo .env
def load_env():
    load_dotenv()

# Configuración de la aplicación
def get_config():
    return {
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'redirect_uri': os.getenv('REDIRECT_URI'),
        'authorization_code': os.getenv('AUTHORIZATION_CODE'),
        'token_file': 'tokens.json'
    }

# Función para guardar tokens en un archivo
def save_tokens(token_file, access_token, refresh_token):
    tokens = {
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    with open(token_file, 'w') as file:
        json.dump(tokens, file)

# Función para cargar tokens desde un archivo
def load_tokens(token_file):
    if os.path.exists(token_file):
        with open(token_file, 'r') as file:
            return json.load(file)
    return None

# Función para obtener un nuevo token usando el código de autorización
def get_new_tokens(config):
    token_url = 'https://id.twitch.tv/oauth2/token'
    response = requests.post(token_url, {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': config['authorization_code'],
        'grant_type': 'authorization_code',
        'redirect_uri': config['redirect_uri']
    })

    if response.status_code == 200:
        tokens = response.json()
        save_tokens(config['token_file'], tokens['access_token'], tokens['refresh_token'])
        return tokens['access_token']
    else:
        print("Error al obtener el token de acceso:", response.json())
        return None

# Función para renovar el token de acceso usando el refresh token
def refresh_access_token(config, refresh_token):
    token_url = 'https://id.twitch.tv/oauth2/token'
    response = requests.post(token_url, {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    })

    if response.status_code == 200:
        new_tokens = response.json()
        save_tokens(config['token_file'], new_tokens['access_token'], new_tokens['refresh_token'])
        return new_tokens['access_token']
    else:
        print("Error al renovar el token de acceso:", response.json())
        return None

# Función para obtener el token de acceso, renovándolo si es necesario
def get_access_token(config):
    tokens = load_tokens(config['token_file'])
    if tokens:
        return refresh_access_token(config, tokens['refresh_token'])
    else:
        return get_new_tokens(config)

# Función para asignar medallas (opcional)
def assign_medals(subscribers):
    if subscribers:
        subscribers[0]['medal'] = '<span class="iconify" data-icon="emojione:1st-place-medal" style="color: #ffd700;"></span>'  # Medalla de oro
        for i in range(1, len(subscribers)):
            if subscribers[i]['gift_count'] > 0:
                subscribers[i]['medal'] = '<span class="iconify" data-icon="emojione:2nd-place-medal" style="color: #c0c0c0;"></span>'  # Medalla de plata
            else:
                subscribers[i]['medal'] = '<span class="iconify" data-icon="emojione:3rd-place-medal" style="color: #cd7f32;"></span>'  # Medalla de bronce

# Función para generar filas HTML
# Función para generar filas HTML
def generate_table_rows(subscribers):
    icon_list = [
        'mdi:alien',
        'mdi:ghost',
        'mdi:robot',
        'mdi:rocket',
        'mdi:space-invader'
    ]

    rows_html = []
    for subscriber in subscribers:
        icon = random.choice(icon_list)
        color = f"#{random.randint(0, 0xFFFFFF):06x}"  # Generar un color aleatorio en formato hexadecimal
        icon_html = f'<span class="iconify" data-icon="{icon}" style="color: {color}; font-size: 32px;"></span>'
        rows_html.append(
            f"<tr>"
            f"<td class='py-3 px-6 text-left'>{icon_html}</td>"
            f"<td class='py-3 px-6 text-left'>{subscriber['User Name']}</td>"  # Asegúrate de que 'User Name' sea la clave correcta
            f"<td class='py-3 px-6 text-left'>{subscriber['Tier']}</td>"        # Asegúrate de que 'Tier' sea la clave correcta
            f"<td class='py-3 px-6 text-left'>{subscriber['gift_count']}</td>"  # 'gift_count' es calculado por tu función
            f"</tr>"
        )

    return "\n".join(rows_html)

# Función para tomar una captura de pantalla usando Selenium
def take_screenshot(html_file_path, output_image_path):
    edge_options = EdgeOptions()
    edge_options.headless = True  # Ejecuta el navegador en modo headless (sin interfaz gráfica)
    
    # Configurar para que se abra en fullscreen
    #edge_options.add_argument("--start-fullscreen")  # Fullscreen mode
    edge_options.add_argument("--window-size=1920,1080")  # Establecer tamaño de ventana (pantalla completa estándar)

    # Iniciar el navegador Edge
    driver = webdriver.Edge(options=edge_options)

    ruta=os.getcwd()
    # Abrir el archivo HTML generado
    driver.get(f'file:///{ruta}//{html_file_path}')

    # Esperar un momento para asegurarse de que la página se haya cargado completamente
    time.sleep(2)  # Aumentar el tiempo de espera si es necesario

    # Tomar una captura de pantalla
    driver.save_screenshot(output_image_path)

    # Cerrar el navegador
    driver.quit()

# Función para obtener el ID de usuario de Twitch
def get_user_id(headers, twitch_username):
    url = f'https://api.twitch.tv/helix/users?login={twitch_username}'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user_info = response.json()
        return user_info['data'][0]['id']  # Aquí obtienes tu ID de usuario
    else:
        print("Error al obtener el ID de usuario:", response.json())
        return None

# Función para obtener la lista de suscriptores
def get_subscribers(headers, user_id):
    url = f'https://api.twitch.tv/helix/subscriptions?broadcaster_id={user_id}'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()['data']
    else:
        print("Error al obtener la lista de suscriptores:", response.json())
        return None

# Función para guardar los suscriptores en un archivo CSV
def save_subscribers_to_csv(subscribers, csv_filename):
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Escribir los encabezados
        writer.writerow(['User ID', 'User Name', 'User Login', 'Plan Name', 'Tier', 'Is Gift', 'Gifter Name'])

        # Escribir los datos de los suscriptores
        for subscriber in subscribers:
            writer.writerow([
                subscriber['user_id'],
                subscriber['user_name'],
                subscriber['user_login'],
                subscriber['plan_name'],
                subscriber['tier'],
                subscriber['is_gift'],
                subscriber.get('gifter_name', '')
            ])

# Función para procesar la lista de suscriptores (calcular el número de regalos) leyendo desde el CSV
def process_subscribers_from_csv(csv_filename):
    subscribers = []

    # Leer los datos desde el archivo CSV
    with open(csv_filename, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Convertir los campos necesarios de texto a los tipos correctos si es necesario
            row['gift_count'] = 0  # Inicializar el campo de gift_count
            subscribers.append(row)

    # Procesar los suscriptores para contar el número de regalos
    for subscriber in subscribers:
        gift_count = sum(1 for other_subscriber in subscribers if other_subscriber.get('Gifter Name') == subscriber['User Name'])
        subscriber['gift_count'] = gift_count

    return sorted(subscribers, key=lambda x: int(x['gift_count']), reverse=True)


# Función para generar el HTML con la lista de suscriptores
def generate_html(template_html_filename, output_html_filename, rows_html):
    with open(template_html_filename, 'r', encoding='utf-8') as file:
        html_template = file.read()

    html_content = html_template.replace("<!-- PLACEHOLDER -->", rows_html)

    with open(output_html_filename, 'w', encoding='utf-8') as file:
        file.write(html_content)

    print(f"Archivo HTML generado: {output_html_filename}")

def peticion():
    load_env()
    config = get_config()

    access_token = get_access_token(config)
    if not access_token:
        return

    headers = {
        'Client-ID': config['client_id'],
        'Authorization': f'Bearer {access_token}'
    }

    twitch_username = 'patriciofernandezia'
    user_id = get_user_id(headers, twitch_username)
    if not user_id:
        return

    subscribers = get_subscribers(headers, user_id)
    if not subscribers:
        return

    csv_filename = 'suscriptores.csv'
    save_subscribers_to_csv(subscribers, csv_filename)
    print(f"La lista de suscriptores se ha guardado en '{csv_filename}'.")
    return subscribers
    

# Función principal para generar el HTML y tomar la captura de pantalla
def main():
    #subscribers=peticion()

    sorted_subscribers = process_subscribers_from_csv('suscriptores.csv')
    rows_html = generate_table_rows(sorted_subscribers)

    output_html_filename = 'index_con_placeholder.html'
    generate_html('template.html', output_html_filename, rows_html)

    take_screenshot(output_html_filename, 'screenshot.png')

if __name__ == '__main__':
    main()
