"""Sample match seed script for Match Copilot.

Loads ONE sample T20 match with ball-by-ball data and sample fantasy teams.
Sample data. Not official Dream11 scoring.
"""

from datetime import datetime, timezone

from app.core.logging import logger
from app.db.models import ChatMessage, Delivery, FantasyTeam, FantasyTeamPlayer, Match, Player
from app.db.session import Base, SessionLocal, engine

PLAYERS_DATA = [
    # MI (Mumbai Indians)
    {"id": "p_rohit", "name": "Rohit Sharma", "team": "MI", "role": "BAT", "credits": 9.5},
    {"id": "p_ishan", "name": "Ishan Kishan", "team": "MI", "role": "WK", "credits": 8.5},
    {"id": "p_surya", "name": "Suryakumar Yadav", "team": "MI", "role": "BAT", "credits": 9.5},
    {"id": "p_tilak", "name": "Tilak Varma", "team": "MI", "role": "BAT", "credits": 8.0},
    {"id": "p_hardik", "name": "Hardik Pandya", "team": "MI", "role": "AR", "credits": 9.0},
    {"id": "p_david", "name": "Tim David", "team": "MI", "role": "BAT", "credits": 8.0},
    {"id": "p_shepherd", "name": "Romario Shepherd", "team": "MI", "role": "AR", "credits": 7.5},
    {"id": "p_coetzee", "name": "Gerald Coetzee", "team": "MI", "role": "BOWL", "credits": 8.5},
    {"id": "p_chawla", "name": "Piyush Chawla", "team": "MI", "role": "BOWL", "credits": 7.5},
    {"id": "p_bumrah", "name": "Jasprit Bumrah", "team": "MI", "role": "BOWL", "credits": 9.5},
    {"id": "p_thushara", "name": "Nuwan Thushara", "team": "MI", "role": "BOWL", "credits": 7.5},

    # CSK (Chennai Super Kings)
    {"id": "p_ruturaj", "name": "Ruturaj Gaikwad", "team": "CSK", "role": "BAT", "credits": 9.0},
    {"id": "p_rachin", "name": "Rachin Ravindra", "team": "CSK", "role": "AR", "credits": 8.5},
    {"id": "p_rahane", "name": "Ajinkya Rahane", "team": "CSK", "role": "BAT", "credits": 8.0},
    {"id": "p_dube", "name": "Shivam Dube", "team": "CSK", "role": "AR", "credits": 9.0},
    {"id": "p_mitchell", "name": "Daryl Mitchell", "team": "CSK", "role": "AR", "credits": 8.5},
    {"id": "p_jadeja", "name": "Ravindra Jadeja", "team": "CSK", "role": "AR", "credits": 9.0},
    {"id": "p_dhoni", "name": "MS Dhoni", "team": "CSK", "role": "WK", "credits": 8.5},
    {"id": "p_shardul", "name": "Shardul Thakur", "team": "CSK", "role": "BOWL", "credits": 8.0},
    {"id": "p_deshpande", "name": "Tushar Deshpande", "team": "CSK", "role": "BOWL", "credits": 7.5},
    {"id": "p_mustafizur", "name": "Mustafizur Rahman", "team": "CSK", "role": "BOWL", "credits": 8.5},
    {"id": "p_pathirana", "name": "Matheesha Pathirana", "team": "CSK", "role": "BOWL", "credits": 9.0},
]


