# --- START OF MODIFIED app.py (Conceptual Additions) ---
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room # Using join_room but not leave_room
from pokemon_service import PokemonService # Assuming this service helps manage battle logic
import logging
import uuid # For generating session IDs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key!' # Important for SocketIO
socketio = SocketIO(app) # Initialize SocketIO
pokemon_service = PokemonService()

# --- Session Management Data Structures ---
lobbies = {} # { session_id: {'players': [sid1, sid2], 'ready_count': 0, 'player_sids_in_order': [], 'player_ready_status': {sid: True/False}} }
pending_battle_setups = {} # { session_id: {'player1_team': None, 'player2_team': None, 'teams_submitted_count': 0, 'player_sids_map': {sid: 'player1'/'player2'}} }
active_battles = {} # { session_id: BattleGameInstance_or_dict }

# --- Helper ---
def get_player_role_by_sid(session_id, player_sid):
    if session_id in pending_battle_setups:
        return pending_battle_setups[session_id].get('player_sids_map', {}).get(player_sid)
    elif session_id in active_battles:
        battle_game = active_battles[session_id]
        if isinstance(battle_game, dict): # Placeholder check
            if battle_game.get('player1_data', {}).get('sid') == player_sid:
                return 'player1'
            if battle_game.get('player2_data', {}).get('sid') == player_sid:
                return 'player2'
        # Add more sophisticated role checking if BattleGameInstance is a class
    return None

# --- HTTP Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pokemon/<int:pokemon_id>')
def get_pokemon(pokemon_id):
    pokemon = pokemon_service.get_pokemon_data(pokemon_id)
    if pokemon:
        return jsonify(pokemon)
    return jsonify({"error": "Pokemon not found"}), 404

@app.route('/api/pokemon_list')
def get_pokemon_list():
    names = pokemon_service.get_all_pokemon_names()
    return jsonify(names)

@app.route('/api/pokemon_details')
def get_pokemon_details_by_name():
    pokemon_name = request.args.get('name')
    if not pokemon_name:
        return jsonify({"error": "Missing 'name' query parameter"}), 400
    pokemon_data = pokemon_service.get_pokemon_data_by_name(pokemon_name)
    if pokemon_data:
        return jsonify(pokemon_data)
    return jsonify({"error": f"Pokemon '{pokemon_name}' not found"}), 404

@app.route('/manual_setup')
def manual_setup():
    return render_template('manual_setup.html')

@app.route('/api/create_lobby', methods=['POST'])
def create_new_lobby():
    session_id = str(uuid.uuid4())
    lobbies[session_id] = {'players': [], 'ready_count': 0, 'player_sids_in_order': [], 'player_ready_status': {}}
    logger.info(f"Lobby created: {session_id}")
    return jsonify({'session_id': session_id})

@app.route('/battle_lobby')
def battle_lobby_page():
    # Check if session_id is provided as a query parameter
    session_id = request.args.get('session_id')
    
    # If no session_id provided, create a new one
    if not session_id:
        session_id = str(uuid.uuid4())
        # Initialize the lobby for this session
        lobbies[session_id] = {'players': [], 'ready_count': 0, 'player_sids_in_order': [], 'player_ready_status': {}}
        logger.info(f"Lobby created: {session_id}")
    
    return render_template('battle_lobby.html', session_id=session_id)

