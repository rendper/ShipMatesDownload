import tkinter as tk
import random
import math
import json
import threading
import websocket
import base64
import sounddevice as sd
import numpy as np

# Make sure this matches your exact Render URL
WS_URL = "wss://crewserver.onrender.com/ws"

TILE = 28
COLS, ROWS = 32, 20
WIDTH, HEIGHT = COLS * TILE, ROWS * TILE + 80
VISION = 5.5

# --- GLOBAL VOICE CHAT SETUP (UDP / Cloud WebSocket Relay) ---
voice_enabled = True
audio_active = True

def record_and_send_audio(ws_conn, p_id):
    def callback(indata, frames, time, status):
        if not voice_enabled or not audio_active: return
        try:
            audio_bytes = indata.astype(np.float32).tobytes()
            b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            payload = json.dumps({"action": "voice", "sender": p_id, "audio": b64_audio})
            if ws_conn and ws_conn.sock and ws_conn.sock.connected:
                ws_conn.send(payload)
        except:
            pass

    try:
        stream = sd.InputStream(samplerate=8000, channels=1, callback=callback, blocksize=2048)
        stream.start()
    except Exception as e:
        print("Mic initialization note (audio optional):", e)

def play_incoming_audio(b64_audio):
    if not voice_enabled or not audio_active: return
    try:
        audio_bytes = base64.b64decode(b64_audio)
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
        sd.play(audio_data, 8000)
    except:
        pass
# -----------------------------------------------------------

root = tk.Tk()
root.title("Shipmates - Full Online Multiplayer Edition")
root.resizable(False, False)
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#101827", highlightthickness=0)
canvas.pack()

COLORS = [
    ("Cyan", "#22a9e8"), ("Red", "#ed4545"), ("Lime", "#5bd18a"),
    ("Purple", "#b46bea"), ("Yellow", "#f2c94c")
]
screen = "menu"
username = "Player1"
role = "Crewmate"
color_index = 0
keys = set()
player_id = username
player = {"x": 4, "y": 4, "color": COLORS[0][1], "name": username}
other_players = {}
tasks = set()
bodies = []
chat_messages = []
chat_input_text = ""
typing_chat = False
message = ""
task_game = None
meeting_active = False
votes = {}
voted = False

kill_btn = (WIDTH - 110, HEIGHT - 70, WIDTH - 10, HEIGHT - 38)
report_btn = (WIDTH - 230, HEIGHT - 70, WIDTH - 130, HEIGHT - 38)

ws = None

def connect_ws():
    global ws
    def on_message(ws_conn, message_str):
        global other_players, tasks, bodies, meeting_active, votes, message, chat_messages, role, voted
        try:
            data = json.loads(message_str)
            if data.get("action") == "voice":
                if data.get("sender") != player_id:
                    play_incoming_audio(data.get("audio"))
                return

            if "players" in data:
                other_players = {k: v for k, v in data["players"].items() if k != player_id}
                if player_id in data["players"]:
                    role = data["players"][player_id].get("role", "Crewmate")
            if "bodies" in data:
                bodies = data["bodies"]
            
            old_meeting = meeting_active
            if "meeting" in data:
                meeting_active = data["meeting"]
                if old_meeting and not meeting_active:
                    voted = False  # Reset vote state when meeting ends

            if "votes" in data:
                votes = data["votes"]
            if "chat" in data:
                chat_messages = data["chat"]
            if "msg" in data:
                message = data["msg"]
        except Exception as e:
            print("WS Error:", e)

    try:
        ws = websocket.WebSocketApp(WS_URL, on_message=on_message)
        threading.Thread(target=ws.run_forever, daemon=True).start()
        threading.Thread(target=record_and_send_audio, args=(ws, player_id), daemon=True).start()
    except Exception as e:
        print("Could not connect:", e)

floor = set()
def room(x1, y1, x2, y2):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            floor.add((x, y))

room(1, 1, 8, 6)
room(11, 1, 18, 6)
room(21, 1, 30, 6)
room(1, 12, 8, 18)
room(11, 12, 18, 18)
room(21, 12, 30, 18)

for x in range(1, 31):
    floor.add((x, 9))
    floor.add((x, 10))
for y in (6, 7, 8, 11, 12):
    for x in (4, 14, 25):
        floor.add((x, y))
for x in range(8, 12):
    floor.update(((x, 4), (x, 14)))
for x in range(18, 22):
    floor.update(((x, 4), (x, 14)))

