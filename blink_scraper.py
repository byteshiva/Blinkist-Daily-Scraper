# coding: utf-8
from bs4 import BeautifulSoup
from slugify import slugify # added to remove spaces between strings 
from datetime import datetime
import os
import tomd
import urllib3



headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15'}
http = urllib3.PoolManager(10, headers = headers)
urllib3.disable_warnings()

def get_element_from_request(url, element, class_):
    response = http.request('GET', url)
    soup = BeautifulSoup(response.data.decode('utf-8'), "html5lib")
    return soup.find(element, class_ = class_)

# Get meta data
container = get_element_from_request('https://www.blinkist.com/nc/daily', 'div', "daily-book__container")

title = container.find('h3', 'daily-book__headline').string.strip()
author = container.find('div', 'daily-book__author').string.strip()
# description = container.find('div', 'dailyV2__free-book__description').string.strip()
description_html = container.find('div', 'book-tabs__content-inner')
description = tomd.convert(str(description_html).strip())

cta = container.find('a', 'daily-book__cta').get('href')
img_url = container.find('img')['src']
# Get actual content
article = get_element_from_request(f'https://www.blinkist.com{cta}', 'article', 'shared__reader__blink reader__container__content')

# Convert to markdown, add source and dump to a file
output = f'![{title}]({img_url})\n# {title}\n*{author}*\n\n>{description}\n\n{tomd.convert(str(article).strip())}\n\nSource: [{title} by {author}](https://www.blinkist.com{cta})'

title_slugified = slugify(title)
author_slugified = slugify(author)

date = datetime.now().strftime('%Y%m%d')
with open(f'./books/{date}-{title_slugified}-{author_slugified}.md', "w", encoding="utf8") as text_file:
    text_file.write(output)

os.system(f'git add "./books/{date}-{title_slugified}-{author_slugified}.md"')
os.system(f'git commit -m "{title} by {author}"')
os.system(f'git push')
