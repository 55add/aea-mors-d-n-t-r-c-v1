import tkinter as tk
from tkinter import filedialog, messagebox
import wave
import numpy as np
import os
import threading
from PIL import Image, ImageTk

# --- KÜRESEL DEĞİŞKEN (Sonucu burada tutacağız) ---
hafizadaki_sonuc = ""

# --- MORS ALFABESİ SÖZLÜĞÜ ---
MORSE_CODE_DICT = {
    '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
    '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
    '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
    '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
    '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
    '--..': 'Z',
    '.----': '1', '..---': '2', '...--': '3', '....-': '4', '.....': '5',
    '-....': '6', '--...': '7', '---..': '8', '----.': '9', '-----': '0',
    '--..--': ', ', '.-.-.-': '.', '..--..': '?', '-..-.': '/', '-....-': '-',
    '-.--.': '(', '-.--.-': ')'
}


def mors_cevir(morse_code):
    words = []
    for morse_word in morse_code.split('   '):
        chars = []
        for char in morse_word.split(' '):
            if char in MORSE_CODE_DICT:
                chars.append(MORSE_CODE_DICT[char])
        words.append("".join(chars))
    return " ".join(words)


# --- ARKA PLAN İŞLEMİ ---
def islem_yap(filename):
    global hafizadaki_sonuc

    try:
        # Arayüze bilgi ver
        root.after(0, lambda: durum_guncelle("Dosya okunuyor, lütfen bekleyin...", "orange"))

        wav_file = wave.open(filename, 'r')
        nframes = wav_file.getnframes()
        nchannels = wav_file.getnchannels()
        frames = wav_file.readframes(nframes)
        signal = np.frombuffer(frames, dtype=np.int16)

        if nchannels > 1:
            signal = signal.reshape(-1, nchannels)
            signal = signal.mean(axis=1)

        signal = np.abs(signal)
        threshold = np.max(signal) * 0.4
        binary_signal = (signal > threshold).astype(int)

        root.after(0, lambda: durum_guncelle("Sinyal analiz ediliyor...", "blue"))

        changes = np.where(np.diff(binary_signal) != 0)[0]

        if len(changes) > 0:
            durations = np.diff(changes)
            avg_len = np.mean(durations)

            morse_code = ""
            for i, d in enumerate(durations):
                is_signal = binary_signal[changes[i] + 1] == 1
                if is_signal:
                    if d > avg_len * 1.5:
                        morse_code += "-"
                    elif d > avg_len * 0.2:
                        morse_code += "."
                else:
                    if d > avg_len * 2.5:
                        morse_code += "   "
                    elif d > avg_len * 0.8:
                        morse_code += " "

            morse_code = morse_code.strip()
            decoded_text = mors_cevir(morse_code)

            # Sonuçları değişkene kaydet (Ekrana basmıyoruz)
            hafizadaki_sonuc = "--- MORS KODU ---\n" + morse_code + "\n\n"
            hafizadaki_sonuc += "--- ÇÖZÜLEN MESAJ ---\n" + decoded_text + "\n"

            # İşlem bitti
            root.after(0, lambda: islem_basarili())

        else:
            root.after(0, lambda: durum_guncelle("HATA: Sinyal bulunamadı.", "red"))
            root.after(0, lambda: analyze_button.config(state=tk.NORMAL, text=">>> TEKRAR DENE <<<", bg="black"))

    except Exception as e:
        root.after(0, lambda: durum_guncelle(f"Hata: {e}", "red"))
        root.after(0, lambda: analyze_button.config(state=tk.NORMAL))


def islem_basarili():
    durum_guncelle("✔ İŞLEM TAMAMLANDI! Sonucu kopyalayabilirsiniz.", "green")
    analyze_button.config(state=tk.NORMAL, text=">>> YENİ DOSYA SEÇ <<<", bg="black")
    copy_button.config(state=tk.NORMAL, bg="#008000", text="📄 SONUÇLARI KOPYALA")  # Kopyala butonunu aç


def panoya_kopyala():
    if hafizadaki_sonuc:
        root.clipboard_clear()
        root.clipboard_append(hafizadaki_sonuc)
        root.update()  # Panoyu güncelle
        messagebox.showinfo("Başarılı", "Tüm sonuçlar kopyalandı!\nİstediğiniz yere yapıştırabilirsiniz (CTRL+V).")
    else:
        messagebox.showwarning("Boş", "Kopyalanacak sonuç yok.")


def durum_guncelle(mesaj, renk):
    status_label.config(text=mesaj, fg=renk)


