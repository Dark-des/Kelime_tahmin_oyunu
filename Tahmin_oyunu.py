# -*- coding: utf-8 -*-
# Son Hali - Tema Seçimi, Tur Tabanlı ÇP, Kelime Limiti, Seri Bonusu
# (Skor Biriktirme, Güncel Ana Menü Butonları ve Yeni Raunt Sistemi ile)
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import random
import sys
import os

# --- Kütüphane Importları ---
try:
    from PIL import Image, ImageTk
    PIL_YUKLU = True
except ImportError:
    PIL_YUKLU = False
try:
    import pygame
    PYGAME_YUKLU = True
except ImportError:
    PYGAME_YUKLU = False
try:
    import google.generativeai as genai
    GOOGLE_AI_YUKLU = True
except ImportError:
    GOOGLE_AI_YUKLU = False

# ---------- API Anahtarı ----------
GEMINI_API_KEY = "API_KEY" # KENDİ ANAHTARINIZI GİRİN!

# ---------- Sabitler ----------
SKOR_DOSYASI = r"skorlar.txt" # Dosya yolu basitleştirildi, programın yanına kaydeder.
LOGO_ICON_PATH = r"kelime_tahmin.png" # Dosya yolu basitleştirildi.(kendi dosya yolunuzu girin )
KAZANMA_SESI_YOLU = r"game_sound/level-win-game-sound.mp3" # Dosya yolu basitleştirildi.(kendi dosya yolunuzu girin )
KAYBETME_SESI_YOLU = r"game_sound/fail-game-sound.mp3" # Dosya yolu basitleştirildi.(kendi dosya yolunuzu girin )
YANLIS_CEVAP_SESI_YOLU = r"game_sound/wrong-answer-game-sound.mp3" # Dosya yolu basitleştirildi.(kendi dosya yolunuzu girin )

MIN_KELIME_UZUNLUK = 3
MAX_KELIME_UZUNLUK = 15
TOPLAM_TUR_SAYISI = 3 # Çift oyunculu mod için toplam tur sayısı (en fazla 3 raunt, ilk 2'yi alan kazanır)
SERI_BONUS_ESIGI = 3
SERI_BONUS_MIKTARI = 2

# Renk Paletleri
DARK_THEME = {
    "bg": "#2E3440", "fg": "#ECEFF4", "accent": "#88C0D0", "success": "#A3BE8C",
    "error": "#BF616A", "warning": "#D08770", "info": "#5E81AC",
    "btn_fg": "#2E3440", "btn_fg_light": "#ECEFF4",
    "entry_bg": "#D8DEE9", "entry_fg": "#2E3440"
}
LIGHT_THEME = {
    "bg": "#ECEFF4", "fg": "#2E3440", "accent": "#5E81AC", "success": "#8FBCBB",
    "error": "#BF616A", "warning": "#D08770", "info": "#81A1C1",
    "btn_fg": "#ECEFF4", "btn_fg_light": "#2E3440",
    "entry_bg": "#E5E9F0", "entry_fg": "#2E3440"
}
aktif_tema = DARK_THEME

# ---------- Global Değişkenler ----------
ana_pencere = None; oyun_penceresi = None; oyun_bitti = False;
mevcut_zorluk = "Orta"; oyun_modu = "Tek Oyunculu"; kelime = ""; gizli_kelime = [];
oyuncular = {}; aktif_oyuncu = ""; ipucu_bedeli = 3;
oyuncu_isimleri_listesi = []; kullanilan_kelimeler_bu_oturumda = set()
logo_photoimage_ana = None; logo_photoimage_oyun = None
kazanma_ses_obj = None; kaybetme_ses_obj = None; yanlis_cevap_ses_obj = None
PYGAME_MIXER_INIT = False; API_KONFIGURE_EDILDI = False
aktif_gorev_aciklamasi = ""; mevcut_tur = 1; kim_kelime_giriyor = None; dogru_tahmin_serisi = 0

# Ana menü seçimleri için Tkinter StringVars ve etiket referansları
oyun_modu_var = None
zorluk_var = None
secili_mod_etiket = None
secili_zorluk_etiket = None

# Widget Referansları
can_para_label=None; kelime_label=None; tahmin_giris=None; gorev_label=None;
tahmin_button=None; ipucu_button=None; yeniden_baslat_button=None;
ana_menu_button_oyun=None; buton_frame=None; tema_button=None;

# ---------- API Yapılandırma ----------
if GOOGLE_AI_YUKLU and GEMINI_API_KEY and "API_KEY" not in GEMINI_API_KEY: # API Key kontrolü eklendi
    try:
        genai.configure(api_key=GEMINI_API_KEY); API_KONFIGURE_EDILDI = True; print("API Yapılandırıldı.")
    except Exception as e: print(f"API Yapılandırma Hatası: {e}")
else: print("API Yapılandırılamadı (Kütüphane eksik veya API Key girilmemiş/geçersiz).")

# ---------- Fonksiyon Tanımlamaları ----------
def kaynak_yolu(relative_path):
    """ Geçici dizin için kaynak yolu oluşturur (PyInstaller için). """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def dosya_kontrol(dosya_yolu):
    # PyInstaller ile paketlendiğinde doğru yolu bulmak için kaynak_yolu kullan
    gercek_yol = kaynak_yolu(dosya_yolu)
    if not gercek_yol or not isinstance(gercek_yol, str): return False
    exists = os.path.exists(gercek_yol)
    if not exists: print(f"Uyarı: Dosya bulunamadı -> '{gercek_yol}' (Orijinal: '{dosya_yolu}')")
    return exists


def rastgele_kelime():
    global kullanilan_kelimeler_bu_oturumda, API_KONFIGURE_EDILDI
    if not API_KONFIGURE_EDILDI: return "TEST"
    max_deneme = 5; son_alinan_kelime = None
    for deneme in range(max_deneme):
        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            prompt = "Bana tek kelimelik rastgele bir Türkçe isim veya fiil öner. Sadece kelimeyi ver..."
            generation_config = genai.types.GenerationConfig(temperature=0.95)
            response = model.generate_content(prompt, generation_config=generation_config)
            kelime_adayi = None; kelime_adayi_text = ""
            if hasattr(response, 'parts') and response.parts: kelime_adayi_text = "".join(part.text for part in response.parts).strip()
            elif hasattr(response, 'text') and response.text: kelime_adayi_text = response.text.strip()
            if kelime_adayi_text and ' ' not in kelime_adayi_text and len(kelime_adayi_text) > 2:
                kelime_adayi = kelime_adayi_text.upper(); son_alinan_kelime = kelime_adayi
            if kelime_adayi:
                if kelime_adayi not in kullanilan_kelimeler_bu_oturumda: kullanilan_kelimeler_bu_oturumda.add(kelime_adayi); return kelime_adayi
                else: print(f"'{kelime_adayi}' tekrar etti ({deneme + 1}/{max_deneme})"); continue
            else: print(f"Geçersiz yanıt ({kelime_adayi_text}) ({deneme + 1}/{max_deneme})"); continue
        except Exception as e: print(f"API hatası (deneme {deneme + 1}): {e}"); return "HATA"
    print(f"Uyarı: {max_deneme} denemede yeni kelime bulunamadı.")
    if son_alinan_kelime and son_alinan_kelime not in kullanilan_kelimeler_bu_oturumda:
        print(f"Son alınan '{son_alinan_kelime}' kullanılıyor."); kullanilan_kelimeler_bu_oturumda.add(son_alinan_kelime); return son_alinan_kelime
    else: print("Farklı kelime alınamadı. TEKRAR durumu."); return "TEKRAR"

