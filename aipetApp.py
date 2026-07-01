#you can change the model and the prompts if u want to, enjoyy!

import sys
import sqlite3
import requests
import json
import random
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QMainWindow, QTextBrowser, QFileDialog

class weatherstuff(QThread):
    signalweather = pyqtSignal(dict)
    def __init__(self,city):
        super().__init__()
        self.city =city
    def run(self):
        api = "4e82ae2ab02eaa6c9c4078536e027579"
        url = f"https://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={api}"
        r = requests.get(url)
        if r.status_code == 200:
            response = r.json()
            temperature = response['main']['temp']
            weather_description = response['weather'][0]['description']
            humidity = response['main']['humidity']
            wind_speed = response['wind']['speed']
            temp_c = temperature - 273.15
            x ={
                "temp":temp_c,
                "humidity":humidity,
                "wind_speed":wind_speed,
                "weather_description":weather_description,
            }
        self.signalweather.emit(x)

class ollamastuff(QThread):
    signal = pyqtSignal(dict)
    def __init__(self,user_prompt,chat_context,memory_for_val,reading,weatherstuffig):
        super().__init__()
        self.user_prompt = user_prompt
        self.chat_context = chat_context
        self.memory_for_val = memory_for_val
        self.reading = reading
        self.weatherstuffig = weatherstuffig
    def run(self):
        url = "http://localhost:11434/api/generate"
        session_proxies = {
            "http": None,
            "https": None,
        }
        system_prompt = (
            "You are Lilac (nicknamed 'Lal'), a highly intelligent AI companion "
            "for Dan, an 18-year-old software engineering student at Koya University.\n\n"

            "GENERAL RULES:\n"
            "- Always respond ONLY with valid JSON.\n"
            "- Never output any text outside the JSON object.\n"
            "- Be intelligent, concise, honest, and helpful.\n"
            "- Never invent facts. If you don't know something, say so.\n\n"

            "AVAILABLE TOOLS:\n\n"

            "1. MEMORY TOOL\n"
            "- If Dan asks you to permanently remember something, "
            "set action='remember'.\n"
            "- Store the information using memory_key and memory_value.\n"
            "- If memory is not required, set action to null.\n\n"

            "2. WEATHER TOOL\n"
            "- You CANNOT access live weather yourself.\n"
            "- Whenever Dan asks about current weather, temperature, humidity, rain, "
            "wind, or today's forecast, call the weather tool.\n"
            "- Set action='weather'.\n"
            "- tool_input MUST contain ONLY the city name.\n"
            "- Examples of valid tool_input:\n"
            "  London\n"
            "  Erbil\n"
            "  Tokyo\n"
            "- Do NOT include extra words such as:\n"
            "  weather in London\n"
            "  city: London\n\n"

            "- If Dan does not specify a city, ask which city he means.\n"
            "- In that situation:\n"
            "  action = null\n"
            "  tool_input = null\n\n"

            "- If weather information has already been provided by the application, "
            "DO NOT call the weather tool again.\n"
            "- Instead, answer naturally using the supplied weather data.\n\n"

            "EXAMPLES:\n\n"

            "User: What's the weather in London?\n"
            "{\n"
            '  "reply":"Checking the weather for London...",\n'
            '  "action":"weather",\n'
            '  "tool_input":"London",\n'
            '  "memory_key":null,\n'
            '  "memory_value":null\n'
            "}\n\n"

            "User: What's the weather today?\n"
            "{\n"
            '  "reply":"Which city would you like the weather for?",\n'
            '  "action":null,\n'
            '  "tool_input":null,\n'
            '  "memory_key":null,\n'
            '  "memory_value":null\n'
            "}\n\n"

            "REQUIRED JSON FORMAT:\n"
            "{\n"
            '  "reply":"...",\n'
            '  "action":"remember" | "weather" | null,\n'
            '  "tool_input":"..." | null,\n'
            '  "memory_key":"..." | null,\n'
            '  "memory_value":"..." | null\n'
            "}"
        )
        full_prompt = (
            f"{system_prompt}\n"
            f"MEMORY:\n{self.memory_for_val}\n\n"
            f"CONVERSATION HISTORY:\n"
            f"{self.chat_context}\n"
            f"Dan: {self.user_prompt}\n"
            f"FILE CONTENT {self.reading}\n"
            f"WEATHER {self.weatherstuffig}"
            f"Lal:"
        )
        payload = {"model":"qwen2.5:7b","prompt":full_prompt,"stream":False,"format":"json"}
        try:
            response = requests.post(url,json=payload,proxies = session_proxies)
            response_json = response.json()
            raw_reply = response_json.get("response","{}")
            parsed_data = json.loads(raw_reply)
        except Exception as e:
            parsed_data = {"reply":f"Error connecting to Ollama or parsing JSON: {str(e)}",
                           "action":None,
                           "tool_input":None,
                           "memory_key":None,
                           "memory_value":None
                           }
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
class LalLiteVer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.f = ""
        self.desc = ""
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
        self.mood = "normal"
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.trigger_blink)
        rand_timer = random.randint(2500,7000)
        self.blink_timer.start(rand_timer)
        self.db = lalsdatabase()
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
        self.backgrounddrawing(painter)
        self.lals_body(painter)
        self.normal_eyes(painter)
        self.mouth(painter)
    def backgrounddrawing(self,painter):
        if self.mood == "normal":
            painter.fillRect(self.rect(),QColor("#31616b"))
        elif self.mood == "thinking":
            painter.fillRect(self.rect(),QColor("#1a3a4b"))
        elif self.mood == "error":
            painter.fillRect(self.rect(),QColor("red"))
        elif self.mood == "blink":
            painter.fillRect(self.rect(),QColor("#31616b"))
    def lals_body(self,painter):
        y = int(47 + self.breath_count)
        if self.mood == "normal":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#0b2330"))
            painter.drawEllipse(25,y,200,200)
        elif self.mood == "error":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("black"))
            painter.drawEllipse(25,y,200,200)
        elif self.mood == "thinking":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#0b2330"))
            painter.drawEllipse(25,47,200,200)
        elif self.mood == "blink":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#0b2330"))
            painter.drawEllipse(25,47,200,200)
    def normal_eyes(self,painter):
        y = int(112 + self.eye_count_up)
        x_pup = int(123 + self.eye_count_up)
        up_down = int(x_pup + self.up_down)
        right_right = int(self.right_left + 154)
        left_left = int(self.right_left + 83)
        if self.mood == "normal":
            #eyes
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("black"))
            painter.drawEllipse(65,y,45,35)
            painter.drawEllipse(137,y,45,32)
            #pupil
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("white"))
            painter.drawEllipse(left_left,up_down,10,10)
            painter.drawEllipse(right_right,up_down,10,10)
        elif self.mood == "thinking":
            #eyes
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("black"))
            painter.drawEllipse(65,109,45,35)
            painter.drawEllipse(137,109,45,32)
            #pupil
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("white"))
            painter.drawEllipse(83,112,10,10)
            painter.drawEllipse(154,112,10,10)
        elif self.mood == "error":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(176, 45, 12))
            painter.drawEllipse(65,x_pup,45,35)
            painter.drawEllipse(137,x_pup,45,32)
        elif self.mood == "blink":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setPen(QPen(QColor("white"),3))
            painter.drawLine(65, 125, 110, 125)
            painter.drawLine(137, 125, 182, 125)
    def mouth(self,painter):
        y = int(self.breath_count + 180)
        if self.mood == "normal":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("white"))
            painter.drawEllipse(97,y,55,15)
        elif self.mood == "error":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("red"))
            painter.drawEllipse(100,y,45,25)
        elif self.mood == "thinking":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("black"))
            painter.drawEllipse(100,180,45,25)
        elif self.mood == "blink":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setPen(QPen(QColor("white"),3))
            painter.drawEllipse(100,180,45,25)
    def handling_labels(self):
        if self.mood == "error":
            self.label.setText("Error")
    def keyPressEvent(self,event):
        if event.key() in (Qt.Key.Key_Enter,Qt.Key.Key_Return):
            self.memory_for_lal()
    def is_clicked_fr(self):
        self.memory_for_lal()
    def memory_for_lal(self):
        text = self.line.text().strip()
        self.mood = "thinking"
        self.update()
        self.line.clear()
        self.display_text.append(f"Dan: {text}")
        chat_history = self.db.get_recent_context(limit=4)
        memory_for_val = self.db.recall()
        if not text:
            return
        else:
            self.current_user_text = text
            self.worker = ollamastuff(text,chat_history,memory_for_val,self.f,self.desc)
            self.worker.signal.connect(self.handle_ai_reply)
            self.worker.start()
    def handle_ai_reply(self,aiq_reply):
        self.line.setPlaceholderText(f"Enter message")
        self.mood = "normal"
        self.update()
        ai_reply = aiq_reply.get("reply","")
        action = aiq_reply.get("action")
        city = aiq_reply.get("tool_input")
        memory_key = aiq_reply.get("memory_key")
        memory_value = aiq_reply.get("memory_value")

        if action == "weather":
            self.starter = weatherstuff(city)
            self.starter.signalweather.connect(self.weather_fr)
            self.starter.weatherdescription.connect(self.weather_fr)
            self.starter.start()














        if action == "remember" and memory_key and memory_value:
            self.db.remembering(memory_key, memory_value)
            self.display_text.append(f"[System: Lal executed 'remember' -> {memory_key}: {memory_value}]\n")
        self.display_text.append(f"Lal: {ai_reply}\n")
        self.db.insert_message(self.current_user_text, ai_reply)
        if ai_reply.startswith("Error"):
            self.mood = "error"
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
    def weather_fr(self,desc):
        self.desc = desc



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LalLiteVer()
    window.show()
    sys.exit(app.exec())
