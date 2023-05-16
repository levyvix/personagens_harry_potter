# Personagens de Harry Potter

Web Scraping de personagens da série harry potter

## Como foi feito?

Utilizando a biblioteca BeautifulSoup, foi feito um web scraping no site [Harry Potter Wiki](https://harrypotter.fandom.com/pt-br/wiki/P%C3%A1gina_Principal) para obter os nomes dos personagens da série.

Foi criado um script que faz a requisição para cada página dos 7 livros. Cada página contém um resumo dos acontecimentos e dos personagens que aparecem em cada cena.

Para cada personagem, contém um hyperlink que leva para a página do personagem, onde contém mais informações sobre ele.

## Como executar?
- Clone o repositório
- Instale as dependências
- Execute o script

```bash
git clone
cd harry-potter-characters
pip install -r requirements.txt
python get_data.py
```
