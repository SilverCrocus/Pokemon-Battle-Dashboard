from flask import Flask, render_template, jsonify, request
from pokemon_service import PokemonService
import logging
import uuid
from flask import redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from battle_logic import Battle # Import the Battle class

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_secret_key_for_socketio' # Needed for SocketIO
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*") # Removed async_mode='gevent'
pokemon_service = PokemonService()
# Temporary storage for battle sessions and teams
battle_sessions = {}

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/new_battle')
def new_battle():
    """Generate a new battle session and redirect to the battle lobby."""
    session_id = str(uuid.uuid4()) # Generate a unique session ID
    logger.info(f"Created new battle session: {session_id}")
    # Initialize session data
    battle_sessions[session_id] = {'teams': {}, 'players': {}, 'ready': {}, 'state': 'lobby'}
    return redirect(url_for('battle_lobby_page', session_id=session_id))

@app.route('/battle_lobby')
def battle_lobby_page():
    """Render the battle lobby page."""
    session_id = request.args.get('session_id')
    if not session_id or session_id not in battle_sessions:
        return "Battle session not found.", 404 # TODO: Render an error template
    logger.info(f"Rendering battle lobby page for session {session_id}.")
    return render_template('battle_lobby.html', session_id=session_id)

@app.route('/api/battle')
def generate_battle():
    """API endpoint to generate a new battle."""
    battle_data = pokemon_service.generate_battle()
    return jsonify(battle_data)

@app.route('/api/pokemon/<int:pokemon_id>')
def get_pokemon(pokemon_id):
    """API endpoint to get a specific Pokemon."""
    pokemon = pokemon_service.get_pokemon_data(pokemon_id)
    if pokemon:
        return jsonify(pokemon)
    return jsonify({"error": "Pokemon not found"}), 404

@app.route('/api/pokemon_list')
def get_pokemon_list():
    """API endpoint to get the list of all Pokemon names."""
    names = pokemon_service.get_all_pokemon_names()
    logger.info(f"Returning {len(names)} Pokemon names.")
    return jsonify(names)

@app.route('/api/pokemon_details')
def get_pokemon_details_by_name():
    """API endpoint to get details for a specific Pokemon by name."""
    pokemon_name = request.args.get('name')
    if not pokemon_name:
        logger.warning("Missing 'name' parameter for /api/pokemon_details")
        return jsonify({"error": "Missing 'name' query parameter"}), 400

    logger.info(f"Fetching details for Pokemon: {pokemon_name}")
    pokemon_data = pokemon_service.get_pokemon_data_by_name(pokemon_name)

    if pokemon_data:
        return jsonify(pokemon_data)
    else:
        logger.warning(f"Pokemon details not found for: {pokemon_name}")
        return jsonify({"error": f"Pokemon '{pokemon_name}' not found"}), 404

@app.route('/team_setup')
def team_setup_page():
    """Render the team setup page."""
    session_id = request.args.get('session_id')
    logger.info(f"Team setup page accessed. Session ID from request: {session_id}")
    logger.info(f"Current battle_sessions keys: {battle_sessions.keys()}")
    if not session_id or session_id not in battle_sessions:
        logger.error(f"Session check failed: session_id='{session_id}' (type: {type(session_id)}), battle_sessions keys: {battle_sessions.keys()} (type: {type(battle_sessions)})")
        return "Battle session not found.", 404 # TODO: Render an error template
    logger.info(f"Rendering team setup page for session {session_id}.")
    return render_template('team_setup.html', session_id=session_id)

@app.route('/manual_setup')
def manual_setup():
    """Render the manual team setup page."""
    logger.info("Rendering manual setup page.")
    return render_template('manual_setup.html')


