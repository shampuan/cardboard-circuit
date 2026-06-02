#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import pygame
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDialog, QProgressBar, QGridLayout
)
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtCore import Qt, QTimer

# Wayland ve modern masaüstü ortamları için uyumluluk ayarları
if "GNOME" in os.environ.get("XDG_CURRENT_DESKTOP", ""):
    os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

# SABİTLER (Ses seviyesini ayarlamak için sonradan ekledim)
VOL_ANA_MENU_MUZIK = 0.4 # Buraya artık ellemeyelim bu iyi.

class YardimDialog(QDialog):
    """Oyun tuşlarını gösteren yardım penceresi."""
    def __init__(self, ebeveyn=None):
        super().__init__(ebeveyn)
        self.setWindowTitle("Help - Controls")
        self.setFixedSize(400, 400)
        self.setModal(True)
        
        düzen = QVBoxLayout(self)
        
        baslik = QLabel("GAME CONTROLS")
        baslik.setFont(QFont("Liberation Sans", 16, QFont.Weight.Bold))
        baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        düzen.addWidget(baslik)
        
        icerik = QLabel(
            "W: Start Game / Accelerate\n"
            "Mouse: Steer Left / Right\n"
            "S: Brake\n"
            "P: Pause\n"
            "Esc: Exit Game\n\n"
            "Tips:\n"
            "Grey areas slow you down by 0.12 amount.\n"
            "Green areas slow you down by 0.15 amount.\n"
            "Water areas slow you down by 0.18 amount.\n"
            "Braking causes the most slowdown (0.23 amount).\n"
            "These four factors drain the battery faster.\n"
            "Avoid braking or entering colored areas.\n"
            "Accelerating helps conserve the battery."
        )
        icerik.setFont(QFont("Liberation Sans", 11))
        icerik.setAlignment(Qt.AlignmentFlag.AlignLeft)
        düzen.addWidget(icerik)
        
        kapat_buton = QPushButton("OK")
        kapat_buton.setFont(QFont("Liberation Sans", 11))
        kapat_buton.clicked.connect(self.close)
        düzen.addWidget(kapat_buton)

class HakkindaDialog(QDialog):
    """Program hakkında bilgiler içeren pencere."""
    def __init__(self, ebeveyn=None):
        super().__init__(ebeveyn)
        self.setWindowTitle("About")
        self.setFixedSize(450, 400)
        self.setModal(True)
        
        düzen = QVBoxLayout(self)
        
        baslik = QLabel("About Cardboard Circuit")
        baslik.setFont(QFont("Liberation Sans", 16, QFont.Weight.Bold))
        baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        düzen.addWidget(baslik)
        
        icerik = QLabel(
            "Version: 1.0.0\n"
            "License: GNU GPLv3\n"
            "GUI/UX: Python3 Qt6\n"
            "Developer: A. Serhat KILIÇOĞLU (shampuan)\n"
            "Github: www.github.com/shampuan\n\n"
            "This is a fun racing game developed for children aged 6-12.\n"
            "Supported with stage music and sound effects.\n"
            "Content is completely free licensed.\n\n"
            "This program comes with no warranty.\n\n"
            "Copyright © 2026 - A. Serhat KILIÇOĞLU"
        )
        icerik.setFont(QFont("Liberation Sans", 11))
        icerik.setAlignment(Qt.AlignmentFlag.AlignLeft)
        düzen.addWidget(icerik)
        
        kapat_buton = QPushButton("OK")
        kapat_buton.setFont(QFont("Liberation Sans", 11))
        kapat_buton.clicked.connect(self.close)
        düzen.addWidget(kapat_buton)

class SplashEkran(QDialog):
    """Oyun yüklenirken ekranda beliren çerçevesiz yükleme ekranı."""
    def __init__(self, dosya_yolu, ebeveyn=None):
        super().__init__(ebeveyn)
        # Pencere kenarlıklarını, başlığını ve butonlarını tamamen kaldırır
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        düzen = QVBoxLayout(self)
        düzen.setContentsMargins(0, 0, 0, 0)
        
        etiket = QLabel(self)
        pixmap = QPixmap(dosya_yolu)
        if not pixmap.isNull():
            etiket.setPixmap(pixmap)
            self.setFixedSize(pixmap.width(), pixmap.height())
        else:
            self.setFixedSize(600, 400) # Görsel bulunamazsa varsayılan boyut
            
        düzen.addWidget(etiket)

