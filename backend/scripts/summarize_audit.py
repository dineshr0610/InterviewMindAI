import json
import os

with open("reports/database_dataset_forensic_audit_raw.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("--- TABLES ---")
for tbl, info in d["schema_inventory"].items():
    print(f"{tbl}: {info['row_count']} rows, {len(info['columns'])} cols, PK: {info['primary_key']}, FKs: {len(info['foreign_keys'])}, RLS: {info['rls_enabled']}")
    for col in info["columns"]:
        print(f"   col: {col['column_name']} ({col['data_type']}/{col['udt_name']}) nullable={col['is_nullable']} def={col['column_default']}")
    for fk in info["foreign_keys"]:
        print(f"   fk: {fk['column_name']} -> {fk['foreign_table_name']}({fk['foreign_column_name']}) on_del={fk['delete_rule']}")
    for idx in info["indexes"]:
        print(f"   idx: {idx['indexname']} def={idx['indexdef']}")
    for pol in info["rls_policies"]:
        print(f"   policy: {pol['policyname']} ({pol['cmd']})")

print("\n--- RPCS ---")
for rpc in d["rpcs"]:
    print(rpc["proname"])

print("\n--- DOC EMBEDDINGS SUMMARY ---")
de = d["document_embeddings_audit"]
print(f"Total: {de['total_rows']}, Populated: {de['populated_embeddings']}, Null: {de['null_embeddings']}, Dims: {de['dimensions']}")
print(f"Status: {de['status']}")
print(f"Metadata keys: {de['metadata_hygiene']['distinct_keys']}")
print(f"Syntax: {de['syntax']}")
print(f"Lengths Words: {de['content_length_stats_words']}")
print(f"Classifications: {de['classification_breakdown']}")
print(f"Duplicates exact: {de['duplicates']['exact_duplicate_groups']} groups, {de['duplicates']['exact_duplicate_records']} records")
print(f"Duplicates norm: {de['duplicates']['normalized_duplicate_groups']} groups, {de['duplicates']['normalized_duplicate_records']} records")
