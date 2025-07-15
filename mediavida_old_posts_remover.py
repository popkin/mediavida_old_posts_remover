import requests
from bs4 import BeautifulSoup
import time
import getpass
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

# --- Configuración ---
BASE_URL = "https://www.mediavida.com"
LOGIN_URL = f"{BASE_URL}/login"
LOG_FILE = "edited_posts.txt" # Archivo para registrar los posts editados

def load_edited_posts():
    """Carga las URLs de los posts ya editados desde el archivo de log."""
    if not os.path.exists(LOG_FILE):
        return set()
    try:
        with open(LOG_FILE, 'r') as f:
            # Usamos un set para una búsqueda más rápida (O(1) en promedio)
            return {line.strip() for line in f}
    except Exception as e:
        print(f"Advertencia: No se pudo leer el archivo de log '{LOG_FILE}'. Se continuará sin él. Error: {e}")
        return set()

def log_edited_post(post_url):
    """Añade la URL de un post editado al archivo de log."""
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(post_url + '\n')
    except Exception as e:
        print(f"Advertencia: No se pudo escribir en el archivo de log '{LOG_FILE}'. Error: {e}")


def login(session, username, password):
    """
    Maneja el inicio de sesión en Mediavida.
    Extrae el token de seguridad CSRF necesario para el login.
    Devuelve True si el inicio de sesión fue exitoso, False en caso contrario.
    """
    print("Iniciando sesión...")
    try:
        login_page_response = session.get(LOGIN_URL)
        login_page_response.raise_for_status()
        soup = BeautifulSoup(login_page_response.text, 'html.parser')

        token_input = soup.find('input', {'name': '_token'})
        if not token_input or not token_input.has_attr('value'):
            print("No se pudo encontrar el token de seguridad (_token) en la página de login.")
            return False
        
        csrf_token = token_input['value']
        print("Token de seguridad encontrado.")

        login_data = {
            'name': username,
            'password': password,
            'cookie': '1',
            '_token': csrf_token,
            'return': ''
        }

        response = session.post(LOGIN_URL, data=login_data, headers={"Referer": LOGIN_URL})
        response.raise_for_status()

        if 'logout' in response.text.lower():
            print("¡Inicio de sesión exitoso!")
            return True
        else:
            print("Error en el inicio de sesión. Revisa tu usuario y contraseña.")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error de red durante el inicio de sesión: {e}")
        return False
    except Exception as e:
        print(f"Ocurrió un error inesperado durante el login: {e}")
        return False

