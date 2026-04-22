"""
Defactra AI - Risk Score Backfill Script
========================================
Run this ONCE to fix existing properties that have detections
but missing risk scores / summaries in the database.

Usage:
    backfill_risk_scores.py
"""

import snowflake.connector
import pandas as pd
import uuid
from datetime import datetime

# ── Connection ────────────────────────────────────────────────────────────────
SNOWFLAKE_CONFIG = {
    "user":      "PARAGOD2",
    "password":  "Sivanandshibu@2004",
    "account":   "ZISLDVH-YL82287",
    "warehouse": "COMPUTE_WH",
    "database":  "PROPERTY_INSPECTION",
    "schema":    "INSPECTION_DATA",
}


def get_connection():
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)


# ── Risk scoring helpers ──────────────────────────────────────────────────────
SEVERITY_WEIGHTS = {"critical": 25, "high": 10, "medium": 4, "low": 1}
SEVERITY_THRESHOLDS = {
    "property_grade": [(90, "A"), (75, "B"), (55, "C"), (35, "D"), (0, "F")],
    "risk_category":  [(70, "Low Risk"), (40, "Medium Risk"), (0, "High Risk")],
}


def severity_counts(detections_df):
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for sev in detections_df["severity"].dropna():
        s = sev.strip().lower()
        if s in counts:
            counts[s] += 1
    return counts


def calc_property_score(counts, total):
    if total == 0:
        return 100.0
    penalty = (
        counts["critical"] * SEVERITY_WEIGHTS["critical"]
        + counts["high"]    * SEVERITY_WEIGHTS["high"]
        + counts["medium"]  * SEVERITY_WEIGHTS["medium"]
        + counts["low"]     * SEVERITY_WEIGHTS["low"]
    )
    return max(0.0, min(100.0, 100.0 - penalty))


def grade(score):
    for threshold, label in SEVERITY_THRESHOLDS["property_grade"]:
        if score >= threshold:
            return label
    return "F"


def risk_category(score):
    for threshold, label in SEVERITY_THRESHOLDS["risk_category"]:
        if score >= threshold:
            return label
    return "High Risk"


def generate_summary(property_id, address, counts, total, prop_score):
    grade_label = grade(prop_score)
    if prop_score >= 75:
        status = "generally in good condition with some maintenance items noted"
    elif prop_score >= 55:
        status = "in fair condition requiring moderate repairs"
    elif prop_score >= 35:
        status = "in poor condition needing significant attention"
    else:
        status = "in critical condition with serious safety concerns"

    summary = (
        f"Property {property_id} ({address}) is {status}. "
        f"AI inspection detected {total} total defect(s): "
        f"{counts['critical']} critical, {counts['high']} high, "
        f"{counts['medium']} medium, {counts['low']} low priority. "
        f"Overall property condition score: {prop_score:.1f}/100 (Grade {grade_label}). "
    )

    if counts["critical"] > 0:
        summary += (
            f"URGENT: {counts['critical']} critical issue(s) require immediate professional "
            "inspection and repair to ensure occupant safety. "
        )
    if counts["high"] > 0:
        summary += (
            f"{counts['high']} high-priority issue(s) should be addressed within 7 days "
            "to prevent further deterioration. "
        )
    summary += (
        "Regular maintenance and periodic AI-assisted inspections are recommended "
        "to maintain property value and safety standards."
    )
    return summary


