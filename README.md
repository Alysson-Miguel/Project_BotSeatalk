# Project_BotSeatalk
No Basico, o Bot reporta hora a hora.


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