@app.route('/team_setup')
def team_setup_page():
    session_id = request.args.get('session_id')
    error_message = None

    if not session_id:
        error_message = 'Session ID missing.'
    elif session_id not in pending_battle_setups:
        logger.warning(f"Session {session_id} not in pending_battle_setups when accessing /team_setup. Checking lobbies...")
        # Try to re-initialize from lobby state if it was ready
        if session_id in lobbies:
            lobby = lobbies[session_id]
            # Ensure conditions for creating pending_battle_setups are met
            if lobby.get('ready_count') == 2 and \
               len(lobby.get('players', [])) == 2 and \
               len(lobby.get('player_sids_in_order', [])) == 2:
                
                logger.info(f"Re-initializing pending_battle_setup for session {session_id} from ready lobby state during /team_setup access.")
                pending_battle_setups[session_id] = {
                    'player1_team': None, 'player2_team': None, 'teams_submitted_count': 0,
                    'player_sids_map': {
                        lobby['player_sids_in_order'][0]: 'player1',
                        lobby['player_sids_in_order'][1]: 'player2'
                    }
                }
                logger.info(f"Re-initialized. Current pending_battle_setups: {list(pending_battle_setups.keys())}")
            else:
                logger.warning(f"Session {session_id} in lobbies, but lobby not in state to auto-transition to team setup. "
                               f"RC:{lobby.get('ready_count')}, Players:{len(lobby.get('players',[]))}, SIDs_Order:{len(lobby.get('player_sids_in_order',[]))}")
                error_message = 'Invalid session: Lobby not fully ready or player(s) might have left.'
        else:
            logger.warning(f"Session {session_id} not in pending_battle_setups AND not in lobbies for /team_setup.")
            error_message = 'Invalid session for team setup (session does not exist).'
    
    if error_message:
        logger.error(f"Error rendering team_setup for {session_id}: {error_message}. Available pending: {list(pending_battle_setups.keys())}")
        return render_template('team_setup.html', session_id=session_id, error_message=error_message)
    
    logger.info(f"Successfully rendering team_setup_page for session {session_id}. Player SID: {request.sid if hasattr(request, 'sid') else 'N/A for HTTP'}")
    return render_template('team_setup.html', session_id=session_id)

@app.route('/battle')
def battle_page():
    return render_template('battle.html')

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")
    sid_to_remove = request.sid

    # Cleanup from lobbies
    for session_id, lobby_data in list(lobbies.items()):
        if sid_to_remove in lobby_data.get('players', []):
            lobby_data['players'].remove(sid_to_remove)
            if sid_to_remove in lobby_data.get('player_sids_in_order', []):
                 lobby_data['player_sids_in_order'].remove(sid_to_remove)
            if lobby_data.get('player_ready_status', {}).pop(sid_to_remove, False):
                lobby_data['ready_count'] = max(0, lobby_data.get('ready_count', 1) - 1)
            
            logger.info(f"Player {sid_to_remove} removed from lobby {session_id}. R:{lobby_data['ready_count']}, T:{len(lobby_data['players'])}")
            if not lobby_data['players']:
                logger.info(f"Lobby {session_id} empty, removing.")
                del lobbies[session_id]
            else:
                 emit('lobby_state_update', {'ready_players': lobby_data['ready_count'], 'total_players': len(lobby_data['players'])}, room=session_id)
            break

    # Cleanup from pending_battle_setups
    for session_id, setup_data in list(pending_battle_setups.items()):
        player_sids_map = setup_data.get('player_sids_map', {})
        if sid_to_remove in player_sids_map: # SID is the key
            disconnected_role = player_sids_map[sid_to_remove]
            logger.info(f"Player {disconnected_role} ({sid_to_remove}) from pending setup {session_id} disconnected. Removing setup.")
            other_player_sid = next((sid for sid, role in player_sids_map.items() if sid != sid_to_remove), None)
            if other_player_sid:
                emit('error_message', {'message': 'Opponent disconnected during team setup.'}, room=other_player_sid)
                emit('opponent_left_setup', {}, room=other_player_sid)
            del pending_battle_setups[session_id]
            # If the lobby still exists (e.g. players disconnected from setup but lobby wasn't auto-deleted)
            # you might want to notify players in that lobby too or reset its state.
            # For now, we assume lobby is either deleted or handled separately.
            break

    # Cleanup from active_battles
    for session_id, battle_data in list(active_battles.items()):
        # Using placeholder structure
        player1_sid = battle_data.get('player1_data', {}).get('sid')
        player2_sid = battle_data.get('player2_data', {}).get('sid')
        disconnected_player_role_in_battle = None
        opponent_sid_in_battle = None

        if sid_to_remove == player1_sid:
            disconnected_player_role_in_battle = battle_data.get('player1_data', {}).get('role', 'player1')
            opponent_sid_in_battle = player2_sid
        elif sid_to_remove == player2_sid:
            disconnected_player_role_in_battle = battle_data.get('player2_data', {}).get('role', 'player2')
            opponent_sid_in_battle = player1_sid
        
        if disconnected_player_role_in_battle:
            logger.info(f"Player {disconnected_player_role_in_battle} ({sid_to_remove}) from active battle {session_id} disconnected. Ending.")
            if opponent_sid_in_battle:
                winner_role = 'player2' if disconnected_player_role_in_battle == 'player1' else 'player1'
                emit('game_over', {'winner': winner_role, 'loser': disconnected_player_role_in_battle, 'reason': 'disconnect'}, room=opponent_sid_in_battle)
                emit('battle_message', {'message': f'Opponent ({disconnected_player_role_in_battle}) disconnected. You win!'}, room=opponent_sid_in_battle)
            del active_battles[session_id]
            break

