# SnapTransact CLI – process.md

## 0. Meta

-   **Version**: 0.1
-   **Last Updated**: 2025-01-27
-   **Author**: Team
-   **Status**: Development Complete (100%), Ready for CI/CD & Production

---

## 1. Overview / Goals

To build a Command-Line Interface (CLI) application using **Python 3.11+** to automate the extraction of transaction data from screenshots. The application will analyze images, perform Optical Character Recognition (OCR), process the data, and export the results to a CSV file.

The application will be packaged in a **Docker container** to ensure a consistent execution environment and to avoid requiring users to install complex dependencies (like Tesseract OCR).

**KPIs**

-   Processing time per image ⩽ 3 seconds. (Not tested yet)
-   Docker image size ⩽ 350 MB. (Not optimized yet)
-   Test coverage ≥ 85%. ✅ **Complete** (comprehensive unit tests added)

**Current Implementation Status**

✅ **Complete (100%)**:
- CLI framework with Typer
- OCR processing with Tesseract
- Transaction parsing with regex patterns
- CSV export with Pandas
- Docker containerization
- Configuration management
- Error handling and logging
- **Unit testing with 85%+ coverage**
- **Sentry integration for error tracking**
- **Configuration examples and documentation**

❌ **Pending**:
- CI/CD pipeline setup
- Performance optimization and KPI testing
- Production deployment
- Docker image size optimization

---

## 2. Architecture & Tech Stack

### 2.1 Application Core

| Layer               | Technology                                      | Rationale                                                                        |
| :------------------ | :---------------------------------------------- | :------------------------------------------------------------------------------- |
| CLI Framework       | **Typer 0.12** | Builds powerful, intuitive CLIs based on Python type hints, auto-generates help messages. |
| Image Processing    | **Pillow 10.4** | The most popular and robust foundational image processing library in the Python ecosystem. |
| OCR Engine          | **Pytesseract 0.3** (wrapper for Tesseract 5)   | A powerful open-source OCR engine with support for multiple languages, including Vietnamese. |
| Data Manipulation   | **Pandas 2.2** | Provides a powerful DataFrame structure for processing, grouping, and exporting data to CSV. |
| Configuration       | **Pydantic 2.8** | Strictly validates configuration from files (e.g., `config.yaml`) or environment variables. |
| Packaging           | **Poetry 1.8** | Manages dependencies, virtual environments, and project packaging in a modern, reliable way. |
| Logging             | **Loguru 0.7** | Offers a simpler, more powerful logging API than the default `logging` module. |

### 2.2 Data Layer

-   Primary data sources are image files (`.png`, `.jpg`) and configuration files (`.yaml`).

### 2.3 Build/Tooling

-   **Python 3.11+**.
-   **Ruff** (linter & formatter) + **Mypy** (static type checking).
-   **pre-commit** + **commitlint** (Conventional Commits).
-   **pytest 8.2** + `pytest-cov` for unit/integration testing and coverage measurement.

### 2.4 CI/CD & Containerization

-   **Docker** multi-stage: `python:3.11-slim` base, a build stage for installing dependencies, and a **Distroless** runtime stage for optimized security and size.
-   **Docker Compose** for local development (running the tool + any dependent services).
-   **GitHub Actions**: lint/type-check → test → build → publish image to GHCR.
-   **Renovate**/Dependabot for automatic dependency updates.

### 2.5 Monitoring & Security

-   **Sentry Python SDK** for error tracking.
-   **pip-audit** to scan for security vulnerabilities in dependencies.
-   **SonarCloud** for static code quality analysis.

---

## 3. Development Checklist

```markdown
- [x] Initialize project with Poetry + Typer
- [x] Set up Ruff/Mypy/pre-commit
- [x] Create multi-stage Dockerfile + Compose file
- [x] Implement OCR module (Pillow + Pytesseract)
- [x] Implement Parser module (regex, logic) to extract information
- [x] Create a `process` command that accepts an image file/folder as input
- [x] Integrate Pandas to create and export the CSV file
- [x] Write unit tests for the Parser with pytest and mocker (100% complete - all modules tested)
- [x] Set coverage threshold ≥ 85% (configured in pyproject.toml)
- [x] Integrate Sentry to track errors in production (code ready, config example provided)
```

## 4. Progress Log

| Date    | Task                  | Status | Notes                      |
| :------ | :-------------------- | :----: | :------------------------- |
| 03-07   | Initialize process.md |   ✅   | Base structure for CLI app |
| Current | Core Implementation   |   ✅   | CLI, OCR, Parser, Docker completed |
| Current | Testing Infrastructure|   ✅   | Complete unit tests for all modules |
| Current | Configuration Management | ✅   | Sentry integration, config examples |
| Current | Development Complete  |   ✅   | All checklist items finished |
| Current | CI/CD Pipeline       |   ❌   | GitHub Actions not setup yet |
| Current | Production Features  |   ❌   | Performance testing, optimization needed |

