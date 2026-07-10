import datetime
import sys
from renderer import Renderering
import sqlite3
from dispatcher import Tools
import requests
from config import OPENWEATHER_API
from promptbuilder import Prompts
import json
import random
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QMainWindow, QTextBrowser, QFileDialog
from ddgs import DDGS
from dataclasses import dataclass
from typing import Optional
@dataclass
class AIReply:
    reply: str
    action: Optional[str]
    tool_input: Optional[str]
    memory_key: Optional[str]
    memory_value: Optional[str]

@dataclass
class WeatherData:
    temperaturec: Optional[float]
    humidityc: Optional[float]
    wind_speedc: Optional[float]
    weather_descriptionc: str | None
@dataclass
class SearchResult:
    title: str
    url: str
    body: str
class WebSearch(QThread):
    signal = pyqtSignal(object)
    def __init__(self,texts):
        super().__init__()
        self.texts = texts
    def run(self):
        web_results:list[SearchResult] = []
        with DDGS() as ddgs:
            results = ddgs.text(self.texts,max_results=3)
            if results:
                for r in results:
                    title = r["title"]
                    url = r["href"]
                    body = r["body"]
                    web_results.append(SearchResult(
                        title=title,
                        url=url,
                        body=body
                    ))
                self.signal.emit(web_results)
            else:
                self.signal.emit("No results found")
class weatherstuff(QThread):
    signalweather = pyqtSignal(object)
    def __init__(self,city:str) ->None:
        super().__init__()
        self.city =city
    def run(self):
        api = OPENWEATHER_API
        url = f"https://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={api}"
        r = requests.get(url)
        if r.status_code == 200:
            response = r.json()
            temperature = response['main']['temp']
            weather_description = response['weather'][0]['description']
            humidity = response['main']['humidity']
            wind_speed = response['wind']['speed']
            temp_c = temperature - 273.15
            x =WeatherData(
                temperaturec= temp_c,
                humidityc = humidity,
                wind_speedc= wind_speed,
                weather_descriptionc = weather_description

            )
        else:
            x =WeatherData(
                temperaturec= None,
                humidityc= None,
                wind_speedc=None,
                weather_descriptionc = None
            )
        self.signalweather.emit(x)
class ollamastuff(QThread):
    signal = pyqtSignal(object)
    def __init__(self,user_prompt,chat_context,memory_for_val,reading,weatherstuffig,websearch1):
        super().__init__()
        self.user_prompt = user_prompt
        self.chat_context = chat_context
        self.memory_for_val = memory_for_val
        self.reading = reading
        self.weatherstuffig = weatherstuffig
        self.websearchstuff = websearch1
    def run(self):
        url = "http://localhost:11434/api/generate"
        session_proxies = {
            "http": None,
            "https": None,
        }
        mibowlo = Prompts.build(self.user_prompt,self.chat_context,self.memory_for_val,self.reading,self.weatherstuffig,self.websearchstuff)

        payload = {"model":"qwen2.5:7b","prompt":mibowlo,"stream":False,"format":"json"}
        try:
            response = requests.post(url,json=payload,proxies = session_proxies)
            response_json = response.json()
            raw_reply = response_json.get("response","{}")
            raw = json.loads(raw_reply)
            parsed_data = AIReply(
                reply=raw.get("reply",""),
                action=raw.get("action",None),
                tool_input=raw.get("tool_input",None),
                memory_key=raw.get("memory_key",None),
                memory_value=raw.get("memory_value",None),
            )
        except Exception as e:
            parsed_data = AIReply(
                reply=f"SORRY YOU ENCOUNTERED AN ERROR {e}",
                action=None,
                tool_input=None,
                memory_key= None,
                memory_value= None
            )
        self.signal.emit(parsed_data)
