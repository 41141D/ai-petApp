class Tools:
    def __init__(self,window):
        self.window = window

    def dispatch(self,action, tool_input, memory_key, memory_value):
        if action == "weather":
            from Signatureproject import weatherstuff
            self.window.starter = weatherstuff(tool_input)
            self.window.starter.signalweather.connect(self.window.weather_fr)
            self.window.starter.start()
            return True
        elif action == "search":
            from Signatureproject import WebSearch
            self.window.webstarter = WebSearch(tool_input)
            self.window.webstarter.signal.connect(self.window.web_search_Fr)
            self.window.webstarter.start()
            return True
        elif action == "remember" and memory_key and memory_value:
            self.window.db.remembering(memory_key, memory_value)
            return False
        return None
