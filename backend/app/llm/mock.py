"""Mock LLM implementation for offline testing and zero-API-key mode.

Strictly follows the core design principle:
Answers ANY natural question about the match, fantasy team, specific players,
captaincy, points breakdown, or rain scenarios using deterministic engine data.
Supports natural English and engaging Hinglish.
"""

import re

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
from app.services.scoring_engine import calculate_team_points, load_scoring_rules


def is_out_of_scope(message: str) -> bool:
    msg = message.lower().strip()
    # If it's a greeting or asking for help, it's NOT out of scope
    greetings = ["hi", "hello", "hey", "help", "who are you", "what can you do", "namaste", "kaise ho"]
    if any(g == msg or msg.startswith(f"{g} ") for g in greetings):
        return False

    cricket_keywords = [
        "point", "captain", "vc", "vice", "over", "wicket", "run", "rain",
        "dls", "target", "score", "change", "player", "match", "team",
        "why", "fix", "advice", "suggest", "drop", "gain", "lose", "lost", "rohit",
        "surya", "bumrah", "jadeja", "dhoni", "hardik", "pathirana", "what if",
        "best", "worst", "status", "summary", "doing", "standing", "rank", "ball",
        "bat", "bowl", "perform", "stats", "ishan", "tilak", "david", "shepherd",
        "coetzee", "chawla", "thushara", "ruturaj", "rachin", "rahane", "dube",
        "mitchell", "shardul", "deshpande", "mustafizur", "top", "leader"
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
    msg_lower = message.lower().strip()

    # 1. Check Out of Scope
    if is_out_of_scope(message):
        return ChatResponse(
            answer=OUT_OF_SCOPE_MESSAGE_HINGLISH if is_hinglish else OUT_OF_SCOPE_MESSAGE_EN,
            evidence=None,
            over=over,
            language=language,
            is_out_of_scope=True,
        )

    team_players = get_team_players_for_db(session, team_id)
    deliveries = get_match_deliveries_from_db(session, match_id)
    rules = load_scoring_rules()

    # Pre-calculate team score at current over
    team_score = calculate_team_points(
        team_id=team_id,
        team_name=team_id,
        team_players=team_players,
        deliveries=deliveries,
        over_number=over,
        rules=rules,
    )
    players_sorted_by_pts = sorted(team_score.players, key=lambda p: p.total_points, reverse=True)
    captain_p = next((p for p in team_score.players if p.is_captain), None)
    vc_p = next((p for p in team_score.players if p.is_vice_captain), None)

    # 2. Greetings / Introduction Intent
    if any(msg_lower.startswith(w) or msg_lower == w for w in ["hi", "hello", "hey", "namaste", "what can you do"]):
        cap_name = captain_p.player_name if captain_p else "None"
        if is_hinglish:
            ans = (
                f"Namaste! 🙏 Main hoon aapka **Match Copilot**.\n\n"
                f"Abhi **Over {over}** chal raha hai. Aapki team ke paas **{team_score.total_points} fantasy points** hain, "
                f"aur aapke Captain **{cap_name}** hain.\n\n"
                f"Aap mujhse kuch bhi pooch sakte hain, jaise:\n"
                f"- *'Meri team kaisa perform kar rahi hai?'*\n"
                f"- *'Kya mujhe captain badalna chahiye?'*\n"
                f"- *'Rohit Sharma ka score aur points kya hain?'*\n"
                f"- *'Agar baarish se 15 overs ho gaye toh kya hoga?'*"
            )
        else:
            ans = (
                f"Hey there! 🏏 I'm your **Match Copilot**.\n\n"
                f"We are at **Over {over}**. Your fantasy team currently has **{team_score.total_points} points**, "
                f"with **{cap_name}** as your captain.\n\n"
                f"You can ask me anything about your team and the match:\n"
                f"- *'How is my team doing overall?'*\n"
                f"- *'Should I change my captain?'*\n"
                f"- *'How is Rohit Sharma or Bumrah performing?'*\n"
                f"- *'What if rain reduces the match to 15 overs?'*"
            )
        return ChatResponse(answer=ans, evidence=None, over=over, language=language)

    # 3. Specific Player Inquiry (e.g., "How is Rohit doing?", "Bumrah points", "Tell me about Surya")
    player_keywords = {
        "rohit": "Rohit Sharma",
        "surya": "Suryakumar Yadav",
        "suryakumar": "Suryakumar Yadav",
        "bumrah": "Jasprit Bumrah",
        "ishan": "Ishan Kishan",
        "hardik": "Hardik Pandya",
        "tilak": "Tilak Varma",
        "david": "Tim David",
        "shepherd": "Romario Shepherd",
        "coetzee": "Gerald Coetzee",
        "chawla": "Piyush Chawla",
        "thushara": "Nuwan Thushara",
        "ruturaj": "Ruturaj Gaikwad",
        "rachin": "Rachin Ravindra",
        "rahane": "Ajinkya Rahane",
        "dube": "Shivam Dube",
        "mitchell": "Daryl Mitchell",
        "jadeja": "Ravindra Jadeja",
        "dhoni": "MS Dhoni",
        "shardul": "Shardul Thakur",
        "deshpande": "Tushar Deshpande",
        "mustafizur": "Mustafizur Rahman",
        "pathirana": "Matheesha Pathirana",
    }
    matched_player_name = next((full_name for kw, full_name in player_keywords.items() if kw in msg_lower), None)

    if matched_player_name:
        target_p = next((p for p in team_score.players if p.player_name.lower() == matched_player_name.lower()), None)
        if target_p:
            events_str = ", ".join(e.description for e in target_p.events) if target_p.events else "Starting XI only"
            role_badge = f"{target_p.role}" + (" (Captain 2x)" if target_p.is_captain else " (VC 1.5x)" if target_p.is_vice_captain else "")

            if is_hinglish:
                status_note = f"Out ({target_p.dismissal_kind})" if target_p.is_dismissed else "Abhi active hai"
                ans = (
                    f"👤 **{target_p.player_name}** ({role_badge}) ka update (Over {over} tak):\n\n"
                    f"- **Total Fantasy Points:** **{target_p.total_points} pts** (Base: {target_p.base_points} × {target_p.multiplier}x)\n"
                    f"- **Batting:** {target_p.runs} runs ({target_p.balls_faced} balls, {target_p.fours} चौके, {target_p.sixes} छक्के)\n"
                    f"- **Bowling:** {target_p.overs_bowled} overs, {target_p.wickets} wickets, {target_p.runs_conceded} runs conceded\n"
                    f"- **Status:** {status_note}\n\n"
                    f"**Events:** {events_str}"
                )
            else:
                status_note = f"Dismissed ({target_p.dismissal_kind})" if target_p.is_dismissed else "Active in match"
                ans = (
                    f"👤 **{target_p.player_name}** ({role_badge}) Report (up to Over {over}):\n\n"
                    f"- **Total Fantasy Points:** **{target_p.total_points} pts** (Base: {target_p.base_points} × {target_p.multiplier}x)\n"
                    f"- **Batting:** {target_p.runs} runs off {target_p.balls_faced} balls ({target_p.fours} fours, {target_p.sixes} sixes)\n"
                    f"- **Bowling:** {target_p.overs_bowled} overs, {target_p.wickets} wickets, {target_p.runs_conceded} runs\n"
                    f"- **Status:** {status_note}\n\n"
                    f"**Key Scoring Events:** {events_str}."
                )

            evidence_rows = [
                {
                    "Category": e.category.capitalize(),
                    "Action": e.description,
                    "Points": e.points,
                }
                for e in target_p.events
            ]
            evidence = EvidencePayload(
                tool_called="player_breakdown",
                title=f"{target_p.player_name} Detailed Event Ledger (Over {over})",
                summary=f"{target_p.player_name} has earned {target_p.total_points} points so far.",
                confidence_note="Audited from ball-by-ball match events.",
                table_headers=["Category", "Action", "Points"],
                table_rows=evidence_rows,
                raw_data={"player": target_p.player_name, "points": target_p.total_points},
            )
            return ChatResponse(answer=ans, evidence=evidence, over=over, language=language)

    # 4. Team Status / "How is my team doing?" / Summary Intent
    if any(k in msg_lower for k in ("how is my team", "team status", "team summary", "standing", "how am i doing", "overall", "my score")):
        top_player = players_sorted_by_pts[0] if players_sorted_by_pts else None
        cap_pts = captain_p.total_points if captain_p else 0

        if is_hinglish:
            ans = (
                f"📊 **Team Performance Summary (Over {over}):**\n\n"
                f"- **Total Points:** **{team_score.total_points} pts**\n"
                f"- **Top Performer:** **{top_player.player_name if top_player else 'N/A'}** ({top_player.total_points if top_player else 0} pts)\n"
                f"- **Captain ({captain_p.player_name if captain_p else 'None'}):** {cap_pts} pts (2.0x multiplier)\n"
                f"- **Vice-Captain ({vc_p.player_name if vc_p else 'None'}):** {vc_p.total_points if vc_p else 0} pts (1.5x multiplier)\n\n"
                f"{'Captain out ho chuke hain, isliye captain switch consider karein!' if captain_p and captain_p.is_dismissed else 'Team achi position me hai!'}"
            )
        else:
            ans = (
                f"📊 **Team Performance Summary (Over {over}):**\n\n"
                f"- **Total Points:** **{team_score.total_points} pts**\n"
                f"- **Top Scorer:** **{top_player.player_name if top_player else 'N/A'}** with {top_player.total_points if top_player else 0} points\n"
                f"- **Captain ({captain_p.player_name if captain_p else 'None'}):** {cap_pts} points (2.0x boost)\n"
                f"- **Vice-Captain ({vc_p.player_name if vc_p else 'None'}):** {vc_p.total_points if vc_p else 0} points (1.5x boost)\n\n"
                f"{'⚠️ Alert: Your captain is dismissed. Switch to an active player for remaining overs!' if captain_p and captain_p.is_dismissed else 'Your team is active and on track.'}"
            )

        evidence_rows = [
            {
                "Player": p.player_name,
                "Role": p.role + (" (C)" if p.is_captain else " (VC)" if p.is_vice_captain else ""),
                "Points": p.total_points,
                "Runs/Wkts": f"{p.runs}r / {p.wickets}w",
                "Status": "Out" if p.is_dismissed else "Active",
            }
            for p in players_sorted_by_pts
        ]
        evidence = EvidencePayload(
            tool_called="team_summary",
            title=f"Squad Scorecard (Over {over})",
            summary=f"Team has {team_score.total_points} points at Over {over}.",
            confidence_note="Calculated via deterministic scoring engine.",
            table_headers=["Player", "Role", "Points", "Runs/Wkts", "Status"],
            table_rows=evidence_rows,
        )
        return ChatResponse(answer=ans, evidence=evidence, over=over, language=language)

    # 5. Best / Top Performer Intent
    if any(k in msg_lower for k in ("best player", "top scorer", "most points", "highest")):
        top_3 = players_sorted_by_pts[:3]
        if is_hinglish:
            ans = (
                f"🌟 **Top 3 Performers (Over {over} tak):**\n\n"
                + "\n".join(
                    f"{idx+1}. **{p.player_name}** — **{p.total_points} pts** ({p.runs} runs, {p.wickets} wickets)"
                    for idx, p in enumerate(top_3)
                )
                + "\n\nNiche table me har player ke exact points check karein!"
            )
        else:
            ans = (
                f"🌟 **Top 3 Performers (Up to Over {over}):**\n\n"
                + "\n".join(
                    f"{idx+1}. **{p.player_name}** ({p.role}) — **{p.total_points} pts** ({p.runs} runs, {p.wickets} wickets)"
                    for idx, p in enumerate(top_3)
                )
                + "\n\nDetailed breakdown is available in the table below."
            )

        evidence_rows = [
            {"Rank": f"#{i+1}", "Player": p.player_name, "Role": p.role, "Points": p.total_points}
            for i, p in enumerate(top_3)
        ]
        evidence = EvidencePayload(
            tool_called="top_performers",
            title="Leading Fantasy Point Scorers",
            summary=f"{top_3[0].player_name} leads your team with {top_3[0].total_points} points.",
            table_headers=["Rank", "Player", "Role", "Points"],
            table_rows=evidence_rows,
        )
        return ChatResponse(answer=ans, evidence=evidence, over=over, language=language)

    # 6. What-If / Rain / DLS Intent
    if any(k in msg_lower for k in ("rain", "dls", "cut", "reduced", "what if", "15 overs", "weather")):
        match_digits = re.search(r"\b(\d+)\s*overs?\b", msg_lower)
        reduced_overs = int(match_digits.group(1)) if match_digits else 15
        if reduced_overs <= 0 or reduced_overs > 20:
            reduced_overs = 15

        dls_result = simulate_reduced_overs(
            team_players=team_players,
            deliveries=deliveries,
            current_over=over,
            reduced_overs=reduced_overs,
        )

        evidence_rows = [
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
                f"- **Match situation:** Current score {dls_result.runs_scored_so_far}/{dls_result.wickets_lost_so_far} "
                f"hai ({over} overs ke baad). {dls_result.overs_lost} overs cut ho gaye hain.\n"
                f"- **Projected Innings 1 Score:** Range **{dls_result.projected_innings1_total_low} - {dls_result.projected_innings1_total_high} runs** "
                f"(Expected: {dls_result.projected_innings1_total_expected} runs).\n"
                f"- **DLS Revised Target:** Team 2 ko chase ke liye **{dls_result.approximate_revised_target} runs** ka target milega.\n\n"
                f"📊 **Fantasy Impact:** Death overs kam hone ki wajah se finishing batters ka points upside limit ho jayega!"
            )
        else:
            answer = (
                f"🌧️ **What-If Rain Analysis ({reduced_overs} Overs Match):**\n\n"
                f"- **Match Situation:** Current score is {dls_result.runs_scored_so_far}/{dls_result.wickets_lost_so_far} "
                f"after {over} overs ({dls_result.overs_lost} overs lost).\n"
                f"- **Projected Innings 1 Score:** Range **{dls_result.projected_innings1_total_low} to {dls_result.projected_innings1_total_high} runs** "
                f"(expected: {dls_result.projected_innings1_total_expected}).\n"
                f"- **Approximate DLS Revised Target:** Team 2 would chase **{dls_result.approximate_revised_target} runs** in {reduced_overs} overs.\n\n"
                f"📊 **Fantasy Impact:** With fewer remaining overs, point potentials contract. Check the exact player ranges in the table below."
            )

        evidence = EvidencePayload(
            tool_called="simulate_reduced_overs",
            title=f"Approximate DLS Target & Simulation ({reduced_overs} Overs)",
            summary=dls_result.summary,
            confidence_note=dls_result.confidence_note,
            table_headers=["Player", "Role", "Current Pts", "Projected Range", "Expected", "Context"],
            table_rows=evidence_rows,
            raw_data={"reduced_overs": reduced_overs, "approximate_revised_target": dls_result.approximate_revised_target},
        )
        return ChatResponse(answer=answer, evidence=evidence, over=over, language=language)

    # 7. Captaincy / Tactical Advice Intent
    if any(k in msg_lower for k in ("captain", "vc", "vice-captain", "vice captain", "fix my captain", "should i change", "change captain")):
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
                    f"⚠️ **Captain Recommendation (Over {over}):**\n\n"
                    f"Aapko apna captain **{advisor_res.current_captain}** se badal kar **{advisor_res.recommended_captain}** ko banana chahiye!\n\n"
                    f"**Kyun?**\n"
                    + "\n".join(f"- {s}" for s in advisor_res.suggestions)
                    + f"\n\n🏆 **Top Captaincy Picks:** {top_str_hi}."
                )
            else:
                answer = (
                    f"✅ **Captain Evaluation (Over {over}):**\n\n"
                    f"Aapka current captain **{advisor_res.current_captain}** abhi bilkul sahi choice hai!\n\n"
                    + "\n".join(f"- {s}" for s in advisor_res.suggestions)
                    + f"\n\n🔥 **Top Prospects:** {top_str_hi}."
                )
        else:
            if advisor_res.should_change_captain:
                answer = (
                    f"⚠️ **Captain Recommendation (Over {over}):**\n\n"
                    f"We recommend switching your captain from **{advisor_res.current_captain}** to **{advisor_res.recommended_captain}**.\n\n"
                    f"**Key Reasons & Risks:**\n"
                    + "\n".join(f"- {s}" for s in advisor_res.suggestions)
                    + f"\n\n🏆 **Highest Projected (if Captain 2.0x):**\n{top_str_en}."
                )
            else:
                answer = (
                    f"✅ **Captain Evaluation (Over {over}):**\n\n"
                    f"Your captain **{advisor_res.current_captain}** remains optimal at this stage.\n\n"
                    + "\n".join(f"- {s}" for s in advisor_res.suggestions)
                    + f"\n\n🔥 **Top Performers:** {top_str_en}."
                )

        evidence = EvidencePayload(
            tool_called="suggest_changes",
            title=f"Captaincy Rankings & Projections (Over {over})",
            summary=advisor_res.summary_narrative,
            confidence_note="Projections calculated from run rates and remaining quotas.",
            table_headers=["Rank", "Player", "Role", "Current Pts", "Exp Rem Pts", "If Captain (2x)", "Status & Risks"],
            table_rows=advisor_res.evidence_table,
            raw_data={"current_captain": advisor_res.current_captain, "recommended_captain": advisor_res.recommended_captain},
        )
        return ChatResponse(answer=answer, evidence=evidence, over=over, language=language)

    # 8. Match Situation / Scorecard Intent
    if any(k in msg_lower for k in ("match", "score", "wicket", "runs", "what happened")):
        active_d = [d for d in deliveries if d.get("over_number", 0) <= over] if over > 0 else []
        runs_so_far = sum(d.get("runs_batter", 0) + d.get("runs_extras", 0) for d in active_d)
        wkts_so_far = sum(1 for d in active_d if d.get("is_wicket"))
        crr = round(runs_so_far / over, 2) if over > 0 else 0.0

        if is_hinglish:
            ans = (
                f"🏏 **Match Scorecard (Over {over}):**\n\n"
                f"- **Score:** {runs_so_far}/{wkts_so_far} ({over}.0 overs)\n"
                f"- **Run Rate:** {crr} RPO\n"
                f"- **Aapki Fantasy Team:** {team_score.total_points} points\n\n"
                f"Aap slider ko kisi bhi over par le ja kar match moment replay dekh sakte hain!"
            )
        else:
            ans = (
                f"🏏 **Match Situation (Over {over}):**\n\n"
                f"- **Score:** {runs_so_far}/{wkts_so_far} in {over}.0 overs\n"
                f"- **Current Run Rate:** {crr} RPO\n"
                f"- **Your Fantasy Points:** {team_score.total_points} pts\n\n"
                f"Feel free to scrub the slider to analyze any specific over."
            )
        return ChatResponse(answer=ans, evidence=None, over=over, language=language)

    # 9. Default: Points Explanation Intent ("Why did my points change?")
    compare_over = max(0, over - 1)
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
        top_movers_text = (
            "\n".join(
                f"- **{p.player_name}**: {'+' if p.delta_points > 0 else ''}{p.delta_points} pts ({', '.join(p.causes)})"
                for p in top_movers[:4]
            )
            if top_movers
            else "- Is over me koi bada scoring event nahi hua."
        )

        answer = (
            f"📈 **Points Breakdown (Over {compare_over} se Over {over}):**\n\n"
            f"Aapki team ne is dauran **{sign}{explain_res.net_points_change} points** {direction_str} kiye "
            f"(Total: {explain_res.previous_total_points} ➡️ **{explain_res.current_total_points}**).\n\n"
            f"**Key Players:**\n"
            f"{top_movers_text}\n\n"
            f"Exact numbers dekhne ke liye niche 'Show the numbers' par click karein."
        )
    else:
        top_movers_text = (
            "\n".join(
                f"- **{p.player_name}** ({p.role}): {'+' if p.delta_points > 0 else ''}{p.delta_points} pts — {', '.join(p.causes)}"
                for p in top_movers[:4]
            )
            if top_movers
            else "- Quiet over; no significant point movements."
        )

        answer = (
            f"📈 **Points Explanation (Over {compare_over} to Over {over}):**\n\n"
            f"Your team **{direction_str} {abs(explain_res.net_points_change)} points** "
            f"({explain_res.previous_total_points} ➡️ **{explain_res.current_total_points} pts**).\n\n"
            f"**Key Player Drivers:**\n"
            f"{top_movers_text}\n\n"
            f"Check the audited evidence table below for ball-by-ball details."
        )

    evidence = EvidencePayload(
        tool_called="explain_points_change",
        title=f"Points Movement Audit (Over {compare_over} to Over {over})",
        summary=explain_res.summary_narrative,
        confidence_note="100% deterministic attribution from match timeline.",
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
