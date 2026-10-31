"""Mock LLM implementation for offline testing and zero-API-key mode.

Strictly follows the product context and engineering standards:
1. Answers in 2 to 4 short sentences.
2. Leads with the direct answer in the first sentence.
3. Gives the biggest 1-2 causes naming players and points.
4. Gives one clear suggested next step.
5. Tone: knowledgeable cricket buddy on the couch watching on TV.
6. Zero mention of money, prizes, betting, or cash stakes.
7. Estimates strictly formatted as ranges (low / likely / high) with a confidence note.
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

    # 1. Out of Scope Check
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
    cap_name = captain_p.player_name if captain_p else "None"
    vc_name = vc_p.player_name if vc_p else "None"

    # 2. Greetings
    if any(msg_lower.startswith(w) or msg_lower == w for w in ["hi", "hello", "hey", "namaste", "kaise ho", "what can you do"]):
        if is_hinglish:
            ans = (
                f"Hey dost! Over {over} tak aapki team ke {team_score.total_points} points hain ({cap_name} C, {vc_name} VC). "
                f"Aap mujhse pooch sakte hain ki points kyun badle, captain fix karna hai ya nahi, ya baarish ka kya asar hoga."
            )
        else:
            ans = (
                f"Hey! Your team is currently sitting on {team_score.total_points} points at Over {over} ({cap_name} C, {vc_name} VC). "
                f"Ask me why your points moved, whether your captain choice holds up, or what happens if rain cuts the match."
            )
        return ChatResponse(answer=ans, evidence=None, over=over, language=language)

    # 3. What-If Rain / Reduced Overs
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
                "Likely": p.projected_expected,
                "Context": p.notes,
            }
            for p in dls_result.player_projections
        ]

        if is_hinglish:
            ans = (
                f"Agar baarish ki wajah se match {reduced_overs} overs ka ho jata hai, toh Team 2 ka approximate revised target {dls_result.approximate_revised_target} runs hoga. "
                f"Aapki team ka projected score {dls_result.projected_innings1_total_low} se {dls_result.projected_innings1_total_high} runs (likely {dls_result.projected_innings1_total_expected}) ke range me rahega kyunki death overs kam ho gaye hain. "
                f"Apne death bowlers par dhyan dein kyunki kam overs me unka points impact sabse zyada hoga."
            )
        else:
            ans = (
                f"If rain reduces this match to {reduced_overs} overs, Team 2's approximate revised target becomes {dls_result.approximate_revised_target} runs. "
                f"Your team's projected innings total adjusts to a range of {dls_result.projected_innings1_total_low}–{dls_result.projected_innings1_total_high} runs (likely {dls_result.projected_innings1_total_expected}) due to lost batting overs. "
                f"Prioritize death bowlers who will bowl a larger share of the remaining contest."
            )

        evidence = EvidencePayload(
            tool_called="simulate_reduced_overs",
            title=f"Approximate DLS Target & Points Simulation ({reduced_overs} Overs)",
            summary=dls_result.summary,
            confidence_note="Estimates shown as a range. Based on standard T20 resource percentages.",
            table_headers=["Player", "Role", "Current Pts", "Projected Range", "Likely", "Context"],
            table_rows=evidence_rows,
            raw_data={"reduced_overs": reduced_overs, "approximate_revised_target": dls_result.approximate_revised_target},
        )
        return ChatResponse(answer=ans, evidence=evidence, over=over, language=language)

    # 4. Captaincy Advice ("Fix my captain", "Should I change my captain")
    if any(k in msg_lower for k in ("captain", "vc", "vice-captain", "vice captain", "fix my captain", "should i change", "change captain")):
        advisor_res = advise_team_lineup(
            session=session,
            match_id=match_id,
            team_id=team_id,
            current_over=over,
        )

        rec_pick = advisor_res.player_rankings[0] if advisor_res.player_rankings else None
        rec_name = advisor_res.recommended_captain
        curr_name = advisor_res.current_captain

        if advisor_res.should_change_captain:
            if is_hinglish:
                ans = (
                    f"Haan, aapko apna captain {curr_name} se badal kar {rec_name} ko banana chahiye. "
                    f"{curr_name} already out ho chuke hain aur aage batting points nahi de sakte, jabki {rec_name} se rest-of-match me {rec_pick['projected_remaining']} points expected hain. "
                    f"Apne league me lead banaye rakhne ke liye agle over se pehle captain switch kar lijiye."
                )
            else:
                ans = (
                    f"Yes, you should switch your captain from {curr_name} to {rec_name}. "
                    f"{curr_name} is already dismissed and has zero remaining batting upside, whereas {rec_name} has a projected rest-of-match potential of {rec_pick['projected_remaining']} points. "
                    f"Make the switch to maximize your points for the remaining overs (noted as an estimate)."
                )
        else:
            if is_hinglish:
                ans = (
                    f"Apna captain {curr_name} hi rehne dein—woh abhi bhi aapke sabse strong choice hain. "
                    f"Unke overs bache hue hain aur rest-of-match potential {rec_pick['projected_remaining']} points ka hai. "
                    f"Abhi koi badlav karne ki zaroorat nahi hai; unko match finish karne dein."
                )
            else:
                ans = (
                    f"Stick with {curr_name} as your captain—they remain your best projected performer right now. "
                    f"They have active overs remaining with an expected rest-of-match potential of {rec_pick['projected_remaining']} points. "
                    f"Hold steady and let them finish their spell."
                )

        evidence = EvidencePayload(
            tool_called="suggest_changes",
            title=f"Captaincy Rankings & Rest-of-Match Projections (Over {over})",
            summary=advisor_res.summary_narrative,
            confidence_note="Estimates provided as ranges based on remaining overs, status, and bowling quotas.",
            table_headers=["Rank", "Player", "Role", "Current Pts", "Exp Rem Pts", "If Captain (2x)", "Status & Risks"],
            table_rows=advisor_res.evidence_table,
            raw_data={"current_captain": curr_name, "recommended_captain": rec_name, "should_change": advisor_res.should_change_captain},
        )
        return ChatResponse(answer=ans, evidence=evidence, over=over, language=language)

    # 5. Specific Player Query
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
            events_str = ", ".join(e.description for e in target_p.events) if target_p.events else "Starting XI"
            status_text = f"dismissed ({target_p.dismissal_kind})" if target_p.is_dismissed else "active"
            status_text_hi = f"out ({target_p.dismissal_kind})" if target_p.is_dismissed else "active"

            if is_hinglish:
                ans = (
                    f"{target_p.player_name} ke is waqt {target_p.total_points} fantasy points hain ({target_p.runs} runs, {target_p.wickets} wickets). "
                    f"Unhone {events_str} ke zariye points kamaye hain aur abhi {status_text_hi} hain. "
                    f"{'Aage koi batting upside nahi bacha hai.' if target_p.is_dismissed else 'Aage ke overs me unse aur points milne ki achi umeed hai.'}"
                )
            else:
                ans = (
                    f"{target_p.player_name} currently has {target_p.total_points} fantasy points from {target_p.runs} runs and {target_p.wickets} wickets. "
                    f"Their tally comes from {events_str}, and they are currently {status_text}. "
                    f"{'With their dismissal, their batting scoring has concluded.' if target_p.is_dismissed else 'They remain a key contributor for the remaining overs.'}"
                )

            evidence_rows = [
                {"Category": e.category.capitalize(), "Action": e.description, "Points": e.points}
                for e in target_p.events
            ]
            evidence = EvidencePayload(
                tool_called="player_breakdown",
                title=f"{target_p.player_name} Event Ledger (Over {over})",
                summary=f"{target_p.player_name} has earned {target_p.total_points} points so far.",
                confidence_note="Audited from deterministic match timeline.",
                table_headers=["Category", "Action", "Points"],
                table_rows=evidence_rows,
            )
            return ChatResponse(answer=ans, evidence=evidence, over=over, language=language)

    # 6. Team Status & Top Scorer
    if any(k in msg_lower for k in ("how is my team", "team status", "team summary", "standing", "how am i doing", "overall", "my score", "best player", "top scorer")):
        top_p = players_sorted_by_pts[0] if players_sorted_by_pts else None
        top_name = top_p.player_name if top_p else "N/A"
        top_pts = top_p.total_points if top_p else 0

        if is_hinglish:
            ans = (
                f"Aapki team abhi Over {over} tak {team_score.total_points} points par hai, aur {top_name} ({top_pts} pts) aapke best performer hain. "
                f"Aapke captain {cap_name} ne {captain_p.total_points if captain_p else 0} points contribute kiye hain. "
                f"{'Captain out ho chuke hain, isliye captain switch check karein!' if captain_p and captain_p.is_dismissed else 'Team achi position me chal rahi hai.'}"
            )
        else:
            ans = (
                f"Your team has {team_score.total_points} total points at Over {over}, led by {top_name} with {top_pts} points. "
                f"Your captain {cap_name} has delivered {captain_p.total_points if captain_p else 0} points under the 2x multiplier. "
                f"{'Consider reviewing your captaincy since your current captain is out.' if captain_p and captain_p.is_dismissed else 'Your team is active and on track for solid bragging rights.'}"
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
            title=f"Squad Performance Table (Over {over})",
            summary=f"Team score is {team_score.total_points} points.",
            confidence_note="Audited from deterministic scoring engine.",
            table_headers=["Player", "Role", "Points", "Runs/Wkts", "Status"],
            table_rows=evidence_rows,
        )
        return ChatResponse(answer=ans, evidence=evidence, over=over, language=language)

    # 7. Default: Points Explanation ("Why did my points change?")
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

    net = explain_res.net_points_change
    direction = "gained" if net >= 0 else "lost"
    direction_hi = "badhe" if net >= 0 else "kam hue"

    top_movers = [p for p in explain_res.player_changes if p.delta_points != 0]
    top_movers.sort(key=lambda x: abs(x.delta_points), reverse=True)

    if top_movers:
        primary = top_movers[0]
        cause_summary_en = f"{primary.player_name} contributed {('+' if primary.delta_points > 0 else '')}{primary.delta_points} pts ({', '.join(primary.causes)})"
        cause_summary_hi = f"{primary.player_name} ne {('+' if primary.delta_points > 0 else '')}{primary.delta_points} pts banaye ({', '.join(primary.causes)})"
    else:
        cause_summary_en = "no major point events occurred during this quiet over"
        cause_summary_hi = "is over me koi bada event nahi hua"

    if is_hinglish:
        ans = (
            f"Over {compare_over} se Over {over} ke beech aapki team ke {abs(net)} points {direction_hi} aur ab total {explain_res.current_total_points} points hain. "
            f"Iska main reason yeh raha ki {cause_summary_hi}. "
            f"Ball-by-ball exact numbers dekhne ke liye niche 'Show the numbers' par tap karein."
        )
    else:
        ans = (
            f"Your team {direction} {abs(net)} points between Over {compare_over} and Over {over}, moving to {explain_res.current_total_points} points. "
            f"The primary driver was that {cause_summary_en}. "
            f"Tap 'Show the numbers' below if you want to inspect the exact ball-by-ball ledger."
        )

    evidence = EvidencePayload(
        tool_called="explain_points_change",
        title=f"Points Movement Audit (Over {compare_over} to Over {over})",
        summary=explain_res.summary_narrative,
        confidence_note="100% deterministic attribution from match timeline.",
        table_headers=["Player", "Role", f"Over {compare_over} Pts", f"Over {over} Pts", "Delta", "Key Causes"],
        table_rows=explain_res.evidence_table,
        raw_data={"previous_total": explain_res.previous_total_points, "current_total": explain_res.current_total_points, "net_delta": net},
    )

    return ChatResponse(
        answer=ans,
        evidence=evidence,
        over=over,
        language=language,
    )
