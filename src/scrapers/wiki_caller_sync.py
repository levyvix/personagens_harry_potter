"""Scraper síncrono usando BeautifulSoup."""

import pendulum as pend
import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from .base import BaseWikiCaller

pend.set_locale("en_us")


class WikiCaller(BaseWikiCaller):
    """Scraper síncrono para personagens do Wiki de Harry Potter.

    Usa BeautifulSoup para parsing HTML e requests para fazer requisições HTTP.
    É a versão mais simples e lenta, mas também a mais fácil de entender.
    """

    def __init__(self):
        """Inicializa o scraper síncrono."""
        super().__init__()
        self.setup_logger()
        self.href_personagens = []
        self.verified_characters = []

    def get_character_info(self, url: str) -> dict:
        """Visita a página de um personagem e extrai suas informações.

        Args:
            url: Link da página do personagem

        Returns:
            Dicionário com informações do personagem
        """
        # Usa cache se disponível, senão faz requisição
        if url in self.cache:
            response = self.cache[url]
        else:
            response = requests.get(url)
            self.cache[url] = response

        soup = BeautifulSoup(response.text, "html.parser")

        # Extrai o nome do personagem
        nome = soup.select_one(
            "h2.pi-item.pi-item-spacing.pi-title.pi-secondary-background"
        ).text

        # Extrai os nomes das colunas (ex: "Nascimento", "Espécie")
        columns = soup.select("h3.pi-data-label.pi-secondary-font")
        column_names = []
        for col in columns:
            column_names.append(col.text)

        # Extrai os valores de cada campo
        infos = []
        for el in soup.select("div.pi-data-value.pi-font"):
            # Se tem lista (múltiplos <li>), junta com vírgulas
            list_items = el.select("li")
            if len(list_items) > 0:
                text_parts = []
                for li in list_items:
                    text_parts.append(li.text)
                infos.append(", ".join(text_parts))
            else:
                infos.append(el.text)

        # Monta dicionário com pares coluna:valor
        data = {}
        for col, info in zip(column_names, infos):
            data[col] = [info]

        data["Nome"] = nome
        data["url"] = url

        return data

    def have_banner(self, soup: BeautifulSoup) -> bool:
        """Verifica se o personagem tem banner de nascimento.

        Args:
            soup: Objeto BeautifulSoup com HTML da página

        Returns:
            True se tem banner de "Nascimento"
        """
        labels = soup.select("h3.pi-data-label.pi-secondary-font")

        for label in labels:
            if label.text == "Nascimento":
                return True

        return False

    def have_informacoes_bibliograficas(self, soup: BeautifulSoup) -> bool:
        """Verifica se tem seção de informações biográficas.

        Args:
            soup: Objeto BeautifulSoup com HTML da página

        Returns:
            True se tem seção "Informações biográficas"
        """
        css_selector = (
            "h2.pi-item.pi-header.pi-secondary-font."
            "pi-item-spacing.pi-secondary-background > center"
        )
        headers = soup.select(css_selector)

        for header in headers:
            if header.text == "Informações biográficas":
                return True

        return False

    def verify_href(self, href: str) -> str | None:
        """Verifica se um link é de personagem válido.

        Um personagem é válido se tem banner de nascimento OU informações biográficas.

        Args:
            href: URL para verificar

        Returns:
            A própria URL se for personagem válido, None caso contrário
        """
        # Usa cache se disponível
        if href in self.cache:
            response = self.cache[href]
        else:
            response = requests.get(href)
            self.cache[href] = response

        soup = BeautifulSoup(response.text, "html.parser")

        # Verifica se tem banner OU informações biográficas
        if self.have_banner(soup):
            return href

        if self.have_informacoes_bibliograficas(soup):
            return href

        return None

    def get_book_info(self, url: str) -> list[str]:
        """Extrai links de personagens de uma página de livro.

        Busca todos os links <a> dentro de parágrafos <p> na página.

        Args:
            url: Link da página do livro

        Returns:
            Lista com URLs completas dos personagens
        """
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        links_personagens = set()

        # Busca todos os links dentro de parágrafos
        all_links = soup.select("div.mw-parser-output > p > a")
        for a in tqdm(all_links, desc=f"Getting book info for {url}"):
            href = a.get("href")
            if href:
                links_personagens.add(href)

        # Converte links relativos em absolutos
        complete_links = []
        for link in links_personagens:
            if link.startswith("/"):
                complete_links.append(self.url_personagem_base + link)
            else:
                complete_links.append(link)

        return complete_links

    def get_data(self) -> None:
        """Coleta links de personagens de todos os livros."""
        all_links = []

        for livro in tqdm(self.url_livros, desc="Getting book info for all books"):
            book_links = self.get_book_info(livro)
            all_links.extend(book_links)

        self.href_personagens = all_links

    def verify_links(self):
        """Verifica quais links são de personagens válidos."""
        verified = []

        for href in tqdm(self.href_personagens, desc="Verifying character links..."):
            result = self.verify_href(href)
            if result is not None:
                verified.append(result)

        self.verified_characters = verified

    def get_char_data(self) -> None:
        """Extrai informações de todos os personagens verificados."""
        all_character_data = []

        for link_personagem in tqdm(
            self.verified_characters, desc="Getting character info..."
        ):
            try:
                char_info = self.get_character_info(link_personagem)
                all_character_data.append(char_info)
            except Exception as e:
                logger.error(
                    f"Erro ao extrair dados de {link_personagem}: {e}. "
                    f"Verifique se a estrutura HTML da página mudou."
                )
                continue

        # Limpa dados usando método da classe base
        self.list_of_dicts = self.clean_character_data(all_character_data)
        logger.info("Got all character info")

    def run(self) -> None:
        """Executa o pipeline completo de scraping.

        Passos:
        1. Coleta links dos livros
        2. Verifica quais são personagens válidos
        3. Extrai dados de cada personagem
        4. Salva em CSV e DuckDB
        """
        now = pend.now()

        self.get_data()
        self.verify_links()
        self.get_char_data()
        self.save_to_csv()
        self.save_data_to_duckdb()

        logger.info(f"Data collected and saved in {(pend.now() - now).in_words()}")


if __name__ == "__main__":
    wiki = WikiCaller()
    wiki.run()
