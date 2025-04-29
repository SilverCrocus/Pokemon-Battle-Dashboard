import random
import logging
import json
import os

logger = logging.getLogger(__name__)

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


class Pokemon:
    def __init__(self, name, level, type, base_stats, moves):
        self.name = name
        self.level = level
        self.types = type # Use 'types' as it's a list
        self.base_stats = base_stats
        self.max_hp = self._calculate_hp(base_stats['hp'], level) # Calculate actual HP
        self.current_hp = self.max_hp
        self.attack = self._calculate_stat(base_stats['attack'], level)
        self.defense = self._calculate_stat(base_stats['defense'], level)
        self.special_attack = self._calculate_stat(base_stats['special_attack'], level)
        self.special_defense = self._calculate_stat(base_stats['special_defense'], level)
        self.speed = self._calculate_stat(base_stats['speed'], level)
        self.moves = [Move(m['name'], m['type'], m['power'], m['accuracy'], m['pp'], m['damage_class']) for m in moves]
        self.status = None # e.g., 'poison', 'paralysis'
        self.is_fainted = False

    def _calculate_hp(self, base_hp, level):
        # Simplified HP calculation (Level 50 formula without EVs/IVs)
        return int(((2 * base_hp) * level) / 100 + level + 10)

    def _calculate_stat(self, base_stat, level):
         # Simplified stat calculation (Level 50 formula without EVs/IVs, non-HP)
        return int(((2 * base_stat) * level) / 100 + 5)


    def take_damage(self, damage):
        self.current_hp -= damage
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_fainted = True
            logger.info(f"{self.name} fainted!")
        logger.info(f"{self.name} took {damage} damage. Current HP: {self.current_hp}")

    def is_alive(self):
        return not self.is_fainted

class Move:
    def __init__(self, name, type, power, accuracy, pp, damage_class):
        self.name = name
        self.type = type
        self.power = power
        self.accuracy = accuracy
        self.max_pp = pp
        self.current_pp = pp
        self.damage_class = damage_class # 'physical' or 'special'