@socketio.on('join_lobby')
def handle_join_lobby(data):
    session_id = data.get('session_id')
    player_sid = request.sid

    if not session_id or session_id not in lobbies:
        emit('error_message', {'message': 'Lobby not found.'})
        logger.warning(f"Join lobby failed: Session {session_id} not found for SID {player_sid}.")
        return

    lobby = lobbies[session_id]
    if player_sid not in lobby['players']:
        if len(lobby['players']) < 2:
            lobby['players'].append(player_sid)
            if player_sid not in lobby['player_sids_in_order']: # Add only if not already there (reconnect case)
                lobby['player_sids_in_order'].append(player_sid)
            join_room(session_id) 
            logger.info(f"Player {player_sid} joined lobby {session_id}. Players: {len(lobby['players'])}")
            emit('lobby_state_update', {'ready_players': lobby['ready_count'], 'total_players': len(lobby['players'])}, room=session_id)
        else:
            emit('error_message', {'message': 'Lobby is full.'})
            logger.warning(f"Join lobby failed: Session {session_id} full for SID {player_sid}.")
    else: 
        join_room(session_id) # Ensure re-joiner is in the room
        logger.info(f"Player {player_sid} re-joined lobby {session_id}.")
        emit('lobby_state_update', {'ready_players': lobby['ready_count'], 'total_players': len(lobby['players'])}, room=player_sid)

@socketio.on('join_team_setup')
def handle_join_team_setup(data):
    session_id = data.get('session_id')
    player_sid = request.sid
    
    logger.info(f"Player {player_sid} joining team setup for session {session_id}")
    logger.info(f"Current pending_battle_setups: {list(pending_battle_setups.keys())}")
    logger.info(f"Current lobbies: {list(lobbies.keys())}")
    
    # CRITICAL: If we're still in the lobby phase, create the pending battle setup now
    # This ensures that even if the battle_start event was missed, we can still proceed
    if session_id in lobbies and session_id not in pending_battle_setups:
        lobby = lobbies[session_id]
        if len(lobby['players']) >= 1:  # Need at least one player
            logger.info(f"Creating pending_battle_setup for session {session_id} that was in lobbies but not pending_battle_setups")
            
            # Create the pending battle setup with the available players
            player_sids_map = {}
            if len(lobby['player_sids_in_order']) >= 1:
                player_sids_map[lobby['player_sids_in_order'][0]] = 'player1'
            if len(lobby['player_sids_in_order']) >= 2:
                player_sids_map[lobby['player_sids_in_order'][1]] = 'player2'
            # Add the current player if not already present
            if player_sid not in player_sids_map and len(player_sids_map) < 2:
                role = 'player1' if 'player1' not in player_sids_map.values() else 'player2'
                player_sids_map[player_sid] = role
                
            pending_battle_setups[session_id] = {
                'player1_team': None, 'player2_team': None, 'teams_submitted_count': 0,
                'player_sids_map': player_sids_map
            }
    
    # Check again if the session is now in pending_battle_setups
    if session_id in pending_battle_setups:
        # Session is valid, add player to the room
        setup_info = pending_battle_setups[session_id]
        
        # If player is not in the player_sids_map, try to add them if there's space
        if player_sid not in setup_info.get('player_sids_map', {}):
            logger.info(f"Player {player_sid} not found in player_sids_map for session {session_id}")

            # This can happen if a player reconnects with a new SID
            # Try to match them based on their previous role if possible
            # For simplicity, we'll just assign them a new role if there's an empty slot
            if 'player1' not in setup_info.get('player_sids_map', {}).values():
                setup_info['player_sids_map'][player_sid] = 'player1'
                logger.info(f"Assigned reconnected player {player_sid} to role player1 in session {session_id}")
            elif 'player2' not in setup_info.get('player_sids_map', {}).values():
                setup_info['player_sids_map'][player_sid] = 'player2'
                logger.info(f"Assigned reconnected player {player_sid} to role player2 in session {session_id}")
            else:
                logger.error(f"Cannot assign role to player {player_sid} in session {session_id}, all roles taken")
                emit('error_message', {'message': 'Cannot join team setup. All player slots filled.'}, room=player_sid)
                return
        
        # Add player to the room for this session
        join_room(session_id)
        logger.info(f"Player {player_sid} joined team setup room {session_id}")
        
        # If both teams have been submitted, redirect player to battle immediately
        if setup_info.get('teams_submitted_count', 0) == 2 and session_id in active_battles:
            logger.info(f"Both teams already submitted for session {session_id}, redirecting player {player_sid} to battle")
            emit('battle_fully_ready', {'session_id': session_id}, room=player_sid)
        else:
            # Emit a success event to let the client know they successfully joined
            emit('team_setup_joined', {'session_id': session_id}, room=player_sid)
    else:
        # Neither in lobbies nor in pending_battle_setups - it's an invalid session
        logger.error(f"Invalid session {session_id} for team setup from {player_sid}. Not found in lobbies or pending_battle_setups.")
        emit('error_message', {'message': 'Invalid session for team setup.'}, room=player_sid)