def baslat_thread():
    filename = path_entry.get().strip()
    global hafizadaki_sonuc
    hafizadaki_sonuc = ""  # Önceki sonucu temizle

    # Butonları ayarla
    copy_button.config(state=tk.DISABLED, bg="gray", text="Sonuç Bekleniyor...")

    if not filename:
        durum_guncelle("Lütfen bir dosya seçin.", "red")
        return

    if not os.path.exists(filename):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        if os.path.exists(desktop_path):
            filename = desktop_path
        else:
            durum_guncelle("Dosya bulunamadı!", "red")
            return

    if os.path.isdir(filename):
        durum_guncelle("Klasör seçtiniz, dosya seçin.", "red")
        return

    analyze_button.config(state=tk.DISABLED, text="İŞLENİYOR...", bg="gray")

    t = threading.Thread(target=islem_yap, args=(filename,))
    t.daemon = True
    t.start()


def dosya_sec():
    baslangic_klasoru = r"C:\Users\admin\Desktop\aea"
    if not os.path.exists(baslangic_klasoru):
        baslangic_klasoru = os.path.expanduser("~")

    filename = filedialog.askopenfilename(
        initialdir=baslangic_klasoru,
        title="Bir WAV Dosyası Seç",
        filetypes=(("WAV files", "*.wav"), ("all files", "*.*"))
    )
    if filename:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, filename)
        durum_guncelle("Dosya seçildi. Çözümlemeye hazır.", "black")


# --- ARAYÜZ ---
root = tk.Tk()
root.title("AEA - Mors Çözücü (Performans Modu)")
root.geometry("750x550")
root.configure(bg="white")

root.columnconfigure(1, weight=1)
root.rowconfigure(2, weight=1)

# SOL PANEL (RESİM)
left_panel = tk.Frame(root, bg="black", width=250)
left_panel.grid(row=0, column=0, rowspan=3, sticky="nswe")
left_panel.grid_propagate(False)

try:
    tam_resim_yolu = r"C:\Users\admin\Desktop\aea\sol_gorsel.png"
    orijinal_resim = Image.open(tam_resim_yolu)
    yeniden_boyutlanmis = orijinal_resim.resize((250, 550))
    photo = ImageTk.PhotoImage(yeniden_boyutlanmis)
    image_label = tk.Label(left_panel, image=photo, bg="black")
    image_label.image = photo
    image_label.place(relx=0.5, rely=0.5, anchor="center")
except Exception as e:
    tk.Label(left_panel, text=f"Resim Yok:\n{e}", fg="red", bg="black", wraplength=240).place(relx=0.5, rely=0.5,
                                                                                              anchor="center")

# SAĞ PANEL
right_panel = tk.Frame(root, bg="white")
right_panel.grid(row=0, column=1, sticky="nwe", padx=20, pady=20)

tk.Label(right_panel, text="AEA", font=("Arial", 32, "bold"), bg="white").pack(anchor="w", pady=(0, 20))
tk.Label(right_panel, text="Ses dosyasının yolunu yazınız:", font=("Arial", 12), bg="white").pack(anchor="w")

input_frame = tk.Frame(right_panel, bg="white")
input_frame.pack(fill="x", pady=10)

path_entry = tk.Entry(input_frame, font=("Arial", 11))
path_entry.pack(side=tk.LEFT, fill="x", expand=True)

tk.Button(input_frame, text="Gözat...", command=dosya_sec, bg="#e1e1e1").pack(side=tk.RIGHT, padx=(5, 0))

# ANALİZ BUTONU
analyze_button = tk.Button(right_panel, text=">>> ÇÖZÜMLE VE ÇEVİR <<<", command=baslat_thread,
                           font=("Arial", 12, "bold"), bg="black", fg="white")
analyze_button.pack(fill="x", pady=20)

# --- SONUÇ YERİNE DURUM PANELİ ---
status_frame = tk.Frame(root, bg="#f0f0f0", bd=2, relief="groove")
status_frame.grid(row=2, column=1, sticky="nsew", padx=20, pady=(0, 20))

# Durum Mesajı (Ortada kocaman yazar)
status_label = tk.Label(status_frame, text="Dosya seçip 'Çözümle' butonuna basın.", font=("Arial", 14), bg="#f0f0f0",
                        fg="gray", wraplength=400)
status_label.pack(expand=True, fill="both", pady=20)

# KOPYALA BUTONU (En altta)
copy_button = tk.Button(status_frame, text="Sonuç Bekleniyor...", command=panoya_kopyala, font=("Arial", 14, "bold"),
                        bg="gray", fg="white", state=tk.DISABLED, height=2)
copy_button.pack(fill="x", side="bottom")

root.mainloop()