from Kekik.cli import konsol
from cloudscraper import CloudScraper
import os, re, requests, hashlib

class M3U8Updater:
    def __init__(self):
        self.oturum = CloudScraper()
        self.m3u8_url = "https://raw.githubusercontent.com/Kraptor123/yaylink/main/channels.m3u"
        self.m3u8_dosya = "channels.m3u"
        self.original_content = self._dosya_indir()  # İlk içeriği kaydet

    def _dosya_indir(self):
        """M3U8 dosyasını indir ve içeriğini döndür"""
        try:
            response = requests.get(self.m3u8_url)
            return response.text
        except Exception as hata:
            konsol.log(f"[!] İndirme hatası: {hata}")
            raise

    def _url_al(self, url, regex_pattern):
        """Belirtilen siteden URL'yi regex ile çek"""
        try:
            kaynak = self.oturum.get(url).text
            if match := re.search(regex_pattern, kaynak):
                return match.group(1).strip("/") + "/"
            konsol.log(f"[!] URL bulunamadı: {url}")
            return None
        except Exception as hata:
            konsol.log(f"[!] Hata ({url}): {hata}")
            return None

    def _m3u8_guncelle(self, hedef_url, yeni_url):
        """M3U8 içeriğinde URL güncelle"""
        if not yeni_url:
            return self.original_content
            
        # Debug çıktısı
        konsol.log(f"[DEBUG] {hedef_url} -> {yeni_url}")
        
        return re.sub(
            rf'(#EXTVLCOPT:http-referrer={re.escape(hedef_url)}/\nhttps?://)([^/]+)(/.*\.m3u8)',
            fr'\g<1>{yeni_url.split("://")[1]}\g<3>',
            self.original_content
        )

    def calistir(self):
        """Ana işlem"""
        # Güncel URL'leri al
        taraftarium_url = self._url_al(
            "https://taraftarium.co/channel.html?id=yayinstar",
            r'baseurl\s*=\s*"([^"]+)"'
        )
        trgoals_url = self._url_al(
            "https://trgoals1313.xyz/channel.html?id=yayin1",
            r'const baseurl\s*=\s*"([^"]+)"'
        )
        
        # M3U8'i güncelle
        yeni_icerik = self._m3u8_guncelle("https://taraftarium.co", taraftarium_url)
        yeni_icerik = self._m3u8_guncelle("https://trgoals1312.xyz", trgoals_url)
        
        # Değişiklik kontrolü
        degisiklik_var = yeni_icerik != self.original_content
        
        if degisiklik_var:
            with open(self.m3u8_dosya, "w", encoding="utf-8") as f:
                f.write(yeni_icerik)
            konsol.log("[+] M3U8 başarıyla güncellendi!")
        else:
            konsol.log("[✔] Değişiklik yok")
            
        return degisiklik_var

if __name__ == "__main__":
    degisiklik = M3U8Updater().calistir()
    with open(os.environ.get('GITHUB_OUTPUT', ''), 'a') as fh:
        print(f'degisiklik={str(degisiklik).lower()}', file=fh)
