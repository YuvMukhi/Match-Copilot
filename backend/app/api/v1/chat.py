import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.rate_limiter import rate_limit_dependency
from app.db.models import ChatMessage, FantasyTeam, Match
from app.db.session import get_db
from app.llm.client import llm_client
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(rate_limit_dependency),
) -> ChatResponse:
    # Validate match and team existence
    match = db.query(Match).filter_by(id=req.match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{req.match_id}' not found",
        )

    team = db.query(FantasyTeam).filter_by(id=req.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fantasy team with id '{req.team_id}' not found",
        )

    # Save user message
    user_msg = ChatMessage(
        match_id=req.match_id,
        team_id=req.team_id,
        over_number=req.over,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    db.commit()

    # Invoke LLM Client with tool calling
    logger.info(f"Processing chat for team {req.team_id} at over {req.over}: {req.message}")
    response = await llm_client.chat(
        session=db,
        match_id=req.match_id,
        team_id=req.team_id,
        over=req.over,
        message=req.message,
        language=req.language,
    )

    # Save assistant message with evidence
    evidence_dump = None
    if response.evidence:
        evidence_dump = json.dumps(response.evidence.model_dump())

    assistant_msg = ChatMessage(
        match_id=req.match_id,
        team_id=req.team_id,
        over_number=req.over,
        role="assistant",
        content=response.answer,
        evidence_json=evidence_dump,
    )
    db.add(assistant_msg)
    db.commit()

    return response
