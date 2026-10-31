"""LLM Client for Match Copilot.

Coordinates with Anthropic Claude API for tool calling,
and provides seamless offline fallback via MockLlm.
Never lets the LLM compute points or mathematical rates.
"""

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import logger
from app.llm.mock import run_mock_chat
from app.llm.prompts import SYSTEM_PROMPT_EN, SYSTEM_PROMPT_HINGLISH
from app.llm.tools import ANTHROPIC_TOOLS
from app.schemas.chat import ChatResponse, EvidencePayload
from app.services.advisor_service import advise_team_lineup
from app.services.dls_estimator import simulate_reduced_overs
from app.services.explain_service import (
    explain_points_change,
    get_match_deliveries_from_db,
    get_team_players_for_db,
)

settings = get_settings()


class LlmClient:
    def __init__(self) -> None:
        self.use_mock = settings.use_mock_llm or not bool(settings.anthropic_api_key.strip())
        self.model = settings.anthropic_model

    async def chat(
        self,
        session: Session,
        match_id: str,
        team_id: str,
        over: int,
        message: str,
        language: str = "en",
    ) -> ChatResponse:
        """Processes a chat query via Anthropic Tool Use or Mock LLM."""
        if self.use_mock:
            logger.info("Running in Mock LLM mode (offline ready).")
            return run_mock_chat(
                session=session,
                match_id=match_id,
                team_id=team_id,
                over=over,
                message=message,
                language=language,
            )

        # Attempt Anthropic Claude API call with tool execution
        try:
            return await self._call_anthropic_with_tools(
                session=session,
                match_id=match_id,
                team_id=team_id,
                over=over,
                message=message,
                language=language,
            )
        except Exception as exc:
            logger.warning(
                f"Anthropic API call failed ({exc}); falling back gracefully to deterministic Mock LLM.",
                exc_info=True,
            )
            return run_mock_chat(
                session=session,
                match_id=match_id,
                team_id=team_id,
                over=over,
                message=message,
                language=language,
            )

    async def _call_anthropic_with_tools(
        self,
        session: Session,
        match_id: str,
        team_id: str,
        over: int,
        message: str,
        language: str,
    ) -> ChatResponse:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        is_hinglish = language.lower() in ("hinglish", "hi")
        system_prompt = SYSTEM_PROMPT_HINGLISH if is_hinglish else SYSTEM_PROMPT_EN

        user_content = (
            f"Context: Match ID: {match_id}, Fantasy Team ID: {team_id}, Current Over: {over}.\n"
            f"User Question: {message}"
        )

        messages: list[dict[str, Any]] = [
            {"role": "user", "content": user_content}
        ]

        logger.info(f"Calling Anthropic API ({self.model}) with tool calling enabled...")
        response = await client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=ANTHROPIC_TOOLS,
        )

        # Check for tool use
        tool_call = next((block for block in response.content if block.type == "tool_use"), None)

        if not tool_call:
            # Model responded directly without calling a tool (e.g. out of scope or general text)
            direct_text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            return ChatResponse(
                answer=direct_text or "I can only help with this live match and your fantasy team.",
                evidence=None,
                over=over,
                language=language,
                is_out_of_scope="only help with this" in direct_text.lower(),
            )

        # Execute deterministic tool
        tool_name = tool_call.name
        tool_input = tool_call.input or {}
        logger.info(f"LLM invoked tool: {tool_name} with input {tool_input}")

        tool_result_data: dict[str, Any] = {}
        evidence_payload: EvidencePayload

        if tool_name == "explain_points_change":
            cmp_over = tool_input.get("compare_over", max(0, over - 1))
            res = explain_points_change(
                session=session,
                match_id=match_id,
                team_id=team_id,
                current_over=over,
                compare_over=cmp_over,
            )
            tool_result_data = {
                "previous_over": res.compare_over,
                "current_over": res.current_over,
                "previous_total": res.previous_total_points,
                "current_total": res.current_total_points,
                "net_change": res.net_points_change,
                "player_changes": [
                    {
                        "player": p.player_name,
                        "role": p.role,
                        "delta": p.delta_points,
                        "current_pts": p.current_points,
                        "causes": p.causes,
                    }
                    for p in res.player_changes
                ],
                "summary": res.summary_narrative,
            }
            evidence_payload = EvidencePayload(
                tool_called=tool_name,
                title=f"Points Movement Audit (Over {res.compare_over} to Over {res.current_over})",
                summary=res.summary_narrative,
                confidence_note="100% deterministic attribution from match timeline.",
                table_headers=["Player", "Role", f"Over {res.compare_over} Pts", f"Over {res.current_over} Pts", "Delta", "Key Causes"],
                table_rows=res.evidence_table,
                raw_data=tool_result_data,
            )

        elif tool_name == "suggest_changes":
            adv_res = advise_team_lineup(
                session=session,
                match_id=match_id,
                team_id=team_id,
                current_over=over,
            )
            tool_result_data = {
                "current_captain": adv_res.current_captain,
                "recommended_captain": adv_res.recommended_captain,
                "should_change": adv_res.should_change_captain,
                "suggestions": adv_res.suggestions,
                "rankings": adv_res.player_rankings,
            }
            evidence_payload = EvidencePayload(
                tool_called=tool_name,
                title=f"Captaincy Rankings & Rest-of-Match Projections (Over {over})",
                summary=adv_res.summary_narrative,
                confidence_note="Deterministic projections based on match run rates and quotas.",
                table_headers=["Rank", "Player", "Role", "Current Pts", "Exp Rem Pts", "If Captain (2x)", "Status & Risks"],
                table_rows=adv_res.evidence_table,
                raw_data=tool_result_data,
            )

        elif tool_name == "simulate_reduced_overs":
            red_overs = int(tool_input.get("reduced_overs", 15))
            team_players = get_team_players_for_db(session, team_id)
            deliveries = get_match_deliveries_from_db(session, match_id)
            dls_res = simulate_reduced_overs(
                team_players=team_players,
                deliveries=deliveries,
                current_over=over,
                reduced_overs=red_overs,
            )
            tool_result_data = {
                "reduced_overs": red_overs,
                "overs_lost": dls_res.overs_lost,
                "projected_innings1_expected": dls_res.projected_innings1_total_expected,
                "projected_innings1_range": f"{dls_res.projected_innings1_total_low}-{dls_res.projected_innings1_total_high}",
                "approximate_dls_target": dls_res.approximate_revised_target,
                "summary": dls_res.summary,
            }
            evidence_rows = [
                {
                    "Player": p.player_name,
                    "Role": p.role,
                    "Current Pts": p.current_points,
                    "Projected Range": f"{p.projected_low} - {p.projected_high} pts",
                    "Expected": p.projected_expected,
                    "Context": p.notes,
                }
                for p in dls_res.player_projections
            ]
            evidence_payload = EvidencePayload(
                tool_called=tool_name,
                title=f"Approximate DLS Target & Simulation ({red_overs} Overs)",
                summary=dls_res.summary,
                confidence_note=dls_res.confidence_note,
                table_headers=["Player", "Role", "Current Pts", "Projected Range", "Expected", "Context"],
                table_rows=evidence_rows,
                raw_data=tool_result_data,
            )

        else:
            raise ValueError(f"Unknown tool called: {tool_name}")

        # Send tool execution result back to Claude for final conversational answer
        tool_result_message = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": json.dumps(tool_result_data),
                }
            ],
        }

        # Append assistant tool use message & tool result message
        messages.append({"role": "assistant", "content": response.content})
        messages.append(tool_result_message)

        final_response = await client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )

        final_answer = "".join(
            block.text for block in final_response.content if hasattr(block, "text")
        )

        return ChatResponse(
            answer=final_answer,
            evidence=evidence_payload,
            over=over,
            language=language,
        )


llm_client = LlmClient()
