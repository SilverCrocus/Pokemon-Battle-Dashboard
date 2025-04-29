document.addEventListener('DOMContentLoaded', () => {
    const sessionIdSpan = document.getElementById('session-id');
    const opponentSpriteDiv = document.getElementById('opponent-sprite');
    const opponentHpSpan = document.getElementById('opponent-hp');
    const playerSpriteDiv = document.getElementById('player-sprite');
    const playerHpSpan = document.getElementById('player-hp');
    const moveOptionsDiv = document.getElementById('move-options');
    const logEntriesUl = document.getElementById('log-entries');

    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');

    if (!sessionId) {
        sessionIdSpan.textContent = 'No session ID provided.';
        addLogEntry('Error: Could not find session_id in URL.');
        return;
    }

    sessionIdSpan.textContent = sessionId;

    const socket = io(); // Connect to the default namespace

    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
        // Maybe join a room specific to the battle page/session?
        // Example: socket.emit('join_battle_room', { session_id: sessionId });
        // This depends on server setup; for now, default namespace might be fine
        // if server handles session_id correctly.
         addLogEntry('Connected to battle server.');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket server');
        addLogEntry('Disconnected from battle server.');
        // Optionally disable UI elements
    });

    socket.on('error_message', (data) => {
        console.error('Server error:', data.message);
        addLogEntry(`Error: ${data.message}`);
    });

     socket.on('action_error', (data) => {
        console.warn('Action error:', data.message);
        addLogEntry(`Action Failed: ${data.message}`);
        // Re-enable move options if needed, depends on game flow
        // Example: if (state.player_pokemon && state.player_pokemon.moves) displayMoveOptions(state.player_pokemon.moves);
    });

    // Listen for the corrected event name
    socket.on('battle_update', (data) => {
        console.log('Battle state update received:', data);
        updateBattleUI(data); // Update UI with the new state
        // Clear "Waiting for opponent..." message if player needs to act again
        if (data.prompt_action) { // Assuming the state indicates if the player needs to act
             if (data.player_pokemon && data.player_pokemon.moves) {
                 displayMoveOptions(data.player_pokemon.moves);
             }
             // Add logic here for displaying switch options if applicable
        }
    });

    socket.on('game_over', (data) => {
        console.log('Game over:', data);
        addLogEntry(`Game Over! Winner: ${data.winner}, Loser: ${data.loser}`);
        moveOptionsDiv.innerHTML = '<h2>Game Over</h2>'; // Clear move options and show game over
    });

    // We don't expect 'battle_log_message' or 'move_options' as separate events
    // based on the app.py logic, which sends the full state via 'battle_update'.
    // Removing listeners for them to avoid confusion.

    function updateBattleUI(state) {
        console.log("Updating UI with state:", state);
        // Update opponent's Pokemon
        if (state.opponent_active_pokemon) {
            opponentSpriteDiv.innerHTML = `<img src="/static/sprites/${state.opponent_active_pokemon.name.toLowerCase()}.png" alt="${state.opponent_active_pokemon.name}">`;
            opponentHpSpan.textContent = `${state.opponent_active_pokemon.current_hp} / ${state.opponent_active_pokemon.max_hp}`;
        } else {
            opponentSpriteDiv.innerHTML = 'Opponent: ---';
            opponentHpSpan.textContent = '---';
        }

        // Update player's Pokemon
        if (state.player_active_pokemon) {
            playerSpriteDiv.innerHTML = `<img src="/static/sprites/${state.player_active_pokemon.name.toLowerCase()}.png" alt="${state.player_active_pokemon.name}">`;
            playerHpSpan.textContent = `${state.player_active_pokemon.current_hp} / ${state.player_active_pokemon.max_hp}`;

            // Display move options ONLY if the player needs to make a choice
            if (state.prompt_action && state.player_active_pokemon.moves) {
                 displayMoveOptions(state.player_active_pokemon.moves);
                 // TODO: Add logic to display switch options from state.player_team
            } else if (!state.game_over) {
                 moveOptionsDiv.innerHTML = 'Waiting for opponent...';
            }
        } else {
            playerSpriteDiv.innerHTML = 'Player: ---';
            playerHpSpan.textContent = '---';
            moveOptionsDiv.innerHTML = ''; // Clear options if no active pokemon (e.g., fainted, needs switch)
            // TODO: Prompt for switch if needed based on state
        }

        // Update battle log
        if (state.log) {
            logEntriesUl.innerHTML = ''; // Clear previous log entries
            state.log.forEach(entry => addLogEntry(entry));
        }
    }

    function displayMoveOptions(moves) {
        moveOptionsDiv.innerHTML = '<h3>Select Move:</h3>'; // Add a header
        moves.forEach((move, index) => { // Use the index
            if (move) { // Ensure move data exists
                const moveButton = document.createElement('button');
                // Display PP if available: `${move.name} (${move.current_pp}/${move.max_pp})`
                moveButton.textContent = `${move.name} (${move.current_pp}/${move.pp})`; // Assuming state provides pp and current_pp
                moveButton.disabled = move.current_pp <= 0; // Disable if no PP

                moveButton.addEventListener('click', () => {
                    console.log(`Move button clicked: ${move.name}, Index: ${index}`);
                    // Emit the corrected event name and data structure
                    socket.emit('player_action', {
                        session_id: sessionId,
                        action_type: 'move',
                        details: { move_index: index } // Send the index
                    });
                    moveOptionsDiv.innerHTML = 'Waiting for opponent...'; // Indicate waiting
                });
                moveOptionsDiv.appendChild(moveButton);
            }
        });
        // TODO: Add Switch Button here
        // const switchButton = document.createElement('button');
        // switchButton.textContent = 'Switch Pokemon';
        // switchButton.addEventListener('click', () => { /* ... display switch options ... */ });
        // moveOptionsDiv.appendChild(switchButton);
    }

    function addLogEntry(message) {
        const li = document.createElement('li');
        li.textContent = message;
        logEntriesUl.appendChild(li);
        logEntriesUl.scrollTop = logEntriesUl.scrollHeight; // Auto-scroll
    }
});