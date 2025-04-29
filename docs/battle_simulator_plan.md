# Pokemon Battle Simulator Plan

## Requirement Clarification

*   **Core Functionality:** Add a 1v1 real-time battle simulator page to the existing web application.
*   **Immediate Use Cases:** Two online players can form 6-Pokemon teams and battle each other.
*   **Essential Constraints:** Initially use common movesets for simplicity; future customization is a possibility.
*   **Interaction Model:** Real-time, simultaneous online battle where both players take turns selecting moves.
*   **Integration:** The battle simulator will be a new page within the existing web application.
*   **Team Formation Link:** A unique link will be generated for players to set up their teams for a specific battle session.
*   **Move Selection:** Initially, use common movesets.

## Core Solution Design

Implement a real-time battle experience integrated into the existing web application using WebSockets for communication.

## Implementation Details

1.  **Frontend (New Files):**
    *   `templates/team_setup.html`: Page for players to select their 6 Pokemon team.
    *   `static/js/team_setup.js`: JavaScript for the team setup page, handling Pokemon selection and sending the team to the backend.
    *   `templates/battle.html`: Page to display the battle, including Pokemon sprites, health bars, move options, and battle log.
    *   `static/js/battle.js`: JavaScript for the battle page, handling move selection, receiving battle updates via WebSockets, and updating the UI.
    *   Potentially new CSS in `static/css/style.css` or a new file for battle-specific styling.

2.  **Backend (`app.py` and potentially new files):**
    *   Add routes for `/team_setup` and `/battle`.
    *   Implement logic to handle team submissions from `team_setup.js`, storing teams temporarily with a unique battle session ID.
    *   Integrate a WebSocket library (e.g., `Flask-SocketIO`).
    *   Implement WebSocket event handlers for connecting players, receiving moves, and sending battle state updates.
    *   Develop the battle simulation logic (in `app.py` or `battle_logic.py`).
    *   Implement logic to determine common movesets (e.g., from a local file).

3.  **Team Formation Link:**
    *   Generate a unique battle session ID and a link (`/team_setup?session_id=XYZ`) when a battle is initiated.
    *   Frontend (`team_setup.js`) reads `session_id` from the URL and includes it in team submission.
    *   `/battle` route requires `session_id` to connect players.

4.  **Move Selection (Common Movesets):**
    *   Backend determines the common moveset for the active Pokemon.
    *   Moveset is sent to the frontend (`battle.js`) for display and selection.

## Key Design Decisions

*   **Real-time Communication:** WebSockets.
*   **Battle State Management:** Backend is the single source of truth.
*   **Battle Session Management:** Unique session IDs.
*   **Data for Movesets:** Local file for common movesets initially.

## Battle Flow Diagram

```mermaid
graph TD
    A[User 1 Initiates Battle] --> B{Backend: Create Session ID}
    B --> C[Backend: Generate Team Setup Link (session_id)]
    C --> D[User 1 Shares Link with User 2]
    D --> E[User 1 & 2 Visit Team Setup Link]
    E --> F[Frontend: Team Setup Page]
    F --> G{User Selects 6 Pokemon}
    G --> H[Frontend: Submit Team (with session_id)]
    H --> I[Backend: Store Team (with session_id)]
    I --> J{Both Teams Submitted?}
    J -- No --> K[Frontend: Waiting for Opponent]
    J -- Yes --> L[Backend: Start Battle Session]
    L --> M[Frontend: Redirect to Battle Page (session_id)]
    M --> N[Frontend: Display Initial Battle State]
    N --> O{Player 1 Selects Move}
    N --> P{Player 2 Selects Move}
    O --> Q[Frontend: Send Move (with session_id)]
    P --> Q
    Q --> R[Backend: Receive Moves]
    R --> S[Backend: Simulate Turn]
    S --> T[Backend: Send Battle State Update (via WebSocket)]
    T --> U[Frontend: Update Battle Display]
    U --> V{Battle Over?}
    V -- No --> N
    V -- Yes --> W[Frontend: Display Battle Results]