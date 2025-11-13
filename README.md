# PM4 – AI Assisted Food Tracker

This project contains a lightweight food tracking application that blends the
standard features of calorie trackers with an AI-inspired recognition engine.
The codebase now offers both a command-line experience and a fullstack web
application. The FastAPI backend exposes the tracker over HTTP, while the
bundled frontend delivers a responsive interface for scanning foods, logging
meals, and reviewing summaries.

## Features

- **AI-assisted food scanning** – type or paste a description to get the top
  matches along with confidence scores in the browser or via the CLI.
- **Manual logging** – quickly add foods that are not part of the reference
  database while still storing macros and calories.
- **Daily summaries** – review the foods eaten each day alongside total
  calories and macronutrients.
- **Fullstack delivery** – FastAPI powers a JSON API and serves a polished
  single-page interface without extra build steps.
- **Extensible design** – the recognition engine is intentionally simple so it
  can run offline, but its API can be swapped for a heavier ML model when
  needed.

## Getting Started

1. Ensure you have Python 3.10+ installed.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the web application:

   ```bash
   uvicorn food_tracker.api:app --reload
   ```

   Visit <http://localhost:8000> to use the AI-assisted food tracker in your
   browser. The API is exposed under the `/api` prefix if you want to integrate
   with other clients.

4. (Optional) Run the CLI instead of, or alongside, the web app:

   ```bash
   python ai.py --help
   ```

   Example sessions:

   ```bash
   # Ask the AI to recognise a food item
   python ai.py scan "grilled chicken salad"

   # Log the best match returned by the AI
   python ai.py log "grilled chicken salad" --quantity 1.5

   # Manually log a custom food
   python ai.py add "Homemade Protein Bar" "1 bar" 210 --protein 15 --carbs 18 --fat 8

   # Show today's summary
   python ai.py summary
   ```

Data is stored as JSON under `~/.food_tracker/log.json` so you can safely delete
that file to reset your log. The web UI, API, and CLI all share the same
persistent log.

## Extending the AI Component

The `FoodRecognitionEngine` in `food_tracker/ai.py` uses a simple bag-of-words
embedding so the project remains dependency free. To integrate a more
sophisticated model:

1. Replace the implementation of `EmbeddingModel.encode` with calls to your
   preferred ML library.
2. Expand `food_tracker/data/foods.json` or connect the tracker to a nutrition
   API.
3. Update the CLI or build a GUI/mobile frontend using the `FoodTracker` class
   from `food_tracker/tracker.py`.

## Project Layout

```
food_tracker/
├── ai.py              # AI recognition helpers
├── api.py             # FastAPI application & static file server
├── cli.py             # Command line interface
├── data/foods.json    # Reference nutrition dataset
├── models.py          # Data classes and helpers
├── storage.py         # Persistence utilities
└── tracker.py         # High-level orchestration
frontend/
├── app.js             # Browser client logic
├── index.html         # Single-page shell served by FastAPI
└── styles.css         # UI styling
```

Use `FoodTracker` as the main entry point if you intend to embed the tracking
logic into another application layer.
