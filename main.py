import os
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
import pytesseract
import pyperclip
import webbrowser
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\sssqaq\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Константы стиля
COLOR_BLACK = "#000000"
COLOR_PINK = "#FF1493"  # Deep Pink
COLOR_YELLOW = "#FFD700" # Gold / Yellow
MODERN_FONT = "Segoe UI"

class Database:
    def __init__(self, db_name="hivine_ocr.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT, width INTEGER, height INTEGER,
                    size_mb REAL, format TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка БД: {e}")

    def log_image(self, filename, width, height, size_bytes, img_format):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            size_mb = round(size_bytes / (1024 * 1024), 2)
            cursor.execute('INSERT INTO stats (filename, width, height, size_mb, format) VALUES (?, ?, ?, ?, ?)',
                           (filename, width, height, size_mb, img_format))
            conn.commit()
            conn.close()
        except Exception:
            pass

class HivineOCR(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Hivine OCR")
        self.geometry("800x700")
        self.configure(fg_color=COLOR_BLACK)
        
        self.db = Database()
        self.setup_main_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def open_github(self):
        webbrowser.open("https://github.com/Haryce/Hivine-OCR")

    def setup_main_screen(self):
        self.clear_screen()

        # Кнопка GitHub
        github_btn = ctk.CTkButton(
            self, text="GitHub ↗", width=80, height=30,
            fg_color="transparent", border_width=1, border_color=COLOR_PINK,
            text_color=COLOR_PINK, font=(MODERN_FONT, 12),
            command=self.open_github
        )
        github_btn.pack(anchor="ne", padx=20, pady=20)

        # Центрирующий контейнер
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(expand=True)

        # Название
        self.label_title = ctk.CTkLabel(
            main_frame, text="Hivine OCR", 
            font=(MODERN_FONT, 52, "bold"),
            text_color=COLOR_PINK
        )
        self.label_title.pack(pady=(0, 5))

        self.label_subtitle = ctk.CTkLabel(
            main_frame, text="Приложения для распознавание текста)", 
            font=(MODERN_FONT, 18),
            text_color=COLOR_YELLOW
        )
        self.label_subtitle.pack(pady=(0, 50))

        # Кнопка Начать 
        self.start_btn = ctk.CTkButton(
            main_frame, text="НАЧАТЬ", 
            command=self.upload_images,
            width=260, height=60,
            corner_radius=30,
            font=(MODERN_FONT, 20, "bold"),
            fg_color=COLOR_PINK,
            hover_color=COLOR_YELLOW,
            text_color="white"
        )
        self.start_btn.pack()

    def upload_images(self):
        files = filedialog.askopenfilenames(
            title="Выберите фото (макс. 4)",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png")]
        )
        
        if not files: return
        if len(files) > 4:
            messagebox.showwarning("Лимит", "Максимум 4 фотографии!")
            return

        full_text = ""
        for file_path in files:
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 35 * 1024 * 1024: continue

                img = Image.open(file_path)
                w, h = img.size
                if not (400 <= w <= 4000 and 400 <= h <= 4000): continue

                text = pytesseract.image_to_string(img, lang='rus+eng')
                full_text += f"--- {os.path.basename(file_path)} ---\n{text}\n\n"
                
                self.db.log_image(os.path.basename(file_path), w, h, file_size, img.format)
            except Exception as e:
                print(f"Ошибка обработки: {e}")

        self.show_result(full_text)

    def show_result(self, text):
        self.clear_screen()

        # Текстовое поле
        self.result_box = ctk.CTkTextbox(
            self, width=700, height=400, 
            fg_color="#121212", 
            border_color=COLOR_PINK, 
            border_width=1,
            font=(MODERN_FONT, 14)
        )
        self.result_box.pack(pady=30)
        self.result_box.insert("1.0", text)

        # Панель кнопок
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        copy_btn = ctk.CTkButton(
            btn_frame, text="Скопировать", 
            fg_color="transparent", border_width=2, border_color=COLOR_PINK,
            text_color="white", hover_color=COLOR_PINK,
            command=lambda: self.copy_text(text)
        )
        copy_btn.grid(row=0, column=0, padx=10)

        save_btn = ctk.CTkButton(
            btn_frame, text="Сохранить .txt", 
            fg_color="transparent", border_width=2, border_color=COLOR_YELLOW,
            text_color="white", hover_color=COLOR_YELLOW,
            command=lambda: self.save_to_file(text)
        )
        save_btn.grid(row=0, column=1, padx=10)

        # Кнопка Загрузить еще
        more_btn = ctk.CTkButton(
            self, text="ЗАГРУЗИТЬ ЕЩЁ", 
            fg_color=COLOR_PINK, hover_color=COLOR_YELLOW,
            text_color="white", font=(MODERN_FONT, 16, "bold"),
            width=200, height=45, corner_radius=20,
            command=self.upload_images
        )
        more_btn.pack(pady=20)

        back_btn = ctk.CTkButton(
            self, text="В начало", fg_color="transparent", 
            text_color="gray", command=self.setup_main_screen
        )
        back_btn.pack()

    def copy_text(self, text):
        pyperclip.copy(text)
        messagebox.showinfo("OK", "Текст скопирован")

    def save_to_file(self, text):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            messagebox.showinfo("OK", "Сохранено")

if __name__ == "__main__":
    app = HivineOCR()
    app.mainloop()