# ── Main backfill ─────────────────────────────────────────────────────────────
def backfill(conn):
    cursor = conn.cursor()

    # 1. Find all properties that have detections but missing risk scores
    print("\n🔍 Scanning for properties with missing risk data...")

    missing_df = pd.read_sql(
        """
        SELECT DISTINCT r.property_id
        FROM findings f
        JOIN rooms r ON f.room_id = r.room_id
        JOIN ai_detections ad ON f.detection_id = ad.detection_id
        WHERE r.property_id NOT IN (
            SELECT property_id FROM property_risk_scores
        )
        """,
        conn,
    )
    missing_df.columns = missing_df.columns.str.lower()

    if missing_df.empty:
        print("✅ No properties with missing risk data found.")
        # Also check if any property has stale (0-defect) risk scores
    else:
        print(f"   Found {len(missing_df)} propert(ies) to backfill: {list(missing_df['property_id'])}")

    # Process every property that has detections (insert or replace)
    all_props_df = pd.read_sql(
        """
        SELECT DISTINCT r.property_id, p.address, p.city
        FROM findings f
        JOIN rooms r    ON f.room_id = r.room_id
        JOIN properties p ON r.property_id = p.property_id
        JOIN ai_detections ad ON f.detection_id = ad.detection_id
        """,
        conn,
    )
    all_props_df.columns = all_props_df.columns.str.lower()

    if all_props_df.empty:
        print("⚠️  No properties with AI detections found at all.")
        return

    for _, prop_row in all_props_df.iterrows():
        pid     = prop_row["property_id"]
        address = prop_row.get("address", "Unknown")
        city    = prop_row.get("city", "")
        full_address = f"{address}, {city}".strip(", ")

        print(f"\n📦 Processing property: {pid}")

        # ── Fetch all detections for this property ─────────────────────────
        det_df = pd.read_sql(
            f"""
            SELECT
                r.room_id,
                r.room_name,
                r.room_type,
                ad.severity,
                ad.confidence_score,
                ad.detected_object
            FROM findings f
            JOIN rooms r    ON f.room_id = r.room_id
            JOIN ai_detections ad ON f.detection_id = ad.detection_id
            WHERE r.property_id = '{pid}'
            """,
            conn,
        )
        det_df.columns = det_df.columns.str.lower()

        total   = len(det_df)
        counts  = severity_counts(det_df)
        p_score = calc_property_score(counts, total)
        p_grade = grade(p_score)
        p_cat   = risk_category(p_score)

        # ── Count high-risk rooms ──────────────────────────────────────────
        room_groups = det_df.groupby(["room_id", "room_name", "room_type"])
        high_risk_rooms = 0
        total_rooms     = 0

        for (room_id, room_name, room_type), room_det in room_groups:
            total_rooms += 1
            room_counts = severity_counts(room_det)
            room_total  = len(room_det)
            room_score  = calc_property_score(room_counts, room_total)
            room_cat    = risk_category(room_score)

            if room_cat == "High Risk":
                high_risk_rooms += 1

            # ── Upsert room_risk_scores ────────────────────────────────────
            cursor.execute(
                """
                MERGE INTO room_risk_scores t
                USING (SELECT %s AS room_id) s ON t.room_id = s.room_id
                WHEN MATCHED THEN UPDATE SET
                    property_id     = %s,
                    room_name       = %s,
                    room_type       = %s,
                    room_risk_score = %s,
                    risk_category   = %s,
                    total_defects   = %s,
                    critical_count  = %s,
                    high_count      = %s,
                    medium_count    = %s
                WHEN NOT MATCHED THEN INSERT
                    (room_id, property_id, room_name, room_type,
                     room_risk_score, risk_category,
                     total_defects, critical_count, high_count, medium_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    # USING clause
                    room_id,
                    # UPDATE
                    pid, room_name, room_type or "room",
                    room_score, room_cat,
                    room_total,
                    room_counts["critical"], room_counts["high"], room_counts["medium"],
                    # INSERT
                    room_id, pid, room_name, room_type or "room",
                    room_score, room_cat,
                    room_total,
                    room_counts["critical"], room_counts["high"], room_counts["medium"],
                ),
            )
            print(f"   ✅ Room '{room_name}': score={room_score:.1f} ({room_cat}), defects={room_total}")

        # ── Upsert property_risk_scores ────────────────────────────────────
        cursor.execute(
            """
            MERGE INTO property_risk_scores t
            USING (SELECT %s AS property_id) s ON t.property_id = s.property_id
            WHEN MATCHED THEN UPDATE SET
                address                 = %s,
                property_risk_score     = %s,
                property_grade          = %s,
                property_risk_category  = %s,
                total_defects           = %s,
                total_critical          = %s,
                high_risk_rooms         = %s,
                total_rooms             = %s
            WHEN NOT MATCHED THEN INSERT
                (property_id, address,
                 property_risk_score, property_grade, property_risk_category,
                 total_defects, total_critical, high_risk_rooms, total_rooms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                pid,
                # UPDATE
                full_address,
                p_score, p_grade, p_cat,
                total, counts["critical"], high_risk_rooms, total_rooms,
                # INSERT
                pid, full_address,
                p_score, p_grade, p_cat,
                total, counts["critical"], high_risk_rooms, total_rooms,
            ),
        )
        print(f"   ✅ Property score: {p_score:.1f} (Grade {p_grade} | {p_cat})")

        # ── Upsert inspection_summaries ────────────────────────────────────
        summary_text = generate_summary(pid, full_address, counts, total, p_score)
        summary_id   = str(uuid.uuid4())

        cursor.execute(
            """
            MERGE INTO inspection_summaries t
            USING (SELECT %s AS property_id) s ON t.property_id = s.property_id
            WHEN MATCHED THEN UPDATE SET
                summary_text = %s
            WHEN NOT MATCHED THEN INSERT
                (summary_id, property_id, summary_text)
            VALUES (%s, %s, %s)
            """,
            (
                pid,
                # UPDATE
                summary_text,
                # INSERT
                summary_id, pid, summary_text,
            ),
        )
        print(f"   ✅ Summary written ({len(summary_text)} chars)")

    conn.commit()
    print("\n🎉 Backfill complete! All risk scores and summaries are now in the database.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("Defactra AI - Risk Score Backfill")
    print("=" * 60)
    try:
        conn = get_connection()
        print("✅ Connected to Snowflake")
        backfill(conn)
        conn.close()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()