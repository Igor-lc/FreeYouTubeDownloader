import tkinter as tk
import yt_dlp
import threading
import os
import logging
import re

class YouTubeDownloaderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('🎬🛠️🚀 Free YouTube Downloader  |  Crafted by Igor Balitskyi  |  https://www.linkedin.com/in/ibalitskyi/  |  +380681325212')
        self.root.geometry("1400x325")
        self.desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        self.download_folder = os.path.join(self.desktop_path, "YouTube_Downloads")
        os.makedirs(self.download_folder, exist_ok=True)
        logging.basicConfig(filename=os.path.join(self.download_folder, "log.txt"), level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.url_pattern = re.compile(r'^https?://(?:www\.)?(?:youtube\.com|youtu\.be)/')
        self.entry = tk.Entry(self.root, width=150, justify='center', font=('Arial', 12), state='readonly')
        self.entry.pack(pady=5)
        self.progress_label = tk.Label(self.root, width=150, text='Очікування URL...', font=('Arial', 12))
        self.progress_label.pack(pady=5)
        self.log_text = tk.Text(self.root, width=225, height=7, font=('Arial', 8))
        self.log_text.pack(pady=5)
        self.log_text.config(state=tk.DISABLED)
        self.stop_event = threading.Event()
        self.paste_button = tk.Button(self.root, width=150, text='📋 Вставити YouTube URL', font=('Arial', 12), command=self.paste_from_clipboard)
        self.paste_button.pack(pady=5)
        self.download_button = tk.Button(self.root, width=150, text='⬇️ Завантажити відео в папку на Робочому столі: YouTube_Downloads', font=('Arial', 12), command=self.download_video, state=tk.DISABLED)
        self.download_button.pack(pady=5)
        self.stop_button = tk.Button(self.root, width=150, text='🛑 Зупинити завантаження', font=('Arial', 12), command=self.stop_download, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

    class MyLogger:
        def __init__(self, app):
            self.app = app
        def log(self, level, icon, msg):
            if msg.strip():
                getattr(logging, level)(msg)
                self.app.root.after(0, self.app.update_log, f'{icon} {msg}')
        def debug(self, msg):
            self.log('debug', '🐛', msg)
        def info(self, msg):
            self.log('info', 'ℹ️', msg)
        def warning(self, msg):
            self.log('warning', '⚠️', msg)
        def error(self, msg):
            self.log('error', '❌', msg)

    def validate_url(self, url):
        return bool(self.url_pattern.match(url))

    def paste_from_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get()
            self.entry.config(state='normal')
            self.entry.delete(0, tk.END)
            self.entry.insert(0, clipboard_text)
            self.entry.config(state='readonly')
            if self.validate_url(clipboard_text):
                self.download_button.config(state=tk.NORMAL)
                self.progress_label.config(text='URL вставлено. Готово до завантаження!')
                logging.info(f'URL вставлено: {clipboard_text}')
            else:
                self.download_button.config(state=tk.DISABLED)
                self.progress_label.config(text='❌ Невірний URL.')
                logging.warning(f'Невірний URL: {clipboard_text}')
        except tk.TclError:
            self.progress_label.config(text='Помилка вставки буфера обміну.')
            logging.error('Помилка вставки буфера обміну.')

    def update_log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def progress_hook(self, d):
        if self.stop_event.is_set():
            raise Exception("Завантаження перервано користувачем.")
        status = d.get('status')
        if status == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            self.root.after(0, lambda: self.progress_label.config(
                text=f'⬇️ Завантаження: {percent}'))
            logging.debug(f'⬇️ Завантаження: {percent}')
        elif status == 'finished':
            self.root.after(0, self.download_success)
            logging.info('✅ Завантаження завершено.')

    def run_download(self, url):
        try:
            with yt_dlp.YoutubeDL({
                'format': 'best',
                'outtmpl': os.path.join(self.download_folder, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'logger': self.MyLogger(self),
                'noplaylist': True,
            }) as ydl:
                ydl.download([url])
        except Exception as e:
            if self.stop_event.is_set():
                self.root.after(0, lambda: self.download_error("Завантаження зупинено користувачем."))
                logging.info('Завантаження зупинено користувачем.')
            else:
                self.root.after(0, lambda: self.download_error(str(e)))
                logging.error(str(e))

    def download_video(self):
        url = self.entry.get()
        if not self.validate_url(url):
            self.progress_label.config(text='⚠️ Введіть правильний URL.')
            logging.warning('Спроба завантаження з неправильним URL.')
            return
        self.stop_event.clear()
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.download_button.config(state=tk.DISABLED, text='⏳ Завантаження...')
        self.paste_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        threading.Thread(target=self.run_download, args=(url,), daemon=True).start()
        logging.info(f'Почато завантаження: {url}')

    def stop_download(self):
        self.stop_event.set()
        self.progress_label.config(text='🛑 Зупиняємо...')
        logging.info('Натиснута кнопка "Зупинити".')

    def download_success(self):
        self.download_button.config(state=tk.NORMAL, text='⬇️ Завантажити відео в папку на Робочому столі: YouTube_Downloads')
        self.paste_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_label.config(text='✅ Завантаження завершено!')

    def download_error(self, message):
        self.download_button.config(state=tk.NORMAL, text='⬇️ Завантажити відео в папку на Робочому столі: YouTube_Downloads')
        self.paste_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_label.config(text=f'❌ Помилка: {message}')
        logging.error(f'Помилка: {message}')

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.run()