def center_window(window, parent):
    window.update_idletasks()
    try:
        parent_geo = parent.geometry().split('+'); parent_w = parent.winfo_width(); parent_h = parent.winfo_height()
        parent_x = int(parent_geo[1]) if len(parent_geo) > 1 else parent.winfo_x()
        parent_y = int(parent_geo[2]) if len(parent_geo) > 2 else parent.winfo_y()
        win_w = window.winfo_width(); win_h = window.winfo_height()
        x = parent_x + (parent_w // 2) - (win_w // 2); y = parent_y + (parent_h // 2) - (win_h // 2)
        window.geometry(f'+{x}+{y}')
    except Exception as e: print(f"Pencere ortalanamadı: {e}")

def kelime_girisi_al(oyuncu_adi, parent_window):
    girilen_kelime_strvar = tk.StringVar()
    kelime_penceresi = tk.Toplevel(parent_window);
    kelime_penceresi.title("Kelime Girişi"); kelime_penceresi.config(bg=aktif_tema["bg"]); kelime_penceresi.resizable(False, False); kelime_penceresi.transient(parent_window); kelime_penceresi.grab_set()
    frame = tk.Frame(kelime_penceresi, bg=aktif_tema["bg"], padx=20, pady=20); frame.pack()
    tk.Label(frame, text=f"{oyuncu_adi}, tahmin edilecek kelimeyi gir:", bg=aktif_tema["bg"], fg=aktif_tema["fg"]).pack(pady=5)
    entry_kelime = ttk.Entry(frame, width=30, show="*", textvariable=girilen_kelime_strvar, style="TEntry"); entry_kelime.pack(pady=5); entry_kelime.focus()
    tk.Label(frame, text=f"({MIN_KELIME_UZUNLUK}-{MAX_KELIME_UZUNLUK} harf, boşluksuz, sadece harf)", bg=aktif_tema["bg"], fg=aktif_tema["info"], font=('Arial', 9)).pack(pady=(0,10))
    def kelimeyi_onayla():
        kelime_val = entry_kelime.get().strip()
        if not kelime_val or ' ' in kelime_val or not kelime_val.isalpha():
            messagebox.showwarning("Geçersiz Kelime", "Lütfen sadece harflerden oluşan ve boşluk içermeyen bir kelime girin.", parent=kelime_penceresi); return
        if not (MIN_KELIME_UZUNLUK <= len(kelime_val) <= MAX_KELIME_UZUNLUK):
            messagebox.showwarning("Geçersiz Uzunluk", f"Kelime uzunluğu {MIN_KELIME_UZUNLUK} ile {MAX_KELIME_UZUNLUK} harf arasında olmalıdır.", parent=kelime_penceresi); return
        kelime_penceresi.result = kelime_val.upper(); kelime_penceresi.destroy()
    ttk.Button(frame, text="✅ Onayla", command=kelimeyi_onayla, style="Success.TButton").pack(pady=10)
    entry_kelime.bind("<Return>", lambda event: kelimeyi_onayla()); kelime_penceresi.protocol("WM_DELETE_WINDOW", lambda: setattr(kelime_penceresi, 'result', None) or kelime_penceresi.destroy())
    center_window(kelime_penceresi, parent_window); parent_window.wait_window(kelime_penceresi)
    return getattr(kelime_penceresi, 'result', None)

def gorev_girisi_al(oyuncu1_adi, oyuncu2_adi, parent_window):
    girilen_gorev_strvar = tk.StringVar()
    gorev_penceresi = tk.Toplevel(parent_window); gorev_penceresi.title("Görev Belirle"); gorev_penceresi.config(bg=aktif_tema["bg"]); gorev_penceresi.resizable(False, False); gorev_penceresi.transient(parent_window); gorev_penceresi.grab_set()
    frame = tk.Frame(gorev_penceresi, bg=aktif_tema["bg"], padx=20, pady=20); frame.pack()
    tk.Label(frame, text=f"{oyuncu1_adi}, {oyuncu2_adi}'nin uyması gereken görevi/kuralı yaz:", bg=aktif_tema["bg"], fg=aktif_tema["fg"], wraplength=300).pack(pady=(5,10))
    entry_gorev = ttk.Entry(frame, width=40, textvariable=girilen_gorev_strvar, style="TEntry"); entry_gorev.pack(pady=5); entry_gorev.focus()
    tk.Label(frame, text="(Örn: 'Sadece 3 canın var')", bg=aktif_tema["bg"], fg=aktif_tema["info"], font=('Arial', 9)).pack(pady=(0,10))
    def gorevi_onayla():
        gorev_aciklamasi = entry_gorev.get().strip()
        if not gorev_aciklamasi: gorev_aciklamasi = "Standart Oyun"
        gorev_penceresi.result = gorev_aciklamasi; gorev_penceresi.destroy()
    ttk.Button(frame, text="✅ Görevi Belirle", command=gorevi_onayla, style="Success.TButton").pack(pady=10)
    entry_gorev.bind("<Return>", lambda event: gorevi_onayla()); gorev_penceresi.protocol("WM_DELETE_WINDOW", lambda: setattr(gorev_penceresi, 'result', "Standart Oyun") or gorev_penceresi.destroy())
    center_window(gorev_penceresi, parent_window); parent_window.wait_window(gorev_penceresi)
    return getattr(gorev_penceresi, 'result', "Standart Oyun")

def isim_girisi_baslat(mod_secimi_param, zorluk_secimi_param): # Parametre isimleri daha açıklayıcı
    global ana_pencere
    if not ana_pencere or not ana_pencere.winfo_exists(): return
    
    # Global oyun_modu ve mevcut_zorluk'u burada, oyun başlamadan hemen önce kesinleştir.
    global oyun_modu, mevcut_zorluk
    oyun_modu = mod_secimi_param
    mevcut_zorluk = zorluk_secimi_param

    isim_penceresi = tk.Toplevel(ana_pencere); isim_penceresi.title("Oyuncu İsimleri"); isim_penceresi.config(bg=aktif_tema["bg"]); isim_penceresi.resizable(False, False); isim_penceresi.transient(ana_pencere); isim_penceresi.grab_set()
    isim_frame = tk.Frame(isim_penceresi, bg=aktif_tema["bg"], padx=20, pady=20); isim_frame.pack()
    entries = {}; tk.Label(isim_frame, text=f"{'Oyuncu' if oyun_modu == 'Tek Oyunculu' else 'Oyuncu 1'} Adı:", bg=aktif_tema["bg"], fg=aktif_tema["fg"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    entry_isim1 = ttk.Entry(isim_frame, width=25, style="TEntry"); entry_isim1.grid(row=0, column=1, padx=5, pady=5); entry_isim1.focus(); entries['isim1'] = entry_isim1; entry_isim2 = None
    if oyun_modu == "Çift Oyunculu": tk.Label(isim_frame, text="Oyuncu 2 Adı:", bg=aktif_tema["bg"], fg=aktif_tema["fg"]).grid(row=1, column=0, padx=5, pady=5, sticky="w"); entry_isim2 = ttk.Entry(isim_frame, width=25, style="TEntry"); entry_isim2.grid(row=1, column=1, padx=5, pady=5); entries['isim2'] = entry_isim2
    baslat_btn = ttk.Button(isim_frame, text="▶️ Devam Et", style="Success.TButton", command=lambda: isimleri_kontrol_et_ve_baslat(entries, isim_penceresi)); baslat_btn.grid(row=2, column=0, columnspan=2, pady=15)
    if entry_isim2: entry_isim2.bind("<Return>", lambda event: isimleri_kontrol_et_ve_baslat(entries, isim_penceresi))
    else: entry_isim1.bind("<Return>", lambda event: isimleri_kontrol_et_ve_baslat(entries, isim_penceresi))
    center_window(isim_penceresi, ana_pencere)

def isimleri_kontrol_et_ve_baslat(entries, pencere):
    # oyun_modu ve mevcut_zorluk zaten isim_girisi_baslat'ta global olarak ayarlandı.
    global oyuncu_isimleri_listesi, ana_pencere, mevcut_tur, kim_kelime_giriyor, oyuncular, oyun_modu, mevcut_zorluk
    
    isim1 = entries['isim1'].get().strip(); isim2 = entries.get('isim2').get().strip() if entries.get('isim2') else None
    if not isim1 or (oyun_modu == "Çift Oyunculu" and not isim2): messagebox.showerror("Hata", "Lütfen tüm oyuncu isimlerini girin.", parent=pencere); return
    if oyun_modu == "Çift Oyunculu" and isim1.lower() == isim2.lower(): messagebox.showerror("Hata", "Oyuncu isimleri farklı olmalıdır.", parent=pencere); return
    
    oyuncu_isimleri_listesi = [isim1]
    if isim2: oyuncu_isimleri_listesi.append(isim2)

    manuel_kelime = None; girilen_gorev_aciklamasi = None
    if oyun_modu == "Çift Oyunculu":
        mevcut_tur = 1 
        kim_kelime_giriyor = oyuncu_isimleri_listesi[0]
        
        can_init, para_init, toplam_can_init = 0, 0, 0
        if mevcut_zorluk=="Kolay": can_init,para_init,toplam_can_init=7,15,7
        elif mevcut_zorluk=="Orta": can_init,para_init,toplam_can_init=5,10,5
        elif mevcut_zorluk=="Zor": can_init,para_init,toplam_can_init=3,5,3
        else: can_init,para_init,toplam_can_init=5,10,5

        oyuncular = {} 
        for isim_oyuncu in oyuncu_isimleri_listesi:
            oyuncular[isim_oyuncu] = {"can": can_init, "para": para_init, "skor": 0, "toplam_can": toplam_can_init, "raund_galibiyeti": 0}

        print(f"\n--- RAUND {mevcut_tur} / {TOPLAM_TUR_SAYISI} ---")
        print(f"{kim_kelime_giriyor} kelime ve görev girecek...")
        
        pencere.withdraw() 
        manuel_kelime = kelime_girisi_al(kim_kelime_giriyor, ana_pencere)
        if manuel_kelime is None: 
            pencere.deiconify(); messagebox.showinfo("İptal", "Kelime girişi iptal edildi.", parent=ana_pencere if ana_pencere and ana_pencere.winfo_exists() else None)
            ana_menuye_don(pencere_ref=pencere) # ana_menuye_don'e pencere referansını da ver
            return
        
        tahmin_edecek_oyuncu_adi = oyuncu_isimleri_listesi[1]
        girilen_gorev_aciklamasi = gorev_girisi_al(kim_kelime_giriyor, tahmin_edecek_oyuncu_adi, ana_pencere)
        if girilen_gorev_aciklamasi is None: girilen_gorev_aciklamasi = "Standart Oyun"
        
        if pencere.winfo_exists(): pencere.destroy() 
        baslat_oyun(oyun_modu, mevcut_zorluk, oyuncu_isimleri_listesi, manuel_kelime, girilen_gorev_aciklamasi)
    else: # Tek Oyunculu
        if pencere.winfo_exists(): pencere.destroy()
        baslat_oyun(oyun_modu, mevcut_zorluk, oyuncu_isimleri_listesi)

def ipucu_ver():
    global oyuncular, aktif_oyuncu, gizli_kelime, kelime_label, kelime, can_para_label, ipucu_bedeli
    if oyun_bitti or not aktif_oyuncu or aktif_oyuncu not in oyuncular: return
    if oyuncular[aktif_oyuncu]['para'] >= ipucu_bedeli:
        oyuncular[aktif_oyuncu]['para'] -= ipucu_bedeli
        if can_para_label: can_para_label.config(text=guncelle_can_para())
        acik_olmayan_indeksler = [i for i, harf in enumerate(gizli_kelime) if harf == "_"]
        if acik_olmayan_indeksler:
            rastgele_indeks = random.choice(acik_olmayan_indeksler)
            if kelime and rastgele_indeks < len(kelime):
                gizli_kelime[rastgele_indeks] = kelime[rastgele_indeks]
                if kelime_label: kelime_label.config(text=" ".join(gizli_kelime), fg=aktif_tema["fg"])
                if "_" not in gizli_kelime:
                    if kelime_label: kelime_label.config(text=f"Tebrikler {aktif_oyuncu}! İpucuyla buldun! Kelime: {kelime}", fg=aktif_tema["success"])
                    oyun_sonu() 
            else: oyuncular[aktif_oyuncu]['para'] += ipucu_bedeli;
        else:
            oyuncular[aktif_oyuncu]['para'] += ipucu_bedeli
            if kelime_label: kelime_label.config(text="Açılmamış harf kalmadı!", fg=aktif_tema["warning"])
            if ipucu_button and ipucu_button.winfo_exists(): ipucu_button.config(state=tk.DISABLED)
    else:
        if kelime_label: kelime_label.config(text=f"💡 İpucu için yeterli paranız yok ({aktif_oyuncu})!", fg=aktif_tema["error"])

def baslat_oyun(mod_param, zorluk_param_baslat, oyuncu_adlari_param, manuel_kelime=None, gorev_aciklamasi=None):
    global kelime, gizli_kelime, oyuncular, aktif_oyuncu, oyun_penceresi, oyun_modu, ana_pencere, oyun_bitti, mevcut_zorluk, oyuncu_isimleri_listesi, logo_photoimage_oyun, aktif_gorev_aciklamasi
    global dogru_tahmin_serisi, kim_kelime_giriyor

    if oyun_penceresi and oyun_penceresi.winfo_exists(): oyun_penceresi.destroy(); oyun_penceresi = None
    
    # oyun_modu ve mevcut_zorluk zaten isim_girisi_baslat -> isimleri_kontrol_et_ve_baslat içinde global olarak ayarlandı.
    # Bu fonksiyon çağrıldığında bu global değerler kullanılır. Parametreler sadece ilk çağrı için önemli.
    # Ancak tutarlılık için, fonksiyon içindeki global değişkenleri kullanalım.
    # mod_param ve zorluk_param_baslat'ı doğrudan global'lere atamak yerine,
    # global'lerin zaten doğru olduğunu varsayalım (isim_girisi_baslat ayarladığı için).
    # Ya da en iyisi, bu fonksiyon çağrıldığında her zaman global'leri güncelleyelim.
    oyun_modu = mod_param
    mevcut_zorluk = zorluk_param_baslat
    oyuncu_isimleri_listesi = oyuncu_adlari_param

    oyun_bitti = False
    aktif_gorev_aciklamasi = ""; dogru_tahmin_serisi = 0 

    if ana_pencere and ana_pencere.winfo_exists(): ana_pencere.withdraw()
    oyun_penceresi = tk.Tk(); oyun_penceresi.title(f"{oyun_modu} Kelime Oyunu - {mevcut_zorluk}"); oyun_penceresi.geometry("650x480"); oyun_penceresi.config(bg=aktif_tema["bg"]); oyun_penceresi.resizable(False, False); oyun_penceresi.protocol("WM_DELETE_WINDOW", ana_menuye_don)
    
    logo_path_gercek = kaynak_yolu(LOGO_ICON_PATH)
    if dosya_kontrol(LOGO_ICON_PATH): # dosya_kontrol zaten kaynak_yolu'nu kullanıyor
        try: 
            logo_photoimage_oyun = tk.PhotoImage(file=logo_path_gercek)
            oyun_penceresi.iconphoto(True, logo_photoimage_oyun)
        except Exception as e: print(f"Oyun ikonu hatası: {e}")

    if oyun_modu == "Çift Oyunculu" and manuel_kelime: kelime = manuel_kelime.strip().upper()
    else: kelime = rastgele_kelime()

    if kelime in ["HATA", "TEST", "TEKRAR", "KELİME"] or not kelime:
        msg = ""; fg_renk = aktif_tema["error"];
        if kelime == "HATA": msg = "Kelime alınamadı."
        elif kelime == "TEST": msg = "API Anahtarı eksik ('TEST')."; fg_renk = aktif_tema["warning"]
        elif kelime == "TEKRAR": msg = "Farklı kelime alınamadı.\nTekrar deneyin."
        elif kelime == "KELİME": msg = "Geçerli kelime alınamadı."; fg_renk = aktif_tema["warning"]
        elif not kelime: msg = "Kelime belirlenemedi!";
        frame_msg = tk.Frame(oyun_penceresi, bg=aktif_tema["bg"]); frame_msg.pack(expand=True); tk.Label(frame_msg, text=msg, bg=aktif_tema["bg"], fg=fg_renk, justify=tk.CENTER).pack(pady=20, padx=20); ttk.Button(frame_msg, text="🏠 Ana Menüye Dön", command=ana_menuye_don, style="Accent.TButton").pack(pady=10, padx=20, fill="x"); oyun_penceresi.mainloop(); return

    gizli_kelime = ["_" for _ in kelime]
    can_tur, para_tur, toplam_can_tur = 0,0,0
    if mevcut_zorluk=="Kolay": can_tur,para_tur,toplam_can_tur=7,15,7
    elif mevcut_zorluk=="Orta": can_tur,para_tur,toplam_can_tur=5,10,5
    elif mevcut_zorluk=="Zor": can_tur,para_tur,toplam_can_tur=3,5,3
    else: can_tur,para_tur,toplam_can_tur=5,10,5 

    if oyun_modu == "Tek Oyunculu":
        oyuncular = {} 
        if oyuncu_isimleri_listesi: 
            oyuncular[oyuncu_isimleri_listesi[0]] = {"can": can_tur, "para": para_tur, "skor": 0, "toplam_can": toplam_can_tur, "raund_galibiyeti":0}
    else: # Çift Oyunculu
        # oyuncular sözlüğü zaten isimleri_kontrol_et_ve_baslat'ta skor:0 ve raund_galibiyeti:0 ile başlatıldı.
        # Burada sadece mevcut raunt için can ve paralarını güncelliyoruz.
        for isim_oyuncu in oyuncu_isimleri_listesi:
            if isim_oyuncu in oyuncular:
                oyuncular[isim_oyuncu]['can'] = can_tur
                oyuncular[isim_oyuncu]['para'] = para_tur
                oyuncular[isim_oyuncu]['toplam_can'] = toplam_can_tur
            else: 
                print(f"UYARI: Oyuncu {isim_oyuncu} `oyuncular` sözlüğünde bulunamadı (baslat_oyun). Yeni kayıt oluşturuluyor.")
                oyuncular[isim_oyuncu] = {"can": can_tur, "para": para_tur, "skor": 0, "toplam_can": toplam_can_tur, "raund_galibiyeti":0}
    
    if oyun_modu == "Tek Oyunculu":
        aktif_oyuncu = oyuncu_isimleri_listesi[0] if oyuncu_isimleri_listesi else ""
    else: 
        if kim_kelime_giriyor == oyuncu_isimleri_listesi[0]:
            aktif_oyuncu = oyuncu_isimleri_listesi[1] 
        elif kim_kelime_giriyor == oyuncu_isimleri_listesi[1]:
             aktif_oyuncu = oyuncu_isimleri_listesi[0]
        else: 
            # kim_kelime_giriyor None ise (ilk turda isimleri_kontrol_et_ve_baslat ayarladıktan sonra buraya gelinir)
            # veya beklenmedik bir değerse, mantıklı bir varsayılan ata.
            # Bu durum normalde oluşmamalı.
            if kim_kelime_giriyor is None and len(oyuncu_isimleri_listesi) > 1:
                # Genelde ilk kelimeyi P1 girer, P2 tahmin eder.
                # kim_kelime_giriyor'un None olması buraya kadar gelinmemesi gereken bir durum.
                # isimleri_kontrol_et_ve_baslat'ta ayarlanıyor.
                print(f"UYARI: kim_kelime_giriyor None, aktif_oyuncu varsayılan olarak ayarlandı.")
                aktif_oyuncu = oyuncu_isimleri_listesi[1]
            else:
                aktif_oyuncu = oyuncu_isimleri_listesi[1] if len(oyuncu_isimleri_listesi) > 1 else (oyuncu_isimleri_listesi[0] if oyuncu_isimleri_listesi else "")
                print(f"UYARI: kim_kelime_giriyor ('{kim_kelime_giriyor}') beklenmedik. Aktif oyuncu: {aktif_oyuncu}")


    if oyun_modu == "Çift Oyunculu":
        aktif_gorev_aciklamasi = gorev_aciklamasi if gorev_aciklamasi else "Standart Oyun"
        print(f"[DEBUG] Raund {mevcut_tur} Başlıyor.")
        print(f"[DEBUG] Aktif Oyuncu (Tahminci): {aktif_oyuncu}")
        print(f"[DEBUG] Kelime Giren: {kim_kelime_giriyor}")
        print(f"[DEBUG] Aktif Görev: {aktif_gorev_aciklamasi}")
    else:
        aktif_gorev_aciklamasi = ""

    setup_game_ui_widgets(); oyun_penceresi.mainloop()

def setup_game_ui_widgets():
    global can_para_label, kelime_label, gorev_label, tahmin_giris, tahmin_button, ipucu_button, yeniden_baslat_button, ana_menu_button_oyun, buton_frame, kelime, ipucu_bedeli, oyun_modu, mevcut_zorluk, oyuncu_isimleri_listesi, aktif_gorev_aciklamasi

    oyun_penceresi.columnconfigure(0, weight=1); oyun_penceresi.rowconfigure(2, weight=1); oyun_penceresi.rowconfigure(4, weight=1)
    can_para_label = tk.Label(oyun_penceresi, text=guncelle_can_para(), bg=aktif_tema["bg"], fg=aktif_tema["info"], font=('Arial', 11)); can_para_label.grid(row=0, column=0, padx=15, pady=(10, 0), sticky="ew")
    gorev_label = tk.Label(oyun_penceresi, text="", bg=aktif_tema["bg"], fg=aktif_tema["warning"], font=('Arial', 10, 'italic'), wraplength=600); gorev_label.grid(row=1, column=0, padx=15, pady=(0,5), sticky="ew")
    if oyun_modu == "Çift Oyunculu" and aktif_gorev_aciklamasi and aktif_gorev_aciklamasi != "Standart Oyun": gorev_label.config(text=f"❗ Görev: {aktif_gorev_aciklamasi}")
    else: gorev_label.config(text="") 
    kelime_label = tk.Label(oyun_penceresi, text=" ".join(gizli_kelime), bg=aktif_tema["bg"], fg=aktif_tema["fg"], font=("Arial", 20, "bold")); kelime_label.grid(row=2, column=0, padx=20, pady=5, sticky="nsew")
    tahmin_giris = ttk.Entry(oyun_penceresi, justify=tk.CENTER, font=("Arial", 14), style="TEntry"); tahmin_giris.grid(row=3, column=0, padx=50, pady=10, sticky="ew"); tahmin_giris.bind("<Return>", tahmin_et); tahmin_giris.focus()
    buton_frame = tk.Frame(oyun_penceresi, bg=aktif_tema["bg"]); buton_frame.grid(row=4, column=0, pady=(10, 15), sticky="ew"); buton_frame.columnconfigure((0, 1, 2, 3), weight=1) # column 3 eklendi
    tahmin_button = ttk.Button(buton_frame, text="✅ Tahmin Et", command=tahmin_et, style="Accent.TButton", width=16); tahmin_button.grid(row=0, column=0, padx=5, pady=5, sticky="e")
    ipucu_button = ttk.Button(buton_frame, text=f"💡 İpucu Al ({ipucu_bedeli}₺)", command=ipucu_ver, style="Warning.TButton", width=16); ipucu_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    if kelime == "TEST": ipucu_button.config(state=tk.DISABLED)
    
    yeniden_baslat_button_text = "🔄 Raundu Yeniden Başlat" if oyun_modu == "Çift Oyunculu" else "🔄 Oyunu Yeniden Başlat"
    yeniden_baslat_button = ttk.Button(buton_frame, text=yeniden_baslat_button_text, command=lambda: baslat_oyun(oyun_modu, mevcut_zorluk, oyuncu_isimleri_listesi, kelime if oyun_modu == "Çift Oyunculu" else None, aktif_gorev_aciklamasi if oyun_modu == "Çift Oyunculu" else None), style="Success.TButton", width=20); 
    yeniden_baslat_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
    ana_menu_button_oyun = ttk.Button(buton_frame, text="🏠 Ana Menü", command=ana_menuye_don, style="Error.TButton", width=16) 
    # Ana menü butonu oyun sonunda gösterilecek, başlangıçta grid'e eklenmiyor.


def guncelle_can_para():
    global oyuncu_isimleri_listesi, oyuncular, aktif_oyuncu, oyun_modu
    if not oyuncular : return "Oyuncu verisi yok."
    
    if oyun_modu == "Tek Oyunculu":
        if not oyuncu_isimleri_listesi: return "Oyuncu listesi boş!"
        oyuncu_adi_tek = oyuncu_isimleri_listesi[0]
        if oyuncu_adi_tek not in oyuncular: 
            return f"{oyuncu_adi_tek} için veri yok!"
        oyuncu_datasi = oyuncular[oyuncu_adi_tek]
        can = oyuncu_datasi['can']; para = oyuncu_datasi['para']; skor = oyuncu_datasi['skor']
        return f"{oyuncu_adi_tek} | Can: {can} | Para: {para}₺ | Skor: {skor}"
    
    elif oyun_modu == "Çift Oyunculu":
        if len(oyuncu_isimleri_listesi) < 2: return "Çift oyuncu listesi eksik!"
        isim1, isim2 = oyuncu_isimleri_listesi[0], oyuncu_isimleri_listesi[1]
        
        if isim1 not in oyuncular or isim2 not in oyuncular: return "Bazı oyuncu verileri eksik!"
            
        p1=oyuncular[isim1]; p2=oyuncular[isim2]
        
        o1_info = f"{isim1} (Can:{p1['can']}, Para:{p1['para']}₺, Skor:{p1['skor']}, Rnd:{p1.get('raund_galibiyeti',0)})"
        o2_info = f"{isim2} (Can:{p2['can']}, Para:{p2['para']}₺, Skor:{p2['skor']}, Rnd:{p2.get('raund_galibiyeti',0)})"
        
        if aktif_oyuncu == isim1: o1_info = f"▶ {o1_info}"
        elif aktif_oyuncu == isim2: o2_info = f"▶ {o2_info}"
            
        return f" {o1_info}  |  {o2_info} "
    return "Mod bilgisi hatalı."

def tahmin_et(event=None):
    global aktif_oyuncu, oyun_bitti, gizli_kelime, kelime_label, can_para_label, oyuncu_isimleri_listesi, yanlis_cevap_ses_obj, PYGAME_MIXER_INIT
    global dogru_tahmin_serisi, oyuncular

    if oyun_bitti or not tahmin_giris : return
    tahmin_eden_oyuncu = aktif_oyuncu 
    if not tahmin_eden_oyuncu or tahmin_eden_oyuncu not in oyuncular:
        print(f"HATA: Geçersiz tahmin eden oyuncu: {tahmin_eden_oyuncu}")
        if kelime_label: kelime_label.config(text="Oyuncu hatası!", fg=aktif_tema["error"])
        return

    tahmin = tahmin_giris.get().strip().upper(); tahmin_giris.delete(0, tk.END);
    if not tahmin or not kelime: return

    dogru_tahmin_yapildi_bu_adimda = False # Sadece bu tahmin adımı için
    yanlis_tahmin = False; bonus_mesaj = ""

    if len(tahmin) == len(kelime): 
        if tahmin == kelime:
            gizli_kelime = list(kelime);
            if kelime_label and kelime_label.winfo_exists(): kelime_label.config(text=f"🏆 Tebrikler {tahmin_eden_oyuncu}! Kazandın! Kelime: {kelime}", fg=aktif_tema["success"])
            
            tur_skoru = oyuncular[tahmin_eden_oyuncu]['can'] * 5 + oyuncular[tahmin_eden_oyuncu]['para'] + 5 
            oyuncular[tahmin_eden_oyuncu]['skor'] += tur_skoru
            
            dogru_tahmin_yapildi_bu_adimda = True; dogru_tahmin_serisi = 0; oyun_sonu(); return 
        else:
            oyuncular[tahmin_eden_oyuncu]['can'] -= 1; yanlis_tahmin = True; dogru_tahmin_serisi = 0 
            if kelime_label and kelime_label.winfo_exists(): kelime_label.config(text="❌ Yanlış Kelime!", fg=aktif_tema["error"])
    elif len(tahmin) == 1: 
        if tahmin in kelime:
            if tahmin in gizli_kelime:
                if kelime_label and kelime_label.winfo_exists(): kelime_label.config(text=f"⚠️ '{tahmin}' harfi zaten açık!", fg=aktif_tema["warning"]);
                # Bu durumda can_para_label güncellemesi gereksiz olabilir çünkü bir değişiklik yok.
                return # Yanlış veya doğru değil, sadece bilgi.
            else:
                bulunan_sayisi = sum(1 for i, c in enumerate(kelime) if c == tahmin and gizli_kelime[i] == "_")
                for i, c in enumerate(kelime):
                    if c == tahmin: gizli_kelime[i] = tahmin
                oyuncular[tahmin_eden_oyuncu]['para'] += bulunan_sayisi
                if kelime_label and kelime_label.winfo_exists(): kelime_label.config(text=" ".join(gizli_kelime), fg=aktif_tema["fg"])
                dogru_tahmin_yapildi_bu_adimda = True 
                dogru_tahmin_serisi += 1 
                if dogru_tahmin_serisi >= SERI_BONUS_ESIGI and dogru_tahmin_serisi % SERI_BONUS_ESIGI == 0:
                    oyuncular[tahmin_eden_oyuncu]['para'] += SERI_BONUS_MIKTARI
                    bonus_mesaj = f" +{SERI_BONUS_MIKTARI}₺ Seri Bonusu!"
                    print(f"[BONUS] {tahmin_eden_oyuncu} {dogru_tahmin_serisi} seri yakaladı!")
                if kelime_label and kelime_label.winfo_exists() and bonus_mesaj:
                    orijinal_text = " ".join(gizli_kelime) 
                    kelime_label.config(text=f"{orijinal_text} {bonus_mesaj}", fg=aktif_tema["success"])
                    kelime_label.after(1500, lambda: kelime_label.config(text=orijinal_text, fg=aktif_tema["fg"]) if kelime_label.winfo_exists() and kelime_label.cget("text").endswith(bonus_mesaj) else None)
        else: 
            oyuncular[tahmin_eden_oyuncu]['can'] -= 1; yanlis_tahmin = True; dogru_tahmin_serisi = 0 
            if kelime_label and kelime_label.winfo_exists(): kelime_label.config(text=f"❌ '{tahmin}' harfi yok!", fg=aktif_tema["error"])
    else: 
        if kelime_label and kelime_label.winfo_exists(): kelime_label.config(text="⚠️ Hatalı giriş!", fg=aktif_tema["error"])
        yanlis_tahmin = True; dogru_tahmin_serisi = 0 
        # Hatalı girişte can düşürmüyoruz, sadece uyarı veriyoruz. Para/can durumu değişmediği için return yeterli.
        return

    if yanlis_tahmin and PYGAME_MIXER_INIT and yanlis_cevap_ses_obj:
        try: yanlis_cevap_ses_obj.play()
        except pygame.error as e: print(f"Yanlış cevap sesi hatası: {e}")

    if can_para_label and can_para_label.winfo_exists(): can_para_label.config(text=guncelle_can_para())

    if "_" not in gizli_kelime and not oyun_bitti: 
        if kelime_label and kelime_label.winfo_exists() and not kelime_label.cget("text").startswith("🏆"): 
             kelime_label.config(text=f"🏆 Tebrikler {tahmin_eden_oyuncu}! Kazandın! Kelime: {kelime}", fg=aktif_tema["success"])
        
        # Eğer kelime tamamlanarak değil de son harf açılarak bittiyse ve skor zaten kelime tahminiyle hesaplanmadıysa
        if len(tahmin) == 1 and dogru_tahmin_yapildi_bu_adimda: 
            tur_skoru = oyuncular[tahmin_eden_oyuncu]['can'] * 5 + oyuncular[tahmin_eden_oyuncu]['para']
            oyuncular[tahmin_eden_oyuncu]['skor'] += tur_skoru
            if can_para_label and can_para_label.winfo_exists(): can_para_label.config(text=guncelle_can_para())
        oyun_sonu(); return

    if tahmin_eden_oyuncu in oyuncular and oyuncular[tahmin_eden_oyuncu]['can'] <= 0 and not oyun_bitti: 
        if kelime_label and kelime_label.winfo_exists(): kelime_label.config(text=f"💔 {tahmin_eden_oyuncu} kaybettin! Kelime: {kelime}", fg=aktif_tema["error"])
        oyun_sonu(); return

    if tahmin_giris and tahmin_giris.winfo_exists(): tahmin_giris.focus()

def skor_kaydet(oyuncu_adi, skor):
    global mevcut_zorluk, oyun_modu
    if not oyuncu_adi: print("Hata: Geçersiz oyuncu adı."); return
    try: skor_int = int(skor)
    except (ValueError, TypeError): print(f"Hata: Geçersiz skor: {skor}"); return
    
    skor_dosyasi_yolu = kaynak_yolu(SKOR_DOSYASI)
    try:
        with open(skor_dosyasi_yolu, "a", encoding='utf-8') as f:
            f.write(f"{oyuncu_adi},{skor_int},{mevcut_zorluk},{oyun_modu}\n")
    except IOError as e: print(f"HATA: Skor dosyasına yazılamadı! '{skor_dosyasi_yolu}'. Hata: {e}")
    except Exception as e: print(f"Skor kaydetmede hata: {e}")

def skor_goster():
    global ana_pencere
    if not ana_pencere or not ana_pencere.winfo_exists(): return
    
    skor_dosyasi_yolu = kaynak_yolu(SKOR_DOSYASI)
    try:
        with open(skor_dosyasi_yolu, "r", encoding='utf-8') as f: satirlar = f.readlines()
    except FileNotFoundError:
        skor_penceresi_yok = tk.Toplevel(ana_pencere); skor_penceresi_yok.title("Liderlik Tablosu"); skor_penceresi_yok.config(bg=aktif_tema["bg"]); skor_penceresi_yok.geometry("300x100"); skor_penceresi_yok.transient(ana_pencere); skor_penceresi_yok.grab_set(); tk.Label(skor_penceresi_yok, text="Henüz skor kaydedilmedi.", bg=aktif_tema["bg"], fg=aktif_tema["warning"]).pack(pady=20, padx=10); center_window(skor_penceresi_yok, ana_pencere); return
    except Exception as e: print(f"Skor okumada hata: {e}"); return
    
    skorlar = [];
    for satir in satirlar:
        if not satir.strip(): continue; bilgiler = satir.strip().split(',')
        if len(bilgiler) == 4:
            oyuncu, skor_str, zorluk_skor, mod_skor = bilgiler; 
            try: skorlar.append({"oyuncu": oyuncu, "skor": int(skor_str), "zorluk": zorluk_skor, "mod": mod_skor})
            except ValueError: print(f"Skor dosyasında geçersiz satır (sayısal olmayan skor): {satir.strip()}"); continue
        else: print(f"Skor dosyasında geçersiz satır (eksik bilgi): {satir.strip()}"); continue
    
    skorlar.sort(key=lambda x: x['skor'], reverse=True)
    skor_penceresi = tk.Toplevel(ana_pencere); skor_penceresi.title("Liderlik Tablosu"); skor_penceresi.config(bg=aktif_tema["bg"]); skor_penceresi.geometry("450x400"); skor_penceresi.transient(ana_pencere); skor_penceresi.grab_set()
    tk.Label(skor_penceresi, text="🏆 Liderlik Tablosu 🏆", bg=aktif_tema["bg"], fg=aktif_tema["accent"], font=("Arial", 16, "bold")).pack(pady=15)
    main_frame = tk.Frame(skor_penceresi, bg=aktif_tema["bg"]); main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    my_canvas = tk.Canvas(main_frame, bg=aktif_tema["bg"], highlightthickness=0); my_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    my_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=my_canvas.yview); my_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    my_canvas.configure(yscrollcommand=my_scrollbar.set); my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))
    second_frame = tk.Frame(my_canvas, bg=aktif_tema["bg"]); my_canvas.create_window((0,0), window=second_frame, anchor="nw")
    
    # Stil zaten arayuzu_yenile'de uygulanıyor, Treeview için özel olanlar burada da kalabilir veya oraya taşınabilir.
    style = ttk.Style() 
    style.configure("Treeview.Heading", font=('Arial', 10,'bold'), background=aktif_tema["accent"], foreground=aktif_tema["btn_fg"])
    style.configure("Treeview", font=('Arial', 9), fieldbackground=aktif_tema["bg"], background=aktif_tema["bg"], foreground=aktif_tema["fg"])
    style.map('Treeview', background=[('selected', aktif_tema["accent"])], foreground=[('selected', aktif_tema["btn_fg"])])

    tree = ttk.Treeview(second_frame, columns=("Sıra", "Oyuncu", "Skor", "Zorluk", "Mod"), show="headings", style="Treeview")
    tree.heading("Sıra", text="Sıra"); tree.heading("Oyuncu", text="Oyuncu"); tree.heading("Skor", text="Skor")
    tree.heading("Zorluk", text="Zorluk"); tree.heading("Mod", text="Mod")
    tree.column("Sıra", width=40, anchor=tk.CENTER); tree.column("Oyuncu", width=120); tree.column("Skor", width=70, anchor=tk.CENTER)
    tree.column("Zorluk", width=80, anchor=tk.CENTER); tree.column("Mod", width=100, anchor=tk.CENTER)

    for i, skor_data in enumerate(skorlar[:20]): 
        tree.insert("", "end", values=(i+1, skor_data['oyuncu'], skor_data['skor'], skor_data['zorluk'], skor_data['mod']))
    tree.pack(expand=True, fill=tk.BOTH)
    center_window(skor_penceresi, ana_pencere)