class ArabaButon(QPushButton):
    """Seçilebilir araba resmini barındıran ve parlama efekti taklit eden özel buton."""
    def __init__(self, dosya_adi, dosya_yolu, ebeveyn=None):
        super().__init__(ebeveyn)
        self.dosya_adi = dosya_adi
        self.setFixedSize(90, 110)
        self.setCheckable(True)
        
        # Seçim durumunu belli etmek için kenarlık rengiyle oynamak yerine 
        # arka plan rengini Qt'un varsayılan paletiyle uyumlu şekilde değiştireceğiz
        self.setAutoFillBackground(True)
        
        düzen = QVBoxLayout(self)
        düzen.setContentsMargins(5, 5, 5, 5)
        
        # Araba İkonu
        self.ikon_etiket = QLabel()
        pixmap = QPixmap(dosya_yolu)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.ikon_etiket.setPixmap(pixmap)
        self.ikon_etiket.setAlignment(Qt.AlignmentFlag.AlignCenter)
        düzen.addWidget(self.ikon_etiket)
        
        # Araba İsmi (Uzantısız)
        isim_etiket = QLabel(os.path.splitext(dosya_adi)[0].capitalize())
        isim_etiket.setFont(QFont("Liberation Sans", 9, QFont.Weight.Bold))
        isim_etiket.setAlignment(Qt.AlignmentFlag.AlignCenter)
        düzen.addWidget(isim_etiket)