task_spots = [(6, 3), (15, 3), (26, 4), (5, 15), (15, 15), (26, 15)]

def start_game():
    global screen, tasks, message, task_game, meeting_active, player_id
    screen = "game"
    message = ""
    task_game = None
    meeting_active = False
    player_id = username.strip() if username.strip() else "Player"
    player["x"], player["y"] = 4, 4
    player["color"] = COLORS[color_index][1]
    player["name"] = player_id
    tasks = set(task_spots)
    connect_ws()

def send_state():
    if ws and ws.sock and ws.sock.connected:
        state = {
            "id": player_id,
            "x": player["x"],
            "y": player["y"],
            "color": player["color"],
            "role": role,
            "name": player["name"]
        }
        try:
            ws.send(json.dumps(state))
        except:
            pass

def click_handler(event):
    global task_game, meeting_active, votes, voted
    mx, my = event.x, event.y

    if screen == "game":
        if role == "Impostor" and not meeting_active and not typing_chat:
            x1, y1, x2, y2 = kill_btn
            if x1 <= mx <= x2 and y1 <= my <= y2:
                for pid, pdata in other_players.items():
                    if abs(player["x"] - pdata["x"]) + abs(player["y"] - pdata["y"]) <= 1:
                        new_body = {"x": pdata["x"], "y": pdata["y"], "color": pdata["color"], "name": pid}
                        bodies.append(new_body)
                        if ws and ws.sock and ws.sock.connected:
                            ws.send(json.dumps({"action": "kill", "target": pid, "body": new_body}))
                        break
                return
        if not meeting_active and not typing_chat:
            x1, y1, x2, y2 = report_btn
            if x1 <= mx <= x2 and y1 <= my <= y2:
                for b in bodies:
                    if abs(player["x"] - b["x"]) + abs(player["y"] - b["y"]) <= 3:
                        meeting_active = True
                        votes = {}
                        voted = False
                        if ws and ws.sock and ws.sock.connected:
                            ws.send(json.dumps({"action": "report", "body": b}))
                        break
                return

    if meeting_active and not voted:
        all_p = list(other_players.values()) + [{"name": player["name"], "id": player_id}]
        for idx, pdata in enumerate(all_p[:6]):
            vy = 140 + idx * 40
            if 200 <= mx <= WIDTH - 200 and vy <= my <= vy + 30:
                target_name = pdata.get("name", "Player")
                votes[player_id] = target_name
                voted = True
                if ws and ws.sock and ws.sock.connected:
                    ws.send(json.dumps({"action": "vote", "voter": player_id, "target": target_name}))
                break

    if task_game:
        for i, col in enumerate(task_game["left"]):
            wy = 160 + i * 50
            if 220 <= mx <= 244 and wy - 12 <= my <= wy + 12:
                task_game["selected"] = i
                return
        if task_game["selected"] is not None:
            left_idx = task_game["selected"]
            left_color = task_game["left"][left_idx]
            for j, col in enumerate(task_game["right"]):
                wy = 160 + j * 50
                if 550 <= mx <= 574 and wy - 12 <= my <= wy + 12:
                    if col == left_color:
                        task_game["connected"][left_idx] = j
                        task_game["selected"] = None
                        if len(task_game["connected"]) == 4:
                            tasks.remove(task_game["pos"])
                            task_game = None
                    break

root.bind("<Button-1>", click_handler)

