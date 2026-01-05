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
*   **Styling**: Lucide React (Icons), CSS Modules/Tailwind (implied)

### Backend
*   **Framework**: FastAPI
*   **Data Processing**: PySpark 4.0+ (Development build)
*   **Table Format**: Apache Iceberg
*   **Server**: Uvicorn

## 📦 Installation & Setup

### Prerequisites
*   Node.js (v18+ recommended)
*   Python 3.10+
*   Java (for PySpark)

### 1. Backend Setup

The backend handles the connection to the Spark/Iceberg cluster and provides APIs for catalog metadata and data querying.

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Running the Backend Server:**

```bash
# From the backend directory
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`. You can view the automatic API docs at `http://localhost:8000/docs`.

### 2. Frontend Setup

The frontend connects to the backend to display the user interface.

```bash
# Navigate to the project root (if not already there)
cd ..

# Install dependencies
npm install

# Start the development server
npm run dev
```
The application will be available at `http://localhost:5173`.

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
