#!/usr/bin/env python3
"""
openLCA Bridge — Connect Cortex to openLCA via IPC.

Requires:
  - openLCA 2.x running with IPC server enabled (Tools > Developer Tools > IPC Server)
  - Python 3.11+

Dependencies auto-installed on first run: olca-ipc, olca-schema

Usage:
  python olca_bridge.py ping                          — Test connection
  python olca_bridge.py databases                     — List available databases
  python olca_bridge.py processes [--search NAME]     — List/search processes
  python olca_bridge.py flows [--search NAME]         — List/search flows
  python olca_bridge.py methods                       — List LCIA methods
  python olca_bridge.py providers [--flow NAME]       — List technology providers
  python olca_bridge.py import-jsonld <zip_path>      — Import JSON-LD zip into openLCA
  python olca_bridge.py create-system <process_name>  — Create product system from process
  python olca_bridge.py calculate <system_or_process> --method <method_name> [--amount N]
  python olca_bridge.py result <result_id> impacts    — Get LCIA results
  python olca_bridge.py result <result_id> flows      — Get inventory flows
  python olca_bridge.py result <result_id> contributions <impact_name>  — Process contributions
  python olca_bridge.py result <result_id> dispose    — Release result resources
"""

import argparse
import json
import os
import subprocess
import sys

# ── Auto-install dependencies ──
try:
    import olca_ipc as ipc
    import olca_schema as o
    from olca_schema.zipio import ZipReader