@socketio.on('player_ready')
def handle_player_ready(data):
    session_id = data.get('session_id')
    player_sid = request.sid

    if not session_id or session_id not in lobbies:
        emit('error_message', {'message': 'Lobby not found.'})
        logger.warning(f"player_ready: Lobby {session_id} not found for SID {player_sid}")
        return

    lobby = lobbies[session_id]
    if player_sid in lobby['players']:
        if not lobby['player_ready_status'].get(player_sid, False):
            lobby['player_ready_status'][player_sid] = True
            lobby['ready_count'] += 1
            logger.info(f"Player {player_sid} ready in {session_id}. Ready: {lobby['ready_count']}/{len(lobby['players'])}")
        
        emit('lobby_state_update', {'ready_players': lobby['ready_count'], 'total_players': len(lobby['players'])}, room=session_id)

        if lobby['ready_count'] == 2 and len(lobby['players']) == 2:
            if session_id not in pending_battle_setups: 
                logger.info(f"Both players ready in {session_id}. Lobby state before creating pending: {lobby}")
                
                # CRITICAL CHECK: Ensure player_sids_in_order is valid
                if len(lobby.get('player_sids_in_order', [])) == 2:
                    pending_battle_setups[session_id] = {
                        'player1_team': None, 'player2_team': None, 'teams_submitted_count': 0,
                        'player_sids_map': {
                            lobby['player_sids_in_order'][0]: 'player1',
                            lobby['player_sids_in_order'][1]: 'player2'
                        }
                    }
                    logger.info(f"Created pending_battle_setup for {session_id}. Current pending_battle_setups: {list(pending_battle_setups.keys())}")
                    emit('battle_start', {'session_id': session_id}, room=session_id)
                else:
                    logger.error(f"Critical state inconsistency in lobby {session_id} for SID {player_sid}: Ready/Player count is 2, but player_sids_in_order length is {len(lobby.get('player_sids_in_order', []))}. Lobby: {lobby}")
                    emit('error_message', {'message': 'Internal server error: Could not prepare battle. Please try again.'}, room=session_id)
                    # Consider resetting lobby state here or notifying players
                    # For now, just prevent proceeding with inconsistent state
                    return 
    else:
        emit('error_message', {'message': 'You are not in this lobby.'})
        logger.warning(f"player_ready: SID {player_sid} not in players list for lobby {session_id}. Lobby: {lobby}")

