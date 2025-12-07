"""
Módulo de análise de dados da Shopee
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime


class ShopeeDataAnalyzer:
    """Analisador de dados da Shopee"""
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Inicializa o analisador com um DataFrame
        
        Args:
            dataframe: DataFrame com os dados da Shopee
        """
        self.df = dataframe
        self._validate_dataframe()
    
    def _validate_dataframe(self):
        """Valida se o DataFrame possui dados"""
        if self.df is None or self.df.empty:
            raise ValueError("DataFrame está vazio ou não foi fornecido")
    
    def get_total_quantity(self, product_name: Optional[str] = None, 
                          column_name: str = 'quantidade') -> Union[int, float]:
        """
        Calcula a quantidade total
        
        Args:
            product_name: Nome do produto (opcional, se None calcula total geral)
            column_name: Nome da coluna de quantidade
        
        Returns:
            Total de quantidade
        """
        try:
            if column_name not in self.df.columns:
                # Tenta encontrar coluna similar
                possible_columns = [col for col in self.df.columns 
                                  if 'quant' in col.lower() or 'qty' in col.lower()]
                if possible_columns:
                    column_name = possible_columns[0]
                else:
                    raise ValueError(f"Coluna de quantidade não encontrada. Colunas disponíveis: {list(self.df.columns)}")
            
            if product_name:
                # Busca por produto específico
                product_column = self._find_product_column()
                filtered_df = self.df[self.df[product_column].str.contains(product_name, case=False, na=False)]
                total = filtered_df[column_name].sum()
            else:
                total = self.df[column_name].sum()
            
            return total
            
        except Exception as e:
            raise Exception(f"Erro ao calcular quantidade total: {str(e)}")
    
    def get_weighted_average(self, value_column: str, weight_column: str,
                           filter_column: Optional[str] = None,
                           filter_value: Optional[str] = None) -> float:
        """
        Calcula média ponderada
        
        Args:
            value_column: Coluna com os valores
            weight_column: Coluna com os pesos
            filter_column: Coluna para filtrar (opcional)
            filter_value: Valor do filtro (opcional)
        
        Returns:
            Média ponderada
        """
        try:
            df = self.df.copy()
            
            # Aplica filtro se especificado
            if filter_column and filter_value:
                df = df[df[filter_column].str.contains(filter_value, case=False, na=False)]
            
            if df.empty:
                return 0.0
            
            # Calcula média ponderada
            weighted_sum = (df[value_column] * df[weight_column]).sum()
            total_weight = df[weight_column].sum()
            
            if total_weight == 0:
                return 0.0
            
            return weighted_sum / total_weight
            
        except Exception as e:
            raise Exception(f"Erro ao calcular média ponderada: {str(e)}")
    
    def get_summary_by_product(self, quantity_column: str = 'quantidade',
                              value_column: Optional[str] = None) -> pd.DataFrame:
        """
        Obtém resumo agrupado por produto
        
        Args:
            quantity_column: Nome da coluna de quantidade
            value_column: Nome da coluna de valor (opcional)
        
        Returns:
            DataFrame com resumo por produto
        """
        try:
            product_column = self._find_product_column()
            
            agg_dict = {quantity_column: 'sum'}
            
            if value_column and value_column in self.df.columns:
                agg_dict[value_column] = 'sum'
            
            summary = self.df.groupby(product_column).agg(agg_dict).reset_index()
            summary = summary.sort_values(by=quantity_column, ascending=False)
            
            return summary
            
        except Exception as e:
            raise Exception(f"Erro ao gerar resumo por produto: {str(e)}")
    
    def get_summary_by_period(self, date_column: str, 
                             quantity_column: str = 'quantidade',
                             period: str = 'D') -> pd.DataFrame:
        """
        Obtém resumo agrupado por período
        
        Args:
            date_column: Nome da coluna de data
            quantity_column: Nome da coluna de quantidade
            period: Período de agrupamento ('D'=dia, 'W'=semana, 'M'=mês)
        
        Returns:
            DataFrame com resumo por período
        """
        try:
            df = self.df.copy()
            
            # Converte coluna de data
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            # Remove linhas com datas inválidas
            df = df.dropna(subset=[date_column])
            
            # Agrupa por período
            df.set_index(date_column, inplace=True)
            summary = df[quantity_column].resample(period).sum().reset_index()
            
            return summary
            
        except Exception as e:
            raise Exception(f"Erro ao gerar resumo por período: {str(e)}")
    
    def get_top_products(self, n: int = 10, 
                        quantity_column: str = 'quantidade') -> pd.DataFrame:
        """
        Obtém os N produtos com maior quantidade
        
        Args:
            n: Número de produtos a retornar
            quantity_column: Nome da coluna de quantidade
        
        Returns:
            DataFrame com top N produtos
        """
        try:
            summary = self.get_summary_by_product(quantity_column)
            return summary.head(n)
            
        except Exception as e:
            raise Exception(f"Erro ao obter top produtos: {str(e)}")
    
    def search_product(self, product_name: str) -> pd.DataFrame:
        """
        Busca informações de um produto específico
        
        Args:
            product_name: Nome ou parte do nome do produto
        
        Returns:
            DataFrame com dados do produto
        """
        try:
            product_column = self._find_product_column()
            result = self.df[self.df[product_column].str.contains(product_name, case=False, na=False)]
            
            return result
            
        except Exception as e:
            raise Exception(f"Erro ao buscar produto: {str(e)}")
    
    def get_statistics(self, column_name: str) -> Dict[str, float]:
        """
        Obtém estatísticas descritivas de uma coluna
        
        Args:
            column_name: Nome da coluna
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            if column_name not in self.df.columns:
                raise ValueError(f"Coluna '{column_name}' não encontrada")
            
            stats = {
                'total': float(self.df[column_name].sum()),
                'média': float(self.df[column_name].mean()),
                'mediana': float(self.df[column_name].median()),
                'mínimo': float(self.df[column_name].min()),
                'máximo': float(self.df[column_name].max()),
                'desvio_padrão': float(self.df[column_name].std()),
                'contagem': int(self.df[column_name].count())
            }
            
            return stats
            
        except Exception as e:
            raise Exception(f"Erro ao calcular estatísticas: {str(e)}")
    
    def _find_product_column(self) -> str:
        """
        Encontra a coluna que contém nomes de produtos
        
        Returns:
            Nome da coluna de produto
        """
        possible_names = ['produto', 'product', 'nome', 'name', 'item', 'sku']
        
        for col in self.df.columns:
            if any(name in col.lower() for name in possible_names):
                return col
        
        # Se não encontrar, retorna a primeira coluna
        return self.df.columns[0]
    
    def get_column_names(self) -> List[str]:
        """
        Retorna os nomes de todas as colunas disponíveis
        
        Returns:
            Lista com nomes das colunas
        """
        return list(self.df.columns)
    
    def get_data_preview(self, n: int = 5) -> pd.DataFrame:
        """
        Retorna uma prévia dos dados
        
        Args:
            n: Número de linhas a retornar
        
        Returns:
            DataFrame com primeiras n linhas
        """
        return self.df.head(n)
