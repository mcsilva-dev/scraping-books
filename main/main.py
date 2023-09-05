from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
import re

url = 'https://novatec.com.br/'
html = urlopen(url)
soup = BeautifulSoup(html, 'html.parser')
books = {
    'Título': [],
    'Descrição': [],
    'Gênero': [],
    'ISBN': [],
    'Páginas': [],
    'Preço': [],
    'Link': []
}
gender = {
    'genero': [x.a.get_text() for x in soup.find_all('td',{'class':'menu_lateral'})],
    'link': [x.a['href'] for x in soup.find_all('td',{'class':'menu_lateral'})]
}

def check_pages(soup):
    return [x['href'] for x in bs.find_all('a', href = re.compile('^(lista\.php\?).*$'))[:-1]]

def get_urls(url):
    bs = BeautifulSoup(urlopen(url), 'html')
    urls = []
    for x in bs.find_all('a', href = re.compile('^(livros/).*$')):
        if x['href'] not in urls:
            urls.append(x['href'])
    return urls

def get_books(page, url, indice):

    urls = get_urls(page)

    for link in urls:
        link = url+link
        
        print(link)
        
        bs = BeautifulSoup(urlopen(link), 'html.parser')
        title = bs.find('h1').get_text()
        description = bs.find('div', {'id':'menos'}).text.replace('\n', '').strip().replace('\r', '')
        isbn = bs.find('span', {'itemprop':'isbn'}).get_text()
        pages = bs.find('span', {'class':'style7'}).get_text().replace('\r', '').replace('\t','').strip().split()[-1]
        price = bs.find('span', {'itemprop':'price'}).get_text()

        books['Título'].append(title)
        books['Descrição'].append(description)
        books['Gênero'].append(gender['genero'][indice])
        books['ISBN'].append(isbn)
        books['Páginas'].append(pages)
        books['Preço'].append(price)
        books['Link'].append(link)

        print(f"Livro: {title}\n"
              f"Descrição: {description}\n"
              f"Genero: {gender['genero'][indice]}\n"
              f"ISBN: {isbn}\n"
              f"Páginas: {pages}\n"
              f"Preço: {price}\n\n\n")
        
        

    

for indice, link in enumerate(gender['link']):
    bs = BeautifulSoup(urlopen(link), 'html.parser')
    pages = check_pages(bs)

    if pages is not None:
        if len(pages) > 0:
            for link in pages:
                new_url = url + link
                print(f"acessando: {new_url}")
                get_books(new_url, url, indice)
    else:
        print(f"acessando: {link}")
        get_books(link, url, indice)


df = pd.DataFrame(books)
df.sort_values(by='Título')
df.drop_duplicates()
df.to_excel('livros.xlsx', index=False)