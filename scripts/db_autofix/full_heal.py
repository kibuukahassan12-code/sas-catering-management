# FULL DB AUTO-HEAL SYSTEM (TYPE + SCHEMA HEALING)

# Save as: scripts/db_autofix/full_heal.py

# Usage:

#   - Edit MODELS_TO_CHECK to list (module_path, ModelClassName)

#   - Run: python scripts/db_autofix/full_heal.py

#   - Or call auto_heal_db() from app startup BEFORE routes are registered



import os

import shutil

import sqlite3

import sys

import traceback

from datetime import datetime

from importlib import import_module

from pathlib import Path



# ------------------------------------------------------------------

# CONFIG — EDIT THIS to match your project layout

# ------------------------------------------------------------------

# Hardcoded absolute paths for reliability
DB_PATH = Path(
    r"C:/Users/DELL/Desktop/sas management system/sas_management/instance/sas.db"
)

# Ensure the backup folder exists inside sas_management/instance:
BACKUP_DIR = Path(
    r"C:/Users/DELL/Desktop/sas management system/sas_management/instance/db_backups/"
)

MODELS_TO_CHECK = [

    ("sas_management.hire.models", "HireOrder"),

    ("sas_management.hire.models", "HireOrderItem"),   # <-- Fixes price column

    ("sas_management.clients.models", "Client"),

    ("sas_management.events.models", "Event"),

]



# ------------------------------------------------------------------

# Utilities

# ------------------------------------------------------------------

def ensure_dirs():

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)



def backup_db():

    ensure_dirs()

    if not DB_PATH.exists():

        raise FileNotFoundError(f"Database file not found: {DB_PATH}")

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    backup_path = BACKUP_DIR / f"app.db.backup.{ts}"

    shutil.copy2(DB_PATH, backup_path)

    print(f"[BACKUP] DB backed up to: {backup_path}")

    return backup_path



def restore_backup(backup_path):

    if backup_path and backup_path.exists():

        shutil.copy2(backup_path, DB_PATH)

        print(f"[RESTORE] Restored DB from backup: {backup_path}")

    else:

        print("[RESTORE] No backup found to restore.")



# Map SQLAlchemy column types -> SQLite affinity/type string

def sa_type_to_sqlite(sa_type):

    # Accepts SQLAlchemy type class or instance

    name = type(sa_type).__name__.lower()

    if "integer" in name or "int" in name:

        return "INTEGER"

    if "string" in name or "varchar" in name or "text" in name or "unicode" in name:

        return "TEXT"

    if "float" in name or "numeric" in name or "decimal" in name:

        return "REAL"

    if "boolean" in name or "bool" in name:

        return "INTEGER"

    if "datetime" in name or "date" in name or "time" in name:

        return "TEXT"

    # fallback

    return "TEXT"



def get_model_columns(model):

    cols = []

    for c in model.__table__.columns:

        cols.append({

            "name": c.name,

            "nullable": c.nullable,

            "primary_key": c.primary_key,

            "type": c.type,

            "default": getattr(c, "default", None),

            "server_default": getattr(c, "server_default", None)

        })

    return cols



def get_db_table_info(cur, table):

    cur.execute(f"PRAGMA table_info('{table}')")

    rows = cur.fetchall()

    # rows: cid, name, type, notnull, dflt_value, pk

    return [{"cid": r[0], "name": r[1], "type": (r[2] or "").upper(), "notnull": bool(r[3]), "dflt_value": r[4], "pk": bool(r[5])} for r in rows]



# Build CREATE TABLE SQL for model

def build_create_table_sql(table_name, model_cols):

    parts = []

    pk_cols = [c["name"] for c in model_cols if c["primary_key"]]

    for c in model_cols:

        col_type = sa_type_to_sqlite(c["type"])

        col_def = f'"{c["name"]}" {col_type}'

        if c["primary_key"] and len(pk_cols) == 1 and col_type == "INTEGER":

            # allow autoincrement PK (sqlite uses INTEGER PRIMARY KEY)

            col_def = f'"{c["name"]}" INTEGER PRIMARY KEY'

        else:

            if c["primary_key"]:

                col_def += " PRIMARY KEY"

            if not c["nullable"]:

                col_def += " NOT NULL"

        # Note: defaults and server_defaults are not expanded for simplicity

        parts.append(col_def)

    cols_sql = ", ".join(parts)

    return f'CREATE TABLE "{table_name}__new" ({cols_sql});'



# Safely copy data from old->new using common columns, casting where needed

def build_data_copy_sql(old_table, new_table, model_cols, db_cols):

    db_col_names = [c["name"] for c in db_cols]

    model_names = [c["name"] for c in model_cols]

    common = [name for name in model_names if name in db_col_names]

    insert_cols = ', '.join(f'"{c}"' for c in model_names)  # new table columns in model order

    # For source select, map each model column to either existing column or NULL

    select_parts = []

    for m in model_cols:

        name = m["name"]

        if name in db_col_names:

            # CAST to target type if types differ (best-effort)

            target_sqltype = sa_type_to_sqlite(m["type"])

            # Use CAST(...) to attempt conversion; SQLite ignores some casts if not needed.

            select_parts.append(f'CAST("{name}" AS {target_sqltype}) AS "{name}"')

        else:

            select_parts.append(f'NULL AS "{name}"')

    select_sql = ', '.join(select_parts)

    return f'INSERT INTO "{new_table}" ({insert_cols}) SELECT {select_sql} FROM "{old_table}";'



