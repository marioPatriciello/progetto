import os
import Src.Utilities.config as config
dotenv = config.dotenv

# You need to keep dotenv disabled on remote servers
if dotenv == "1":
    from dotenv import load_dotenv
    load_dotenv(".env")

def load_env():
    env_vars = {}
    env_vars['TMDB_KEY'] = os.getenv('TMDB_KEY')
    # Nota: Assicurati che su HF il secret sia PROXY o PROXY_CREDENTIALS in base a come lo hai chiamato
    env_vars['PROXY_CREDENTIALS'] = os.getenv('PROXY') 
    env_vars['ForwardProxy'] = os.getenv('FORWARDPROXY')
    env_vars['PORT_ENV'] = os.getenv('PORT')
    
    # --- AGGIUNTA FONDAMENTALE PER MFP ---
    env_vars['MFP_URL'] = os.getenv('MFP_URL')
    env_vars['MFP_KEY'] = os.getenv('MFP_KEY')
    
    return env_vars