class AnaEkran(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cardboard Circuit - Main Menu")
        self.setFixedSize(850, 550) # Karton resminin tam boyutu
        
        self.dizin = os.path.dirname(os.path.abspath(__file__))
        self.cars_dizin = os.path.join(self.dizin, "cars")
        self.disks_dizin = os.path.join(self.dizin, "disks")
        self.sounds_dizin = os.path.join(self.dizin, "sounds")
        
        # Başlangıç Müziğini Çal
        pygame.mixer.init()
        self.snd_main_screen = pygame.mixer.Sound(os.path.join(self.sounds_dizin, "main-screen.ogg"))
        self.snd_main_screen.set_volume(VOL_ANA_MENU_MUZIK)
        self.snd_main_screen.play(loops=-1)
        
        self.secilen_araba = None
        self._arayüz_olustur()
        # İkonu ana dizinde bul ve ayarla
        ikon_yolu = os.path.join(self.dizin, "caricon.png")
        if os.path.exists(ikon_yolu):
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(ikon_yolu))
        
    def _arayüz_olustur(self):
        # Arka Plan Karton Resmi
        self.arka_plan = QLabel(self)
        yol_karton = os.path.join(self.disks_dizin, "cardboarddialogbase.jpg")
        pixmap_karton = QPixmap(yol_karton)
        if not pixmap_karton.isNull():
            self.arka_plan.setPixmap(pixmap_karton)
        self.arka_plan.setGeometry(0, 0, 850, 550)
        
        # Ana Widget ve Düzenleyici
        merkez_widget = QWidget(self)
        merkez_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCentralWidget(merkez_widget)
        
        ana_düzen = QVBoxLayout(merkez_widget)
        ana_düzen.setContentsMargins(30, 20, 30, 20)
        
        # Başlık Resmini Yükle ve Konumlandır
        self.baslik_resmi_etiketi = QLabel()
        yol_baslik_resmi = os.path.join(self.disks_dizin, "cardboardcircuitmenu.jpg")
        pixmap_baslik = QPixmap(yol_baslik_resmi)
        if not pixmap_baslik.isNull():
            # Orijinal boyutları koruyarak (1376x768), pencere genişliğine (850) göre ölçeklendirelim.
            ölçekli_pixmap = pixmap_baslik.scaled(450, 200, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.baslik_resmi_etiketi.setPixmap(ölçekli_pixmap)
        self.baslik_resmi_etiketi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Orijinal başlık metnini kaldırıp resim etiketini ekle
        # ana_düzen.addWidget(self.baslik) # Bu satırı kaldırdık.
        ana_düzen.addWidget(self.baslik_resmi_etiketi)
        
        # Arabaların Listeleneceği Izgara (Grid) Düzeni
        self.araba_paneli = QWidget()
        self.araba_paneli.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.ızgara = QGridLayout(self.araba_paneli)
        self.ızgara.setSpacing(15)
        
        self.araba_butonlari = []
        self._arabaları_yukle()
        ana_düzen.addWidget(self.araba_paneli)
        
        
        
       # Alt Buton Grubu (Hakkında, Yardım, Başla)
        alt_düzen = QHBoxLayout()
        
        self.btn_about = QPushButton("About")
        self.btn_about.setFont(QFont("Liberation Sans", 12))
        self.btn_about.clicked.connect(self._hakkinda_ac)
        alt_düzen.addWidget(self.btn_about)
        
        self.btn_help = QPushButton("Help")
        self.btn_help.setFont(QFont("Liberation Sans", 12))
        self.btn_help.clicked.connect(self._yardim_ac)
        alt_düzen.addWidget(self.btn_help)
        
        alt_düzen.addStretch()
        
        self.btn_start = QPushButton("Start Race")
        self.btn_start.setFont(QFont("Liberation Sans", 14, QFont.Weight.Bold))
        self.btn_start.setEnabled(False) # Araba seçilmeden basılamaz
        self.btn_start.clicked.connect(self._yarisi_baslat_tetik)
        alt_düzen.addWidget(self.btn_start)
        
        ana_düzen.addLayout(alt_düzen)

    def _arabaları_yukle(self):
        """cars klasöründeki png dosyalarını bulur ve ızgaraya dizer."""
        if not os.path.exists(self.cars_dizin):
            print(f"HATA: cars dizini bulunamadı -> {self.cars_dizin}")
            return
            
        arabalar = sorted([f for f in os.listdir(self.cars_dizin) if f.endswith(".png")])
        
        satir = 0
        sütun = 0
        # Maksimum 6 sütun genişliğinde dizilim yapalım (12 araba için 2 satır oluşturur)
        maks_sütun = 6 
        
        for araba_dosya in arabalar:
            yol = os.path.join(self.cars_dizin, araba_dosya)
            buton = ArabaButon(araba_dosya, yol)
            buton.clicked.connect(lambda checked, b=buton: self._araba_secildi(b))
            
            self.ızgara.addWidget(buton, satir, sütun)
            self.araba_butonlari.append(buton)
            
            sütun += 1
            if sütun >= maks_sütun:
                sütun = 0
                satir += 1

    def _araba_secildi(self, tıklanan_buton):
        """Seçilen arabayı işaretler, diğerlerinin seçimini kaldırır ve parlatma efektini yönetir."""
        for buton in self.araba_butonlari:
            if buton != tıklanan_buton:
                buton.setChecked(False)
                # Varsayılan fusion stiline geri çekmek için stylesheet'i temizle
                buton.setStyleSheet("") 
                
        if tıklanan_buton.isChecked():
            self.secilen_araba = tıklanan_buton.dosya_adi
            # Parlama / Seçim Efekti (Fusion stiline uygun belirgin sarı/altın kenarlık)
            tıklanan_buton.setStyleSheet("border: 3px solid #ffcc00; background-color: rgba(255, 204, 0, 30);")
            self.btn_start.setEnabled(True)
        else:
            self.secilen_araba = None
            tıklanan_buton.setStyleSheet("")
            self.btn_start.setEnabled(False)

    def _yardim_ac(self):
        dlg = YardimDialog(self)
        dlg.exec()

    def _hakkinda_ac(self):
        dlg = HakkindaDialog(self)
        dlg.exec()

    def _yarisi_baslat_tetik(self):
        """Müziği kapatır, car.py'yi arkada başlatır ve ön planda çerçevesiz splash ekranını açar."""
        # Başlangıç müziğini hemen sonlandırıyoruz
        pygame.mixer.stop()
        pygame.mixer.quit()
        
        # Ana menü penceresini hemen gizliyoruz
        self.hide()
        
        # 1. ADIM: Çerçevesiz splash ekranını bağımsız olarak hemen ekrana getiriyoruz
        yol_splash = os.path.join(self.disks_dizin, "splashscreen.png")
        self.aktif_splash = SplashEkran(yol_splash)
        self.aktif_splash.show()
        
        # Ekranın donmaması ve anında çizilmesi için Qt olay döngüsünü zorluyoruz
        QApplication.processEvents()
        
        # 2. ADIM: car.py'yi ASENKRON (arka planda) hemen başlatıyoruz (Pencereler kilitlenmez)
        oyun_yolu = os.path.join(self.dizin, "car.py")
        if os.path.exists(oyun_yolu):
            # subprocess.run yerine Popen kullanarak car.py'nin bitmesini beklemeden koda devam ediyoruz
            self.oyun_sureci = subprocess.Popen([sys.executable, oyun_yolu, self.secilen_araba])
        else:
            print(f"HATA: {oyun_yolu} bulunamadı!")
        
        # 3. ADIM: Tam 6 saniye (6000 ms) sonra splash ekranı kapatıp main.py'yi sonlandıracak zamanlayıcı
        QTimer.singleShot(6000, self._oyunu_baslat)

    def _oyunu_baslat(self):
        """6 saniye dolduğunda ön plandaki splash ekranı kapatır ve ana menüyü tamamen sonlandırır."""
        if hasattr(self, 'aktif_splash') and self.aktif_splash:
            self.aktif_splash.close()
            
        # Ana menü sürecini tamamen kapatıyoruz, arkada asenkron açılan car.py bağımsız yaşamaya devam eder
        self.close()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Tercih edilen Fusion stili sabitlendi
    pencere = AnaEkran()
    pencere.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