def oyun_sonu_arayuz_guncelle(mesaj_text, mesaj_fg, ses_obj=None):
    global oyun_bitti, tahmin_button, ipucu_button, tahmin_giris, kelime_label, ana_menu_button_oyun, buton_frame
    oyun_bitti = True 
    if kelime_label and kelime_label.winfo_exists(): kelime_label.config(text=mesaj_text, fg=mesaj_fg)
    if tahmin_button and tahmin_button.winfo_exists(): tahmin_button.config(state=tk.DISABLED)
    if ipucu_button and ipucu_button.winfo_exists(): ipucu_button.config(state=tk.DISABLED)
    if tahmin_giris and tahmin_giris.winfo_exists(): tahmin_giris.config(state=tk.DISABLED)
    
    if ana_menu_button_oyun and buton_frame : 
        try: 
            if not ana_menu_button_oyun.winfo_ismapped():
                 ana_menu_button_oyun.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        except tk.TclError: 
             ana_menu_button_oyun.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    if PYGAME_MIXER_INIT and ses_obj:
        try: ses_obj.play()
        except pygame.error as e: print(f"Oyun sonu sesi hatası: {e}")

def sonraki_tur_baslat(kim_girecek_sonraki_tur, tahmin_edecek_sonraki_tur):
    global ana_pencere, oyun_penceresi, mevcut_tur
    parent_for_msg = oyun_penceresi if oyun_penceresi and oyun_penceresi.winfo_exists() else \
                     (ana_pencere if ana_pencere and ana_pencere.winfo_exists() else None)

    messagebox.showinfo("Raund Değişikliği", 
                        f"--- RAUND {mevcut_tur} / {TOPLAM_TUR_SAYISI} ---\n\n"
                        f"Şimdi sıra {kim_girecek_sonraki_tur}'de kelime ve görev girmek için.\n"
                        f"{tahmin_edecek_sonraki_tur} tahmin edecek.",
                        parent=parent_for_msg)
    
    if oyun_penceresi and oyun_penceresi.winfo_exists():
        oyun_penceresi.destroy(); oyun_penceresi = None
    
    if ana_pencere and not ana_pencere.winfo_exists(): ana_ekran_olustur()
    elif ana_pencere: ana_pencere.deiconify()

    isimleri_kontrol_et_ve_baslat_sonraki_tur(kim_girecek_sonraki_tur, tahmin_edecek_sonraki_tur)

