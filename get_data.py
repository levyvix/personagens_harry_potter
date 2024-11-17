

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm.notebook import tqdm



url_personagem_base = "https://harrypotter.fandom.com"


def get_character_info(url):
    """Visita a página de um personagem e retorna as informações da cartão de informações

    Args:
        url (str): o link do site do personagem

    Returns:
        pandas.DataFrame: linha com as informações do personagem
    """

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    nome = soup.select("h2.pi-item.pi-item-spacing.pi-title.pi-secondary-background")[
        0
    ].text
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


def have_banner(response):
    """Vê se o personagem tem um banner de nascimento na página

    Args:
        response (str): link do personagem

    Returns:
        bool: True se o personagem tem um banner de nascimento
    """

    soup = BeautifulSoup(response.text, "html.parser")

    columns = soup.select("h3.pi-data-label.pi-secondary-font")
    return "Nascimento" in [c.text for c in columns]


def have_informacoes_bibliograficas(response):
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


def get_book_info(url):
    """Visita a página de um livro e retorna as informações da cartão de informações para cada link <a> que estiver na página,
        dentro de um parágrafo <p>

    Args:
        url (str): link da pagina do livro

    Returns:
        list[str]: lista com os links dos personagens que tem um banner de nascimento ou informações biográficas
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    links_personagens = []

    for a in tqdm(
        soup.select("div.mw-parser-output > p > a"),
        total=len(soup.select("div.mw-parser-output > p > a")),
    ):
        try:
            response = requests.get(url_personagem_base + a["href"])
        except:
            continue
        if (
            have_banner(response)
            or have_informacoes_bibliograficas(response)
            and (url_personagem_base + a["href"]) not in links_personagens
        ):
            links_personagens.append(a["href"])

    return list(set([url_personagem_base + link for link in links_personagens]))



url_livro1 = (
    "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_a_Pedra_Filosofal"
)
url_livro2 = (
    "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_a_C%C3%A2mara_Secreta"
)
url_livro3 = (
    "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_o_Prisioneiro_de_Azkaban"
)
url_livro4 = (
    "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_o_C%C3%A1lice_de_Fogo"
)
url_livro5 = (
    "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_a_Ordem_da_F%C3%AAnix"
)
url_livro6 = (
    "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_o_Enigma_do_Pr%C3%ADncipe"
)
url_livro7 = "https://harrypotter.fandom.com/pt-br/wiki/Harry_Potter_e_as_Rel%C3%ADquias_da_Morte"

livros = [
    url_livro1,
    url_livro2,
    url_livro3,
    url_livro4,
    url_livro5,
    url_livro6,
    url_livro7,
]

href_personagens = []
for livro in tqdm(livros):
    href_personagens += get_book_info(livro)




# write to file
with open("href_personagens.txt", "w") as f:
    for href in href_personagens:
        f.write(href + "\n")




# read
with open("href_personagens.txt", "r") as f:
    # remove \n
    href_personagens = [line[:-1] for line in f.readlines()]




dataframes_personagem = []
for link_personagem in href_personagens:
    try:
        dataframes_personagem.append(get_character_info(link_personagem))

    except Exception as e:
        print("error", e, link_personagem)
        continue


df_personagens = pd.concat(dataframes_personagem)



(
    df_personagens.drop_duplicates(subset="Nome")
    # drop Joanne Rowling
    .query('Nome != "Joanne Rowling"').to_csv("personagens.csv", index=False)
)
