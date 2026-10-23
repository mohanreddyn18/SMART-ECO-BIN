#!/usr/bin/env python3
"""
SMART ECO BIN — Migration Utility: Local JSON to Google Cloud Firestore

Usage:
    # 1. Preview migration without writing anything:
    python migrate_to_firestore.py --dry-run

    # 2. Execute migration with confirmation:
    python migrate_to_firestore.py --confirm

    # 3. Specify custom source file:
    python migrate_to_firestore.py --source data/custom_records.json --dry-run
"""

import os
import sys
import argparse
import json

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.services.storage_service import create_storage_provider
from app.services.migration_service import MigrationService


def main():
    parser = argparse.ArgumentParser(
        description="Migrates local classification_records.json into Google Cloud Firestore idempotently."
    )
    parser.add_argument(
        "--source",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "classification_records.json"),
        help="Path to the source classification_records.json file."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the migration without writing any documents to Firestore."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Acknowledge and confirm live write to target storage provider."
    )

    args = parser.parse_args()

    print("=" * 70)
    print(" SMART ECO BIN — Local JSON to Firestore Migration Tool")
    print("=" * 70)

    if not args.dry_run and not args.confirm:
        print("\n[SAFETY NOTICE]")
        print("To protect your data, live migration requires explicit confirmation.")
        print("Run with `--dry-run` to preview the migration, or `--confirm` to execute live writes.\n")
        print(f"Example:")
        print(f"  python migrate_to_firestore.py --dry-run")
        print(f"  python migrate_to_firestore.py --confirm")
        sys.exit(1)

    # Initialize target provider
    try:
        target_provider = create_storage_provider()
    except Exception as e:
        print(f"\n[ERROR] Could not initialize target storage provider: {e}")
        print("Ensure STORAGE_PROVIDER=firestore and Google Cloud ADC is configured.\n")
        sys.exit(1)

    status = target_provider.get_status()
    print(f"Target Storage Mode:     {status['mode']}")
    print(f"Target Storage Backend:  {status['storage_backend']}")
    print(f"Cloud Provider:          {status['cloud_provider']}")
    print(f"Target Collection:       {status.get('collection', 'N/A')}")
    print(f"Source JSON File:        {args.source}")
    print(f"Dry Run Simulation:      {args.dry_run}")
    print("-" * 70)

    migration = MigrationService(target_provider=target_provider)
    result = migration.migrate_from_file(args.source, dry_run=args.dry_run)

    print("\n" + "=" * 70)
    print(" MIGRATION REPORT SUMMARY")
    print("=" * 70)
    print(f"Total Records Found:     {result['total_found']}")
    print(f"Successfully Imported:   {result['imported']}{' (Simulated)' if args.dry_run else ''}")
    print(f"Skipped (Already Exist): {result['skipped']}")
    print(f"Failed / Malformed:      {result['failed']}")

    if result["errors"]:
        print("\nEncountered Errors / Warnings:")
        for err in result["errors"][:10]:
            print(f"  - Record [{err['id']}]: {err['error']}")
        if len(result["errors"]) > 10:
            print(f"  ... and {len(result['errors']) - 10} more errors.")

    print("\n" + ("=" * 70))
    if args.dry_run:
        print("[SUCCESS] Dry-run preview completed. No changes were made to Firestore.")
    elif result["failed"] == 0:
        print("[SUCCESS] Live migration completed successfully! All records verified.")
    else:
        print("[COMPLETED WITH WARNINGS] Some records failed validation. See report above.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