def isimleri_kontrol_et_ve_baslat_sonraki_tur(kim_kelime_giriyor_simdi_param, tahmin_edecek_oyuncu_simdi_param):
    global oyun_modu, mevcut_zorluk, oyuncu_isimleri_listesi, ana_pencere, kim_kelime_giriyor
    
    if not ana_pencere or not ana_pencere.winfo_exists():
        print("HATA: Sonraki tur için ana pencere bulunamadı!")
        ana_ekran_olustur()
        if not ana_pencere or not ana_pencere.winfo_exists(): return

    kim_kelime_giriyor = kim_kelime_giriyor_simdi_param # Global değişkeni sonraki tur için ayarla

    print(f"\n--- RAUND {mevcut_tur} / {TOPLAM_TUR_SAYISI} (Sonraki Raund Başlangıcı) ---")
    print(f"{kim_kelime_giriyor} kelime ve görev girecek...")

    manuel_kelime = kelime_girisi_al(kim_kelime_giriyor, ana_pencere)
    if manuel_kelime is None:
        messagebox.showinfo("İptal", "Kelime girişi iptal edildi. Oyun ana menüye dönüyor.", parent=ana_pencere)
        ana_menuye_don()
        return

    girilen_gorev_aciklamasi = gorev_girisi_al(kim_kelime_giriyor, tahmin_edecek_oyuncu_simdi_param, ana_pencere)
    if girilen_gorev_aciklamasi is None: girilen_gorev_aciklamasi = "Standart Oyun"

    baslat_oyun(oyun_modu, mevcut_zorluk, oyuncu_isimleri_listesi, manuel_kelime, girilen_gorev_aciklamasi)

