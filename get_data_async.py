import asyncio
import sys
import unicodedata
from itertools import chain
from typing import Optional
from urllib.parse import unquote

import aiohttp
import dlt
import pandas as pd
import pendulum as pend
from loguru import logger
from selectolax.lexbor import LexborHTMLParser as HTMLParser
from tqdm.asyncio import tqdm as async_tqdm

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
)

class WikiCaller:
    """Class to fetch Harry Potter characters from the Harry Potter Wiki."""
    def __init__(self):
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
        self.verified_characters = []
        self.cache = {}
        self.list_of_dicts = []

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch URL content asynchronously with caching."""
        if url in self.cache:
            return self.cache[url]

        async with session.get(url) as response:
            text = await response.text()
            self.cache[url] = text
            return text

    async def get_book_info(
        self, session: aiohttp.ClientSession, url: str
    ) -> list[str]:
        """Fetch character links from a book page."""
        html = await self.fetch(session, url)
        soup = HTMLParser(html)
        return {
                self.url_personagem_base + a.attributes["href"]
                if a.attributes["href"].startswith("/")
                else a.attributes["href"]
                for a in soup.css("div.mw-parser-output > p > a")
            }
        

    async def verify_href(
        self, session: aiohttp.ClientSession, href: str
    ) -> Optional[str]:
        """Check if the character page contains relevant information."""
        html = await self.fetch(session, href)
        soup = HTMLParser(html)
        return (
            href
            if self.have_banner(soup) or self.have_informacoes_bibliograficas(soup)
            else None
        )

    def have_banner(self, soup: HTMLParser) -> bool:
        """Check if the page has a banner."""
        return "Nascimento" in {
            c.text() for c in soup.css("h3.pi-data-label.pi-secondary-font")
        }

    def have_informacoes_bibliograficas(self, soup: HTMLParser) -> bool:
        """Check if the page has bibliographic information."""
        return "Informações biográficas" in {
            c.text()
            for c in soup.css(
                "h2.pi-item.pi-header.pi-secondary-font.pi-item-spacing.pi-secondary-background > center"
            )
        }

    def remove_accents(self, text):
        """Get the text without accents. ç -> c, á -> a, etc."""
        return "".join(
            char
            for char in unicodedata.normalize("NFD", text)
            if unicodedata.category(char) != "Mn"
        )

    async def get_character_info(
        self, session: aiohttp.ClientSession, url: str
    ) -> dict[str, str]:
        """Fetch character information from a character page."""

        if self.cache.get(url):
            html = self.cache[url]
        else:
            html = await self.fetch(session, url)

        self.cache[url] = html

        soup = HTMLParser(html)

        nome = soup.css_first(
            "h2.pi-item.pi-item-spacing.pi-title.pi-secondary-background"
        ).text(strip=True)

        columns = [
            self.remove_accents(c.text(strip=True))
            for c in soup.css("h3.pi-data-label.pi-secondary-font")
        ]

        infos = [
            [li.text(strip=True) for li in el.css("li")]
            if el.css("li")
            else [el.text()]
            for el in soup.css("div.pi-data-value.pi-font")
        ]

        data = {column: info for column, info in zip(columns, infos)}
        data["Nome"] = nome
        data["url"] = url

        return data

    async def get_data(self):
        """Collect character links."""
        logger.info("Fetching character links...")
        async with aiohttp.ClientSession() as session:
            book_links = await async_tqdm.gather(
                *[self.get_book_info(session, url) for url in self.url_livros],
                desc="Fetching links from books...",
            )
            character_links = chain.from_iterable(book_links)

            logger.info("Verifying character links...")
            verified = await async_tqdm.gather(
                *[self.verify_href(session, href) for href in character_links],
                desc="Verifying characters links...",
            )
            self.verified_characters = dict.fromkeys(list(filter(None, verified)))

    async def get_char_data(self):
        """Fetch data for all verified characters."""
        async with aiohttp.ClientSession() as session:
            data = await async_tqdm.gather(
                *[
                    self.get_character_info(session, url)
                    for url in self.verified_characters
                ],
                desc="Fetching character data...",
            )
            
            # remove duplicate names
            
            self.list_of_dicts = pd.DataFrame(data).drop_duplicates(subset="Nome").query(
                'Nome != "Joanne Rowling"'
            ).to_dict(orient="records")
            

    def save_data_to_duckdb(self):
        """Save the dataframe to a duckdb database."""

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
        logger.info(load_info)

    def save_to_csv(self):
        """Save the dataframe to a csv file."""
        pd.DataFrame(self.list_of_dicts).to_csv("personagens.csv", index=False, sep=";")


async def main():
    now = pend.now()
    wiki = WikiCaller()
    await wiki.get_data()
    await wiki.get_char_data()
    wiki.save_data_to_duckdb()
    wiki.save_to_csv()

    logger.info(
        f"Data collected and saved in {(pend.now() - now).in_words(locale='en_us')}"
    )


if __name__ == "__main__":
    asyncio.run(main())
