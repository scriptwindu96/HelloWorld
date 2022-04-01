from bs4 import BeautifulSoup
import requests
from github import Github
from time import sleep
from keywords import keywords
import logging
from datetime import datetime
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

queries = ['santander','santander consumer', 'banco santander']

#simple logger for error detection
def callLog(msg):
    logging.basicConfig(filename='error.log', filemode='a', level=logging.INFO,
    format="%(levelname)s - %(asctime)s - %(message)s")
    logger = logging.getLogger(__name__)
    logger.info(msg)

#Class handles queries to github API
class gitQuery:
    def __init__(self):
        self.urls = []
        self.bit = 0
        self.keywords = keywords
    
    #Iterate through available API tokens
    def selectToken(self, bit):
        ACCESS_TOKENS = [#github API tokens]
        token = ACCESS_TOKENS[bit % len(ACCESS_TOKENS)]
        return Github(token)
    
    #Using keyword, generate github query and submit to Github Search API - if result is error change token and resubmit
    def sendGithubQuery(self, query):
        g = self.selectToken(self.bit)
        try:
            result = g.search_code(query, order='desc')
            print(f'Found {result.totalCount} file(s) for {query}')
            for file in result:
                url = (f'{file.download_url}')
                self.urls.append(url)

        except Exception as ex:
            callLog(ex)
            self.bit += 1
            g = self.selectToken(self.bit)
            self.sendGithubQuery(query)
    
    #def buildGitHubQuery(self, keyword):
        #for q in queries:
            #query = f'{q} {keyword} in:file extension:{args.extension}'
            #self.sendGithubQuery(query)

    def ThreadingQuery(self, keyword):
        n = len(self.keywords)
        g = self.selectToken(self.bit)
        for q in queries:
            with ThreadPoolExecutor(max_workers=n) as executor:
                query = f'{q} {keyword} in:file extension:{args.extension}'
                executor.submit(g.search_code, query, order='desc')
                self.sendGithubQuery(query)
            

            
            
    
    #Iterate through all keywords and call "sendGithubQuery"
    def loopkeywords(self):
        for word in self.keywords:
            self.ThreadingQuery(word)
        return self.urls

    
#write results to outfile
def write_results(nline):
    with open(args.outfile, 'a') as f:
        f.writelines(nline)
        f.close()

#collect the actual line from the Github URL containing the keyword found
def get_githubContents(u):
    lines = []
    newLines = []
    page = requests.get(u)
    soup = BeautifulSoup(page.content, 'html.parser')
    output = soup.prettify()
    flines = output.split("\n")
    for fline in flines:
        for keyword in keywords:
            if keyword in fline:
                lines.append(fline)
    for line in lines:
        newLines.append(F'{u}, {line}\n')
    newLines = list(dict.fromkeys(newLines))
    return newLines

#Iterate through all the URLs. See if they are already logged. If so - pass. Otherewise, collect code line from raw Github
def RepoScrape(urls):
    try:
        newlines = []
        with open(args.outfile, 'r') as f:
            olines = f.read()
            for u in urls:
                doesExist = check_doc(olines, u)
                if doesExist:
                    pass
                else:
                    newlines = get_githubContents(u)
                    newlines = list(dict.fromkeys(newlines))
                    for line in newlines:
                        write_results(line)
            f.close()
    except Exception as E:
        callLog(E)
        callLog(f"Creating document {args.outfile}")
        with open(args.outfile, 'w') as f:
            f.close()
        RepoScrape(urls)


#simple check to see if the URL exists in the outfile already
def check_doc(olines, url):
    if url in olines:
        return True
    else:
        return False


def main():
    callLog("Initializing cyberscraper tool")
    searcher = gitQuery()
    urls = searcher.loopkeywords()
    RepoScrape(urls)


if __name__ == '__main__':
    keywords = keywords
    parser = argparse.ArgumentParser(description="Scrapes Github for EFX data", usage="parser -e <extension> -k <keywordsfile")
    parser.add_argument('-e', '--extension', help="define file extension to explore (i.e., py, js, etc", 
    required=False, default='py')
    parser.add_argument('-o', '--outfile', help="define an outfile to write data to", required=False, default='git_pages.csv')
    args = parser.parse_args()
    main()
