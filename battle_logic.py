import random
import logging
import json
import os
import math # Added for damage calculation

logger = logging.getLogger(__name__)

# --- [DONE] Chunk 1: Basic Types & Class Updates ---
# Key: Attacking Type, Value: Dict of {Defending Type: Multiplier}
TYPE_CHART = {
    'Normal': {'Rock': 0.5, 'Ghost': 0, 'Steel': 0.5},
    'Fire': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 2, 'Bug': 2, 'Rock': 0.5, 'Dragon': 0.5, 'Steel': 2},
    'Water': {'Fire': 2, 'Water': 0.5, 'Grass': 0.5, 'Ground': 2, 'Rock': 2, 'Dragon': 0.5},
    'Electric': {'Water': 2, 'Electric': 0.5, 'Grass': 0.5, 'Ground': 0, 'Flying': 2, 'Dragon': 0.5},
    'Grass': {'Fire': 0.5, 'Water': 2, 'Grass': 0.5, 'Poison': 0.5, 'Ground': 2, 'Flying': 0.5, 'Bug': 0.5, 'Rock': 2, 'Dragon': 0.5, 'Steel': 0.5},
    'Ice': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 0.5, 'Ground': 2, 'Flying': 2, 'Dragon': 2, 'Steel': 0.5},
    'Fighting': {'Normal': 2, 'Flying': 0.5, 'Poison': 0.5, 'Rock': 2, 'Bug': 0.5, 'Ghost': 0, 'Steel': 2, 'Psychic': 0.5, 'Ice': 2, 'Dark': 2, 'Fairy': 0.5},
    'Poison': {'Grass': 2, 'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5, 'Steel': 0, 'Fairy': 2},
    'Ground': {'Fire': 2, 'Electric': 2, 'Grass': 0.5, 'Poison': 2, 'Flying': 0, 'Bug': 0.5, 'Rock': 2, 'Steel': 2},
    'Flying': {'Electric': 0.5, 'Grass': 2, 'Fighting': 2, 'Rock': 0.5, 'Bug': 2, 'Steel': 0.5},
    'Psychic': {'Fighting': 2, 'Poison': 2, 'Steel': 0.5, 'Psychic': 0.5, 'Dark': 0},
    'Bug': {'Fire': 0.5, 'Grass': 2, 'Fighting': 0.5, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 2, 'Ghost': 0.5, 'Dark': 2, 'Steel': 0.5, 'Fairy': 0.5},
    'Rock': {'Fire': 2, 'Ice': 2, 'Fighting': 0.5, 'Ground': 0.5, 'Flying': 2, 'Bug': 2, 'Steel': 0.5},
    'Ghost': {'Normal': 0, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5},
    'Dragon': {'Dragon': 2, 'Steel': 0.5, 'Fairy': 0},
    'Dark': {'Fighting': 0.5, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5, 'Fairy': 0.5},
    'Steel': {'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Ice': 2, 'Rock': 2, 'Steel': 0.5, 'Fairy': 2},
    'Fairy': {'Fire': 0.5, 'Fighting': 2, 'Poison': 0.5, 'Dragon': 2, 'Dark': 2, 'Steel': 0.5}
}

def get_type_effectiveness(move_type, defender_types):
    """Calculates the type effectiveness multiplier."""
    if not move_type or not defender_types:
        return 1.0
    effectiveness = 1.0
    if move_type in TYPE_CHART:
        attack_effectiveness = TYPE_CHART[move_type]
        for def_type in defender_types:
            # Ensure def_type is valid before accessing
            if def_type in attack_effectiveness:
                effectiveness *= attack_effectiveness[def_type]
            # Handle cases where a type might not be in the inner dict (neutral effectiveness)
    return effectiveness
# --- END [DONE] Chunk 1 ---

# Load Pokemon data from JSON file
POKEMON_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pokemon.json')
try:
    with open(POKEMON_DATA_PATH, 'r') as f:
        POKEMON_DATA = json.load(f)
    logger.info(f"Loaded {len(POKEMON_DATA)} Pokemon from {POKEMON_DATA_PATH}")
except FileNotFoundError:
    logger.error(f"Pokemon data file not found at {POKEMON_DATA_PATH}")
    POKEMON_DATA = []
