import sys
import io
import os
import json
import re
import pickle
import threading
from difflib import SequenceMatcher
from tkinter import filedialog, messagebox

import customtkinter as ctk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Ensure correct encoding for PyInstaller --noconsole builds
if sys.stdout is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr is not None:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

CONFIG_FILE = "settings.json"

LANG = {
    "en": {
        "title_settings": "Settings",
        "tab_keys": "API Keys",
        "tab_lang": "Language",
        "tab_help": "Help",
        "save": "Save",
        "saved": "Settings saved!",
        "connect": "☁ Connect Accounts",
        "connected": "✔ Connected",
        "source_lbl": "Source Platform:",
        "combo_wait": "Connect first...",
        "combo_empty": "No playlists found",
        "btn_to_sp": "Transfer to Spotify →",
        "btn_to_yt": "Transfer to YouTube →",
        "working": "Working...",
        "welcome": "Welcome to PlaylistMover.\n1. Click ⚙ to setup keys.\n2. Connect accounts.\n3. Select a playlist and click the button.",
        "log_connect_sp": "☁ Connecting to Spotify...",
        "log_connect_yt": "☁ Connecting to YouTube...",
        "log_ok": "✨ Connected successfully! Loading lists...",
        "log_err": "❌ Error: ",
        "log_err_keys": "Check API keys in settings.",
        "err_no_keys": "❌ Error: Settings missing! Click ⚙.",
        "header_not_found": "\n⚠️ TRACKS NOT FOUND (ADD MANUALLY):",
        "success_sp": "\n✨ DONE! Playlist created in Spotify.",
        "success_yt": "\n✨ DONE! Playlist created in YouTube.",
        "search": "Found {0} tracks. Starting transfer...",
        "not_found_file": "YouTube JSON file not found",
        "browse": "Browse",
        "err_quota": "⛔ YOUTUBE QUOTA EXCEEDED!\nDaily limit reached (~60 songs). Try again tomorrow.",
        "help_text": """1. SPOTIFY:
- Go to developer.spotify.com/dashboard
- Create App -> Settings -> Redirect URIs: http://127.0.0.1:8888/callback
- Copy Client ID & Secret.

2. YOUTUBE:
- Go to console.cloud.google.com
- Enable "YouTube Data API v3"
- Credentials -> Create OAuth Client ID -> Desktop App
- Download JSON file."""
    },
    "ru": {
        "title_settings": "Настройки",
        "tab_keys": "API Ключи",
        "tab_lang": "Язык",
        "tab_help": "Помощь",
        "save": "Сохранить",
        "saved": "Настройки сохранены!",
        "connect": "☁ Подключить аккаунты",
        "connected": "✔ Подключено",
        "source_lbl": "Откуда переносим музыку?",
        "combo_wait": "Сначала подключитесь...",
        "combo_empty": "Нет плейлистов",
        "btn_to_sp": "Перенести в Spotify →",
        "btn_to_yt": "Перенести в YouTube →",
        "working": "Работаю...",
        "welcome": "Добро пожаловать в PlaylistMover.\n1. Нажмите ⚙ и настройте ключи.\n2. Подключите аккаунты.\n3. Выберите плейлист и нажмите кнопку.",
        "log_connect_sp": "☁ Подключение к Spotify...",
        "log_connect_yt": "☁ Подключение к YouTube...",
        "log_ok": "✨ Успешно подключено! Загружаю списки...",
        "log_err": "❌ Ошибка: ",
        "log_err_keys": "Проверьте ключи в настройках.",
        "err_no_keys": "❌ Ошибка: Не заполнены настройки! Нажмите ⚙.",
        "header_not_found": "\n⚠️ ЭТИ ТРЕКИ НЕ НАЙДЕНЫ (ДОБАВЬТЕ ВРУЧНУЮ):",
        "success_sp": "\n✨ ГОТОВО! Плейлист создан в Spotify.",
        "success_yt": "\n✨ ГОТОВО! Плейлист создан в YouTube.",
        "search": "Найдено {0} треков. Начинаю перенос...",
        "not_found_file": "Не найден файл JSON для YouTube",
        "browse": "Обзор",
        "err_quota": "⛔ ЛИМИТ YOUTUBE ИСЧЕРПАН!\nДневной лимит (~60 песен) достигнут. Попробуйте завтра.",
        "help_text": """1. SPOTIFY:
- На сайте developer.spotify.com создайте приложение.
- Redirect URI: http://127.0.0.1:8888/callback
- Скопіюйте ID и Secret.

2. YOUTUBE:
- На console.cloud.google.com включите YouTube Data API v3.
- Создайте OAuth Client ID (Desktop App).
- Скачайте JSON."""
    },
    "ua": {
        "title_settings": "Налаштування",
        "tab_keys": "API Ключі",
        "tab_lang": "Мова",
        "tab_help": "Допомога",
        "save": "Зберегти",
        "saved": "Налаштування збережено!",
        "connect": "☁ Підключити акаунти",
        "connected": "✔ Підключено",
        "source_lbl": "Звідки переносимо музику?",
        "combo_wait": "Спочатку підключіться...",
        "combo_empty": "Немає плейлистів",
        "btn_to_sp": "Перенести в Spotify →",
        "btn_to_yt": "Перенести в YouTube →",
        "working": "Працюю...",
        "welcome": "Ласкаво просимо в PlaylistMover.\n1. Натисніть ⚙ та налаштуйте ключі.\n2. Підключіть акаунти.\n3. Оберіть плейлист та натисніть кнопку.",
        "log_connect_sp": "☁ Підключення до Spotify...",
        "log_connect_yt": "☁ Підключення до YouTube...",
        "log_ok": "✨ Успішно підключено! Завантажую списки...",
        "log_err": "❌ Помилка: ",
        "log_err_keys": "Перевірте ключі в налаштуваннях.",
        "err_no_keys": "❌ Помилка: Не заповнені налаштування! Натисніть ⚙.",
        "header_not_found": "\n⚠️ ЦІ ТРЕКИ НЕ ЗНАЙДЕНО (ДОДАЙТЕ ВРУЧНУ):",
        "success_sp": "\n✨ ГОТОВО! Плейлист створено в Spotify.",
        "success_yt": "\n✨ ГОТОВО! Плейлист створено в YouTube.",
        "search": "Знайдено {0} треків. Починаю перенесення...",
        "not_found_file": "Не знайдено файл JSON для YouTube",
        "browse": "Огляд",
        "err_quota": "⛔ ЛІМІТ YOUTUBE ВИЧЕРПАНО!\nДенний ліміт (~60 пісень) досягнуто. Спробуйте завтра.",
        "help_text": """1. SPOTIFY:
- На сайті developer.spotify.com створіть додаток.
- Redirect URI: http://127.0.0.1:8888/callback
- Скопіюйте ID та Secret.

2. YOUTUBE:
- На console.cloud.google.com увімкніть YouTube Data API v3.
- Створіть OAuth Client ID (Desktop App).
- Завантажте JSON."""
    }
}

