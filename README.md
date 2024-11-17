# Personagens de Harry Potter

Web Scraping de personagens da série Harry Potter.

## Como foi feito?

Utilizando a biblioteca BeautifulSoup, foi feito um web scraping no site [Harry Potter Wiki](https://harrypotter.fandom.com/pt-br/wiki/P%C3%A1gina_Principal) para obter os nomes dos personagens da série.

Foi criado um script que faz a requisição para cada página dos 7 livros. Cada página contém um resumo dos acontecimentos e dos personagens que aparecem em cada cena.

Para cada personagem, contém um hyperlink que leva para a página do personagem, onde contém mais informações sobre ele.

## Como executar?

- Clone o repositório
- Instale as dependências
- Execute o script

```bash
git clone https://github.com/levyvix/personagens_harry_potter.git
cd personagens_harry_potter
python -m pip install -r requirements.txt
python get_data.py
```

Vai ser criado um arquivo chamado `personagens.csv` com os dados obtidos.

Lembre-se que os dados ainda precisam ser limpos e tratados para serem utilizados em um projeto.

### Versão com multiprocessamento

Para obter os dados mais rapidamente, foi criado um script que utiliza multiprocessamento para fazer as requisições de forma paralela.

> ⚠️ **CUIDADO:** Este script utiliza todos os núcleos do seu processador. Se você tiver um processador com muitos núcleos, pode ser que o site bloqueie o seu IP por fazer muitas requisições em um curto espaço de tempo.

Para executar o script com multiprocessamento, execute o seguinte comando:

```bash
python get_data_multiprocessing.py
```