def oyun_sonu():
    global oyun_bitti, aktif_oyuncu, kelime, oyuncular, kazanma_ses_obj, kaybetme_ses_obj, oyun_modu, oyuncu_isimleri_listesi, mevcut_tur, kim_kelime_giriyor, TOPLAM_TUR_SAYISI

    # Eğer zaten oyun_bitti True ise ve bu tek oyunculu mod için değilse (çünkü ÇP'de raund sonları da buraya gelir), çık.
    if oyun_bitti and oyun_modu == "Tek Oyunculu": 
        return
    # Çift oyunculu modda, oyun_bitti genel oyunun bitip bitmediğini gösterir. Raund sonlarında burası tekrar çağrılabilir.
    # Eğer genel oyun zaten bitti olarak işaretlendiyse (genel_kazanan_isim bulunduysa), tekrar işlem yapma.
    if oyun_bitti and oyun_modu == "Çift Oyunculu": # Bu kontrol, genel kazanan belirlendikten sonra tekrar girilmesini engeller.
        return


    if not aktif_oyuncu or aktif_oyuncu not in oyuncular: # aktif_oyuncu'nun varlığını ve geçerliliğini kontrol et
        print(f"HATA: Oyun sonunda aktif oyuncu ('{aktif_oyuncu}') geçersiz veya oyuncularda bulunamadı.")
        if oyun_penceresi and oyun_penceresi.winfo_exists(): # Hata mesajını oyun penceresine yazdır
            oyun_sonu_arayuz_guncelle("Kritik oyuncu hatası!", aktif_tema["error"])
        return

    kazandi_mi_raundu = "_" not in gizli_kelime # Mevcut raundu aktif oyuncu (tahminci) kazandı mı?
    can_bitti_mi = oyuncular[aktif_oyuncu]['can'] <= 0

    if oyun_modu == "Tek Oyunculu":
        oyun_bitti = True 
        if kazandi_mi_raundu:
            mesaj = f"🏆 Tebrikler {aktif_oyuncu}! Kazandın! Kelime: {kelime}"
            renk = aktif_tema["success"]; ses = kazanma_ses_obj
            skor_kaydet(aktif_oyuncu, oyuncular[aktif_oyuncu]['skor'])
        elif can_bitti_mi:
            mesaj = f"💔 {aktif_oyuncu} kaybettin! Kelime: {kelime}"
            renk = aktif_tema["error"]; ses = kaybetme_ses_obj
            skor_kaydet(aktif_oyuncu, oyuncular[aktif_oyuncu]['skor']) 
        else: 
            mesaj = f"Oyun bitti. Kelime: {kelime}"; renk = aktif_tema["info"]; ses = None
        oyun_sonu_arayuz_guncelle(mesaj, renk, ses)

    elif oyun_modu == "Çift Oyunculu":
        mevcut_raund_no = mevcut_tur 
        
        if kazandi_mi_raundu: 
            oyuncular[aktif_oyuncu]['raund_galibiyeti'] += 1
            print(f"Raund {mevcut_raund_no} Sonucu: {aktif_oyuncu} kelimeyi ('{kelime}') buldu ve raundu kazandı.")
        elif can_bitti_mi: 
            kelimeyi_giren_oyuncu = oyuncu_isimleri_listesi[0] if aktif_oyuncu == oyuncu_isimleri_listesi[1] else oyuncu_isimleri_listesi[1]
            if kelimeyi_giren_oyuncu in oyuncular: # Ekstra kontrol
                oyuncular[kelimeyi_giren_oyuncu]['raund_galibiyeti'] += 1
                print(f"Raund {mevcut_raund_no} Sonucu: {aktif_oyuncu} kelimeyi ('{kelime}') bulamadı. Raundu {kelimeyi_giren_oyuncu} kazandı.")
        
        p1_isim = oyuncu_isimleri_listesi[0]
        p2_isim = oyuncu_isimleri_listesi[1]
        p1_raund_wins = oyuncular[p1_isim]['raund_galibiyeti']
        p2_raund_wins = oyuncular[p2_isim]['raund_galibiyeti']
        print(f"Güncel Raund Durumu: {p1_isim}: {p1_raund_wins} - {p2_isim}: {p2_raund_wins}")
        if can_para_label and can_para_label.winfo_exists(): can_para_label.config(text=guncelle_can_para())

        genel_kazanan_isim = None
        if p1_raund_wins == 2: genel_kazanan_isim = p1_isim
        elif p2_raund_wins == 2: genel_kazanan_isim = p2_isim

        if genel_kazanan_isim:
            oyun_bitti = True 
            kazanan_mesaji = f"🏆 OYUN BİTTİ! {genel_kazanan_isim} kazandı! (Raundlar: {p1_raund_wins}-{p2_raund_wins})"
            ses = kazanma_ses_obj
            skor_kaydet(genel_kazanan_isim, oyuncular[genel_kazanan_isim]['skor'])
            oyun_sonu_arayuz_guncelle(kazanan_mesaji, aktif_tema["success"], ses)
            if ana_menu_button_oyun and buton_frame and ana_menu_button_oyun.winfo_exists(): # Kontrol eklendi
                 if not ana_menu_button_oyun.winfo_ismapped():
                      ana_menu_button_oyun.grid(row=0, column=3, padx=5, pady=5, sticky="w")
            return 

        if mevcut_raund_no < TOPLAM_TUR_SAYISI:
            oyun_bitti = False 
            mevcut_tur += 1 
            
            idx_kim_girecek = (mevcut_tur - 1) % len(oyuncu_isimleri_listesi)
            kim_girecek_sonraki_tur = oyuncu_isimleri_listesi[idx_kim_girecek]
            
            idx_kim_tahmin_edecek = (idx_kim_girecek + 1) % len(oyuncu_isimleri_listesi)
            tahmin_edecek_sonraki_tur = oyuncu_isimleri_listesi[idx_kim_tahmin_edecek]
            
            sonraki_tur_baslat(kim_girecek_sonraki_tur, tahmin_edecek_sonraki_tur)
        else: 
            oyun_bitti = True 
            # Bu noktada 3 raund oynanmış olmalı ve kazanan zaten yukarıda belirlenmiş olmalı.
            # Eğer buraya gelinirse, bir mantık hatası olabilir veya 3. raund sonunda kazanan belirlenmemiştir.
            # (Örn: 1-1'den sonra 3. raund oynandı, kazananın genel_kazanan_isim'e atanması gerekirdi)
            # Bu bir failsafe olarak düşünülebilir.
            if p1_raund_wins > p2_raund_wins: genel_kazanan_isim = p1_isim
            elif p2_raund_wins > p1_raund_wins: genel_kazanan_isim = p2_isim
            
            if genel_kazanan_isim:
                 kazanan_mesaji = f"🏆 OYUN BİTTİ! {genel_kazanan_isim} kazandı! (Raundlar: {p1_raund_wins}-{p2_raund_wins})"
                 ses = kazanma_ses_obj
                 skor_kaydet(genel_kazanan_isim, oyuncular[genel_kazanan_isim]['skor'])
            else: # 3 raund sonunda hala kazanan yoksa (bu imkansız olmalı: 1.5-1.5 gibi)
                 kazanan_mesaji = f"Oyun bitti! Sonuç: {p1_isim} {p1_raund_wins} - {p2_isim} {p2_raund_wins}. Beraberlik durumu!"
                 ses = None # Beraberlik için farklı bir ses olabilir
                 # Beraberlikte iki oyuncunun da skoru kaydedilebilir.
                 skor_kaydet(p1_isim, p1_raund_wins) # Raund sayısını değil, toplam puanı kaydetmek daha mantıklı olabilir.
                 skor_kaydet(p2_isim, p2_raund_wins) # Veya sadece bir mesaj gösterilir.
            oyun_sonu_arayuz_guncelle(kazanan_mesaji, aktif_tema["success"] if genel_kazanan_isim else aktif_tema["info"], ses)
            if ana_menu_button_oyun and buton_frame and ana_menu_button_oyun.winfo_exists():
                 if not ana_menu_button_oyun.winfo_ismapped():
                      ana_menu_button_oyun.grid(row=0, column=3, padx=5, pady=5, sticky="w")