def load_config():
    default = {"sp_id": "", "sp_secret": "", "sp_redirect": "http://127.0.0.1:8888/callback", "yt_json_path": "", "lang": "en"}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                default.update(data)
                return default
        except Exception:
            pass
    return default

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def tr(key):
    cfg = load_config()
    lang_code = cfg.get("lang", "en")
    return LANG.get(lang_code, LANG["en"]).get(key, key)


class MusicLogic:
    def __init__(self, log_callback):
        self.log = log_callback
        self.sp = None
        self.yt = None
        self.config = load_config()

    def update_config(self):
        self.config = load_config()

    def connect(self):
        self.update_config()
        if not self.config["sp_id"] or not self.config["yt_json_path"]:
            self.log(tr("err_no_keys"))
            return False
        try:
            self.log(tr("log_connect_sp"))
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.config["sp_id"],
                client_secret=self.config["sp_secret"],
                redirect_uri=self.config["sp_redirect"],
                scope="playlist-read-private playlist-modify-public playlist-modify-private"
            ))
            self.sp.current_user()
            
            self.log(tr("log_connect_yt"))
            self.yt = self._auth_youtube()
            
            self.log(tr("log_ok"))
            return True
        except Exception as e:
            self.log(f"{tr('log_err')}{e}")
            self.log(tr("log_err_keys"))
            return False

    def _auth_youtube(self):
        creds = None
        if os.path.exists('token_yt.pickle'):
            try:
                with open('token_yt.pickle', 'rb') as token:
                    creds = pickle.load(token)
            except Exception:
                creds = None
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            
            if not creds:
                if not os.path.exists(self.config["yt_json_path"]):
                    raise FileNotFoundError(tr("not_found_file"))
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config["yt_json_path"], ['https://www.googleapis.com/auth/youtube.force-ssl'])
                creds = flow.run_local_server(port=0)
            
            with open('token_yt.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return build('youtube', 'v3', credentials=creds)

    def get_user_playlists(self, service):
        playlists = {}
        try:
            if service == 'spotify':
                results = self.sp.current_user_playlists(limit=50)
                for item in results['items']:
                    playlists[item['name']] = item['id']
            elif service == 'youtube':
                request = self.yt.playlists().list(part="snippet", mine=True, maxResults=50)
                response = request.execute()
                for item in response['items']:
                    playlists[item['snippet']['title']] = item['id']
            return playlists
        except HttpError as e:
            if "quotaExceeded" in str(e):
                self.log("\n" + tr("err_quota"))
            else:
                self.log(f"Error: {e}")
            return {}
        except Exception as e:
            self.log(f"Error: {e}")
            return {}

    def _clean_string(self, text):
        if not text: return ""
        text = text.lower()
        text = re.sub(r'^\d+\s*[-\.]\s*', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        bad_words = ["official video", "official audio", "lyrics", "visualizer", "hd", "4k", "hq", "prod.", "official"]
        for w in bad_words:
            text = text.replace(w, "")
        text = re.sub(r'(ft\.|feat\.|featuring).*', '', text)
        return text.strip()

    def _clean_channel(self, name):
        if not name: return ""
        return name.replace(" - Topic", "").replace("VEVO", "").replace("Official", "").replace("Release", "").strip()

    def _similarity(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def _search_spotify_smart(self, query, artist, track_name, strict=True):
        try:
            res = self.sp.search(q=query, limit=1, type='track')
            if not res['tracks']['items']: return None
            track = res['tracks']['items'][0]
            sp_artist = self._clean_string(track['artists'][0]['name'])
            sp_name = self._clean_string(track['name'])
            
            name_sim = self._similarity(track_name, sp_name)
            artist_match = False
            if artist:
                art_sim = self._similarity(artist, sp_artist)
                if art_sim > 0.4 or (artist in sp_artist) or (sp_artist in artist):
                    artist_match = True
            
            if strict:
                if artist_match and name_sim >= 0.5: return track
            else:
                if name_sim >= 0.7: return track
                if artist and artist in sp_name: return track
            return None
        except Exception:
            return None

    def run_transfer(self, mode, playlist_id, playlist_name):
        failed_tracks = []
        
        if mode == 'yt_to_sp':
            self.log(f"\n--- YouTube ({playlist_name}) -> Spotify ---")
            videos = []
            next_page = None
            try:
                while True:
                    req = self.yt.playlistItems().list(part='snippet', playlistId=playlist_id, maxResults=50, pageToken=next_page)
                    resp = req.execute()
                    for item in resp['items']:
                        videos.append({
                            'title': item['snippet']['title'],
                            'channel': item['snippet'].get('videoOwnerChannelTitle', item['snippet']['channelTitle'])
                        })
                    next_page = resp.get('nextPageToken')
                    if not next_page: break
            except Exception as e:
                self.log(f"❌ YouTube Error: {e}")
                return

            self.log(tr("search").format(len(videos)))
            uris = []
            for vid in videos:
                raw_t = vid['title']
                clean_c = self._clean_string(self._clean_channel(vid['channel']))
                
                if " - " in raw_t:
                    parts = raw_t.split(" - ")
                    artist_g = self._clean_string(parts[0])
                    track_g = self._clean_string(" ".join(parts[1:])) if len(parts)>2 else self._clean_string(parts[1])
                else:
                    artist_g = clean_c
                    track_g = self._clean_string(raw_t)

                found = self._search_spotify_smart(f"artist:{artist_g} track:{track_g}", artist_g, track_g, True)
                if not found:
                    found = self._search_spotify_smart(f"{artist_g} {track_g}", artist_g, track_g, True)
                if not found:
                    found = self._search_spotify_smart(track_g, artist_g, track_g, False)

                if found:
                    uris.append(found['uri'])
                    self.log(f"[+] {raw_t} -> {found['artists'][0]['name']} - {found['name']}")
                else:
                    self.log(f"[-] NOT FOUND: {raw_t}")
                    failed_tracks.append(raw_t)

            if uris:
                try:
                    uid = self.sp.current_user()['id']
                    pl = self.sp.user_playlist_create(uid, f"PlaylistMover: {playlist_name}", public=False)
                    for i in range(0, len(uris), 100):
                        self.sp.playlist_add_items(pl['id'], uris[i:i+100])
                    self.log(tr("success_sp"))
                except Exception as e:
                    self.log(f"Error: {e}")
            else:
                self.log("Nothing found.")

        elif mode == 'sp_to_yt':
            self.log(f"\n--- Spotify ({playlist_name}) -> YouTube ---")
            try:
                res = self.sp.playlist_items(playlist_id)
                tracks = [i['track'] for i in res['items'] if i['track']]
                while res['next']:
                    res = self.sp.next(res)
                    tracks.extend([i['track'] for i in res['items'] if i['track']])
            except Exception as e:
                self.log(f"❌ Spotify Error: {e}")
                return

            self.log(tr("search").format(len(tracks)))
            
            new_pl_id = None
            try:
                new_pl = self.yt.playlists().insert(part='snippet,status', body={
                    'snippet': {'title': f"PlaylistMover: {playlist_name}"},
                    'status': {'privacyStatus': 'private'}
                }).execute()
                new_pl_id = new_pl['id']
            except HttpError as e:
                if "quotaExceeded" in str(e):
                    self.log("\n" + tr("err_quota"))
                    return
                else:
                    self.log(f"❌ YouTube Error: {e}")
                    return
            except Exception as e:
                self.log(f"Error: {e}")
                return

            for t in tracks:
                query = f"{t['artists'][0]['name']} - {t['name']}"
                try:
                    search = self.yt.search().list(q=query, part='id', maxResults=1, type='video').execute()
                    if search['items']:
                        vid = search['items'][0]['id']['videoId']
                        self.yt.playlistItems().insert(part='snippet', body={
                            'snippet': {'playlistId': new_pl_id, 'resourceId': {'kind': 'youtube#video', 'videoId': vid}}
                        }).execute()
                        self.log(f"[+] {query}")
                    else:
                        self.log(f"[-] NOT FOUND: {query}")
                        failed_tracks.append(query)
                except HttpError as e:
                    if "quotaExceeded" in str(e):
                        self.log("\n" + tr("err_quota"))
                        break
                    else:
                        self.log(f"[!] API Error: {e}")
                        failed_tracks.append(query)
                except Exception as e:
                    self.log(f"[!] Error: {e}")
                    failed_tracks.append(query)
            
            self.log(tr("success_yt"))

        if failed_tracks:
            self.log(tr("header_not_found"))
            self.log("-" * 40)
            for fail in failed_tracks:
                self.log(f"• {fail}")
            self.log("-" * 40)


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(tr("title_settings"))
        self.geometry("500x550")
        self.parent = parent
        
        self.tabview = ctk.CTkTabview(self, width=480, height=480)
        self.tabview.pack(padx=10, pady=10)
        
        self.tab_keys = self.tabview.add(tr("tab_keys"))
        self.tab_lang = self.tabview.add(tr("tab_lang"))
        self.tab_help = self.tabview.add(tr("tab_help"))

        config = load_config()

        ctk.CTkLabel(self.tab_keys, text="Spotify Client ID:").pack(anchor="w", padx=10)
        self.entry_sp_id = ctk.CTkEntry(self.tab_keys, width=400)
        self.entry_sp_id.insert(0, config.get("sp_id", ""))
        self.entry_sp_id.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(self.tab_keys, text="Spotify Client Secret:").pack(anchor="w", padx=10)
        self.entry_sp_secret = ctk.CTkEntry(self.tab_keys, width=400, show="*")
        self.entry_sp_secret.insert(0, config.get("sp_secret", ""))
        self.entry_sp_secret.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(self.tab_keys, text="Spotify Redirect URI:").pack(anchor="w", padx=10)
        self.entry_sp_uri = ctk.CTkEntry(self.tab_keys, width=400)
        self.entry_sp_uri.insert(0, config.get("sp_redirect", "http://127.0.0.1:8888/callback"))
        self.entry_sp_uri.pack(padx=10, pady=(0, 10))

        ctk.CTkLabel(self.tab_keys, text="YouTube JSON:").pack(anchor="w", padx=10)
        self.frame_yt = ctk.CTkFrame(self.tab_keys, fg_color="transparent")
        self.frame_yt.pack(padx=10, pady=(0, 10), fill="x")
        self.entry_yt_path = ctk.CTkEntry(self.frame_yt, width=300)
        self.entry_yt_path.insert(0, config.get("yt_json_path", ""))
        self.entry_yt_path.pack(side="left")
        ctk.CTkButton(self.frame_yt, text=tr("browse"), width=80, fg_color="#333", hover_color="#444", command=self.browse_file).pack(side="right", padx=5)

        self.lang_var = ctk.StringVar(value=config.get("lang", "en"))
        ctk.CTkLabel(self.tab_lang, text="Language:", font=("Arial", 14)).pack(pady=20)
        ctk.CTkRadioButton(self.tab_lang, text="English", variable=self.lang_var, value="en").pack(pady=10)
        ctk.CTkRadioButton(self.tab_lang, text="Русский", variable=self.lang_var, value="ru").pack(pady=10)
        ctk.CTkRadioButton(self.tab_lang, text="Українська", variable=self.lang_var, value="ua").pack(pady=10)

        ctk.CTkButton(self, text=tr("save"), fg_color="#00A8E8", text_color="#1a1a1a", hover_color="#4CC9F0", font=("Arial", 13, "bold"), command=self.save_settings).pack(pady=10)
        
        help_box = ctk.CTkTextbox(self.tab_help, width=450, height=400)
        help_box.pack(pady=5)
        help_box.insert("0.0", tr("help_text"))
        help_box.configure(state="disabled")

    def browse_file(self):
        f = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if f:
            self.entry_yt_path.delete(0, "end")
            self.entry_yt_path.insert(0, f)

    def save_settings(self):
        save_config({
            "sp_id": self.entry_sp_id.get().strip(),
            "sp_secret": self.entry_sp_secret.get().strip(),
            "sp_redirect": self.entry_sp_uri.get().strip(),
            "yt_json_path": self.entry_yt_path.get().strip(),
            "lang": self.lang_var.get()
        })
        messagebox.showinfo(tr("saved"), tr("saved"))
        self.parent.refresh_ui_text()
        self.destroy()


class SSK4SApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PlaylistMover")
        self.geometry("600x650")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.col_sky = "#00A8E8"
        self.col_sky_hover = "#4CC9F0"
        self.text_on_sky = "#1a1a1a"
        
        self.logic = MusicLogic(self.log_message)
        self.yt_playlists = {}
        self.sp_playlists = {}
        
        try:
            self.iconbitmap("PlaylistMover.ico") 
        except Exception:
            pass 

        self.header_frame = ctk.CTkFrame(self, height=60, fg_color="transparent")
        self.header_frame.pack(pady=20, fill="x")
        
        self.lbl_title = ctk.CTkLabel(self.header_frame, text="PlaylistMover", font=("Futura", 40, "bold"), text_color=self.col_sky)
        self.lbl_title.place(relx=0.5, rely=0.5, anchor="center")

        self.btn_settings = ctk.CTkButton(self.header_frame, text="⚙", width=40, height=40, fg_color="#333", hover_color="#444", command=self.open_settings)
        self.btn_settings.place(relx=0.92, rely=0.5, anchor="center")

        self.btn_connect = ctk.CTkButton(self, text=tr("connect"), fg_color=self.col_sky, hover_color=self.col_sky_hover, text_color=self.text_on_sky, height=40, font=("Arial", 14, "bold"), command=self.start_connect)
        self.btn_connect.pack(pady=10)

        self.lbl_src = ctk.CTkLabel(self, text=tr("source_lbl"))
        self.lbl_src.pack(pady=(20, 5))

        self.source_var = ctk.StringVar(value="YouTube")
        self.seg_source = ctk.CTkSegmentedButton(self, values=["YouTube", "Spotify"], variable=self.source_var, command=self.on_source_change, selected_color=self.col_sky, selected_hover_color=self.col_sky_hover)
        self.seg_source.pack(pady=5)

        self.combo_var = ctk.StringVar(value=tr("combo_wait"))
        self.combo_playlist = ctk.CTkComboBox(self, width=400, variable=self.combo_var, state="disabled")
        self.combo_playlist.pack(pady=10)

        self.btn_start = ctk.CTkButton(self, text=tr("btn_to_sp"), fg_color=self.col_sky, hover_color=self.col_sky_hover, text_color=self.text_on_sky, height=50, width=250, font=("Arial", 16, "bold"), state="disabled", command=self.start_transfer)
        self.btn_start.pack(pady=20)

        self.textbox = ctk.CTkTextbox(self, width=550, height=200, border_color="#333", border_width=2)
        self.textbox.pack(pady=10)
        self.textbox.configure(state="disabled")
        
        self.log_message(tr("welcome"))

    def refresh_ui_text(self):
        self.btn_connect.configure(text=tr("connect"))
        self.lbl_src.configure(text=tr("source_lbl"))
        self.combo_var.set(tr("combo_wait"))
        self.on_source_change(self.source_var.get())
        self.log_message("-" * 20)
        self.log_message(tr("welcome"))

    def log_message(self, message):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def open_settings(self):
        SettingsWindow(self)

    def start_connect(self):
        threading.Thread(target=self._connect_thread, daemon=True).start()

    def _connect_thread(self):
        if self.logic.connect():
            self.yt_playlists = self.logic.get_user_playlists('youtube')
            self.sp_playlists = self.logic.get_user_playlists('spotify')
            self.btn_connect.configure(state="disabled", text=tr("connected"), fg_color="#333", text_color="white")
            self.combo_playlist.configure(state="normal")
            self.btn_start.configure(state="normal")
            self.on_source_change(self.source_var.get())

    def on_source_change(self, value):
        if not self.yt_playlists and not self.sp_playlists: return
        
        target_list = self.yt_playlists if value == "YouTube" else self.sp_playlists
        names = list(target_list.keys())
        
        if names:
            self.combo_playlist.configure(values=names)
            self.combo_var.set(names[0])
        else:
            self.combo_playlist.configure(values=[tr("combo_empty")])
            self.combo_var.set(tr("combo_empty"))

        if value == "YouTube":
            self.btn_start.configure(text=tr("btn_to_sp"))
        else:
            self.btn_start.configure(text=tr("btn_to_yt"))

    def start_transfer(self):
        pl_name = self.combo_var.get()
        source = self.source_var.get()
        mode = 'yt_to_sp' if source == "YouTube" else 'sp_to_yt'
        pl_id = self.yt_playlists.get(pl_name) if source == "YouTube" else self.sp_playlists.get(pl_name)
        
        if not pl_id:
            self.log_message(f"❌ {tr('combo_empty')}")
            return

        self.btn_start.configure(state="disabled", text=tr("working"), fg_color="#444", text_color="white")
        threading.Thread(target=self._run_logic_wrapper, args=(mode, pl_id, pl_name), daemon=True).start()

    def _run_logic_wrapper(self, mode, pl_id, pl_name):
        self.logic.run_transfer(mode, pl_id, pl_name)
        source = self.source_var.get()
        new_text = tr("btn_to_sp") if source == "YouTube" else tr("btn_to_yt")
        self.btn_start.configure(state="normal", text=new_text, fg_color=self.col_sky, text_color=self.text_on_sky)

if __name__ == "__main__":
    app = SSK4SApp()
    app.mainloop()
