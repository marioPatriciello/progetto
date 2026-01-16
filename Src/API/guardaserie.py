from Src.Utilities.info import is_movie
from bs4 import BeautifulSoup, SoupStrainer
import re
import Src.Utilities.config as config
from fake_headers import Headers  
from Src.Utilities.loadenv import load_env  
import json, random
from Src.Utilities.info import get_info_imdb, get_info_tmdb
import urllib.parse
from Src.Utilities.convert import get_IMDB_id_from_TMDb_id
from Src.API.extractors.supervideo import supervideo
import logging
from Src.Utilities.config import setup_logging

level = config.LEVEL
logger = setup_logging(level)

env_vars = load_env()
GS_PROXY = config.GS_PROXY
GS_DOMAIN = config.GS_DOMAIN
GS_ForwardProxy = config.GS_ForwardProxy

# --- INIZIO MODIFICA: Proxy Sicuro ---
def get_safe_proxy(env_vars):
    try:
        raw_creds = env_vars.get('PROXY_CREDENTIALS')
        if not raw_creds:
            return {}
        proxy_list = json.loads(raw_creds)
        if not proxy_list:
            return {}
        proxy = random.choice(proxy_list)
        if not proxy:
            return {}
        return {
            "http": proxy,
            "https": proxy
        }
    except Exception as e:
        logger.warning(f"Errore caricamento proxy in Guardaserie: {e}")
        return {}

proxies = {}
if GS_PROXY == "1":
    proxies = get_safe_proxy(env_vars)

if GS_ForwardProxy == "1":
    ForwardProxy = env_vars.get('ForwardProxy')
else:
    ForwardProxy = ""
# --- FINE MODIFICA ---


# Headers statici per sembrare più umani
base_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': f'{GS_DOMAIN}/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
}

async def search_imdb(clean_id, client):
    try:
        # Usa headers realistici
        headers = base_headers.copy()
        
        # --- MODIFICA ANTI-403: Aggiunto impersonate="chrome124" ---
        response = await client.get(
            ForwardProxy + f'{GS_DOMAIN}/?story={clean_id}&do=search&subaction=search', 
            allow_redirects=True, 
            headers=headers, 
            proxies=proxies,
            impersonate="chrome124" 
        )
        
        if response.status_code != 200:
            logger.warning(f"Guardaserie Failed to fetch search results: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'lxml', parse_only=SoupStrainer('div', class_="mlnh-2"))
        # Protezione se non trova risultati
        div_mlnh2 = soup.select_one('div.mlnh-2:nth-of-type(2)')
        if not div_mlnh2:
            return None
            
        a_tag = div_mlnh2.find('h2').find('a')
        href = a_tag['href']
        return href
    except Exception as e:
        logger.warning(f'GS Search Error: {e}')
        return None

async def player_url(page_url, season, episode, client):
    try:
        headers = base_headers.copy()
        headers['Referer'] = page_url # Importante: diciamo che veniamo dalla pagina precedente
        
        # --- MODIFICA ANTI-403: Aggiunto impersonate="chrome124" ---
        response = await client.get(
            ForwardProxy + page_url, 
            allow_redirects=True, 
            headers=headers, 
            proxies=proxies,
            impersonate="chrome124"
        )
        
        soup = BeautifulSoup(response.text, 'lxml', parse_only=SoupStrainer('a'))
        a_tag = soup.find('a', id=f"serie-{season}_{episode}")
        
        if a_tag:
            href = a_tag['data-link']
            return href
        return None
    except Exception as e:
        logger.warning(f'GS Player URL Error: {e}')
        return None

async def guardaserie(streams, id, client):
    try:
        general = await is_movie(id)
        ismovie = general[0]
        clean_id = general[1]
        
        if ismovie == 1:
            return streams
            
        if ismovie == 0:
            season = general[2]
            episode = general[3]
            
        # type = "Guardaserie" (non usato nel codice attivo)
        page_url = await search_imdb(clean_id, client)
        
        if page_url:
            supervideo_link = await player_url(page_url, season, episode, client)
            if supervideo_link: 
                streams = await supervideo(supervideo_link, client, streams, "Guardaserie", proxies, ForwardProxy)
            else:
                logger.info("GS: Episodio non trovato nella pagina")
        else:
            logger.info("GS: Serie non trovata")
            
        return streams
    except Exception as e:
        logger.warning(f"MammaMia: Guardaserie Failed: {e}")
        return streams


async def test_script():
    from curl_cffi.requests import AsyncSession
    async with AsyncSession() as client:
        # Replace with actual id, for example 'anime_id:episode' format
        test_id = "tt10919420:1:1"  # This is an example ID format tt0460649
        results = await guardaserie({'streams': []}, test_id, client)
        print(results)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_script())
