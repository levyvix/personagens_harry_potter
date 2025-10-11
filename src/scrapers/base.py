"""Classe base compartilhada para todos os scrapers do Wiki de Harry Potter."""

import sys
import unicodedata
from abc import ABC, abstractmethod

import dlt
import pandas as pd
from loguru import logger


class BaseWikiCaller(ABC):
    """Classe base abstrata para scrapers do Wiki de Harry Potter.

    Contém todo o código compartilhado entre as três implementações:
    - Configuração de URLs
    - Remoção de acentos
    - Salvamento em CSV e DuckDB
    - Limpeza de dados
    """

    def __init__(self):
        """Inicializa URLs e estruturas de dados comuns."""
        self.url_personagem_base = "https://harrypotter.fandom.com"
        self.url_livros = [
            "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_a_Pedra_Filosofal",
            "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_a_C%C3%A2mara_Secreta",
            "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_o_Prisioneiro_de_Azkaban",
            "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_o_C%C3%A1lice_de_Fogo",
            "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_a_Ordem_da_F%C3%AAnix",
            "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_o_Enigma_do_Pr%C3%ADncipe",
            "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_as_Rel%C3%ADquias_da_Morte",
        ]
        self.list_of_dicts = []
        self.cache = {}

    @staticmethod
    def setup_logger():
        """Configura o logger com formato padrão."""
        logger.remove()
        logger.add(
            sys.stdout,
            colorize=True,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level}</level> | "
                "<level>{message}</level>"
            ),
        )

    def remove_accents(self, text: str) -> str:
        """Remove acentos de um texto.

        Transforma: café -> cafe, São -> Sao, Informações -> Informacoes

        Args:
            text: Texto com possíveis acentos

        Returns:
            Texto sem acentos
        """
        # Normaliza para NFD (decompõe caracteres acentuados)
        normalized = unicodedata.normalize("NFD", text)

        # Remove marcas de combinação (os acentos)
        result = []
        for char in normalized:
            if unicodedata.category(char) != "Mn":
                result.append(char)

        return "".join(result)

    def clean_character_data(self, data: list[dict]) -> list[dict]:
        """Limpa e filtra dados de personagens.

        Remove duplicatas por nome e filtra a autora J.K. Rowling.

        Args:
            data: Lista de dicionários com dados de personagens

        Returns:
            Lista limpa de dicionários
        """
        if not data:
            return []

        df = pd.DataFrame(data)

        # Remove duplicatas mantendo a primeira ocorrência
        df = df.drop_duplicates(subset="Nome", keep="first")

        # Remove a autora (não é um personagem)
        df = df.query('Nome != "Joanne Rowling"')

        return df.to_dict(orient="records")

    def save_to_csv(self, output_path: str = "personagens.csv"):
        """Salva os dados em arquivo CSV.

        Args:
            output_path: Caminho do arquivo CSV a ser criado
        """
        if not self.list_of_dicts:
            logger.warning("Nenhum dado para salvar em CSV")
            return

        df = pd.DataFrame(self.list_of_dicts)
        df.to_csv(output_path, index=False, sep=";")
        logger.info(f"Dados salvos em {output_path}")

    def save_data_to_duckdb(self, db_name: str = "personagens_harry_potter.duckdb"):
        """Salva os dados em banco DuckDB.

        Args:
            db_name: Nome do banco de dados DuckDB
        """
        if not self.list_of_dicts:
            logger.warning("Nenhum dado para salvar no DuckDB")
            return

        pipeline = dlt.pipeline(
            pipeline_name="personagens_harry_potter",
            dataset_name="harry_potter",
            destination="duckdb",
        )

        load_info = pipeline.run(
            data=self.list_of_dicts,
            table_name="personagens",
            write_disposition="replace",
        )

        logger.info(f"Dados carregados no DuckDB: {load_info}")

    @abstractmethod
    def run(self):
        """Executa o pipeline completo de scraping.

        Cada implementação deve definir seu próprio método run().
        """
        pass