@app.route('/battle')
def battle_page():
    """Render the battle page."""
    session_id = request.args.get('session_id')
    if not session_id or session_id not in battle_sessions or len(battle_sessions[session_id].get('teams', {})) < 2:
        # Redirect or show error if session is invalid or not ready
        return "Battle session not found or not ready.", 404 # TODO: Render an error template
    logger.info(f"Rendering battle page for session {session_id}.")
    return render_template('battle.html', session_id=session_id)

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client {request.sid} disconnected')
    # Find which session and player disconnected
    disconnected_session_id = None
    disconnected_player_id = None
    # Ensure battle_sessions is a dictionary before iterating
    if isinstance(battle_sessions, dict):
        for session_id, session_data in list(battle_sessions.items()): # Use list to allow modification during iteration
            # Ensure players is a dictionary before iterating
            if isinstance(session_data.get('players'), dict):
                for player_id, sid in session_data['players'].items():
                    if sid == request.sid:
                        disconnected_session_id = session_id
                        disconnected_player_id = player_id
                        break
            if disconnected_session_id:
                break

    if disconnected_session_id and disconnected_player_id:
        logger.info(f"Player {disconnected_player_id} ({request.sid}) disconnected from session {disconnected_session_id}")
        # Remove player from session
        # Check if the player_id exists before attempting to delete
        if disconnected_player_id in battle_sessions[disconnected_session_id].get('players', {}):
             del battle_sessions[disconnected_session_id]['players'][disconnected_player_id]

        # Notify the other player (if any)
        remaining_player_sid = None
        # Ensure players is a dictionary before iterating
        if isinstance(battle_sessions[disconnected_session_id].get('players'), dict):
            for p_id, sid in battle_sessions[disconnected_session_id]['players'].items():
                if sid != request.sid:
                    remaining_player_sid = sid
                    break

        if remaining_player_sid:
            emit('battle_message', {'message': 'Opponent disconnected. Battle ended.'}, room=remaining_player_sid)
            emit('battle_end', {'message': 'Opponent disconnected. Battle ended.'}, room=remaining_player_sid)

        # Clean up session if no players remain
        session_state = battle_sessions[disconnected_session_id].get('state', 'lobby') # Default to lobby if state is missing
        remaining_players_count = len(battle_sessions[disconnected_session_id].get('players', {}))

        if session_state == 'lobby':
            # In lobby state, if any player disconnects, the lobby is invalid
            logger.info(f"Player {disconnected_player_id} disconnected from lobby session {disconnected_session_id}. Cleaning up session.")
            del battle_sessions[disconnected_session_id]
        elif session_state == 'team_setup':
             # In team_setup state, do not clean up the session based on player count
             logger.info(f"Player {disconnected_player_id} disconnected from session {disconnected_session_id} (state: {session_state}). Session persists for team setup.")
        else:
            # For any other future states, add specific cleanup logic here if needed
            logger.info(f"Player {disconnected_player_id} disconnected from session {disconnected_session_id} (state: {session_state}). No specific cleanup rule for this state yet.")


@socketio.on('join_lobby')
def handle_join_lobby(data):
    """Socket.IO event for clients joining the battle lobby page."""
    session_id = data.get('session_id')
    if not session_id or session_id not in battle_sessions:
        logger.error(f"Attempted to join non-existent session: {session_id}")
        emit('error_message', {'message': 'Battle session not found.'})
        return

    join_room(session_id)
    logger.info(f"Client {request.sid} joined room {session_id}")

    session_data = battle_sessions[session_id]

    # Assign player_id if not already assigned
    player_id = None
    for p_id, sid in session_data.get('players', {}).items():
        if sid == request.sid:
            player_id = p_id
            break

    if not player_id:
        if 'player1' not in session_data.get('players', {}):
            player_id = 'player1'
            session_data.setdefault('players', {})[player_id] = request.sid
            logger.info(f"Assigned {request.sid} as player1 in session {session_id}")
        elif 'player2' not in session_data.get('players', {}):
            player_id = 'player2'
            session_data.setdefault('players', {})[player_id] = request.sid
            logger.info(f"Assigned {request.sid} as player2 in session {session_id}")
        else:
            logger.warning(f"Session {session_id} is full. Client {request.sid} cannot join.")
            emit('error_message', {'message': 'Battle lobby is full.'})
            return

    # Initialize ready state for the player
    session_data.setdefault('ready', {})[player_id] = False

    # Emit updated lobby state to the room
    ready_count = sum(session_data.get('ready', {}).values())
    emit('lobby_state_update', {'ready_players': ready_count}, room=session_id)


