import mss
import mss.tools
from PIL import Image
import os
from datetime import datetime

def take_screenshot_area(x, y, width, height, save_folder_name="ScreenShots"):
    """
    Tira uma screenshot de uma área específica da tela e salva como um arquivo PNG
    dentro de uma pasta especificada no mesmo diretório do script.

    Args:
        x (int): A coordenada X do canto superior esquerdo da área a ser capturada.
        y (int): A coordenada Y do canto superior esquerdo da área a ser capturada.
        width (int): A largura da área a ser capturada.
        height (int): A altura da área a ser capturada.
        save_folder_name (str): O nome da pasta onde a screenshot será salva.
                                 A pasta será criada no mesmo diretório do script
                                 se não existir. O padrão é "screenshots".

    Returns:
        str or None: O caminho completo do arquivo da screenshot se for bem-sucedido,
                     caso contrário, não.
    """
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
            timestamp = datetime.now().strftime("%H.%M")
            filename = f"Report das {timestamp}.png"
            full_file_path = os.path.join(full_save_path, filename)

            img.save(full_file_path)
            print(f"Screenshot da área salva em: {full_file_path}")
            return full_file_path

    except Exception as e:
        print(f"Ocorreu um erro ao tirar a screenshot da área: {e}")
        return None

if __name__ == "__main__":
    #Salva a screenshot na pasta padrão "screenshots" (se ela não existir, será criada)
    print("\nCapturando uma área de 300x200 pixels em (0, 0) e salvando na pasta padrão 'ScreenShots'...")
