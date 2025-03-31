document.addEventListener('DOMContentLoaded', function() {
    console.log('Manual setup page loaded.');

    // DOM Elements
    // Removed player1NameInput, player2NameInput
    const player1Header = document.getElementById('player1-header'); // Editable h2
    const player2Header = document.getElementById('player2-header'); // Editable h2
    const allPokemonCardInputs = document.querySelectorAll('.pokemon-input-in-card'); // Target inputs inside cards
    const allPokemonCards = document.querySelectorAll('.pokemon-card'); // Target the cards themselves
    const player1TeamStatsDiv = document.getElementById('player1-team-stats');
    const player2TeamStatsDiv = document.getElementById('player2-team-stats');
    const startManualBattleBtn = document.getElementById('start-manual-battle-btn');

    // State
    let allPokemonNames = [];
    let pokemonList1 = new Array(6).fill(null);
    let pokemonList2 = new Array(6).fill(null);
    let activeAutocomplete = null;

    // Type colors (copied from script.js)
    const typeColors = {
        normal: '#A8A878', fire: '#F08030', water: '#6890F0', electric: '#F8D030',
        grass: '#78C850', ice: '#98D8D8', fighting: '#C03028', poison: '#A040A0',
        ground: '#E0C068', flying: '#A890F0', psychic: '#F85888', bug: '#A8B820',
        rock: '#B8A038', ghost: '#705898', dragon: '#7038F8', dark: '#705848',
        steel: '#B8B8D0', fairy: '#EE99AC'
    };

    // --- Initialization ---
    fetchAllPokemonNames();

    // --- Fetch Pokemon List ---
    async function fetchAllPokemonNames() {
        console.log('Fetching all Pokemon names for autocomplete...');
        try {
            const response = await fetch('/api/pokemon_list');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            allPokemonNames = await response.json();
            console.log(`Fetched ${allPokemonNames.length} Pokemon names.`);
            // Enable inputs/button now that names are loaded
            startManualBattleBtn.disabled = false;
            allPokemonCardInputs.forEach(input => input.disabled = false);
        } catch (error) {
            console.error("Could not fetch Pokemon list:", error);
            alert("Failed to load Pokemon list. Please try refreshing the page.");
            // Disable functionality if list fails to load
            startManualBattleBtn.disabled = true;
            allPokemonCardInputs.forEach(input => input.disabled = true);
        }
    }

    // --- Autocomplete Functions ---
    function showAutocomplete(inputElement, suggestions) {
        // Find the dropdown within the same .pokemon-selector as the input
        const selectorDiv = inputElement.closest('.pokemon-selector');
        if (!selectorDiv) return;
        const dropdown = selectorDiv.querySelector('.autocomplete-dropdown');
        if (!dropdown) return;

        dropdown.innerHTML = ''; // Clear previous
        if (suggestions.length === 0) {
            dropdown.classList.remove('active');
            return;
        }

        suggestions.slice(0, 10).forEach(name => {
            const item = document.createElement('div');
            item.classList.add('autocomplete-item');
            item.textContent = name.charAt(0).toUpperCase() + name.slice(1);
            item.addEventListener('click', () => {
                inputElement.value = item.textContent;
                dropdown.classList.remove('active');
                activeAutocomplete = null;
                handlePokemonSelection(inputElement, name);
            });
            dropdown.appendChild(item);
        });

        dropdown.classList.add('active');
        activeAutocomplete = dropdown;
    }

    function hideAutocomplete() {
        if (activeAutocomplete) {
            activeAutocomplete.classList.remove('active');
            activeAutocomplete = null;
        }
    }

    function handleAutocompleteInput(event) {
        const inputElement = event.target; // Should be .pokemon-input-in-card
        const value = inputElement.value.toLowerCase();
        if (value.length < 1) { // Suggest even from 1 character
            hideAutocomplete();
            return;
        }
        const suggestions = allPokemonNames.filter(name => name.toLowerCase().startsWith(value));
        showAutocomplete(inputElement, suggestions);
    }

    // --- Manual Selection Handling ---

    // Update a Pokemon card with real data (copied from script.js and adapted)
    function updatePokemonCardDisplay(cardElement, pokemon) {
        const detailsFace = cardElement.querySelector('.manual-details-face');
        if (!detailsFace) return;

        // Set image
        const img = detailsFace.querySelector('.pokemon-image img');
        img.src = pokemon.sprite || ''; // Handle null sprite
        img.alt = pokemon.name;

        // Set name
        detailsFace.querySelector('.pokemon-name').textContent = pokemon.name;

        // Set types
        const typesContainer = detailsFace.querySelector('.pokemon-types');
        typesContainer.innerHTML = ''; // Clear previous types
        pokemon.types.forEach(type => {
            const typeElement = document.createElement('span');
            typeElement.className = 'type-badge';
            typeElement.textContent = type;
            typeElement.style.backgroundColor = typeColors[type.toLowerCase()] || '#AAA'; // Use lowercase for matching
            typesContainer.appendChild(typeElement);
        });

        // Set stats
        detailsFace.querySelector('.stat.hp').textContent = `HP: ${pokemon.stats.hp}`;
        detailsFace.querySelector('.stat.attack').textContent = `Atk: ${pokemon.stats.attack}`;
        detailsFace.querySelector('.stat.defense').textContent = `Def: ${pokemon.stats.defense}`;
        detailsFace.querySelector('.stat.special-attack').textContent = `SpA: ${pokemon.stats['special-attack']}`;
        detailsFace.querySelector('.stat.special-defense').textContent = `SpD: ${pokemon.stats['special-defense']}`;
        detailsFace.querySelector('.stat.speed').textContent = `Spd: ${pokemon.stats.speed}`;
        detailsFace.querySelector('.stat.total').textContent = `Total: ${pokemon.total_stats}`;
    }


    async function handlePokemonSelection(inputElement, pokemonName) {
        const player = parseInt(inputElement.dataset.player);
        const index = parseInt(inputElement.dataset.index);
        const cardElement = inputElement.closest('.pokemon-card'); // Get the parent card

        if (!cardElement) return;

        console.log(`Handling selection: Player ${player}, Index ${index}, Name: ${pokemonName}`);
        inputElement.disabled = true; // Disable input during fetch
        cardElement.style.cursor = 'wait'; // Indicate loading

        try {
            const response = await fetch(`/api/pokemon_details?name=${encodeURIComponent(pokemonName.toLowerCase())}`);
            if (!response.ok) {
                 if (response.status === 404) {
                    alert(`Pokemon "${pokemonName}" not found. Please select from the list.`);
                    inputElement.value = ''; // Clear invalid input
                 } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                 }
                 // Clear data if previously selected and update card state
                 clearPokemonSlot(player, index, cardElement);
            } else {
                const pokemonData = await response.json();
                console.log('Fetched Pokemon details:', pokemonData);

                // Store data
                if (player === 1) pokemonList1[index] = pokemonData;
                else pokemonList2[index] = pokemonData;

                // Update the card display
                updatePokemonCardDisplay(cardElement, pokemonData);
                cardElement.classList.remove('manual-input-mode');
                cardElement.classList.add('manual-selected-mode');
                // Show remove button
                const removeBtn = cardElement.querySelector('.remove-pokemon');
                if(removeBtn) removeBtn.style.display = 'inline-block';
            }
            updateTeamStats(player); // Update overall team score display
            updateWinningIndicator(); // Check winner after selection
        } catch (error) {
            console.error(`Error fetching details for ${pokemonName}:`, error);
            alert(`Failed to fetch details for ${pokemonName}. Please try again.`);
             clearPokemonSlot(player, index, cardElement); // Clear slot on error
             updateTeamStats(player);
             updateWinningIndicator(); // Check winner after error/clear
        } finally {
             inputElement.disabled = false; // Re-enable input
             cardElement.style.cursor = 'default';
             // inputElement.focus(); // Maybe not focus here, as the input is now hidden
        }
    }

    // Clear data and reset card to input mode
    function clearPokemonSlot(player, index, cardElement) {
         if (player === 1) pokemonList1[index] = null;
         else pokemonList2[index] = null;

         cardElement.classList.remove('manual-selected-mode');
         cardElement.classList.add('manual-input-mode');

         const input = cardElement.querySelector('.pokemon-input-in-card');
         if (input) input.value = '';

         const removeBtn = cardElement.querySelector('.remove-pokemon');
         if(removeBtn) removeBtn.style.display = 'none';
    }

    // Update the total stats display for a player
    function updateTeamStats(player) {
        const teamList = player === 1 ? pokemonList1 : pokemonList2;
        const teamStatsDiv = player === 1 ? player1TeamStatsDiv : player2TeamStatsDiv;

        let currentTotalStats = 0;
        let pokemonCount = 0;

        teamList.forEach(pokemon => {
            if (pokemon) {
                pokemonCount++;
                currentTotalStats += pokemon.total_stats;
            }
        });

        teamStatsDiv.textContent = `Total Stats: ${currentTotalStats}`;
        if (pokemonCount === 6) {
            teamStatsDiv.classList.add('team-complete');
            teamStatsDiv.classList.remove('team-incomplete');
        } else {
            teamStatsDiv.classList.remove('team-complete');
            teamStatsDiv.classList.add('team-incomplete');
        }
    }

    function handleRemovePokemon(event) {
        const button = event.target;
        const player = parseInt(button.dataset.player);
        const index = parseInt(button.dataset.index);
        const cardElement = button.closest('.pokemon-card');

        if (!cardElement) return;

        console.log(`Removing Pokemon: Player ${player}, Index ${index}`);
        clearPokemonSlot(player, index, cardElement);
        updateTeamStats(player); // Update score after removal
        updateWinningIndicator(); // Update winner indicator after removal
    }

    // --- Winning Indicator ---
    function updateWinningIndicator() {
        const player1Section = player1Header.closest('.player-section');
        const player2Section = player2Header.closest('.player-section');

        if (!player1Section || !player2Section) return;

        // Remove previous classes
        player1Section.classList.remove('winning', 'losing', 'tie');
        player2Section.classList.remove('winning', 'losing', 'tie');

        // Check if both teams are complete
        const player1Ready = pokemonList1.filter(p => p !== null).length === 6;
        const player2Ready = pokemonList2.filter(p => p !== null).length === 6;

        if (player1Ready && player2Ready) {
            // Calculate scores (redundant if updateTeamStats was just called, but safe)
            const score1 = pokemonList1.reduce((sum, p) => sum + (p ? p.total_stats : 0), 0);
            const score2 = pokemonList2.reduce((sum, p) => sum + (p ? p.total_stats : 0), 0);

            if (score1 > score2) {
                player1Section.classList.add('winning');
                player2Section.classList.add('losing');
            } else if (score2 > score1) {
                player2Section.classList.add('winning');
                player1Section.classList.add('losing');
            } else {
                player1Section.classList.add('tie');
                player2Section.classList.add('tie');
            }
        }
        // If teams are not complete, no classes are added (cleared above)
    }


    // --- Start Battle Logic ---
    function startManualBattle() {
        // Get names from editable headers, default if empty
        const player1Name = player1Header.textContent.trim() || "Player 1";
        const player2Name = player2Header.textContent.trim() || "Player 2";
        // Update header text if it was empty to show the default
        if (!player1Header.textContent.trim()) player1Header.textContent = player1Name;
        if (!player2Header.textContent.trim()) player2Header.textContent = player2Name;


        const player1Ready = pokemonList1.filter(p => p !== null).length === 6;
        const player2Ready = pokemonList2.filter(p => p !== null).length === 6;

        if (!player1Ready || !player2Ready) {
            alert('Both players must select 6 Pokemon before starting the battle.');
            return;
        }

        // Prepare data to pass to the main page
        const battleData = {
            player1Name: player1Name,
            player2Name: player2Name,
            player1Pokemon: pokemonList1,
            player2Pokemon: pokemonList2,
            mode: 'manual' // Indicate this was a manual setup
        };

        // Store data in localStorage
        try {
            localStorage.setItem('manualBattleData', JSON.stringify(battleData));
            console.log('Manual battle data saved to localStorage.');
            // Redirect to the main page
            window.location.href = '/';
        } catch (e) {
            console.error("Error saving data to localStorage:", e);
            alert("Could not save battle data. Please try again.");
        }
    }

    // --- Event Listeners ---
    allPokemonCardInputs.forEach(input => {
        input.addEventListener('input', handleAutocompleteInput);
        input.addEventListener('blur', () => setTimeout(hideAutocomplete, 150)); // Delay hide
        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                const potentialMatch = allPokemonNames.find(name => name.toLowerCase() === input.value.toLowerCase());
                if (potentialMatch) {
                    input.value = potentialMatch.charAt(0).toUpperCase() + potentialMatch.slice(1);
                    hideAutocomplete();
                    handlePokemonSelection(input, potentialMatch);
                } else if (input.value.trim() !== '') {
                    // Check if input is empty after potential match/alert
                    if (input.value.trim() === '') {
                         const player = parseInt(input.dataset.player);
                         const index = parseInt(input.dataset.index);
                         const cardElement = input.closest('.pokemon-card');
                         clearPokemonSlot(player, index, cardElement); // Ensure slot is cleared if input is empty
                         updateTeamStats(player);
                    }
                } else if (input.value.trim() !== '') {
                    alert(`"${input.value}" is not a recognized Pokemon. Please select from the list.`);
                    input.value = '';
                    const player = parseInt(input.dataset.player);
                    const index = parseInt(input.dataset.index);
                    const cardElement = input.closest('.pokemon-card');
                    clearPokemonSlot(player, index, cardElement); // Ensure slot is cleared
                    updateTeamStats(player);
                }
            } else if (event.key === 'Escape') {
                 hideAutocomplete();
            }
        });
        // Disable initially until names are loaded
        input.disabled = true;
    });

    // Add listeners to remove buttons (needs to be delegated or added after creation)
    // Since buttons are added/removed dynamically, delegate from a static parent
    document.querySelector('.container').addEventListener('click', function(event) {
        if (event.target.classList.contains('remove-pokemon')) {
            handleRemovePokemon(event);
        }
    });


    document.addEventListener('click', (event) => {
        // Hide autocomplete if clicking outside a selector
        if (!event.target.closest('.pokemon-selector')) {
            hideAutocomplete();
        }
    });

    if (startManualBattleBtn) {
        startManualBattleBtn.addEventListener('click', startManualBattle);
        // Disable initially until names are loaded
        startManualBattleBtn.disabled = true;
    } else {
        console.error("Start Manual Battle button not found!");
    }

    // Add listeners for editable headers
    [player1Header, player2Header].forEach(header => {
        // Prevent adding new lines on Enter
        header.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                header.blur(); // Trigger blur to save/process
            }
        });
        // Optional: Trim whitespace on blur
        header.addEventListener('blur', () => {
             // Basic sanitization: remove extra whitespace
             let name = header.textContent.replace(/\s+/g, ' ').trim();
             // Prevent empty names, revert to default? Or keep previous?
             if (!name) {
                 name = header.id === 'player1-header' ? 'Player 1' : 'Player 2';
             }
             header.textContent = name;
             console.log(`Header ${header.id} updated to: ${name}`);
        });
    });

});
