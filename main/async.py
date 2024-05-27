
from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
import re
import asyncio
from datetime import datetime

NOW = datetime.now()

URL = 'https://novatec.com.br/'

BOOKS = {
    'Título': [],
    'Descrição': [],
    'Gênero': [],
    'ISBN': [],
    'Páginas': [],
    'Preço': [],
    'Link': []
}

async def set_title(soup):
    if soup.find('h1') is not None:
        BOOKS['Título'].append(
            soup.find('h1').get_text()
        )
    else: 
        BOOKS['Título'].append("")
    

async def set_description(soup):
    if soup.find('div', {'id':'menos'}) is not None:
        BOOKS['Descrição'].append(
            soup.find('div', {'id':'menos'}).text.replace('\n', '').strip().replace('\r', '')
        )
    else:
        BOOKS['Descrição'].append("")


async def set_isbn(soup):
    if soup.find('span', {'itemprop':'isbn'}) is not None:
        BOOKS['ISBN'].append(
            soup.find('span', {'itemprop':'isbn'}).get_text()
        )
    else:
        BOOKS['ISBN'].append("")
        


async def set_pages(soup):
    if soup.find('span', {'class':'style7'}) is not None:
        BOOKS['Páginas'].append(
            soup.find('span', {'class':'style7'}).get_text().replace('\r', '').replace('\t','').strip().split()[-1]
        )
    else:
        BOOKS['Páginas'].append("")
    

async def set_price(soup):
    if  soup.find('span', {'itemprop':'price'}) is not None:
        BOOKS['Preço'].append(
            soup.find('span', {'itemprop':'price'}).get_text()
        )
    else:
        BOOKS['Preço'].append("")


async def set_gender(genders, index):
    BOOKS['Gênero'].append(genders['genero'][index])
    

async def set_link(link):
    BOOKS['Link'].append(link)


async def get_books(page, url, index, genders):
    event = asyncio.get_event_loop()
    urls = await event.create_task(get_urls(page, event))
    for link in urls:
        link = url + link
        soup = await event.create_task(get_html(link, event))
        event.create_task(set_title(soup))
        event.create_task(set_description(soup))
        event.create_task(set_isbn(soup))
        event.create_task(set_pages(soup))
        event.create_task(set_price(soup))
        event.create_task(set_gender(genders, index))
        event.create_task(set_link(link))
        

async def get_urls(url, event):
    soup = await event.create_task(get_html(url, event))
    urls = []
    [urls.append(x["href"]) for x in soup.find_all("a", href=re.compile('^(livros/).*$')) if x["href"] not in urls]
    return urls
    

async def get_pages(soup):
    return [x['href'] for x in soup.find_all('a', href = re.compile('^(lista\\.php\\?)*.*$'))[:-1]]


async def get_gender(soup):
    return [x.a.get_text() for x in soup.find_all('td',{'class':'menu_lateral'})]


async def get_links(soup):
    return [x.a['href'] for x in soup.find_all('td',{'class':'menu_lateral'})]
    
    
async def get_gendersdict(soup, event):
    genderdict = {
        'genero': await get_gender(soup),
        'link': await get_links(soup)
    }
    return genderdict

async def get_soupobject(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup


async def get_html(url, event):
    html = urlopen(URL)
    return await event.create_task(get_soupobject(html))  


async def main():
    # Capturando o event loop
    event = asyncio.get_event_loop()
    # Recebendo o objeto BeautifulSoup da primeira pagina do site.
    soup = await event.create_task(get_html(URL, event))
    # Capturando os links e nomes das categorias
    genders = await get_gendersdict(soup, event)
    # Após obtido link de todas as categorias vamos entrar em cada uma delas e capturar todos os livros
    for index, link in enumerate(genders["link"]):
        soup, pages = await asyncio.gather(
            event.create_task(get_html(link, event)),
            event.create_task(get_pages(soup))
        )
        if pages is not None and len(pages) > 0:
            new_url = URL + link
            print(f"acessando: {new_url}")
            await asyncio.gather(get_books(soup, new_url, index, genders))
        else:
            print(f"acessando: {link}")
            await asyncio.gather(get_books(soup, new_url, index, genders))


asyncio.run(main())


df = pd.DataFrame(BOOKS)
df.sort_values(by='Título')
df.drop_duplicates()
df.to_excel('books.xlsx', index=False)
print(datetime.now()-NOW)