@socketio.on('submit_team')
def handle_submit_team(data):
    session_id = data.get('session_id')
    team_data = data.get('team') 
    player_sid = request.sid

    logger.info(f"Team submission from {player_sid} for {session_id}. Team: {bool(team_data)}")

    if not session_id or session_id not in pending_battle_setups:
        emit('error_message', {'message': 'Invalid session for team submission.'})
        return

    setup_info = pending_battle_setups[session_id]
    player_role = setup_info['player_sids_map'].get(player_sid)
    
    if not player_role:
        emit('error_message', {'message': 'Player not recognized for this session.'})
        return

    if (player_role == 'player1' and setup_info['player1_team']) or \
       (player_role == 'player2' and setup_info['player2_team']):
        emit('team_submit_error', {'message': 'Team already submitted.'}, room=player_sid)
        return

    if player_role == 'player1':
        setup_info['player1_team'] = team_data
    elif player_role == 'player2':
        setup_info['player2_team'] = team_data
    
    setup_info['teams_submitted_count'] += 1
    logger.info(f"{player_role.capitalize()} ({player_sid}) submitted team for {session_id}. {setup_info['teams_submitted_count']}/2.")
    emit('team_submit_confirm', {'message': 'Team received.'}, room=player_sid)

    if setup_info['teams_submitted_count'] == 2:
        logger.info(f"Both teams submitted for {session_id}. Initializing battle.")
        
        p1_sid = next((sid for sid, role in setup_info['player_sids_map'].items() if role == 'player1'), None)
        p2_sid = next((sid for sid, role in setup_info['player_sids_map'].items() if role == 'player2'), None)

        if not (p1_sid and p2_sid and setup_info['player1_team'] and setup_info['player2_team']):
            logger.error(f"Critical data missing for battle creation in {session_id}. P1_SID:{p1_sid}, P2_SID:{p2_sid}, P1_Team:{bool(setup_info['player1_team'])}, P2_Team:{bool(setup_info['player2_team'])}")
            emit('error_message', {'message': 'Internal server error starting battle.'}, room=session_id)
            # Clean up to prevent broken state
            if session_id in pending_battle_setups: del pending_battle_setups[session_id]
            if session_id in lobbies: del lobbies[session_id]
            return

        active_battles[session_id] = {
            'session_id': session_id,
            'player1_data': {'team': setup_info['player1_team'], 'active_pokemon_idx': 0, 'sid': p1_sid, 'role': 'player1'},
            'player2_data': {'team': setup_info['player2_team'], 'active_pokemon_idx': 0, 'sid': p2_sid, 'role': 'player2'},
            'current_turn': 'player1', 
            'log': [f"Battle starting: P1 ({p1_sid}) vs P2 ({p2_sid})!"]
        }
        
        del pending_battle_setups[session_id]
        if session_id in lobbies: del lobbies[session_id] # Clean up original lobby

        socketio.emit('battle_fully_ready', {'session_id': session_id}, room=session_id)
        logger.info(f"Battle {session_id} active and ready.")
    else:
        # Notify opponent
        opponent_sid = next((sid for sid, role in setup_info['player_sids_map'].items() if sid != player_sid), None)
        if opponent_sid:
             emit('opponent_team_submitted', {}, room=opponent_sid)

@socketio.on('join_battle')
def handle_join_battle(data):
    session_id = data.get('session_id')
    player_sid = request.sid
    logger.info(f"Player {player_sid} attempting to join battle {session_id}")

    # Check if session exists in pending_battle_setups but not in active_battles
    # This could indicate teams are being submitted but battle not yet fully initialized
    if session_id not in active_battles and session_id in pending_battle_setups:
        setup_info = pending_battle_setups[session_id]
        teams_submitted = setup_info.get('teams_submitted_count', 0)
        logger.warning(f"Battle {session_id} not active yet but found in pending_battle_setups. Teams submitted: {teams_submitted}/2")
        emit('error_message', {'message': f'Battle not ready yet. {teams_submitted}/2 teams submitted. Please wait.'}, room=player_sid)
        # If player is part of this pending battle, add them to the room
        if player_sid in setup_info.get('player_sids_map', {}):
            join_room(session_id)
            logger.info(f"Added player {player_sid} to room {session_id} while waiting for battle to be ready")
        return

    # If not in active_battles or pending_battle_setups, this is an invalid session
    if session_id not in active_battles:
        logger.error(f"Battle {session_id} not found in active_battles or pending_battle_setups for SID {player_sid}.")
        emit('error_message', {'message': f'Battle session {session_id} not found or not initialized yet.'}, room=player_sid)
        return

    battle_session = active_battles[session_id]
    player_role_in_battle = None
    if battle_session.get('player1_data', {}).get('sid') == player_sid:
        player_role_in_battle = 'player1'
    elif battle_session.get('player2_data', {}).get('sid') == player_sid:
        player_role_in_battle = 'player2'

    # If player's SID doesn't match either player in the battle, check if they might be reconnecting
    if not player_role_in_battle:
        # This could be a player that disconnected and reconnected with a new SID
        logger.warning(f"SID {player_sid} not found in battle {session_id}, checking if this is a reconnection")
        
        # Try to assign them to a role if possible (in a real implementation, you'd want a more
        # robust way to identify returning players, like cookies or auth tokens)
        if 'player1_reconnect_token' in battle_session and battle_session.get('player1_reconnect_token') == data.get('reconnect_token'):
            player_role_in_battle = 'player1'
            battle_session['player1_data']['sid'] = player_sid
            logger.info(f"Reconnected player {player_sid} as player1 in battle {session_id}")
        elif 'player2_reconnect_token' in battle_session and battle_session.get('player2_reconnect_token') == data.get('reconnect_token'):
            player_role_in_battle = 'player2'
            battle_session['player2_data']['sid'] = player_sid
            logger.info(f"Reconnected player {player_sid} as player2 in battle {session_id}")
        else:
            logger.error(f"SID {player_sid} not authorized for battle {session_id} and no valid reconnection token")
            emit('error_message', {'message': 'You are not part of this battle session.'}, room=player_sid)
            return

    # Player is authorized, add them to the room
    join_room(session_id)
    logger.info(f"Player {player_role_in_battle} ({player_sid}) joined battle room {session_id}")
    emit('battle_update', battle_session, room=player_sid) # Send current state to the player
    
    # Let other players know this player has joined (if you want to show "Player X has joined" messages)
    emit('player_joined', {'role': player_role_in_battle}, room=session_id, skip_sid=player_sid)

