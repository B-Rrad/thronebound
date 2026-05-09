# Thronebound

`Thronebound` is a local fantasy card game built with `pygame`. Players draft realm cards and hero cards, then battle through attack/defense rounds until one player reaches 6 wounds or wins the realm-deck endgame. The desktop game supports two local players or a local player against Random, Greedy, or Strategic AI.

## Submission Contents

This repository includes:

- Full source code for the game
- A prebuilt Windows executable at `release/Ringbound.exe`
- Game data files in `data/`
- A TypeScript/canvas browser rewrite in `web/`

The Game can be played online here: https://drpeterjamieson.com/PROJECTS/THRONEBOUND/index.html

The gameplay video can be found here: https://youtu.be/C1FrNUbSaL8

## Repository Layout

```text
thronebound/
|-- data/
|   |-- dominions.json
|   |-- hero_cards.json
|   `-- realm_cards.json
|-- ringbound_game/
|   |-- ai_turns.py
|   |-- audio.py
|   |-- combat.py
|   |-- drafting.py
|   |-- events.py
|   |-- game.py
|   |-- heroes.py
|   |-- rounds.py
|   |-- rules.py
|   |-- state.py
|   `-- ui_game.py
|-- ui/
|   |-- input_handler.py
|   |-- renderer.py
|   `-- ...
|-- web/
|   |-- index.html
|   `-- src/
|-- release/
|   `-- Ringbound.exe
|-- main.py
|-- package.json
|-- settings.py
|-- ui_elements.py
|-- balance_analysis.py
|-- requirements.txt
|-- .gitignore
`-- README.md
```

## Requirements

- Windows 10/11 to run the included executable
- Python 3.10+ and `pygame==2.6.1` if running the desktop game from source
- Node.js 20+ if running the browser rewrite

## Run The Prebuilt Executable

1. Download using GitHub's 'Download ZIP' option.
2. Extract the ZIP.
3. Open the `release` folder.
4. Double-click `Ringbound.exe`.

## Run From Source

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Start the game:

```powershell
python main.py
```

## Desktop Controls

- Use the splash-screen buttons to start `Two Players`, `Vs Random AI`, `Vs Greedy AI`, or `Vs Strategic AI`
- Click cards to draft or play them
- Click on-screen buttons such as `Take Wound`, `End Attack`, `Pass Attack`, `P1 Heal`, `P2 Heal`, or suit choices when prompted
- Press `Space` to confirm the currently highlighted target, `Esc` to open the restart confirmation, and use the mouse wheel or log arrow buttons to scroll the game log

## Gameplay Rules

- Each player finishes the draft with a maximum of `6` realm cards and `4` hero cards. The opening realm card counts toward that limit.
- After a defended round, the defender becomes the next attacker. If the defender takes a wound, the attacker keeps the initiative.
- When the realm deck is empty, drawing stops. The endgame is then decided by empty realm hands first, then fewer wounds, then fewer total remaining cards.

## Hero Timing Notes

- `Asclepius` may be used at any time while that player has wounds remaining.
- `Medea` and `Argus Panoptes` are start-of-round attack tools.
- `Athena` and `Ajax` are defensive responses.
- `Achilles` and `Ares` must be played together with a legal realm attack card.
- `Autolycus` lets the player who played it choose the temporary crown suit for the round.

## Project Notes

- `main.py` is the launch entrypoint for the game.
- `ringbound_game/ui_game.py` composes the main game object from focused modules.
- `ringbound_game/state.py`, `drafting.py`, `rules.py`, `heroes.py`, `rounds.py`, `ai_turns.py`, `events.py`, and `audio.py` own their named slices of gameplay and app behavior.
- `ui/` owns rendering, responsive layout, animation, card surface caching, and input intent handling.
- `ui_elements.py` remains for legacy smoke-test compatibility.
- `settings.py` contains shared window, color, and state constants.
- `balance_analysis.py` is a separate analysis utility and is not required to play the game.
- `web/` contains the TypeScript/canvas rewrite scaffold for a browser version.
- The game loads `36` realm cards and `12` hero cards from JSON files in `data/`.
- The game-over screen includes a short reason so special endgame outcomes and tiebreaks are visible to the player.

## Browser Rewrite

The browser rewrite is in `web/`. It loads the same JSON card data and generated placeholder artwork as the desktop game. See `WEB_REWRITE.md` for current scope and migration notes.

Run it locally with:

```bash
npm install
npm run web:dev
```

Build it with:

```bash
npm run web:build
```

## Rebuild The Executable

If you need to regenerate the executable on Windows:

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Ringbound --add-data "data;data" --add-data "output;output" --add-data "fonts;fonts" --add-data "music;music" --add-data "background.jpg;." main.py
```
