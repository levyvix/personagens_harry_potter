#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm.notebook import tqdm


# In[2]:


def get_character_info(url):
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

    return result


# In[5]:


url_personagem_base = "https://harrypotter.fandom.com"


def have_banner(href):
    try:
        response = requests.get(url_personagem_base + href)
    except:
        return False

    soup = BeautifulSoup(response.text, "html.parser")

    columns = soup.select("h3.pi-data-label.pi-secondary-font")
    if "Nascimento" in [c.text for c in columns]:
        return True
    else:
        return False


def have_informacoes_bibliograficas(href):
    try:
        response = requests.get(url_personagem_base + href)
    except:
        return False

    soup = BeautifulSoup(response.text, "html.parser")

    columns = soup.select(
        "h2.pi-item.pi-header.pi-secondary-font.pi-item-spacing.pi-secondary-background > center"
    )

    if "Informações biográficas" in [c.text for c in columns]:
        return True
    else:
        return False


def get_book_info(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # get all hrefs inside paragraphs <p> that have a <a> inside

    links_personagens = []

    # for p in tqdm(soup.select('p')):
    for a in tqdm(soup.select("div.mw-parser-output > p > a")):
        # print(a.text, a['href'])
        # see if the link is a character
        if (
            have_banner(a["href"])
            or have_informacoes_bibliograficas(a["href"])
            and (url_personagem_base + a["href"]) not in links_personagens
        ):
            # print('achou', a['href'])
            links_personagens.append(a["href"])

    return list(set([url_personagem_base + link for link in links_personagens]))


# In[21]:


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


# In[ ]:


with open("href_personagens.txt", "w") as f:
    for href in href_personagens:
        f.write(href + "\n")


# In[8]:


# read

with open("href_personagens.txt", "r") as f:
    # remove \n
    href_personagens = [line[:-1] for line in f.readlines()]


# In[10]:


dataframes_personagem = []
for link_personagem in href_personagens:
    try:
        dataframes_personagem.append(get_character_info(link_personagem))

    except:
        print("error")
        continue


df_personagens = pd.concat(dataframes_personagem)


# In[14]:


(
    df_personagens.drop_duplicates(subset="Nome")
    # drop Joanne Rowling
    .query('Nome != "Joanne Rowling"')
).to_csv("personagens.csv", index=False)
