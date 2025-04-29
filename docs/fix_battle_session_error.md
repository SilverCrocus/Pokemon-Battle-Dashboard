# Plan to Fix "Battle session not found" Error

**Problem:**

After both players submit their teams, they are sometimes redirected incorrectly or lose their session association, resulting in a "Battle session not found." error when trying to perform actions on the battle page (`/battle`).

Logs indicate that the server correctly creates the battle session after team submission, but subsequent requests (e.g., accessing `/team_setup` again without a `session_id`, or connecting to the `/battle` page) fail because the server cannot map the new client connection (or incorrect request) back to the existing session and specific player (`player1` or `player2`).

**Root Cause:**

The server currently lacks a mechanism to re-associate a player's Socket.IO SID when they connect to the `/battle` page after being redirected from `/team_setup`. The `request.sid` changes upon page navigation/reconnection, and the server doesn't know which player (`player1` or `player2`) this new SID belongs to within the battle session.

**Solution:**

1.  **Modify `handle_submit_team` (`app.py`):**
    *   Instead of emitting `teams_ready_start_battle` to the entire session room, emit it *individually* to each player's specific SID (`player1_sid`, `player2_sid`).
    *   Include the corresponding `player_id` (`'player1'` or `'player2'`) in the data payload of this event.
    *   **(Status: Code generated, needs manual application due to file sync issue)**

2.  **Modify `team_setup.js`:**
    *   Update the event listener for `teams_ready_start_battle`.
    *   Extract the received `player_id` from the event data.
    *   Modify the redirection logic (`window.location.href = ...`) to include *both* the `session_id` and the `player_id` as URL query parameters (e.g., `/battle?session_id=...&player_id=...`).

3.  **Modify `battle.js`:**
    *   On page load (`DOMContentLoaded`), extract both `session_id` and `player_id` from the URL query parameters (`new URLSearchParams(window.location.search)`).
    *   Modify the `socket.emit('join_battle', ...)` call to send *both* the `session_id` and the `player_id` to the server.

4.  **Add `handle_join_battle` (`app.py`):**
    *   Create a new SocketIO event handler: `@socketio.on('join_battle')`.
    *   This handler should receive `session_id` and `player_id` from the client's event data.
    *   Find the correct `session_data` using `session_id`.
    *   Update the stored SID for the specific player: `session_data['players'][player_id] = request.sid`.
    *   Have the new connection join the `session_id` room using `join_room(session_id)`.
    *   Retrieve the current battle state for that specific player using `battle.get_state_for_player(player_id)`.
    *   Emit an initial `battle_update` event *only* to the connecting player (`request.sid`) with their specific state.

This ensures that when players arrive on the battle page, the server correctly updates their SID in the session data, allowing subsequent `player_action` events to be processed correctly.
