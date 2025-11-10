# Project Restructuring Plan

## Current Issues

1. ❌ **Poor separation of concerns**: crawler, scheduler, and API files mixed
2. ❌ **Test files scattered in root**: Multiple test_*.py files cluttering root directory
3. ❌ **No clear src/ structure**: Code spread across api/, crawler/, scheduler/ at root level
4. ❌ **Documentation scattered**: Multiple .md files in root
5. ❌ **Temporary scripts in root**: batch_fix_tests.py, add_headers.py, etc.
6. ❌ **No clear entry points**: Multiple runner scripts without clear purpose

## Target Structure (Evaluation Criteria Compliant)

```
web_crawler_project/
│
├── README.md                          # Main project documentation
├── requirements.txt                   # Python dependencies
├── .gitignore                        # Git ignore rules
├── .env                              # Environment variables (not in git)
│
├── run_crawler.py                    # Entry point: Run crawler
├── run_scheduler.py                  # Entry point: Run scheduler
├── run_api.py                        # Entry point: Run API server
│
├── src/                              # Main source code
│   ├── __init__.py
│   │
│   ├── crawler/                      # Part 1: Crawler
│   │   ├── __init__.py
│   │   ├── models.py                 # Pydantic models for book data
│   │   ├── settings.py               # Crawler-specific settings
│   │   ├── crawler.py                # Main crawler logic
│   │   ├── html_storage.py           # GridFS HTML storage
│   │   └── logging_config.py         # Crawler logging setup
│   │
│   ├── scheduler/                    # Part 2: Scheduler & Change Detection
│   │   ├── __init__.py
│   │   ├── scheduler.py              # APScheduler setup
│   │   ├── jobs.py                   # Scheduled job definitions
│   │   ├── change_tracker.py         # Change detection logic
│   │   ├── fingerprinting.py         # Content hash/fingerprint
│   │   ├── notifications.py          # Email/log alerts
│   │   ├── reporting.py              # Daily reports (JSON/CSV)
│   │   └── settings.py               # Scheduler-specific settings
│   │
│   ├── api/                          # Part 3: RESTful API
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app initialization
│   │   ├── dependencies.py           # FastAPI dependencies
│   │   ├── exception_handlers.py     # Global exception handlers
│   │   │
│   │   ├── routes/                   # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── books.py              # GET /books, GET /books/{id}
│   │   │   ├── changes.py            # GET /changes
│   │   │   └── health.py             # GET /health
│   │   │
│   │   ├── middleware/               # Custom middleware
│   │   │   ├── __init__.py
│   │   │   ├── rate_limiter.py       # Rate limiting (100 req/hour)
│   │   │   └── logging_middleware.py # Request/response logging
│   │   │
│   │   ├── auth/                     # Authentication
│   │   │   ├── __init__.py
│   │   │   └── api_key.py            # API key validation
│   │   │
│   │   ├── models/                   # API data models
│   │   │   ├── __init__.py
│   │   │   └── schemas.py            # Pydantic response models
│   │   │
│   │   ├── utils/                    # API utilities
│   │   │   ├── __init__.py
│   │   │   └── query_builder.py      # MongoDB query builder
│   │   │
│   │   └── settings.py               # API-specific settings
│   │
│   └── utils/                        # Shared utilities
│       ├── __init__.py
│       ├── database.py               # MongoDB connection (shared)
│       ├── logging.py                # Logging utilities (shared)
│       └── config.py                 # Base configuration (shared)
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration (shared fixtures)
│   │
│   ├── unit/                         # Unit tests
│   │   ├── __init__.py
│   │   ├── conftest.py               # Unit test fixtures
│   │   ├── test_crawler_models.py
│   │   ├── test_api_models.py
│   │   ├── test_auth.py
│   │   ├── test_query_builder.py
│   │   ├── test_rate_limiter.py
│   │   ├── test_fingerprinting.py
│   │   └── test_change_tracker.py
│   │
│   └── integration/                  # Integration tests
│       ├── __init__.py
│       ├── conftest.py               # Integration test fixtures
│       ├── test_books_endpoint.py
│       ├── test_book_detail_endpoint.py
│       ├── test_changes_endpoint.py
│       ├── test_auth_and_rate_limit.py
│       └── test_error_handling.py
│
├── scripts/                          # Utility scripts
│   ├── generate_api_key.py           # Generate API keys
│   ├── check_db_health.py            # Database health check
│   └── seed_test_data.py             # Seed test data
│
├── config/                           # Configuration files
│   ├── .env.example                  # Example environment file
│   └── logging.yaml                  # Logging configuration (optional)
│
├── docs/                             # Documentation
│   ├── API_DOCUMENTATION.md          # Complete API reference
│   ├── POSTMAN_GUIDE.md              # Postman collection guide
│   ├── DEPLOYMENT.md                 # Deployment instructions
│   └── MONGODB_SCHEMA.md             # MongoDB schema documentation
│
├── postman/                          # Postman collections
│   ├── Books_API_Collection.json
│   ├── Environment_Local.json
│   └── Environment_Production.json
│
├── logs/                             # Log files (generated, not in git)
├── reports/                          # Crawl reports (generated, not in git)
└── myvenv/                           # Virtual environment (not in git)
```

## Migration Steps

### Phase 1: Create New Structure (Steps 1-5)
1. Create all new directories under `src/`
2. Create `tests/unit/` and `tests/integration/` structure
3. Create `docs/`, `scripts/`, `config/`, `postman/` directories