def get_total_pages(session, username):
    """
    Obtiene el número total de páginas de posts de un usuario.
    """
    print("Obteniendo el número total de páginas de posts...")
    try:
        first_page_url = f"{BASE_URL}/id/{username}/posts"
        response = session.get(first_page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        page_numbers = [1] # Siempre habrá al menos una página
        pagination_links = soup.select('ul.pg a[href]')
        for link in pagination_links:
            href = link.get('href', '')
            if '/posts/' in href:
                try:
                    page_num_str = href.split('/')[-1]
                    if page_num_str.isdigit():
                        page_numbers.append(int(page_num_str))
                except (ValueError, IndexError):
                    continue
        
        total_pages = max(page_numbers)
        print(f"Se encontraron {total_pages} páginas en total.")
        return total_pages
    except Exception as e:
        print(f"No se pudo determinar el número total de páginas: {e}. Se asumirá 1.")
        return 1

def get_oldest_post_date_on_page(session, url):
    """
    Devuelve la fecha del post MÁS ANTIGUO en una página determinada.
    """
    try:
        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        all_timestamps = [int(tag['data-time']) for tag in soup.select('span.rd[data-time]')]
        
        if not all_timestamps:
            return None

        oldest_timestamp = min(all_timestamps)
        return datetime.fromtimestamp(oldest_timestamp)
    except requests.exceptions.RequestException as e:
        print(f"  Error de red al acceder a {url}: {e}")
        return None
    except (ValueError, TypeError, IndexError):
        return None

def find_start_page(session, username, cutoff_date, total_pages):
    """
    Usa búsqueda binaria para encontrar la primera página que contiene posts antiguos.
    """
    print("\n--- Iniciando búsqueda binaria para encontrar la primera página con posts antiguos ---")
    low = 1
    high = total_pages
    start_page = -1

    while low <= high:
        mid = (low + high) // 2
        print(f"  Comprobando página {mid}...")
        
        page_url = f"{BASE_URL}/id/{username}/posts/{mid}"
        oldest_date_on_page = get_oldest_post_date_on_page(session, page_url)
        
        time.sleep(1)

        if oldest_date_on_page is None:
            high = mid - 1
            continue

        if oldest_date_on_page > cutoff_date:
            print(f"    -> La página {mid} es demasiado reciente. Buscando en páginas posteriores.")
            low = mid + 1
        else:
            print(f"    -> La página {mid} contiene posts antiguos. Es un candidato. Buscando en páginas anteriores.")
            start_page = mid
            high = mid - 1
            
    if start_page != -1:
        print(f"--- Búsqueda binaria finalizada. Se empezará a escanear desde la página {start_page} ---")
    else:
        print("--- Búsqueda binaria finalizada. No se encontraron páginas con posts que cumplan el criterio. ---")
        
    return start_page

def process_and_edit_posts(session, username, years_old):
    """
    Recorre las páginas de posts del usuario usando búsqueda binaria y edita los posts antiguos.
    """
    cutoff_date = datetime.now() - relativedelta(years=years_old)
    print(f"Se editarán todos los posts anteriores al {cutoff_date.strftime('%d-%m-%Y')}.")

    already_edited_urls = load_edited_posts()
    print(f"Se han cargado {len(already_edited_urls)} URLs de posts ya editados anteriormente.")

    total_pages = get_total_pages(session, username)
    start_page = find_start_page(session, username, cutoff_date, total_pages)

    if start_page == -1:
        print("\nNo se encontraron posts que cumplan con los criterios de antigüedad.")
        return

    posts_to_edit = []
    print("\n--- Fase 1: Recopilando posts para editar desde la página de inicio encontrada ---")
    for page_num in range(start_page, total_pages + 1):
        posts_page_url = f"{BASE_URL}/id/{username}/posts/{page_num}"
        print(f"Analizando página: {posts_page_url}")

        try:
            response = session.get(posts_page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            rows = soup.select('tbody#temas tr')
            if not rows:
                break

            for row in rows:
                date_span = row.select_one('span.rd[data-time]')
                if not date_span:
                    continue

                post_timestamp = int(date_span['data-time'])
                post_date = datetime.fromtimestamp(post_timestamp)

                if post_date < cutoff_date:
                    link_tag = row.select_one('a.hb[href]')
                    if link_tag:
                        post_url = BASE_URL + link_tag['href']
                        if post_url in already_edited_urls:
                            print(f"  [SALTADO] El post ya está en el log de editados: {link_tag.text.strip()}")
                            continue
                        
                        posts_to_edit.append(post_url)
                        print(f"  [AÑADIDO] Post del {post_date.strftime('%d-%m-%Y')}: {link_tag.text.strip()}")
            
            time.sleep(2)

        except Exception as e:
            print(f"Ocurrió un error inesperado al procesar la página {page_num}: {e}")
            continue

    if not posts_to_edit:
        print("\nNo se encontraron posts que cumplan con los criterios de antigüedad.")
        return

    print(f"\n--- Fase 2: Edición de posts ---")
    print(f"Se han encontrado {len(posts_to_edit)} posts para editar.")
    
    confirm = input("¿Estás SEGURO de que quieres reemplazar el contenido de estos posts por un '.'? (escribe 'si' para confirmar): ")
    if confirm.lower() != 'si':
        print("Operación cancelada.")
        return

    for i, post_url in enumerate(posts_to_edit):
        print(f"\nEditando post {i + 1}/{len(posts_to_edit)}: {post_url}")
        try:
            status = edit_post(session, post_url)
            
            if status == 'edited':
                print("  -> Post editado correctamente.")
                log_edited_post(post_url)
                print("  -> Esperando 3 segundos antes del siguiente...")
                time.sleep(3)
            elif status == 'skipped':
                print("  -> Saltado. El contenido ya es '.'.")
                log_edited_post(post_url)
                time.sleep(1)
                
        except Exception as e:
            print(f"  -> ERROR: No se pudo editar el post. {e}")
            print("  -> Saltando al siguiente post.")
            continue
            
    print("\n¡Proceso completado!")

def edit_post(session, post_url):
    """
    Navega a un post específico, comprueba su contenido, y si no es '.',
    lo edita y envía el formulario.
    Devuelve 'edited', 'skipped' o lanza una excepción.
    """
    post_page = session.get(post_url)
    post_page.raise_for_status()
    soup = BeautifulSoup(post_page.text, 'html.parser')
    
    edit_link_tag = soup.find('a', class_='post-btn', title='Editar')
    if not edit_link_tag or not edit_link_tag.has_attr('href'):
        raise Exception("No se encontró el enlace de edición. Puede que no tengas permisos o que el post esté cerrado.")
    
    edit_page_url = BASE_URL + edit_link_tag['href']

    edit_page = session.get(edit_page_url)
    edit_page.raise_for_status()
    edit_soup = BeautifulSoup(edit_page.text, 'html.parser')
    
    form = edit_soup.find('form', id='postear')
    if not form:
        raise Exception("No se encontró el formulario de edición.")
        
    textarea = form.find('textarea', id='cuerpo')
    if textarea and textarea.text.strip() == ".":
        return 'skipped'

    action_url = BASE_URL + form['action']
    
    payload = {'cuerpo': '.'}
    hidden_inputs = form.find_all('input', {'type': 'hidden'})
    for input_tag in hidden_inputs:
        payload[input_tag['name']] = input_tag.get('value', '')
        
    submit_button = form.find('button', {'type': 'submit'})
    if submit_button and submit_button.has_attr('name'):
        payload[submit_button['name']] = submit_button.get('value', '')

    response = session.post(action_url, data=payload, headers={"Referer": edit_page_url})
    response.raise_for_status()

    if response.status_code == 200:
        return 'edited'
    else:
        raise Exception(f"La edición falló con el código de estado {response.status_code}")

if __name__ == "__main__":
    print("--- Script para editar posts antiguos en Mediavida ---")
    print("ADVERTENCIA: Esta acción es irreversible y modificará tus posts permanentemente.")
    
    username = input("Introduce tu nombre de usuario de Mediavida: ")
    password = getpass.getpass("Introduce tu contraseña de Mediavida (no se mostrará): ")
    
    while True:
        try:
            years_old_str = input("Editar posts con más de (introduce un número) años de antigüedad: ")
            years_old = int(years_old_str)
            if years_old > 0:
                break
            else:
                print("Por favor, introduce un número mayor que cero.")
        except ValueError:
            print("Entrada no válida. Por favor, introduce un número entero.")

    with requests.Session() as s:
        s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        if login(s, username, password):
            process_and_edit_posts(s, username, years_old)
