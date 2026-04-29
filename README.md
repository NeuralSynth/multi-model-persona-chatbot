# SST Persona Chatbot

A persona-based multi-model chatbot built with Python and Streamlit.

The app lets you chat with three Scaler School of Technology personas while switching the underlying LLM at runtime. The LLM layer uses a Strategy + Factory design so the UI can route cleanly between ChatGPT, Gemini, DeepSeek, and self-hosted OpenAI-compatible models.

## Features

- Three distinct SST personas with separate prompts and metadata
- Gemini as the default model on first load
- Runtime model selection from the UI
- Strategy + Factory provider layer in `core/llm.py`
- Streaming responses with provider-specific integrations
- Faint in-stream `Thinking` indicator while the assistant is generating output
- Isolated conversation history per persona and per model
- Deployment-safe fallback when a provider is not configured
- Self-hosted OpenAI-compatible model support
- Circular local avatar images loaded from `assets/avatars/`
- Responsive UI for desktop and mobile
- Docker and docker-compose support

## Supported Models

- ChatGPT via OpenAI
- Gemini via Google GenAI
- DeepSeek via DeepSeek's OpenAI-compatible API
- Self-hosted OpenAI-compatible models

If a selected provider is missing required configuration at deploy time, the app shows:

`Model unavailable at this time. It is being implemented.`

## Architecture

### UI layer

- `app.py` handles Streamlit layout, persona selection, model selection, streaming output, and avatar rendering.

### State layer

- `core/session.py` owns Streamlit session state for:
  - active persona
  - active model
  - pending chips
  - conversation history scoped to each persona/model pair

### LLM layer

- `core/llm.py` implements the provider abstraction.
- Strategy pattern: each provider has its own streaming strategy.
- Factory pattern: the selected model id is resolved into the right provider strategy.

Current strategies:

- `OpenAICompatibleStrategy`
- `GeminiStrategy`
- `LLMStrategyFactory`

## Conversation Behavior

- Switching personas keeps separate chat history for each persona.
- Switching models keeps separate chat history for each model.
- The effective conversation context is isolated per `persona + model` combination.
- Clearing chat only clears the currently active persona/model conversation.

## Environment Variables

Configure one or more providers. Unconfigured models remain selectable in the UI but return the unavailable-model message until their required values are set.

### OpenAI / ChatGPT

```env
OPENAI_API_KEY=
OPENAI_MODEL=
```

### Gemini

```env
GEMINI_API_KEY=
GEMINI_MODEL=
```

### DeepSeek

```env
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=
```

### Self-hosted OpenAI-compatible

```env
SELF_HOSTED_BASE_URL=
SELF_HOSTED_MODEL_NAME=
SELF_HOSTED_API_KEY=
```

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Then open `http://localhost:8501`.

## Avatar Images

Place local avatar images in `assets/avatars/` using these filenames:

- `anshuman_singh`
- `abhimanyu_saxena`
- `kshitij_mishra`

Supported extensions:

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`

The folder is kept in git with `.gitkeep`, while the actual image files are ignored by `.gitignore`.

## Docker

```bash
cp .env.example .env
docker-compose up --build
```

Manual build:

```bash
docker build -t sst-chatbot .
docker run -p 8501:8501 --env-file .env sst-chatbot
```

Notes:

- The container runs `python main.py`.
- `assets/` is copied into the image, so avatar images must be present before building if you want them included.
- If you use a self-hosted model from inside Docker, `SELF_HOSTED_BASE_URL` must be reachable from the container, for example `http://host.docker.internal:8000/v1`.
