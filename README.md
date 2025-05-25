# Dry Martini

Dry Martini is a full-stack “Bond Explorer” application that provides investors and analysts with easy access to bond market data, document archives, and fund holding information. It consists of:

- **Backend** (`martini/`): A Python FastAPI service that exposes REST endpoints, handles database interactions, and proxies PDF documents from Google Cloud Storage.  
- **Frontend** (`dry-martini-web/`): A React application (with Material-UI) that offers an interactive UI for browsing securities, viewing price charts, reading documents, and inspecting fund holdings.

---

## Table of Contents

1. [Features](#features)  
2. [Architecture](#architecture)  
3. [Getting Started](#getting-started)  
   - [Prerequisites](#prerequisites)  
   - [Backend Setup](#backend-setup)  
   - [Frontend Setup](#frontend-setup)  
4. [Usage](#usage)  
   - [API Endpoints](#api-endpoints)  
   - [Frontend](#frontend)  
5. [Configuration](#configuration)  
6. [Development](#development)  
7. [Contributing](#contributing)  
8. [License](#license)  

---

## Features

- **List Securities**: Browse securities ordered by popularity, ISIN, name, or issue date.  
- **Detail View**: View bond metadata, price history chart, summary text, PDF documents, and fund holdings.  
- **PDF Proxying**: Securely serve documents stored in Google Cloud Storage via HTTPS proxy endpoints.  
- **Infinite Scroll & Search**: Seamless browsing with search and infinite-scroll in the sidebar.  
- **Dark Theme**: Modern UI with a dark Material-UI theme.

---

## Architecture

### Backend (`martini/`)
- **FastAPI** for high-performance async HTTP endpoints.  
- **SQLAlchemy (async)** + **PostgreSQL** for data storage.  
- **Google Cloud Storage** client for PDF blobs.  
- **Pydantic** schemas for request/response models.  
- **Uvicorn** as ASGI server.

Directory structure:
```
martini/
├── main.py              # Application entrypoint & route definitions
├── db.py                # Async engine & session factory
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic models
├── utils/               # Logging helper, HTTP helpers, etc.
└── data/                # Static CSVs (e.g., state lists)
```

### Frontend (`dry-martini-web/`)
- **React** with **Material-UI** components.  
- **Chart.js** (via `react-chartjs-2`) with annotation plugin for interactive price charts.  
- **Infinite scroll** via `IntersectionObserver`.  
- **Axios / Fetch API** to communicate with FastAPI backend.

Directory structure:
```
dry-martini-web/
├── src/
│   ├── App.js           # Main application component
│   ├── components/      # Sidebar, ChartCard, Panels, PdfViewer, etc.
│   ├── theme.js         # MUI dark theme definition
│   └── utils/           # helper functions
└── public/              # static assets (e.g., icons)
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**  
- **Node.js 16+** & **npm/yarn**  
- **PostgreSQL** instance  
- **Google Cloud** project with a storage bucket for documents  

### Backend Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/your-org/dry-martini.git
   cd dry-martini/martini
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   ```bash
   export POSTGRES_CONNECTION=postgresql+asyncpg://user:pass@localhost:5432/dbname
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-key.json
   export DRY_MARTINI_BUCKET=dry-martini-docs
   ```
4. Launch the API:
   ```bash
   uvicorn martini.main:app --host 0.0.0.0 --port 6010 --reload
   ```

### Frontend Setup

1. In a separate terminal, navigate to the frontend folder:
   ```bash
   cd ../dry-martini-web
   ```
2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```
3. Configure backend URL (optional):
   - Edit `.env` or set `REACT_APP_BACKEND_URL` to your FastAPI URL (default `http://localhost:6010`).
4. Run the development server:
   ```bash
   npm start
   # or
   yarn start
   ```
5. Open your browser at `http://localhost:3000`.

---

## Usage

### API Endpoints

| Method | Path                           | Description                                   |
| ------ | ------------------------------ | --------------------------------------------- |
| GET    | `/`                            | Health-check / welcome message                |
| GET    | `/securities?skip=&limit=&sort=` | List securities (popularity, isin, name, issue_date) |
| GET    | `/securities/{isin}`           | Retrieve detailed security info               |
| POST   | `/securities/{isin}/documents` | Attach a new document to a security           |
| GET    | `/documents/{doc_id}/proxy`    | Proxy-fetch a PDF document                    |

### Frontend

- **Sidebar**: Search and sort securities with infinite scrolling.  
- **Main Panel**: Displays price chart, metadata grid, and document list.  
- **PDF Viewer**: Inline PDF rendering via an `<iframe>`.  
- **Summary & Fund Panels**: Show text summaries and fund holding chips.

---

## Configuration

- **Environment Variables**:
  - `POSTGRES_CONNECTION`: PostgreSQL DSN  
  - `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account JSON  
  - `DRY_MARTINI_BUCKET`: GCS bucket name for PDFs  
  - `REACT_APP_BACKEND_URL`: Frontend’s target API URL  

- **Database Migrations**: Tables are auto-created at startup via `Base.metadata.create_all()`.

---

## Development

- Run tests (if any) with:
  ```bash
  pytest
  ```
- Lint & format:
  ```bash
  black .
  flake8
  ```
- Commit conventions: follow Conventional Commits.

---

## Contributing

1. Fork the repository.  
2. Create a feature branch: `git checkout -b feat/my-feature`.  
3. Make your changes and add tests.  
4. Commit & push: `git push origin feat/my-feature`.  
5. Open a Pull Request.

---

## License

This project is licensed under the [MIT License](LICENSE).
