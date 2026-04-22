"""
Defactra AI - save_risk_data.py
================================
Drop this file next to app.py.
Call save_all_risk_data() from app.py right after the inspection
finishes saving to ai_detections / findings.

Integration in app.py (New Inspection flow, after all findings saved):
    from save_risk_data import save_all_risk_data
    save_all_risk_data(conn, property_id)
"""

import uuid
import pandas as pd
import streamlit as st

# ── Weights ───────────────────────────────────────────────────────────────────
SEVERITY_WEIGHTS = {"critical": 25, "high": 10, "medium": 4, "low": 1}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _severity_counts(df: pd.DataFrame) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for sev in df["severity"].dropna():
        key = sev.strip().lower()
        if key in counts:
            counts[key] += 1
    return counts


def _calc_score(counts: dict, total: int) -> float:
    if total == 0:
        return 100.0
    penalty = sum(counts[s] * SEVERITY_WEIGHTS[s] for s in counts)
    return round(max(0.0, min(100.0, 100.0 - penalty)), 2)


def _grade(score: float) -> str:
    if score >= 90: return "A"
    if score >= 75: return "B"
    if score >= 55: return "C"
    if score >= 35: return "D"
    return "F"


def _risk_category(score: float) -> str:
    if score >= 70: return "Low Risk"
    if score >= 40: return "Medium Risk"
    return "High Risk"


def _build_summary(pid, address, counts, total, score) -> str:
    grade = _grade(score)
    if score >= 75:
        status = "generally in good condition with some maintenance items noted"
    elif score >= 55:
        status = "in fair condition requiring moderate repairs"
    elif score >= 35:
        status = "in poor condition needing significant attention"
    else:
        status = "in critical condition with serious safety concerns"

    text = (
        f"Property {pid} ({address}) is {status}. "
        f"AI inspection detected {total} defect(s): "
        f"{counts['critical']} critical, {counts['high']} high, "
        f"{counts['medium']} medium, {counts['low']} low. "
        f"Overall score: {score}/100 (Grade {grade}). "
    )
    if counts["critical"] > 0:
        text += (
            f"URGENT: {counts['critical']} critical issue(s) require immediate "
            "professional repair for occupant safety. "
        )
    if counts["high"] > 0:
        text += f"{counts['high']} high-priority issue(s) should be resolved within 7 days. "
    text += (
        "Regular maintenance and periodic AI-assisted inspections are recommended "
        "to maintain property value and safety standards."
    )
    return text


