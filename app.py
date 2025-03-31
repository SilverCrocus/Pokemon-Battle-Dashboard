from flask import Flask, render_template, jsonify, request
from pokemon_service import PokemonService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.route('/manual_setup')
def manual_setup():
    """Render the manual team setup page."""
    logger.info("Rendering manual setup page.")
    return render_template('manual_setup.html')

if __name__ == '__main__':
    # Consider adding host='0.0.0.0' if running in a container or need external access
    app.run(debug=True)
