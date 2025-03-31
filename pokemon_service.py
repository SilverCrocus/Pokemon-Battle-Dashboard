import random
import requests
from typing import Dict, List, Tuple, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PokemonService:
    def __init__(self):
        self.base_url = "https://pokeapi.co/api/v2/"
        # Increased limit to potentially cover more Pokemon, adjust if needed
        self.total_pokemon_count = 1118 
        self.pokemon_name_list = self._fetch_all_pokemon_names() # Cache names on init
        logger.info(f"Initialized PokemonService with {len(self.pokemon_name_list)} names.")

    def _fetch_all_pokemon_names(self) -> List[str]:
        """Fetch a list of all Pokemon names from PokeAPI."""
        all_names = []
        url = f"{self.base_url}pokemon?limit=10000" # Fetch a large batch initially
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            results = data.get('results', [])
            all_names.extend([p['name'] for p in results])
            
            # PokeAPI might paginate even with a large limit, though unlikely for just names
            # If needed, add pagination logic here based on data['next']

            logger.info(f"Fetched {len(all_names)} Pokemon names.")
            return sorted(all_names)
        except requests.RequestException as e:
            logger.error(f"Error fetching Pokemon list: {e}")
            return [] # Return empty list on error
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching Pokemon names: {e}")
            return []

    def get_all_pokemon_names(self) -> List[str]:
        """Return the cached list of Pokemon names."""
        return self.pokemon_name_list

    def get_random_pokemon_ids(self, count: int = 6) -> List[int]:
        """Generate random Pokemon IDs."""
        return [random.randint(1, self.total_pokemon_count) for _ in range(count)]
    
    def get_pokemon_data(self, pokemon_id: int) -> Dict[str, Any]:
        """Fetch data for a specific Pokemon by ID."""
        try:
            response = requests.get(f"{self.base_url}pokemon/{pokemon_id}")
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
            logger.error(f"Error fetching Pokemon ID {pokemon_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching Pokemon ID {pokemon_id}: {e}")
            return None

    def get_pokemon_data_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific Pokemon by name."""
        if not name:
            return None
        try:
            # PokeAPI uses lowercase names in URLs
            response = requests.get(f"{self.base_url}pokemon/{name.lower()}")
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
                logger.warning(f"Pokemon not found: {name}")
            else:
                logger.error(f"HTTP error fetching Pokemon '{name}': {e}")
            return None
        except requests.RequestException as e:
            logger.error(f"Request error fetching Pokemon '{name}': {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching Pokemon '{name}': {e}")
            return None

    def generate_battle(self) -> Dict[str, Any]:
        """Generate a complete battle between two players."""
        # Generate random Pokemon for each player
        player1_ids = self.get_random_pokemon_ids()
        player2_ids = self.get_random_pokemon_ids()
        
        # Get Pokemon data
        player1_pokemon = [self.get_pokemon_data(pid) for pid in player1_ids]
        player2_pokemon = [self.get_pokemon_data(pid) for pid in player2_ids]
        
        # Filter out any failed requests
        player1_pokemon = [p for p in player1_pokemon if p]
        player2_pokemon = [p for p in player2_pokemon if p]
        
        # Calculate total scores
        player1_score = sum(p['total_stats'] for p in player1_pokemon)
        player2_score = sum(p['total_stats'] for p in player2_pokemon)
        
        # Determine winner
        if player1_score > player2_score:
            winner = "Player 1"
        elif player2_score > player1_score:
            winner = "Player 2"
        else:
            winner = "Tie"
            
        return {
            "player1": {
                "pokemon": player1_pokemon,
                "score": player1_score
            },
            "player2": {
                "pokemon": player2_pokemon,
                "score": player2_score
            },
            "winner": winner
        }
