# Testing Strategy for SecondMate

This document describes the testing approach for SecondMate, including unit tests and end-to-end (E2E) tests.

## End-to-End (E2E) Tests

E2E tests verify the application as a whole by running a browser against a live server. They are implemented using Python and Playwright.

### Running E2E Tests

To run the E2E tests, you need to have the frontend built and Python with Playwright installed.

1.  **Build the frontend** (if not already built):
    ```bash
    npm run build
    ```

2.  **Run the E2E test script**:
    ```bash
    python3 tests/e2e/test_workspace_initial_state.py
    ```

The script automatically starts a temporary local server to serve the static assets and then runs the Playwright tests against it.

## Unit Tests

Unit tests verify individual components in isolation. They are implemented using Vitest and React Testing Library.

### Running Unit Tests

1.  **Install dependencies** (if not already installed):
    ```bash
    npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
    ```

2.  **Run the tests**:
    ```bash
    npx vitest run
    ```

Current unit tests:
- `src/components/Layout/Workspace.test.tsx`: Verifies the initial state of the Workspace component.

## Verification Scripts

The repository also contains several Python verification scripts that check specific aspects of the build and API:
- `verify_assets.py`: Checks if assets are correctly served with relative paths.
- `verify_conditional_data.py`: Verifies data integrity.
- `verify_injection.py`: Checks for potential injection vulnerabilities.
- `verify_pyspark.py`: Verifies PySpark integration.