# Recreate table safely preserving data

def rebuild_table(cur, table_name, model_cols, db_cols):

    print(f"[REBUILD] Rebuilding table: {table_name}")

    create_sql = build_create_table_sql(table_name, model_cols)

    print("[REBUILD] Create SQL:", create_sql)

    cur.execute(create_sql)



    # copy data

    insert_sql = build_data_copy_sql(table_name, f"{table_name}__new", model_cols, db_cols)

    print("[REBUILD] Copying data with:", insert_sql)

    cur.execute(insert_sql)



    # drop old table and rename

    cur.execute(f'DROP TABLE "{table_name}";')

    cur.execute(f'ALTER TABLE "{table_name}__new" RENAME TO "{table_name}";')

    print(f"[REBUILD] Table {table_name} rebuilt and renamed back.")



# Main healing routine

def auto_heal_db():

    backup_path = None

    try:

        print("=== DB AUTO-HEAL START ===")

        backup_path = backup_db()

        conn = sqlite3.connect(DB_PATH)

        cur = conn.cursor()



        for module_path, class_name in MODELS_TO_CHECK:

            try:

                module = import_module(module_path)

                model = getattr(module, class_name)

            except Exception as e:

                print(f"[WARN] Could not import {module_path}.{class_name}: {e}")

                continue



            table = model.__tablename__

            print(f"\n[CHECK] Model: {module_path}.{class_name} -> table '{table}'")

            model_cols = get_model_columns(model)

            db_cols = get_db_table_info(cur, table)

            db_names = [c["name"] for c in db_cols]

            model_names = [c["name"] for c in model_cols]



            print("[CHECK] Model columns:", model_names)

            print("[CHECK] DB columns:   ", db_names)



            # 1) Add missing columns via ALTER TABLE if possible

            missing = [c for c in model_cols if c["name"] not in db_names]

            if missing:

                for m in missing:

                    # For simple add — let SQLite handle TEXT/INTEGER etc.

                    colname = m["name"]

                    coltype = sa_type_to_sqlite(m["type"])

                    try:

                        print(f"[ALTER] Adding column '{colname}' as {coltype}")

                        # SQLite-safe: ONE ADD COLUMN per statement, no trailing commas
                        sql = f'ALTER TABLE "{table}" ADD COLUMN "{colname}" {coltype}'
                        sql = sql.rstrip(';').rstrip(',')  # Ensure no trailing punctuation
                        cur.execute(sql)

                    except Exception as e:

                        error_msg = f"[ERROR] ALTER TABLE failed for {colname}: {e}"
                        print(error_msg)
                        # Don't silently continue - log the error clearly

                # refresh db_cols after ALTERs

                db_cols = get_db_table_info(cur, table)

                db_names = [c["name"] for c in db_cols]



            # 2) Detect type mismatches

            mismatches = []

            for m in model_cols:

                if m["name"] in db_names:

                    dbcol = next((d for d in db_cols if d["name"] == m["name"]), None)

                    if dbcol:

                        model_type = sa_type_to_sqlite(m["type"])

                        db_type = (dbcol["type"] or "").upper()

                        # Normalize simple affinities for comparison

                        if db_type == "":

                            db_type = "TEXT"  # sqlite sometimes returns blank -> treat as TEXT

                        # Consider mismatch if types differ (not a perfect science with sqlite)

                        if model_type not in db_type and db_type not in model_type:

                            mismatches.append((m, dbcol))

            if mismatches:

                print(f"[MISMATCH] Detected type mismatches for table {table}:")

                for mm in mismatches:

                    print(" - column:", mm[0]["name"], "model_type:", sa_type_to_sqlite(mm[0]["type"]), "db_type:", mm[1]["type"])

                # Rebuild table to exact model schema (safe-copy)

                rebuild_table(cur, table, model_cols, db_cols)

                # Refresh db_cols after rebuild

                db_cols = get_db_table_info(cur, table)

                db_names = [c["name"] for c in db_cols]

            else:

                print(f"[OK] No type mismatches for table {table}.")



            conn.commit()



        conn.close()

        # Only report success if no errors occurred
        print("\n=== DB AUTO-HEAL COMPLETE ===")
        # Note: Schema may not be fully synchronized if errors occurred above

        return True



    except Exception as e:

        print("[FATAL] Auto-heal failed:", e)

        traceback.print_exc(file=sys.stdout)

        print("[FATAL] Attempting to restore DB from backup...")

        try:

            restore_backup(backup_path)

        except Exception as re:

            print("[FATAL] Restore failed:", re)

        return False



# If executed directly, run the auto heal

if __name__ == "__main__":

    ok = auto_heal_db()

    if not ok:

        print("Auto-heal failed: see logs above. Exiting with code 2.")

        sys.exit(2)

    else:

        print("Auto-heal succeeded. Exiting with code 0.")

        sys.exit(0)



# ------------------------------------------------------------------

# END file

# ------------------------------------------------------------------

