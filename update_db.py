# update_db.py
from app import app
from models import db
from sqlalchemy import text

def update_database():
    """Adds all missing columns to the applications table without deleting data."""
    with app.app_context():
        print("Checking current database schema...")

        # 1. Get the list of columns that already exist
        result = db.session.execute(text("PRAGMA table_info(applications)")).fetchall()
        existing_columns = [col[1] for col in result]
        print(f"Existing columns: {existing_columns}")

        # 2. Define all the new columns we need to add (based on your updated models.py)
        columns_to_add = [
            ("interview_date", "VARCHAR(20)"),
            ("interview_time", "VARCHAR(20)"),
            ("interview_mode", "VARCHAR(50)"),
            ("interview_location", "VARCHAR(200)"),
            ("interview_scheduled", "BOOLEAN DEFAULT 0"),
            ("interview_round1_status", "VARCHAR(20) DEFAULT 'pending'"),
            ("interview_round1_remarks", "TEXT"),
            ("interview_round2_status", "VARCHAR(20) DEFAULT 'pending'"),
            ("interview_round2_remarks", "TEXT"),
            ("interview_round3_status", "VARCHAR(20) DEFAULT 'pending'"),
            ("interview_round3_remarks", "TEXT"),
            ("technical_score", "INTEGER"),
            ("communication_score", "INTEGER"),
            ("overall_score", "INTEGER"),
            ("offer_letter_generated", "BOOLEAN DEFAULT 0"),
            ("offer_letter_path", "VARCHAR(200)"),
            ("offer_letter_sent_date", "DATETIME"),
            ("offer_accepted", "BOOLEAN DEFAULT 0"),
            ("offer_acceptance_date", "DATETIME"),
            ("joining_date", "VARCHAR(20)"),
            ("joining_confirmed", "BOOLEAN DEFAULT 0")
        ]

        # 3. Add columns one by one if they are missing
        print("\nAdding missing columns...")
        columns_added = 0
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                try:
                    # The core SQL command to add a column
                    sql_command = f"ALTER TABLE applications ADD COLUMN {col_name} {col_type}"
                    db.session.execute(text(sql_command))
                    db.session.commit()
                    print(f"  ✅ Added: {col_name}")
                    columns_added += 1
                except Exception as e:
                    # Rollback in case of error for this specific column
                    db.session.rollback()
                    print(f"  ❌ Error adding {col_name}: {e}")
            else:
                print(f"  ⏩ Already exists: {col_name}")

        # 4. Final report
        if columns_added > 0:
            print(f"\n✅ Successfully added {columns_added} new columns to the 'applications' table.")
        else:
            print("\n✅ No new columns were needed. Your table is already up-to-date.")

        # 5. Verify the final schema
        result = db.session.execute(text("PRAGMA table_info(applications)")).fetchall()
        final_columns = [col[1] for col in result]
        print(f"\n📊 Final columns in database ({len(final_columns)} total):")
        print(final_columns)

if __name__ == "__main__":
    update_database()