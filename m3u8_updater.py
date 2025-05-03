from Kekik.cli import konsol
from cloudscraper import CloudScraper
import os, re, requests, hashlib

class M3U8Updater:
    def __init__(self):
        self.oturum = CloudScraper()
        self.m3u8_url = "https://raw.githubusercontent.com/Kraptor123/yaylink/main/channels.m3u"
        self.m3u8_dosya = "channels.m3u"
        self.base_urls = {"taraftarium": None, "trgoals": None}
        self.original_hash = self._hash_kontrol()

    def _hash_kontrol(self):
        """Dosya hash'ini al"""
        if os.path.exists(self.m3u8_dosya):
            with open(self.m3u8_dosya, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        return None

    def degisiklik_var_mi(self):
        """Hash karşılaştırması yap"""
        with open(self.m3u8_dosya, "rb") as f:
            yeni_hash = hashlib.md5(f.read()).hexdigest()
        return yeni_hash != self.original_hash

    def _dosya_indir(self):
        """M3U8 dosyasını indir"""
        try:
            response = requests.get(self.m3u8_url)
            with open(self.m3u8_dosya, "w", encoding="utf-8") as f:
                f.write(response.text)
            konsol.log("[+] M3U8 dosyası başarıyla indirildi")
        except Exception as hata:
            konsol.log(f"[!] İndirme hatası: {hata}")
            raise

    def _taraftarium_baseurl_al(self):
        """Taraftarium URL'sini çek"""
        try:
            kaynak = self.oturum.get("https://taraftarium.co/channel.html?id=yayinstar").text
            if match := re.search(r'baseurl\s*=\s*"([^"]+)"', kaynak):
                self.base_urls["taraftarium"] = match.group(1).rstrip("/") + "/"
                konsol.log(f"[+] Taraftarium URL: {self.base_urls['taraftarium']}")
            else:
                konsol.log("[!] Taraftarium URL bulunamadı")
        except Exception as hata:
            konsol.log(f"[!] Taraftarium hatası: {hata}")

    def _trgoals_baseurl_al(self):
        """TrGoals URL'sini çek"""
        try:
            kaynak = self.oturum.get("https://trgoals1313.xyz/channel.html?id=yayin1").text
            if match := re.search(r'const baseurl\s*=\s*"([^"]+)"', kaynak):
                self.base_urls["trgoals"] = match.group(1).rstrip("/") + "/"
                konsol.log(f"[+] TrGoals URL: {self.base_urls['trgoals']}")
            else:
                konsol.log("[!] TrGoals URL bulunamadı")
        except Exception as hata:
            konsol.log(f"[!] TrGoals hatası: {hata}")

    def _m3u8_guncelle(self):
        """M3U8 dosyasını güncelle"""
        with open(self.m3u8_dosya, "r", encoding="utf-8") as f:
            icerik = f.read()

        # Regex pattern'leri
        patterns = [
            (
                r'(#EXTVLCOPT:http-referrer=https://taraftarium\.co/\nhttps?://)([^/]+)(/.*\.m3u8)',
                self.base_urls["taraftarium"]
            ),
            (
                r'(#EXTVLCOPT:http-referrer=https://trgoals1312\.xyz/\nhttps?://)([^/]+)(/.*\.m3u8)',
                self.base_urls["trgoals"]
            )
        ]

        # Güncelleme işlemi
        for pattern, new_url in patterns:
            if new_url:
                icerik = re.sub(
                    pattern,
                    lambda m: f"{m.group(1)}{new_url.split('://')[1]}{m.group(3)}",
                    icerik
                )

        # Değişiklikleri kaydet
        with open(self.m3u8_dosya, "w", encoding="utf-8") as f:
            f.write(icerik)
        konsol.log("[✔] M3U8 başarıyla güncellendi")

    def calistir(self):
        """Ana çalıştırıcı"""
        self._dosya_indir()
        self._taraftarium_baseurl_al()
        self._trgoals_baseurl_al()
        self._m3u8_guncelle()
        return self.degisiklik_var_mi()

if __name__ == "__main__":
    updater = M3U8Updater()
    degisiklik = updater.calistir()
    print(f"::set-output name=degisiklik::{str(degisiklik).lower()}")