except json.JSONDecodeError:
    logger.error(f"Error decoding JSON from {POKEMON_DATA_PATH}")
    POKEMON_DATA = []

# --- [DONE] Chunk 1: Class Updates ---
class Pokemon:
    def __init__(self, name, level, type_list, base_stats, moves):
        self.name = name
        self.level = level
        # --- UPDATED: Handle type_list ---
        self.types = type_list if isinstance(type_list, list) else [type_list] # Ensure it's a list
        # --- END UPDATED ---
        self.base_stats = base_stats
        self.max_hp = self._calculate_hp(base_stats.get('hp', 1), level) # Use .get for safety
        self.current_hp = self.max_hp
        self.attack = self._calculate_stat(base_stats.get('attack', 1), level)
        self.defense = self._calculate_stat(base_stats.get('defense', 1), level)
        self.special_attack = self._calculate_stat(base_stats.get('special_attack', 1), level)
        self.special_defense = self._calculate_stat(base_stats.get('special_defense', 1), level)
        self.speed = self._calculate_stat(base_stats.get('speed', 1), level)
        # Ensure moves is a list before processing
        self.moves = [Move(m) for m in moves if isinstance(m, dict)] if isinstance(moves, list) else []
        self.status = None # e.g., 'poison', 'paralysis'
        self.is_fainted = False

    # --- ADDED: get_opponent_view method ---
    def get_opponent_view(self):
        """Returns a simplified dictionary view suitable for the opponent."""
        return {
            'name': self.name,
            'level': self.level,
            'current_hp': self.current_hp, # Send current HP
            'max_hp': self.max_hp,         # Send max HP for percentage display
            'hp_percentage': int((self.current_hp / self.max_hp) * 100) if self.max_hp > 0 else 0,
            'status': self.status,
            'is_fainted': self.is_fainted,
            # Add sprite URL if available later
        }
    # --- END ADDED ---

    def _calculate_hp(self, base_hp, level):
        # Simplified HP calculation (Gen 1-2 style approx for level 50)
        # Formula: floor(floor((Base + IV) * 2 + floor(ceil(sqrt(Stat Exp)) / 4)) * Level / 100) + Level + 10
        # Simplified: Assuming IV=0, Stat Exp=0 for simplicity
        return math.floor((base_hp * 2 * level) / 100) + level + 10

    def _calculate_stat(self, base_stat, level):
        # Simplified stat calculation (Gen 1-2 style approx for level 50)
        # Formula: floor(floor((Base + IV) * 2 + floor(ceil(sqrt(Stat Exp)) / 4)) * Level / 100) + 5
        # Simplified: Assuming IV=0, Stat Exp=0
        return math.floor((base_stat * 2 * level) / 100) + 5

    def take_damage(self, damage):
        """Applies damage and updates fainted status."""
        effective_damage = max(0, damage) # Ensure damage isn't negative
        self.current_hp -= effective_damage
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_fainted = True
            logger.info(f"{self.name} fainted!")
        logger.info(f"{self.name} took {effective_damage} damage. Current HP: {self.current_hp}/{self.max_hp}")
        return effective_damage # Return actual damage dealt

    def is_alive(self):
        return not self.is_fainted

# --- [DONE] Chunk 1: Class Updates ---
class Move:
    # --- UPDATED: Accept move data dictionary ---
    def __init__(self, move_data):
        if not isinstance(move_data, dict):
            logger.error(f"Invalid move_data provided: {move_data}. Creating default move.")
            move_data = {} # Default to empty dict to avoid errors

        self.name = move_data.get('name', 'Struggle')
        self.type = move_data.get('type', 'Normal').capitalize() # Ensure consistent capitalization
        self.power = move_data.get('power') # Can be None for status moves
        self.accuracy = move_data.get('accuracy') # Can be None
        self.max_pp = move_data.get('pp', 1) # Default PP to 1 if missing
        self.current_pp = self.max_pp
        self.damage_class = move_data.get('damage_class', 'physical') # 'physical' or 'special'
        # TODO: Add other move attributes like priority, effects, target, etc.
    # --- END UPDATED ---

    # --- ADDED: Method to use PP ---
    def use_pp(self):
        """Decrements PP if available. Returns True if PP was used, False otherwise."""
        if self.current_pp > 0:
            self.current_pp -= 1
            logger.debug(f"Used 1 PP for {self.name}. Remaining: {self.current_pp}/{self.max_pp}")
            return True
        logger.warning(f"Move {self.name} has no PP left.")
        return False
    # --- END ADDED ---
