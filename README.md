# Pokemon Battle Dashboard

![Pokemon Battle Dashboard](screenshots/dashboard.png)

A web application that automates Pokemon battles between two players, with dramatic revealing of Pokemon and stat calculations.

## Features

- 🎮 **Random Pokemon Generation**: Automatically generates 6 random Pokemon for each player
- 👥 **Player Names**: Custom names for each player
- 🎭 **Dramatic Reveals**: Two reveal modes - automatic or manual, one Pokemon at a time
- 📊 **Live Score Tracking**: Real-time score updates as Pokemon are revealed
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🏆 **Battle History**: Tracks win/loss records between players

## Screenshots

### Setup Screen
![Setup Screen](screenshots/setup.png)

### Battle in Progress
![Battle in Progress](screenshots/battle.png)

### Winner Announcement
![Winner](screenshots/winner.png)

## How It Works

The application uses the [PokeAPI](https://pokeapi.co/) to fetch random Pokemon data. For each player, 6 Pokemon are randomly selected, and their total stats are calculated. The player with the highest total stat score wins the battle.

During the reveal process, Pokemon are shown one at a time, alternating between players, building suspense as the scores change.

## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd Pokemon_battle_mel
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Access the dashboard at `http://localhost:5000`

## Project Structure