# ── Core save function ────────────────────────────────────────────────────────
def save_all_risk_data(conn, property_id: str) -> bool:
    """
    Compute and UPSERT risk scores + summary for `property_id`.
    Call this after every completed inspection.

    Returns True on success, False on failure.
    """
    try:
        cursor = conn.cursor()

        # ── Fetch property meta ────────────────────────────────────────────
        prop_df = pd.read_sql(
            f"SELECT address, city FROM properties WHERE property_id = '{property_id}'",
            conn,
        )
        prop_df.columns = prop_df.columns.str.lower()
        if prop_df.empty:
            st.warning(f"⚠️ Property {property_id} not found in properties table.")
            return False

        address  = prop_df["address"].iloc[0] or "Unknown"
        city     = prop_df["city"].iloc[0] or ""
        full_addr = f"{address}, {city}".strip(", ")

        # ── Fetch all detections for property ─────────────────────────────
        det_df = pd.read_sql(
            f"""
            SELECT r.room_id, r.room_name, r.room_type,
                   ad.severity, ad.confidence_score, ad.detected_object
            FROM findings f
            JOIN rooms r          ON f.room_id = r.room_id
            JOIN ai_detections ad ON f.detection_id = ad.detection_id
            WHERE r.property_id = '{property_id}'
            """,
            conn,
        )
        det_df.columns = det_df.columns.str.lower()

        total        = len(det_df)
        p_counts     = _severity_counts(det_df)
        p_score      = _calc_score(p_counts, total)
        p_grade      = _grade(p_score)
        p_cat        = _risk_category(p_score)

        pid = property_id  # must be defined before room loop

        # ── Room-level scores ──────────────────────────────────────────────
        high_risk_rooms = 0
        total_rooms     = 0

        for (room_id, room_name, room_type), room_df in det_df.groupby(
            ["room_id", "room_name", "room_type"]
        ):
            total_rooms += 1
            rc = _severity_counts(room_df)
            rs = _calc_score(rc, len(room_df))
            rcat = _risk_category(rs)
            if rcat == "High Risk":
                high_risk_rooms += 1

            cursor.execute(
                """
                MERGE INTO room_risk_scores t
                USING (SELECT %s AS room_id) s ON t.room_id = s.room_id
                WHEN MATCHED THEN UPDATE SET
                    property_id = %s, room_name = %s, room_type = %s,
                    room_risk_score = %s, risk_category = %s,
                    total_defects = %s, critical_count = %s,
                    high_count = %s, medium_count = %s
                WHEN NOT MATCHED THEN INSERT
                    (room_id, property_id, room_name, room_type,
                     room_risk_score, risk_category,
                     total_defects, critical_count, high_count, medium_count)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    room_id,
                    pid, room_name, room_type or "room", rs, rcat,
                    len(room_df), rc["critical"], rc["high"], rc["medium"],
                    room_id, pid, room_name, room_type or "room", rs, rcat,
                    len(room_df), rc["critical"], rc["high"], rc["medium"],
                ),
            )

        pid = property_id  # must be defined before room loop (already set above)

        # ── Property-level score ───────────────────────────────────────────
        # Ensure required columns exist (safe to run repeatedly)
        for col in ("total_high", "total_medium", "total_low"):
            try:
                cursor.execute(
                    f"ALTER TABLE property_risk_scores ADD COLUMN {col} INT DEFAULT 0"
                )
            except Exception:
                pass  # column already exists

        cursor.execute(
            """
            MERGE INTO property_risk_scores t
            USING (SELECT %s AS property_id) s ON t.property_id = s.property_id
            WHEN MATCHED THEN UPDATE SET
                address = %s, property_risk_score = %s,
                property_grade = %s, property_risk_category = %s,
                total_defects = %s, total_critical = %s,
                total_high = %s, total_medium = %s, total_low = %s,
                high_risk_rooms = %s, total_rooms = %s
            WHEN NOT MATCHED THEN INSERT
                (property_id, address, property_risk_score,
                 property_grade, property_risk_category,
                 total_defects, total_critical, total_high,
                 total_medium, total_low,
                 high_risk_rooms, total_rooms)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                pid,
                full_addr, p_score, p_grade, p_cat,
                total, p_counts["critical"],
                p_counts["high"], p_counts["medium"], p_counts["low"],
                high_risk_rooms, total_rooms,
                pid, full_addr, p_score, p_grade, p_cat,
                total, p_counts["critical"],
                p_counts["high"], p_counts["medium"], p_counts["low"],
                high_risk_rooms, total_rooms,
            ),
        )

        # ── Inspection summary ─────────────────────────────────────────────
        summary_text = _build_summary(pid, full_addr, p_counts, total, p_score)
        summary_id   = str(uuid.uuid4())

        cursor.execute(
            """
            MERGE INTO inspection_summaries t
            USING (SELECT %s AS property_id) s ON t.property_id = s.property_id
            WHEN MATCHED THEN UPDATE SET summary_text = %s
            WHEN NOT MATCHED THEN INSERT (summary_id, property_id, summary_text)
            VALUES (%s, %s, %s)
            """,
            (pid, summary_text, summary_id, pid, summary_text),
        )

        conn.commit()
        return True

    except Exception as e:
        st.error(f"❌ Failed to save risk data: {e}")
        import traceback
        st.code(traceback.format_exc())
        return False


# ── Dashboard query helpers (use these in app.py tabs) ───────────────────────
def fetch_property_overview(conn, property_id: str) -> pd.DataFrame:
    """For the 📊 Dashboard tab."""
    df = pd.read_sql(
        f"""
        SELECT
            prs.property_risk_score,
            prs.property_grade,
            prs.property_risk_category,
            prs.total_defects,
            prs.total_critical,
            prs.high_risk_rooms,
            prs.total_rooms,
            p.address, p.city, p.property_type, p.bedrooms, p.area_sqft, p.year_built
        FROM property_risk_scores prs
        JOIN properties p ON prs.property_id = p.property_id
        WHERE prs.property_id = '{property_id}'
        """,
        conn,
    )
    df.columns = df.columns.str.lower()
    return df


def fetch_room_risk_scores(conn, property_id: str) -> pd.DataFrame:
    """For the 📈 Risk Analysis tab."""
    df = pd.read_sql(
        f"""
        SELECT room_name, room_type, room_risk_score, risk_category,
               total_defects, critical_count, high_count, medium_count
        FROM room_risk_scores
        WHERE property_id = '{property_id}'
        ORDER BY room_risk_score ASC
        """,
        conn,
    )
    df.columns = df.columns.str.lower()
    return df


def fetch_inspection_summary(conn, property_id: str) -> str:
    """For the 📝 Summary Report tab."""
    df = pd.read_sql(
        f"SELECT summary_text FROM inspection_summaries WHERE property_id = '{property_id}'",
        conn,
    )
    df.columns = df.columns.str.lower()
    if df.empty:
        return ""
    return df["summary_text"].iloc[0]