def key_down(event):
    global screen, color_index, username, typing_chat, chat_input_text, task_game, voice_enabled
    k = event.keysym

    if screen == "menu":
        if k == "Return":
            start_game()
        elif k == "c" or k == "C":
            color_index = (color_index + 1) % len(COLORS)
        elif k == "BackSpace":
            username = username[:-1]
        elif len(k) == 1 and len(username) < 12:
            username += k
        return

    if typing_chat:
        if k == "Return":
            if chat_input_text.strip() and ws and ws.sock and ws.sock.connected:
                chat_payload = {"action": "chat", "sender": player["name"], "text": chat_input_text.strip()}
                ws.send(json.dumps(chat_payload))
            chat_input_text = ""
            typing_chat = False
        elif k == "BackSpace":
            chat_input_text = chat_input_text[:-1]
        elif k == "space" or k == "Space":
            if len(chat_input_text) < 40:
                chat_input_text += " "
        elif len(k) == 1 and len(chat_input_text) < 40:
            chat_input_text += k
        return

    k_lower = k.lower()
    keys.add(k_lower)

    if k_lower == "t":
        typing_chat = True
    elif k_lower == "m":
        voice_enabled = not voice_enabled
    elif k_lower == "escape":
        screen = "menu"
        task_game = None
    elif screen == "game" and not meeting_active:
        if k_lower == "e" and role == "Crewmate":
            if task_game:
                task_game = None
            else:
                for task in list(tasks):
                    if abs(player["x"] - task[0]) + abs(player["y"] - task[1]) <= 1:
                        left_colors = ["#ed4545", "#22a9e8", "#f2c94c", "#b46bea"]
                        right_colors = left_colors.copy()
                        random.shuffle(right_colors)
                        task_game = {"pos": task, "left": left_colors, "right": right_colors, "selected": None, "connected": {}}
                        break
        elif k_lower == "space" and role == "Impostor":
            for pid, pdata in other_players.items():
                if abs(player["x"] - pdata["x"]) + abs(player["y"] - pdata["y"]) <= 1:
                    new_body = {"x": pdata["x"], "y": pdata["y"], "color": pdata["color"], "name": pid}
                    bodies.append(new_body)
                    if ws and ws.sock and ws.sock.connected:
                        ws.send(json.dumps({"action": "kill", "target": pid, "body": new_body}))
                    break
        elif k_lower == "r":
            for b in bodies:
                if abs(player["x"] - b["x"]) + abs(player["y"] - b["y"]) <= 3:
                    global meeting_active, votes, voted
                    meeting_active = True
                    votes = {}
                    voted = False
                    if ws and ws.sock and ws.sock.connected:
                        ws.send(json.dumps({"action": "report", "body": b}))
                    break

def key_up(event):
    keys.discard(event.keysym.lower())

root.bind("<KeyPress>", key_down)
root.bind("<KeyRelease>", key_up)

def try_move(actor, dx, dy):
    nx, ny = actor["x"] + dx, actor["y"] + dy
    if (nx, ny) in floor:
        actor["x"], actor["y"] = nx, ny

def draw_crew(x, y, color, label=None):
    cx, cy = x * TILE + TILE // 2, y * TILE + TILE // 2
    r = 10
    canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=color, outline="white")
    canvas.create_oval(cx+1, cy-r+3, cx+r+5, cy-1, fill="#a9e8f5", outline="white")
    if label:
        canvas.create_text(cx, cy+16, text=label, fill="white", font=("Arial", 7, "bold"))

def draw_map():
    canvas.delete("all")
    px, py = player["x"], player["y"]

    for y in range(ROWS):
        for x in range(COLS):
            dist = math.hypot(x - px, y - py)
            if dist > VISION:
                canvas.create_rectangle(x*TILE, y*TILE, (x+1)*TILE, (y+1)*TILE, fill="#080d14", outline="")
            elif (x, y) in floor:
                canvas.create_rectangle(x*TILE, y*TILE, (x+1)*TILE, (y+1)*TILE, fill="#283e54", outline="#35506c")
            else:
                canvas.create_rectangle(x*TILE, y*TILE, (x+1)*TILE, (y+1)*TILE, fill="#141f2e", outline="#1c2b3d")

    for tx, ty in tasks:
        if math.hypot(tx - px, ty - py) <= VISION:
            cx, cy = tx * TILE + TILE // 2, ty * TILE + TILE // 2
            canvas.create_oval(cx-6, cy-6, cx+6, cy+6, fill="#ffd84d", outline="white")

    for b in bodies:
        if math.hypot(b["x"] - px, b["y"] - py) <= VISION:
            cx, cy = b["x"] * TILE + TILE // 2, b["y"] * TILE + TILE // 2
            canvas.create_oval(cx-10, cy-5, cx+10, cy+5, fill=b["color"], outline="red", width=2)
            canvas.create_text(cx, cy+14, text="DEAD", fill="red", font=("Arial", 7, "bold"))

    for pid, pdata in other_players.items():
        if math.hypot(pdata["x"] - px, pdata["y"] - py) <= VISION:
            draw_crew(pdata["x"], pdata["y"], pdata["color"], pdata.get("name", pid))

    draw_crew(px, py, player["color"], player["name"])

