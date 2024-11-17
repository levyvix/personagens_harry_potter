import sys

import dlt
import pandas as pd
import pendulum as pend
import requests
from bs4 import BeautifulSoup
from loguru import logger
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
        self.list_of_dicts = []
        self.cache = {}
        self.verified_characters = []
        

    def get_character_info(self, url: str) -> dict:
        """Visita a página de um personagem e retorna as informações da cartão de informações

        Args:
            url (str): o link do site do personagem

        Returns:
            pandas.DataFrame: linha com as informações do personagem
        """

        response = self.cache.get(url, requests.get(url))

        soup = BeautifulSoup(response.text, "html.parser")

        nome = soup.select_one(
            "h2.pi-item.pi-item-spacing.pi-title.pi-secondary-background"
        ).text
        columns = soup.select("h3.pi-data-label.pi-secondary-font")
        column_names = [c.text for c in columns]
        infos = []
        for el in soup.select("div.pi-data-value.pi-font"):
            # if its a list then put a comma between each element
            if len(el.select("li")) > 0:
                infos.append(", ".join([li.text for li in el.select("li")]))
            else:
                infos.append(el.text)

        data = {col: [info] for col, info in zip(column_names, infos)}
        data["Nome"] = nome
        data["url"] = url
        
        self.cache[url] = response
        

        return data

    def have_banner(self, response: requests.Response) -> bool:
        """Vê se o personagem tem um banner de nascimento na página

        Args:
            response (str): link do personagem

        Returns:
            bool: True se o personagem tem um banner de nascimento
        """

        soup = BeautifulSoup(response.text, "html.parser")

        return "Nascimento" in [c.text for c in soup.select("h3.pi-data-label.pi-secondary-font")]

    def have_informacoes_bibliograficas(self, soup):
        """Ver se o personagem tem a caixa de informações biográficas

        Args:
            href (str): link do personagem

        Returns:
            bool: True se o personagem tem a caixa de informações biográficas
        """

        return "Informações biográficas" in [
            c.text
            for c in soup.select(
                "h2.pi-item.pi-header.pi-secondary-font.pi-item-spacing.pi-secondary-background > center"
            )
        ]

    def verify_href(self, href):
        response = self.cache.get(href, requests.get(href))
        soup = BeautifulSoup(response.text, "html.parser")

        self.cache[href] = response
        return (
            href
            if self.have_banner(soup) or self.have_informacoes_bibliograficas(soup)
            else None
        )

    def get_book_info(self, url: str) -> list[str]:
        """Visita a página de um livro e retorna as informações da cartão de informações para cada link <a> que estiver na página,
            dentro de um parágrafo <p>

        Args:
            url (str): link da pagina do livro

        Returns:
            list[str]: lista com os links dos personagens que tem um banner de nascimento ou informações bibliográficas
        """
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        links_personagens = set()

        for a in tqdm(
            soup.select("div.mw-parser-output > p > a"),
            desc=f"Getting book info for {url}",
        ):
            links_personagens.add(a["href"])

        return (
            self.url_personagem_base + link if link.startswith("/") else link
            for link in links_personagens
        )

    def get_data(self) -> None:
        """
        Salva os links dos personagens que tem um banner de nascimento ou informações bibliográficas dentre todos os livros.
        """

        for livro in tqdm(self.url_livros, desc="Getting book info for all books"):
            self.href_personagens += self.get_book_info(livro)
            
            
    def verify_links(self):
        
        self.verified_characters = (
            self.verify_href(href) for href in tqdm(self.href_personagens, desc="Verifying character links...")
        )
        
        self.verified_characters = list(filter(None, self.verified_characters))

    def get_char_data(self) -> None:
        """
        Pega as informações de cada personagem e salva em um DataFrame
        """
        for link_personagem in tqdm(
            self.verified_characters, desc="Getting character info..."
        ):
            try:
                self.list_of_dicts.append(self.get_character_info(link_personagem))

            except Exception as e:
                print("error", e, link_personagem)
                continue

        self.list_of_dicts = (
            pd.DataFrame(self.list_of_dicts)
            .query('Nome != "Joanne Rowling"')
            .drop_duplicates(subset="Nome")
            .to_dict(orient="records")
        )
        logger.info("Got all character info")

    def save_dataframe(self):
        """
        Salva o DataFrame em um arquivo csv, removendo duplicatas e a autora Joanne Rowling (que não é um personagem)
        """
        (
            pd.DataFrame(self.list_of_dicts).to_csv(
                "personagens.csv", index=False, sep=";"
            )
        )

    def save_data_to_duckdb(self):
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


if __name__ == "__main__":
    now = pend.now()

    wiki = WikiCaller()
    wiki.get_data()
    wiki.verify_links()
    wiki.get_char_data()
    wiki.save_dataframe()
    wiki.save_data_to_duckdb()

    # human readable time
    logger.info(f"Data collected and saved in {(pend.now() - now).in_words()}")