### Phase 2: Move Files (Steps 6-8)
4. Move crawler files → `src/crawler/`
5. Move scheduler files → `src/scheduler/`
6. Move API files → `src/api/` (preserve sub-structure)
7. Move test files → `tests/unit/` and `tests/integration/`
8. Move documentation → `docs/`
9. Move Postman files → `postman/`
10. Move utility scripts → `scripts/`

### Phase 3: Update Imports (Step 9)
11. Update all import statements to use new paths
12. Update entry point scripts

### Phase 4: Clean Up (Step 10)
13. Remove temporary files from root
14. Remove old empty directories
15. Update .gitignore

### Phase 5: Documentation (Step 11)
16. Update README.md with new structure
17. Create MONGODB_SCHEMA.md
18. Update all documentation references

### Phase 6: Validation (Step 12)
19. Run all tests
20. Test crawler execution
21. Test scheduler execution
22. Test API server
23. Verify all imports work

## Files to Move

### From Root → src/crawler/
- No main.py exists yet (need to create crawler.py from existing logic)
- crawler/models.py → src/crawler/models.py
- crawler/settings.py → src/crawler/settings.py
- crawler/logging_config.py → src/crawler/logging_config.py

### From scheduler/ → src/scheduler/
- scheduler/scheduler.py → src/scheduler/scheduler.py
- scheduler/jobs.py → src/scheduler/jobs.py
- scheduler/change_tracker.py → src/scheduler/change_tracker.py
- scheduler/fingerprinting.py → src/scheduler/fingerprinting.py
- scheduler/notifications.py → src/scheduler/notifications.py
- scheduler/reporting.py → src/scheduler/reporting.py
- scheduler/settings.py → src/scheduler/settings.py
- scheduler/models.py → src/scheduler/models.py (if different from crawler)

### From api/ → src/api/
- Entire api/ directory structure preserved
- api/config.py → src/api/settings.py (rename for consistency)
- api/database.py → src/utils/database.py (shared utility)

### Test Files to Organize
- tests/ directory already exists with good structure
- Move any root-level test_*.py → tests/unit/ or delete if obsolete
- Keep existing tests/unit/ and tests/integration/ structure

### Documentation Files
- API_DOCUMENTATION.md → docs/
- POSTMAN_GUIDE.md → docs/
- PART3_IMPLEMENTATION_PLAN.md → docs/ (or delete)
- STEP12_LOGGING_SUMMARY.md → docs/ (or delete)

### Postman Files
- Books_API_Postman_Collection.json → postman/Books_API_Collection.json
- Books_API_Environment_Local.json → postman/Environment_Local.json
- Books_API_Environment_Production.json → postman/Environment_Production.json

### Scripts
- scripts/generate_api_key.py → Keep in scripts/
- Add more utility scripts as needed

### Files to Delete (Temporary/Obsolete)
- add_headers.py (temporary batch fix script)
- batch_fix_tests.py (temporary batch fix script)
- fix_integration_tests.py (temporary fix script)
- check_book_structure.py (temporary test script)
- test_*.py in root (move to tests/ or delete)
- run_scheduler.py (replace with new run_scheduler.py)

### Configuration
- .env → stays at root
- Create config/.env.example
- Keep requirements.txt at root

## Import Statement Updates

### Before (Current)
```python
from crawler.models import Book
from api.models.schemas import BookResponse
from api.auth.api_key import validate_api_key
```

### After (New Structure)
```python
from src.crawler.models import Book
from src.api.models.schemas import BookResponse
from src.api.auth.api_key import validate_api_key
from src.utils.database import get_database
```

## Entry Points

### run_crawler.py
```python
"""Entry point for running the web crawler."""
from src.crawler.crawler import run_crawler

if __name__ == "__main__":
    run_crawler()
```

### run_scheduler.py
```python
"""Entry point for running the scheduler."""
from src.scheduler.scheduler import start_scheduler

if __name__ == "__main__":
    start_scheduler()
```

### run_api.py
```python
"""Entry point for running the API server."""
import uvicorn
from src.api.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Benefits of New Structure

1. ✅ **Clear separation of concerns**: crawler, scheduler, API in separate modules
2. ✅ **Professional structure**: Follows Python best practices with src/ directory
3. ✅ **Easy navigation**: Clear folder hierarchy matching project requirements
4. ✅ **Shared utilities**: Common code in src/utils/ to avoid duplication
5. ✅ **Clean tests**: Unit and integration tests properly separated
6. ✅ **Organized docs**: All documentation in docs/ directory
7. ✅ **Clear entry points**: Three simple scripts to run each component
8. ✅ **Better for deployment**: Easier to package and deploy
9. ✅ **Meets evaluation criteria**: Exactly matches required folder structure

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Broken imports after moving | High | Update all imports systematically, test after each phase |
| Lost file during move | Medium | Use git to track changes, commit frequently |
| Tests fail after restructure | High | Run tests after each phase, fix imports immediately |
| Documentation out of sync | Low | Update docs in Phase 5 before final validation |

## Timeline Estimate

- Phase 1 (Directory creation): 10 minutes
- Phase 2 (File moves): 30 minutes
- Phase 3 (Import updates): 45 minutes
- Phase 4 (Cleanup): 15 minutes
- Phase 5 (Documentation): 20 minutes
- Phase 6 (Validation): 30 minutes

**Total: ~2.5 hours**

## Success Criteria

- ✅ All files in correct locations per new structure
- ✅ No files left in root except entry points, README, requirements.txt, .env, .gitignore
- ✅ All imports updated and working
- ✅ All 112 unit tests passing
- ✅ All 90 integration tests passing
- ✅ Crawler runs successfully
- ✅ Scheduler runs successfully
- ✅ API server starts and responds
- ✅ Documentation updated with new structure
- ✅ README reflects new folder organization

---

*Created: November 10, 2025*