class lalsdatabase:
    def __init__(self):
        self.sql = sqlite3.connect('Signatureproject.db')
        self.cursor = self.sql.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS conversations(message_id INTEGER PRIMARY KEY AUTOINCREMENT,user_message TEXT,ai_message TEXT, date_added TEXT DEFAULT (datetime('now','localtime')))''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS LongTermMemory(memory_key TEXT,memory_value TEXT)
        ''')
        self.sql.commit()
    def insert_message(self,user_message,ai_message):
        self.cursor.execute("INSERT INTO conversations(user_message,ai_message) VALUES (?,?)",(user_message,ai_message))
        self.sql.commit()
    def remembering(self,memory_key,memory_value):
        self.cursor.execute("INSERT OR REPLACE INTO LongTermMemory(memory_key,memory_value) VALUES(?,?)",(memory_key,memory_value,))
        self.sql.commit()
    def recall(self):
        self.cursor.execute("SELECT memory_key,memory_value FROM LongTermMemory")
        x = self.cursor.fetchall()
        key_val = ""
        for memory_key,memory_value in x:
            key_val += f"{memory_key},{memory_value}\n"
        return key_val
    def get_recent_context(self,limit=4):
        self.cursor.execute("SELECT user_message,ai_message FROM conversations ORDER BY date_added DESC LIMIT ?", (limit,))
        rows = self.cursor.fetchall()
        rows.reverse()
        context = ""
        for user_message,ai_message in rows:
            if user_message:
                context += f"dan: {user_message}\n"
            if ai_message:
                context += f"lal: {ai_message}\n"
        return context
import time
def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(end - start)
        return result
    return wrapper
def busy_guard(func):
    def wrapper(self,*args, **kwargs):
        if self.busy:
            return
        self.busy = True
        try:
            return func(self,*args, **kwargs)
        finally:
            self.busy = False
    return wrapper
def catch_errors(func):
    def wrapper(self,*args, **kwargs):
        try:
            return func(self,*args, **kwargs)
        except Exception as e:
            print(f"ERROR {func.__name__} : {str(e)}")
    return wrapper
def log(func):
    def wrapper(self,*args, **kwargs):
        print("starting the function")
        result = func(self,*args, **kwargs)
        print("finished the function")
        return result
    return wrapper
class LalLiteVer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.busy = False
        self.in_tool_followup = False
        self.current_ai_reply = ""
        self.current_char_index = 0
        self.typing_timer = QTimer(self)
        self.typing_timer.timeout.connect(self.type_next_character)
        self.mood = "normal"
        self.db = lalsdatabase()
        self.dispatcher = Tools(self)
        self.rendering = Renderering(self)
        self.f = ""
        self.desc = ""
        self.descforweb = ""
        self.button_for_file = QPushButton("upload TXT file",self)
        self.button_for_file.setGeometry(730,390,120,23)
        self.button_for_file.clicked.connect(self.open_file_fr)
        self.right_left = 0
        self.rightleft_add = 1.5
        self.rightleft_timer = QTimer(self)
        self.rightleft_timer.timeout.connect(self.rightleft_func)
        self.rightleft_timer.start(400)
        self.up_down = 0
        self.updown_add = 1.5
        self.updown_timer = QTimer(self)
        self.updown_timer.timeout.connect(self.updown_func)
        self.updown_timer.start(900)
        self.eye_count_up = 0
        self.eye_count_add = 0.2
        self.eye_count_timer = QTimer(self)
        self.eye_count_timer.timeout.connect(self.eye_count_func)
        self.eye_count_timer.start(10)
#my mind is burning rn fuck this.
        self.breath_count = 0
        self.breath_add = 0.2
        self.breathing_timer = QTimer(self)
        self.health = "breath out"
        self.breathing_timer.timeout.connect(self.breathing_timer_face)
        self.breathing_timer.start(10)
        self.thinking_timer = QTimer(self)
        self.thinking_timer.timeout.connect(self.update_thinking_dots)
        self.dots_count = 0
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.trigger_blink)
        rand_timer = random.randint(2500,7000)
        self.blink_timer.start(rand_timer)
        self.mouse_pos = QPoint(735, 370)
        self.setMouseTracking(True)
        self.setWindowTitle("LalLite")
        self.button = QPushButton("Send message",self)
        self.setGeometry(20,40,1470,740)
        self.button.setGeometry(740,450,100,23)
        self.label = QLabel("Lite Version Of Lal",self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setGeometry(5,265,250,66)
        self.label.setWordWrap(True)
        self.line = QLineEdit(self)
        self.line.setPlaceholderText("Enter message")
        self.line.setGeometry(590,420,400,23)
        self.button.clicked.connect(self.is_clicked_fr)
        self.display_text = QTextBrowser(self)
        self.display_text.setGeometry(590,20,400,250)
        self.styling()
    def styling(self):
        self.setStyleSheet("""
        QPushButton {color:white;
         font-family: Verdana;
         font-size: 12px;
         font-weight: bold;
         background-color: #31616b;
         border: 1px solid #31616b;
         border-radius: 5px;
         }
        QPushButton:hover {background-color: grey;}
        QLabel{font-family: Verdana;
        font-size: 32px;
        font-weight: bold;
        color: white;}
        QTextBrowser{font-family: Verdana;
        font-size: 12px;
        font-weight: bold;
        color: black;
        } 
        """)
    def paintEvent(self,event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.rendering.backgrounddrawing(painter)
        self.rendering.lals_body(painter)
        self.rendering.normal_eyes(painter)
        self.rendering.mouth(painter)
    def handling_labels(self):
        if self.mood == "error":
            self.label.setText("Error")
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Enter,Qt.Key.Key_Return):
            self.memory_for_lal()
    def is_clicked_fr(self):
        self.memory_for_lal()
    @busy_guard
    @log
    @timer

    def memory_for_lal(self):
        text = self.line.text().strip()
        if not text:
            return
        current_time = datetime.datetime.now().strftime("%H:%M")
        dan_html = f"""
        <span style="color: gray; font-size: 10px;">[{current_time}]</span><br>
        <b><font color="#5aa9ff"> 🔵 Dan</font></b><br>
        {text}<br><br>
        """
        self.mood = "thinking"
        self.update()
        self.line.clear()
        self.display_text.append(dan_html)
        self.thinking_timer.start(100)
        chat_history = self.db.get_recent_context(limit=4)
        memory_for_val = self.db.recall()
        if not text:
            return
        else:
            self.current_user_text = text
            self.worker = ollamastuff(text,chat_history,memory_for_val,self.f,self.desc,self.descforweb)
            self.worker.signal.connect(self.handle_ai_reply)
            self.worker.start()
        self.scroll_to_bottom()
    def handle_ai_reply(self,aiq_reply):
        self.line.setPlaceholderText(f"Enter message")
        current_time = datetime.datetime.now().strftime("%H:%M")
        lal_header = f"""
                <span style="color: gray; font-size: 10px;">[{current_time}]</span><br>
                <b><font color="#ff7aff">🟣 Lal</font></b><br>
                """
        self.mood = "normal"
        self.update()
        ai_reply = aiq_reply.reply
        action = aiq_reply.action
        tool_input = aiq_reply.tool_input
        memory_key = aiq_reply.memory_key
        memory_value = aiq_reply.memory_value
        if self.in_tool_followup:
            action = None
            self.in_tool_followup = False
        if self.dispatcher.dispatch(action, tool_input, memory_key, memory_value):
            return
        self.display_text.append(lal_header)
        self.current_ai_reply = ai_reply
        self.current_char_index = 0
        self.typing_timer.start(30)
        self.db.insert_message(self.current_user_text, ai_reply)
        if ai_reply.startswith("Error"):
            self.mood = "error"
        self.desc = ""
        self.descforweb = ""
    def update_thinking_dots(self):
        self.dots_count = (self.dots_count + 1) % 4
        self.dots = "." * self.dots_count
        self.line.setPlaceholderText(f"lal is thinking {self.dots}")
    def trigger_blink(self):
        if self.mood == "normal":
            self.mood = "blink"
        QTimer.singleShot(150, self.reset_blink)
        self.update()
    def reset_blink(self):
        if self.mood == "blink":
            self.mood = "normal"
        self.update()
    def breathing_timer_face(self):
        self.breath_count += self.breath_add
        if self.breath_count >= 6:
            self.breath_add= -0.2
        elif self.breath_count <= 0:
            self.breath_add = 0.2
        self.update()
    def eye_count_func(self):
        self.eye_count_up += self.eye_count_add
        if self.eye_count_up >= 6:
            self.eye_count_add = -0.2
        elif self.eye_count_up <=0:
            self.eye_count_add = 0.2
    def updown_func(self):
        self.up_down += self.updown_add
        if self.up_down >= 10:
            self.updown_add = -1.2
        elif self.up_down <= -10:
            self.updown_add = 1.2
    def rightleft_func(self):
        self.right_left += self.rightleft_add
        if self.right_left >= 10:
            self.rightleft_add = -1.5
        elif self.right_left <= -10:
            self.rightleft_add = 1.5
    def open_file_fr(self):
        self.filename,_ = QFileDialog.getOpenFileName(self,"Open File")
        if self.filename:
            with open(self.filename,"r") as f:
                 self.f = f.read()
    @catch_errors
    def weather_fr(self,desc: object) -> None:
        if desc:
            self.desc = desc
        chat_history = self.db.get_recent_context(limit=4)
        recalling = self.db.recall()
        self.in_tool_followup = True
        self.workerweb3 = ollamastuff(self.current_user_text,chat_history,recalling,self.f,self.desc,self.descforweb)
        self.workerweb3.signal.connect(self.handle_ai_reply)
        self.workerweb3.start()
    @catch_errors
    def web_search_Fr(self,descforweb:object)  -> None:
        if descforweb:
            self.descforweb = descforweb
        chat_history = self.db.get_recent_context(limit=4)
        recalling = self.db.recall()
        self.in_tool_followup = True
        self.workerweb1 = ollamastuff(self.current_user_text,chat_history,recalling,self.f,self.desc,self.descforweb)
        self.workerweb1.signal.connect(self.handle_ai_reply)
        self.workerweb1.start()
    def scroll_to_bottom(self):
        scroll_bar = self.display_text.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
    def type_next_character(self):
        if self.current_char_index < len(self.current_ai_reply):
            char = self.current_ai_reply[self.current_char_index]
            self.display_text.insertPlainText(char)
            self.current_char_index += 1
            self.scroll_to_bottom()
        else:
            self.typing_timer.stop()
        self.thinking_timer.stop()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LalLiteVer()
    window.show()
    sys.exit(app.exec())
