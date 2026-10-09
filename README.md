# TextForge AI — LSTM-Powered Text Generation Platform

TextForge AI is a full-stack text-generation application built around a word-level Long Short-Term Memory (LSTM) neural network trained on Shakespeare's works. It provides a React interface for generating text, managing generation history, and starting and monitoring training runs through a FastAPI backend.

> **Model limitation:** This is an educational/demo-scale language model. It can learn Shakespeare-inspired vocabulary and patterns, but generated text may be grammatically incorrect, repetitive, or incoherent.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [How It Works](#how-it-works)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Run with Docker Compose](#run-with-docker-compose)
- [Run Locally Without Docker](#run-locally-without-docker)
- [Train the Model](#train-the-model)
- [Standalone Assignment Script](#standalone-assignment-script)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Deployment Overview](#deployment-overview)
- [Testing](#testing)
- [Limitations and Future Improvements](#limitations-and-future-improvements)
- [License](#license)

## Features

- **Text generation:** Generate Shakespeare-inspired text from a starting phrase.
- **Sampling controls:** Adjust generation length and temperature; optionally use top-k sampling.
- **User authentication:** Register and log in using JWT-based authentication.
- **Generation history:** Browse, search, paginate, view, and delete saved generations, subject to ownership checks.
- **Dashboard:** Review generation statistics and recent activity.
- **Model training:** Start a training run and review run status and epoch metrics.
- **Training visualisation:** View training and validation loss charts.
- **Model artifacts:** Save trained Keras models and their vocabulary for later inference.
- **API documentation:** Explore available endpoints through FastAPI's interactive `/docs` page.
- **Local database fallback:** Use SQLite for simple local development or PostgreSQL for a more production-like setup.
- **Responsive interface:** React, TypeScript, and Tailwind CSS frontend.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, Recharts, Axios, Lucide |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Authentication | JWT with PyJWT and bcrypt |
| AI / ML | TensorFlow, Keras, NumPy, scikit-learn |
| Database | PostgreSQL; SQLite fallback for local development |
| Local orchestration | Docker Compose |
| Deployment options | Vercel (frontend), Render (API), managed PostgreSQL |

## How It Works

1. **Preprocessing:** The dataset is lowercased, punctuation is stripped while apostrophes are retained, whitespace is normalised, and text is split into words.
2. **Vocabulary:** The most frequent words are selected up to the configured vocabulary limit. Special `<pad>` and `<unk>` tokens are used where applicable. The vocabulary is saved as `vocab.json`.
3. **Training sequences:** A sliding window of `seq_length` words is used to predict the next word. The data is split into training and validation sets.
4. **Model architecture:** An embedding layer feeds one or more LSTM layers, with optional dropout, followed by a dense softmax layer that predicts the next token.
5. **Optimisation:** The model uses Adam and sparse categorical cross-entropy loss.
6. **Training controls:** Early stopping monitors validation loss, and model checkpointing retains the best checkpoint when configured.
7. **Generation:** The model repeatedly predicts the next word from the most recent context. Temperature controls sampling randomness; optional top-k sampling limits the candidate words.

## Dataset

The default dataset is the Shakespeare text file provided by TensorFlow:

- **Default source:** [Shakespeare text dataset](https://storage.googleapis.com/download.tensorflow.org/data/shakespeare.txt)
- **Alternative source:** [Project Gutenberg — Shakespeare's works](https://www.gutenberg.org/ebooks/100)
- **Other datasets:** [Kaggle Datasets](https://www.kaggle.com/datasets)

The application is configured to download the default dataset automatically when required. The downloaded file is stored locally under `data/` unless your configuration specifies another location.

Please review the terms and attribution requirements of any alternative dataset before using it.

## Project Structure

```text
TextForge-AI/
├── backend/
│   ├── app/
│   │   ├── api/              # Authentication, generation, training, dependencies
│   │   ├── core/             # Configuration and security
│   │   ├── db/               # Database session setup
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Preprocessing, LSTM, training, generation
│   │   └── main.py           # FastAPI application
│   ├── scripts/
│   │   └── lstm_text_generation.py
│   ├── tests/
│   │   └── test_api.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React + TypeScript + Vite application
├── data/                     # Downloaded training dataset
├── artifacts/                # Model checkpoints and vocabulary (local; usually ignored by Git)
├── notebooks/                # Experiments / notebooks, if present
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

> The tree describes the intended layout. Some optional files or folders may not exist in every checkout.

## Prerequisites

Choose the setup that matches your environment.

### For Docker Compose

- Docker Desktop (or Docker Engine) with the Compose plugin
- Enough memory for the backend and TensorFlow

### For manual setup

- Python version supported by your installed TensorFlow release (Python 3.10–3.11 is recommended by this project configuration)
- Node.js and npm compatible with the frontend's `package.json`
- Git (optional, for cloning the repository)

TensorFlow can require significant RAM, particularly during training. First-time setup may also download dependencies and the dataset.

## Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

When the services have started, open:

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **Interactive API docs:** http://localhost:8000/docs

The exact ports depend on `docker-compose.yml`. If your configuration uses different host ports, use those values instead.

To stop the services, press `Ctrl+C`, then run:

```bash
docker compose down
```

To also remove the Compose-managed database volume (this permanently deletes data stored in that volume), run:

```bash
docker compose down -v
```

## Run Locally Without Docker

The commands below use Windows PowerShell / Command Prompt examples and are followed by the equivalent Unix activation command where relevant.

### 1. Set up the backend

From the repository root:

**Windows (Command Prompt):**

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**macOS / Linux:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Keep the backend terminal running. The API should be available at http://localhost:8000.

### 2. Set up the frontend

Open a second terminal at the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, typically http://localhost:5173.

If the frontend is configured to proxy `/api` requests to `http://localhost:8000`, no additional frontend API URL is needed for local development. Otherwise, configure the API base URL as described in your frontend configuration.

### 3. Use the application

1. Open the frontend in your browser.
2. Register an account or log in.
3. Open **Training** and start a training run if a compatible trained model is not already available.
4. Wait for training to complete.
5. Open **Playground**, enter a starting phrase, choose generation settings, and generate text.
6. Visit **History** to review saved generations.

> **Note:** Training can take time and may use substantial memory. If a trained model is already available and loaded, you can test generation without starting another training run.

## Train the Model

The Training page exposes configurable training parameters. Common parameters include:

| Parameter | Meaning |
|---|---|
| Epochs | Maximum number of passes over the training data |
| Sequence length | Number of preceding words used to predict the next word |
| Embedding dimension | Size of each word's learned vector representation |
| LSTM units | Hidden-state size for each LSTM layer |
| LSTM layers | Number of stacked LSTM layers |
| Dropout | Regularisation applied during training |
| Batch size | Number of training examples processed per batch |
| Maximum vocabulary | Limit on the number of vocabulary entries |

Training uses validation loss for monitoring. Early stopping and best-model checkpointing are enabled when configured by the training pipeline. Actual training duration and output quality depend on the dataset, hyperparameters, hardware, and software environment.

## Standalone Assignment Script

The repository includes a standalone script for running the text-generation assignment without using the web interface.

From the repository root:

```bash
cd backend
python scripts/lstm_text_generation.py
```

To run the optional experiments:

```bash
python scripts/lstm_text_generation.py --experiments
```

The script's available command-line options and output depend on the implementation in your checkout. Run it with `--help` if supported by the script.

## API Reference

The API is served by FastAPI. Start the backend, then visit [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI.

The following endpoints are documented by this project:

| Method | Endpoint | Authentication | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/register` | No | Register an account |
| `POST` | `/api/auth/login` | No | Log in and receive an authentication token |
| `GET` | `/api/auth/me` | Yes | Get the current user's account |
| `GET` | `/api/health` | No | Check API and model status |
| `POST` | `/api/generate` | Yes | Generate text from a seed phrase |
| `GET` | `/api/generations?q=&limit=&offset=` | Yes | Search and paginate generation history |
| `GET` | `/api/generations/{id}` | Yes | View a generation owned by the current user |
| `DELETE` | `/api/generations/{id}` | Yes | Delete a generation owned by the current user |
| `GET` | `/api/stats` | Yes | Retrieve dashboard statistics |
| `GET` | `/api/model/info` | Yes | Retrieve active model information |
| `POST` | `/api/training/start` | Yes | Start a training run |
| `GET` | `/api/training/runs` | Yes | List training runs |
| `GET` | `/api/training/runs/{id}` | Yes | Retrieve a training run and its metrics |

Authentication requirements and endpoint availability should be confirmed against the running API's `/docs` page, which reflects the implementation in your checkout.

## Configuration

Use `.env.example` as the starting point for local configuration. Create a local `.env` file only if the application expects one, and set values appropriate to your environment.

Common deployment configuration values may include:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Database connection string |
| `SECRET_KEY` | Secret used to sign or validate tokens |
| `CORS_ORIGINS` | Allowed frontend origins |
| `DATA_DIR` | Directory for dataset files |
| `DATASET_PATH` | Path to the training dataset |
| `ARTIFACTS_DIR` | Directory for saved model artifacts |
| `VITE_API_URL` | Backend base URL used by the frontend build |

The exact variable names and defaults are determined by the code in `backend/app/core/config.py` and the frontend configuration. Do not commit real secrets, production credentials, or private connection strings. Use a long, random secret key outside local development.

### Local database

SQLite can simplify local setup when enabled by the project configuration. For PostgreSQL, create a database and set `DATABASE_URL` to the connection string expected by SQLAlchemy and the configured database driver. For example, a PostgreSQL SQLAlchemy URL may begin with:

```text
postgresql+psycopg2://USER:PASSWORD@HOST:5432/DATABASE
```

Use the driver installed in `requirements.txt`; the example above is not a substitute for checking the configured driver.

## Deployment Overview

A possible deployment arrangement is:

- **Frontend:** Vercel, with the frontend directory as the project root and the build command/output directory set to match the Vite configuration (`npm run build` / `dist`).
- **Backend:** Render or another Python/Docker host that supports the app's runtime and resource needs.
- **Database:** Managed PostgreSQL, such as a service from Render, Neon, or Supabase.

Before deploying:

1. Configure the frontend's backend API URL.
2. Set a strong `SECRET_KEY` and production database connection string in the backend environment.
3. Restrict CORS to the actual deployed frontend origin.
4. Configure persistent storage for model artifacts and dataset files if the service filesystem is ephemeral.
5. Verify memory and CPU limits; model training may exceed small free-tier limits.
6. Test registration, login, generation, history, and training against the deployed services.

The deployment setup must match the actual environment variables, paths, ports, and service configuration in this repository. Deployment is not implied by the local run instructions.

## Testing

From the repository root, activate the backend virtual environment and run the tests if the required test dependencies are installed:

```bash
cd backend
pytest
```

If the project uses additional test configuration or environment variables, follow those requirements. Also verify the main user flow manually:

- Register and log in.
- Generate text with several seed phrases.
- Confirm generations appear in history.
- Search and paginate through history.
- Start a training run and check its status and metrics.
- Confirm the active model loads after training or application restart, where persistence is configured.

## Limitations and Future Improvements

- **Generation quality:** A small word-level LSTM can produce incoherent, repetitive, or grammatically incorrect text.
- **Model capacity:** Vocabulary limits, sequence length, architecture, dataset size, and training duration affect results.
- **Background training:** If training runs in an in-process background thread, it is suitable for a demo but not robust job orchestration for a production service.
- **Database schema:** If tables are created at application startup, schema migrations (for example, Alembic) should be added before evolving production schemas.
- **Persistence:** Model and dataset files must live on durable storage if they need to survive container or host restarts.
- **Evaluation:** Record sample outputs and compare runs with a consistent set of prompts and settings before claiming a quality improvement.

Potential next steps include expanding the training corpus, tuning model hyperparameters, adding repeatable evaluation, adding database migrations, and moving training jobs to a dedicated queue for larger deployments.

## License

No license is specified here. Add a `LICENSE` file if you intend to publish this repository with an explicit open-source license.
