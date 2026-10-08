import json

with open("reports/database_dataset_forensic_audit_raw.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("=== RLS POLICIES ===")
for tbl, info in d["schema_inventory"].items():
    print(f"Table: {tbl} (RLS enabled: {info['rls_enabled']}, RLS forced: {info['rls_forced']})")
    for pol in info["rls_policies"]:
        print(f"  - Policy: {pol['policyname']}, cmd: {pol['cmd']}, roles: {pol['roles']}, qual: {pol['qual']}")

print("\n=== RPCS ===")
for rpc in d["rpcs"]:
    print(f"RPC Name: {rpc['proname']}")
    print(rpc["def"])
    print("-" * 50)
