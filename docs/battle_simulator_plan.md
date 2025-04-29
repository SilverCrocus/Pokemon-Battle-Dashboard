# Pokemon Battle Logic Enhancement Plan

1.  **[DONE] Chunk 1: Basic Types & Class Updates**
    *   Add `TYPE_CHART` and [get_type_effectiveness](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:30:0-39:24) function.
    *   Update `Pokemon.__init__` to handle `type_list`.
    *   Add `Pokemon.get_opponent_view` method.
    *   Update [Move](cci:2://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:104:0-125:24) class to accept a data dictionary and add [use_pp](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:117:4-124:20) method.

2.  **[DONE (needs fix)] Chunk 2: Player Actions Setup**
    *   Initialize `self.player_actions` in `Battle.__init__`.
    *   Update `Battle.select_move` to store actions in `self.player_actions`.
    *   Rename `are_moves_selected` to [are_actions_selected](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:17:4-27:62) and update its logic.
    *   **Fix:** Update the call in [run_turn](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:210:4-263:71) to use [are_actions_selected](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:17:4-27:62).

3.  **Chunk 3: Switch Implementation**
    *   Create `Battle.select_switch` method to handle switching Pokemon.
    *   Update `player_actions` to accommodate switch actions.
    *   Update [are_actions_selected](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:17:4-27:62) (if needed) to correctly handle both moves and switches.
    *   Implement logic within [run_turn](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:210:4-263:71) (or a helper) to perform the switch action.

4.  **Chunk 4: Turn Execution Logic**
    *   Refine `Battle.run_turn`.
    *   Determine turn order based on Pokemon speed (and potentially action priority later).
    *   Implement `Battle._execute_action` (or similar) to handle performing moves or switches.
    *   Implement `Battle._calculate_damage` using [get_type_effectiveness](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:30:0-39:24), stats, and move power.
    *   Update Pokemon HP using [take_damage](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:93:4-99:87).
    *   Decrement move PP using `move.use_pp()`.
    *   Reset `player_actions` at the end of the turn.

5.  **Chunk 5: Battle State & Game Over**
    *   Implement `Battle.get_state_for_player` to provide comprehensive state updates (active Pokemon, team status, opponent view, log).
    *   Implement `Battle.check_game_over` to determine if a player has no usable Pokemon left.
    *   Update [run_turn](cci:1://file:///e:/Documents/Pokemon_battle_mel/battle_logic.py:210:4-263:71) to check for game over conditions.

6.  **Chunk 6: SocketIO Integration (`app.py`)**
    *   Update `handle_player_action` in `app.py` to call `battle.select_move` or `battle.select_switch`.
    *   Trigger `battle.run_turn` when both players have selected actions.
    *   Emit updated battle states (`battle.get_state_for_player`) to clients after each action and turn resolution.
    *   Handle game over events.

7.  **Chunk 7: PokeAPI Integration (Future)**
    *   Replace static `POKEMON_DATA` loading with dynamic fetching from PokeAPI during `Battle._create_pokemon`.
    *   Fetch move details dynamically as needed.