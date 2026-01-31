# Architecture Patterns

**Project:** PubCheck - PDF Design Compliance Checker
**Researched:** 2026-01-31
**Confidence:** HIGH (verified with official documentation)

---

## Recommended Architecture

PubCheck follows a **layered pipeline architecture** optimized for local-first operation. The system separates concerns into distinct layers while maintaining a unified data flow through a multi-pass processing pipeline.

```
+------------------+     +------------------+     +------------------+
|   Presentation   |     |    Processing    |     |    Storage       |
|     Layer        |     |     Pipeline     |     |     Layer        |
+------------------+     +------------------+     +------------------+
| - Upload Page    |     | - Validator      |     | - File System    |
| - Settings Page  | --> | - Extractor      | --> | - Session Store  |
| - Review Page    |     | - Rule Checker   |     | - YAML Configs   |
| - Static Assets  |     | - AI Verifier    |     | - JSON Learnings |
+------------------+     +------------------+     +------------------+
        |                        |                        |
        v                        v                        v
+---------------------------------------------------------------+
|                        FastAPI Core                           |
|  - Routing / Endpoints                                        |
|  - Background Tasks                                           |
|  - Dependency Injection                                       |
+---------------------------------------------------------------+
```

### Why FastAPI over Flask

For PubCheck, **FastAPI** is recommended because:

| Factor | FastAPI | Flask |
|--------|---------|-------|
| Async I/O | Native async/await | Requires extensions |
| Background tasks | Built-in `BackgroundTasks` | Needs Celery/RQ |
| Type safety | Pydantic validation | Manual |
| API documentation | Auto-generated OpenAPI | Manual |
| Performance | 5-10x faster | Adequate |

FastAPI's built-in `BackgroundTasks` is ideal for PDF processing without needing external task queues like Celery.