## 5. Prompt / Shortcut

> **prompt:** "Write a unit test for the `parse_transaction_from_text` function using pytest, and use `mocker` to mock the output from Tesseract OCR."

---

## 6. Unit Test & Coverage

-   **Framework**: **pytest** for unit and integration tests.
-   **Coverage Tool**: **pytest-cov** (using `coverage.py`) to generate `lcov` + `html` reports.
-   **Required Threshold**: **Lines, branches ≥ 85%** (long-term goal: 95%).
-   **CI Gate**: The `pytest --cov --cov-fail-under=85` step in GitHub Actions – the pipeline will fail if coverage is below the threshold.
-   **Reporting**: Upload HTML coverage report as a GitHub artifact; SonarCloud ingests `lcov.info` to display trends.

```bash
# Run all tests locally and view the coverage report
poetry run pytest --cov

# Run tests on CI (fails if coverage is low)
poetry run pytest --cov --cov-fail-under=85
```

---

## 7. Directory Structure

### 7.1 General Principles

1.  **Source Layout**: Application code is placed in the `src/` directory to clearly separate it from configuration files and tests in the root directory.
2.  **Modular Design**: Each major feature (OCR, parsing, export) is separated into its own module within the main package.
3.  **Clear Naming**: Adhere to **PEP 8**. Use `snake_case.py` for filenames and modules. Use `PascalCase` for class names.
4.  **Isolated Tests**: All tests are located in the root `tests/` directory, with a structure that mirrors the `src/` directory.
5.  **Centralized Configuration**: All project configuration (dependencies, tool settings) is located in `pyproject.toml`.

### 7.2 Reference Directory Tree

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── snap_transact/        # Main package name
│       ├── __init__.py
│       ├── main.py           # Typer CLI entrypoint
│       ├── ocr.py            # Image processing and OCR logic
│       ├── parser.py         # Text data extraction logic
│       ├── core.py           # Main orchestration logic
│       ├── models.py         # Pydantic models (Transaction,...)
│       └── utils.py          # Helper functions
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   └── fixtures/             # Sample data for tests (images, text)
├── .env.example              # Example environment variables
├── .gitignore
├── Dockerfile                # Multi-stage Dockerfile
├── docker-compose.yml
├── poetry.lock
├── pyproject.toml            # Poetry's project management file
└── README.md
```

### 7.3 Additional Rules

-   **Virtual Environment**: Always develop within a virtual environment managed by **Poetry**.
-   **Dependencies**: Clearly declare main and development dependencies in `pyproject.toml`.
-   **Absolute Imports**: Use absolute imports from `src` (`from snap_transact.parser import ...`).
-   **Environment Variables**: Use a library like `pydantic-settings` to safely load configuration from `.env` files. Do not commit `.env` files containing sensitive information.

---

## 8. Next Steps (Priority Order)

### High Priority (This Week)
- [x] **Complete Unit Tests**: Add tests for `core.py`, `ocr.py`, and integration tests
- [x] **Coverage Target**: Achieve 85% test coverage threshold
- [x] **Sentry Integration**: Error tracking configuration complete
- [ ] **GitHub Actions CI**: Set up lint → test → build → publish pipeline
- [ ] **Performance Testing**: Verify ≤ 3s per image KPI

### Medium Priority (Next 2 Weeks)
- [ ] **Docker Optimization**: Reduce image size to ≤ 350MB
- [ ] **Production Config**: Environment-specific settings, Sentry DSN
- [ ] **Error Handling**: Comprehensive error scenarios and recovery
- [ ] **Documentation**: API docs, deployment guide

### Low Priority (Future)
- [ ] **Security Scanning**: pip-audit, vulnerability checks
- [ ] **Monitoring**: Detailed metrics and alerts
- [ ] **Template System**: Bank-specific transaction formats
- [ ] **Interactive Mode**: User confirmation for uncertain OCR

## 9. Ideas Parking Lot 🧠

-   Develop a template system (e.g., YAML files) allowing users to define transaction structures for different banks.
-   Implement an interactive mode: if OCR is uncertain, prompt the user for confirmation.
-   Integrate cloud storage: read images from S3/Google Cloud Storage and save the CSV back to it.
-   Generate summary reports by month/quarter or by spending category.
-   Build a simple web interface (using FastAPI) to provide the same functionality via an API.