class Battle:
    def __init__(self, session_id, team1_data, team2_data):
        self.session_id = session_id
        self.team1 = [self._create_pokemon(p_name) for p_name in team1_data]
        self.team2 = [self._create_pokemon(p_name) for p_name in team2_data]
        self.current_turn = 1
        self.active_pokemon = {
            'player1': self._get_first_alive_pokemon(self.team1),
            'player2': self._get_first_alive_pokemon(self.team2)
        }
        self.player_moves = {} # Stores moves selected by players for the current turn
        self.log = [] # Battle log entries

    def _get_first_alive_pokemon(self, team):
        """Returns the first alive Pokemon in a team, or None if all are fainted."""
        for pokemon in team:
            if pokemon.is_alive():
                return pokemon
        return None


    def _create_pokemon(self, pokemon_name):
        """Creates a Pokemon instance based on data from pokemon.json."""
        pokemon_data = next((p for p in POKEMON_DATA if p['name'].lower() == pokemon_name.lower()), None)
        if pokemon_data:
            logger.info(f"Creating Pokemon: {pokemon_name}")
            return Pokemon(
                name=pokemon_data['name'],
                level=pokemon_data['level'],
                type=pokemon_data['type'],
                base_stats=pokemon_data['base_stats'],
                moves=pokemon_data['moves']
            )
        else:
            logger.warning(f"Pokemon data not found for: {pokemon_name}. Creating placeholder.")
            # Return a basic placeholder if data is not found
            return Pokemon(
                name=pokemon_name,
                level=50,
                type=["Normal"],
                base_stats={"hp": 50, "attack": 50, "defense": 50, "special_attack": 50, "special_defense": 50, "speed": 50},
                moves=[{"name": "Tackle", "type": "Normal", "power": 40, "accuracy": 100, "pp": 35, "damage_class": "physical"}]
            )


    def select_move(self, player_id, move_name):
        """Record the move selected by a player."""
        if player_id not in ['player1', 'player2']:
            logger.warning(f"Invalid player_id: {player_id}")
            return False

        active_pokemon = self.active_pokemon.get(player_id)
        if not active_pokemon:
            logger.warning(f"Player {player_id} has no active Pokemon.")
            return False

        selected_move = next((move for move in active_pokemon.moves if move.name == move_name), None)

        if selected_move and selected_move.current_pp > 0:
            self.player_moves[player_id] = selected_move
            logger.info(f"Player {player_id} selected move: {move_name}")
            return True
        else:
            logger.warning(f"Player {player_id} selected invalid or out-of-PP move: {move_name}")
            return False

    def are_moves_selected(self):
        """Check if both players have selected their moves for the turn."""
        # Check if both players have active Pokemon and have selected moves
        return self.active_pokemon.get('player1') is not None and 'player1' in self.player_moves and \
               self.active_pokemon.get('player2') is not None and 'player2' in self.player_moves


    def run_turn(self):
        """Simulate one turn of the battle."""
        if not self.are_moves_selected():
            logger.warning("Cannot run turn: Moves not selected by both players.")
            return

        logger.info(f"--- Turn {self.current_turn} ---")
        self.log.append(f"--- Turn {self.current_turn} ---")

        move1 = self.player_moves['player1']
        move2 = self.player_moves['player2']
        pokemon1 = self.active_pokemon['player1']
        pokemon2 = self.active_pokemon['player2']

        # Determine turn order (based on Speed stat, then move priority - simplified)
        if pokemon1.speed > pokemon2.speed:
            first_pokemon, first_move = pokemon1, move1
            second_pokemon, second_move = pokemon2, move2
            first_player_id = 'player1'
            second_player_id = 'player2'
        elif pokemon2.speed > pokemon1.speed:
            first_pokemon, first_move = pokemon2, move2
            second_pokemon, second_move = pokemon1, move1
            first_player_id = 'player2'
            second_player_id = 'player1'
        else: # Tie in speed, random order
            if random.random() > 0.5:
                first_pokemon, first_move = pokemon1, move1
                second_pokemon, second_move = pokemon2, move2
                first_player_id = 'player1'
                second_player_id = 'player2'
            else:
                first_pokemon, first_move = pokemon2, move2
                second_pokemon, second_move = pokemon1, move1
                first_player_id = 'player2'
                second_player_id = 'player1'


        # Execute first move
        if first_pokemon.is_alive():
             self._execute_move(first_pokemon, second_pokemon, first_move, first_player_id)

        # Execute second move if the target is still alive
        if second_pokemon.is_alive() and second_move: # Check if second_move exists (could be None if first move caused switch)
            self._execute_move(second_pokemon, first_pokemon, second_move, second_player_id)

        # Check for fainted Pokemon and handle switches (simplified for now)
        self._check_fainted()

        # Clear selected moves for the next turn
        self.player_moves = {}
        self.current_turn += 1
        logger.info(f"--- End of Turn {self.current_turn - 1} ---")
        self.log.append(f"--- End of Turn {self.current_turn - 1} ---")


    def _execute_move(self, attacker, defender, move, player_id):
        """Execute a single move."""
        logger.info(f"{attacker.name} used {move.name}!")
        self.log.append(f"{attacker.name} used {move.name}!")

        move.current_pp -= 1 # Deduct PP

        # TODO: Implement accuracy check
        # TODO: Implement type effectiveness
        # TODO: Implement critical hits, random damage variation, STAB, etc.

        # Simplified damage calculation (based on stats, types, power, damage_class)
        if move.power > 0: # Only calculate damage for attacking moves
            if move.damage_class == 'physical':
                attack_stat = attacker.attack
                defense_stat = defender.defense
            else: # special
                attack_stat = attacker.special_attack
                defense_stat = defender.special_defense

            # Basic damage formula: (((2 * Level / 5 + 2) * Power * Attack / Defense) / 50 + 2) * Modifiers
            # Simplified further for Level 50 and no modifiers initially
            damage = max(1, int((((2 * attacker.level / 5 + 2) * move.power * attack_stat / defense_stat) / 50 + 2)))

            defender.take_damage(damage)
            self.log.append(f"{defender.name} took {damage} damage.")
        else:
            # Handle non-damaging moves (e.g., stat changes, status)
            self.log.append(f"But nothing happened.") # Placeholder


    def _check_fainted(self):
        """Check for fainted Pokemon and handle switches."""
        # Simplified: Automatically switch to the next available Pokemon
        if self.active_pokemon.get('player1') and not self.active_pokemon['player1'].is_alive():
            self.active_pokemon['player1'] = self._get_first_alive_pokemon(self.team1)
            if self.active_pokemon['player1']:
                self.log.append(f"{self.active_pokemon['player1'].name} sent out!")
            else:
                self.log.append("Player 1 has no more Pokemon!")

        if self.active_pokemon.get('player2') and not self.active_pokemon['player2'].is_alive():
            self.active_pokemon['player2'] = self._get_first_alive_pokemon(self.team2)
            if self.active_pokemon['player2']:
                self.log.append(f"{self.active_pokemon['player2'].name} sent out!")
            else:
                self.log.append("Player 2 has no more Pokemon!")


    def get_battle_state(self, player_id):
        """Get the current state of the battle for a specific player."""
        if player_id == 'player1':
            player_pokemon = self.active_pokemon.get('player1')
            opponent_pokemon = self.active_pokemon.get('player2')
            # Determine if it's this player's turn to select a move
            # This is true if they have an active Pokemon and haven't selected a move yet for the current turn
            is_player_turn = player_pokemon is not None and player_id not in self.player_moves
        elif player_id == 'player2':
            player_pokemon = self.active_pokemon.get('player2')
            opponent_pokemon = self.active_pokemon.get('player1')
            # Determine if it's this player's turn to select a move
            is_player_turn = player_pokemon is not None and player_id not in self.player_moves
        else:
            return None # Invalid player_id

        state = {
            'session_id': self.session_id,
            'current_turn': self.current_turn,
            'player_pokemon': {
                'name': player_pokemon.name,
                'current_hp': player_pokemon.current_hp,
                'max_hp': player_pokemon.max_hp,
                'moves': [{'name': m.name, 'current_pp': m.current_pp, 'max_pp': m.max_pp} for m in player_pokemon.moves] # Include move details
            } if player_pokemon else None,
            'opponent_pokemon': {
                 'name': opponent_pokemon.name,
                'current_hp': opponent_pokemon.current_hp,
                'max_hp': opponent_pokemon.max_hp,
                 # Don't send opponent's moves initially for realism
            } if opponent_pokemon else None,
            'is_player_turn': is_player_turn,
            'status': 'Your turn' if is_player_turn else 'Opponent\'s turn',
            'log_entries': list(self.log) # Send a copy of the log entries
            # TODO: Add more state information as needed (e.g., status effects, weather)
        }
        # self.log = [] # DO NOT Clear log here - clear it in app.py after sending to both players
        return state

    def clear_log(self):
        """Clears the battle log."""
        self.log = []
        logger.info("Battle log cleared.")

    def is_battle_over(self):
        """Check if the battle is over."""
        # Battle is over if either player has no more alive Pokemon
        player1_has_pokemon = any(p.is_alive() for p in self.team1)
        player2_has_pokemon = any(p.is_alive() for p in self.team2)

        if not player1_has_pokemon:
            self.log.append("Player 1 has no more Pokemon!")
            self.log.append("Player 2 wins!")
            return True
        elif not player2_has_pokemon:
            self.log.append("Player 2 has no more Pokemon!")
            self.log.append("Player 1 wins!")
            return True
        else:
            return False
