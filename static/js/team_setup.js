document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    const statusMessageEl = document.getElementById('status-message'); 

    const sessionIdSpan = document.getElementById('session-id'); 
    if (sessionIdSpan && sessionId) {
        sessionIdSpan.textContent = sessionId;
    }

    if (!sessionId) {
        if (statusMessageEl) statusMessageEl.textContent = 'Error: No session ID provided in URL.';
        const submitButton = document.getElementById('submit-team-button');
        if(submitButton) submitButton.disabled = true;
        return;
    }

    const serverErrorMessage = document.body.getAttribute('data-error-message');
    if (serverErrorMessage) {
        if (statusMessageEl) statusMessageEl.textContent = serverErrorMessage;
        const submitButton = document.getElementById('submit-team-button');
        if(submitButton) submitButton.disabled = true;
        return; 
    } 

    const socket = io();
    const teamSetupForm = document.getElementById('team-setup-form'); 
    
    // Variables related to new autocomplete and team display
    // These might integrate or replace parts of the old selectedPokemon logic
    const teamSlotsContainer = document.getElementById('team-slots-container'); // From old code, ensure it's used correctly if HTML expects it
    const selectedCountSpan = document.getElementById('selected-count'); // From old code
    const submitTeamButton = document.getElementById('submit-team-button'); // From old code, ensure its event listener is the primary one

    // It's possible the detailed Pokemon selection logic (selectedPokemon array, maxSelection)
    // from the old code needs to be merged here if the new form submission isn't sufficient.
    // For now, the new code has its own way of collecting team members on submit.
    // If the old detailed card display and selection tracking is required, it needs careful integration here.

    socket.on('connect', () => {
        console.log('Connected for team setup, session:', sessionId);
        socket.emit('join_team_setup', { session_id: sessionId });
    });

    socket.on('team_setup_joined', (data) => {
        console.log('Successfully joined team setup room:', data);
        if (statusMessageEl) statusMessageEl.textContent = data.message || 'Successfully joined team setup. Select your team.';
        if(submitTeamButton) submitTeamButton.disabled = false;
    });

    socket.on('error_message', (data) => {
        console.error('Team setup SocketIO Error:', data.message);
        if (statusMessageEl) statusMessageEl.textContent = `Error: ${data.message}`;
        if(submitTeamButton) submitTeamButton.disabled = true;
    });

    socket.on('team_submit_confirm', (data) => {
        console.log('Team submission confirmed:', data);
        if (statusMessageEl) statusMessageEl.textContent = data.message;
        if(submitTeamButton) submitTeamButton.disabled = true;
    });

    socket.on('battle_fully_ready', (data) => {
        console.log('Battle fully ready, redirecting to battle page for session:', data.session_id);
        if (statusMessageEl) statusMessageEl.textContent = 'Both teams submitted! Redirecting to battle...';
        window.location.href = `/battle?session_id=${data.session_id}`;
    });

    if (teamSetupForm) {
        teamSetupForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const team = [];
            const inputs = document.querySelectorAll('.team-slot .pokemon-slot-input'); 
            inputs.forEach(input => {
                if (input.value) {
                    const pokemonName = input.dataset.pokemonName || input.value;
                    team.push(pokemonName.toLowerCase());
                }
            });

            // Validate team size (e.g. 1 to 6 Pokémon)
            // The old code had `maxSelection` which was 6. Assuming similar logic.
            if (team.length > 0 && team.length <= 6) { 
                console.log('Submitting team:', team, 'for session:', sessionId);
                socket.emit('submit_team', { session_id: sessionId, team: team });
                if (statusMessageEl) statusMessageEl.textContent = 'Team submitted. Waiting for opponent...';
                if(submitTeamButton) submitTeamButton.disabled = true;
            } else {
                if (statusMessageEl) statusMessageEl.textContent = `Please select between 1 and 6 Pokémon for your team. You selected ${team.length}.`;
            }
        });
    }

    // Autocomplete logic integrated from the new code block
    document.querySelectorAll('.pokemon-slot-input').forEach(input => {
        input.addEventListener('input', function() {
            const query = this.value;
            const resultsContainer = this.closest('.team-slot').querySelector('.autocomplete-results-slot');
            if (!resultsContainer) return; // Guard if structure is not as expected
            if (query.length < 2) { 
                resultsContainer.innerHTML = '';
                resultsContainer.style.display = 'none';
                return;
            }
            fetch(`/api/search_pokemon?name=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    resultsContainer.innerHTML = '';
                    if (data.length > 0) {
                        data.forEach(pokemon => {
                            const div = document.createElement('div');
                            div.textContent = pokemon.name;
                            div.classList.add('autocomplete-item');
                            div.addEventListener('click', () => {
                                this.value = pokemon.name; 
                                this.dataset.pokemonName = pokemon.name; 
                                resultsContainer.innerHTML = '';
                                resultsContainer.style.display = 'none';
                                const cardDisplay = this.closest('.team-slot').querySelector('.pokemon-card-display');
                                if (cardDisplay) {
                                    // Ensure sprite_url and name are present in the pokemon object from API
                                    cardDisplay.innerHTML = `<img src="${pokemon.sprite_url || ''}" alt="${pokemon.name}"> <p>${pokemon.name}</p>`;
                                }
                            });
                            resultsContainer.appendChild(div);
                        });
                        resultsContainer.style.display = 'block';
                    } else {
                        resultsContainer.style.display = 'none';
                    }
                })
                .catch(error => {
                    console.error('Error fetching Pokémon for autocomplete:', error);
                    resultsContainer.style.display = 'none';
                });
        });
    });

    // Hide autocomplete if clicked outside
    document.addEventListener('click', function(event) {
        document.querySelectorAll('.autocomplete-results-slot').forEach(container => {
            // Check if the click is outside the container AND not on an input field that might trigger it
            const associatedInput = container.closest('.team-slot')?.querySelector('.pokemon-slot-input');
            if (!container.contains(event.target) && event.target !== associatedInput) {
                container.style.display = 'none';
            }
        });
    });

    // Any unique logic from the old 'initializeSlots', 'handleInput (old version)', 
    // 'selectPokemonForSlot', 'renderSlot', 'removePokemonFromSlot', 'updateTeamStatus' 
    // or 'fetchAllPokemonNames' would need to be brought in here if the current 
    // autocomplete and form submission isn't sufficient for the desired UX.
    // For example, the detailed card rendering and tracking in `selectedPokemon` array 
    // and updating `selectedCountSpan` is not in the new code block snippet directly.
    // If that UX is desired, it needs to be re-integrated carefully here.

    // Example: If `selectedCountSpan` and `maxSelection` from old code are needed:
    // const maxSelection = 6; // Define if not already available
    // function updateTeamStatusDisplay() { 
    //     const inputs = document.querySelectorAll('.team-slot .pokemon-slot-input');
    //     let currentCount = 0;
    //     inputs.forEach(input => {
    //         if (input.dataset.pokemonName) { // Check if a pokemon is selected for this slot via autocomplete
    //             currentCount++;
    //         }
    //     });
    //     if (selectedCountSpan) selectedCountSpan.textContent = currentCount;
    //     if (submitTeamButton) submitTeamButton.disabled = currentCount !== maxSelection;
    // }
    // Add event listeners to inputs that call updateTeamStatusDisplay() when a selection changes.
    // This would be after an autocomplete item is clicked and `dataset.pokemonName` is set.

});
