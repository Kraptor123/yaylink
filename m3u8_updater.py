import re
import os
import hashlib
import argparse
from Kekik.cli import konsol
from cloudscraper import CloudScraper
import requests

class M3U8Updater:
    def __init__(self, remote_url, local_file):
        self.oturum = CloudScraper()
        self.m3u8_url = remote_url
        self.m3u8_dosya = local_file
        self.original_content = self._dosya_indir()
        self.fallbacks = {
            'taraftarium': 'https://t6co.32ufajdjfnsa32.workers.dev/list/',
            'trgoals':    'https://b0.4928d54d950ee70q42.click/'
        }

    def _dosya_indir(self):
        try:
            resp = requests.get(self.m3u8_url, timeout=10)
            resp.raise_for_status()
            return resp.text
        except Exception as hata:
            konsol.log(f"[!] M3U8 indirme hatası: {hata}")
            raise

    def _url_al(self, url, pattern, key):
        try:
            kaynak = self.oturum.get(url).text
            if m := re.search(pattern, kaynak):
                return m.group(1).rstrip('/') + '/'  # ensure trailing slash
            konsol.log(f"[!] URL bulunamadı: {url}")
        except Exception as hata:
            konsol.log(f"[!] Hata ({url}): {hata}")
        return self.fallbacks.get(key)

    def _m3u8_guncelle(self, referrer, yeni_baseurl, content):
        if not yeni_baseurl:
            return content
        # pattern: referrer line + next .m3u8 url\        
        pattern = (rf"(#EXTVLCOPT:http-referrer={re.escape(referrer)})"  
                   r"\s*\n\s*https?://[^/]+/([^\s]+\.m3u8)")
        def repl(m):
            yeni = f"{m.group(1)}\n{yeni_baseurl}{m.group(2)}"
            konsol.log(f"[DEBUG] Güncelle: {m.group(0).splitlines()[1]} -> {yeni_baseurl}{m.group(2)}")
            return yeni
        return re.sub(pattern, repl, content, flags=re.MULTILINE)

    def calistir(self):
        # Kaynak URL'ler ve regex desenleri
        tara_url = self._url_al(
            "https://taraftarium.co/channel.html?id=yayinstar",
            r"baseurl\s*=\s*\"([^\"]+)\"",
            'taraftarium'
        )
        trg_url = self._url_al(
            "https://trgoals1313.xyz/channel.html?id=yayin1",
            r"const baseurl\s*=\s*\"([^\"]+)\"",
            'trgoals'
        )

        updated = self._m3u8_guncelle("https://taraftarium.co/", tara_url, self.original_content)
        updated = self._m3u8_guncelle("https://trgoals1312.xyz/", trg_url, updated)

        # Değişiklik kontrolü
        if hashlib.sha256(updated.encode('utf-8')).hexdigest() != hashlib.sha256(self.original_content.encode('utf-8')).hexdigest():
            with open(self.m3u8_dosya, 'w', encoding='utf-8') as f:
                f.write(updated)
            konsol.log("[+] M3U8 başarıyla güncellendi!")
            return True
        else:
            konsol.log("[✔] Değişiklik yok")
            return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Otomatik M3U8 Güncelleyici')
    parser.add_argument('--remote', default='https://raw.githubusercontent.com/Kraptor123/yaylink/main/channels.m3u',
                        help='Uzak M3U8 dosya URL')
    parser.add_argument('--local', default='channels.m3u',
                        help='Yerel M3U8 dosya yolu')
    args = parser.parse_args()

    degisiklik = M3U8Updater(args.remote, args.local).calistir()
    # GitHub Actions için çıktı
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
            print(f'degisiklik={str(degisiklik).lower()}', file=out)
