from fastapi import APIRouter, HTTPException, Request

from src.config import settings
from src.data.layout import business_dir, calendar_file, split_dir
from src.models import Question
from src.services.ingest import IngestService
from src.services.qa import QAService

router = APIRouter(prefix="/ask", tags=["ask"])


def _service(request: Request) -> QAService:
    if request.app.state.qa is None:
        root = split_dir(settings.data_dir, settings.split)
        request.app.state.qa = QAService(
            IngestService(settings.work_dir, calendar=calendar_file(root)),
            package_dir=lambda business_id: business_dir(root, business_id),
        )
    return request.app.state.qa


@router.post("")
def ask(question: Question, request: Request) -> dict:
    """Answer one question and return the trace (candidates, SQL, votes).

    For debugging and the demo UI in app/; the competition runs `python -m src` in batch.
    """
    try:
        service = _service(request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    answer, trace = service.answer(question)
    return {"answer": answer.model_dump(), "trace": trace}
