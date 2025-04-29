document.addEventListener('DOMContentLoaded', () => {
    const readyButton = document.getElementById('ready-button');
    const lobbyStatus = document.getElementById('lobby-status');
    const battleLink = document.getElementById('battle-link');

    const socket = io();

    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');

    if (!sessionId) {
        lobbyStatus.textContent = 'Error: Invalid battle session ID.';
        readyButton.disabled = true;
        return;
    }

    // Display the shareable link
    battleLink.textContent = `${window.location.origin}/battle_lobby?session_id=${sessionId}`;

    socket.on('connect', () => {
        console.log('Connected to WebSocket');
        // Join the lobby room
        socket.emit('join_lobby', { session_id: sessionId });
    });

    socket.on('lobby_state_update', (data) => {
        console.log('Lobby state update received:', data);
        // Update lobby status based on the number of ready players
        if (data.ready_players === 1) {
            lobbyStatus.textContent = 'One player ready. Waiting for opponent...';
        } else if (data.ready_players === 2) {
            lobbyStatus.textContent = 'Both players ready. Starting battle...';
        } else {
             lobbyStatus.textContent = 'Waiting for players...';
        }
    });

    socket.on('battle_start', (data) => {
        console.log('Battle start signal received:', data);
        console.log('Redirecting to team setup...');
        console.log('Attempting redirect to:', `/team_setup?session_id=${sessionId}`);
        // Redirect to the team setup page
        window.location.href = `/team_setup?session_id=${sessionId}`;
    });

    socket.on('error_message', (data) => {
        console.error('Error from server:', data.message);
        lobbyStatus.textContent = `Error: ${data.message}`;
        readyButton.disabled = true;
    });


    readyButton.addEventListener('click', () => {
        // Emit 'ready' event to the server
        socket.emit('player_ready', { session_id: sessionId });
        readyButton.disabled = true; // Prevent multiple clicks
        lobbyStatus.textContent = 'Waiting for opponent...';
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket');
        lobbyStatus.textContent = 'Disconnected from battle lobby.';
        readyButton.disabled = true;
    });

    // Initial state
    lobbyStatus.textContent = 'Waiting for players...';
});