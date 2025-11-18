# Webots AI Drone

This project makes a drone fly autonomously in **Webots**. It takes pictures, sends them to a local AI (**Ollama**), and moves based on what the AI sees.

## The Files

* **`vlm_controller.py` This controller runs inside Webots. It keeps the drone stable, takes photos, and follows commands.
* **`vlm_server.py` This runs in your terminal. It talks to the AI model and tells the drone to turn left, turn right, or move forward.

---

## Downloads

1.  **[Webots Simulator](https://cyberbotics.com/)**
2.  **[Ollama](https://ollama.com/)**
3.  **Python 3.10+**

---

## Setup

### 1. Install the AI
Open your terminal and run:
```bash
ollama run llava
```
Wait for the download to complete and type:
```bash
/bye
```
### 2. Setup the custom Ollama Llava Server
Install Dependencies for Ollama Server:
```bash
pip install fastapi uvicorn python-multipart ollama
```
Run the server in the background:
```bash
python vlm_server.py
```
### 3. Run the Webots Controller in Webots






