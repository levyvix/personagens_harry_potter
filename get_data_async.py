import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from loguru import logger
import sys
import pendulum as pend
from urllib.parse import unquote
import asyncio
import httpx

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
        self.df_personagens = pd.DataFrame()

    def get_character_info(self, response) -> pd.DataFrame:
        """Visita a página de um personagem e retorna as informações da cartão de informações

        Args:
                        url (str): o link do site do personagem

        Returns:
                        pandas.DataFrame: linha com as informações do personagem
        """

        soup = BeautifulSoup(response.text, "html.parser")

        nome = soup.select(
            "h2.pi-item.pi-item-spacing.pi-title.pi-secondary-background"
        )[0].text
        columns = soup.select("h3.pi-data-label.pi-secondary-font")
        infos = []
        for el in soup.select("div.pi-data-value.pi-font"):
            # if its a list then put a comma between each element
            if len(el.select("li")) > 0:
                infos.append(", ".join([li.text for li in el.select("li")]))
            else:
                infos.append(el.text)

        result = pd.DataFrame([infos], columns=[el.text for el in columns])
        # include name
        result = result.assign(Nome=nome)

        # name first
        result = result[["Nome"] + [el.text for el in columns]]

        # clean all columns, removing brackets and numbers like [4]
        for col in result.columns:
            result[col] = result[col].str.replace(r"\[.*\]", "")
            result[col] = result[col].str.strip()

        return result

    def have_banner(self, response) -> bool:
        """Vê se o personagem tem um banner de nascimento na página

        Args:
                        response (str): link do personagem

        Returns:
                        bool: True se o personagem tem um banner de nascimento
        """

        soup = BeautifulSoup(response.text, "html.parser")

        columns = soup.select("h3.pi-data-label.pi-secondary-font")
        return "Nascimento" in [c.text for c in columns]

    def have_informacoes_bibliograficas(self, response):
        """Ver se o personagem tem a caixa de informações biográficas

        Args:
                        href (str): link do personagem

        Returns:
                        bool: True se o personagem tem a caixa de informações biográficas
        """

        soup = BeautifulSoup(response.text, "html.parser")

        columns = soup.select(
            "h2.pi-item.pi-header.pi-secondary-font.pi-item-spacing.pi-secondary-background > center"
        )

        return "Informações biográficas" in [c.text for c in columns]

    async def get_book_info(self, url, client) -> list[str]:
        """Visita a página de um livro e retorna as informações da cartão de informações para cada link <a> que estiver na página,
                        dentro de um parágrafo <p>

        Args:
                        url (str): link da pagina do livro

        Returns:
                        list[str]: lista com os links dos personagens que tem um banner de nascimento ou informações bibliográficas
        """
        response = await client.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        links_personagens = []

        for a in tqdm(
            soup.select("div.mw-parser-output > p > a"),
            # total=len(soup.select("div.mw-parser-output > p > a")),
            desc=f"Getting book info for {unquote(url.split('/')[-1])}",
        ):
            try:
                response = await client.get(self.url_personagem_base + a["href"])
            except Exception as e:
                print(e)
                continue
            if (
                self.have_banner(response)
                or self.have_informacoes_bibliograficas(response)
                and (self.url_personagem_base + a["href"]) not in links_personagens
            ):
                links_personagens.append(a["href"])

        return list(
            set([self.url_personagem_base + link for link in links_personagens])
        )

    async def get_data(self) -> None:
        """
        Salva os links dos personagens que tem um banner de nascimento ou informações bibliográficas dentre todos os livros.
        """

        semaphore = asyncio.Semaphore(10)
        async with httpx.AsyncClient() as client:

            async def safe_get(url):
                async with semaphore:
                    return await client.get(url)

            tasks = [self.get_book_info(url, safe_get) for url in self.url_livros]
            self.href_personagens = await asyncio.gather(*tasks)
            self.href_personagens = [
                item for sublist in self.href_personagens for item in sublist
            ]
            self.href_personagens = list(
                dict.fromkeys(self.href_personagens)
            )  # Remove duplicatas

    def save_href(self) -> None:
        """
        Salva os links dos personagens em um arquivo txt, um por linha
        """
        with open("href_personagens.txt", "w") as f:
            for href in self.href_personagens:
                f.write(href + "\n")

    async def append_dataframes(self) -> None:
        """
        Pega as informações de cada personagem e salva em um DataFrame
        """

        async with httpx.AsyncClient() as client:
            tasks = [client.get(url) for url in self.href_personagens]
            responses = await asyncio.gather(*tasks)

        for response in tqdm(responses, desc="Getting character info..."):
            try:
                self.dataframes_personagem.append(self.get_character_info(response))
            except Exception as e:
                print("error", e, response.url)
                continue

        self.df_personagens = pd.concat(self.dataframes_personagem)

    def save_dataframe(self):
        """
        Salva o DataFrame em um arquivo csv, removendo duplicatas e a autora Joanne Rowling (que não é um personagem)
        """

        if not self.df_personagens.empty:
            (
                self.df_personagens.drop_duplicates(subset="Nome")
                # drop Joanne Rowling
                .query('Nome != "Joanne Rowling"').to_csv(
                    "personagens.csv", index=False
                )
            )


if __name__ == "__main__":

    now = pend.now()

    wiki = WikiCaller()
    asyncio.run(wiki.get_data())
    wiki.save_href()
    asyncio.run(wiki.append_dataframes())
    wiki.save_dataframe()

    # human readable time
    logger.info(f"Data collected and saved in {(pend.now() - now).in_words()}")
