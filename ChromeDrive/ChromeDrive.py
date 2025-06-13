import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager # <<< ESSA LINHA É CRUCIAL

def open_google_drive(
    user_data_dir: str = None,
    profile_directory: str = "Default", 
                                        
    headless: bool = False
):
    """
    Abre o Google Drive no navegador Chrome, usando webdriver_manager.
    """
    driver = None
    GOOGLE_DRIVE_URL = "https://drive.google.com/"

    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")

        if headless:
            chrome_options.add_argument("--headless")
            print("Executando Chrome em modo headless (sem interface gráfica).")

        if user_data_dir:
            # user-data-dir deve ser o diretório pai 'User Data'
            chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            # profile-directory deve ser o nome da subpasta do perfil
            chrome_options.add_argument(f"profile-directory={profile_directory}")
            print(f"Tentando carregar perfil Chrome de: {user_data_dir} - Perfil: {profile_directory}")
        else:
            print("Nenhum diretório de dados de usuário especificado. O Chrome pode abrir uma nova sessão ou pedir login.")

        # --- AQUI ESTÁ A CHAVE: USANDO WEBDRIVER_MANAGER ---
        service = Service(ChromeDriverManager().install())
        print("ChromeDriver instalado/atualizado com sucesso via webdriver_manager.")
        # --- FIM DA CHAVE ---

        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"Navegador Chrome iniciado. Abrindo: {GOOGLE_DRIVE_URL}")

        driver.get(GOOGLE_DRIVE_URL)

        print("Aguardando o carregamento do Google Drive (até 30 segundos)...")
        # Uma espera mais robusta por um elemento do Google Drive
        # Você pode ajustar este se conhecer um elemento específico que sempre aparece.
        # Por exemplo, By.ID, "docs-chrome" ou By.CSS_SELECTOR, ".gb_Oc" (para o logo Google)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        time.sleep(5) # Pequena pausa adicional para renderização completa

        print("Google Drive aberto com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro ao abrir o Google Drive: {e}")
    finally:
        if driver and "detach" not in chrome_options.experimental_options:
            print("Fechando o navegador...")
            driver.quit()
        elif driver and "detach" in chrome_options.experimental_options:
            print("Navegador permanecerá aberto (detach=True).")


if __name__ == "__main__":
    # --- CAMINHOS DO SEU PERFIL DO CHROME ---
    # AGORA CORRETO: user_data_dir aponta para a pasta PAI 'User Data'
    MY_CHROME_USER_DATA_DIR = r"C:\Users\SPXBR16549\AppData\Local\Google\Chrome\User Data"
    # E profile_directory aponta para a subpasta do perfil
    MY_CHROME_PROFILE_DIRECTORY = "Profile 3"

    print("Iniciando a abertura do Google Drive...")
    open_google_drive(
        user_data_dir=MY_CHROME_USER_DATA_DIR,
        profile_directory=MY_CHROME_PROFILE_DIRECTORY,
        headless=False
    )
    print("\nProcesso de abertura do Google Drive finalizado.")