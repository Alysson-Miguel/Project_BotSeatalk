"""
Cliente para interação com Google Sheets API
Suporta leitura de múltiplas abas
"""
import os
import logging
from typing import Optional, Dict
import pandas as pd
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class SheetsClient:
    """Cliente para interagir com Google Sheets"""
    
    # Escopos necessários para a API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        """
        Inicializa o cliente do Google Sheets
        
        Args:
            credentials_path: Caminho para o arquivo de credenciais
        """
        self.credentials_path = credentials_path
        self.service = None
        self.spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
        
        # Dicionário de ranges/abas configuradas
        self.sheet_ranges = {
            'main': os.getenv('GOOGLE_SHEET_RANGE', 'Sheet1!A1:Z1000'),  # Aba principal
            'secondary': os.getenv('GOOGLE_SHEET_RANGE_2', 'Sheet2!A1:Z1000'),  # Segunda aba
        }
        
        self._authenticate()
    
    def _authenticate(self):
        """Autentica com a API do Google Sheets"""
        try:
            logger.info(f"🔐 Autenticando com Google Sheets...")
            logger.info(f"📄 Arquivo de credenciais: {self.credentials_path}")
            
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"Arquivo de credenciais não encontrado: {self.credentials_path}")
            
            # Autenticação com Service Account
            creds = ServiceAccountCredentials.from_service_account_file(
                self.credentials_path, 
                scopes=self.SCOPES
            )
            
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Autenticação bem-sucedida!")
            
        except Exception as e:
            logger.error(f"❌ Erro na autenticação: {str(e)}")
            raise
    
    def get_all_data(self, sheet_key: str = 'main') -> Optional[pd.DataFrame]:
        """
        Busca todos os dados de uma aba específica
        
        Args:
            sheet_key: Chave da aba no dicionário sheet_ranges (default: 'main')
        
        Returns:
            DataFrame com os dados ou None em caso de erro
        """
        try:
            range_name = self.sheet_ranges.get(sheet_key)
            
            if not range_name:
                logger.error(f"❌ Chave '{sheet_key}' não encontrada em sheet_ranges")
                logger.error(f"   Chaves disponíveis: {list(self.sheet_ranges.keys())}")
                return None
            
            logger.info(f"📊 Buscando dados da aba: {sheet_key}")
            logger.info(f"📍 Range: {range_name}")
            logger.info(f"🆔 Spreadsheet ID: {self.spreadsheet_id}")
            
            if not self.spreadsheet_id:
                logger.error("❌ GOOGLE_SHEET_ID não configurado!")
                return None
            
            # Buscar dados do Google Sheets
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning(f"⚠️ Nenhum dado encontrado na aba '{sheet_key}'")
                return pd.DataFrame()
            
            # Converter para DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])
            
            logger.info(f"✅ Dados carregados com sucesso!")
            logger.info(f"   Aba: {sheet_key}")
            logger.info(f"   Linhas: {len(df)}")
            logger.info(f"   Colunas: {len(df.columns)}")
            
            return df
            
        except HttpError as e:
            logger.error(f"❌ Erro HTTP ao acessar Google Sheets: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados: {str(e)}")
            logger.exception("Stack trace:")
            return None
    
    def get_data_from_custom_range(self, range_name: str) -> Optional[pd.DataFrame]:
        """
        Busca dados de um range customizado
        
        Args:
            range_name: Nome do range (ex: 'Sheet1!A1:D10')
        
        Returns:
            DataFrame com os dados ou None em caso de erro
        """
        try:
            logger.info(f"📊 Buscando dados do range customizado: {range_name}")
            
            if not self.spreadsheet_id:
                logger.error("❌ GOOGLE_SHEET_ID não configurado!")
                return None
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning(f"⚠️ Nenhum dado encontrado no range '{range_name}'")
                return pd.DataFrame()
            
            df = pd.DataFrame(values[1:], columns=values[0])
            
            logger.info(f"✅ Dados do range customizado carregados!")
            logger.info(f"   Linhas: {len(df)}")
            logger.info(f"   Colunas: {len(df.columns)}")
            
            return df
            
        except HttpError as e:
            logger.error(f"❌ Erro HTTP ao acessar range: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar range customizado: {str(e)}")
            logger.exception("Stack trace:")
            return None
        
    def get_cell_value(self, range_name: str):
        """Lê uma única célula sem converter para DataFrame"""
        try:
            logger.info(f"📌 Buscando célula: {range_name}")

            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get("values", [])

            if not values or not values[0]:
                logger.warning(f"⚠️ Célula {range_name} está vazia ou não encontrada.")
                return None

            return values[0][0]

        except Exception as e:
            logger.error(f"❌ Erro ao buscar célula {range_name}: {e}")
            return None
    
    def add_sheet_range(self, key: str, range_name: str):
        """
        Adiciona um novo range/aba ao dicionário
        
        Args:
            key: Chave identificadora
            range_name: Range no formato 'Sheet!A1:Z100'
        """
        self.sheet_ranges[key] = range_name
        logger.info(f"✅ Range '{key}' adicionado: {range_name}")
    
    def list_available_sheets(self) -> Dict[str, str]:
        """
        Lista todas as abas/ranges disponíveis
        
        Returns:
            Dicionário com as abas configuradas
        """
        return self.sheet_ranges.copy()
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com o Google Sheets
        
        Returns:
            True se conectado, False caso contrário
        """
        try:
            logger.info("🧪 Testando conexão com Google Sheets...")
            
            result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            title = result.get('properties', {}).get('title', 'Sem título')
            logger.info(f"✅ Conexão OK! Planilha: {title}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Falha na conexão: {str(e)}")
            return False
        

