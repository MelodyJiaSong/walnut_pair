# Walnut Pair Solution

A sophisticated walnut image processing and pair system that analyzes walnut images from multiple camera angles, extracts dimensional and visual features, and performs intelligent similarity comparisons to identify matching pairs.

## Overview

This solution processes walnut images captured from different camera angles (front, back, left, right, top, down), extracts physical dimensions and deep learning embeddings, and compares walnuts based on multiple similarity metrics to find the best matching pairs. The system uses advanced computer vision techniques, including ResNet50 for image embeddings and vector similarity search using PostgreSQL's pgvector extension.

## Executable Applications

### 1. Batch Processing Application (`app__batch/`)

The batch application processes walnut images from a filesystem directory and performs bulk operations:

- **Image Processing**: Scans a configured image directory, processes walnut images from multiple camera angles
- **Entity Creation**: Creates walnut entities from images, extracting dimensions and generating image embeddings
- **Comparison Processing**: Performs bulk comparisons between all walnuts using configurable similarity algorithms
- **Database Persistence**: Saves processed walnuts, images, embeddings, and comparison results to PostgreSQL

**Usage:**
```bash
python app__batch/main.py
```

**Configuration:** `app__batch/config.yml` (database connection, image root directory, algorithm parameters)

### 2. Web API Application (`app__webapi/`)

A FastAPI-based REST API that provides query endpoints for walnut pair results:

- **Query Endpoints**: Retrieve walnut comparisons, pair results, and similarity scores
- **Real-time Access**: Query processed walnut data and comparison results via HTTP endpoints
- **Interactive Documentation**: Swagger UI (`/docs`) and ReDoc (`/redoc`) for API exploration

**Usage:**
```bash
python app__webapi/main.py
# Or with uvicorn:
uvicorn app__webapi.main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation:** Available at `http://localhost:8000/docs` when running

**Configuration:** `app__webapi/config.yml` (database connection settings)

## Shared Library Code (`libs/`)

The `libs/` directory contains all shared business logic organized in layers following Clean Architecture principles:

### Layer Structure

- **`common/`**: Shared utilities, interfaces, enums, constants, and DI registry
- **`domain_layer/`**: Pure business logic (entities, value objects, domain services, factories)
- **`application_layer/`**: Application orchestration (commands, queries, DTOs, mappers)
- **`infrastructure_layer/`**: Technical implementations (database access, file readers, image processing services)

## Project Structure

```
walnut_pair/
├── app__batch/              # Batch processing application
│   ├── main.py             # Entry point
│   ├── application.py      # Application orchestration logic
│   ├── config.yml          # Batch configuration
│   └── di_container.py     # Dependency injection setup
│
├── app__webapi/            # FastAPI web application
│   ├── main.py             # FastAPI entry point
│   ├── controllers/        # API controllers (endpoints)
│   ├── routes.py          # Route constants
│   ├── dependencies.py    # FastAPI dependency injection
│   ├── di_container.py    # WebAPI DI container
│   └── config.yml         # WebAPI configuration
│
├── libs/                   # Shared library code
│   ├── common/            # Interfaces, enums, constants, DI registry
│   ├── domain_layer/      # Domain entities, value objects, services
│   ├── application_layer/ # Commands, queries, DTOs, mappers
│   └── infrastructure_layer/ # Database, file I/O, image processing
│
├── sql_scripts/            # Database schema and migrations
├── scripts/                # Utility scripts (dependency checking, etc.)
├── business_docs/          # Business documentation
│
├── ARCHITECTURE.md         # Detailed architecture documentation
├── CQRS_ARCHITECTURE.md    # CQRS pattern details
├── CODE_QUALITY.md         # Code quality guidelines
├── pyproject.toml          # Python project configuration
├── requirements.txt        # Python dependencies
├── mypy.ini                # Type checking configuration
└── Makefile                # Build and utility commands
```

## Architectural Patterns

### Domain-Driven Design (DDD)

The solution follows DDD principles with a pure domain layer:

