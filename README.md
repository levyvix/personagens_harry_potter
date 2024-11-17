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

### Comparação de velocidade

Processador: Ryzen 5 5500

Memória: 16GB

- NORMAL: 5 minutes 32 seconds

- MULTITHREAD:  3 minutes 21 seconds

- MULTIPROCESS: 1 minute 13 seconds

- ASYNCIO: 3 minutes
