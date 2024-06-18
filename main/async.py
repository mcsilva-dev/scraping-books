import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import pandas as pd
import re



URL = 'https://novatec.com.br/'

SUBLINKS = []

SUBPAGES = []

BOOKS = {
    'Título': [],
    'Descrição': [],
    'ISBN': [],
    'Páginas': [],
    'Ano': [],
    'Preço': []
}


async def set_book(soup):
    await asyncio.sleep(1)
    if soup.h1 is not None:
        BOOKS['Título'].append(soup.h1.text)
    else:
        BOOKS['Título'].append('')
    if soup.find('div', {'id':'menos'}) is not None:
        BOOKS['Descrição'].append(soup.find('div', {'id':'menos'}).text.replace('\n', '').strip().replace('\r',''))
    else:
        BOOKS['Descrição'].append('')
    if soup.find('span', {'itemprop':'isbn'}) is not None:
        BOOKS['ISBN'].append(soup.find('span', {'itemprop':'isbn'}).text)
    else:
        BOOKS['ISBN'].append('')
    if soup.find('span', {'class': 'style7'}) is not None:
        BOOKS['Páginas'].append(soup.find('span', {'class': 'style7'}).text.replace('\r\n', '').split()[-1])
    else:
        BOOKS['Páginas'].append('')
    if soup.find('span', {'class': 'style7'}) is not None:
        BOOKS['Ano'].append(soup.find('span', {'class': 'style7'}).text.replace('\r\n', '').split()[-3])
    else:
        BOOKS['Ano'].append('')
    if soup.find('span', {'itemprop': 'price'}) is not None:
        BOOKS['Preço'].append(soup.find('span', {'itemprop': 'price'}).text.replace('\r\n', '').split()[-1])
    else:
        BOOKS['Preço'].append('')


async def get_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

        
async def get_bsobject(url):
    html = await get_html(url)
    return BeautifulSoup(html, 'html.parser')


async def get_gendersmenu(soup):
    return [categoria.a.text for categoria in soup.find_all('td', {'class':'menu_lateral'})]


async def get_menulinks(soup):
    return [categoria.a['href'] for categoria in soup.find_all('td', {'class':'menu_lateral'})]


async def get_sublinks(soup):
    SUBLINKS.extend([link['href'] for link in soup.find_all('a', href=re.compile(r'^(livros\/).*$')) if link['href'] not in SUBLINKS])


async def get_subpages(soup):
    SUBPAGES.extend([pages['href'] for pages in soup.find_all('a', href=re.compile(r'^(lista\.php\?id).*$'))[:-1] if pages['href'] not in SUBPAGES])


async def main():
    event = asyncio.get_event_loop()
    soup = await get_bsobject(URL)
    links = await event.create_task(get_menulinks(soup))
    sublinks_soups = await asyncio.gather(*[get_bsobject(link) for link in links])
    await asyncio.gather(*[get_subpages(soup) for soup in sublinks_soups])
    subpages_soups = await asyncio.gather(*[get_bsobject(URL + page) for page in SUBPAGES])
    await asyncio.gather(*[get_sublinks(soup) for soup in subpages_soups])
    total = len(SUBLINKS)
    count = 0
    books_soups = []
    # controlando o numero de requisições para nao causar erro 504.
    while count <= (total - 100):
        books_soups.extend(await asyncio.gather(*[get_bsobject(URL + sublink) for sublink in SUBLINKS[count:count+100]]))
        count += 100
    books_soups.extend(await asyncio.gather(*[get_bsobject(URL + sublink) for sublink in SUBLINKS[count:]]))
    await asyncio.gather(*[set_book(soup) for soup in books_soups])

if __name__ == '__main__':
    asyncio.run(main())
    try:
        df = pd.DataFrame(BOOKS)
        df.sort_values(by='Título')
        df.drop_duplicates()
        df.to_excel('books.xlsx', index=False)
    except Exception as e:
        with open('books.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(BOOKS, ensure_ascii=False))