@socketio.on('store_reconnect_token')
def handle_store_reconnect_token(data):
    """
    Store a reconnection token for a player in a battle session.
    This allows them to rejoin with a new socket ID in case of disconnection.
    """
    session_id = data.get('session_id')
    role = data.get('role')
    token = data.get('token')
    player_sid = request.sid
    
    if not all([session_id, role, token]):
        logger.warning(f"Missing data for reconnect token storage: {data}")
        return
        
    if session_id not in active_battles:
        logger.warning(f"Can't store reconnect token for non-existent battle: {session_id}")
        return
        
    battle_session = active_battles[session_id]
    
    # Verify the player's role matches their SID
    expected_sid = None
    if role == 'player1':
        expected_sid = battle_session.get('player1_data', {}).get('sid')
    elif role == 'player2':
        expected_sid = battle_session.get('player2_data', {}).get('sid')
        
    if player_sid != expected_sid:
        logger.warning(f"SID mismatch for reconnect token storage. Expected {expected_sid}, got {player_sid}")
        return
        
    # Store the token
    token_key = f"{role}_reconnect_token"
    battle_session[token_key] = token
    logger.info(f"Stored reconnect token for {role} in battle {session_id}")

@socketio.on('player_action')
def handle_player_action(data):
    session_id = data.get('session_id')
    player_sid = request.sid
    action_type = data.get('action_type')
    details = data.get('details')

    logger.info(f"Action from {player_sid} in {session_id}: {action_type}, {details}")

    if session_id not in active_battles:
        emit('action_error', {'message': 'Battle session not found.'}, room=player_sid)
        return

    battle_game = active_battles[session_id]
    actor_role = None
    if battle_game.get('player1_data', {}).get('sid') == player_sid:
        actor_role = 'player1'
    elif battle_game.get('player2_data', {}).get('sid') == player_sid:
        actor_role = 'player2'

    if not actor_role:
        emit('action_error', {'message': 'Player not recognized.'}, room=player_sid)
        return

    if battle_game.get('current_turn') == actor_role:
        # Placeholder: actual game logic (e.g. from PokemonService or Battle class) would go here
        battle_game['log'].append(f"{actor_role.capitalize()} action: {action_type} {details}")
        battle_game['current_turn'] = 'player2' if battle_game['current_turn'] == 'player1' else 'player1'
        emit('battle_update', battle_game, room=session_id)
        logger.info(f"Battle {session_id} updated. Turn: {battle_game['current_turn']}.")
        # Add game over check here if applicable after an action
    else:
        emit('action_error', {'message': 'Not your turn or action already processed.'}, room=player_sid)

if __name__ == '__main__':
    logger.info("Starting Flask-SocketIO server...")
    # For production, use a proper WSGI server like gunicorn with eventlet or gevent workers
    # Example: gunicorn --worker-class eventlet -w 1 module:app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
# --- END OF MODIFIED app.py ---