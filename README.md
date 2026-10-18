# 🚀 Shipmates

**Shipmates** is a custom-built online multiplayer social deduction game inspired by *Among Us*, developed using **Python**, **Tkinter**, **FastAPI**, and **WebSockets**. 

Play online with friends across the world without messing around with complicated local network setups or port forwarding—hosted effortlessly on **Render**!

---

## ✨ Features

* **🌐 True Online Multiplayer:** Connects live via WebSockets hosted in the cloud.
* **🕵️ Random Roles:** Automatically assigns secret roles (**Crewmate** or **Impostor**) upon joining.
* **👁️ Fog-of-War Vision:** Limited vision system so you can only see rooms and corridors immediately around your character.
* **⚡ Interactive Tasks:** Complete interactive wire-matching puzzles to win as a crewmate.
* **🔪 Kill & Report Mechanics:** Impostors can eliminate players, leaving behind dead bodies that other crewmates can report.
* **🚨 Emergency Meetings:** Trigger meetings to debate suspects and chat.
* **💬 Built-in Live Text Chat:** Press **T** anytime in-game to chat live with other players across different PCs.
* **👤 Username & Avatar Customization:** Pick your custom username and color before launching into the ship.

---

## 📁 Repository Structure

To host and run the game, your repository should contain:
* `server.py` — The FastAPI & WebSocket backend server.
* `requirements.txt` — Python dependencies for the server (`fastapi`, `uvicorn`, `websockets`).
* `shipmates.py` — The local Python/Tkinter game client running on players' PCs.

---

## 🛠️ Setup Instructions

### Part 1: Deploy the Backend Server (Render)
1. Create a new public repository on GitHub and upload `server.py` and `requirements.txt`.
2. Go to [Render](https://dashboard.render.com/), click **New +** -> **Web Service**, and connect your repository.
3. Configure your service:
   * **Language:** Python 3
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `python server.py`
   * **Plan:** Free
4. Once live, copy your public URL (e.g., `https://your-app-name.onrender.com`).

### Part 2: Set Up and Run the Game Client
1. Make sure you have Python installed on your PC.
2. Open your terminal/command prompt and install the required websocket client package:
   ```bash
   pip install websocket-client
