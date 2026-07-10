# LalLiteVer 🤖

A custom PyQt6 desktop virtual assistant interface named **LalLite**. It communicates with a locally hosted LLM via Ollama (`qwen2.5:7b`), handles real-time web searching, fetches live weather updates, and features a dynamic animated face.

## Features
* **Local AI Processing:** Queries a local Ollama instance using structured JSON schema.
* **Persistent Memory:** SQLite integration to remember user conversation histories and core memory attributes.
* **Asynchronous Execution:** Multi-threaded operations (`QThread`) ensure the PyQt UI remains fluid during API or local inference tasks.
* **Dynamic UI Painting:** Custom animated avatar face showing breathing cycles, blinking, and thinking states.

## Prerequisites
* Python 3.10+
* Ollama installed locally with the `qwen2.5:7b` model pulled.
* OpenWeatherAPI Key.
