import random
import requests
from typing import Dict, List, Tuple, Any, Optional
import logging
# import json # No longer needed for loading local data
# import os # No longer needed for local file paths

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PokemonService:
    def __init__(self):
        self.base_url = "https://pokeapi.co/api/v2/"
        # Changed from 1118 to 1025 to avoid 404 errors
        self.total_pokemon_count = 1025
        self.pokemon_name_list = self._fetch_all_pokemon_names() # Fetch names from PokeAPI on init
        logger.info(f"Initialized PokemonService with {len(self.pokemon_name_list)} names from PokeAPI.")

    def _fetch_all_pokemon_names(self) -> List[str]:
        """Fetch a list of all Pokemon names from PokeAPI."""
        all_names = []
        url = f"{self.base_url}pokemon?limit=10000" # Fetch a large batch initially
        try:
            response = requests.get(url, verify=False) # Disable SSL verification
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            all_names.extend([p['name'] for p in results])

            # PokeAPI might paginate even with a large limit, though unlikely for just names
            # If needed, add pagination logic here based on data['next']

            logger.info(f"Fetched {len(all_names)} Pokemon names from PokeAPI.")
            return sorted(all_names)
        except requests.RequestException as e:
            logger.error(f"Error fetching Pokemon list from PokeAPI: {e}")
            return [] # Return empty list on error
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching Pokemon names from PokeAPI: {e}")
            return []

    # Removed _load_pokemon_data as we are now using PokeAPI for the full list

    def get_all_pokemon_names(self) -> List[str]:
        """Return the cached list of Pokemon names fetched from PokeAPI."""
        return self.pokemon_name_list

    def get_random_pokemon_ids(self, count: int = 6) -> List[int]:
        """Generate random Pokemon IDs (still using PokeAPI range for now)."""
        # This method is not used for the new battle simulator team selection,
        # but keeping it for potential future use or other parts of the app.
        return [random.randint(1, self.total_pokemon_count) for _ in range(count)]

    def get_pokemon_data(self, pokemon_id: int) -> Dict[str, Any]:
        """Fetch data for a specific Pokemon by ID from PokeAPI."""
        # This method is not used for the new battle simulator battle logic currently,
        # but keeping it for potential future use or other parts of the app.
        try:
            response = requests.get(f"{self.base_url}pokemon/{pokemon_id}", verify=False) # Disable SSL verification
            response.raise_for_status()
            data = response.json()

            # Extract relevant information
            pokemon = {
                'id': data['id'],
                'name': data['name'].capitalize(),
                'sprite': data['sprites']['other']['official-artwork']['front_default']
                         or data['sprites']['front_default'],
                'stats': {stat['stat']['name']: stat['base_stat'] for stat in data['stats']},
                'types': [t['type']['name'] for t in data['types']]
            }

            # Calculate total stats
            pokemon['total_stats'] = sum(pokemon['stats'].values())

            return pokemon
        except requests.RequestException as e:
            logger.error(f"Error fetching Pokemon ID {pokemon_id} from PokeAPI: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching Pokemon ID {pokemon_id} from PokeAPI: {e}")
            return None


    def get_pokemon_data_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific Pokemon by name from PokeAPI."""
        if not name:
            return None
        try:
            # PokeAPI uses lowercase names in URLs
            response = requests.get(f"{self.base_url}pokemon/{name.lower()}", verify=False) # Disable SSL verification
            response.raise_for_status() # Will raise HTTPError for 404 Not Found
            data = response.json()

            # Extract relevant information (same structure as get_pokemon_data)
            pokemon = {
                'id': data['id'],
                'name': data['name'].capitalize(),
                'sprite': data['sprites']['other']['official-artwork']['front_default']
                         or data['sprites']['front_default'],
                'stats': {stat['stat']['name']: stat['base_stat'] for stat in data['stats']},
                'types': [t['type']['name'] for t in data['types']]
            }

            # Calculate total stats
            pokemon['total_stats'] = sum(pokemon['stats'].values())

            return pokemon
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Pokemon not found on PokeAPI: {name}")
            else:
                logger.error(f"HTTP error fetching Pokemon '{name}' from PokeAPI: {e}")
            return None
        except requests.RequestException as e:
            logger.error(f"Request error fetching Pokemon '{name}' from PokeAPI: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching Pokemon '{name}' from PokeAPI: {e}")
            return None


    def generate_battle(self) -> Dict[str, Any]:
        """Generate a complete battle between two players (using PokeAPI data)."""
        # Select random Pokemon names from the fetched list
        if len(self.pokemon_name_list) < 12:
            logger.error("Not enough Pokemon names fetched from PokeAPI to generate a battle.")
            return {"error": "Not enough Pokemon data available."}

        player1_names = random.sample(self.pokemon_name_list, 6)
        player2_names = random.sample(self.pokemon_name_list, 6)

        # For the battle logic, we need more than just names.
        # We should fetch the full data for the selected Pokemon from PokeAPI.
        # This is a more significant change and will require updating battle_logic.py
        # For now, I will return a simplified structure with just names,
        # and we can implement fetching full data for battle later.

        # TODO: Update this to fetch full Pokemon data for the selected teams from PokeAPI
        # For now, returning just names as a placeholder for the battle structure
        player1_pokemon_data = [{'name': name} for name in player1_names]
        player2_pokemon_data = [{'name': name} for name in player2_names]


        # The concept of 'score' based on total stats is from the original random battle,
        # and might not be relevant for the new simulator.
        # Removing score calculation for the new battle type.

        return {
            "player1": {
                "pokemon": player1_pokemon_data
            },
            "player2": {
                "pokemon": player2_pokemon_data
            }
            # Removing winner as it's a real-time battle
        }