except ImportError:
    print("[openLCA Bridge] Installing olca-ipc...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "olca-ipc"])
    import olca_ipc as ipc
    import olca_schema as o
    from olca_schema.zipio import ZipReader

# ── Connection ──

DEFAULT_PORT = int(os.environ.get("OPENLCA_IPC_PORT", "8080"))

def get_client(port=None):
    return ipc.Client(port or DEFAULT_PORT)


# ── Commands ──

def cmd_ping(args):
    """Test connection to openLCA IPC server."""
    try:
        client = get_client(args.port)
        # Try fetching descriptors to verify connection
        client.get_descriptors(o.Flow)
        print(json.dumps({"status": "connected", "port": args.port or DEFAULT_PORT}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        return 1
    return 0


def cmd_databases(args):
    """List processes to verify database is loaded."""
    try:
        client = get_client(args.port)
        process_count = len(list(client.get_descriptors(o.Process)))
        flow_count = len(list(client.get_descriptors(o.Flow)))
        method_count = len(list(client.get_descriptors(o.ImpactMethod)))
        print(json.dumps({
            "processes": process_count,
            "flows": flow_count,
            "impact_methods": method_count,
        }, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1
    return 0


def cmd_processes(args):
    """List or search processes."""
    client = get_client(args.port)
    descriptors = list(client.get_descriptors(o.Process))

    if args.search:
        query = args.search.lower()
        descriptors = [d for d in descriptors if query in (d.name or "").lower()]

    results = []
    for d in descriptors[:args.limit]:
        results.append({
            "id": d.id,
            "name": d.name,
            "category": d.category if hasattr(d, 'category') else None,
        })

    print(json.dumps({"count": len(descriptors), "showing": len(results), "processes": results}, indent=2))
    return 0


def cmd_flows(args):
    """List or search flows."""
    client = get_client(args.port)
    descriptors = list(client.get_descriptors(o.Flow))

    if args.search:
        query = args.search.lower()
        descriptors = [d for d in descriptors if query in (d.name or "").lower()]

    results = []
    for d in descriptors[:args.limit]:
        results.append({
            "id": d.id,
            "name": d.name,
            "flow_type": str(d.flow_type) if hasattr(d, 'flow_type') else None,
        })

    print(json.dumps({"count": len(descriptors), "showing": len(results), "flows": results}, indent=2))
    return 0


def cmd_methods(args):
    """List available LCIA methods."""
    client = get_client(args.port)
    descriptors = list(client.get_descriptors(o.ImpactMethod))

    results = []
    for d in descriptors:
        results.append({"id": d.id, "name": d.name})

    print(json.dumps({"count": len(results), "methods": results}, indent=2))
    return 0


def cmd_providers(args):
    """List technology providers (optionally for a specific flow)."""
    client = get_client(args.port)

    flow_ref = None
    if args.flow:
        flow_ref = client.find(o.Flow, args.flow)
        if not flow_ref:
            print(json.dumps({"error": f"Flow not found: {args.flow}"}))
            return 1

    providers = list(client.get_providers(flow=flow_ref))
    results = []
    for p in providers[:args.limit]:
        results.append({
            "process": p.process.name if p.process else None,
            "flow": p.flow.name if p.flow else None,
        })

    print(json.dumps({"count": len(providers), "showing": len(results), "providers": results}, indent=2))
    return 0


def cmd_import_jsonld(args):
    """Import a JSON-LD zip into the running openLCA database."""
    client = get_client(args.port)
    zip_path = args.zip_path

    if not os.path.isfile(zip_path):
        print(json.dumps({"error": f"File not found: {zip_path}"}))
        return 1

    try:
        reader = ZipReader(zip_path)
        imported = {"processes": 0, "flows": 0, "flow_properties": 0, "unit_groups": 0, "others": 0}

        # Import in dependency order: unit_groups → flow_properties → flows → processes
        for entity_type, key in [
            (o.UnitGroup, "unit_groups"),
            (o.FlowProperty, "flow_properties"),
            (o.Flow, "flows"),
            (o.Process, "processes"),
        ]:
            for entity in reader.read_each(entity_type):
                try:
                    client.put(entity)
                    imported[key] += 1
                except Exception as e:
                    print(f"Warning: failed to import {entity_type.__name__} {getattr(entity, 'name', '?')}: {e}", file=sys.stderr)

        # Also try sources, actors, impact categories, impact methods
        # ImpactMethod must come AFTER ImpactCategory (reference dependency)
        for entity_type in [o.Source, o.Actor, o.ImpactCategory, o.ImpactMethod]:
            for entity in reader.read_each(entity_type):
                try:
                    client.put(entity)
                    imported["others"] += 1
                except Exception:
                    pass

        reader.close()
        total = sum(imported.values())
        print(json.dumps({"status": "success", "total_imported": total, "details": imported}, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1
    return 0


def cmd_create_system(args):
    """Create a product system from a process."""
    client = get_client(args.port)

    process_ref = client.find(o.Process, args.process_name)
    if not process_ref:
        print(json.dumps({"error": f"Process not found: {args.process_name}"}))
        return 1

    try:
        config = o.LinkingConfig(
            prefer_unit_processes=args.prefer_unit,
            provider_linking=o.ProviderLinking.PREFER_DEFAULTS,
        )
        system_ref = client.create_product_system(process_ref, config=config)
        print(json.dumps({
            "status": "created",
            "product_system": {"id": system_ref.id, "name": system_ref.name},
        }, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1
    return 0


def cmd_calculate(args):
    """Run LCIA calculation."""
    client = get_client(args.port)

    # Find target (product system or process)
    target_ref = client.find(o.ProductSystem, args.target)
    if not target_ref:
        # Try as process, auto-create system
        process_ref = client.find(o.Process, args.target)
        if not process_ref:
            print(json.dumps({"error": f"Not found: {args.target}"}))
            return 1
        print(f"Creating product system from process: {process_ref.name}...", file=sys.stderr)
        target_ref = client.create_product_system(process_ref)

    # Find LCIA method
    method_ref = client.find(o.ImpactMethod, args.method)
    if not method_ref:
        print(json.dumps({"error": f"LCIA method not found: {args.method}"}))
        return 1

    try:
        setup = o.CalculationSetup(
            target=target_ref,
            impact_method=method_ref,
            amount=args.amount,
        )
        result = client.calculate(setup)
        result.wait_until_ready()

        # Get total impacts
        impacts = []
        for impact in result.get_total_impacts():
            cat = impact.impact_category
            impacts.append({
                "category": cat.name if cat else "?",
                "value": round(impact.amount, 6),
                "unit": cat.ref_unit if cat else "",
            })

        # Get demand info
        demand = result.get_demand()

        result_id = id(result)
        # Store result for follow-up queries
        _results[result_id] = result

        print(json.dumps({
            "status": "calculated",
            "result_id": result_id,
            "target": target_ref.name,
            "method": method_ref.name,
            "amount": args.amount,
            "demand": {
                "flow": demand.envi_flow.flow.name if demand and demand.envi_flow else None,
                "amount": demand.amount if demand else None,
            } if demand else None,
            "total_impacts": impacts,
        }, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1
    return 0


def cmd_result(args):
    """Query a calculation result."""
    result = _results.get(args.result_id)
    if not result:
        print(json.dumps({"error": f"Result {args.result_id} not found. Run calculate first."}))
        return 1

    if args.subcmd == "impacts":
        impacts = []
        for impact in result.get_total_impacts():
            cat = impact.impact_category
            impacts.append({
                "category": cat.name if cat else "?",
                "value": round(impact.amount, 6),
                "unit": cat.ref_unit if cat else "",
            })
        print(json.dumps({"impacts": impacts}, indent=2))

    elif args.subcmd == "flows":
        flows = []
        for fv in result.get_total_flows():
            ef = fv.envi_flow
            flows.append({
                "flow": ef.flow.name if ef and ef.flow else "?",
                "is_input": ef.is_input if ef else None,
                "value": round(fv.amount, 6),
            })
        # Sort by absolute value, show top 20
        flows.sort(key=lambda x: abs(x["value"]), reverse=True)
        print(json.dumps({"flows": flows[:20], "total": len(flows)}, indent=2))

    elif args.subcmd == "contributions":
        if not args.impact_name:
            print(json.dumps({"error": "Specify impact category name"}))
            return 1
        # Find impact category
        impact_ref = None
        for cat in result.get_impact_categories():
            if args.impact_name.lower() in (cat.name or "").lower():
                impact_ref = cat
                break
        if not impact_ref:
            print(json.dumps({"error": f"Impact category not found: {args.impact_name}"}))
            return 1

        contribs = []
        for item in result.get_impact_contributions_of(impact_ref):
            tf = item.tech_flow
            contribs.append({
                "process": tf.process.name if tf and tf.process else "?",
                "value": round(item.amount, 6),
                "share": round(item.share * 100, 2) if hasattr(item, 'share') else None,
            })
        contribs.sort(key=lambda x: abs(x["value"]), reverse=True)
        print(json.dumps({
            "impact_category": impact_ref.name,
            "contributions": contribs[:20],
            "total": len(contribs),
        }, indent=2))

    elif args.subcmd == "dispose":
        result.dispose()
        del _results[args.result_id]
        print(json.dumps({"status": "disposed"}))

    return 0


# ── Result storage (in-memory for single session) ──
_results = {}


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(description="openLCA Bridge — Connect Cortex to openLCA via IPC")
    parser.add_argument("--port", type=int, default=None, help=f"IPC port (default: {DEFAULT_PORT}, or OPENLCA_IPC_PORT env)")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("ping", help="Test connection")
    sub.add_parser("databases", help="Show database statistics")

    p_proc = sub.add_parser("processes", help="List/search processes")
    p_proc.add_argument("--search", "-s", help="Search by name")
    p_proc.add_argument("--limit", "-n", type=int, default=50)

    p_flow = sub.add_parser("flows", help="List/search flows")
    p_flow.add_argument("--search", "-s", help="Search by name")
    p_flow.add_argument("--limit", "-n", type=int, default=50)

    sub.add_parser("methods", help="List LCIA methods")

    p_prov = sub.add_parser("providers", help="List technology providers")
    p_prov.add_argument("--flow", "-f", help="Filter by flow name")
    p_prov.add_argument("--limit", "-n", type=int, default=50)

    p_imp = sub.add_parser("import-jsonld", help="Import JSON-LD zip into openLCA")
    p_imp.add_argument("zip_path", help="Path to JSON-LD zip file")

    p_sys = sub.add_parser("create-system", help="Create product system from process")
    p_sys.add_argument("process_name", help="Process name")
    p_sys.add_argument("--prefer-unit", action="store_true", help="Prefer unit processes over system processes")

    p_calc = sub.add_parser("calculate", help="Run LCIA calculation")
    p_calc.add_argument("target", help="Product system or process name")
    p_calc.add_argument("--method", "-m", required=True, help="LCIA method name")
    p_calc.add_argument("--amount", "-a", type=float, default=1.0, help="Functional unit amount")

    p_res = sub.add_parser("result", help="Query calculation result")
    p_res.add_argument("result_id", type=int, help="Result ID from calculate command")
    p_res.add_argument("subcmd", choices=["impacts", "flows", "contributions", "dispose"])
    p_res.add_argument("impact_name", nargs="?", help="Impact category name (for contributions)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    cmd_map = {
        "ping": cmd_ping,
        "databases": cmd_databases,
        "processes": cmd_processes,
        "flows": cmd_flows,
        "methods": cmd_methods,
        "providers": cmd_providers,
        "import-jsonld": cmd_import_jsonld,
        "create-system": cmd_create_system,
        "calculate": cmd_calculate,
        "result": cmd_result,
    }

    return cmd_map[args.command](args) or 0


if __name__ == "__main__":
    sys.exit(main())
