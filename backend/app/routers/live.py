from fastapi import APIRouter

from ..services import openf1

router = APIRouter(prefix="/api/live", tags=["live"])


def _latest_by(rows: list[dict], key: str) -> dict:
    out: dict = {}
    for r in rows:  # rows are time-ordered; last wins
        out[r[key]] = r
    return out


@router.get("/session")
def live_session():
    """Latest OpenF1 session (live if one is running, otherwise the most recent finished one)."""
    sessions = openf1.get("sessions", ttl=30, session_key="latest")
    if not sessions:
        return {"session": None}
    sess = sessions[-1]
    sk = sess["session_key"]
    drivers = {d["driver_number"]: d for d in openf1.get("drivers", ttl=300, session_key=sk)}
    pos = _latest_by(openf1.get("position", session_key=sk), "driver_number")
    gaps = _latest_by(openf1.get("intervals", session_key=sk), "driver_number")
    tower = []
    for num, p in sorted(pos.items(), key=lambda kv: kv[1]["position"]):
        d = drivers.get(num, {})
        g = gaps.get(num, {})
        tower.append(
            {
                "position": p["position"],
                "driver_number": num,
                "code": d.get("name_acronym"),
                "name": d.get("full_name"),
                "team": d.get("team_name"),
                "team_colour": d.get("team_colour"),
                "gap_to_leader": g.get("gap_to_leader"),
                "interval": g.get("interval"),
            }
        )
    weather = openf1.get("weather", session_key=sk)
    msgs = openf1.get("race_control", session_key=sk)
    return {
        "session": {k: sess.get(k) for k in ("session_key", "session_name", "session_type", "circuit_short_name", "country_name", "date_start", "date_end", "year")},
        "tower": tower,
        "weather": weather[-1] if weather else None,
        "race_control": msgs[-10:][::-1],
    }
