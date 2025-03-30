from flask import Flask, render_template, jsonify
from pokemon_service import PokemonService

app = Flask(__name__)
pokemon_service = PokemonService()

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True)
