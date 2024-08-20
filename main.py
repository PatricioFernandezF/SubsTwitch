import requests
import json
import os
import csv
import random
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium import webdriver
from dotenv import load_dotenv
import time

# Cargar las variables de entorno desde el archivo .env manualmente
def load_env():
    env_vars = {}
    env_path = os.path.join(ruta, '.env')  # Ruta al archivo .env

    if os.path.exists(env_path):
        with open(env_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    else:
        print(f"El archivo .env no se encontró en la ruta: {env_path}")
    
    return env_vars

# Configuración de la aplicación
def get_config():
    env_vars = load_env()
    print(env_vars)
    return {
        'client_id': env_vars.get('CLIENT_ID'),
        'client_secret': env_vars.get('CLIENT_SECRET'),
        'redirect_uri': env_vars.get('REDIRECT_URI'),
        'authorization_code': env_vars.get('AUTHORIZATION_CODE'),
        'token_file': os.path.join(ruta, 'tokens.json')
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
    if os.path.exists(ruta + "//" + token_file):
        with open(ruta + "//" + token_file, 'r') as file:
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

# Función para cargar la lista de iconos desde un archivo JSON
def load_icons_from_json(json_filename):
    try:
        with open(ruta + "//" + json_filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data.get('icons', [])
    except Exception as e:
        print(f"Error loading icons from {json_filename}: {e}")
        return ['mdi:alien']  # Fallback icon if there's an issue

# Función para generar filas HTML
def generate_table_rows(subscribers):
    icon_list = load_icons_from_json('iconos.json')  # Cargar los iconos desde el archivo JSON

    rows_html = []
    for subscriber in subscribers:
        try:
            # Asegurar que siempre haya un icono seleccionado
            if icon_list:
                icon = random.choice(icon_list)
            else:
                icon = 'mdi:alien'  # Fallback icon

            color = f"#{random.randint(0, 0xFFFFFF):06x}"  # Generar un color aleatorio en formato hexadecimal
            icon_html = f'<span class="iconify" data-icon="{icon}" style="color: {color}; font-size: 70px;"></span>'
            
            # Asegurarse de que los datos del suscriptor existen
            user_name = subscriber.get('User Name', 'Unknown')
            if user_name == "patriciofernandezia":
                continue  # Omitir este suscriptor
            
            tier = subscriber.get('Tier', 'N/A')
            gift_count = subscriber.get('gift_count', '0')

            # Añadir la fila a la lista de filas HTML
            rows_html.append(
                f"<tr>"
                f"<td class='py-3 px-6 text-center'>{icon_html}</td>"
                f"<td class='py-3 px-6 text-left'>{user_name}</td>"  
                f"<td class='py-3 px-6 text-center'>{tier}</td>"        
                f"<td class='py-3 px-6 text-center'>{gift_count}</td>"
                f"</tr>"
            )
        except Exception as e:
            print(f"Error generating row for subscriber {subscriber}: {e}")
            rows_html.append(
                f"<tr>"
                f"<td class='py-3 px-6 text-left'><span class='iconify' data-icon='mdi:alien' style='color: #000; font-size: 48px;'></span></td>"
                f"<td class='py-3 px-6 text-left'>{subscriber.get('User Name', 'Unknown')}</td>"
                f"<td class='py-3 px-6 text-left'>{subscriber.get('Tier', 'N/A')}</td>"
                f"<td class='py-3 px-6 text-center'>{subscriber.get('gift_count', '0')}</td>"
                f"</tr>"
            )
            continue

    return "\n".join(rows_html)

# Función para tomar una captura de pantalla usando Selenium
def take_screenshot(html_file_path, output_image_path):
    edge_options = EdgeOptions()
    edge_options.headless = True  # Ejecuta el navegador en modo headless (sin interfaz gráfica)
    
    # Configurar para que se abra en fullscreen
    edge_options.add_argument("--window-size=1920,1080")  # Establecer tamaño de ventana (pantalla completa estándar)

    # Iniciar el navegador Edge
    driver = webdriver.Edge(options=edge_options)

    # Abrir el archivo HTML generado
    driver.get(f'file:///{ruta}//{html_file_path}')

    # Esperar un momento para asegurarse de que la página se haya cargado completamente
    time.sleep(2)  # Aumentar el tiempo de espera si es necesario

    # Configurar el nivel de zoom al 50% utilizando JavaScript
    driver.execute_script("document.body.style.zoom='50%'")

    # Tomar una captura de pantalla
    driver.save_screenshot(ruta + "//" + output_image_path)

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
    with open(ruta + "//" + csv_filename, mode='w', newline='', encoding='utf-8') as file:
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
    with open(ruta + "//" + csv_filename, mode='r', newline='', encoding='utf-8') as file:
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
    with open(ruta + "//" + template_html_filename, 'r', encoding='utf-8') as file:
        html_template = file.read()

    html_content = html_template.replace("<!-- PLACEHOLDER -->", rows_html)

    with open(ruta + "//" + output_html_filename, 'w', encoding='utf-8') as file:
        file.write(html_content)

    print(f"Archivo HTML generado: {ruta + '//' + output_html_filename}")

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
    print(f"La lista de suscriptores se ha guardado en '{ruta + '//' + csv_filename}'.")
    return subscribers

# Función principal para generar el HTML y tomar la captura de pantalla
def main():
    global ruta
    #Para que el obs lo procese
    ruta = r"C:\Users\Patricio\Documents\Clases Video\Directos\personalizacion\SubsTwitch"
    subscribers = peticion()

    sorted_subscribers = process_subscribers_from_csv('suscriptores.csv')
    rows_html = generate_table_rows(sorted_subscribers)

    output_html_filename = 'index_con_placeholder.html'
    generate_html('template.html', output_html_filename, rows_html)

    take_screenshot(output_html_filename, 'screenshot.png')

if __name__ == '__main__':
    main()
