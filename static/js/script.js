document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing Pokemon Battle Dashboard');
    
    // DOM elements - Setup
    const setupForm = document.getElementById('setup-form');
    const startBattleBtn = document.getElementById('start-battle-btn');
    const player1NameInput = document.getElementById('player1-name');
    const player2NameInput = document.getElementById('player2-name');
    const autoRevealRadio = document.getElementById('auto-reveal');
    
    // DOM elements - Battle
    const loadingElement = document.getElementById('loading');
    const battleContainer = document.getElementById('battle-container');
    const revealNextBtn = document.getElementById('reveal-next-btn');
    const revealAllBtn = document.getElementById('reveal-all-btn');
    const newBattleBtn = document.getElementById('new-battle-btn');
    const player1Pokemon = document.getElementById('player1-pokemon');
    const player2Pokemon = document.getElementById('player2-pokemon');
    const player1Score = document.getElementById('player1-score');
    const player2Score = document.getElementById('player2-score');
    const fixedPlayer1Score = document.getElementById('fixed-player1-score');
    const fixedPlayer2Score = document.getElementById('fixed-player2-score');
    const fixedPlayer1Name = document.getElementById('fixed-player1-name');
    const fixedPlayer2Name = document.getElementById('fixed-player2-name');
    const player1Header = document.getElementById('player1-header');
    const player2Header = document.getElementById('player2-header');
    const winnerBanner = document.getElementById('winner-banner');
    const revealProgressText = document.getElementById('reveal-progress-text');
    const progressFill = document.getElementById('progress-fill');
    const pokemonCardTemplate = document.getElementById('pokemon-card-template');
    const battleStatus = document.getElementById('battle-status');
    
    // Log which elements we couldn't find
    if (!startBattleBtn) console.error('Could not find start battle button!');
    if (!setupForm) console.error('Could not find setup form!');
    
    // Battle state
    let battleData = null;
    let revealedCount = 0;
    let totalPokemonPerPlayer = 6; // Default count per player
    let player1CurrentScore = 0;
    let player2CurrentScore = 0;
    let revealInterval = null;
    let player1Name = "Player 1";
    let player2Name = "Player 2";
    let isAutoReveal = true;
    let pokemonList1 = []; // renamed from player1Pokemon to avoid conflict with DOM element
    let pokemonList2 = []; // renamed from player2Pokemon to avoid conflict with DOM element

    // Battle statistics
    let battleStats = {
        totalBattles: 0,
        playerWins: {}
    };

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

    // Load stats from localStorage
    function loadBattleStats() {
        const storedStats = localStorage.getItem('pokemonBattleStats');
        if (storedStats) {
            battleStats = JSON.parse(storedStats);
        }
    }

    // Save stats to localStorage
    function saveBattleStats() {
        localStorage.setItem('pokemonBattleStats', JSON.stringify(battleStats));
    }

    // Update stats when battle ends
    function updateBattleStats(winner) {
        battleStats.totalBattles++;
        if (winner !== "It's a tie") {
            if (!battleStats.playerWins[winner]) {
                battleStats.playerWins[winner] = 0;
            }
            battleStats.playerWins[winner]++;
        }
        saveBattleStats();
        displayBattleStats();
    }

    // Display battle stats in a new section
    function displayBattleStats() {
        // Implementation depends on where you want to show these stats
    }

    // Start a new battle - MAIN FUNCTION THAT NEEDS TO WORK
    function startBattle() {
        console.log('Starting battle...');
        
        // Get player names and reveal mode
        player1Name = player1NameInput.value || "Player 1";
        player2Name = player2NameInput.value || "Player 2";
        isAutoReveal = autoRevealRadio.checked;

        // Update player headers and fixed scoreboard
        player1Header.textContent = player1Name;
        player2Header.textContent = player2Name;
        
        if (fixedPlayer1Name) fixedPlayer1Name.textContent = player1Name;
        if (fixedPlayer2Name) fixedPlayer2Name.textContent = player2Name;

        // Set up reveal button based on mode
        if (revealNextBtn) {
            revealNextBtn.style.display = isAutoReveal ? 'none' : 'inline-block';
        }

        // Hide setup, show loading
        setupForm.style.display = 'none';
        loadingElement.style.display = 'flex';
        battleContainer.style.display = 'none';
        
        // Reset state
        revealedCount = 0;
        player1CurrentScore = 0;
        player2CurrentScore = 0;
        pokemonList1 = [];
        pokemonList2 = [];
        
        // Clear previous Pokemon
        player1Pokemon.innerHTML = '';
        player2Pokemon.innerHTML = '';
        
        // Reset scores
        player1Score.textContent = '0';
        player2Score.textContent = '0';
        
        if (fixedPlayer1Score) fixedPlayer1Score.textContent = '0';
        if (fixedPlayer2Score) fixedPlayer2Score.textContent = '0';
        
        // Hide winner banner
        winnerBanner.style.display = 'none';
        
        console.log('Fetching battle data...');
        
        // Fetch new battle data
        fetch('/api/battle')
            .then(response => {
                console.log('API Response:', response);
                return response.json();
            })
            .then(data => {
                console.log('Battle data received:', data);
                // Store battle data
                battleData = data;
                
                // Store Pokemon data
                pokemonList1 = data.player1.pokemon;
                pokemonList2 = data.player2.pokemon;
                
                // Update total counts
                totalPokemonPerPlayer = Math.max(pokemonList1.length, pokemonList2.length);
                
                // Update progress
                updateRevealProgress();
                
                // Hide loading, show battle
                loadingElement.style.display = 'none';
                battleContainer.style.display = 'block';
                
                // Create placeholders for all Pokemon cards
                createPokemonPlaceholders();
                
                // If auto-reveal is enabled, start revealing
                if (isAutoReveal) {
                    startAutoReveal();
                }
            })
            .catch(error => {
                console.error('Error generating battle:', error);
                loadingElement.style.display = 'none';
                setupForm.style.display = 'block';
                alert('Error generating battle. Please try again.');
            });
    }

    // Create placeholders for all Pokemon cards
    function createPokemonPlaceholders() {
        console.log('Creating placeholders...');
        
        // Create exactly the number of placeholders needed for each player
        for (let i = 0; i < pokemonList1.length; i++) {
            const card = createEmptyPokemonCard(1, i);
            player1Pokemon.appendChild(card);
        }
        
        for (let i = 0; i < pokemonList2.length; i++) {
            const card = createEmptyPokemonCard(2, i);
            player2Pokemon.appendChild(card);
        }
        
        // Update the total count for progress tracking
        totalPokemonPerPlayer = Math.max(pokemonList1.length, pokemonList2.length);
    }
    
    // Create an empty card placeholder
    function createEmptyPokemonCard(playerNum, index) {
        const card = pokemonCardTemplate.content.cloneNode(true);
        const cardElement = card.querySelector('.pokemon-card');
        
        // Add identifiers for later reference
        cardElement.classList.add(`player-${playerNum}-card`);
        cardElement.dataset.index = index;
        cardElement.dataset.player = playerNum;
        
        return cardElement;
    }
    
    // Reveal next Pokemon
    function revealNextPokemon() {
        if (revealedCount >= totalPokemonPerPlayer * 2) return;
        
        // Alternate between players
        const currentPlayerNum = (revealedCount % 2) + 1;
        const pokemonIndex = Math.floor(revealedCount / 2);
        
        // Get the corresponding Pokemon data
        let pokemonData;
        if (currentPlayerNum === 1 && pokemonIndex < pokemonList1.length) {
            pokemonData = pokemonList1[pokemonIndex];
        } else if (currentPlayerNum === 2 && pokemonIndex < pokemonList2.length) {
            pokemonData = pokemonList2[pokemonIndex];
        } else {
            // Skip if we don't have data for this slot
            revealedCount++;
            updateRevealProgress();
            return;
        }
        
        // Find the card element to update
        const selector = `.player-${currentPlayerNum}-card[data-index="${pokemonIndex}"]`;
        const cardElement = document.querySelector(selector);
        
        if (cardElement) {
            // Update card with Pokemon data
            updatePokemonCard(cardElement, pokemonData);
            
            // Reveal the card
            cardElement.classList.remove('hidden');
            cardElement.classList.add('revealed');
            
            // Scroll to the card
            cardElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // Update score with visual feedback
            if (currentPlayerNum === 1) {
                player1CurrentScore += pokemonData.total_stats;
                
                // Update both score displays
                player1Score.textContent = player1CurrentScore;
                if (fixedPlayer1Score) {
                    fixedPlayer1Score.textContent = player1CurrentScore;
                    fixedPlayer1Score.classList.add('updated');
                    setTimeout(() => fixedPlayer1Score.classList.remove('updated'), 1000);
                }
                
                // Visual feedback for in-section score
                player1Score.parentElement.classList.add('updated');
                setTimeout(() => player1Score.parentElement.classList.remove('updated'), 1000);
                
                // Update leading indicator
                if (fixedPlayer1Score && fixedPlayer2Score) {
                    updateLeadingPlayer();
                }
            } else {
                player2CurrentScore += pokemonData.total_stats;
                
                // Update both score displays
                player2Score.textContent = player2CurrentScore;
                if (fixedPlayer2Score) {
                    fixedPlayer2Score.textContent = player2CurrentScore;
                    fixedPlayer2Score.classList.add('updated');
                    setTimeout(() => fixedPlayer2Score.classList.remove('updated'), 1000);
                }
                
                // Visual feedback for in-section score
                player2Score.parentElement.classList.add('updated');
                setTimeout(() => player2Score.parentElement.classList.remove('updated'), 1000);
                
                // Update leading indicator
                if (fixedPlayer1Score && fixedPlayer2Score) {
                    updateLeadingPlayer();
                }
            }
        }
        
        // Increment revealed count and update progress
        revealedCount++;
        updateRevealProgress();
        
        // Check if all Pokemon have been revealed - WITH DELAY FOR LAST ONE
        if (revealedCount >= (pokemonList1.length + pokemonList2.length)) {
            // Add delay before showing the winner to let users see the last Pokemon
            setTimeout(() => {
                finalizeBattle();
            }, 2500); // 2.5 second delay
        }
    }
    
    // Start auto-revealing Pokemon
    function startAutoReveal() {
        if (revealInterval) clearInterval(revealInterval);
        revealInterval = setInterval(() => {
            revealNextPokemon();
            if (revealedCount >= totalPokemonPerPlayer * 2) {
                clearInterval(revealInterval);
            }
        }, 2000); // Reveal every 2 seconds
    }
    
    // Update a Pokemon card with real data
    function updatePokemonCard(cardElement, pokemon) {
        // Set image
        const img = cardElement.querySelector('.pokemon-image img');
        img.src = pokemon.sprite;
        img.alt = pokemon.name;
        
        // Set name
        cardElement.querySelector('.pokemon-name').textContent = pokemon.name;
        
        // Set types
        const typesContainer = cardElement.querySelector('.pokemon-types');
        typesContainer.innerHTML = ''; // Clear previous types
        pokemon.types.forEach(type => {
            const typeElement = document.createElement('span');
            typeElement.className = 'type-badge';
            typeElement.textContent = type;
            typeElement.style.backgroundColor = typeColors[type] || '#AAA';
            typesContainer.appendChild(typeElement);
        });
        
        // Set stats
        cardElement.querySelector('.stat.hp').textContent = `HP: ${pokemon.stats.hp}`;
        cardElement.querySelector('.stat.attack').textContent = `Atk: ${pokemon.stats.attack}`;
        cardElement.querySelector('.stat.defense').textContent = `Def: ${pokemon.stats.defense}`;
        cardElement.querySelector('.stat.special-attack').textContent = `SpA: ${pokemon.stats['special-attack']}`;
        cardElement.querySelector('.stat.special-defense').textContent = `SpD: ${pokemon.stats['special-defense']}`;
        cardElement.querySelector('.stat.speed').textContent = `Spd: ${pokemon.stats.speed}`;
        cardElement.querySelector('.stat.total').textContent = `Total: ${pokemon.total_stats}`;
    }
    
    // Update the reveal progress
    function updateRevealProgress() {
        const totalCards = pokemonList1.length + pokemonList2.length;
        revealProgressText.textContent = `Revealing: ${revealedCount}/${totalCards} Pokemon`;
        const progressPercent = (revealedCount / totalCards) * 100;
        progressFill.style.width = `${progressPercent}%`;
    }
    
    // Finalize the battle and show the winner
    function finalizeBattle() {
        // Determine winner based on current scores
        let winner;
        if (player1CurrentScore > player2CurrentScore) {
            winner = player1Name;
        } else if (player2CurrentScore > player1CurrentScore) {
            winner = player2Name;
        } else {
            winner = "It's a tie";
        }
        
        // Update and show winner banner
        winnerBanner.textContent = winner === "It's a tie" ? winner : `${winner} wins!`;
        winnerBanner.style.display = 'block';
        winnerBanner.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Add celebration effect if there's a winner
        if (winner !== "It's a tie") {
            createConfetti();
        }
        
        // Disable reveal buttons
        revealNextBtn.disabled = true;
        revealAllBtn.disabled = true;
        
        // Update battle stats
        updateBattleStats(winner);
    }
    
    // Reveal all remaining Pokemon
    function revealAllPokemon() {
        if (revealInterval) clearInterval(revealInterval);
        
        const remainingCount = (pokemonList1.length + pokemonList2.length) - revealedCount;
        
        if (remainingCount <= 0) return;
        
        // Reveal them one by one with a short delay between each
        let revealed = 0;
        const revealOne = () => {
            revealNextPokemon();
            revealed++;
            
            if (revealed < remainingCount) {
                setTimeout(revealOne, 300); // 300ms between reveals when "Reveal All" is clicked
            }
        };
        
        revealOne();
    }
    
    // Update which player is leading
    function updateLeadingPlayer() {
        if (!fixedPlayer1Score || !fixedPlayer2Score) return;
        
        const player1ScoreEl = fixedPlayer1Score.parentElement;
        const player2ScoreEl = fixedPlayer2Score.parentElement;
        
        player1ScoreEl.classList.remove('leading');
        player2ScoreEl.classList.remove('leading');
        
        if (player1CurrentScore > player2CurrentScore) {
            player1ScoreEl.classList.add('leading');
        } else if (player2CurrentScore > player1CurrentScore) {
            player2ScoreEl.classList.add('leading');
        }
    }
    
    // Create a simple confetti effect for the winner
    function createConfetti() {
        const confettiContainer = document.createElement('div');
        confettiContainer.className = 'confetti-container';
        battleContainer.appendChild(confettiContainer);
        
        for (let i = 0; i < 100; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.animationDelay = Math.random() * 5 + 's';
            confetti.style.backgroundColor = `hsl(${Math.random() * 360}, 100%, 50%)`;
            confettiContainer.appendChild(confetti);
        }
        
        // Remove confetti after animation
        setTimeout(() => {
            confettiContainer.remove();
        }, 10000);
    }

    // CRITICAL: Make sure we attach the event listener properly
    // Add event listeners with both approaches to ensure it works
    if (startBattleBtn) {
        console.log('Adding click handlers to start battle button');
        // Method 1: Direct property assignment
        startBattleBtn.onclick = startBattle;
        
        // Method 2: Event listener
        startBattleBtn.addEventListener('click', function() {
            console.log('Start battle button clicked!');
            startBattle();
        });
    }
    
    // Other event listeners
    if (revealNextBtn) revealNextBtn.addEventListener('click', revealNextPokemon);
    if (revealAllBtn) revealAllBtn.addEventListener('click', revealAllPokemon);
    if (newBattleBtn) {
        newBattleBtn.addEventListener('click', () => {
            if (revealInterval) clearInterval(revealInterval);
            setupForm.style.display = 'block';
            battleContainer.style.display = 'none';
            revealNextBtn.disabled = false;
            revealAllBtn.disabled = false;
        });
    }

    // Load battle stats
    loadBattleStats();

    // Log when the page is fully loaded
    console.log('DOM fully loaded and parsed');
});
