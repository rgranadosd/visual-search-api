# -*- coding: utf-8 -*-

import sys
import os
import requests
import base64
import json   # Para formatear el JSON
import traceback   # Para imprimir tracebacks detallados
import urllib.parse   # Para analizar y modificar URLs
from bs4 import BeautifulSoup   # Para hacer scraping en la página destino
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTextBrowser, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
import yaml

def cargar_configuracion(config_file="config.yml"):
    """Carga la configuración desde un fichero YAML ubicado en el mismo directorio que la aplicación."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_file)
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        raise Exception(f"Error al cargar el fichero de configuración: {str(e)}")

def select_image():
    """Abre un diálogo para que el usuario seleccione un archivo de imagen."""
    filename, _ = QFileDialog.getOpenFileName(
        None,
        "Selecciona una imagen",
        os.path.expanduser("~"),
        "Imágenes (*.png *.jpg *.jpeg *.bmp)"
    )
    if filename:
        return filename
    else:
        raise Exception("No se seleccionó ninguna imagen")

def load_qimage(image_path):
    """Carga una imagen desde la ruta dada y la devuelve como QImage."""
    image = QImage(image_path)
    if image.isNull():
        raise Exception(f"No se pudo cargar la imagen desde {image_path}")
    return image

def upload_image_to_imgbb(image_path, api_key):
    """Sube la imagen a imgBB usando su API y devuelve la URL pública."""
    imgbb_upload_url = "https://api.imgbb.com/1/upload"
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        b64_image = base64.b64encode(image_data).decode("utf-8")
        payload = {"image": b64_image}
        upload_url = f"{imgbb_upload_url}?key={api_key}"
        response = requests.post(upload_url, data=payload, timeout=30)
        response.raise_for_status()
        json_response = response.json()
        if json_response.get("success"):
            return json_response["data"]["url"]
        else:
            error_message = json_response.get("error", {}).get("message", "Error desconocido de imgBB")
            raise Exception(f"Error en la API de imgBB: {error_message}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de red o conexión al subir a imgBB: {str(e)}")
    except Exception as e:
        raise Exception(f"Excepción al subir imagen a imgBB: {str(e)}")

def get_oauth2_token(client_id, client_secret):
    """Obtiene un token OAuth2 de Inditex usando credenciales de cliente."""
    token_url = "https://auth.inditex.com:443/openam/oauth2/itxid/itxidmp/access_token"
    data = "grant_type=client_credentials&scope=technology.catalog.read"
    headers = {
        "User-Agent": "OpenPlatform/1.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        response = requests.post(token_url, data=data, headers=headers,
                                 auth=(client_id, client_secret), timeout=15)
        response.raise_for_status()
        json_response = response.json()
        token = json_response.get("id_token")
        if token is None:
            raise Exception("La respuesta de autenticación no contiene un 'id_token'")
        return token
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de red o conexión al obtener token: {str(e)}")
    except Exception as e:
        raise Exception(f"Excepción al obtener token: {str(e)}")

def visual_search(image_url, token):
    """Realiza la búsqueda visual en la API de Inditex y devuelve los resultados."""
    api_url = "https://api.inditex.com/pubvsearch/products"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "OpenPlatform/1.0"
    }
    params = {
        "image": image_url,
        "page": 1,
        "perPage": 5
    }
    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        json_response = response.json()
        print("\n--- Respuesta API Visual Search (primer producto si existe): ---")
        if json_response and isinstance(json_response, list):
            print(json.dumps(json_response[0], indent=2))
        else:
            print(json_response)
        print("-----------------------------------------------------------\n")
        return json_response
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error de red o conexión en la búsqueda visual: {str(e)}")
    except Exception as e:
        try:
            error_detail = response.text
        except:
            error_detail = "No se pudo obtener texto de la respuesta."
        raise Exception(f"Excepción en la búsqueda visual: {str(e)}. Respuesta: {error_detail}")

def get_product_thumbnail(product_link, desired_width="882", product_name=None):
    """
    Asegura que la URL del producto incluya "www.zara.com" y, si no tiene
    slug, la reconstruye usando el nombre del producto. Luego solicita la página
    con headers adicionales y extrae la URL de la imagen desde la meta "og:image",
    actualizando el parámetro "w" al valor deseado.
    """
    parsed = urllib.parse.urlparse(product_link)
    netloc = parsed.netloc
    if not netloc.startswith("www."):
        netloc = "www." + netloc.lstrip(".")
        product_link = urllib.parse.urlunparse(parsed._replace(netloc=netloc))
    last_part = product_link.rsplit("/", 1)[-1]
    if last_part.startswith("-P") and product_name:
        slug = product_name.lower().replace(" ", "-")
        product_code = last_part.lstrip("-P").rsplit(".", 1)[0]
        product_link = f"https://www.zara.com/es/en/{slug}-p{product_code}.html"
    print("Producto link transformado:", product_link)
    
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/90.0.4430.85 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.zara.com/"
    }
    try:
        response = requests.get(product_link, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        final_url = response.url
        print("URL final tras redirección:", final_url)
        print("Página descargada. Longitud:", len(response.text))
        soup = BeautifulSoup(response.text, 'html.parser')
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            url = meta["content"]
            parsed_url = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed_url.query)
            qs["w"] = [desired_width]
            new_qs = urllib.parse.urlencode(qs, doseq=True)
            new_url = urllib.parse.urlunparse(parsed_url._replace(query=new_qs))
            print("Thumbnail extraído:", new_url)
            return new_url
        else:
            print("No se encontró la meta 'og:image' en la página.")
        picture = soup.find("picture", class_="media-image")
        if picture:
            source = picture.find("source")
            if source and source.has_attr("srcset"):
                srcset = source["srcset"]
                first_url = srcset.split(",")[0].strip().split()[0]
                print("Thumbnail extraído desde <picture>:", first_url)
                return first_url
        return None
    except Exception as e:
        print("Error en get_product_thumbnail:", e)
        return None

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Search App con PyQt5")
        self.resize(800, 700)
        # Cargar la configuración y extraer las credenciales
        config = cargar_configuracion()
        indiTEx_config = config.get("indiTEx", {})
        self.oauth_client_id = indiTEx_config.get("oauth_client_id")
        self.oauth_client_secret = indiTEx_config.get("oauth_client_secret")
        imgBB_config = config.get("imgBB", {})
        self.imgbb_api_key = imgBB_config.get("api_key")
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.image_label = QLabel("La imagen seleccionada se mostrará aquí")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.layout.addWidget(self.image_label)
        self.select_button = QPushButton("Seleccionar imagen y buscar")
        self.select_button.clicked.connect(self.select_and_search)
        self.layout.addWidget(self.select_button)
        self.results_text = QTextBrowser()
        self.results_text.setReadOnly(True)
        self.results_text.setOpenExternalLinks(True)
        self.layout.addWidget(self.results_text)
        self.setLayout(self.layout)

    def show_message(self, title, message, icon=QMessageBox.Information):
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

    def select_and_search(self):
        self.results_text.setPlainText("Procesando...")
        QApplication.processEvents()
        self.select_button.setEnabled(False)
        try:
            # Seleccionar y cargar imagen
            image_path = select_image()
            qimage = load_qimage(image_path)
            pixmap = QPixmap.fromImage(qimage).scaled(
                self.image_label.width() - 20,
                self.image_label.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(pixmap)
            
            # Subir imagen a imgBB
            self.results_text.append("Subiendo imagen a imgBB...")
            QApplication.processEvents()
            imgbb_url = upload_image_to_imgbb(image_path, self.imgbb_api_key)
            print(f"URL de imgBB obtenida: {imgbb_url}")
            self.results_text.append(f"Imagen subida: <a href='{imgbb_url}'>{imgbb_url}</a>")
            
            # Obtener token OAuth2 de Inditex
            self.results_text.append("Obteniendo token de autenticación...")
            QApplication.processEvents()
            token = get_oauth2_token(self.oauth_client_id, self.oauth_client_secret)
            print("Token obtenido con éxito.")
            self.results_text.append("Token obtenido.")
            
            # Realizar búsqueda visual en Inditex
            self.results_text.append("Realizando búsqueda visual...")
            QApplication.processEvents()
            results = visual_search(imgbb_url, token)
            print(f"Resultados de búsqueda obtenidos: {len(results)} productos.")
            
            # Procesar y mostrar resultados
            html_result_text = ""
            if not results or not isinstance(results, list):
                html_result_text = "<b>No se encontraron productos similares o la respuesta no es válida.</b>"
                print("La respuesta de la API no fue una lista válida de productos.")
            else:
                html_result_text += f"<b>Se encontraron {len(results)} productos:</b><br/><br/>"
                print("\n--- Procesando productos para HTML ---")
                for i, product in enumerate(results):
                    print(f"Producto #{i+1}:")
                    product_id = product.get("id", "N/D")
                    product_name = product.get("name", "Sin nombre")
                    price_info = product.get("price", {})
                    current_price = price_info.get("value", {}).get("current", "N/D")
                    currency = price_info.get("currency", "")
                    product_link = product.get("link", "")
                    brand = product.get("brand", "N/D")
                    product_image_url = ""
                    if isinstance(product.get('images'), list) and product.get('images'):
                        image_data = product['images'][0]
                        if isinstance(image_data, dict):
                            product_image_url = image_data.get('url', '')
                    image_html = ""
                    if product_image_url.startswith("http"):
                        image_html = f"<img src='{product_image_url}' width='100' alt='Thumb {product_name}'><br/>"
                    thumbnail_html = ""
                    if product_link:
                        thumbnail_url = get_product_thumbnail(product_link, product_name=product_name)
                        if thumbnail_url and thumbnail_url.startswith("http"):
                            thumbnail_html = f"<img src='{thumbnail_url}' width='100' alt='Thumbnail de la página {product_name}'><br/>"
                        else:
                            thumbnail_html = "<p>Sin vista previa</p>"
                            print(f"No se encontró imagen real en el enlace: {product_link}")
                    html_result_text += image_html + thumbnail_html
                    html_result_text += (
                        f"<b>ID:</b> {product_id}<br/>"
                        f"<b>Nombre:</b> {product_name}<br/>"
                        f"<b>Precio:</b> {current_price} {currency}<br/>"
                        f"<b>Link:</b> {'<a href=\"%s\">%s</a>' % (product_link, product_link) if product_link else 'No disponible'}<br/>"
                        f"<b>Marca:</b> {brand}<br/><hr/>"
                    )
                print("--------------------------------------\n")
            print("\n--- HTML Final generado para QTextBrowser ---")
            print(html_result_text)
            print("-------------------------------------------\n")
            self.results_text.setHtml(html_result_text)
        except Exception as e:
            error_message = f"Ocurrió un error:\n{str(e)}"
            print(f"Error en select_and_search: {error_message}")
            traceback.print_exc()
            self.show_message("Error", error_message, QMessageBox.Critical)
            self.results_text.setPlainText(f"Error durante el proceso:\n{str(e)}\n{traceback.format_exc()}")
        finally:
            self.select_button.setEnabled(True)

if __name__ == "__main__":
    # Configuración para alta resolución en pantallas HiDPI
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())