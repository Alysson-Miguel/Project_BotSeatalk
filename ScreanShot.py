import mss
from PIL import Image
import os
from datetime import datetime

def take_screenshot_area(x, y, width, height, save_folder_name="ScreanShots"):
    if not all(isinstance(arg, int) and arg >= 0 for arg in [x, y, width, height]):
        print("Erro: As coordenadas e dimensões devem ser inteiros não negativos.")
        return None
    if width == 0 or height == 0:
        print("Erro: A largura e a altura da área não podem ser zero.")
        return None

    try:
        with mss.mss() as sct:
            # Define a área a ser capturada
            monitor = {
                "top": y,
                "left": x,
                "width": width,
                "height": height
            }

            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
            full_save_path = os.path.join(os.getcwd(), save_folder_name)
            os.makedirs(full_save_path, exist_ok=True)

            # Gera um nome de arquivo único com timestamp
            timestamp = datetime.now().strftime("%H")
            filename = f"Report das {timestamp}.png"
            full_file_path = os.path.join(full_save_path, filename)

            img.save(full_file_path)
            print(f"Screenshot da área salva em: {full_file_path}")
            return full_file_path

    except Exception as e:
        print(f"Ocorreu um erro ao tirar a screenshot da área: {e}")
        return None
