# SnapTransact CLI - Vibe coding

[![CI](https://github.com/your-org/Transaction-Screenshot-Parser/workflows/CI/badge.svg)](https://github.com/your-org/Transaction-Screenshot-Parser/actions)
[![Coverage](https://img.shields.io/codecov/c/github/your-org/Transaction-Screenshot-Parser)](https://codecov.io/gh/your-org/Transaction-Screenshot-Parser)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![Poetry](https://img.shields.io/badge/poetry-1.8%2B-blue)](https://python-poetry.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com)

**SnapTransact CLI** is a powerful command-line application that automatically extracts transaction data from screenshots using Optical Character Recognition (OCR). Built with Python 3.11+, it processes images to identify transaction details and exports them to CSV format for easy analysis.

## ✨ Features

- 🔍 **Advanced OCR**: Uses Tesseract OCR with support for English and Vietnamese
- 📊 **Smart Parsing**: Intelligent extraction of dates, amounts, descriptions, and references
- 🏢 **Multi-format Support**: Processes PNG, JPEG, TIFF, and BMP images
- 📈 **CSV Export**: Clean, structured output ready for analysis
- 🐳 **Docker Ready**: Containerized for consistent deployment
- ⚡ **High Performance**: Processing time ≤ 3 seconds per image
- 🧪 **Well Tested**: 85%+ test coverage
- 📝 **Type Safe**: Full type hints with MyPy validation

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Pull the latest image
docker pull ghcr.io/your-org/transaction-screenshot-parser:latest

# Process images from input directory
docker run --rm \
  -v /path/to/images:/app/input:ro \
  -v /path/to/output:/app/output \
  ghcr.io/your-org/transaction-screenshot-parser:latest \
  process /app/input --output /app/output/transactions.csv
```

### Using Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-org/Transaction-Screenshot-Parser.git
cd Transaction-Screenshot-Parser

# Place images in images/ directory
cp /path/to/your/images/* images/

# Run processing
docker-compose up snap-transact
```

### Local Installation

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone and install
git clone https://github.com/your-org/Transaction-Screenshot-Parser.git
cd Transaction-Screenshot-Parser
poetry install

# Install Tesseract OCR (system dependency)
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-vie

# macOS:
brew install tesseract tesseract-lang

# Run the application
poetry run snap-transact --help
```

## 💻 Usage

### Basic Usage

```bash
# Process a single image
snap-transact process images/transaction1.png

# Process all images in the images directory
snap-transact process images/

# Specify output file in output directory
snap-transact process images/ --output output/january_transactions.csv

# Enable verbose logging
snap-transact process images/ --verbose
```

### Advanced Usage

```bash
# Use custom configuration
snap-transact process images/ --config config.yaml

# Process with specific output location
snap-transact process images/ --output output/monthly_report.csv

# Get version information
snap-transact --version

# Show help
snap-transact --help
```

### Configuration

Create a `config.yaml` file to customize OCR and processing settings:

```yaml
ocr:
  language: "eng+vie"  # OCR languages
  oem: 3              # OCR Engine Mode
  psm: 6              # Page Segmentation Mode
  dpi: 300           # Image DPI
  preprocess: true   # Enable image preprocessing

output_format: "csv"
max_image_size: 10000000  # 10MB limit
log_level: "INFO"

# Optional: Sentry error tracking
sentry_dsn: "your-sentry-dsn-here"
```

### Environment Variables

You can also configure the application using environment variables:

```bash
export SNAP_TRANSACT_LOG_LEVEL=DEBUG
export SNAP_TRANSACT_OCR__LANGUAGE=eng+vie
export SNAP_TRANSACT_SENTRY_DSN=your-sentry-dsn
```

## 📊 Output Format

The application generates a CSV file with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `date` | Transaction date | `2024-03-15` |
| `amount` | Transaction amount | `1500000` |
| `description` | Transaction description | `Transfer to supplier` |
| `account` | Account information | `*1234` |
| `category` | Transaction category | `Transfer` |
| `reference` | Reference number | `TXN123456789` |
| `balance` | Account balance | `5000000` |
| `source_file` | Source image path | `image1.png` |
| `confidence` | OCR confidence score | `0.95` |

## 🏗️ Development

### Prerequisites

- Python 3.11+
- Poetry 1.8+
- Tesseract OCR
- Docker (optional)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/Transaction-Screenshot-Parser.git
cd Transaction-Screenshot-Parser

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Lint and format
poetry run ruff check .
poetry run ruff format .

# Type checking
poetry run mypy src/
```

### Project Structure

```
Transaction-Screenshot-Parser/
├── src/snap_transact/          # Main application code
│   ├── __init__.py
│   ├── main.py                 # CLI entrypoint
│   ├── core.py                 # Main orchestration logic
│   ├── ocr.py                  # OCR processing
│   ├── parser.py               # Transaction parsing
│   ├── models.py               # Pydantic models
│   └── utils.py                # Helper functions
├── tests/                      # Test suite
│   ├── test_parser.py
│   └── fixtures/               # Test data
├── .github/workflows/          # CI/CD pipelines
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Local development
├── pyproject.toml             # Project configuration
└── README.md
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov --cov-report=html

# Run specific test file
poetry run pytest tests/test_parser.py

# Run with verbose output
poetry run pytest -v

# Run tests in Docker
docker-compose --profile test up test
```

### Docker Development

```bash
# Build development image
docker-compose build snap-transact-dev

# Run development container
docker-compose --profile dev up snap-transact-dev

# Run tests in container
docker-compose --profile test up test
```

## 🔧 Architecture

### Technology Stack

- **CLI Framework**: Typer 0.12+ for intuitive command-line interfaces
- **Image Processing**: Pillow 10.4+ for robust image handling
- **OCR Engine**: Pytesseract 0.3+ (Tesseract 5 wrapper)
- **Data Processing**: Pandas 2.2+ for CSV export and data manipulation
- **Configuration**: Pydantic 2.8+ for settings validation
- **Logging**: Loguru 0.7+ for structured logging
- **Testing**: pytest 8.2+ with coverage reporting
- **Code Quality**: Ruff + MyPy for linting and type checking

### Performance Targets

- ⚡ **Processing Speed**: ≤ 3 seconds per image
- 🐳 **Docker Image Size**: ≤ 350 MB
- 🧪 **Test Coverage**: ≥ 85%
- 🔍 **OCR Accuracy**: Optimized for Vietnamese banking screenshots

## 📝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`poetry run pytest && poetry run ruff check .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

We use:
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Conventional Commits** for commit messages
- **Pre-commit hooks** for automated checks

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📚 **Documentation**: [GitHub Wiki](https://github.com/your-org/Transaction-Screenshot-Parser/wiki)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-org/Transaction-Screenshot-Parser/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-org/Transaction-Screenshot-Parser/discussions)
- 📧 **Email**: team@yourcompany.com

## 🙏 Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for the powerful OCR engine
- [Typer](https://typer.tiangolo.com/) for the excellent CLI framework
- [Poetry](https://python-poetry.org/) for dependency management

---

**Made with ❤️ by the SnapTransact Team**
