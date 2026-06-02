#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import random
import pygame
import subprocess
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView,
    QLabel, QGraphicsProxyWidget,
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsItemGroup, QGraphicsLineItem,
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtGui import QPixmap, QColor, QPen
from PyQt6.QtGui import QMovie
from PyQt6 import QtGui
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtCore import QSize

# Wayland ve modern masaüstü ortamları için uyumluluk ayarları
if "GNOME" in os.environ.get("XDG_CURRENT_DESKTOP", ""):
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

# ---------------------------------------------------------------------------
# SABİTLER
# ---------------------------------------------------------------------------
PENCERE_EN    = 1280
PENCERE_BOY   = 720

PANEL_X       = 0

DISK_MERKEZ_X = int(PENCERE_EN * 0.27)
DISK_MERKEZ_Y = int(PENCERE_BOY * -0.05)

DISK_OLCEK    = 0.60
DISK_ORIJINAL = 2048

DONME_HIZI    = -0.5
HIZLANMA_HIZI = -0.9
FREN_HIZI     = -0.2

VOL_ANA_EKRAN = 0.5 # Bunu kaldırdık ama artık kodlar kaldı mı diye bakacağız.
VOL_STAGE_M_1 = 0.3
VOL_STAGE_M_2 = 0.3
VOL_STAGE_M_3 = 0.3
VOL_STAGE_M_4 = 0.3
VOL_STAGE_M_5 = 0.3
VOL_STAGE_TEMIZ = 0.1
VOL_MOTOR = 0.1
VOL_MOTOR_HIZ = 0.1
VOL_MOTOR_YUK = 0.1
VOL_PATLAMA = 0.2
VOL_GRI_SES = 0.4
VOL_ORMAN_SES = 0.5
VOL_SU_SES = 0.6
VOL_STAR_GAME = 0.6

# Ot, su, kıvılcım giflerinin arabaya oturma ayarları
GIF_GENISLIK  = 85  # Piksel cinsinden genişlik 
GIF_YUKSEKLIK = 100  # Piksel cinsinden yükseklik
GIF_Y_GERI_CEKME = 30 # Gif efektinin hizalaması

# Pil Gösterge Koordinatları (Elle ince ayar yapabilmek için çarpan bazlı)
# Panel ölçeklendikten sonra BATT kutusunun yerini bulmak için bu değerlerle oynayabilirsin
IBRE_X_BOS  = 53   # Pil %0 iken çizginin duracağı sol sınır X koordinatı
IBRE_X_DOLU = 140  # Pil %100 iken çizginin duracağı sağ sınır X koordinatı
IBRE_Y_UST  = 83  # İbrenin yukarıdan başlayacağı tepe Y koordinatı
IBRE_Y_ALT  = 123  # İbrenin aşağıda biteceği taban Y koordinatı

# Renk toleransı
def renk_esit(r, g, b, hr, hg, hb, tolerans=25):
    return abs(r - hr) < tolerans and abs(g - hg) < tolerans and abs(b - hb) < tolerans