@socketio.on('player_ready')
def handle_player_ready(data):
    """Socket.IO event for players signaling readiness in the lobby."""
    session_id = data.get('session_id')
    if not session_id or session_id not in battle_sessions:
        logger.error(f"Ready signal for non-existent session: {session_id}")
        emit('error_message', {'message': 'Battle session not found.'})
        return

    session_data = battle_sessions[session_id]

    # Find player_id based on request.sid
    player_id = None
    for p_id, sid in session_data.get('players', {}).items():
        if sid == request.sid:
            player_id = p_id
            break

    if not player_id:
        logger.warning(f"Client {request.sid} not found in players list for session {session_id} on ready signal.")
        emit('error_message', {'message': 'You are not part of this battle session.'})
        return

    session_data.setdefault('ready', {})[player_id] = True
    logger.info(f"Player {player_id} ({request.sid}) is ready in session {session_id}")

    # Emit updated lobby state to the room
    ready_count = sum(session_data.get('ready', {}).values())
    emit('lobby_state_update', {'ready_players': ready_count}, room=session_id)

    # Check if both players are ready
    if len(session_data.get('ready', {})) == 2 and all(session_data['ready'].values()):
        logger.info(f"Both players ready in session {session_id}. Emitting battle_start.")
        emit('battle_start', {'session_id': session_id}, room=session_id)
        session_data['state'] = 'team_setup'

@socketio.on('join_team_setup')
def handle_join_team_setup(data):
    """Socket.IO event for clients joining the team setup page."""
    session_id = data.get('session_id')
    if not session_id or session_id not in battle_sessions:
        logger.error(f"Attempted to join non-existent session for team setup: {session_id}")
        emit('error_message', {'message': 'Battle session not found.'})
        return

    join_room(session_id)
    logger.info(f"Client {request.sid} joined team setup room {session_id}")

    # Optionally, send initial state data to the client if needed for the team setup page
    # For example, send the list of available Pokemon names or details if not fetched via HTTP
    # emit('initial_team_setup_data', {'pokemon_names': pokemon_service.get_all_pokemon_names()}, room=request.sid)


@socketio.on('submit_team')
def handle_submit_team(data):
    """Socket.IO event to receive and store a player's team."""
    session_id = data.get('session_id')
    team = data.get('team')

    if not session_id or not team or len(team) != 6:
        logger.warning(f"Invalid team submission via Socket.IO: session_id={session_id}, team={team}")
        emit('error_message', {'message': 'Invalid session ID or team data.'})
        return

    if session_id not in battle_sessions:
        logger.warning(f"Team submitted via Socket.IO for non-existent session: {session_id}")
        emit('error_message', {'message': 'Battle session not found.'})
        return

    session_data = battle_sessions[session_id]

    # Find player_id based on request.sid (available in Socket.IO context)
    player_id = None
    for p_id, sid in session_data.get('players', {}).items():
        if sid == request.sid:
            player_id = p_id
            break

    if not player_id:
        logger.warning(f"Client {request.sid} not found in players list for session {session_id} on team submission via Socket.IO.")
        emit('error_message', {'message': 'You are not part of this battle session.'})
        return

    # Check if this player has already submitted a team
    if player_id in session_data.get('teams', {}):
        logger.warning(f"Player {player_id} ({request.sid}) already submitted a team for session {session_id} via Socket.IO.")
        emit('error_message', {'message': 'You have already submitted a team for this session.'})
        return

    # Store team associated with player_id
    session_data.setdefault('teams', {})[player_id] = team

    logger.info(f"Team submitted by {player_id} for session {session_id} via Socket.IO. Total teams submitted: {len(session_data.get('teams', {}))}")

    # Check if both teams are submitted
    if len(session_data.get('teams', {})) == 2:
        logger.info(f"Both teams submitted for session {session_id}. Creating battle...")
        # Ensure we have teams for both player1 and player2
        if 'player1' in session_data.get('teams', {}) and 'player2' in session_data.get('teams', {}):
            team1_data = session_data['teams']['player1']
            team2_data = session_data['teams']['player2']
            battle = Battle(session_id, team1_data, team2_data)
            session_data['battle'] = battle # Store the battle instance
            logger.info(f"Battle object created for session {session_id}.")

            # Notify clients via WebSocket to proceed to battle page
            logger.info(f"Emitting 'teams_ready_start_battle' to room {session_id}")
            socketio.emit('teams_ready_start_battle', {'session_id': session_id}, room=session_id)

            # Respond to the client that submitted the team
            emit('team_submission_success', {'message': 'Team submitted. Both teams ready. Starting battle!'})
        else:
            logger.error(f"Team data missing for player1 or player2 in session {session_id} after both teams submitted check via Socket.IO.")
            # This indicates a logic error in team assignment or storage
            emit('error_message', {'message': 'Internal server error processing teams.'})
    else:
        # Only one team submitted so far
        emit('team_submission_success', {'message': 'Team submitted. Waiting for opponent.'})

if __name__ == '__main__':
    # Consider adding host='0.0.0.0' if running in a container or need external access
    socketio.run(app, debug=True, use_reloader=False)
