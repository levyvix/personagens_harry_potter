import sys
import unicodedata
from itertools import chain, filterfalse
from typing import Optional
from urllib.parse import unquote

import dlt
import pandas as pd
import pendulum as pend
import requests
from loguru import logger
from pathos.multiprocessing import ProcessingPool as Pool
from selectolax.lexbor import LexborHTMLParser as HTMLParser
from tqdm import tqdm

pend.set_locale("en_us")

logger.remove()

logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
)


class WikiCaller:
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
        self.href_personagens = []
        self.dataframes_personagem = []
        self.cache = {}
        self.verified_characters = []
        self.session = requests.Session()
        self.list_of_dicts = []

    def get_book_info(self, url: str) -> list[str]:
        """Visita a página de um livro e retorna as informações da cartão de informações para cada link <a> que estiver na página,
                dentro de um parágrafo <p>

        Args:
                url (str): link da pagina do livro

        Returns:
                list[str]: lista com os links dos personagens que tem um banner de nascimento ou informações bibliográficas
        """
        response = self.session.get(url)
        soup = HTMLParser(response.text)

        return list(
            {
                self.url_personagem_base + a.attributes["href"]
                if a.attributes["href"].startswith("/")
                else a.attributes["href"]
                for a in tqdm(
                    soup.css("div.mw-parser-output > p > a"),
                    desc=f"Getting book info for {unquote(url.split('/')[-1])}",
                )
            }
        )

    def verify_href(self, href: str) -> Optional[str]:
        """
        Verifica um `href` informado, fazendo uma requisição GET e armazenando o resultado na cache.
        Se o personagem tem um banner de nascimento ou informações bibliográficas, o `href` é retornado

        Args:
            href (str): The URL to verify.

        Returns:
            Optional[str]: The `href` if the character has a banner or bibliographic info, otherwise `None`.
        """
        response = self.cache.get(href, self.session.get(href))

        self.cache[href] = response

        return (
            href
            if self.have_banner(response) or self.have_informacoes_bibliograficas(response)
            else None
        )

    def remove_accents(self, text):
        return "".join(
            char
            for char in unicodedata.normalize("NFD", text)
            if unicodedata.category(char) != "Mn"
        )

    def get_character_info(self, url: str) -> dict[str, str]:
        """Visita a página de um personagem e retorna as informações da cartão de informações

        Args:
            url (str): o link do site do personagem

        Returns:
            pandas.DataFrame: linha com as informações do personagem
        """

        response = self.cache.get(url, self.session.get(url))

        soup = HTMLParser(response.text)

        nome = soup.css_first(
            "h2.pi-item.pi-item-spacing.pi-title.pi-secondary-background"
        ).text(strip=True)

        column_names = [
            self.remove_accents(c.text(strip=True))
            for c in soup.css("h3.pi-data-label.pi-secondary-font")
        ]

        infos = [
            [li.text(strip=True) for li in el.css("li")]
            if el.css("li")
            else [el.text()]
            for el in soup.css("div.pi-data-value.pi-font")
        ]

        data = {column: info for column, info in zip(column_names, infos)}
        data["Nome"] = nome
        data["url"] = url

        return data

    def have_banner(self, response: requests.Response) -> bool:
        """Vê se o personagem tem um banner de nascimento na página

        Args:
            response (str): link do personagem

        Returns:
            bool: True se o personagem tem um banner de nascimento
        """

        soup = HTMLParser(response.text)
    
        return "Nascimento" in {
            c.text() for c in soup.css("h3.pi-data-label.pi-secondary-font")
        }

    def have_informacoes_bibliograficas(self, response: requests.Response) -> bool:
        """Ver se o personagem tem a caixa de informações biográficas

        Args:
            response (requests.Response): link do personagem

        Returns:
            bool: True se o personagem tem a caixa de informações biográficas
        """

        soup = HTMLParser(response.text)

        return "Informações biográficas" in {
            c.text()
            for c in soup.css(
                "h2.pi-item.pi-header.pi-secondary-font.pi-item-spacing.pi-secondary-background > center"
            )
        }

    def get_data(self) -> None:
        """
        Salva os links dos personagens que tem um banner de nascimento ou informações bibliográficas dentre todos os livros.
        """

        logger.info("Getting book info...")

        with Pool() as pool:
            self.href_personagens = pool.map(self.get_book_info, self.url_livros)

            logger.info("Flattening all the hrefs from all books...")

            self.href_personagens = chain.from_iterable(self.href_personagens)
            self.href_personagens = dict.fromkeys(self.href_personagens)

            logger.info(f"Verifying hrefs...")

            self.verified_characters = pool.map(self.verify_href, self.href_personagens)

            logger.success("Verified all characters")

        self.verified_characters = list(
            filterfalse(lambda x: x is None, self.verified_characters)
        )

    def get_char_data(self) -> None:
        """
        Pega as informações de cada personagem e salva em um DataFrame
        """

        logger.info("Getting character info for all verified characters...")
        with Pool() as pool:
            data = pool.map(
                self.get_character_info, self.verified_characters
            )

        self.list_of_dicts = pd.DataFrame(data).drop_duplicates(subset="Nome").query(
                'Nome != "Joanne Rowling"'
            ).to_dict(orient="records")

    def save_to_csv(self):
        """Save the dataframe to a csv file."""
        pd.DataFrame(self.list_of_dicts).to_csv("personagens.csv", index=False, sep=";")

    def save_data_to_duckdb(self):
        """Save the dataframe to a duckdb database."""

        pipeline = dlt.pipeline(
            pipeline_name="personagens_harry_potter",
            dataset_name="harry_potter",
            destination="duckdb",
        )

        pipeline.run(
            data=self.list_of_dicts,
            table_name="personagens",
            write_disposition="replace",
        )

if __name__ == "__main__":
    now = pend.now()

    wiki = WikiCaller()
    wiki.get_data()
    wiki.get_char_data()
    wiki.save_to_csv()
    wiki.save_data_to_duckdb()

    # human readable time
    logger.info(f"Data collected and saved in {(pend.now() - now).in_words()}")