# ---------------------------------------------------------------------------
# ANA PENCERE
# ---------------------------------------------------------------------------
class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cardboard Circuit")
        self.setFixedSize(PENCERE_EN, PENCERE_BOY)
        self.dizin = os.path.dirname(os.path.abspath(__file__)) # Dizin tanımını yukarı al

        # İkonu ana dizinde bul ve ayarla
        ikon_yolu = os.path.join(self.dizin, "caricon.png")
        if os.path.exists(ikon_yolu):
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(ikon_yolu))
        self.disk_dizin = os.path.join(self.dizin, "disks")
        # Gerekli klasörlerin varlığını kontrol et
        gerekli_klasorler = ["cars", "disks", "effects", "sounds"]
        for klasor in gerekli_klasorler:
            yol = os.path.join(self.dizin, klasor)
            if not os.path.exists(yol):
                print(f"KRİTİK HATA: Gerekli klasör bulunamadı -> {yol}")
                sys.exit(1)

        self.sahne = QGraphicsScene(self)
        self.sahne.setSceneRect(0, 0, PENCERE_EN, PENCERE_BOY)
        self.sahne.setBackgroundBrush(QColor(30, 30, 30))

        self.view = QGraphicsView(self.sahne, self)
        self.view.setGeometry(0, 0, PENCERE_EN, PENCERE_BOY)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setFrameShape(self.view.Shape.NoFrame)
        self.view.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.view)

        # Fare hareketlerini sürekli dinlemek için takibi açıyoruz
        self.setMouseTracking(True)
        self.view.setMouseTracking(True)
        # View elemanının fare hareketini yutmasını engelleyip pencereye paslıyoruz
        self.view.mouseMoveEvent = self.mouseMoveEvent

        self._panel_yukle()
        self._disk_yukle()

        self.durum = "off"
        self.oyun_basladi = False
        self.oyun_durdu = False
        self.yaris_bitti = False
        self.aci = 0.0
        self.w_basili = False
        self.s_basili = False
        self.guncel_hiz = DONME_HIZI
        self.eski_aci = 0.0
        # Pil Altyapısı (Başlangıçta %85)
        self.pil_seviyesi = 85.0
        self.pil_bitti = False
        self._ibre_olustur()
        self.sounds_dizin = os.path.join(self.dizin, "sounds")
        pygame.mixer.init(44100, -16, 2, 512)
        pygame.mixer.set_num_channels(16)

        self.chan_muzik = pygame.mixer.Channel(0)
        self.chan_motor = pygame.mixer.Channel(1)
        self.chan_zemin = pygame.mixer.Channel(2)
        self.chan_efekt = pygame.mixer.Channel(3)

        self.snd_main_screen = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "main-screen.ogg"))
        self.snd_stage_clear = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "stage-clear.ogg"))
        self.snd_star_of_the_game = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "starofthegame.ogg"))
        self.snd_explosion = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "explosion.ogg"))
        
        self.snd_engine = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "engine.ogg"))
        self.snd_engine_speed = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "engine-speed.ogg"))
        self.snd_engine_overload = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "engine-overload.ogg"))

        self.snd_grey = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "grey-sound.ogg"))
        self.snd_jungle = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "jungle-sound.ogg"))
        self.snd_water = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "water-sound.ogg"))

        self.snd_stages_muzik = {
            1: pygame.mixer.Sound(os.path.join(self.sounds_dizin, "stage-1.ogg")),
            2: pygame.mixer.Sound(os.path.join(self.sounds_dizin, "stage-2.ogg")),
            3: pygame.mixer.Sound(os.path.join(self.sounds_dizin, "stage-3.ogg")),
            4: pygame.mixer.Sound(os.path.join(self.sounds_dizin, "stage-4.ogg")),
            5: pygame.mixer.Sound(os.path.join(self.sounds_dizin, "stage-5.ogg")),
        }

        self.snd_main_screen.set_volume(VOL_ANA_EKRAN)
        self.snd_stage_clear.set_volume(VOL_STAGE_TEMIZ)
        self.snd_explosion.set_volume(VOL_PATLAMA)
        self.snd_engine.set_volume(VOL_MOTOR)
        self.snd_engine_speed.set_volume(VOL_MOTOR_HIZ)
        self.snd_engine_overload.set_volume(VOL_MOTOR_YUK)
        self.snd_grey.set_volume(VOL_GRI_SES)
        self.snd_jungle.set_volume(VOL_ORMAN_SES)
        self.snd_water.set_volume(VOL_SU_SES)
        self.snd_star_of_the_game.set_volume(VOL_STAR_GAME)

        self.snd_stages_muzik[1].set_volume(VOL_STAGE_M_1)
        self.snd_stages_muzik[2].set_volume(VOL_STAGE_M_2)
        self.snd_stages_muzik[3].set_volume(VOL_STAGE_M_3)
        self.snd_stages_muzik[4].set_volume(VOL_STAGE_M_4)
        self.snd_stages_muzik[5].set_volume(VOL_STAGE_M_5)

        
        self.aktif_zemin_sesi = None
        self.aktif_motor_sesi = None

        self.araba_x = DISK_MERKEZ_X - 135 # büyüdükçe sola kayar.
        self.araba_y = DISK_MERKEZ_Y + 410 # büyüdükçe aşağı kayar.
        self.araba_hiz = 8
        self._araba_yukle()
        
        # Savrulma (Drift) Dinamikleri
        self.araba_guncel_aci = 0.0
        self.araba_hedef_aci = 0.0
        self._fare_merkezleniyor = False

        self.timer = QTimer(self)
        self.toplam_tur = 5
        self.guncel_tur = 0
        self.tur_yazisi = self.sahne.addText("")
        font = QtGui.QFont("Liberation Sans", 48, QtGui.QFont.Weight.Bold)
        self.tur_yazisi.setFont(font)
        self.tur_yazisi.setDefaultTextColor(QColor(255, 215, 0))
        self.tur_yazisi.setZValue(10)
        # Yazıyı ortalamak için bounding rect genişliğinin yarısı kadar sola kaydırıyoruz
        # Yazıyı yaklaşık olarak ortaya konumlandırıyoruz
        self.tur_yazisi.setPos(PENCERE_EN // 2 - 100, PENCERE_BOY // 2 - 50)
        self.tur_yazisi.setPlainText("PRESS W TO START")
        
        # Can Altyapısı ve Yıldız İkonları (Maksimum 5 can sınırı ile)
        self.toplam_can = 5
        self.guncel_can = 3
        self.yildiz_itemlar = []
        
        self.yol_yildiz = os.path.join(self.dizin, "effects", "star.png")
        self.pixmap_yildiz = QPixmap(self.yol_yildiz)
        if not self.pixmap_yildiz.isNull():
            self.pixmap_yildiz = self.pixmap_yildiz.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # Başlangıçta sadece güncel can kadar (3 adet) yıldız çizdiriyoruz
            for i in range(self.guncel_can):
                yildiz = QGraphicsPixmapItem(self.pixmap_yildiz)
                yildiz.setPos(20 + (i * 50), 20)
                yildiz.setZValue(10)
                self.sahne.addItem(yildiz)
                self.yildiz_itemlar.append(yildiz)
                
        self.timer.timeout.connect(self._guncelle)
        self.timer.start(16)
        if self.aktif_stage in self.snd_stages_muzik:
            self.chan_muzik.play(self.snd_stages_muzik[self.aktif_stage], loops=-1)
        self._ilk_hareket = True

    # ------------------------------------------------------------------
    # PİL İBRESİ ÇİZİMİ
    # ------------------------------------------------------------------
    def _ibre_olustur(self):
        """Sol panel BATT alanına turuncu dikey ibre çizer."""
        self.ibre_item = QGraphicsLineItem()
        kalem = QPen(QColor("#ff4800"))
        kalem.setWidth(3)
        self.ibre_item.setPen(kalem)
        self.ibre_item.setZValue(5)  # En üstte görünmesi için
        self.sahne.addItem(self.ibre_item)
        self._ibre_guncelle()

    def _ibre_guncelle(self):
        """Pil yüzdesine göre dikey ibrenin X konumunu hesaplar ve kaydırır."""
        yuzde = max(0.0, min(100.0, self.pil_seviyesi))
        # 0 boş (126), 100 dolu (353) olacak şekilde lineer interpolasyon
        ibre_x = IBRE_X_BOS + (yuzde / 100.0) * (IBRE_X_DOLU - IBRE_X_BOS)
        self.ibre_item.setLine(ibre_x, IBRE_Y_UST, ibre_x, IBRE_Y_ALT)

    # ------------------------------------------------------------------
    # SOL PANEL
    # ------------------------------------------------------------------
    def _panel_yukle(self):
        panel_dosyalari = {
            "off":       "game-off.jpeg",
            "normal":    "game-normal.jpeg",
            "overload1": "game-overload.jpeg",
            "overload2": "game-overload.jpeg",
        }
        self.panel_itemlar = {}

        for durum, dosya in panel_dosyalari.items():
            yol = os.path.join(self.disk_dizin, dosya)
            pixmap = QPixmap(yol)
            if pixmap.isNull():
                print(f"UYARI: Panel resmi bulunamadı → {yol}")
                continue
            olcek = PENCERE_BOY / pixmap.height()
            pixmap = pixmap.scaled(
                int(pixmap.width() * olcek),
                PENCERE_BOY,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            item = QGraphicsPixmapItem(pixmap)
            item.setPos(PANEL_X, 0)
            item.setZValue(0)
            item.setVisible(False)
            self.sahne.addItem(item)
            self.panel_itemlar[durum] = item

        if "off" in self.panel_itemlar:
            self.panel_itemlar["off"].setVisible(True)

    # ------------------------------------------------------------------
    # DİSK + MASKE (tutkallanmış grup)
    # ------------------------------------------------------------------
    def _disk_yukle(self):
        self.aktif_stage = 1
        self._disk_resmi_yukle(self.aktif_stage)

    def _disk_resmi_yukle(self, stage_no: int):
        if hasattr(self, "disk_grup") and self.disk_grup is not None:
            self.sahne.removeItem(self.disk_grup)

        yol_disk = os.path.join(self.disk_dizin, f"stage{stage_no}.jpeg")
        pixmap_disk = QPixmap(yol_disk)
        if pixmap_disk.isNull():
            print(f"HATA: Disk bulunamadı → {yol_disk}")
            sys.exit(1)
        
        # NumPy ile yüksek hızlı piksel filtreleme uyguluyoruz
        disk_resmi = pixmap_disk.toImage().convertToFormat(QtGui.QImage.Format.Format_ARGB32)
        genislik = disk_resmi.width()
        yukseklik = disk_resmi.height()
        
        ptr = disk_resmi.bits()
        ptr.setsize(yukseklik * genislik * 4)
        arr = np.frombuffer(ptr, np.uint8).reshape((yukseklik, genislik, 4))
        
        # ARGB32 formatında: arr[..., 0] -> B, arr[..., 1] -> G, arr[..., 2] -> R, arr[..., 3] -> A
        b = arr[..., 0]
        g = arr[..., 1]
        r = arr[..., 2]
        
        # Beyaz ve beyaza yakın tonları bul (R>225, G>225, B>225)
        beyaz_maske = (r > 225) & (g > 225) & (b > 225)
        
        # Yol ortasındaki şerit rengini koru (#E5E3CE -> R:229, G:227, B:206)
        serit_maske = (np.abs(r.astype(np.int16) - 229) < 15) & \
                      (np.abs(g.astype(np.int16) - 227) < 15) & \
                      (np.abs(b.astype(np.int16) - 206) < 15)
        
        # Şerit olmayan beyaz alanların Alpha (şeffaflık) kanalını 0 yap
        silinecek_maske = beyaz_maske & ~serit_maske
        arr[silinecek_maske, 3] = 0
        
        pixmap_disk = QPixmap.fromImage(disk_resmi)

        yol_maske = os.path.join(self.disk_dizin, f"stage{stage_no}mask.png")
        pixmap_maske = QPixmap(yol_maske)
        if pixmap_maske.isNull():
            print(f"HATA: Maske bulunamadı → {yol_maske}")
            sys.exit(1)

        self.disk_item  = QGraphicsPixmapItem(pixmap_disk)
        self.maske_item = QGraphicsPixmapItem(pixmap_maske)
        self.maske_item.setVisible(False)

        self.disk_grup = QGraphicsItemGroup()
        self.disk_grup.addToGroup(self.disk_item)
        self.disk_grup.addToGroup(self.maske_item)

        self.disk_grup.setTransformOriginPoint(
            DISK_ORIJINAL / 2,
            DISK_ORIJINAL / 2
        )
        self.disk_grup.setScale(DISK_OLCEK)

        gorunen_yari = int(DISK_ORIJINAL * DISK_OLCEK / 2)
        self.disk_grup.setPos(
            DISK_MERKEZ_X - gorunen_yari,
            DISK_MERKEZ_Y - gorunen_yari,
        )
        self.disk_grup.setZValue(1)
        self.sahne.addItem(self.disk_grup)
        print(f"Disk ve maske yüklendi: stage{stage_no}")

    # ------------------------------------------------------------------
    # ARABA
    # ------------------------------------------------------------------
    def _araba_yukle(self):
        # Eğer main.py üzerinden bir araba seçilip argüman yollandıysa onu kullan, yoksa random seç
        if len(sys.argv) > 1 and sys.argv[1].endswith(".png"):
            secilen = sys.argv[1]
        else:
            arabalar = [f for f in os.listdir(os.path.join(self.dizin, "cars")) if f.endswith(".png")]
            secilen = random.choice(arabalar) if arabalar else ""
        yol = os.path.join(self.dizin, "cars", secilen)
        pixmap = QPixmap(yol)
        pixmap = pixmap.scaled(
            pixmap.width() // 2,
            pixmap.height() // 2,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        goruntu = pixmap.toImage()
        araba_eni  = goruntu.width()
        araba_boyu = goruntu.height()
        orta_x = araba_eni // 2
        burun_y = 0
        for y in range(araba_boyu):
            if goruntu.pixelColor(orta_x, y).alpha() > 10:
                burun_y = y
                break

        self.kamera_offset_x = orta_x
        self.kamera_offset_y = burun_y + 3

        self.araba_item = QGraphicsPixmapItem(pixmap)
        # Arabanın rotasyon merkezini kameranın (burnunun) olduğu yere sabitleyelim
        self.araba_item.setTransformOriginPoint(self.kamera_offset_x, self.kamera_offset_y)
        self.araba_item.setZValue(2)
        self.araba_item.setPos(self.araba_x, self.araba_y)
        self.sahne.addItem(self.araba_item)
        print(f"Araba: {secilen}  boyut: {araba_eni}x{araba_boyu}  kamera offset: {self.kamera_offset_x},{self.kamera_offset_y}")
        self.effects_dizin = os.path.join(self.dizin, "effects")
        self.gif_yollari = {
            "explosion": os.path.join(self.effects_dizin, "explosion.gif"),
            "friction": os.path.join(self.effects_dizin, "friction.gif"),
            "jungle": os.path.join(self.effects_dizin, "jungle.gif"),
            "water": os.path.join(self.effects_dizin, "water.gif")
        }
        
        self.gif_movies = {}
        self.gif_proxies = {}

        gif_boyut = QSize(GIF_GENISLIK, GIF_YUKSEKLIK)
        
        for key, yol in self.gif_yollari.items():
            movie = QMovie(yol)
            movie.setScaledSize(gif_boyut)
            self.gif_movies[key] = movie
            
            label = QLabel()
            label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            label.setMovie(movie)
            
            proxy = QGraphicsProxyWidget()
            proxy.setWidget(label)
            proxy.setZValue(3)  # Arabanın hemen üstünde görünmesi için
            proxy.setTransformOriginPoint(GIF_GENISLIK // 2, (GIF_YUKSEKLIK // 2) - GIF_Y_GERI_CEKME)
            proxy.setVisible(False)
            
            self.sahne.addItem(proxy)
            self.gif_proxies[key] = proxy
            
        self.aktif_gif_key = None
        # GIF efektlerinin ilk girişte gecikmesini önlemek için önbelleğe alma (Pre-load) işlemi
        for key in self.gif_movies:
            self.gif_movies[key].start()
            self.gif_movies[key].stop()

    # ------------------------------------------------------------------
    # PANEL DURUM GEÇİŞİ
    # ------------------------------------------------------------------
    def _gif_efekti_kapat(self):
        if self.aktif_gif_key and self.aktif_gif_key in self.gif_proxies:
            self.gif_movies[self.aktif_gif_key].stop()
            self.gif_proxies[self.aktif_gif_key].setVisible(False)
            self.aktif_gif_key = None

    def _gif_efekti_ac(self, gif_key: str):
        if self.aktif_gif_key == gif_key:
            return
        self._gif_efekti_kapat()
        if gif_key in self.gif_proxies:
            self.gif_proxies[gif_key].setVisible(True)
            self.gif_movies[gif_key].jumpToFrame(0)  # Efektin her seferinde en baştan başlamasını sağlar
            self.gif_movies[gif_key].start()
            self.aktif_gif_key = gif_key
    
    def oyunu_yeniden_baslat(self):
        """Çarpmadan sonra arabayı ve diski eski konumuna getirir ve hazırda bekletir."""
        self._gif_efekti_kapat()
        self.tur_yazisi.setPlainText("PRESS W TO START")
        self.guncel_tur = 0
        
        # Pozisyonları ve hızları sıfırla
        self.araba_x = DISK_MERKEZ_X - 135
        self.araba_y = DISK_MERKEZ_Y + 410
        self.araba_item.setPos(self.araba_x, self.araba_y)
        self.araba_item.setRotation(0.0)
        self.araba_guncel_aci = 0.0
        self.araba_hedef_aci = 0.0
        
        self.aci = 0.0
        self.disk_grup.setRotation(self.aci)
        self.guncel_hiz = DONME_HIZI
        
        # Pili yeniden başlangıç seviyesine getiriyoruz ve turları sıfırlıyoruz
        self.pil_seviyesi = 85.0
        self.pil_bitti = False
        self.guncel_tur = 0
        
        # Kullanıcının W tuşuna basmasını beklemek için bayrakları indiriyoruz
        self.w_basili = False
        self.s_basili = False
        self.araba_item.setVisible(True)
        self.panel_durumu_guncelle("off")
        
        # Sesleri tamamen temizle ve sahne müziğini yeniden başlat edin
        self.chan_muzik.stop()
        self.chan_motor.stop()
        self.chan_zemin.stop()
        self.aktif_motor_sesi = None
        self.aktif_zemin_sesi = None
        
        if self.aktif_stage in self.snd_stages_muzik:
            self.chan_muzik.play(self.snd_stages_muzik[self.aktif_stage], loops=-1)
        
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._ilk_hareket = True
        
        # En son kilidi kaldırıyoruz ki yeni kare işlenebilsin
        self.carpiyor_mu = False
        self.yaris_bitti = False  # Yarış bitti bayrağını sıfırla ki W tekrar çalışsın
        self._ibre_guncelle()
        self.oyun_basladi = False
    
    def panel_durumu_guncelle(self, yeni_durum: str):
        if yeni_durum == self.durum:
            return
        if self.durum in self.panel_itemlar:
            self.panel_itemlar[self.durum].setVisible(False)
        if yeni_durum in self.panel_itemlar:
            self.panel_itemlar[yeni_durum].setVisible(True)
        self.durum = yeni_durum

    # ------------------------------------------------------------------
    # RENK OKU
    # ------------------------------------------------------------------
    def _renk_oku(self):
        sahne_x = self.araba_x + self.kamera_offset_x
        sahne_y = self.araba_y + self.kamera_offset_y

        self.disk_item.setVisible(False)
        self.araba_item.setVisible(False)
        self.maske_item.setVisible(True)

        from PyQt6.QtCore import QRectF
        from PyQt6.QtGui import QPainter
        
        hedef_alan = QRectF(sahne_x, sahne_y, 1, 1)
        anlik_pixmap = QPixmap(1, 1)
        painter = QPainter(anlik_pixmap)
        self.sahne.render(painter, QRectF(0, 0, 1, 1), hedef_alan)
        painter.end()

        self.disk_item.setVisible(True)
        self.araba_item.setVisible(True)
        self.maske_item.setVisible(False)

        img = anlik_pixmap.toImage()
        renk = img.pixelColor(0, 0)
        return renk.red(), renk.green(), renk.blue()

    def sonraki_bolume_gec(self):
        """Bir sonraki stage bilgilerini yükler ve oyunu başlatır."""
        # Bölüm geçildiğinde, maksimum can sınırına ulaşılana kadar her zaman 1 can ver
        if self.guncel_can < self.toplam_can:
            self.guncel_can += 1
            yeni_yildiz = QGraphicsPixmapItem(self.pixmap_yildiz)
            # Mevcut yıldız listesindeki son yıldızın konumuna göre X koordinatını hesapla
            yeni_yildiz.setPos(20 + ((self.guncel_can - 1) * 50), 20)
            yeni_yildiz.setZValue(10)
            self.sahne.addItem(yeni_yildiz)
            self.yildiz_itemlar.append(yeni_yildiz)
        self.aktif_stage += 1
        if self.aktif_stage > 5:
            self.aktif_stage = 1
        
        # Diski ve maskeyi güncelle
        self._disk_resmi_yukle(self.aktif_stage)
        
        # Müziği güncelle
        self.chan_muzik.stop()
        if self.aktif_stage in self.snd_stages_muzik:
            self.chan_muzik.play(self.snd_stages_muzik[self.aktif_stage], loops=-1)
        
        # Oyunu sıfırla ve başlatmaya hazır hale getir
        self.oyunu_yeniden_baslat()
        self.tur_yazisi.setPlainText("PRESS W TO START")

    def _tur_bitti_diyalog_ac(self):
        """Tur tamamlandığında açılan tebrik ve yönlendirme diyalogu."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.chan_muzik.stop()
        
        diyalog = QDialog(self)
        diyalog.setWindowTitle("Congratulations!")
        diyalog.setFixedSize(350, 250) # Yıldız için biraz alan açtık
        diyalog.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # paintEvent kullanarak arka planı ve yıldızı çiz
        def diyalog_paint_event(event):
            from PyQt6.QtGui import QPainter
            painter = QPainter(diyalog)
            yol_arka_plan = os.path.join(self.disk_dizin, "cardboarddialogbase.jpg")
            diyalog_bg = QPixmap(yol_arka_plan)
            
            if not diyalog_bg.isNull():
                painter.drawPixmap(diyalog.rect(), diyalog_bg)
            
            # Yıldız resmini merkeze çiz
            if not self.pixmap_yildiz.isNull():
                yildiz_w = 60
                yildiz_h = 60
                x = (diyalog.width() - yildiz_w) // 2
                y = 15
                painter.drawPixmap(x, y, yildiz_w, yildiz_h, self.pixmap_yildiz)
            painter.end()
            
        diyalog.paintEvent = diyalog_paint_event
        
        layout = QVBoxLayout()
        layout.addSpacing(80) # Yıldızın altındaki boşluk
        
        mesaj = QLabel(f"You successfully completed the lap!\nStage {self.aktif_stage} finished.")
        mesaj.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QtGui.QFont("Liberation Sans", 12, QtGui.QFont.Weight.Bold)
        mesaj.setFont(font)
        layout.addWidget(mesaj)
        
        buton_layout = QHBoxLayout()
        btn_sonraki = QPushButton("Next Lap")
        btn_ana_ekran = QPushButton("Main Menu")
        btn_cikis = QPushButton("Exit")
        
        btn_sonraki.clicked.connect(lambda: [
            self.chan_efekt.stop(),
            self.sonraki_bolume_gec(),
            diyalog.accept()
        ])
        
        btn_ana_ekran.clicked.connect(lambda: [
            subprocess.Popen([sys.executable, os.path.join(self.dizin, "main.py")]),
            diyalog.accept(),
            self.close()
        ])
        
        btn_cikis.clicked.connect(lambda: QApplication.instance().quit())
        
        buton_layout.addWidget(btn_sonraki)
        buton_layout.addWidget(btn_ana_ekran)
        buton_layout.addWidget(btn_cikis)
        
        layout.addLayout(buton_layout)
        diyalog.setLayout(layout)
        diyalog.exec()

    def _oyun_bitti_diyalog_ac(self):
        """Tüm turlar tamamlandığında açılan final diyalogu."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.chan_muzik.stop()
        self.chan_efekt.play(self.snd_star_of_the_game)
        
        diyalog = QDialog(self)
        diyalog.setWindowTitle("Game Completed!")
        diyalog.setFixedSize(350, 300) # Resim için yüksekliği biraz artırdık
        diyalog.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Kupa resmini yükle
        yol_kupa = os.path.join(self.effects_dizin, "kupa.png")
        kupa_pixmap = QPixmap(yol_kupa)
        
        # paintEvent kullanarak resmi ve arka planı çiz
        def diyalog_paint_event(event):
            from PyQt6.QtGui import QPainter
            painter = QPainter(diyalog)
            # Karton arka planı çiz
            yol_bg = os.path.join(self.disk_dizin, "cardboarddialogbase.jpg")
            bg_pix = QPixmap(yol_bg)
            if not bg_pix.isNull():
                painter.drawPixmap(diyalog.rect(), bg_pix)
            else:
                # Eğer resim yoksa arka planı biraz daha belirgin yap
                painter.fillRect(diyalog.rect(), QColor(50, 50, 50))
            
            # Kupa resmini merkeze yakın çiz
            if not kupa_pixmap.isNull():
                kupa_w = 100
                kupa_h = 100
                x = (diyalog.width() - kupa_w) // 2
                y = 20
                painter.drawPixmap(x, y, kupa_w, kupa_h, kupa_pixmap)
            painter.end()
            
        diyalog.paintEvent = diyalog_paint_event
        
        layout = QVBoxLayout()
        # Resmi içine alacak boşluk (layoutta üst kısım boş kalsın diye)
        layout.addSpacing(120) 
        
        mesaj = QLabel("You completed the game, congratulations!")
        mesaj.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mesaj)
        
        buton_layout = QHBoxLayout()
        btn_ana_ekran = QPushButton("Main Menu")
        btn_cikis = QPushButton("Exit")
        
        btn_ana_ekran.clicked.connect(lambda: [
            subprocess.Popen([sys.executable, os.path.join(self.dizin, "main.py")]),
            diyalog.accept(),
            self.close()
        ])
        btn_cikis.clicked.connect(lambda: QApplication.instance().quit())
        
        buton_layout.addWidget(btn_ana_ekran)
        buton_layout.addWidget(btn_cikis)
        layout.addLayout(buton_layout)
        diyalog.setLayout(layout)
        diyalog.exec()

    # ------------------------------------------------------------------
    # ANA DÖNGÜ
    # ------------------------------------------------------------------
    def _guncelle(self):
        if hasattr(self, "carpiyor_mu") and self.carpiyor_mu:
            # Canlar bittiyse ve yazı GAME OVER ise animasyonların sızmasını engelle
            if self.guncel_can <= 0:
                self.tur_yazisi.setPlainText("GAME OVER")
            return
        # Yumuşak yaylanma efektiyle arabanın kıçını hedef konuma döndürüyoruz (Yaklaşma payı düşürüldü)
        self.araba_guncel_aci += (self.araba_hedef_aci - self.araba_guncel_aci) * 0.12
        
        self.araba_item.setPos(self.araba_x, self.araba_y)
        
        # Dönüş merkezi eşitlendiği için artık sadece düz hizalama yapıyoruz
        gif_x = self.araba_x + (self.kamera_offset_x - (GIF_GENISLIK // 2))
        gif_y = self.araba_y + (self.kamera_offset_y - (GIF_YUKSEKLIK // 2)) + GIF_Y_GERI_CEKME
        
        for proxy in self.gif_proxies.values():
            proxy.setPos(gif_x, gif_y)
            proxy.setRotation(self.araba_guncel_aci)
        self.araba_item.setRotation(self.araba_guncel_aci)
        
        # Fare durduğunda arabanın hemen merkeze çökmemesi için sönümlenme payını esnettik
        self.araba_hedef_aci *= 0.92

        if not self.oyun_basladi or self.oyun_durdu:
            return

        # EĞER PİL BİTTİYSE: Pil bittiğinde aracı durdur, 2 saniye beklet ve can eksilterek resetle
        if self.pil_bitti:
            self.guncel_hiz *= 0.95
            if abs(self.guncel_hiz) < 0.01:
                self.guncel_hiz = 0.0
                self.oyun_basladi = False
                self.pil_bitti = False # Flag'i temizle
                
                # Çarpma mekanizmasını tetikle (Can düşür ve 2 sn sonra resetle)
                self.carpiyor_mu = True
                self.panel_durumu_guncelle("off")
                self.chan_motor.stop()
                self.chan_zemin.stop()
                self._gif_efekti_kapat()
                
                self.guncel_can -= 1
                if len(self.yildiz_itemlar) > 0:
                    silinecek_yildiz = self.yildiz_itemlar.pop()
                    self.sahne.removeItem(silinecek_yildiz)
                
                if self.guncel_can > 0:
                    self.tur_yazisi.setPlainText("BATTERY DEAD!")
                    QTimer.singleShot(2000, self.oyunu_yeniden_baslat)
                else:
                    self.tur_yazisi.setPlainText("GAME OVER")
                    print("Pil bitti ve tüm canlar tükendi.")
                    QTimer.singleShot(3000, lambda: [
                    subprocess.Popen([sys.executable, os.path.join(self.dizin, "main.py")]),
                    QApplication.instance().quit()
                ])
                return

            self.aci += self.guncel_hiz
            self.disk_grup.setRotation(self.aci)
            return

        # 1. ADIM: Önce arabanın altındaki rengi oku
        r, g, b = self._renk_oku()

        # 2. ADIM: Renge göre zemin hız çarpanını, panel durumunu veya patlamayı belirle
        zemin_carpani = 1.0
        zemin_paneli = "normal"
        engel_durumu = False

        if renk_esit(r, g, b, 157, 21, 20):
            # KIRMIZI → Çarpma ve can düşürme mekanizması
            self.carpiyor_mu = True
            self.oyun_basladi = False
            self.w_basili = False
            self.s_basili = False
            self.panel_durumu_guncelle("off")
            self.araba_item.setVisible(False)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Donanımdaki tüm aktif ses çalma işlemlerini anında sıfırlıyoruz
            pygame.mixer.stop()
            pygame.mixer.fadeout(50)
            self.chan_muzik.stop()
            self.chan_motor.stop()
            self.chan_zemin.stop()
            self.aktif_motor_sesi = None
            self.aktif_zemin_sesi = None
            
            # Sadece patlama sesini ve animasyonunu tetikliyoruz
            self.chan_efekt.play(self.snd_explosion)
            self._gif_efekti_ac("explosion")
            
            # Canı bir azalt
            self.guncel_can -= 1
            # Eğer listede yıldız varsa, her zaman en sonuncuyu (en sağdakini) listeden çıkar ve sahneden sil
            if len(self.yildiz_itemlar) > 0:
                silinecek_yildiz = self.yildiz_itemlar.pop()
                self.sahne.removeItem(silinecek_yildiz)
            
            if self.guncel_can > 0:
                self.guncel_tur = 0
                self.tur_yazisi.setPlainText("CRASHED!")
                # 2 saniye sonra oyunu sıfırlayıp PRESS W moduna alıyoruz
                QTimer.singleShot(2000, self.oyunu_yeniden_baslat)
            else:
                self.tur_yazisi.setPlainText("GAME OVER")
                QTimer.singleShot(3000, lambda: [
                    subprocess.Popen([sys.executable, os.path.join(self.dizin, "main.py")]),
                    QApplication.instance().quit()
                ])
                
            return
            
        elif renk_esit(r, g, b, 113, 113, 113):
            # GRİ → %75 hız
            zemin_carpani = 0.75
            zemin_paneli = "overload1"
            engel_durumu = True
            
        elif renk_esit(r, g, b, 40, 124, 0):
            # YEŞİL → %50 hız
            zemin_carpani = 0.50
            zemin_paneli = "overload1"
            engel_durumu = True
            
        elif renk_esit(r, g, b, 0, 40, 255):
            # MAVİ → %50 hız
            zemin_carpani = 0.50
            zemin_paneli = "overload1"
            engel_durumu = True
            
        elif renk_esit(r, g, b, 0, 0, 0):
            zemin_carpani = 1.0
            zemin_paneli = "normal"
            # Engel tipini belirle
        self.engel_tipi = None
        if renk_esit(r, g, b, 113, 113, 113): self.engel_tipi = "gri"
        elif renk_esit(r, g, b, 40, 124, 0): self.engel_tipi = "yesil"
        elif renk_esit(r, g, b, 0, 40, 255): self.engel_tipi = "mavi"

        hedef_gif_key = None
        hedef_zemin_sesi = None

        if renk_esit(r, g, b, 113, 113, 113):
            hedef_gif_key = "friction"
            hedef_zemin_sesi = self.snd_grey
        elif renk_esit(r, g, b, 40, 124, 0):
            hedef_gif_key = "jungle"
            hedef_zemin_sesi = self.snd_jungle
        elif renk_esit(r, g, b, 0, 40, 255):
            hedef_gif_key = "water"
            hedef_zemin_sesi = self.snd_water

        if hedef_gif_key:
            self._gif_efekti_ac(hedef_gif_key)
        else:
            self._gif_efekti_kapat()

        # 3. ADIM: Tuş durumuna göre hızı ve sol paneli belirle

        if hedef_zemin_sesi != self.aktif_zemin_sesi:
            self.chan_zemin.stop()
            if hedef_zemin_sesi is not None:
                self.chan_zemin.play(hedef_zemin_sesi, loops=-1)
            self.aktif_zemin_sesi = hedef_zemin_sesi

        if hedef_zemin_sesi is not None:
            hedef_motor_sesi = None
        else:
            hedef_motor_sesi = self.snd_engine
            if self.s_basili:
                hedef_motor_sesi = self.snd_engine_overload
            elif self.w_basili:
                hedef_motor_sesi = self.snd_engine_speed

        if hedef_motor_sesi != self.aktif_motor_sesi:
            self.chan_motor.stop()
            if hedef_motor_sesi is not None:
                self.chan_motor.play(hedef_motor_sesi, loops=-1)
            self.aktif_motor_sesi = hedef_motor_sesi
        if self.s_basili:
            self.guncel_hiz = FREN_HIZI
            self.panel_durumu_guncelle("overload2")
        else:
            self.guncel_hiz = HIZLANMA_HIZI * zemin_carpani if self.w_basili else DONME_HIZI * zemin_carpani
            self.panel_durumu_guncelle(zemin_paneli)

        # 4. ADIM: Enerji Tüketim Matematiği
        # Baz tüketim değerleri (her karede düşecek pil miktarı)
        if self.s_basili:
            tuketim = 0.23      # Fren tüketimi artırıldı
        elif self.engel_tipi:
            if self.w_basili:
                if self.engel_tipi == "gri": tuketim = 0.12
                elif self.engel_tipi == "yesil": tuketim = 0.15
                elif self.engel_tipi == "mavi": tuketim = 0.18
            else:
                if self.engel_tipi == "gri": tuketim = 0.07
                elif self.engel_tipi == "yesil": tuketim = 0.08
                elif self.engel_tipi == "mavi": tuketim = 0.09
        else:
            if self.w_basili:
                tuketim = 0.032  # Düz yolda gaz tüketimi artırıldı
            else:
                tuketim = 0.023  # Düz yolda boşta akış tüketimi artırıldı
                # Bu değerler çocuklar için fazla ağır olmuş olabilir
                # Gelen değerlendirmelere göre tekrar bakıcam.

        # Pili düş ve ibreyi sahne üzerinde kaydır
        self.pil_seviyesi -= tuketim
        if self.pil_seviyesi <= 0.0:
            self.pil_seviyesi = 0.0
            self.pil_bitti = True
            self.panel_durumu_guncelle("off")
            print("PİL BİTTİ! Motor gücü kesildi, araç süzülüyor...")
            self.chan_motor.stop()
        
        self._ibre_guncelle()

        # 5. ADIM: Diski döndür
        self.aci += self.guncel_hiz
        if self.aci <= -360.0:
            self.aci += 360.0
            self.tur_yazisi.setPlainText("") # Asenkron timer yerine açıyı sıfırlarken temizliyoruz
            if self.oyun_basladi and not self.oyun_durdu and not self.pil_bitti:
                self.guncel_tur += 1
                # Eğer toplam tura ulaşıldıysa yarışı kesin olarak bitir ve güncellemeden çık
                if self.guncel_tur == self.toplam_tur:
                    self._gif_efekti_kapat()
                    self.panel_durumu_guncelle("off")
                    self.chan_muzik.stop()
                    self.chan_motor.stop()
                    self.chan_zemin.stop()
                    self.chan_efekt.play(self.snd_stage_clear)
                    self.oyun_basladi = False
                    self.yaris_bitti = True
                    self.w_basili = False
                    self.s_basili = False
                    if self.aktif_stage >= 5:
                        QTimer.singleShot(100, self._oyun_bitti_diyalog_ac)
                    else:
                        QTimer.singleShot(100, self._tur_bitti_diyalog_ac)
                    return
                elif self.guncel_tur < self.toplam_tur:
                    self.tur_yazisi.setPlainText(f"LAP {self.guncel_tur} / {self.toplam_tur}")
                    QTimer.singleShot(3000, lambda: self.tur_yazisi.setPlainText(""))
        self.disk_grup.setRotation(self.aci)

    # ------------------------------------------------------------------
    # FARE HAREKETİ
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        if self.oyun_basladi and not self.oyun_durdu:
            if self._fare_merkezleniyor:
                self._fare_merkezleniyor = False
                super().mouseMoveEvent(event)
                return

            from PyQt6.QtGui import QCursor

            merkez_global = self.mapToGlobal(self.rect().center())
            anlik_global = QCursor.pos()

            if self._ilk_hareket:
                self._ilk_hareket = False
                self._fare_merkezleniyor = True
                QCursor.setPos(merkez_global)
                super().mouseMoveEvent(event)
                return

            fark_x = anlik_global.x() - merkez_global.x()

            if fark_x != 0:
                self.araba_x += fark_x
                self.araba_x = max(min(self.araba_x, DISK_MERKEZ_X + 250), DISK_MERKEZ_X - 200)
                
                savrulma_miktari = fark_x * 12.0
                self.araba_hedef_aci = max(min(savrulma_miktari, 200.0), -200.0)

                self._fare_merkezleniyor = True
                QCursor.setPos(merkez_global)

        super().mouseMoveEvent(event)

    # ------------------------------------------------------------------
    # KLAVYE
    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        tus = event.key()
        
        if tus == Qt.Key.Key_Escape:
            self.close()
            return

        if tus == Qt.Key.Key_P and self.oyun_basladi and not self.pil_bitti:
            self.oyun_durdu = not self.oyun_durdu
            if self.oyun_durdu:
                self.chan_muzik.pause()
                self.chan_motor.pause()
                self.chan_zemin.pause()
                self.setCursor(Qt.CursorShape.ArrowCursor)
                if self.aktif_gif_key:
                    self.gif_movies[self.aktif_gif_key].setPaused(True)
                self._ilk_hareket = True
                print("Oyun Durduruldu (PAUSE)")
            else:
                self.setCursor(Qt.CursorShape.BlankCursor)
                if self.aktif_gif_key:
                    self.gif_movies[self.aktif_gif_key].setPaused(False)
                print("Oyun Devam Ediyor")
                self.chan_muzik.unpause()
                self.chan_motor.unpause()
                self.chan_zemin.unpause()
            return

        if self.pil_bitti or self.yaris_bitti:
            super().keyPressEvent(event)
            return

        if tus == Qt.Key.Key_W:
            # Eğer araba çarpmışsa veya yarış zaten bitmişse W tuşunu tamamen engelle
            if (hasattr(self, "carpiyor_mu") and self.carpiyor_mu) or self.yaris_bitti:
                super().keyPressEvent(event)
                return
                
            if not self.oyun_basladi:
                from PyQt6.QtGui import QCursor
                
                # W tuşuna basıldığı an ekrandaki hazırlık yazısını siliyoruz
                self.tur_yazisi.setPlainText("")
                
                merkez_global = self.mapToGlobal(self.rect().center())
                self._is_resetting_mouse = True
                QCursor.setPos(merkez_global)
                
                self.oyun_basladi = True
                self.araba_item.setVisible(True)
                self.panel_durumu_guncelle("normal")
                self.chan_motor.play(self.snd_engine, loops=-1)
                self.aktif_motor_sesi = self.snd_engine
                self.setCursor(Qt.CursorShape.BlankCursor)
            if not self.oyun_durdu:
                self.w_basili = True
                
        elif tus == Qt.Key.Key_S:
            if self.oyun_basladi and not self.oyun_durdu:
                self.s_basili = True
                self.panel_durumu_guncelle("overload2")
                
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        tus = event.key()
        if tus == Qt.Key.Key_W:
            self.w_basili = False
        elif tus == Qt.Key.Key_S:
            self.s_basili = False
            if self.oyun_basladi and not self.oyun_durdu and not self.pil_bitti:
                self.panel_durumu_guncelle("normal")
        super().keyReleaseEvent(event)


# ---------------------------------------------------------------------------
# GİRİŞ NOKTASI
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    pencere = AnaPencere()
    pencere.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
