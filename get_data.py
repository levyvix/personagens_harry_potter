import pandas as pd
import requests
from bs4 import BeautifulSoup


def get_character_info(url):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')

    nome = soup.select(
        'h2.pi-item.pi-item-spacing.pi-title.pi-secondary-background')[0].text
    columns = soup.select('h3.pi-data-label.pi-secondary-font')
    infos = []
    for el in soup.select('div.pi-data-value.pi-font'):

        infos.append(el.text)

    result = pd.DataFrame([infos], columns=[el.text for el in columns])
    result = result.assign(Nome=nome)
    return result


def get_info_from_file(file_name):
    with open(file_name, 'r') as f:
        urls = f.readlines()

    full_df = pd.DataFrame()
    for url in urls:
        url = url.replace('\n', '')
        full_df = pd.concat([full_df, get_character_info(url)])

    return full_df
