🚀 Shipmates
An online multiplayer social deduction game built in Python using Tkinter and WebSockets, connecting players live across the globe!

🎮 How to Play
1. Download the Game: Download the shipmates.py file directly from this repository.
2. Install Dependencies: Open your terminal or command prompt and run:
   pip install websocket-client
   (If pip gives an error, try python -m pip install websocket-client)
3. Launch the Game: Run the script using Python:
   python shipmates.py
4. Join the Lobby: Type your username, press C to cycle through avatar colors, hit Enter, and dive straight into the game online!

🕹️ Controls
- Movement: WASD or Arrow Keys
- Live Chat: Press T to start typing, hit Enter to send
- Fix Tasks: Press E near yellow task spots (Crewmates)
- Impostor Kill: Press Spacebar (or click the KILL button)
- Report Dead Body: Press R (or click the REPORT button near a body)
- Cancel / Menu: Escape

📢 Patch Notes & Changelog

🚀 Update 1.2 — Server & Stability Overhaul
- Ghost Player Fix: Fixed a major bug where disconnected players lingered on the map as "ghosts".
- Username-Based Player IDs: Replaced randomized temporary IDs with unique username session tracking. Logging back in after a drop now instantly restores your slot without duplicating your avatar.
- Crash Prevention: Resolved an issue where reporting a dead body with out-of-sync player states caused game client crashes.
- Streamlined UI: Safely capped voting screen player lists to prevent canvas rendering overflows.

🌟 Update 1.1 — Social & Quality of Life
- In-Game Text Chat: Added live chat box at the bottom of the canvas—press T anytime to talk with crewmates.
- Custom Usernames: Enabled custom username selection directly from the main menu.
- Dynamic Role System: Implemented server-side role assignment for Crewmates and Impostors.
- Live Cloud Deployment: Connected client directly to the Render WebSocket server (wss://crewserver.onrender.com/ws).

🛠️ Update 1.0 — Initial Release
- Basic movement, map collision detection, and fog-of-war vision.
- Interactive wire repair task minigame.
- Impostor kill and body report mechanics.
