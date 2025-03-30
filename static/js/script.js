document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const newBattleBtn = document.getElementById('new-battle-btn');
    const loadingElement = document.getElementById('loading');
    const battleContainer = document.getElementById('battle-container');
    const player1Pokemon = document.getElementById('player1-pokemon');
    const player2Pokemon = document.getElementById('player2-pokemon');
    const player1Score = document.getElementById('player1-score');
    const player2Score = document.getElementById('player2-score');
    const winnerBanner = document.getElementById('winner-banner');
    const pokemonCardTemplate = document.getElementById('pokemon-card-template');

    // Type colors for badges
    const typeColors = {
        normal: '#A8A878',
        fire: '#F08030',
        water: '#6890F0',
        electric: '#F8D030',
        grass: '#78C850',
        ice: '#98D8D8',
        fighting: '#C03028',
        poison: '#A040A0',
        ground: '#E0C068',
        flying: '#A890F0',
        psychic: '#F85888',
        bug: '#A8B820',
        rock: '#B8A038',
        ghost: '#705898',
        dragon: '#7038F8',
        dark: '#705848',
        steel: '#B8B8D0',
        fairy: '#EE99AC'
    };

    // Generate a new battle
    function generateBattle() {
        // Show loading, hide battle
        loadingElement.style.display = 'flex';
        battleContainer.style.display = 'none';
        
        // Clear previous Pokemon
        player1Pokemon.innerHTML = '';
        player2Pokemon.innerHTML = '';
        
        // Fetch new battle data
        fetch('/api/battle')
            .then(response => response.json())
            .then(data => {
                // Hide loading, show battle
                loadingElement.style.display = 'none';
                battleContainer.style.display = 'block';
                
                // Render Pokemon for each player
                data.player1.pokemon.forEach(pokemon => {
                    const card = createPokemonCard(pokemon);
                    player1Pokemon.appendChild(card);
                });
                
                data.player2.pokemon.forEach(pokemon => {
                    const card = createPokemonCard(pokemon);
                    player2Pokemon.appendChild(card);
                });
                
                // Update scores
                player1Score.textContent = data.player1.score;
                player2Score.textContent = data.player2.score;
                
                // Show winner
                if (data.winner === 'Tie') {
                    winnerBanner.textContent = "It's a tie!";
                } else {
                    winnerBanner.textContent = `${data.winner} wins!`;
                }
                winnerBanner.style.display = 'block';
            })
            .catch(error => {
                console.error('Error generating battle:', error);
                loadingElement.style.display = 'none';
                alert('Error generating battle. Please try again.');
            });
    }
    
    // Create a Pokemon card element
    function createPokemonCard(pokemon) {
        const card = pokemonCardTemplate.content.cloneNode(true);
        
        // Set image
        const img = card.querySelector('.pokemon-image img');
        img.src = pokemon.sprite;
        img.alt = pokemon.name;
        
        // Set name
        card.querySelector('.pokemon-name').textContent = pokemon.name;
        
        // Set types
        const typesContainer = card.querySelector('.pokemon-types');
        pokemon.types.forEach(type => {
            const typeElement = document.createElement('span');
            typeElement.className = 'type-badge';
            typeElement.textContent = type;
            typeElement.style.backgroundColor = typeColors[type] || '#AAA';
            typesContainer.appendChild(typeElement);
        });
        
        // Set stats
        card.querySelector('.stat.hp').textContent = `HP: ${pokemon.stats.hp}`;
        card.querySelector('.stat.attack').textContent = `Atk: ${pokemon.stats.attack}`;
        card.querySelector('.stat.defense').textContent = `Def: ${pokemon.stats.defense}`;
        card.querySelector('.stat.special-attack').textContent = `SpA: ${pokemon.stats['special-attack']}`;
        card.querySelector('.stat.special-defense').textContent = `SpD: ${pokemon.stats['special-defense']}`;
        card.querySelector('.stat.speed').textContent = `Spd: ${pokemon.stats.speed}`;
        card.querySelector('.stat.total').textContent = `Total: ${pokemon.total_stats}`;
        
        return card;
    }
    
    // Event listeners
    newBattleBtn.addEventListener('click', generateBattle);
    
    // Generate initial battle on page load
    generateBattle();
});
