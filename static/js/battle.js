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
        return;
    }

    sessionIdSpan.textContent = sessionId;

    const socket = io(); // Connect to the default namespace

    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
        socket.emit('join_battle', { session_id: sessionId });
    });

    socket.on('battle_state_update', (data) => {
        console.log('Battle state update received:', data);
        // Update UI based on battle state
        updateBattleUI(data);
    });

    socket.on('battle_log_message', (data) => {
        console.log('Battle log message received:', data);
        addLogEntry(data.message);
    });

    socket.on('move_options', (data) => {
        console.log('Move options received:', data);
        displayMoveOptions(data.moves);
    });

    socket.on('battle_over', (data) => {
        console.log('Battle over:', data);
        addLogEntry(data.message);
        // Disable move options or redirect
        moveOptionsDiv.innerHTML = ''; // Clear move options
    });

    function updateBattleUI(state) {
        // Update opponent's Pokemon sprite and health
        if (state.opponent_pokemon) {
            opponentSpriteDiv.innerHTML = `<img src="/static/sprites/${state.opponent_pokemon.name.toLowerCase()}.png" alt="${state.opponent_pokemon.name}">`;
            opponentHpSpan.textContent = `${state.opponent_pokemon.current_hp}/${state.opponent_pokemon.max_hp}`;
        } else {
            opponentSpriteDiv.innerHTML = '';
            opponentHpSpan.textContent = 'N/A';
        }

        // Update player's Pokemon sprite and health
        if (state.player_pokemon) {
            playerSpriteDiv.innerHTML = `<img src="/static/sprites/${state.player_pokemon.name.toLowerCase()}.png" alt="${state.player_pokemon.name}">`;
            playerHpSpan.textContent = `${state.player_pokemon.current_hp}/${state.player_pokemon.max_hp}`;
        } else {
            playerSpriteDiv.innerHTML = '';
            playerHpSpan.textContent = 'N/A';
        }

        // Display move options if available
        if (state.player_pokemon && state.player_pokemon.moves) {
             displayMoveOptions(state.player_pokemon.moves);
        } else {
            moveOptionsDiv.innerHTML = ''; // Clear move options if no player pokemon or moves
        }
    }

    function displayMoveOptions(moves) {
        moveOptionsDiv.innerHTML = ''; // Clear previous options
        moves.forEach(move => {
            const moveButton = document.createElement('button');
            moveButton.textContent = move.name;
            moveButton.addEventListener('click', () => {
                socket.emit('select_move', { session_id: sessionId, move_name: move.name });
                moveOptionsDiv.innerHTML = 'Waiting for opponent...'; // Disable buttons after selection
            });
            moveOptionsDiv.appendChild(moveButton);
        });
    }

    function addLogEntry(message) {
        const li = document.createElement('li');
        li.textContent = message;
        logEntriesUl.appendChild(li);
        logEntriesUl.scrollTop = logEntriesUl.scrollHeight; // Auto-scroll to latest entry
    }
});