def draw_meeting():
    canvas.create_rectangle(150, 60, WIDTH-150, HEIGHT-60, fill="#182738", outline="white", width=2)
    canvas.create_text(WIDTH//2, 90, text="EMERGENCY MEETING - CLICK TO VOTE", fill="white", font=("Arial", 14, "bold"))
    
    all_p = list(other_players.values()) + [{"name": player["name"]}]
    for idx, pdata in enumerate(all_p[:6]):
        vy = 140 + idx * 40
        name = pdata.get("name", "Player")
        is_voted_status = " (VOTED)" if name in votes.values() else ""
        canvas.create_rectangle(200, vy, WIDTH-200, vy+30, fill="#243b52", outline="white")
        canvas.create_text(WIDTH//2, vy+15, text=f"Vote: {name}{is_voted_status}", fill="white", font=("Arial", 11, "bold"))

def update():
    global screen

    if screen == "menu":
        canvas.delete("all")
        canvas.create_text(WIDTH//2, 80, text="SHIPMATES (ONLINE + VOICE)", fill="white", font=("Arial", 32, "bold"))
        canvas.create_text(WIDTH//2, 150, text=f"Username: {username}  (Type to change)", fill="#ffd84d", font=("Arial", 16, "bold"))
        canvas.create_text(WIDTH//2, 210, text=f"Color: {COLORS[color_index][0]}  (Press C to change)", fill=COLORS[color_index][1], font=("Arial", 15, "bold"))
        canvas.create_text(WIDTH//2, 290, text="Press ENTER to start playing", fill="white", font=("Arial", 18, "bold"))
        canvas.create_text(WIDTH//2, 340, text="🎙️ Global Voice Chat Ready (Press M to Mute/Unmute)", fill="#5bd18a", font=("Arial", 11))
    else:
        if not message and not task_game and not meeting_active:
            dx = int("d" in keys or "right" in keys) - int("a" in keys or "left" in keys)
            dy = int("s" in keys or "down" in keys) - int("w" in keys or "up" in keys)
            if dx: try_move(player, dx, 0)
            if dy: try_move(player, 0, dy)
            send_state()

        draw_map()

        if task_game:
            canvas.create_rectangle(200, 80, 600, 380, fill="#182738", outline="white", width=2)
            canvas.create_text(400, 110, text="FIX WIRES: Click matching color dots", fill="white", font=("Arial", 13, "bold"))
            for i, col in enumerate(task_game["left"]):
                wy = 160 + i * 50
                sel = task_game["selected"] == i
                canvas.create_oval(220, wy-12, 244, wy+12, fill=col, outline="yellow" if sel else "white", width=2)
            for j, col in enumerate(task_game["right"]):
                wy = 160 + j * 50
                canvas.create_oval(550, wy-12, 574, wy+12, fill=col, outline="white", width=2)

        if meeting_active:
            draw_meeting()

        canvas.create_rectangle(0, HEIGHT-80, WIDTH, HEIGHT, fill="#0b121e", outline="")
        voice_status = "ON (Press M)" if voice_enabled else "MUTED"
        status_txt = f"Role: {role} | Tasks: {len(tasks)} | 🎙️ Voice: {voice_status}"
        canvas.create_text(12, HEIGHT-65, anchor="w", text=status_txt, fill="white", font=("Arial", 10, "bold"))

        chat_y = HEIGHT-50
        for msg in chat_messages[-3:]:
            canvas.create_text(12, chat_y, anchor="w", text=msg, fill="#a9e8f5", font=("Arial", 9))
            chat_y += 15

        typing_prompt = f"Chat (Press T to type): {chat_input_text}_" if typing_chat else "Press T to chat"
        canvas.create_text(12, HEIGHT-12, anchor="w", text=typing_prompt, fill="#ffd84d" if typing_chat else "#88a0b8", font=("Arial", 9))

        canvas.create_rectangle(report_btn[0], report_btn[1], report_btn[2], report_btn[3], fill="#f2c94c", outline="white")
        canvas.create_text((report_btn[0]+report_btn[2])//2, (report_btn[1]+report_btn[3])//2, text="REPORT (R)", fill="black", font=("Arial", 9, "bold"))

        if role == "Impostor":
            canvas.create_rectangle(kill_btn[0], kill_btn[1], kill_btn[2], kill_btn[3], fill="#ed4545", outline="white")
            canvas.create_text((kill_btn[0]+kill_btn[2])//2, (kill_btn[1]+kill_btn[3])//2, text="KILL (SPACE)", fill="white", font=("Arial", 9, "bold"))

    root.after(100, update)

update()
root.mainloop()
