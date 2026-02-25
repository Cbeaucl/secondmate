# SecondMate

SecondMate is a modern data catalog and exploration tool built with a high-performance Python backend and a dynamic React frontend. It provides a seamless interface for managing data catalogs, namespaces, and tables, with built-in support for Apache Iceberg and PySpark.

## 🚀 Key Features

*   **Dynamic Catalog Browser**: Navigate through your data hierarchy (Catalogs -> Namespaces -> Tables) with an intuitive tree view.
*   **Data Preview**: Instantly query and visualize data from your tables.
*   **Integrated Querying**: Built-in support for executing queries against your data lake.
*   **Iceberg Native**: Designed with Apache Iceberg in mind, including automatic sample data initialization.
*   **Modern UI**: Built with React 19, TypeScript, and Vite, featuring a responsive design with resizable panels and a premier dark-mode aesthetic.

## 🛠️ Tech Stack

### Frontend
*   **Framework**: React 19 + TypeScript
*   **Build Tool**: Vite
*   **State Management**: Zustand
*   **Component**: Monaco Editor, React Resizable Panels
*   **Styling**: Lucide React (Icons), CSS Modules

### Backend
*   **Framework**: FastAPI
*   **Data Processing**: PySpark 4.0+ (Development build)
*   **Table Format**: Apache Iceberg
*   **Server**: Uvicorn

## 📦 Installation & Setup

### Prerequisites
*   Node.js (v18+ recommended)
*   Python 3.11+
*   Java 17+ (for PySpark)
*   [uv](https://github.com/astral-sh/uv) (recommended for Python dependency management)

### 1. Development Environment

SecondMate includes a unified development script that starts both the FastAPI backend and Vite frontend together.

```bash
# Clone the repository and enter the directory
git clone <repository-url>
cd secondmate

# Install frontend dependencies
npm install

# Create a virtual environment and install backend dependencies using uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Start the development server (runs both backend and frontend)
./dev.sh
```

- The UI will be available at `http://localhost:5173`.
- The API will be available at `http://localhost:8000`.
- Automatic API docs at `http://localhost:8000/docs`.

### 2. Manual/Separate Setup

**Frontend (Vite Server):**
```bash
npm install
npm run dev
```

**Backend (FastAPI Server):**
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
uvicorn secondmate.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Production Build

When building for production, the Vite frontend compiles into the Python package (`secondmate/static`), which is then served by FastAPI.

```bash
# Build the frontend (outputs to secondmate/static)
npm run build

# Install the Python package and run the CLI
uv pip install -e .
secondmate --port 4050
```
*The app will be available at `http://localhost:4050` serving both UI and API.*

## 📚 API Endpoints

The backend exposes several key endpoints for metadata and data retrieval:

*   `GET /health`: Service health check.
*   `GET /info`: Spark session and application details.
*   `GET /catalogs`: List all available catalogs.
*   `GET /catalogs/{catalog_name}/namespaces`: List namespaces within a catalog.
*   `GET /catalogs/{catalog_name}/namespaces/{namespace}/tables`: List tables within a namespace.
*   `GET /query`: Execute a sample query (currently fetches `user.ipgeo`).

## 🧪 Sample Data

On startup, the backend automatically initializes a local Spark Iceberg environment with the following sample tables:
*   `user.ipgeo` (1000 rows)
*   `user.sales.transactions`
*   `user.finance.budget`

Enjoy exploring your data with SecondMate!
