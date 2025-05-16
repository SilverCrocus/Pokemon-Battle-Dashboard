import random
import requests
import urllib3
from typing import Dict, List, Tuple, Any, Optional
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_session():
    """Create a requests session with retry strategy."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

class PokemonService:
    def __init__(self):
        self.base_url = "https://pokeapi.co/api/v2/"
        self.total_pokemon_count = 1025  # Latest stable generation count
        self.session = create_session()
        self.pokemon_name_list = self._fetch_all_pokemon_names()  # Cache names on init
        logger.info(f"Initialized PokemonService with {len(self.pokemon_name_list)} names.")
        
        # If we couldn't fetch the list, load a fallback list
        if not self.pokemon_name_list:
            logger.warning("Using fallback Pokemon name list")
            self.pokemon_name_list = self._get_fallback_pokemon_list()
            logger.info(f"Initialized with fallback list of {len(self.pokemon_name_list)} Pokemon names.")

    def _fetch_all_pokemon_names(self) -> List[str]:
        """Fetch a list of all Pokemon names from PokeAPI with retries and fallback."""
        url = f"{self.base_url}pokemon?limit=10000"
        
        # First try with verify=True (recommended for production)
        try:
            response = self.session.get(url, verify=True, timeout=10)
            response.raise_for_status()
            return self._process_pokemon_list_response(response)
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"First attempt failed with SSL verification: {e}")
            
        # If that fails, try without SSL verification (for development)
        try:
            response = self.session.get(url, verify=False, timeout=10)
            response.raise_for_status()
            return self._process_pokemon_list_response(response)
        except Exception as e:
            logger.error(f"Failed to fetch Pokemon list after retries: {e}")
            return []
    
    def _process_pokemon_list_response(self, response) -> List[str]:
        """Process the response from the Pokemon list endpoint."""
        try:
            data = response.json()
            results = data.get('results', [])
            all_names = [p['name'] for p in results]
            
            # Handle pagination if needed
            next_url = data.get('next')
            while next_url:
                response = self.session.get(next_url, verify=False, timeout=10)
                response.raise_for_status()
                page_data = response.json()
                all_names.extend([p['name'] for p in page_data.get('results', [])])
                next_url = page_data.get('next')
            
            logger.info(f"Fetched {len(all_names)} Pokemon names.")
            return sorted(all_names)
        except (ValueError, KeyError) as e:
            logger.error(f"Error processing Pokemon list response: {e}")
            return []
    
    def _get_fallback_pokemon_list(self) -> List[str]:
        """Return a fallback list of Pokemon names if the API is unavailable."""
        return [
            'bulbasaur', 'ivysaur', 'venusaur', 'charmander', 'charmeleon', 'charizard',
            'squirtle', 'wartortle', 'blastoise', 'caterpie', 'metapod', 'butterfree',
            'pikachu', 'raichu', 'sandshrew', 'sandslash', 'nidoran-f', 'nidorina',
            'nidoqueen', 'nidoran-m', 'nidorino', 'nidoking', 'clefairy', 'clefable',
            'vulpix', 'ninetales', 'jigglypuff', 'wigglytuff', 'zubat', 'golbat'
            # Add more common Pokemon as needed
        ]

    def get_all_pokemon_names(self) -> List[str]:
        """Return the cached list of Pokemon names."""
        return self.pokemon_name_list

    def get_random_pokemon_ids(self, count: int = 6) -> List[int]:
        """Generate random Pokemon IDs."""
        return [random.randint(1, self.total_pokemon_count) for _ in range(count)]
    
    def get_pokemon_data(self, pokemon_id: int) -> Dict[str, Any]:
        """Fetch data for a specific Pokemon by ID with retry logic."""
        url = f"{self.base_url}pokemon/{pokemon_id}"
        
        # First try with SSL verification
        try:
            response = self.session.get(url, verify=True, timeout=10)
            response.raise_for_status()
            return self._process_pokemon_data(response.json())
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"First attempt failed for Pokemon ID {pokemon_id} with SSL: {e}")
        
        # Fallback to non-SSL if first attempt fails
        try:
            response = self.session.get(url, verify=False, timeout=10)
            response.raise_for_status()
            return self._process_pokemon_data(response.json())
        except Exception as e:
            logger.error(f"Failed to fetch Pokemon ID {pokemon_id} after retries: {e}")
            return None
    
    def _process_pokemon_data(self, data: dict) -> Optional[Dict[str, Any]]:
        """Process Pokemon data from the API response."""
        try:
            pokemon = {
                'id': data['id'],
                'name': data['name'].capitalize(),
                'sprite': (data['sprites'].get('other', {}).get('official-artwork', {}).get('front_default') or 
                          data['sprites'].get('front_default')),
                'stats': {stat['stat']['name']: stat['base_stat'] for stat in data['stats']},
                'types': [t['type']['name'] for t in data['types']]
            }
            pokemon['total_stats'] = sum(pokemon['stats'].values())
            return pokemon
        except (KeyError, TypeError) as e:
            logger.error(f"Error processing Pokemon data: {e}")
            return None

    def get_pokemon_data_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific Pokemon by name with retry logic."""
        if not name:
            return None
            
        # Clean and normalize the name
        name = name.strip().lower()
        
        # First try with SSL verification
        try:
            response = self.session.get(
                f"{self.base_url}pokemon/{name}",
                verify=True,
                timeout=10
            )
            response.raise_for_status()
            return self._process_pokemon_data(response.json())
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Pokemon not found: {name}")
                return None
            logger.warning(f"First attempt failed for Pokemon {name} with SSL: {e}")
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"First attempt failed for Pokemon {name} with error: {e}")
        
        # Fallback to non-SSL if first attempt fails
        try:
            response = self.session.get(
                f"{self.base_url}pokemon/{name}",
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            return self._process_pokemon_data(response.json())
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Pokemon not found (retry): {name}")
            else:
                logger.error(f"HTTP error fetching Pokemon {name} (retry): {e}")
        except Exception as e:
            logger.error(f"Failed to fetch Pokemon {name} after retries: {e}")
        
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
