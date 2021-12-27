import asyncio
import aiosonic
import re
import os
import time
import threading

from tasksio import TaskPool
from colorama import init, Fore

init(convert=True)

class RequestTimeout:
    request_timeout = 100
    sock_read = 100
    sock_connect = 100

TOKENS_LOADED = 0
TOKENS_INVALID = 0
TOKENS_LOCKED = 0
TOKENS_VALID = 0
TOKENS_VALID_LIST = []

def filter_tokens(unfiltered):
    tokens = []
    
    for line in [x.strip() for x in unfiltered.readlines() if x.strip()]:
        for regex in (r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}', r'mfa\.[\w-]{84}'):
            for token in re.findall(regex, line):
                if token not in tokens:
                    tokens.append(token)
                
    return tokens

def title_worker():
    global TOKENS_INVALID, TOKENS_LOCKED, TOKENS_VALID, TOKENS_LOADED
    while True:
        os.system(f"title 🌊 Tokens Trouver: {TOKENS_LOADED} ^| ✅ Valide: {TOKENS_VALID} ^| ❌ Bloquée: {TOKENS_LOCKED} ^| 📛 Invalide: {TOKENS_INVALID}")
        time.sleep(0.1)
        
threading.Thread(target=title_worker, daemon=True).start()

async def check(token, client):
    global TOKENS_INVALID, TOKENS_LOCKED, TOKENS_VALID, TOKENS_VALID_LIST
    
    response = await client.get("https://discord.com/api/v9/users/@me/library", headers={
        "Authorization": token,
        "Content-Type": "application/json"
    }, timeouts=RequestTimeout)
    
    if response.status_code == 200:
        TOKENS_VALID += 1
        TOKENS_VALID_LIST.append(token)
        print(f'{Fore.GREEN}[VALIDE] {token}')
            
    elif response.status_code == 401:      
        TOKENS_INVALID += 1
        print(f'{Fore.RED}[INVALIDE] {token}')
        
    elif response.status_code == 403:
        TOKENS_LOCKED += 1
        print(f'{Fore.RED}[BLOQUE] {token}')
    
async def main():
    global TOKENS_INVALID, TOKENS_LOCKED, TOKENS_VALID, TOKENS_LOADED, TOKENS_VALID_LIST
    
    client = aiosonic.HTTPClient()
    
    try:
        with open('tokens.txt', 'r') as tokens:
            filtered = filter_tokens(tokens)
            TOKENS_LOADED = len(filtered)
            async with TaskPool(100) as pool:
                for token in filtered:
                    await pool.put(check(token, client))
                    
            await client.shutdown()

            print(f"{Fore.BLUE}Tokens Trouver: {TOKENS_LOADED} | {Fore.GREEN}Valide: {TOKENS_VALID} | {Fore.RED}Bloquer: {TOKENS_LOCKED} | {Fore.YELLOW}Invalide: {TOKENS_INVALID}")    
            
            with open(f'working.txt', 'w') as handle:
                handle.write('\n'.join(TOKENS_VALID_LIST))
                handle.close()
                
            input("Sauvegarder dans (working.txt), presse une touche pour finir.")
                      
    except Exception as e:
        print(e)
        input('Je ne trouve pas "tokens.txt"\nPresse une touche pour finir.')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