**Source:** [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

---

## Component Architecture

### Layer 1: Presentation (HTML Pages)

Three static HTML pages served by FastAPI with JavaScript for interactivity.

| Page | Responsibility | API Calls |
|------|----------------|-----------|
| `upload.html` | File upload, format detection | `POST /api/upload`, `GET /api/status/{id}` |
| `settings.html` | Rule configuration, profile management | `GET/PUT /api/settings`, `GET /api/profiles` |
| `review.html` | Results display, AI verification, export | `GET /api/results/{id}`, `POST /api/verify`, `POST /api/export` |

**Pattern:** Keep pages stateless. All state lives in the backend session.

### Layer 2: API Routes

```
api/
  routes/
    upload.py       # File upload and processing initiation
    settings.py     # Configuration management
    review.py       # Results and verification
    export.py       # Output generation
```

Each route file handles a specific domain. Routes are thin wrappers that:
1. Validate input (Pydantic)
2. Call service layer
3. Return structured response

### Layer 3: Services (Business Logic)

```
services/
  upload_service.py     # Orchestrates file handling
  processing_service.py # Manages the 4-pass pipeline
  settings_service.py   # Reads/writes configuration
  ai_service.py         # Claude API integration
  export_service.py     # Report generation
```

**Key principle:** Services contain ALL business logic. Routes and pipeline stages only orchestrate.

### Layer 4: Processing Pipeline

```
pipeline/
  base.py           # Abstract stage interface
  validator.py      # Pass 1: PDF validation
  extractor.py      # Pass 2: Content extraction
  checker.py        # Pass 3: Rule checking
  verifier.py       # Pass 4: AI verification
  orchestrator.py   # Pipeline coordinator
```

### Layer 5: Storage

```
storage/
  session_store.py  # In-progress review state
  config_loader.py  # YAML configuration
  learnings_store.py # JSON learnings persistence
  file_manager.py   # Uploaded file handling
```

---

## Data Flow

### Complete Processing Flow

```
[User Upload]
      |
      v
+-------------+     +---------------+     +---------------+     +-------------+
|   UPLOAD    | --> |   VALIDATE    | --> |   EXTRACT     | --> |    CHECK    |
| (receives   |     | (PDF valid?   |     | (text, images |     | (rules vs   |
|  PDF file)  |     |  format OK?)  |     |  tables, meta)|     |  content)   |
+-------------+     +---------------+     +---------------+     +-------------+
      |                                                               |
      v                                                               v
+-------------+                                               +-------------+
|   STORE     |                                               |   VERIFY    |
| (save to    | <-------------------------------------------- | (Claude AI  |
|  session)   |                                               |  confirms)  |
+-------------+                                               +-------------+
      |
      v
+-------------+     +---------------+
|   REVIEW    | --> |    EXPORT     |
| (display    |     | (PDF report,  |
|  results)   |     |  JSON, etc)   |
+-------------+     +---------------+
```

### Data Structures at Each Stage

**Stage 1: Upload**
```python
class UploadRequest:
    file: UploadFile
    profile: str = "default"

class UploadResponse:
    session_id: str
    filename: str
    status: Literal["queued", "processing", "complete", "error"]
```

**Stage 2: Validation**
```python
class ValidationResult:
    is_valid: bool
    pdf_version: str
    page_count: int
    file_size_bytes: int
    issues: list[ValidationIssue]

class ValidationIssue:
    severity: Literal["error", "warning", "info"]
    code: str
    message: str
    page: int | None
```

**Stage 3: Extraction**
```python
class ExtractionResult:
    text_content: dict[int, str]       # page_num -> text
    images: list[ImageInfo]
    tables: list[TableInfo]
    metadata: DocumentMetadata
    fonts: list[FontInfo]
    colors: list[ColorInfo]

class ImageInfo:
    page: int
    bbox: tuple[float, float, float, float]
    width: int
    height: int
    color_space: str
    dpi: float
```

**Stage 4: Rule Checking**
```python
class CheckResult:
    rule_id: str
    rule_name: str
    passed: bool
    severity: Literal["error", "warning", "info"]
    details: str
    affected_pages: list[int]
    evidence: dict  # What triggered pass/fail
    needs_ai_verification: bool

class CheckingSummary:
    total_rules: int
    passed: int
    failed: int
    warnings: int
    results: list[CheckResult]
```

**Stage 5: AI Verification**
```python
class VerificationRequest:
    check_result: CheckResult
    extracted_content: ExtractionResult
    rule_definition: RuleConfig

class VerificationResult:
    original_result: CheckResult
    ai_agrees: bool
    ai_confidence: float
    ai_reasoning: str
    corrected_result: CheckResult | None
```

**Final Output**
```python
class ReviewSession:
    session_id: str
    filename: str
    upload_time: datetime
    status: str
    validation: ValidationResult
    extraction: ExtractionResult
    checking: CheckingSummary
    verification: list[VerificationResult]
    learnings: list[Learning]
```

---

## Processing Pipeline Pattern

### Recommended: Synchronous Pipeline with Background Execution

For PubCheck, use **synchronous passes within an async background task**:

```python
from fastapi import BackgroundTasks

@app.post("/api/upload")
async def upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    session_store: SessionStore = Depends(get_session_store)
):
    # Create session immediately
    session_id = str(uuid.uuid4())
    session_store.create(session_id, filename=file.filename)

    # Save file
    file_path = await save_upload(file, session_id)

    # Queue processing in background
    background_tasks.add_task(
        process_document,
        session_id=session_id,
        file_path=file_path,
        session_store=session_store
    )

    # Return immediately with session ID
    return {"session_id": session_id, "status": "processing"}
```

### Pipeline Orchestrator

```python
class PipelineOrchestrator:
    def __init__(
        self,
        validator: Validator,
        extractor: Extractor,
        checker: RuleChecker,
        verifier: AIVerifier,
        session_store: SessionStore
    ):
        self.stages = [validator, extractor, checker, verifier]
        self.session_store = session_store

    async def process(self, session_id: str, file_path: Path) -> None:
        """Process document through all pipeline stages."""
        context = PipelineContext(session_id=session_id, file_path=file_path)

        for stage in self.stages:
            try:
                self.session_store.update_status(
                    session_id,
                    f"processing:{stage.name}"
                )
                context = await stage.process(context)

                if context.should_abort:
                    break

            except Exception as e:
                self.session_store.update_status(session_id, "error")
                self.session_store.set_error(session_id, str(e))
                raise

        self.session_store.update_status(session_id, "complete")
        self.session_store.set_results(session_id, context.to_results())
```

### Stage Interface

```python
from abc import ABC, abstractmethod

class PipelineStage(ABC):
    name: str

    @abstractmethod
    async def process(self, context: PipelineContext) -> PipelineContext:
        """Process and return updated context."""
        pass

    def can_skip(self, context: PipelineContext) -> bool:
        """Override to conditionally skip this stage."""
        return False
```

### Why Synchronous Within Background Task?

| Approach | Pros | Cons | Use When |
|----------|------|------|----------|
| **Sync in BackgroundTasks** | Simple, predictable order, easy debugging | Single worker | Local-first, < 10 concurrent users |
| **Async with asyncio.gather** | Parallel stage execution possible | Complex coordination | Independent stages |
| **Celery/RQ** | Multi-process, fault-tolerant | Heavy setup, overkill for local | Server deployment, many users |

For PubCheck's local-first nature, **BackgroundTasks** is the right choice:
- No external dependencies (Redis, RabbitMQ)
- Simpler deployment
- Adequate for single-user local use

**Source:** [FastAPI BackgroundTasks Documentation](https://fastapi.tiangolo.com/tutorial/background-tasks/)

---

## State Management

### Session Storage Strategy

For local-first operation, use **file-based session storage**:

```
data/
  sessions/
    {session_id}/
      metadata.json     # Session state
      upload.pdf        # Original file
      results.json      # Processing results

  config/
    rules/
      default.yaml      # Default rule profile
      strict.yaml       # Strict profile
      custom/           # User-defined profiles

  learnings/
    learnings.json      # AI learnings database
```

### Session Store Implementation

```python
from pathlib import Path
import json
from datetime import datetime

class FileSessionStore:
    def __init__(self, base_path: Path = Path("data/sessions")):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create(self, session_id: str, filename: str) -> None:
        session_dir = self.base_path / session_id
        session_dir.mkdir(exist_ok=True)

        metadata = {
            "session_id": session_id,
            "filename": filename,
            "created_at": datetime.utcnow().isoformat(),
            "status": "created",
            "error": None
        }
        self._write_json(session_dir / "metadata.json", metadata)

    def get_status(self, session_id: str) -> dict:
        return self._read_json(self.base_path / session_id / "metadata.json")

    def update_status(self, session_id: str, status: str) -> None:
        metadata = self.get_status(session_id)
        metadata["status"] = status
        metadata["updated_at"] = datetime.utcnow().isoformat()
        self._write_json(
            self.base_path / session_id / "metadata.json",
            metadata
        )

    def set_results(self, session_id: str, results: dict) -> None:
        self._write_json(
            self.base_path / session_id / "results.json",
            results
        )

    def get_results(self, session_id: str) -> dict | None:
        results_path = self.base_path / session_id / "results.json"
        if results_path.exists():
            return self._read_json(results_path)
        return None

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> None:
        """Remove sessions older than max_age_hours."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        for session_dir in self.base_path.iterdir():
            if session_dir.is_dir():
                metadata = self._read_json(session_dir / "metadata.json")
                created = datetime.fromisoformat(metadata["created_at"])
                if created < cutoff:
                    shutil.rmtree(session_dir)
```

### Learnings Persistence

```python
class LearningsStore:
    def __init__(self, path: Path = Path("data/learnings/learnings.json")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def add_learning(self, learning: Learning) -> None:
        learnings = self._read()
        learnings.append(learning.dict())
        self._write(learnings)

    def get_relevant_learnings(
        self,
        rule_id: str,
        context: str
    ) -> list[Learning]:
        """Find learnings that might apply to this check."""
        learnings = self._read()
        return [
            Learning(**l) for l in learnings
            if l["rule_id"] == rule_id or self._context_matches(l, context)
        ]
```

---

## AI Integration Pattern

### Claude API Service

```python
from anthropic import Anthropic
from pydantic import BaseModel
import asyncio

class VerificationResult(BaseModel):
    agrees_with_check: bool
    confidence: float  # 0.0 to 1.0
    reasoning: str
    suggested_correction: str | None = None

class AIVerificationService:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250514"

    async def verify_check(
        self,
        rule: RuleConfig,
        check_result: CheckResult,
        extracted_content: dict,
        relevant_learnings: list[Learning]
    ) -> VerificationResult:
        """Use Claude to verify a rule check result."""

        prompt = self._build_verification_prompt(
            rule, check_result, extracted_content, relevant_learnings
        )

        # Use structured outputs for guaranteed schema
        response = self.client.messages.parse(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            output_format=VerificationResult
        )

        return response.parsed_output

    def _build_verification_prompt(
        self,
        rule: RuleConfig,
        check_result: CheckResult,
        extracted_content: dict,
        learnings: list[Learning]
    ) -> str:
        learnings_context = ""
        if learnings:
            learnings_context = "\n\n## Previous Learnings\n"
            for l in learnings[:5]:  # Limit to 5 most relevant
                learnings_context += f"- {l.description}\n"

        return f"""You are verifying a design compliance check on a PDF document.

## Rule Being Checked
- **ID:** {rule.id}
- **Name:** {rule.name}
- **Description:** {rule.description}
- **Expected:** {rule.expected_value}

## Automated Check Result
- **Passed:** {check_result.passed}
- **Details:** {check_result.details}
- **Evidence:** {json.dumps(check_result.evidence, indent=2)}

## Extracted Content
{json.dumps(extracted_content, indent=2)}
{learnings_context}

## Your Task
Verify whether the automated check result is correct. Consider:
1. Does the extracted content actually violate/satisfy the rule?
2. Are there edge cases the automated check might have missed?
3. Is there any ambiguity in the rule that affects this check?

Provide your assessment with confidence level and reasoning."""
```

### Error Handling and Rate Limits

```python
import time
from functools import wraps

class AIServiceError(Exception):
    pass

class RateLimitError(AIServiceError):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after}s")

def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying API calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except anthropic.RateLimitError as e:
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_after)
                    last_exception = RateLimitError(retry_after)
                except anthropic.APIError as e:
                    delay = base_delay * (2 ** attempt)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                    last_exception = AIServiceError(str(e))
            raise last_exception
        return wrapper
    return decorator

class AIVerificationService:
    @with_retry(max_retries=3)
    async def verify_check(self, ...):
        # ... implementation
```

### Cost Optimization Strategies

| Strategy | Implementation | Savings |
|----------|----------------|---------|
| **Selective verification** | Only verify failed checks or low-confidence passes | 50-80% |
| **Batch similar checks** | Group related checks in one prompt | 30-50% |
| **Use smaller models first** | Haiku for simple, Sonnet for complex | 40-60% |
| **Cache responses** | Hash prompt content, reuse identical requests | Variable |

```python
class AIVerificationService:
    def should_verify(self, check_result: CheckResult) -> bool:
        """Determine if AI verification is needed."""
        # Always verify failures
        if not check_result.passed:
            return True

        # Verify checks flagged as needing verification
        if check_result.needs_ai_verification:
            return True

        # Verify checks for complex rules
        if check_result.rule_id in self.complex_rules:
            return True

        return False

    def select_model(self, check_result: CheckResult) -> str:
        """Select appropriate model based on complexity."""
        if check_result.rule_id in self.simple_rules:
            return "claude-haiku-3-5-20240307"  # Cheaper, faster
        return "claude-sonnet-4-5-20250514"  # More capable
```

### Structured Outputs for Reliable Parsing

Using Pydantic with Claude's structured outputs guarantees valid responses:

```python
from pydantic import BaseModel, Field
from typing import Literal

class VerificationResult(BaseModel):
    """AI verification result with guaranteed schema."""
    agrees_with_check: bool = Field(
        description="Whether AI agrees with the automated check result"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this assessment (0.0 to 1.0)"
    )
    reasoning: str = Field(
        description="Explanation of the assessment"
    )
    issue_type: Literal["false_positive", "false_negative", "correct", "uncertain"] = Field(
        description="Classification of the check result"
    )
    suggested_correction: str | None = Field(
        default=None,
        description="If disagreeing, what the correct result should be"
    )

# Usage
response = client.messages.parse(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}],
    output_format=VerificationResult
)

# response.parsed_output is a validated VerificationResult instance
```

**Source:** [Claude Structured Outputs Documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Monolithic Route Handlers

**What:** Putting all logic in route functions

```python
# BAD
@app.post("/api/upload")
async def upload(file: UploadFile):
    # 200 lines of validation, extraction, checking...
```

**Why bad:** Untestable, unmaintainable, violates single responsibility

**Instead:** Thin routes that call service layer

```python
# GOOD
@app.post("/api/upload")
async def upload(
    file: UploadFile,
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_service.handle_upload(file)
```

### Anti-Pattern 2: Global State

**What:** Using module-level variables for state

```python
# BAD
_current_session = None
_processing_results = {}
```

**Why bad:** Thread-unsafe, untestable, breaks with multiple users

**Instead:** Dependency injection with session stores

```python
# GOOD
@app.get("/api/status/{session_id}")
async def get_status(
    session_id: str,
    session_store: SessionStore = Depends(get_session_store)
):
    return session_store.get_status(session_id)
```

### Anti-Pattern 3: Sync Claude Calls in Request

**What:** Making synchronous AI calls that block the response

```python
# BAD
@app.post("/api/verify")
def verify(request: VerifyRequest):
    result = claude_client.messages.create(...)  # Blocks for seconds
    return result
```

**Why bad:** Blocks server, poor UX, timeout risk

**Instead:** Background processing with status polling

```python
# GOOD
@app.post("/api/verify")
async def verify(
    request: VerifyRequest,
    background_tasks: BackgroundTasks
):
    verification_id = str(uuid.uuid4())
    background_tasks.add_task(run_verification, verification_id, request)
    return {"verification_id": verification_id, "status": "processing"}

@app.get("/api/verify/{verification_id}")
async def get_verification_status(verification_id: str):
    return session_store.get_verification_status(verification_id)
```

### Anti-Pattern 4: Hardcoded Configuration

**What:** Embedding rules and settings in code

**Why bad:** Requires code changes to modify behavior

**Instead:** External YAML configuration

```yaml
# config/rules/default.yaml
rules:
  - id: font_size_minimum
    name: Minimum Font Size
    description: Body text must be at least 10pt
    category: typography
    severity: error
    check:
      type: font_size
      min_value: 10
      unit: pt
      applies_to: body_text
```

---

## Project Structure

```
pubcheck/
  app/
    __init__.py
    main.py                 # FastAPI app initialization
    dependencies.py         # Dependency injection setup

    api/
      __init__.py
      routes/
        upload.py
        settings.py
        review.py
        export.py

    services/
      __init__.py
      upload_service.py
      processing_service.py
      settings_service.py
      ai_service.py
      export_service.py

    pipeline/
      __init__.py
      base.py               # Abstract stage interface
      context.py            # Pipeline context object
      orchestrator.py       # Pipeline coordinator
      stages/
        validator.py
        extractor.py
        checker.py
        verifier.py

    storage/
      __init__.py
      session_store.py
      config_loader.py
      learnings_store.py
      file_manager.py

    models/
      __init__.py
      requests.py           # API request models
      responses.py          # API response models
      domain.py             # Domain models
      config.py             # Configuration models

  static/
    css/
    js/
    pages/
      upload.html
      settings.html
      review.html

  config/
    rules/
      default.yaml
      strict.yaml
    settings.yaml

  data/
    sessions/               # Session storage (gitignored)
    learnings/
      learnings.json

  tests/
    unit/
    integration/
    fixtures/
      sample_pdfs/

  requirements.txt
  pyproject.toml
```

---

## Suggested Build Order

Based on dependencies and incremental value:

### Phase 1: Foundation (Week 1)
Build order within phase:

1. **Project scaffolding** - FastAPI app, directory structure
2. **File upload endpoint** - Accept PDF, save to disk
3. **Session store** - Track upload status
4. **Basic HTML pages** - Upload form, status display

**Milestone:** Can upload PDF and see it saved

### Phase 2: Extraction (Week 2)
1. **PDF validation** - Check valid PDF, get metadata
2. **Text extraction** - Extract text content per page
3. **Image extraction** - Identify images, get properties
4. **Extraction API** - Endpoint to view extracted content

**Milestone:** Can upload PDF and see extracted content

### Phase 3: Rule Checking (Week 3)
1. **YAML config loader** - Parse rule definitions
2. **Rule checker framework** - Abstract rule interface
3. **Basic rules** - Font size, image resolution, page count
4. **Checking API** - Run checks, return results

**Milestone:** Can check PDF against rules, see pass/fail

### Phase 4: AI Verification (Week 4)
1. **Claude API integration** - Basic message sending
2. **Structured outputs** - Pydantic response models
3. **Verification prompts** - Build effective prompts
4. **Verification API** - Trigger and retrieve verification

**Milestone:** AI can verify check results

### Phase 5: Review & Export (Week 5)
1. **Review page** - Display all results
2. **Learnings system** - Record and apply learnings
3. **Export service** - Generate reports (PDF, JSON)
4. **Settings page** - Configure rules, profiles

**Milestone:** Complete end-to-end workflow

### Phase 6: Polish (Week 6)
1. **Error handling** - Graceful failures, helpful messages
2. **Progress tracking** - Real-time status updates
3. **Performance** - Optimize extraction, caching
4. **Testing** - Unit and integration tests

**Milestone:** Production-ready local tool

---

## Sources

### Official Documentation
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Claude Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Claude Prompt Engineering](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview)

### Architecture Patterns
- [Modern FastAPI Architecture Patterns](https://medium.com/algomart/modern-fastapi-architecture-patterns-for-scalable-production-systems-41a87b165a8b)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [Pipeline Pattern in Python](https://pybit.es/articles/a-practical-example-of-the-pipeline-pattern-in-python/)

### PDF Processing
- [Python PDF Extractors Comparison 2025](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/en/latest/about.html)
- [Docling Pipeline Architecture](https://deepwiki.com/docling-project/docling/5.1-cli-options-and-parameters)

### Local-First Architecture
- [Local-First Web Application Architecture](https://plainvanillaweb.com/blog/articles/2025-07-16-local-first-architecture/)
- [Expo Local-First Guide](https://docs.expo.dev/guides/local-first/)
- [Offline-First Architecture Patterns](https://medium.com/@jusuftopic/offline-first-architecture-designing-for-reality-not-just-the-cloud-e5fd18e50a89)
