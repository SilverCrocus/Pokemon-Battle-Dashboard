document.addEventListener('DOMContentLoaded', () => {
    const sessionIdSpan = document.getElementById('session-id');
    const teamSetupForm = document.getElementById('team-setup-form');
    const teamSlotsContainer = document.getElementById('team-slots-container');
    const selectedCountSpan = document.getElementById('selected-count');
    const submitTeamButton = document.getElementById('submit-team-button');

    const socket = io(); // Initialize Socket.IO client
    let allPokemonNames = []; // Store all Pokemon names
    const selectedPokemon = new Array(6).fill(null); // Array to hold selected Pokemon data for each slot
    const maxSelection = 6;

    // Get session ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');

    if (!sessionId) {
        alert('Error: Invalid session ID.');
        // Optionally redirect or disable the page further
        return;
    }

    sessionIdSpan.textContent = sessionId;

    // --- Socket.IO Event Listeners ---
    socket.on('connect', () => {
        console.log('Connected to WebSocket for team setup');
        socket.emit('join_team_setup', { session_id: sessionId });
    });

    socket.on('team_submission_success', (data) => {
        console.log('Team submission success:', data);
        alert(data.message);
        // Keep button disabled, wait for 'teams_ready_start_battle'
    });

    socket.on('error_message', (data) => {
        console.error('Error from server:', data.message);
        alert('Error: ' + data.message);
        submitTeamButton.disabled = selectedPokemon.filter(p => p !== null).length !== maxSelection; // Re-evaluate button state
    });

    socket.on('teams_ready_start_battle', (data) => {
        console.log('Teams ready signal received:', data);
        console.log('Redirecting to battle...');
        window.location.href = `/battle?session_id=${sessionId}`;
    });

    // --- Fetch Initial Data ---
    fetch('/api/pokemon_list')
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(pokemonNames => {
            allPokemonNames = pokemonNames;
            console.log(`Fetched ${allPokemonNames.length} Pokemon names.`);
            initializeSlots(); // Initialize slots after names are fetched
        })
        .catch(error => {
            console.error('Error fetching Pokemon list:', error);
            alert('Failed to load Pokemon list. Please refresh.');
        });

    // --- Slot Initialization and Event Handling ---
    function initializeSlots() {
        console.log('Initializing slots...');
        const slots = teamSlotsContainer.querySelectorAll('.team-slot');
        slots.forEach((slot, index) => {
            const input = slot.querySelector('.pokemon-slot-input');
            const cardDisplay = slot.querySelector('.pokemon-card-display');
            const autocompleteResults = slot.querySelector('.autocomplete-results-slot');

            console.log(`Adding input listener for slot ${index}`);
            input.addEventListener('input', () => handleInput(input, autocompleteResults));
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault(); // Prevent form submission
                    const firstResult = autocompleteResults.querySelector('.autocomplete-item');
                    if (firstResult) {
                        firstResult.click(); // Simulate click on the first result
                    }
                }
            });

            // Hide autocomplete when clicking outside the specific slot
            document.addEventListener('click', (event) => {
                if (!slot.contains(event.target)) {
                    autocompleteResults.innerHTML = '';
                    autocompleteResults.classList.remove('active');
                }
            });
        });
    }

    console.log(`Handling input: ${inputElement.value}`);
    function handleInput(inputElement, resultsContainer) {
        const searchTerm = inputElement.value.toLowerCase();
        resultsContainer.innerHTML = ''; // Clear previous results

        if (searchTerm.length < 1) { // Start searching after 1 character
            resultsContainer.classList.remove('active');
            return;
        }

        const filteredNames = allPokemonNames.filter(name =>
            name.toLowerCase().startsWith(searchTerm)
        ); // Show all results

        if (filteredNames.length > 0) {
            filteredNames.forEach(name => {
                const resultItem = document.createElement('div');
                resultItem.classList.add('autocomplete-item');
                resultItem.textContent = name.charAt(0).toUpperCase() + name.slice(1);
                resultItem.addEventListener('click', () => {
                    selectPokemonForSlot(name, inputElement.closest('.team-slot'));
                    inputElement.value = ''; // Clear input
                    resultsContainer.innerHTML = ''; // Clear results
                    resultsContainer.classList.remove('active');
                });
                resultsContainer.appendChild(resultItem);
            });
            resultsContainer.classList.add('active');
        } else {
            resultsContainer.classList.remove('active');
        }
    }

    // --- Pokemon Selection and Rendering ---
    function selectPokemonForSlot(name, slotElement) {
        const slotIndex = parseInt(slotElement.dataset.slotIndex, 10);

        // Check if already selected in another slot
        if (selectedPokemon.some(p => p && p.name.toLowerCase() === name.toLowerCase())) {
             alert(`${name.charAt(0).toUpperCase() + name.slice(1)} is already selected in another slot.`);
             return;
        }

        // Fetch details
        fetch(`/api/pokemon_details?name=${name}`)
            .then(response => {
                if (!response.ok) throw new Error(`Pokemon not found: ${name}`);
                return response.json();
            })
            .then(pokemon => {
                console.log('Fetched Pokemon Details:', pokemon); // <-- ADDED THIS LINE
                selectedPokemon[slotIndex] = pokemon; // Store full data
                renderSlot(slotElement, pokemon);
                updateTeamStatus();
            })
            .catch(error => {
                console.error(`Error fetching details for ${name}:`, error);
                alert(`Could not find details for ${name}. Please try again.`);
            });
    }

    function renderSlot(slotElement, pokemonData) {
        const input = slotElement.querySelector('.pokemon-slot-input');
        const cardDisplay = slotElement.querySelector('.pokemon-card-display');
        const autocompleteResults = slotElement.querySelector('.autocomplete-results-slot');

        input.style.display = 'none'; // Hide input
        autocompleteResults.innerHTML = ''; // Clear autocomplete
        autocompleteResults.classList.remove('active');
        cardDisplay.innerHTML = ''; // Clear previous card

        if (pokemonData) {
            const pokemonCard = document.createElement('div');
            pokemonCard.classList.add('pokemon-card', 'selected-in-slot'); // Add specific class
            pokemonCard.dataset.name = pokemonData.name;

            const typesHtml = pokemonData.types.map(type => `<span class="pokemon-type ${type}">${type}</span>`).join('');

            pokemonCard.innerHTML = `
                <img src="${pokemonData.sprite}" alt="${pokemonData.name}">
                <h3>${pokemonData.name}</h3>
                <div class="pokemon-types">${typesHtml}</div>
                <button type="button" class="remove-pokemon-slot">X</button>
            `;

            pokemonCard.querySelector('.remove-pokemon-slot').addEventListener('click', () => {
                removePokemonFromSlot(slotElement);
            });

            cardDisplay.appendChild(pokemonCard);
        } else {
            // Show input again if pokemonData is null (e.g., after removal)
            input.style.display = 'block';
            input.value = '';
            input.placeholder = `Type Pokemon name...`;
        }
    }

    function removePokemonFromSlot(slotElement) {
        const slotIndex = parseInt(slotElement.dataset.slotIndex, 10);
        selectedPokemon[slotIndex] = null; // Remove data from array
        renderSlot(slotElement, null); // Re-render slot as empty
        updateTeamStatus();
    }

    // --- Team Status and Submission ---
    function updateTeamStatus() {
        const currentCount = selectedPokemon.filter(p => p !== null).length;
        selectedCountSpan.textContent = currentCount;
        submitTeamButton.disabled = currentCount !== maxSelection;
    }

    teamSetupForm.addEventListener('submit', (event) => {
        event.preventDefault();

        const finalTeam = selectedPokemon.filter(p => p !== null).map(p => p.name); // Get names from stored data

        if (finalTeam.length !== maxSelection) {
            alert(`Please select exactly ${maxSelection} Pokemon.`);
            return;
        }

        if (typeof socket === 'undefined') {
             console.error('Socket.IO client not initialized.');
             alert('An internal error occurred. Please refresh the page.');
             return;
        }

        socket.emit('submit_team', { session_id: sessionId, team: finalTeam });
        console.log('Emitted submit_team event:', { session_id: sessionId, team: finalTeam });

        submitTeamButton.disabled = true;
        submitTeamButton.textContent = 'Waiting for opponent...';
        // Disable inputs/remove buttons after submission
        teamSlotsContainer.querySelectorAll('.pokemon-slot-input, .remove-pokemon-slot').forEach(el => el.disabled = true);
    });

});
