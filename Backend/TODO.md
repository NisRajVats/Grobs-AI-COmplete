# Resume Pipeline Fix - Make Parsing Async + Reliable
Status: [Paused - Windows CMD Issue] 🔄 Windows Migration Blocked

## 1. [BLOCKED] Database Migration
- Windows CMD doesn't support `cd && alembic` syntax
- Need: `cd Backend` then `alembic revision --autogenerate -m "add pipeline_status"` 
- Run manually in new PowerShell/VSCode terminal please
- Add `pipeline_status` JSON field to `Resume` model (default: `{"stage": "pending", "progress": 0, "error": null}`)
- Add `error_message` String field (nullable)
- `alembic revision --autogenerate -m "add_pipeline_status_fields"`
- `alembic upgrade head`

## 2. [PENDING] Update Resume Model
- Edit `Backend/app/models/resume.py`
- Add fields + relationships

## 3. [PENDING] Update resume_parse_worker.py
- Handle cloud storage: download via `cloud_storage_service.get_signed_url(file_path)` → `BytesIO` → parse
- Update `resume.status = "parsed"` → `resume.pipeline_status = {"stage": "parsed", "progress": 40}`
- Add error handling → set `pipeline_status.error`, `error_message`

## 4. [PENDING] Chain Celery Tasks
- Create `Backend/app/workers/resume_pipeline_tasks.py`: parse → embed → ats → match chain
- Tasks update `pipeline_status` progressively (20%→40%→60%→80%→100%)

## 5. [PENDING] Update upload_resume endpoint
- `Backend/app/routers/resume_router.py`: create resume → `chain(parse_task.s(...), embed_task.s(...))()`
- Return job_id for status polling

## 6. [PENDING] Fix get_pipeline_status()
- `Backend/app/services/resume_service/resume_pipeline.py`: prefer `resume.pipeline_status` → fallback legacy logic
- Fix log to show `status['current_status'] or "unknown"`

## 7. [PENDING] Install Dependencies + Test
- `pip install celery[redis]`
- `celery -A Backend.app.workers.celery_app worker --loglevel=info`
- Test upload → verify logs, status progression, parsing success
- Update tests: `Backend/tests/test_enhanced_resume_service.py`

## 8. [COMPLETED] Verify
- Upload resume → pipeline completes → status="completed", progress=100%
- No more stuck 20%/unknown

**Next step:** Database migration + model update

