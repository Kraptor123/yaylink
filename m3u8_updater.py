import re
import os
import hashlib
import argparse
import time
from Kekik.cli import konsol
from cloudscraper import CloudScraper
import requests
from urllib.parse import urlparse

class M3U8Updater:
    def __init__(self, remote_url, local_file):
        self.oturum = CloudScraper()
        self.m3u8_url = remote_url
        self.m3u8_dosya = local_file
        self.sources = [
            {
                'page_url': 'https://taraftarium.co/channel.html?id=yayinstar',
                'referrer': 'https://taraftarium.co/'
            },
            {
                'page_url': 'https://trgoals1325.xyz/channel.html?id=yayin1',
                'referrer': 'https://trgoals1325.xyz/'
            }
        ]
        self.baseurl_regex = re.compile(r'baseurl\s*=\s*["\'](https?://[^"\']+/)["\']')
        self.original_content = self._dosya_indir()

    def _build_full_url(self, url):
        parsed = urlparse(url)
        return f"{parsed.scheme or 'https'}://{parsed.netloc}{parsed.path}?{parsed.query}"

    def _fetch_baseurl(self, src, retries=2):
        full_url = self._build_full_url(src['page_url'])
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': src['referrer']}
        
        for attempt in range(retries):
            try:
                resp = self.oturum.get(full_url, headers=headers, timeout=10)
                if match := self.baseurl_regex.search(resp.text):
                    return match.group(1).rstrip('/') + '/'  # Trailing slash garantisi
                raise ValueError(f"BaseURL pattern not found in {full_url}")
            except Exception as hata:
                if attempt == retries - 1:
                    raise RuntimeError(f"BaseURL alınamadı: {full_url}") from hata
                time.sleep(3)
                continue

    def _dosya_indir(self):
        try:
            resp = requests.get(self.m3u8_url, timeout=10)
            resp.raise_for_status()
            # Satır sonu karakterlerini koruyarak ayırma
            return resp.content.decode('utf-8').splitlines(keepends=True)
        except Exception as hata:
            konsol.log(f"[!] M3U8 indirme hatası: {hata}")
            raise

    def calistir(self):
        try:
            # BaseURL'leri dinamik olarak çek
            for src in self.sources:
                src['baseurl'] = self._fetch_baseurl(src)
            
            new_content = []
            modified = False
            
            i = 0
            while i < len(self.original_content):
                line = self.original_content[i]
                
                if line.startswith('#EXTVLCOPT:http-referrer=') and (i+1) < len(self.original_content):
                    referrer = line.split('=', 1)[1].strip()
                    next_line = self.original_content[i+1]
                    
                    for src in self.sources:
                        if referrer == src['referrer']:
                            original_url = next_line.strip()
                            filename = original_url.split('/')[-1]
                            new_url = f"{src['baseurl']}{filename}"
                            
                            if not original_url.startswith(src['baseurl']):
                                # Orijinal satır sonu karakterini koru
                                new_line = new_url + next_line[len(original_url):]
                                new_content.extend([line, new_line])
                                konsol.log(f"[+] Güncelleniyor: {original_url} -> {new_url}")
                                modified = True
                            else:
                                new_content.extend([line, next_line])
                            
                            i += 1  # Next line'i atla
                            break
                    else:
                        new_content.extend([line, next_line])
                        i += 1
                else:
                    new_content.append(line)
                
                i += 1

            # Değişiklik kontrolü
            if modified:
                with open(self.m3u8_dosya, 'wb') as f:
                    f.write(''.join(new_content).encode('utf-8'))
                konsol.log("[+] M3U8 başarıyla güncellendi!")
                return True
            else:
                konsol.log("[✔] Değişiklik yok")
                return False
                
        except Exception as e:
            konsol.log(f"[!] Kritik Hata: {str(e)}")
            raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Otomatik M3U8 Güncelleyici')
    parser.add_argument('--remote', default='https://raw.githubusercontent.com/Kraptor123/yaylink/main/channels.m3u',
                        help='Uzak M3U8 dosya URL')
    parser.add_argument('--local', default='channels.m3u',
                        help='Yerel M3U8 dosya yolu')
    args = parser.parse_args()

    try:
        degisiklik = M3U8Updater(args.remote, args.local).calistir()
    except Exception as e:
        degisiklik = False
        konsol.log(f"[!] Güncelleme başarısız: {e}")
    
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            print(f'degisiklik={str(degisiklik).lower()}', file=out)
