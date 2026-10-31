"""Mock LLM implementation for offline testing and zero-API-key mode.

Strictly follows the core design principle:
Calls the deterministic engine services directly and formats explainable answers
in English or natural Hinglish.
"""

import re
from typing import Any

from sqlalchemy.orm import Session

from app.llm.prompts import (
    OUT_OF_SCOPE_MESSAGE_EN,
    OUT_OF_SCOPE_MESSAGE_HINGLISH,
)
from app.schemas.chat import ChatResponse, EvidencePayload
from app.services.advisor_service import advise_team_lineup
from app.services.dls_estimator import simulate_reduced_overs
from app.services.explain_service import (
    explain_points_change,
    get_match_deliveries_from_db,
    get_team_players_for_db,
)


def is_out_of_scope(message: str) -> bool:
    msg = message.lower().strip()
    cricket_keywords = [
        "point", "captain", "vc", "vice", "over", "wicket", "run", "rain",
        "dls", "target", "score", "change", "player", "match", "team",
        "why", "fix", "advice", "suggest", "drop", "gain", "lose", "lost", "rohit",
        "surya", "bumrah", "jadeja", "dhoni", "hardik", "pathirana", "what if"
    ]
    return not any(kw in msg for kw in cricket_keywords)


def run_mock_chat(
    session: Session,
    match_id: str,
    team_id: str,
    over: int,
    message: str,
    language: str = "en",
) -> ChatResponse:
    is_hinglish = language.lower() in ("hinglish", "hi")
    msg_lower = message.lower()

    # 1. Out of Scope Check
    if is_out_of_scope(message):
        return ChatResponse(
            answer=OUT_OF_SCOPE_MESSAGE_HINGLISH if is_hinglish else OUT_OF_SCOPE_MESSAGE_EN,
            evidence=None,
            over=over,
            language=language,
            is_out_of_scope=True,
        )

    # 2. What-If / Rain / DLS Intent
    if any(k in msg_lower for k in ("rain", "dls", "cut", "reduced", "what if", "15 overs")):
        # Extract target overs if specified (e.g. 15)
        match_digits = re.search(r"\b(\d+)\s*overs?\b", msg_lower)
        reduced_overs = int(match_digits.group(1)) if match_digits else 15
        if reduced_overs <= 0 or reduced_overs > 20:
            reduced_overs = 15

        team_players = get_team_players_for_db(session, team_id)
        deliveries = get_match_deliveries_from_db(session, match_id)

        dls_result = simulate_reduced_overs(
            team_players=team_players,
            deliveries=deliveries,
            current_over=over,
            reduced_overs=reduced_overs,
        )

        evidence_rows: list[dict[str, Any]] = [
            {
                "Player": p.player_name,
                "Role": p.role,
                "Current Pts": p.current_points,
                "Projected Range": f"{p.projected_low} - {p.projected_high} pts",
                "Expected": p.projected_expected,
                "Context": p.notes,
            }
            for p in dls_result.player_projections
        ]

        if is_hinglish:
            answer = (
                f"🌧️ **Agar match baarish ki wajah se {reduced_overs} overs ka ho jata hai:**\n\n"
                f"- **Match ki halat:** Current score {dls_result.runs_scored_so_far}/{dls_result.wickets_lost_so_far} "
                f"hai ({over} overs ke baad). {dls_result.overs_lost} overs cut ho gaye hain.\n"
                f"- **Projected Innings 1 Score:** Range **{dls_result.projected_innings1_total_low} - {dls_result.projected_innings1_total_high} runs** "
                f"(Expected: {dls_result.projected_innings1_total_expected} runs).\n"
                f"- **DLS Revised Target:** Team 2 ko chase ke liye **{dls_result.approximate_revised_target} runs** ka target milega.\n\n"
                f"📊 **Fantasy Impact:** Players ke projected points range me hain (niche 'Show the numbers' table me har player ka range dekhein). "
                f"Death overs kam hone ki wajah se finishing batters ka upside limit ho jayega!"
            )
        else:
            answer = (
                f"🌧️ **What-If Rain Analysis ({reduced_overs} Overs Match):**\n\n"
                f"- **Match Situation:** Current score is {dls_result.runs_scored_so_far}/{dls_result.wickets_lost_so_far} "
                f"after {over} overs. Rain causes a loss of {dls_result.overs_lost} overs.\n"
                f"- **Projected Innings 1 Score:** Range **{dls_result.projected_innings1_total_low} to {dls_result.projected_innings1_total_high} runs** "
                f"(expected: {dls_result.projected_innings1_total_expected}).\n"
                f"- **Approximate DLS Revised Target:** Team 2 would chase **{dls_result.approximate_revised_target} runs** in {reduced_overs} overs.\n\n"
                f"📊 **Fantasy Points Impact:** With fewer remaining overs, point potentials contract. "
                f"Check the exact player ranges in the evidence table below."
            )

        evidence = EvidencePayload(
            tool_called="simulate_reduced_overs",
            title=f"Approximate DLS Target & Points Simulation ({reduced_overs} Overs)",
            summary=dls_result.summary,
            confidence_note=dls_result.confidence_note,
            table_headers=["Player", "Role", "Current Pts", "Projected Range", "Expected", "Context"],
            table_rows=evidence_rows,
            raw_data={
                "reduced_overs": reduced_overs,
                "approximate_revised_target": dls_result.approximate_revised_target,
                "projected_innings1_expected": dls_result.projected_innings1_total_expected,
            },
        )

        return ChatResponse(
            answer=answer,
            evidence=evidence,
            over=over,
            language=language,
        )

    # 3. Captaincy / Tactical Advice Intent
    if any(k in msg_lower for k in ("captain", "vc", "vice-captain", "vice captain", "fix my captain", "should i change")):
        advisor_res = advise_team_lineup(
            session=session,
            match_id=match_id,
            team_id=team_id,
            current_over=over,
        )

        top_picks = advisor_res.player_rankings[:3]
        top_str_en = ", ".join(f"{p['player_name']} (Exp: {p['captaincy_potential']} pts)" for p in top_picks)
        top_str_hi = ", ".join(f"{p['player_name']} ({p['captaincy_potential']} pts)" for p in top_picks)

        if is_hinglish:
            if advisor_res.should_change_captain:
                answer = (
                    f"⚠️ **Captain Alert (Over {over}):**\n\n"
                    f"Aapko apna captain **{advisor_res.current_captain}** se badal kar **{advisor_res.recommended_captain}** ko banana chahiye!\n\n"
                    f"**Kyun?**\n"
                    + "\n".join(f"- {s}" for s in advisor_res.suggestions)
                    + f"\n\n🏆 **Top Captaincy Picks:** {top_str_hi}.\n"
                    f"Har player ka detailed math dekhne ke liye niche 'Show the numbers' par click karein."
                )
            else:
                answer = (
                    f"✅ **Captain Analysis (Over {over}):**\n\n"
                    f"Aapka current captain **{advisor_res.current_captain}** abhi bilkul sahi choice hai!\n\n"
                    + "\n".join(f"- {s}" for s in advisor_res.suggestions)
                    + f"\n\n🔥 **Leading Fantasy Prospects:** {top_str_hi}."
                )
        else:
            if advisor_res.should_change_captain:
                answer = (
                    f"⚠️ **Tactical Captaincy Recommendation (Over {over}):**\n\n"
                    f"We recommend switching your captain from **{advisor_res.current_captain}** to **{advisor_res.recommended_captain}**.\n\n"
                    f"**Key Reasons & Risks:**\n"
                    + "\n".join(f"- {s}" for s in advisor_res.suggestions)
                    + f"\n\n🏆 **Highest Projected Players (if 2.0x Captain):**\n{top_str_en}."
                )
            else:
                answer = (
                    f"✅ **Captaincy Evaluation (Over {over}):**\n\n"
                    f"Hold tight! Your captain **{advisor_res.current_captain}** remains your strongest play at this stage of the match.\n\n"
                    + "\n".join(f"- {s}" for s in advisor_res.suggestions)
                    + f"\n\n🔥 **Top Rest-of-Match Projected Performers:** {top_str_en}."
                )

        evidence = EvidencePayload(
            tool_called="suggest_changes",
            title=f"Captaincy Rankings & Rest-of-Match Projections (Over {over})",
            summary=advisor_res.summary_narrative,
            confidence_note="Projections calculated deterministically from run rates, dismissal status, and bowling quotas.",
            table_headers=["Rank", "Player", "Role", "Current Pts", "Exp Rem Pts", "If Captain (2x)", "Status & Risks"],
            table_rows=advisor_res.evidence_table,
            raw_data={
                "current_captain": advisor_res.current_captain,
                "recommended_captain": advisor_res.recommended_captain,
                "should_change": advisor_res.should_change_captain,
            },
        )

        return ChatResponse(
            answer=answer,
            evidence=evidence,
            over=over,
            language=language,
        )

    # 4. Default: Points Explanation Intent ("Why did my points change?")
    compare_over = max(0, over - 1)
    # Check if user asked to compare specific over (e.g. "last 5 overs")
    if "last 5" in msg_lower or "5 overs" in msg_lower:
        compare_over = max(0, over - 5)

    explain_res = explain_points_change(
        session=session,
        match_id=match_id,
        team_id=team_id,
        current_over=over,
        compare_over=compare_over,
    )

    direction_str = "gained" if explain_res.net_points_change >= 0 else "lost"
    sign = "+" if explain_res.net_points_change > 0 else ""

    top_movers = [p for p in explain_res.player_changes if p.delta_points != 0]
    top_movers.sort(key=lambda x: abs(x.delta_points), reverse=True)

    if is_hinglish:
        top_movers_text = ""
        if top_movers:
            top_movers_text = "\n".join(
                f"- **{p.player_name}**: {'+' if p.delta_points > 0 else ''}{p.delta_points} pts ({', '.join(p.causes)})"
                for p in top_movers[:4]
            )
        else:
            top_movers_text = "- Is over me koi bada event nahi hua (quiet over)."

        answer = (
            f"📈 **Points Breakdown (Over {compare_over} se Over {over}):**\n\n"
            f"Aapki team ne is dauran **{sign}{explain_res.net_points_change} points** {direction_str} kiye "
            f"(Total: {explain_res.previous_total_points} ➡️ **{explain_res.current_total_points}**).\n\n"
            f"**Key Khiladi aur Points ka Karan:**\n"
            f"{top_movers_text}\n\n"
            f"Pura ball-by-ball breakdown dekhne ke liye niche 'Show the numbers' open karein."
        )
    else:
        top_movers_text = ""
        if top_movers:
            top_movers_text = "\n".join(
                f"- **{p.player_name}** ({p.role}): {'+' if p.delta_points > 0 else ''}{p.delta_points} pts — {', '.join(p.causes)}"
                for p in top_movers[:4]
            )
        else:
            top_movers_text = "- No major point movements during this quiet over."

        answer = (
            f"📈 **Points Explanation (Over {compare_over} to Over {over}):**\n\n"
            f"Your team **{direction_str} {abs(explain_res.net_points_change)} points** "
            f"moving from {explain_res.previous_total_points} to **{explain_res.current_total_points} pts**.\n\n"
            f"**Key Player Drivers:**\n"
            f"{top_movers_text}\n\n"
            f"Every single ball and point event is listed in the evidence table below."
        )

    evidence = EvidencePayload(
        tool_called="explain_points_change",
        title=f"Points Movement Audit (Over {compare_over} to Over {over})",
        summary=explain_res.summary_narrative,
        confidence_note="100% deterministic ball-by-ball attribution from official match timeline.",
        table_headers=["Player", "Role", f"Over {compare_over} Pts", f"Over {over} Pts", "Delta", "Key Causes"],
        table_rows=explain_res.evidence_table,
        raw_data={
            "previous_total": explain_res.previous_total_points,
            "current_total": explain_res.current_total_points,
            "net_delta": explain_res.net_points_change,
        },
    )

    return ChatResponse(
        answer=answer,
        evidence=evidence,
        over=over,
        language=language,
    )
