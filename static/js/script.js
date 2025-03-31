document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing Pokemon Battle Dashboard');
    
    // DOM elements - Setup
    const setupForm = document.getElementById('setup-form');
    const startBattleBtn = document.getElementById('start-battle-btn');
    const player1NameInput = document.getElementById('player1-name');
    const player2NameInput = document.getElementById('player2-name');
    const autoRevealRadio = document.getElementById('auto-reveal');
    const manualRevealRadio = document.getElementById('manual-reveal');

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
    let totalPokemonPerPlayer = 6; // Default count per player - this is fixed at 6
    let player1CurrentScore = 0;
    let player2CurrentScore = 0;
    let revealInterval = null;
    let player1Name = "Player 1";
    let player2Name = "Player 2";
    let isAutoReveal = true; // For random mode reveal
    // Removed currentBattleMode, allPokemonNames, activeAutocomplete
    let pokemonList1 = []; // Will hold Pokemon data for the current battle (random or manual)
    let pokemonList2 = []; // Will hold Pokemon data for the current battle (random or manual)
    let battleInProgress = false; // Add flag to track battle state
    let lastBattleStartTime = 0; // Track when the last battle started

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


    // Start a new RANDOM battle
    function startBattle() { // Renamed back, only handles random now
        console.log('Starting random battle...');

        // Prevent multiple rapid API calls - enforce a 3 second cooldown
        const now = Date.now();
        if (now - lastBattleStartTime < 3000) {
            console.log('Battle request ignored - too soon after previous request');
            return;
        }
        lastBattleStartTime = now;
        
        // Check if battle is already in progress
        if (battleInProgress) {
            console.log('Battle already in progress, request ignored');
            return;
        }
        
        // Set battle in progress
        battleInProgress = true;
        
        // Get player names and reveal mode for random battle
        player1Name = player1NameInput.value || "Player 1";
        player2Name = player2NameInput.value || "Player 2";
        isAutoReveal = autoRevealRadio.checked;

        // Update player headers and fixed scoreboard
        player1Header.textContent = player1Name;
        player2Header.textContent = player2Name;
        
        if (fixedPlayer1Name) fixedPlayer1Name.textContent = player1Name;
        if (fixedPlayer2Name) fixedPlayer2Name.textContent = player2Name;

        // Hide setup, show loading
        setupForm.style.display = 'none';
        loadingElement.style.display = 'flex';
        battleContainer.style.display = 'none';

        // Reset state for random battle
        revealedCount = 0;
        player1CurrentScore = 0;
        player2CurrentScore = 0;
        pokemonList1 = []; // Clear previous lists
        pokemonList2 = [];

        // Clear previous Pokemon display
        player1Pokemon.innerHTML = '';
        player2Pokemon.innerHTML = '';
        
        // Reset scores
        player1Score.textContent = '0';
        player2Score.textContent = '0';
        
        if (fixedPlayer1Score) fixedPlayer1Score.textContent = '0';
        if (fixedPlayer2Score) fixedPlayer2Score.textContent = '0';
        
        // Hide winner banner
        winnerBanner.style.display = 'none';

        // Set up reveal buttons based on mode
        if (revealNextBtn) {
            revealNextBtn.style.display = isAutoReveal ? 'none' : 'inline-block';
        }
        if (revealAllBtn) revealAllBtn.style.display = 'inline-block';

        console.log('Fetching random battle data from API...');
        // Fetch new battle data
        fetch('/api/battle') // This endpoint remains for random battles
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                console.log('Random API Response received:', response);
                return response.json();
            })
            .then(data => {
                console.log('Random battle data processed successfully');
                battleData = data; // Store raw data if needed for debugging or future features

                // Store Pokemon data from the random fetch
                pokemonList1 = (data.player1?.pokemon || []);
                pokemonList2 = (data.player2?.pokemon || []);

                // Ensure exactly 6 pokemon, pad with null if necessary (though backend should provide 6)
                while (pokemonList1.length < 6) pokemonList1.push(null);
                while (pokemonList2.length < 6) pokemonList2.push(null);
                pokemonList1 = pokemonList1.slice(0, 6);
                pokemonList2 = pokemonList2.slice(0, 6);

                // Log the actual number of Pokemon
                console.log(`Player 1 Pokemon: ${pokemonList1.filter(p => p).length}, Player 2 Pokemon: ${pokemonList2.filter(p => p).length}`);

                totalPokemonPerPlayer = 6; // Fixed count

                updateRevealProgress(); // Update progress bar

                loadingElement.style.display = 'none';
                battleContainer.style.display = 'block';

                player1Pokemon.innerHTML = ''; // Clear battle area grids
                player2Pokemon.innerHTML = '';

                createPokemonPlaceholders(); // Create placeholders in battle area

                if (isAutoReveal) {
                    startAutoReveal();
                }
            })
            .catch(error => {
                console.error('Error generating random battle:', error);
                loadingElement.style.display = 'none';
                setupForm.style.display = 'block'; // Show setup form again
                alert('Error generating random battle. Please try again.');
                battleInProgress = false; // Reset the flag on error
            });
    }


    // Create placeholders for RANDOM battle mode cards
    function createPokemonPlaceholders() {
        console.log('Creating placeholders...');
        
        // Make sure we're working with clean containers
        player1Pokemon.innerHTML = '';
        player2Pokemon.innerHTML = '';
        
        console.log(`Creating ${Math.min(pokemonList1.length, 6)} cards for Player 1`);
        console.log(`Creating ${Math.min(pokemonList2.length, 6)} cards for Player 2`);
        
        // Create exactly 6 placeholders for each player (or fewer if we have fewer Pokemon)
        for (let i = 0; i < 6; i++) {
            // Player 1 placeholder - only if we have data for this position
            if (i < pokemonList1.length) {
                const card = createEmptyPokemonCard(1, i);
                player1Pokemon.appendChild(card);
            }
            
            // Player 2 placeholder - only if we have data for this position
            if (i < pokemonList2.length) {
                const card = createEmptyPokemonCard(2, i);
                player2Pokemon.appendChild(card);
            }
        }
        
        // Log the actual number of cards created
        console.log(`Player 1 card elements: ${player1Pokemon.children.length}`);
        console.log(`Player 2 card elements: ${player2Pokemon.children.length}`);
    }
    
    // Create an empty card placeholder
    function createEmptyPokemonCard(playerNum, index) {
        const card = pokemonCardTemplate.content.cloneNode(true);
        const cardElement = card.querySelector('.pokemon-card');
        
        // Add identifiers for later reference
        cardElement.classList.add(`player-${playerNum}-card`);
        cardElement.classList.add('hidden'); // Explicitly add hidden class
        cardElement.dataset.index = index;
        cardElement.dataset.player = playerNum;
        cardElement.dataset.revealed = 'false'; // Add data attribute to track state
        
        return cardElement;
    }


    // Reveal next Pokemon (Only used in RANDOM mode reveal)
    function revealNextPokemon() {
        if (revealedCount >= totalPokemonPerPlayer * 2) return;
        
        // Block API calls during card reveals by setting a flag
        battleInProgress = true;
        
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
            // Check if already revealed based on our data attribute
            if (cardElement.dataset.revealed !== 'true') {
                console.log(`Revealing card: Player ${currentPlayerNum}, Index ${pokemonIndex}`);
                
                // Update card with Pokemon data first
                updatePokemonCard(cardElement, pokemonData);
                
                // Remove hidden class
                cardElement.classList.remove('hidden');
                
                // Add revealed class and update data attribute
                cardElement.classList.add('revealed');
                cardElement.dataset.revealed = 'true';
                
                // Add a permanent revealed class that won't be affected by transitions
                cardElement.classList.add('permanently-revealed');
                
                console.log(`Card revealed: Player ${currentPlayerNum}, Index ${pokemonIndex}`);
                
                // Check if this is the final card - if so, don't scroll to it
                // because the winner banner will scroll into view
                const isLastCard = revealedCount === (pokemonList1.length + pokemonList2.length - 1);
                if (!isLastCard) {
                    // Scroll to the card if it's not the last one
                    cardElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                
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
            } else {
                console.log(`Card already revealed: Player ${currentPlayerNum}, Index ${pokemonIndex}`);
            }
        } else {
            console.error(`Could not find card element: ${selector}`);
        }
        
        // Increment revealed count and update progress
        revealedCount++;
        updateRevealProgress();
        
        // Check if all Pokemon have been revealed
        if (revealedCount >= (pokemonList1.length + pokemonList2.length)) {
            finalizeBattle();
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
    
    // Update the reveal progress with the actual number of cards
    function updateRevealProgress() {
        // Calculate total cards from the actual number we created
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
        
        // Disable reveal buttons immediately
        revealNextBtn.disabled = true;
        revealAllBtn.disabled = true;
        
        // Update battle stats
        updateBattleStats(winner);
        
        // Immediately show the winner banner without delay
        winnerBanner.textContent = winner === "It's a tie" ? winner : `${winner} wins!`;
        winnerBanner.style.display = 'block';
        
        // Reset battle progress flag when battle is complete
        battleInProgress = false;
    }
    
    // Reveal all remaining Pokemon
    function revealAllPokemon() {
        if (revealInterval) clearInterval(revealInterval);
        while (revealedCount < (pokemonList1.length + pokemonList2.length)) {
            revealNextPokemon();
        }
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

    // CRITICAL: Add one (and only one) click handler for the start battle button
    if (startBattleBtn) {
        console.log('Adding click handlers to start battle button');
        
        // Remove any existing event listeners (not directly possible but safeguard)
        startBattleBtn.onclick = null;
        
        // Just use a single event listener approach
        startBattleBtn.addEventListener('click', function(e) {
            // Prevent any default action or propagation that might trigger duplicate events
            e.preventDefault();
            e.stopPropagation();
            
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

    // --- Event Listeners ---

    // Mode Selection Change
    if (randomModeRadio && manualModeRadio) {
        document.querySelectorAll('input[name="battle-mode"]').forEach(radio => {
            radio.addEventListener('change', function() {
                currentBattleMode = this.value;
                console.log(`Battle mode changed to: ${currentBattleMode}`);
                if (currentBattleMode === 'manual') {
                    manualSelectionArea.style.display = 'block';
                    // Optionally hide reveal mode selection as it's not relevant for manual
                    document.querySelector('label[for="auto-reveal"]').parentElement.parentElement.style.display = 'none';
                } else {
                    manualSelectionArea.style.display = 'none';
                     // Show reveal mode selection again
                    document.querySelector('label[for="auto-reveal"]').parentElement.parentElement.style.display = 'block';
                }
                // Reset selections if switching back to random? Or keep them? Decide on behavior.
                // For now, let's keep them, but reset scores if needed.
            });
        });
    }

    // CRITICAL: Add one (and only one) click handler for the start battle button
    if (startBattleBtn) {
        console.log('Adding click handlers to start battle button');

        // Remove any existing event listeners (not directly possible but safeguard)
        startBattleBtn.onclick = null;

        // Just use a single event listener approach
        startBattleBtn.addEventListener('click', function(e) {
            // Prevent any default action or propagation that might trigger duplicate events
            e.preventDefault();
            e.stopPropagation();

            console.log('Start battle button clicked!');
            startBattle(); // This function now handles both modes
        });
    }

    // Other event listeners
    if (revealNextBtn) revealNextBtn.addEventListener('click', revealNextPokemon); // Only relevant for random manual reveal
    if (revealAllBtn) revealAllBtn.addEventListener('click', revealAllPokemon); // Only relevant for random mode
    if (newBattleBtn) {
        newBattleBtn.addEventListener('click', () => {
            if (revealInterval) clearInterval(revealInterval);
            setupForm.style.display = 'block';
            battleContainer.style.display = 'none';
            revealNextBtn.disabled = false; // Re-enable buttons
            revealAllBtn.disabled = false;

            // Reset manual selection UI if it exists
            if (manualSelectionArea) {
                 allPokemonInputs.forEach(input => input.value = ''); // Clear inputs
                 if(player1SelectedPokemonDiv) player1SelectedPokemonDiv.innerHTML = ''; // Clear previews
                 if(player2SelectedPokemonDiv) player2SelectedPokemonDiv.innerHTML = '';
                 if(player1TeamStatsDiv) player1TeamStatsDiv.textContent = 'Total Stats: 0'; // Reset stats display
                 if(player2TeamStatsDiv) player2TeamStatsDiv.textContent = 'Total Stats: 0';
                 pokemonList1.fill(null); // Clear internal state
                 pokemonList2.fill(null);
            }
             // Reset scores
            player1CurrentScore = 0;
            player2CurrentScore = 0;
            player1Score.textContent = '0';
            player2Score.textContent = '0';
            if (fixedPlayer1Score) fixedPlayer1Score.textContent = '0';
            if (fixedPlayer2Score) fixedPlayer2Score.textContent = '0';
            updateLeadingPlayer(); // Reset leading indicator

        battleInProgress = false; // Reset battle flag
        });
    }

    // Function to display a battle based on data (used for manual battles loaded from localStorage)
    function displayManualBattle(data) {
        console.log("Displaying pre-built manual battle...");
        player1Name = data.player1Name;
        player2Name = data.player2Name;
        pokemonList1 = data.player1Pokemon;
        pokemonList2 = data.player2Pokemon;

        // Update names in UI
        player1Header.textContent = player1Name;
        player2Header.textContent = player2Name;
        if (fixedPlayer1Name) fixedPlayer1Name.textContent = player1Name;
        if (fixedPlayer2Name) fixedPlayer2Name.textContent = player2Name;

        // Calculate scores
        player1CurrentScore = pokemonList1.reduce((sum, p) => sum + (p ? p.total_stats : 0), 0);
        player2CurrentScore = pokemonList2.reduce((sum, p) => sum + (p ? p.total_stats : 0), 0);

        // Update score displays
        player1Score.textContent = player1CurrentScore;
        player2Score.textContent = player2CurrentScore;
        if (fixedPlayer1Score) fixedPlayer1Score.textContent = player1CurrentScore;
        if (fixedPlayer2Score) fixedPlayer2Score.textContent = player2CurrentScore;
        updateLeadingPlayer();

        // Hide setup, show battle container (no loading needed)
        setupForm.style.display = 'none';
        loadingElement.style.display = 'none';
        battleContainer.style.display = 'block';

        // Hide reveal buttons
        if (revealNextBtn) revealNextBtn.style.display = 'none';
        if (revealAllBtn) revealAllBtn.style.display = 'none';

        // Clear existing battle grids
        player1Pokemon.innerHTML = '';
        player2Pokemon.innerHTML = '';

        // Directly display all selected Pokemon cards
        pokemonList1.forEach((pokemon, index) => {
            if (pokemon) {
                // Need a function to create the card element directly from data
                const cardElement = createPopulatedPokemonCard(pokemon, 1, index);
                player1Pokemon.appendChild(cardElement);
            }
        });
        pokemonList2.forEach((pokemon, index) => {
            if (pokemon) {
                const cardElement = createPopulatedPokemonCard(pokemon, 2, index);
                player2Pokemon.appendChild(cardElement);
            }
        });

        // Set progress to 100%
        revealedCount = 12; // Mark all as "revealed"
        updateRevealProgress();

        // Finalize battle immediately
        finalizeBattle();
        battleInProgress = false; // Ensure flag is reset
    }

    // Helper function to create a populated card (similar to manual_setup.js one but adapted)
    function createPopulatedPokemonCard(pokemonData, playerNum, index) {
        const card = pokemonCardTemplate.content.cloneNode(true);
        const cardElement = card.querySelector('.pokemon-card');

        // Add identifiers
        cardElement.classList.add(`player-${playerNum}-card`);
        cardElement.dataset.index = index;
        cardElement.dataset.player = playerNum;

        // Populate with data using the existing function
        updatePokemonCard(cardElement, pokemonData);

        // Make visible immediately
        cardElement.classList.remove('hidden');
        cardElement.classList.add('revealed', 'permanently-revealed');

        return cardElement;
    }


    // --- Initialization ---
    function initialize() {
        console.log('Initializing dashboard...');
        loadBattleStats();

        // Check for manual battle data from localStorage
        const manualDataString = localStorage.getItem('manualBattleData');
        if (manualDataString) {
            console.log('Found manual battle data in localStorage.');
            try {
                const manualData = JSON.parse(manualDataString);
                // Clear the data immediately after reading
                localStorage.removeItem('manualBattleData');
                console.log('Manual battle data cleared from localStorage.');
                // Display the manual battle instead of showing setup
                displayManualBattle(manualData);
            } catch (e) {
                console.error("Error parsing manual battle data from localStorage:", e);
                localStorage.removeItem('manualBattleData'); // Clear corrupted data
                // Fallback to showing setup form
                setupForm.style.display = 'block';
            }
        } else {
            // No manual data, show the setup form for random battle
            console.log('No manual battle data found. Displaying setup form.');
            setupForm.style.display = 'block';
        }

        // Log when the page is fully loaded and initialized
        console.log('DOM fully loaded and parsed, initialization complete.');
    }

    initialize(); // Run initialization logic
});