def generate_20_overs_deliveries(match_id: str) -> list[dict]:
    """Generates an authentic, narrative-driven 20 overs ball-by-ball sequence.

    Innings 1: MT batting, CS bowling.
    Final Score: 184/5 in 20.0 overs.
    Narrative highlights:
    - Over 1-2: Rohit & Ishan steady start against Chahar/Deshpande.
    - Over 3: Ishan hits boundary then gets caught by Dhoni off Deshpande (wicket 1).
    - Over 4: Surya arrives, hits classy fours.
    - Over 6: Rohit hits a huge six off Mustafizur, powerplay finishes 54/1.
    - Over 8: Jadeja bowls tight maiden / 1-run over, Rohit dismissed for 38.
    - Over 11: Tilak Varma out for duck (0 off 2 balls, caught Jadeja b Pathirana) - duck penalty!
    - Over 14: Hardik Pandya & Surya steady ship, Surya reaches 50!
    - Over 16: Pathirana bowls Surya (bowled bonus!).
    - Over 19-20: Hardik & Tim David death overs finish, David hits sixes off Shardul.
    """
    deliveries = []

    # Map overs to bowlers and planned events
    # Each over: (over_num, bowler_id, balls: list of (batter, non_striker, runs_b, extras, extra_type, is_w, kind, dism, fielder))
    over_scripts = [
        # Over 1: Deshpande to Rohit & Ishan (8 runs: 0, 4, 1, 0, 2, 1)
        (1, "p_deshpande", [
            ("p_rohit", "p_ishan", 0, 0, None, False, None, None, None),
            ("p_rohit", "p_ishan", 4, 0, None, False, None, None, None),
            ("p_rohit", "p_ishan", 1, 0, None, False, None, None, None),
            ("p_ishan", "p_rohit", 0, 0, None, False, None, None, None),
            ("p_ishan", "p_rohit", 2, 0, None, False, None, None, None),
            ("p_ishan", "p_rohit", 1, 0, None, False, None, None, None),
        ]),
        # Over 2: Shardul to Ishan & Rohit (9 runs: 1, 0, 4, 1, 2, 1)
        (2, "p_shardul", [
            ("p_ishan", "p_rohit", 1, 0, None, False, None, None, None),
            ("p_rohit", "p_ishan", 0, 0, None, False, None, None, None),
            ("p_rohit", "p_ishan", 4, 0, None, False, None, None, None),
            ("p_rohit", "p_ishan", 1, 0, None, False, None, None, None),
            ("p_ishan", "p_rohit", 2, 0, None, False, None, None, None),
            ("p_ishan", "p_rohit", 1, 0, None, False, None, None, None),
        ]),
        # Over 3: Deshpande to Ishan - WICKET! caught Dhoni (6 runs, 1 wicket: 4, 0, W, 0, 1, 1)
        (3, "p_deshpande", [
            ("p_ishan", "p_rohit", 4, 0, None, False, None, None, None),
            ("p_ishan", "p_rohit", 0, 0, None, False, None, None, None),
            ("p_ishan", "p_rohit", 0, 0, None, True, "caught", "p_ishan", "p_dhoni"),
            ("p_surya", "p_rohit", 0, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 1, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 1, 0, None, False, None, None, None),
        ]),
        # Over 4: Mustafizur to Rohit & Surya (11 runs: 4, 1, 4, 0, 1, 1)
        (4, "p_mustafizur", [
            ("p_rohit", "p_surya", 4, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 4, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 0, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 1, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 1, 0, None, False, None, None, None),
        ]),
        # Over 5: Shardul to Surya & Rohit (8 runs: 2, 1, 1, 2, 1, 1)
        (5, "p_shardul", [
            ("p_surya", "p_rohit", 2, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 1, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 2, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 1, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 1, 0, None, False, None, None, None),
        ]),
        # Over 6: Mustafizur to Rohit - 6! Powerplay end (12 runs: 6, 1, 0, 4, 0, 1)
        (6, "p_mustafizur", [
            ("p_rohit", "p_surya", 6, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 0, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 4, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 0, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 1, 0, None, False, None, None, None),
        ]),
        # Over 7: Jadeja to Surya & Rohit (5 runs: 1, 1, 1, 0, 1, 1)
        (7, "p_jadeja", [
            ("p_surya", "p_rohit", 1, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 1, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 0, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_rohit", 1, 0, None, False, None, None, None),
        ]),
        # Over 8: Rachin to Rohit - WICKET! caught Ruturaj (4 runs, 1 wicket: 1, 1, W, 0, 1, 1)
        (8, "p_rachin", [
            ("p_surya", "p_rohit", 1, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 1, 0, None, False, None, None, None),
            ("p_rohit", "p_surya", 0, 0, None, True, "caught", "p_rohit", "p_ruturaj"),
            ("p_hardik", "p_surya", 0, 0, None, False, None, None, None),
            ("p_hardik", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_hardik", 1, 0, None, False, None, None, None),
        ]),
        # Over 9: Jadeja to Surya & Hardik (6 runs: 1, 2, 1, 1, 0, 1)
        (9, "p_jadeja", [
            ("p_surya", "p_hardik", 1, 0, None, False, None, None, None),
            ("p_hardik", "p_surya", 2, 0, None, False, None, None, None),
            ("p_hardik", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_hardik", 1, 0, None, False, None, None, None),
            ("p_hardik", "p_surya", 0, 0, None, False, None, None, None),
            ("p_hardik", "p_surya", 1, 0, None, False, None, None, None),
        ]),
        # Over 10: Pathirana to Hardik & Surya (7 runs: 0, 1, 4, 1, 0, 1)
        (10, "p_pathirana", [
            ("p_hardik", "p_surya", 0, 0, None, False, None, None, None),
            ("p_hardik", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_hardik", 4, 0, None, False, None, None, None),
            ("p_surya", "p_hardik", 1, 0, None, False, None, None, None),
            ("p_hardik", "p_surya", 0, 0, None, False, None, None, None),
            ("p_hardik", "p_surya", 1, 0, None, False, None, None, None),
        ]),
        # Over 11: Jadeja to Hardik - WICKET! Tilak Varma in and out for DUCK (wicket: 0, W, 0, W, 1, 1)
        # Tilak dismissed for 0 (2 balls, caught Jadeja b Jadeja) -> DUCK PENALTY!
        (11, "p_jadeja", [
            ("p_hardik", "p_surya", 0, 0, None, True, "caught", "p_hardik", "p_mitchell"),
            ("p_tilak", "p_surya", 0, 0, None, False, None, None, None),
            ("p_tilak", "p_surya", 0, 0, None, True, "caught", "p_tilak", "p_jadeja"),
            ("p_david", "p_surya", 0, 0, None, False, None, None, None),
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_david", 1, 0, None, False, None, None, None),
        ]),
        # Over 12: Pathirana to Surya & David (8 runs: 2, 1, 1, 2, 1, 1)
        (12, "p_pathirana", [
            ("p_surya", "p_david", 2, 0, None, False, None, None, None),
            ("p_surya", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_david", 2, 0, None, False, None, None, None),
            ("p_surya", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
        ]),
        # Over 13: Deshpande to David & Surya (11 runs: 1, 4, 1, 4, 0, 1)
        (13, "p_deshpande", [
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_david", 4, 0, None, False, None, None, None),
            ("p_surya", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_surya", 4, 0, None, False, None, None, None),
            ("p_david", "p_surya", 0, 0, None, False, None, None, None),
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
        ]),
        # Over 14: Mustafizur to Surya - Surya completes 50! (10 runs: 2, 4, 1, 1, 1, 1)
        (14, "p_mustafizur", [
            ("p_surya", "p_david", 2, 0, None, False, None, None, None),
            ("p_surya", "p_david", 4, 0, None, False, None, None, None),
            ("p_surya", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
        ]),
        # Over 15: Jadeja to David & Surya (5 runs: 1, 1, 1, 1, 0, 1) -> End of 15th over (Score: 122/4)
        (15, "p_jadeja", [
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
            ("p_surya", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_surya", 0, 0, None, False, None, None, None),
            ("p_david", "p_surya", 1, 0, None, False, None, None, None),
        ]),
        # Over 16: Pathirana to Surya - WICKET! Bowled! (4 runs, 1 wicket: 0, W, 1, 1, 1, 1)
        (16, "p_pathirana", [
            ("p_surya", "p_david", 0, 0, None, False, None, None, None),
            ("p_surya", "p_david", 0, 0, None, True, "bowled", "p_surya", None),
            ("p_shepherd", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 1, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 1, 0, None, False, None, None, None),
        ]),
        # Over 17: Shardul to Shepherd & David (13 runs: 4, 1, 6, 1, 0, 1)
        (17, "p_shardul", [
            ("p_shepherd", "p_david", 4, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 6, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 1, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 0, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 1, 0, None, False, None, None, None),
        ]),
        # Over 18: Mustafizur to David & Shepherd (12 runs: 2, 2, 4, 1, 2, 1)
        (18, "p_mustafizur", [
            ("p_david", "p_shepherd", 2, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 2, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 4, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 1, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 2, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 1, 0, None, False, None, None, None),
        ]),
        # Over 19: Pathirana to Shepherd & David (15 runs: 6, 1, 4, 2, 1, 1)
        (19, "p_pathirana", [
            ("p_shepherd", "p_david", 6, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 4, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 2, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 1, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 1, 0, None, False, None, None, None),
        ]),
        # Over 20: Deshpande to Shepherd & David (18 runs: 6, 6, 1, 4, 0, 1)
        (20, "p_deshpande", [
            ("p_shepherd", "p_david", 6, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 6, 0, None, False, None, None, None),
            ("p_shepherd", "p_david", 1, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 4, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 0, 0, None, False, None, None, None),
            ("p_david", "p_shepherd", 1, 0, None, False, None, None, None),
        ]),
    ]

    for over_num, bowler_id, balls in over_scripts:
        for ball_idx, (bat, non_strik, runs_b, extras, xtype, is_w, kind, dism, fielder) in enumerate(balls, 1):
            deliveries.append({
                "match_id": match_id,
                "innings": 1,
                "over_number": over_num,
                "ball_in_over": ball_idx,
                "bowler_id": bowler_id,
                "batter_id": bat,
                "non_striker_id": non_strik,
                "runs_batter": runs_b,
                "runs_extras": extras,
                "extra_type": xtype,
                "is_wicket": is_w,
                "dismissal_kind": kind,
                "dismissed_player_id": dism,
                "fielder_id": fielder,
            })

    return deliveries


SAMPLE_TEAMS = [
    {
        "id": "team_001",
        "name": "Challengers XI",
        "user_name": "Rahul (You)",
        "captain": "p_rohit",       # Rohit Sharma (2.0x)
        "vice_captain": "p_surya",  # Suryakumar Yadav (1.5x)
        "players": [
            "p_rohit", "p_surya", "p_ishan", "p_hardik", "p_bumrah", "p_coetzee",
            "p_ruturaj", "p_jadeja", "p_dube", "p_pathirana", "p_dhoni"
        ],
    },
    {
        "id": "team_002",
        "name": "Powerhitters XI",
        "user_name": "Priya",
        "captain": "p_hardik",
        "vice_captain": "p_dube",
        "players": [
            "p_hardik", "p_david", "p_surya", "p_tilak", "p_bumrah", "p_shepherd",
            "p_ruturaj", "p_rachin", "p_dube", "p_mustafizur", "p_dhoni"
        ],
    },
    {
        "id": "team_003",
        "name": "CSK Super Kings",
        "user_name": "Ankit",
        "captain": "p_jadeja",
        "vice_captain": "p_pathirana",
        "players": [
            "p_ruturaj", "p_rachin", "p_jadeja", "p_pathirana", "p_deshpande", "p_dhoni",
            "p_rohit", "p_surya", "p_bumrah", "p_hardik", "p_coetzee"
        ],
    },
]


def seed_database(force: bool = False) -> None:
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        # Check if already seeded
        existing_match = session.query(Match).filter_by(id="match_001").first()
        if existing_match and not force:
            logger.info("Database already seeded with sample match_001. Updating match metadata...")
            existing_match.name = "MI VS CSK"
            existing_match.short_name = "MI vs CSK"
            existing_match.team1 = "MI"
            existing_match.team2 = "CSK"
            for p in PLAYERS_DATA:
                player = Player(**p)
                session.merge(player)
            session.commit()
            return

        if force:
            logger.info("Force flag passed. Re-seeding database...")
            session.query(ChatMessage).delete()
            session.query(FantasyTeamPlayer).delete()
            session.query(FantasyTeam).delete()
            session.query(Delivery).delete()
            session.query(Match).delete()
            session.query(Player).delete()
            session.commit()

        logger.info("Seeding players...")
        for p in PLAYERS_DATA:
            player = Player(**p)
            session.merge(player)
        session.commit()

        logger.info("Seeding sample match...")
        sample_match = Match(
            id="match_001",
            name="MI VS CSK",
            short_name="MI vs CSK",
            team1="MI",
            team2="CSK",
            venue="Wankhede Stadium, Mumbai",
            status="in_progress",
            current_innings=1,
            total_overs=20,
            created_at=datetime.now(timezone.utc),
        )
        session.merge(sample_match)
        session.commit()

        logger.info("Seeding ball-by-ball deliveries...")
        deliveries = generate_20_overs_deliveries("match_001")
        for d_data in deliveries:
            deliv = Delivery(**d_data)
            session.add(deliv)
        session.commit()

        logger.info("Seeding fantasy teams...")
        for t_info in SAMPLE_TEAMS:
            team = FantasyTeam(
                id=t_info["id"],
                name=t_info["name"],
                user_name=t_info["user_name"],
                created_at=datetime.now(timezone.utc),
            )
            session.merge(team)
            session.commit()

            for p_id in t_info["players"]:
                ftp = FantasyTeamPlayer(
                    team_id=t_info["id"],
                    player_id=p_id,
                    is_captain=(p_id == t_info["captain"]),
                    is_vice_captain=(p_id == t_info["vice_captain"]),
                )
                session.add(ftp)
        session.commit()

        logger.info(f"Database seeded successfully with {len(PLAYERS_DATA)} players, "
                    f"{len(deliveries)} deliveries, and {len(SAMPLE_TEAMS)} fantasy teams.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding database: {e}", exc_info=True)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
