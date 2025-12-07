"""
Cliente para integração com Google Sheets
"""
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import List, Dict, Optional
from config import Config


class SheetsClient:
    """Cliente para leitura e processamento de dados do Google Sheets"""
    
    # Escopos necessários para acessar Google Sheets
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self):
        self.credentials = None
        self.client = None
        self.spreadsheet = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica com Google Sheets usando Service Account"""
        try:
            self.credentials = Credentials.from_service_account_file(
                Config.GOOGLE_SHEETS_CREDENTIALS_FILE,
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(self.credentials)
            self.spreadsheet = self.client.open_by_key(Config.GOOGLE_SHEET_ID)
            
        except FileNotFoundError:
            raise Exception(
                f"Arquivo de credenciais não encontrado: {Config.GOOGLE_SHEETS_CREDENTIALS_FILE}. "
                "Por favor, baixe o arquivo JSON de credenciais do Google Cloud Console."
            )
        except Exception as e:
            raise Exception(f"Erro ao autenticar com Google Sheets: {str(e)}")
    
    def get_worksheet(self, sheet_name: str = None, index: int = 0):
        """
        Obtém uma planilha específica
        
        Args:
            sheet_name: Nome da planilha (opcional)
            index: Índice da planilha (padrão: 0 - primeira planilha)
        
        Returns:
            Worksheet: Objeto da planilha
        """
        try:
            if sheet_name:
                return self.spreadsheet.worksheet(sheet_name)
            else:
                return self.spreadsheet.get_worksheet(index)
        except Exception as e:
            raise Exception(f"Erro ao obter planilha: {str(e)}")
    
    def get_all_data(self, sheet_name: str = None) -> pd.DataFrame:
        """
        Obtém todos os dados de uma planilha como DataFrame
        
        Args:
            sheet_name: Nome da planilha (opcional, usa primeira se não especificado)
        
        Returns:
            pd.DataFrame: Dados da planilha
        """
        try:
            worksheet = self.get_worksheet(sheet_name)
            data = worksheet.get_all_records()
            
            if not data:
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except Exception as e:
            raise Exception(f"Erro ao ler dados da planilha: {str(e)}")
    
    def get_data_range(self, range_name: str, sheet_name: str = None) -> List[List]:
        """
        Obtém dados de um intervalo específico
        
        Args:
            range_name: Nome do intervalo (ex: 'A1:D10')
            sheet_name: Nome da planilha (opcional)
        
        Returns:
            List[List]: Dados do intervalo
        """
        try:
            worksheet = self.get_worksheet(sheet_name)
            return worksheet.get(range_name)
            
        except Exception as e:
            raise Exception(f"Erro ao ler intervalo da planilha: {str(e)}")
    
    def list_worksheets(self) -> List[str]:
        """
        Lista todas as planilhas disponíveis
        
        Returns:
            List[str]: Nomes das planilhas
        """
        try:
            worksheets = self.spreadsheet.worksheets()
            return [ws.title for ws in worksheets]
            
        except Exception as e:
            raise Exception(f"Erro ao listar planilhas: {str(e)}")
    
    def search_data(self, query: str, sheet_name: str = None) -> List[Dict]:
        """
        Busca dados na planilha que correspondam à query
        
        Args:
            query: Texto a ser buscado
            sheet_name: Nome da planilha (opcional)
        
        Returns:
            List[Dict]: Lista de células encontradas com suas posições
        """
        try:
            worksheet = self.get_worksheet(sheet_name)
            cells = worksheet.findall(query)
            
            results = []
            for cell in cells:
                results.append({
                    'row': cell.row,
                    'col': cell.col,
                    'value': cell.value
                })
            
            return results
            
        except Exception as e:
            raise Exception(f"Erro ao buscar dados: {str(e)}")
    
    def get_column_data(self, column_name: str, sheet_name: str = None) -> List:
        """
        Obtém todos os dados de uma coluna específica
        
        Args:
            column_name: Nome da coluna
            sheet_name: Nome da planilha (opcional)
        
        Returns:
            List: Valores da coluna
        """
        try:
            df = self.get_all_data(sheet_name)
            
            if column_name not in df.columns:
                raise ValueError(f"Coluna '{column_name}' não encontrada. Colunas disponíveis: {list(df.columns)}")
            
            return df[column_name].tolist()
            
        except Exception as e:
            raise Exception(f"Erro ao obter dados da coluna: {str(e)}")
    
    def refresh_connection(self):
        """Reautentica e atualiza a conexão com Google Sheets"""
        self._authenticate()
