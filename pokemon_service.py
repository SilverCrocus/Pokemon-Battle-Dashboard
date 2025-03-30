import random
import requests
from typing import Dict, List, Tuple, Any

class PokemonService:
    def __init__(self):
        self.base_url = "https://pokeapi.co/api/v2/"
        self.total_pokemon_count = 898  # Limiting to first 898 Pokemon for better reliability
    
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
            print(f"Error fetching Pokemon {pokemon_id}: {e}")
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
