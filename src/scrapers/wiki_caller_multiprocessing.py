"""Scraper paralelo usando pathos e selectolax."""

from urllib.parse import unquote

import pendulum as pend
import requests
from loguru import logger
from pathos.multiprocessing import ProcessingPool as Pool
from selectolax.lexbor import LexborHTMLParser as HTMLParser
from tqdm import tqdm

from .base import BaseWikiCaller

pend.set_locale("en_us")


class WikiCaller(BaseWikiCaller):
    """Scraper paralelo para personagens do Wiki de Harry Potter.

    Usa pathos.multiprocessing para processar múltiplas páginas simultaneamente
    e selectolax para parsing HTML mais rápido que BeautifulSoup.
    """

    def __init__(self):
        """Inicializa o scraper paralelo."""
        super().__init__()
        self.setup_logger()
        self.href_personagens = []
        self.verified_characters = []
        self.session = requests.Session()

    def get_book_info(self, url: str) -> list[str]:
        """Extrai links de personagens de uma página de livro.

        Args:
            url: Link da página do livro

        Returns:
            Lista com URLs completas dos personagens
        """
        response = self.session.get(url)
        soup = HTMLParser(response.text)

        links = set()

        # Busca todos os links dentro de parágrafos
        all_links = soup.css("div.mw-parser-output > p > a")
        for a in tqdm(
            all_links,
            desc=f"Getting book info for {unquote(url.split('/')[-1])}",
        ):
            href = a.attributes.get("href") if hasattr(a, "attributes") else None

            if href and href.startswith("/"):
                links.add(self.url_personagem_base + href)

        return list(links)

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
            response = self.session.get(href)
            self.cache[href] = response

        # Verifica se tem banner OU informações biográficas
        if self.have_banner(response):
            return href

        if self.have_informacoes_bibliograficas(response):
            return href

        return None

    def get_character_info(self, url: str) -> dict:
        """Visita a página de um personagem e extrai suas informações.

        Args:
            url: Link da página do personagem

        Returns:
            Dicionário com informações do personagem
        """
        # Usa cache se disponível
        if url in self.cache:
            response = self.cache[url]
        else:
            response = self.session.get(url)

        soup = HTMLParser(response.text)

        # Extrai o nome do personagem
        nome = soup.css_first(
            "h2.pi-item.pi-item-spacing.pi-title.pi-secondary-background"
        ).text(strip=True)

        # Extrai os nomes das colunas sem acentos
        column_names = []
        for col in soup.css("h3.pi-data-label.pi-secondary-font"):
            name_without_accents = self.remove_accents(col.text(strip=True))
            column_names.append(name_without_accents)

        # Extrai os valores de cada campo
        infos = []
        for el in soup.css("div.pi-data-value.pi-font"):
            # Se tem lista (múltiplos <li>), converte para lista
            list_items = el.css("li")
            if list_items:
                item_texts = []
                for li in list_items:
                    item_texts.append(li.text(strip=True))
                infos.append(item_texts)
            else:
                infos.append([el.text()])

        # Monta dicionário com pares coluna:valor
        data = {}
        for column, info in zip(column_names, infos):
            data[column] = info

        data["Nome"] = nome
        data["url"] = url

        return data

    def have_banner(self, response: requests.Response) -> bool:
        """Verifica se o personagem tem banner de nascimento.

        Args:
            response: Resposta HTTP da página

        Returns:
            True se tem banner de "Nascimento"
        """
        soup = HTMLParser(response.text)
        labels = soup.css("h3.pi-data-label.pi-secondary-font")

        for label in labels:
            if label.text() == "Nascimento":
                return True

        return False

    def have_informacoes_bibliograficas(self, response: requests.Response) -> bool:
        """Verifica se tem seção de informações biográficas.

        Args:
            response: Resposta HTTP da página

        Returns:
            True se tem seção "Informações biográficas"
        """
        soup = HTMLParser(response.text)

        css_selector = (
            "h2.pi-item.pi-header.pi-secondary-font."
            "pi-item-spacing.pi-secondary-background > center"
        )
        headers = soup.css(css_selector)

        for header in headers:
            if header.text() == "Informações biográficas":
                return True

        return False

    def get_data(self) -> None:
        """Coleta e verifica links de personagens de todos os livros em paralelo."""
        logger.info("Getting book info...")

        with Pool() as pool:
            # Processa todos os livros em paralelo
            all_book_links = pool.map(self.get_book_info, self.url_livros)

            logger.info("Flattening all the hrefs from all books...")

            # Junta todos os links e remove duplicatas
            all_links = []
            for book_links in all_book_links:
                all_links.extend(book_links)

            # Remove duplicatas mantendo ordem
            unique_links = []
            seen = set()
            for link in all_links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)

            self.href_personagens = unique_links

            logger.info("Verifying hrefs...")

            # Verifica todos os links em paralelo
            verified = pool.map(self.verify_href, self.href_personagens)

            logger.success("Verified all characters")

        # Remove valores None
        self.verified_characters = []
        for link in verified:
            if link is not None:
                self.verified_characters.append(link)

    def get_char_data(self) -> None:
        """Extrai informações de todos os personagens em paralelo."""
        logger.info("Getting character info for all verified characters...")

        with Pool() as pool:
            data = pool.map(self.get_character_info, self.verified_characters)

        # Limpa dados usando método da classe base
        self.list_of_dicts = self.clean_character_data(data)

    def run(self) -> None:
        """Executa o pipeline completo de scraping.

        Passos:
        1. Coleta e verifica links em paralelo
        2. Extrai dados de cada personagem em paralelo
        3. Salva em CSV e DuckDB
        """
        now = pend.now()

        self.get_data()
        self.get_char_data()
        self.save_to_csv()
        self.save_data_to_duckdb()

        logger.info(f"Data collected and saved in {(pend.now() - now).in_words()}")


if __name__ == "__main__":
    wiki = WikiCaller()
    wiki.run()
