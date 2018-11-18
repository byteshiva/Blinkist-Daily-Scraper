# coding: utf-8
from bs4 import BeautifulSoup
from datetime import datetime
from github import Github, GithubException
import os
import tomd
import urllib3

repoName = os.environ['REPO_NAME']
repoToken = os.environ['GITHUB_TOKEN']

def lambda_handler(event, context):
    status = run()

    return {
        "statusCode": 200 if status == 'OK' else 422,
        "msg": status
    }

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1 Safari/605.1.15'}
http = urllib3.PoolManager(10, headers = headers)
urllib3.disable_warnings()

def get_element_from_request(url, element, class_):
    response = http.request('GET', url)
    soup = BeautifulSoup(response.data.decode('utf-8'), "html5lib")
    return soup.find(element, class_ = class_)

def get_meta_data():
    container = get_element_from_request('https://www.blinkist.com/nc/daily', 'div', 'dailyV2__free-book')

    title = container.find('div', 'dailyV2__free-book__title').string.strip()
    author = container.find('div', 'dailyV2__free-book__author').string.strip()
    description = container.find('div', 'dailyV2__free-book__description').string.strip()
    cta = container.find('div', 'dailyV2__free-book__cta').a['href']
    img_url = container.find('img')['src']

    return title, author, description, cta, img_url

def get_article(cta):
    return str(get_element_from_request(f'https://www.blinkist.com{cta}', 'article', 'shared__reader__blink reader__container__content')).strip()

def run():
    print('Fetching content...', end='')
    title, author, description, cta, img_url = get_meta_data()
    article = tomd.convert(get_article(cta))
    print('Done')

    date = datetime.now().strftime('%Y%m%d')
    commitMessage = f'{title} by {author}'
    fileName = os.path.join('blinks', f'{date[:4]}', f'{date}-{title}-{author}.md')

    print('Building output...', end='')
    # Convert to markdown, add source
    output = f'![{title}]({img_url})\n# {title}\n*{author}*\n\n>{description}\n\n{article}\n\nSource: [{commitMessage}](https://www.blinkist.com{cta})'
    print('Done')

    print(f'Committing file {fileName}...', end='')
    g = Github(repoToken)
    repo = g.get_repo(repoName)
    try:
        repo.create_file(fileName, commitMessage, output)
        print('Done')
        return 'OK'
    except GithubException:
        print('already exists')
        return 'File Exists'

lambda_handler(None, None)