# --- END [DONE] Chunk 1 ---

class Battle:
    def __init__(self, session_id, team1_data, team2_data):
        self.session_id = session_id
        self._load_teams(team1_data, team2_data) # Use helper to load teams
        self.current_turn = 1
        # --- [DONE] Chunk 2: Initialize player_actions ---
        self.player_actions = {
            'player1': None,  # Will store {'type': 'move'/'switch', 'value': Move obj / team_index}
            'player2': None
        }
        # --- END [DONE] Chunk 2 ---
        self._initialize_active_pokemon()
        self.log = [] # Battle log entries
        self.winner = None # Track the winner

    def _load_teams(self, team1_data, team2_data):
        """Loads and validates teams."""
        self.team1 = [self._create_pokemon(p_name) for p_name in team1_data if p_name]
        self.team2 = [self._create_pokemon(p_name) for p_name in team2_data if p_name]
        if not self.team1 or not self.team2:
            raise ValueError("Both teams must have at least one Pokemon.")
        logger.info(f"Team 1 loaded: {[p.name for p in self.team1]}")
        logger.info(f"Team 2 loaded: {[p.name for p in self.team2]}")

    def _initialize_active_pokemon(self):
        """Sets the initial active Pokemon for both players."""
        self.active_pokemon = {
            'player1': self._get_first_available_pokemon(self.team1),
            'player2': self._get_first_available_pokemon(self.team2)
        }
        if not self.active_pokemon['player1'] or not self.active_pokemon['player2']:
             # This case should ideally be prevented by team validation, but handle defensively
             self.winner = 'draw' # Or determine based on who has Pokemon
             logger.error("Could not set initial active Pokemon for both players.")
             raise ValueError("Failed to initialize battle: one or both teams have no available Pokemon.")
        logger.info(f"Initial active Pokemon: P1 - {self.active_pokemon['player1'].name}, P2 - {self.active_pokemon['player2'].name}")


    def _get_first_available_pokemon(self, team):
        """Returns the first non-fainted Pokemon in a team."""
        for pokemon in team:
            if pokemon and pokemon.is_alive(): # Check if pokemon object exists and is alive
                return pokemon
        return None

    def _create_pokemon(self, pokemon_name):
        """Creates a Pokemon instance from POKEMON_DATA."""
        # Use case-insensitive comparison
        pokemon_data = next((p for p in POKEMON_DATA if p['name'].lower() == pokemon_name.lower()), None)

        if pokemon_data:
            logger.info(f"Creating Pokemon: {pokemon_data['name']}")
            # --- UPDATED: Pass type_list correctly ---
            return Pokemon(
                name=pokemon_data['name'],
                level=pokemon_data.get('level', 50), # Default level if missing
                type_list=pokemon_data['type'], # Pass the list directly
                base_stats=pokemon_data['base_stats'],
                moves=pokemon_data.get('moves', []) # Default to empty list if missing
            )
            # --- END UPDATED ---
        else:
            logger.warning(f"Pokemon data not found for: {pokemon_name}. Cannot create.")
            # Return None or raise an error if a Pokemon must be found
            return None # Returning None, handle this in _load_teams

    # --- [DONE] Chunk 2: Update select_move ---
    def select_move(self, player_id, move_index):
        """Record the move selected by a player using its index."""
        if self.winner: return False # Don't allow actions if game is over
        if player_id not in self.player_actions:
            logger.warning(f"Invalid player_id: {player_id}")
            return False
        if self.player_actions[player_id] is not None:
             logger.warning(f"Player {player_id} has already selected an action this turn.")
             return False # Action already selected

        active_pokemon = self.active_pokemon.get(player_id)
        if not active_pokemon or not active_pokemon.is_alive():
            logger.warning(f"Player {player_id} has no active, non-fainted Pokemon.")
            return False

        if not isinstance(move_index, int) or move_index < 0 or move_index >= len(active_pokemon.moves):
             logger.warning(f"Player {player_id} selected invalid move index: {move_index}")
             return False

        selected_move = active_pokemon.moves[move_index]

        if selected_move.current_pp <= 0:
            logger.warning(f"Player {player_id} selected move '{selected_move.name}' with no PP left.")
            # TODO: Potentially force Struggle or return False
            return False # For now, disallow selecting move with 0 PP

        # Store the action
        self.player_actions[player_id] = {'type': 'move', 'value': selected_move}
        logger.info(f"Player {player_id} selected move: {selected_move.name}")
        return True
    # --- END [DONE] Chunk 2 ---

    # --- [NEW] Chunk 3: Switch Implementation ---
    def select_switch(self, player_id, team_index):
        """Record the switch action selected by a player."""
        if self.winner: return False # Don't allow actions if game is over
        if player_id not in self.player_actions:
            logger.warning(f"Invalid player_id: {player_id}")
            return False
        if self.player_actions[player_id] is not None:
             logger.warning(f"Player {player_id} has already selected an action this turn.")
             return False # Action already selected

        team = self.team1 if player_id == 'player1' else self.team2
        active_pokemon = self.active_pokemon.get(player_id)

        if not isinstance(team_index, int) or team_index < 0 or team_index >= len(team):
            logger.warning(f"Player {player_id} selected invalid team index: {team_index}")
            return False

        target_pokemon = team[team_index]

        if not target_pokemon:
             logger.warning(f"Player {player_id} tried switching to a non-existent Pokemon at index {team_index}.")
             return False
        if target_pokemon.is_fainted:
            logger.warning(f"Player {player_id} cannot switch to fainted Pokemon: {target_pokemon.name}")
            return False
        if target_pokemon is active_pokemon:
             logger.warning(f"Player {player_id} cannot switch to the currently active Pokemon: {target_pokemon.name}")
             return False

        # Store the action
        self.player_actions[player_id] = {'type': 'switch', 'value': team_index}
        logger.info(f"Player {player_id} selected switch to: {target_pokemon.name} (Index: {team_index})")
        return True
    # --- END [NEW] Chunk 3 ---

    # --- [MODIFIED] Chunk 2 & 3: Renamed and Logic Updated ---
    def are_actions_selected(self):
        """Check if both players (with active Pokemon) have selected their actions."""
        p1_active = self.active_pokemon.get('player1') and self.active_pokemon['player1'].is_alive()
        p2_active = self.active_pokemon.get('player2') and self.active_pokemon['player2'].is_alive()
        p1_action = self.player_actions.get('player1')
        p2_action = self.player_actions.get('player2')

        # Both players need an action selected *if* they have an active Pokemon
        # (Handles cases where one player might faint before selecting)
        player1_ready = not p1_active or p1_action is not None
        player2_ready = not p2_active or p2_action is not None

        return player1_ready and player2_ready
    # --- END [MODIFIED] Chunk 2 & 3 ---

    # --- [REFINED] Chunk 4: Turn Execution Logic ---
    def run_turn(self):
        """Simulate one turn of the battle, executing selected actions."""
        # --- [FIXED] Chunk 2: Use are_actions_selected ---
        if not self.are_actions_selected():
        # --- END [FIXED] Chunk 2 ---
            logger.warning("Cannot run turn: Actions not selected by both players.")
            return False # Indicate turn didn't run

        if self.winner:
            logger.warning("Cannot run turn: Battle is already over.")
            return False

        logger.info(f"--- Turn {self.current_turn} ---")
        self.log.append(f"--- Turn {self.current_turn} ---")

        # Get active Pokemon and actions
        p1 = self.active_pokemon.get('player1')
        p2 = self.active_pokemon.get('player2')
        action1 = self.player_actions.get('player1')
        action2 = self.player_actions.get('player2')

        # Determine turn order (simplistic: speed only, switches happen before attacks if faster)
        # TODO: Implement move/action priority
        order = []
        p1_speed = p1.speed if p1 and p1.is_alive() else 0
        p2_speed = p2.speed if p2 and p2.is_alive() else 0

        if p1_speed > p2_speed:
            order = [('player1', action1), ('player2', action2)]
        elif p2_speed > p1_speed:
            order = [('player2', action2), ('player1', action1)]
        else: # Speed tie - random order
            order = random.sample([('player1', action1), ('player2', action2)], 2)

        logger.debug(f"Turn order determined: {[p[0] for p in order]}")

        # Execute actions in order
        for player_id, action in order:
            if self.winner: break # Stop if a previous action ended the game
            opponent_id = 'player2' if player_id == 'player1' else 'player1'
            if action and self.active_pokemon[player_id] and self.active_pokemon[player_id].is_alive():
                 # Only execute if the Pokemon is still active and alive
                 self._execute_action(player_id, opponent_id, action)
                 # Check for fainting immediately after an action
                 self._check_fainted_and_prompt_switch(opponent_id) # Check opponent first
                 self._check_fainted_and_prompt_switch(player_id)   # Then check attacker
                 # Check for game over after each action
                 if self.check_game_over():
                     break # End turn immediately if game is over

        # End of turn effects (status damage, etc.) - TODO

        # Reset actions for the next turn only if the game is not over
        if not self.winner:
            self.player_actions = {'player1': None, 'player2': None}
            self.current_turn += 1
            logger.info(f"--- End of Turn {self.current_turn - 1} ---")
            self.log.append(f"--- End of Turn {self.current_turn - 1} ---")
        else:
             logger.info(f"--- Battle Ended on Turn {self.current_turn} ---")
             self.log.append(f"--- Battle Ended ---")

        return True # Indicate turn ran successfully (or ended)

    def _execute_action(self, player_id, opponent_id, action):
        """Executes a single player's action (move or switch)."""
        attacker = self.active_pokemon.get(player_id)
        defender = self.active_pokemon.get(opponent_id) # Can be None if opponent fainted

        if not attacker or not attacker.is_alive():
            logger.warning(f"Attempted action for {player_id} but Pokemon is fainted or inactive.")
            return # Should not happen if run_turn checks correctly, but defensive check

        action_type = action.get('type')
        action_value = action.get('value')

        if action_type == 'move':
            move = action_value
            if defender and defender.is_alive(): # Check if defender exists and is alive
                 self._execute_move(attacker, defender, move, player_id)
            elif defender and not defender.is_alive():
                 logger.info(f"{attacker.name} used {move.name}, but {defender.name} already fainted!")
                 self.log.append(f"{attacker.name} used {move.name}, but the target had already fainted!")
                 # Still use PP even if target is fainted
                 move.use_pp()
            else: # Should not happen unless opponent has no Pokemon left
                 logger.info(f"{attacker.name} used {move.name}, but there was no target.")
                 self.log.append(f"{attacker.name} used {move.name}, but there was no target.")
                 move.use_pp()

        elif action_type == 'switch':
            team_index = action_value
            team = self.team1 if player_id == 'player1' else self.team2
            new_pokemon = team[team_index]
            old_pokemon_name = attacker.name

            # Perform the switch
            self.active_pokemon[player_id] = new_pokemon
            logger.info(f"{player_id} switched from {old_pokemon_name} to {new_pokemon.name}")
            self.log.append(f"{player_id.capitalize()} withdrew {old_pokemon_name}!")
            self.log.append(f"{player_id.capitalize()} sent out {new_pokemon.name}!")
            # TODO: Reset volatile statuses, stat changes upon switching

        else:
            logger.error(f"Unknown action type '{action_type}' for {player_id}")

    def _execute_move(self, attacker, defender, move, player_id):
        """Execute a single move, calculate damage, apply effects."""
        logger.info(f"{attacker.name} used {move.name} on {defender.name}!")
        self.log.append(f"{attacker.name} used {move.name}!")

        # --- UPDATED: Use PP via method ---
        if not move.use_pp():
            # This case should ideally be prevented by select_move, but handle Struggle logic here later if needed
            logger.error(f"{attacker.name} tried to use {move.name} but has no PP!")
            self.log.append(f"{attacker.name} has no PP left for {move.name}!")
            # TODO: Implement Struggle
            return

        # TODO: Implement accuracy check
        # accuracy_roll = random.randint(1, 100)
        # if move.accuracy is not None and accuracy_roll > move.accuracy:
        #     logger.info(f"{move.name} missed!")
        #     self.log.append(f"{attacker.name}'s attack missed!")
        #     return

        # Check for type immunity (e.g., Ground vs Flying) before calculating damage
        effectiveness = get_type_effectiveness(move.type, defender.types)
        if effectiveness == 0:
            logger.info(f"{move.name} has no effect on {defender.name}!")
            self.log.append(f"It doesn't affect {defender.name}...")
            return

        # Calculate and apply damage if it's a damaging move
        if move.power is not None and move.power > 0:
            # --- UPDATED: Use _calculate_damage ---
            damage = self._calculate_damage(attacker, defender, move, effectiveness)
            # --- END UPDATED ---

            if damage > 0:
                defender.take_damage(damage)
                self.log.append(f"{defender.name} took {damage} damage.")

                # Log effectiveness
                if effectiveness > 1:
                    self.log.append("It's super effective!")
                elif effectiveness < 1:
                    self.log.append("It's not very effective...")
            else:
                # Handle cases where damage calculates to 0 (maybe due to rounding or low stats)
                 self.log.append(f"The attack had no discernible effect.")


        else:
            # Handle non-damaging moves (e.g., stat changes, status)
            # TODO: Implement status moves logic
            logger.info(f"{move.name} is a non-damaging move (not implemented).")
            self.log.append(f"But nothing happened.") # Placeholder for non-implemented status moves

    def _calculate_damage(self, attacker, defender, move, effectiveness):
        """Calculates damage based on stats, move power, types, etc."""
        # Basic Gen 1-5 formula components:
        # Damage = (((((2 * Level / 5) + 2) * Power * A / D) / 50) + 2) * Modifier
        # Modifier = STAB * Type * Critical * other * random (0.85-1.00)

        level = attacker.level
        power = move.power

        # Determine Attack and Defense stats based on move category
        if move.damage_class == 'special':
            attack_stat = attacker.special_attack
            defense_stat = defender.special_defense
        else: # Default to physical
            attack_stat = attacker.attack
            defense_stat = defender.defense

        # Basic damage calculation (simplified level term for level 50)
        base_damage = (((2 * level / 5 + 2) * power * attack_stat / defense_stat) / 50) + 2

        # Modifiers
        # STAB (Same Type Attack Bonus)
        stab_bonus = 1.5 if move.type in attacker.types else 1.0

        # Type Effectiveness (already calculated)
        type_modifier = effectiveness

        # Critical Hit (simplified placeholder)
        # TODO: Implement proper critical hit chance and modifier (Gen VI+ is 1.5x)
        crit_modifier = 1.0
        # if random.random() < (1/16): # Example crit chance
        #     crit_modifier = 1.5
        #     self.log.append("A critical hit!")

        # Random variation (85% to 100%)
        random_modifier = random.uniform(0.85, 1.00)

        # Combine modifiers
        modifier = stab_bonus * type_modifier * crit_modifier * random_modifier

        # Calculate final damage
        final_damage = math.floor(base_damage * modifier)

        # Ensure minimum 1 damage for effective hits
        return max(1, final_damage) if type_modifier > 0 else 0

    def _check_fainted_and_prompt_switch(self, player_id):
        """Checks if a player's active Pokemon fainted. Doesn't force switch here."""
        active_pokemon = self.active_pokemon.get(player_id)
        if active_pokemon and active_pokemon.is_fainted:
            logger.info(f"{active_pokemon.name} fainted!")
            self.log.append(f"{active_pokemon.name} fainted!")
            # In a real game, the player would be prompted to switch.
            # For this logic, we might automatically switch if possible,
            # or just mark the need for a switch in the state.
            # For now, we won't auto-switch here, letting the game state reflect the faint.
            # Auto-switching might happen at the start of the *next* turn or via game rules.
            # Check game over here too.
            self.check_game_over() # Check if this faint ended the game


    # --- END [REFINED] Chunk 4 ---


    # --- [NEW & REFINED] Chunk 5: Battle State & Game Over ---
    def check_game_over(self):
        """Checks if a player has lost (no usable Pokemon). Sets self.winner."""
        if self.winner: # Already decided
            return True

        player1_lost = all(p is None or p.is_fainted for p in self.team1)
        player2_lost = all(p is None or p.is_fainted for p in self.team2)

        if player1_lost and player2_lost:
             self.winner = 'draw'
             self.log.append("Both players have no Pokemon left! It's a draw!")
             logger.info("Game Over: Draw")
             return True
        elif player1_lost:
            self.winner = 'player2'
            self.log.append("Player 1 has no more Pokemon that can fight!")
            self.log.append("Player 2 wins!")
            logger.info("Game Over: Player 2 wins")
            return True
        elif player2_lost:
            self.winner = 'player1'
            self.log.append("Player 2 has no more Pokemon that can fight!")
            self.log.append("Player 1 wins!")
            logger.info("Game Over: Player 1 wins")
            return True

        return False # Game is not over

    # Renamed from is_battle_over - just checks the flag now
    def is_game_over(self):
        """Returns True if the game has a winner or is a draw."""
        return self.winner is not None

    def get_state_for_player(self, player_id):
        """Get the comprehensive battle state view for a specific player."""
        if player_id not in ['player1', 'player2']:
            logger.error(f"Requested state for invalid player_id: {player_id}")
            return None

        opponent_id = 'player2' if player_id == 'player1' else 'player1'
        player_team = self.team1 if player_id == 'player1' else self.team2
        # opponent_team = self.team2 if player_id == 'player1' else self.team1 # Needed for opponent team status

        player_active_pokemon = self.active_pokemon.get(player_id)
        opponent_active_pokemon = self.active_pokemon.get(opponent_id)

        # Determine if player needs to select an action
        can_select_action = False
        if not self.winner and player_active_pokemon and player_active_pokemon.is_alive():
             if self.player_actions[player_id] is None:
                 can_select_action = True

        # Determine if player is waiting for opponent
        waiting_for_opponent = False
        if not self.winner and player_active_pokemon and player_active_pokemon.is_alive():
             if self.player_actions[player_id] is not None and self.player_actions[opponent_id] is None:
                 # Check if opponent *can* make a move (i.e., they have an active Pokemon)
                 if opponent_active_pokemon and opponent_active_pokemon.is_alive():
                     waiting_for_opponent = True

        state = {
            'session_id': self.session_id,
            'player_id': player_id, # Identify which player this state is for
            'current_turn': self.current_turn,
            'active_pokemon': self._get_detailed_pokemon_view(player_active_pokemon) if player_active_pokemon else None,
            'opponent_active_pokemon': opponent_active_pokemon.get_opponent_view() if opponent_active_pokemon else None,
            'player_team': [self._get_detailed_pokemon_view(p, include_moves=False) for p in player_team if p], # Provide status of own team
            # Optional: Add opponent team summary (e.g., icons with faint status) later
            # 'opponent_team_summary': [{'name': p.name, 'is_fainted': p.is_fainted} for p in opponent_team if p],
            'can_select_action': can_select_action,
            'waiting_for_opponent': waiting_for_opponent,
            'log': list(self.log), # Send a copy of the log
            'game_over': self.is_game_over(),
            'winner': self.winner
        }
        return state

    def _get_detailed_pokemon_view(self, pokemon, include_moves=True):
        """Helper to get a detailed view of a Pokemon for the state."""
        if not pokemon: return None
        view = {
            'name': pokemon.name,
            'level': pokemon.level,
            'types': list(pokemon.types), # Send as list
            'current_hp': pokemon.current_hp,
            'max_hp': pokemon.max_hp,
            'hp_percentage': int((pokemon.current_hp / pokemon.max_hp) * 100) if pokemon.max_hp > 0 else 0,
            'attack': pokemon.attack,
            'defense': pokemon.defense,
            'special_attack': pokemon.special_attack,
            'special_defense': pokemon.special_defense,
            'speed': pokemon.speed,
            'status': pokemon.status,
            'is_fainted': pokemon.is_fainted,
        }
        if include_moves:
             view['moves'] = [{'name': m.name, 'type': m.type, 'power': m.power, 'accuracy': m.accuracy,
                               'damage_class': m.damage_class, 'current_pp': m.current_pp, 'max_pp': m.max_pp}
                              for m in pokemon.moves]
        return view

    # Kept from original code - might be useful for app.py to call after sending state
    def clear_log(self):
        """Clears the battle log."""
        self.log = []
        logger.info("Battle log cleared.")
    # --- END [NEW & REFINED] Chunk 5 ---