- **Entities**: Domain entities with unique identities (e.g., `WalnutEntity`, `WalnutComparisonEntity`)
- **Value Objects**: Immutable value objects representing domain concepts (e.g., `WalnutDimensionValueObject`)
- **Domain Services**: Static services containing domain logic that doesn't belong to a single entity
- **Domain Factories**: Factory methods for creating entities with validation
- **Pure Domain Layer**: Domain layer has no dependencies on infrastructure or application layers

**Key Principles:**
- Domain operations return `Either[Success, DomainError]` for explicit error handling
- Entities are created through factory methods, not direct instantiation
- Business invariants are enforced in the domain layer

### CQRS (Command Query Responsibility Segregation)

The solution separates read and write operations:

- **Commands**: Modify state (create, update, delete operations)
  - Command objects contain all required parameters
  - Command handlers orchestrate domain operations
  - Commands are dispatched via `CommandDispatcher`
  
- **Queries**: Read-only operations
  - Return DTOs for API consumption
  - Return Domain Entities for internal domain operations
  - Queries use infrastructure readers to fetch data

**Benefits:**
- Clear separation of concerns
- Independent optimization of read/write paths
- Domain logic isolated in entities, not handlers

### Dependency Injection (DI) / IoC Container

The solution uses interface-based dependency injection:

- **Interfaces**: Defined in `libs/common/interfaces.py`
- **DI Container**: Uses `dependency-injector` framework
- **Registration**: Each application has its own DI container setup
  - `app__batch/di_container.py` - Batch application DI setup
  - `app__webapi/dependencies.py` - WebAPI FastAPI dependency injection
- **Automatic Resolution**: Container resolves dependencies based on type hints

**Key Rules:**
- Domain layer has NO DI (uses static services)
- Application and Infrastructure layers use DI
- Dependencies flow inward: Infrastructure → Application → Domain

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL with pgvector extension
- Image directory with walnut images organized by walnut ID

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database:**
   ```bash
   # Run initial schema script
   psql -U your_user -d your_database -f sql_scripts/initial.sql
   ```

3. **Configure applications:**
   - Edit `app__batch/config.yml` for batch processing settings
   - Edit `app__webapi/config.yml` for API database connection

### Running the Applications

**Batch Processing:**
```bash
python app__batch/main.py
```

**Web API:**
```bash
python app__webapi/main.py
# Or: uvicorn app__webapi.main:app --reload
```

## Development

### Code Quality

The project uses strict code quality standards:

- **Type Checking**: `mypy` with strict mode
- **Linting**: `flake8` with multiple plugins
- **Formatting**: `black` and `isort` for consistent code style
- **Line Length**: 120 characters (configured in `pyproject.toml`)

**Run checks:**
```bash
make check          # Run all checks
make type-check     # Type checking only
make lint           # Linting only
make format         # Auto-format code
make check-deps     # Check dependency constraints
```

### Key Conventions

- **File Naming**: Use double underscore (`__`) to separate words: `walnut__entity.py`
- **Type Hints**: All variables, parameters, and return values must have explicit type hints
- **Naming**: PascalCase for classes, snake_case for functions/variables, UPPER_SNAKE_CASE for constants
- **Layer Boundaries**: Strict dependency rules enforced (see `ARCHITECTURE.md`)

### Important Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Comprehensive architecture documentation (MUST READ)
- **[CQRS_ARCHITECTURE.md](CQRS_ARCHITECTURE.md)**: Detailed CQRS pattern implementation
- **[CODE_QUALITY.md](CODE_QUALITY.md)**: Code quality standards and guidelines

## Data Flow

1. **Image Processing**: Batch app scans image directory → Creates walnut entities from images
2. **Feature Extraction**: Generates image embeddings using ResNet50 → Stores in database
3. **Comparison**: Compares walnuts using configurable similarity algorithms → Stores results
4. **Query**: Web API queries comparison results → Returns DTOs to clients

## Technology Stack

- **Python 3.12+**: Core language
- **FastAPI**: Web framework for REST API
- **SQLAlchemy 2.0**: ORM for database access
- **PostgreSQL + pgvector**: Database with vector similarity support
- **PyTorch/TorchVision**: Deep learning for image embeddings (ResNet50)
- **OpenCV**: Computer vision operations
- **dependency-injector**: Dependency injection framework
- **structlog**: Structured logging

## License

See [LICENSE](LICENSE) file for details.
