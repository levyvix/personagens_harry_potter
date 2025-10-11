"""Scraper assíncrono usando aiohttp e asyncio."""

import asyncio

import aiohttp
import pendulum as pend
from loguru import logger
from selectolax.lexbor import LexborHTMLParser as HTMLParser
from tqdm.asyncio import tqdm as async_tqdm

from .base import BaseWikiCaller


class WikiCaller(BaseWikiCaller):
    """Scraper assíncrono para personagens do Wiki de Harry Potter.

    Usa aiohttp e asyncio para fazer múltiplas requisições HTTP simultaneamente
    e selectolax para parsing HTML rápido.
    """

    def __init__(self):
        """Inicializa o scraper assíncrono."""
        super().__init__()
        self.setup_logger()
        self.verified_characters = []

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> str:
        """Busca conteúdo de URL com cache.

        Args:
            session: Sessão aiohttp
            url: URL para buscar

        Returns:
            Conteúdo HTML da página
        """
        if url in self.cache:
            return self.cache[url]

        async with session.get(url) as response:
            text = await response.text()
            self.cache[url] = text
            return text

    async def get_book_info(self, session: aiohttp.ClientSession, url: str) -> set[str]:
        """Extrai links de personagens de uma página de livro.

        Args:
            session: Sessão aiohttp
            url: Link da página do livro

        Returns:
            Conjunto com URLs completas dos personagens
        """
        html = await self.fetch(session, url)
        soup = HTMLParser(html)
        links = set()

        # Busca todos os links dentro de parágrafos
        all_links = soup.css("div.mw-parser-output > p > a")
        for a in all_links:
            href = a.attributes.get("href") if hasattr(a, "attributes") else None

            if href and href.startswith("/"):
                links.add(self.url_personagem_base + href)

        return links

    async def verify_href(
        self, session: aiohttp.ClientSession, href: str
    ) -> str | None:
        """Verifica se um link é de personagem válido.

        Um personagem é válido se tem banner de nascimento OU informações biográficas.

        Args:
            session: Sessão aiohttp
            href: URL para verificar

        Returns:
            A própria URL se for personagem válido, None caso contrário
        """
        html = await self.fetch(session, href)
        soup = HTMLParser(html)

        # Verifica se tem banner OU informações biográficas
        if self.have_banner(soup):
            return href

        if self.have_informacoes_bibliograficas(soup):
            return href

        return None

    def have_banner(self, soup: HTMLParser) -> bool:
        """Verifica se o personagem tem banner de nascimento.

        Args:
            soup: Objeto HTMLParser com HTML da página

        Returns:
            True se tem banner de "Nascimento"
        """
        labels = soup.css("h3.pi-data-label.pi-secondary-font")

        for label in labels:
            if label.text() == "Nascimento":
                return True

        return False

    def have_informacoes_bibliograficas(self, soup: HTMLParser) -> bool:
        """Verifica se tem seção de informações biográficas.

        Args:
            soup: Objeto HTMLParser com HTML da página

        Returns:
            True se tem seção "Informações biográficas"
        """
        css_selector = (
            "h2.pi-item.pi-header.pi-secondary-font."
            "pi-item-spacing.pi-secondary-background > center"
        )
        headers = soup.css(css_selector)

        for header in headers:
            if header.text() == "Informações biográficas":
                return True

        return False

    async def get_character_info(
        self, session: aiohttp.ClientSession, url: str
    ) -> dict[str, str | list[str]]:
        """Extrai informações de um personagem.

        Args:
            session: Sessão aiohttp
            url: Link da página do personagem

        Returns:
            Dicionário com informações do personagem
        """
        # Busca HTML (pode estar em cache)
        if url in self.cache:
            html = self.cache[url]
        else:
            html = await self.fetch(session, url)

        self.cache[url] = html

        soup = HTMLParser(html)

        # Extrai o nome do personagem
        nome = soup.css_first(
            "h2.pi-item.pi-item-spacing.pi-title.pi-secondary-background"
        ).text(strip=True)

        # Extrai os nomes das colunas sem acentos
        columns = []
        for col in soup.css("h3.pi-data-label.pi-secondary-font"):
            name_without_accents = self.remove_accents(col.text(strip=True))
            columns.append(name_without_accents)

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
        for column, info in zip(columns, infos):
            data[column] = info

        data["Nome"] = nome
        data["url"] = url

        return data

    async def get_book_data(self):
        """Coleta e verifica links de personagens de todos os livros."""
        logger.info("Fetching character links...")

        async with aiohttp.ClientSession() as session:
            # Busca links de todos os livros em paralelo
            book_links = await async_tqdm.gather(
                *[self.get_book_info(session, url) for url in self.url_livros],
                desc="Fetching links from books...",
            )

            # Junta todos os links removendo duplicatas
            all_links = []
            for links in book_links:
                all_links.extend(links)

            # Remove duplicatas mantendo ordem
            unique_links = []
            seen = set()
            for link in all_links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)

            logger.info("Verifying character links...")

            # Verifica todos os links em paralelo
            verified = await async_tqdm.gather(
                *[self.verify_href(session, href) for href in unique_links],
                desc="Verifying characters links...",
            )

            # Remove valores None
            verified_clean = []
            for link in verified:
                if link is not None:
                    verified_clean.append(link)

            # Remove duplicatas finais
            self.verified_characters = []
            seen = set()
            for link in verified_clean:
                if link not in seen:
                    seen.add(link)
                    self.verified_characters.append(link)

    async def get_char_data(self):
        """Extrai informações de todos os personagens verificados."""
        async with aiohttp.ClientSession() as session:
            data = await async_tqdm.gather(
                *[
                    self.get_character_info(session, url)
                    for url in self.verified_characters
                ],
                desc="Fetching character data...",
            )

            # Limpa dados usando método da classe base
            self.list_of_dicts = self.clean_character_data(data)

    async def run(self) -> None:
        """Executa o pipeline completo de scraping.

        Passos:
        1. Coleta e verifica links de forma assíncrona
        2. Extrai dados de cada personagem de forma assíncrona
        3. Salva em CSV e DuckDB
        """
        now = pend.now()

        await self.get_book_data()
        await self.get_char_data()
        self.save_data_to_duckdb()
        self.save_to_csv()

        logger.info(
            f"Data collected and saved in {(pend.now() - now).in_words(locale='en_us')}"
        )


async def main():
    """Função principal para executar o scraper assíncrono."""
    wiki = WikiCaller()
    await wiki.run()


if __name__ == "__main__":
    asyncio.run(main())