def oyun_penceresi_kapat():
    global oyun_penceresi
    if oyun_penceresi and oyun_penceresi.winfo_exists():
        oyun_penceresi.destroy()
        oyun_penceresi = None

def ana_menuye_don(pencere_ref=None): 
    global oyuncular, mevcut_tur, kim_kelime_giriyor, kullanilan_kelimeler_bu_oturumda, oyun_penceresi, ana_pencere, oyun_bitti
    oyun_bitti = True 
    oyun_penceresi_kapat() 
    
    if pencere_ref and pencere_ref.winfo_exists(): 
        try: pencere_ref.destroy()
        except tk.TclError: pass 

    oyuncular = {}
    mevcut_tur = 1
    kim_kelime_giriyor = None
    kullanilan_kelimeler_bu_oturumda.clear()

    if ana_pencere and ana_pencere.winfo_exists():
        ana_pencere.deiconify() 
    else: 
        ana_ekran_olustur()

def arayuzu_yenile():
    global ana_pencere, oyun_penceresi, aktif_tema, secili_mod_etiket, secili_zorluk_etiket, oyun_modu_var, zorluk_var
    
    style = ttk.Style()
    style.theme_use('clam') 
    
    style.configure("TButton", foreground=aktif_tema["btn_fg_light"], background=aktif_tema["accent"], font=('Arial', 10, 'bold'), padding=5)
    style.map("TButton",
              background=[('active', aktif_tema["info"])],
              foreground=[('active', aktif_tema["btn_fg_light"])])
    style.configure("Success.TButton", foreground=aktif_tema["btn_fg_light"], background=aktif_tema["success"])
    style.map("Success.TButton", background=[('active', aktif_tema["info"])])
    style.configure("Error.TButton", foreground=aktif_tema["btn_fg_light"], background=aktif_tema["error"])
    style.map("Error.TButton", background=[('active', aktif_tema["warning"])])
    style.configure("Warning.TButton", foreground=aktif_tema["btn_fg"], background=aktif_tema["warning"])
    style.map("Warning.TButton", background=[('active', aktif_tema["info"])])
    style.configure("Accent.TButton", foreground=aktif_tema["btn_fg_light"], background=aktif_tema["accent"])
    style.map("Accent.TButton", background=[('active', aktif_tema["info"])])

    style.configure("TLabel", foreground=aktif_tema["fg"], background=aktif_tema["bg"], font=('Arial', 10))
    style.configure("Bold.TLabel", foreground=aktif_tema["fg"], background=aktif_tema["bg"], font=('Arial', 10, "bold"))
    style.configure("TFrame", background=aktif_tema["bg"])
    style.configure("TEntry", fieldbackground=aktif_tema["entry_bg"], foreground=aktif_tema["entry_fg"], insertcolor=aktif_tema["entry_fg"])
    
    style.configure("Treeview.Heading", font=('Arial', 10,'bold'), background=aktif_tema["accent"], foreground=aktif_tema["btn_fg"])
    style.configure("Treeview", font=('Arial', 9), fieldbackground=aktif_tema["bg"], background=aktif_tema["bg"], foreground=aktif_tema["fg"])
    style.map('Treeview', background=[('selected', aktif_tema["accent"])], foreground=[('selected', aktif_tema["btn_fg"])])
    style.configure("Vertical.TScrollbar", background=aktif_tema["accent"], troughcolor=aktif_tema["bg"], bordercolor=aktif_tema["accent"], arrowcolor=aktif_tema["btn_fg"])

    if ana_pencere and ana_pencere.winfo_exists():
        ana_pencere.config(bg=aktif_tema["bg"])
        for widget in ana_pencere.winfo_children():
            widget_type = widget.winfo_class()
            try:
                if isinstance(widget, (tk.Frame, ttk.Frame)):
                    widget.config(bg=aktif_tema["bg"])
                    for child_widget in widget.winfo_children():
                        try: 
                            if isinstance(child_widget, (tk.Frame, ttk.Frame)):
                                child_widget.config(bg=aktif_tema["bg"])
                                for sub_child in child_widget.winfo_children():
                                     if isinstance(sub_child, tk.Label) and not isinstance(sub_child, ttk.Label): sub_child.config(bg=aktif_tema["bg"], fg=aktif_tema["fg"])
                            elif isinstance(child_widget, tk.Label) and not isinstance(child_widget, ttk.Label): child_widget.config(bg=aktif_tema["bg"], fg=aktif_tema["fg"])
                            elif isinstance(child_widget, tk.Button) and not isinstance(child_widget, ttk.Button): child_widget.config(bg=aktif_tema["accent"], fg=aktif_tema["btn_fg_light"])
                        except tk.TclError: pass
                elif isinstance(widget, tk.Label) and not isinstance(widget, ttk.Label): widget.config(bg=aktif_tema["bg"], fg=aktif_tema["fg"])
                elif isinstance(widget, tk.Button) and not isinstance(widget, ttk.Button): widget.config(bg=aktif_tema["accent"], fg=aktif_tema["btn_fg_light"])
            except tk.TclError: pass 
        
        if secili_mod_etiket and oyun_modu_var: secili_mod_etiket.config(text=f"Seçili: {oyun_modu_var.get()}")
        if secili_zorluk_etiket and zorluk_var: secili_zorluk_etiket.config(text=f"Seçili: {zorluk_var.get()}")

    if oyun_penceresi and oyun_penceresi.winfo_exists():
        oyun_penceresi.config(bg=aktif_tema["bg"])
        if can_para_label: can_para_label.config(bg=aktif_tema["bg"], fg=aktif_tema["info"])
        if gorev_label: gorev_label.config(bg=aktif_tema["bg"], fg=aktif_tema["warning"])
        if kelime_label: 
            current_text = kelime_label.cget("text")
            if "Kazandın" in current_text or "Tebrikler" in current_text : kelime_label.config(bg=aktif_tema["bg"], fg=aktif_tema["success"])
            elif "kaybettin" in current_text or "Yanlış" in current_text or "Hatalı" in current_text: kelime_label.config(bg=aktif_tema["bg"], fg=aktif_tema["error"])
            elif "zaten açık" in current_text: kelime_label.config(bg=aktif_tema["bg"], fg=aktif_tema["warning"])
            else: kelime_label.config(bg=aktif_tema["bg"], fg=aktif_tema["fg"])
        if buton_frame: buton_frame.config(bg=aktif_tema["bg"])

def tema_degistir():
    global aktif_tema
    if aktif_tema == DARK_THEME: aktif_tema = LIGHT_THEME
    else: aktif_tema = DARK_THEME
    arayuzu_yenile()

def ana_ekran_olustur():
    global ana_pencere, logo_photoimage_ana, PYGAME_MIXER_INIT, kazanma_ses_obj, kaybetme_ses_obj, yanlis_cevap_ses_obj, tema_button
    global oyun_modu, mevcut_zorluk # Bu global değişkenler butonlarla güncellenecek
    global oyun_modu_var, zorluk_var, secili_mod_etiket, secili_zorluk_etiket

    if ana_pencere and ana_pencere.winfo_exists(): ana_pencere.destroy()
    
    ana_pencere = tk.Tk()
    ana_pencere.title("Kelime Tahmin Oyunu"); ana_pencere.geometry("500x600"); ana_pencere.resizable(False, False)
    ana_pencere.protocol("WM_DELETE_WINDOW", lambda: (ana_pencere.quit(), ana_pencere.destroy(), sys.exit()))

    if PYGAME_YUKLU and not PYGAME_MIXER_INIT:
        try:
            pygame.mixer.init(); PYGAME_MIXER_INIT = True
            if dosya_kontrol(KAZANMA_SESI_YOLU): kazanma_ses_obj = pygame.mixer.Sound(kaynak_yolu(KAZANMA_SESI_YOLU))
            if dosya_kontrol(KAYBETME_SESI_YOLU): kaybetme_ses_obj = pygame.mixer.Sound(kaynak_yolu(KAYBETME_SESI_YOLU))
            if dosya_kontrol(YANLIS_CEVAP_SESI_YOLU): yanlis_cevap_ses_obj = pygame.mixer.Sound(kaynak_yolu(YANLIS_CEVAP_SESI_YOLU))
        except pygame.error as e: print(f"Pygame mixer/ses hatası: {e}"); PYGAME_MIXER_INIT = False

    logo_path_gercek = kaynak_yolu(LOGO_ICON_PATH)
    logo_frame = ttk.Frame(ana_pencere, style="TFrame"); logo_frame.pack(pady=15)
    if PIL_YUKLU and dosya_kontrol(LOGO_ICON_PATH): # dosya_kontrol zaten kaynak_yolu'nu kullanıyor
        try:
            logo_image = Image.open(logo_path_gercek).resize((100, 100), Image.Resampling.LANCZOS)
            logo_photoimage_ana = ImageTk.PhotoImage(logo_image)
            tk.Label(logo_frame, image=logo_photoimage_ana, bg=aktif_tema["bg"]).pack()
            ana_pencere.iconphoto(True, logo_photoimage_ana)
        except Exception as e: print(f"Logo yüklenemedi: {e}"); ttk.Label(logo_frame, text="Kelime Oyunu", font=("Arial", 24, "bold"), style="TLabel").pack()
    else: ttk.Label(logo_frame, text="Kelime Oyunu", font=("Arial", 24, "bold"), style="TLabel").pack()

    oyun_modu_var = tk.StringVar(value=oyun_modu) 
    zorluk_var = tk.StringVar(value=mevcut_zorluk)

    def set_oyun_modu_ve_guncelle(yeni_mod):
        global oyun_modu # Global olan Python string değişkenini güncelle
        oyun_modu_var.set(yeni_mod) # Tkinter StringVar'ını güncelle (etiket için)
        oyun_modu = yeni_mod 
        # print(f"Global oyun_modu: {oyun_modu}") # Test için

    def set_zorluk_ve_guncelle(yeni_zorluk):
        global mevcut_zorluk # Global olan Python string değişkenini güncelle
        zorluk_var.set(yeni_zorluk) # Tkinter StringVar'ını güncelle (etiket için)
        mevcut_zorluk = yeni_zorluk
        # print(f"Global mevcut_zorluk: {mevcut_zorluk}") # Test için

    mod_cerceve = ttk.Frame(ana_pencere, style="TFrame", padding=(10,5)); mod_cerceve.pack(pady=5, fill="x", padx=20)
    ttk.Label(mod_cerceve, text="Oyun Modu:", font=('Arial', 12, "bold"), style="TLabel").pack(side=tk.TOP, anchor="w", pady=(0,5))
    mod_buton_cerceve = ttk.Frame(mod_cerceve, style="TFrame"); mod_buton_cerceve.pack(fill="x")
    ttk.Button(mod_buton_cerceve, text="👤 Tek Oyunculu", command=lambda: set_oyun_modu_ve_guncelle("Tek Oyunculu"), style="TButton").pack(side=tk.LEFT, padx=5, expand=True, fill="x")
    ttk.Button(mod_buton_cerceve, text="👥 Çift Oyunculu", command=lambda: set_oyun_modu_ve_guncelle("Çift Oyunculu"), style="TButton").pack(side=tk.LEFT, padx=5, expand=True, fill="x")
    secili_mod_etiket = ttk.Label(mod_cerceve, text=f"Seçili: {oyun_modu_var.get()}", style="Bold.TLabel")
    secili_mod_etiket.pack(side=tk.TOP, anchor="w", pady=(5,0))
    oyun_modu_var.trace_add("write", lambda *args: secili_mod_etiket.config(text=f"Seçili: {oyun_modu_var.get()}"))

    zorluk_cerceve = ttk.Frame(ana_pencere, style="TFrame", padding=(10,5)); zorluk_cerceve.pack(pady=5, fill="x", padx=20)
    ttk.Label(zorluk_cerceve, text="Zorluk Seviyesi:", font=('Arial', 12, "bold"), style="TLabel").pack(side=tk.TOP, anchor="w", pady=(0,5))
    zorluk_buton_cerceve = ttk.Frame(zorluk_cerceve, style="TFrame"); zorluk_buton_cerceve.pack(fill="x")
    ttk.Button(zorluk_buton_cerceve, text="Kolay", command=lambda: set_zorluk_ve_guncelle("Kolay"), style="TButton").pack(side=tk.LEFT, padx=2, expand=True, fill="x")
    ttk.Button(zorluk_buton_cerceve, text="Orta", command=lambda: set_zorluk_ve_guncelle("Orta"), style="TButton").pack(side=tk.LEFT, padx=2, expand=True, fill="x")
    ttk.Button(zorluk_buton_cerceve, text="Zor", command=lambda: set_zorluk_ve_guncelle("Zor"), style="TButton").pack(side=tk.LEFT, padx=2, expand=True, fill="x")
    secili_zorluk_etiket = ttk.Label(zorluk_cerceve, text=f"Seçili: {zorluk_var.get()}", style="Bold.TLabel")
    secili_zorluk_etiket.pack(side=tk.TOP, anchor="w", pady=(5,0))
    zorluk_var.trace_add("write", lambda *args: secili_zorluk_etiket.config(text=f"Seçili: {zorluk_var.get()}"))
    
    buton_ana_frame = ttk.Frame(ana_pencere, style="TFrame"); buton_ana_frame.pack(pady=20, fill="x", padx=50)
    baslat_button = ttk.Button(buton_ana_frame, text="▶️ Oyunu Başlat", 
                               command=lambda: isim_girisi_baslat(oyun_modu_var.get(), zorluk_var.get()), 
                               style="Success.TButton")
    baslat_button.pack(fill="x", pady=5)
    skor_button = ttk.Button(buton_ana_frame, text="🏆 Liderlik Tablosu", command=skor_goster, style="Accent.TButton")
    skor_button.pack(fill="x", pady=5)
    tema_button = ttk.Button(buton_ana_frame, text="🎨 Tema Değiştir", command=tema_degistir, style="Warning.TButton")
    tema_button.pack(fill="x", pady=5)
    cikis_button = ttk.Button(buton_ana_frame, text="🚪 Çıkış", command=lambda: (ana_pencere.quit(), ana_pencere.destroy(), sys.exit()), style="Error.TButton")
    cikis_button.pack(fill="x", pady=5)
    
    arayuzu_yenile() 
    center_window(ana_pencere, ana_pencere) 
    ana_pencere.mainloop()

if __name__ == "__main__":
    # Skor dosyası yoksa oluştur (kaynak_yolu ile doğru yerde)
    skor_dosyasi_yolu_ana = kaynak_yolu(SKOR_DOSYASI)
    if not os.path.exists(skor_dosyasi_yolu_ana): # os.path.exists doğrudan kullanılabilir
        try:
            with open(skor_dosyasi_yolu_ana, "a", encoding='utf-8') as f:
                pass # Sadece dosyayı oluştur
            print(f"Skor dosyası oluşturuldu: {skor_dosyasi_yolu_ana}")
        except Exception as e:
            print(f"Skor dosyası oluşturulamadı: {e}")
            
    ana_ekran_olustur()
    
    
    
# ------------------------------------------
# © 2025 Hüdayi Emre Sarıça
# Tüm hakları saklıdır.
# Bu kodun izinsiz kopyalanması, paylaşılması veya çoğaltılması yasaktır.
# ------------------------------------------
