#!/usr/bin/env python3
"""
LCA Format Validator — Parse, validate, and convert ILCD/JSON-LD/TIDAS data packages.

Supports: ILCD XML (.zip), openLCA JSON-LD (.zip), LCA JSON (directory).
Dependencies: jsonschema (auto-installed if missing) for full schema validation.

Usage:
  python lca_toolkit.py parse   <path>              — Parse and summarize a data package
  python lca_toolkit.py validate <path>             — Validate structure and generate report
  python lca_toolkit.py convert  <path> --to json    — Convert ILCD XML → JSON (raw)
  python lca_toolkit.py convert  <path> --to jsonld  — Convert ILCD XML → openLCA JSON-LD
  python lca_toolkit.py convert  <path> --to ilcd    — Convert openLCA JSON-LD → ILCD XML
"""

import argparse
import json
import os
import re
import subprocess
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# ── Auto-install jsonschema if missing ──
try:
    from jsonschema import Draft7Validator
    from referencing import Registry
    from referencing.jsonschema import DRAFT7
    HAS_JSONSCHEMA = True
except ImportError:
    print("[LCA Toolkit] Installing jsonschema...", file=sys.stderr)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "jsonschema", "referencing"])
    try:
        from jsonschema import Draft7Validator
        from referencing import Registry
        from referencing.jsonschema import DRAFT7
        HAS_JSONSCHEMA = True
    except ImportError:
        HAS_JSONSCHEMA = False
        print("[LCA Toolkit] Warning: jsonschema not available, using structural validation only", file=sys.stderr)

SCHEMAS_DIR = os.path.join(os.path.dirname(__file__), "schemas")

# ── Constants ──

ILCD_CATEGORIES = {
    "processes": "processDataSet",
    "flows": "flowDataSet",
    "flowproperties": "flowPropertyDataSet",
    "unitgroups": "unitGroupDataSet",
    "sources": "sourceDataSet",
    "contacts": "contactDataSet",
    "lciamethods": "LCIAMethodDataSet",
}

ILCD_NS = {
    "process": "http://lca.jrc.it/ILCD/Process",
    "flow": "http://lca.jrc.it/ILCD/Flow",
    "flowproperty": "http://lca.jrc.it/ILCD/FlowProperty",
    "unitgroup": "http://lca.jrc.it/ILCD/UnitGroup",
    "source": "http://lca.jrc.it/ILCD/Source",
    "contact": "http://lca.jrc.it/ILCD/Contact",
    "lcia": "http://lca.jrc.it/ILCD/LCIAMethod",
    "common": "http://lca.jrc.it/ILCD/Common",
}

JSONLD_TYPES = {
    "processes": "Process",
    "flows": "Flow",
    "flow_properties": "FlowProperty",
    "unit_groups": "UnitGroup",
    "lcia_categories": "ImpactCategory",
    "lcia_methods": "ImpactMethod",
    "actors": "Actor",
    "sources": "Source",
    "locations": "Location",
}

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
CHINESE_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")


# ── Detection ──

def detect_format(path):
    """Detect if path is ILCD zip, JSON-LD zip, TIDAS dir, or unknown."""
    if os.path.isdir(path):
        # Check for TIDAS/JSON directory structure
        for cat in ["processes", "flows", "unitgroups", "flowproperties"]:
            if os.path.isdir(os.path.join(path, cat)):
                return "lca-json-dir"
        # Check for ILCD directory structure
        if os.path.isdir(os.path.join(path, "ILCD")):
            return "ilcd-dir"
        return "unknown-dir"

    if not zipfile.is_zipfile(path):
        return "unknown"

    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        # JSON-LD: has olca-schema.json or processes/*.json
        if any(n.endswith("olca-schema.json") for n in names):
            return "jsonld-zip"
        if any(n.startswith("processes/") and n.endswith(".json") for n in names):
            return "jsonld-zip"
        # ILCD: has ILCD/ prefix or processes/*.xml
        if any(n.startswith("ILCD/") for n in names):
            return "ilcd-zip"
        if any(n.endswith(".xml") for n in names):
            return "ilcd-zip"
        if any(n.endswith(".json") for n in names):
            return "lca-json-zip"

    return "unknown"


# ── ILCD XML Parsing ──

def _find_text(elem, xpath, ns=ILCD_NS):
    """Find text at xpath with namespace support."""
    node = elem.find(xpath, ns)
    return node.text.strip() if node is not None and node.text else ""

def _find_all_text(elem, xpath, ns=ILCD_NS):
    """Find all matching nodes and return their text."""
    return [n.text.strip() for n in elem.findall(xpath, ns) if n.text]

def parse_ilcd_process_xml(xml_content):
    """Parse a single ILCD process XML and extract summary info."""
    root = ET.fromstring(xml_content)
    ns = ILCD_NS
    info = {}

    # UUID
    info["uuid"] = _find_text(root, ".//common:UUID", ns)

    # Name (try multiple paths)
    name = _find_text(root, ".//process:processInformation/process:dataSetInformation/process:name/process:baseName", ns)
    if not name:
        name = _find_text(root, ".//{http://lca.jrc.it/ILCD/Process}name/{http://lca.jrc.it/ILCD/Process}baseName")
    # Fallback: try without namespace
    if not name:
        for elem in root.iter():
            if elem.tag.endswith("}baseName") or elem.tag == "baseName":
                if elem.text:
                    name = elem.text.strip()
                    break
    info["name"] = name

    # Geography
    info["location"] = ""
    for elem in root.iter():
        if "locationOfOperationSupplyOrProduction" in elem.tag:
            info["location"] = elem.get("location", "")
            break

    # Time
    info["reference_year"] = ""
    for elem in root.iter():
        if elem.tag.endswith("}referenceYear") or elem.tag == "referenceYear":
            if elem.text:
                info["reference_year"] = elem.text.strip()
                break

    # Exchanges
    exchanges = []
    for elem in root.iter():
        if "exchange" in elem.tag.lower() and elem.tag.endswith("}exchange"):
            exc = {
                "direction": "",
                "amount": "",
                "flow_name": "",
                "internal_id": elem.get("dataSetInternalID", ""),
            }
            for child in elem.iter():
                if child.tag.endswith("}exchangeDirection"):
                    exc["direction"] = child.text or ""
                elif child.tag.endswith("}meanAmount") or child.tag.endswith("}resultingAmount"):
                    if not exc["amount"] and child.text:
                        exc["amount"] = child.text
                elif child.tag.endswith("}shortDescription"):
                    if not exc["flow_name"] and child.text:
                        exc["flow_name"] = child.text.strip()
            exchanges.append(exc)
    info["exchanges"] = exchanges
    info["exchange_count"] = len(exchanges)

    return info

def parse_ilcd_flow_xml(xml_content):
    """Parse a single ILCD flow XML."""
    root = ET.fromstring(xml_content)
    info = {"uuid": "", "name": "", "flow_type": "", "cas": ""}

    for elem in root.iter():
        if elem.tag.endswith("}UUID") and not info["uuid"]:
            info["uuid"] = (elem.text or "").strip()
        elif elem.tag.endswith("}baseName") and not info["name"]:
            info["name"] = (elem.text or "").strip()
        elif elem.tag.endswith("}typeOfDataSet") and not info["flow_type"]:
            info["flow_type"] = (elem.text or "").strip()
        elif elem.tag.endswith("}CASNumber") and not info["cas"]:
            info["cas"] = (elem.text or "").strip()

    return info


# ── JSON-LD Parsing ──

def parse_jsonld_process(data):
    """Parse an openLCA JSON-LD process."""
    info = {
        "uuid": data.get("@id", ""),
        "name": data.get("name", ""),
        "location": "",
        "process_type": data.get("processType", ""),
        "exchanges": [],
        "exchange_count": 0,
    }

    loc = data.get("location")
    if isinstance(loc, dict):
        info["location"] = loc.get("name", loc.get("code", ""))

    for exc in data.get("exchanges", []):
        flow = exc.get("flow", {})
        unit = exc.get("unit", {})
        info["exchanges"].append({
            "direction": "Input" if exc.get("isInput") else "Output",
            "amount": str(exc.get("amount", "")),
            "flow_name": flow.get("name", "") if isinstance(flow, dict) else "",
            "unit": unit.get("name", "") if isinstance(unit, dict) else "",
            "is_quantitative_reference": exc.get("isQuantitativeReference", False),
        })
    info["exchange_count"] = len(info["exchanges"])
    return info

def parse_jsonld_flow(data):
    """Parse an openLCA JSON-LD flow."""
    return {
        "uuid": data.get("@id", ""),
        "name": data.get("name", ""),
        "flow_type": data.get("flowType", ""),
        "cas": data.get("cas", ""),
    }


# ── LCA JSON Parsing ──

def parse_lca_json_process(data):
    """Parse a LCA JSON process dataset."""
    pds = data.get("processDataSet", data)
    info_block = pds.get("processInformation", {}).get("dataSetInformation", {})

    uuid_val = ""
    common_uuid = info_block.get("common:UUID", info_block.get("UUID", ""))
    if common_uuid:
        uuid_val = common_uuid

    name = ""
    name_block = info_block.get("name", {})
    if isinstance(name_block, dict):
        base_name = name_block.get("baseName", "")
        if isinstance(base_name, list):
            for item in base_name:
                if isinstance(item, dict):
                    name = item.get("#text", "")
                    break
        elif isinstance(base_name, dict):
            name = base_name.get("#text", str(base_name))
        else:
            name = str(base_name)

    exchanges = pds.get("exchanges", {}).get("exchange", [])
    if isinstance(exchanges, dict):
        exchanges = [exchanges]

    return {
        "uuid": uuid_val,
        "name": name,
        "exchange_count": len(exchanges),
    }


# ── Main Parse Command ──

def cmd_parse(path):
    """Parse a data package and print summary."""
    fmt = detect_format(path)
    print(f"# LCA Data Package Summary\n")
    print(f"- **Path**: `{path}`")
    print(f"- **Format**: {fmt}")
    print(f"- **Generated**: {datetime.now().isoformat()[:19]}")
    print()

    if fmt == "ilcd-zip":
        _parse_ilcd_zip(path)
    elif fmt == "jsonld-zip":
        _parse_jsonld_zip(path)
    elif fmt in ("lca-json-dir", "lca-json-zip"):
        _parse_lca_json(path, fmt)
    elif fmt == "ilcd-dir":
        _parse_ilcd_dir(path)
    else:
        print(f"Unknown format. Cannot parse.")
        return 1
    return 0

def _parse_ilcd_zip(path):
    with zipfile.ZipFile(path) as zf:
        categories = {}
        for name in zf.namelist():
            if name.endswith(".xml"):
                parts = name.replace("ILCD/", "").split("/")
                if len(parts) >= 2:
                    cat = parts[0]
                    categories.setdefault(cat, []).append(name)

        print(f"## Categories\n")
        for cat, files in sorted(categories.items()):
            print(f"### {cat} ({len(files)} datasets)\n")
            if cat == "processes":
                for f in files[:20]:
                    try:
                        content = zf.read(f).decode("utf-8")
                        info = parse_ilcd_process_xml(content)
                        loc = f" [{info['location']}]" if info["location"] else ""
                        year = f" ({info['reference_year']})" if info["reference_year"] else ""
                        print(f"- **{info['name']}**{loc}{year} — {info['exchange_count']} exchanges — `{info['uuid'][:8]}...`")
                    except Exception as e:
                        print(f"- {f}: parse error ({e})")
                if len(files) > 20:
                    print(f"- ... and {len(files) - 20} more")
            elif cat == "flows":
                for f in files[:20]:
                    try:
                        content = zf.read(f).decode("utf-8")
                        info = parse_ilcd_flow_xml(content)
                        ftype = f" ({info['flow_type']})" if info["flow_type"] else ""
                        cas = f" CAS:{info['cas']}" if info["cas"] else ""
                        print(f"- {info['name']}{ftype}{cas}")
                    except Exception as e:
                        print(f"- {f}: parse error ({e})")
                if len(files) > 20:
                    print(f"- ... and {len(files) - 20} more")
            else:
                for f in files[:10]:
                    print(f"- `{os.path.basename(f)}`")
                if len(files) > 10:
                    print(f"- ... and {len(files) - 10} more")
            print()

def _parse_ilcd_dir(path):
    ilcd_path = os.path.join(path, "ILCD")
    if not os.path.isdir(ilcd_path):
        ilcd_path = path
    # Reuse zip logic by treating as directory
    print("## Categories\n")
    for cat in sorted(os.listdir(ilcd_path)):
        cat_path = os.path.join(ilcd_path, cat)
        if not os.path.isdir(cat_path):
            continue
        files = [f for f in os.listdir(cat_path) if f.endswith(".xml")]
        print(f"### {cat} ({len(files)} datasets)\n")
        for f in files[:10]:
            print(f"- `{f}`")
        if len(files) > 10:
            print(f"- ... and {len(files) - 10} more")
        print()

def _parse_jsonld_zip(path):
    with zipfile.ZipFile(path) as zf:
        categories = {}
        for name in zf.namelist():
            if name.endswith(".json") and "/" in name:
                cat = name.split("/")[0]
                if cat != "olca-schema.json":
                    categories.setdefault(cat, []).append(name)

        print(f"## Categories\n")
        for cat, files in sorted(categories.items()):
            print(f"### {cat} ({len(files)} datasets)\n")
            if cat == "processes":
                for f in files[:20]:
                    try:
                        data = json.loads(zf.read(f))
                        info = parse_jsonld_process(data)
                        loc = f" [{info['location']}]" if info["location"] else ""
                        print(f"- **{info['name']}**{loc} — {info['exchange_count']} exchanges — `{info['uuid'][:8]}...`")
                    except Exception as e:
                        print(f"- {f}: parse error ({e})")
                if len(files) > 20:
                    print(f"- ... and {len(files) - 20} more")
            elif cat == "flows":
                for f in files[:20]:
                    try:
                        data = json.loads(zf.read(f))
                        info = parse_jsonld_flow(data)
                        ftype = f" ({info['flow_type']})" if info["flow_type"] else ""
                        print(f"- {info['name']}{ftype}")
                    except Exception as e:
                        print(f"- {f}: parse error ({e})")
                if len(files) > 20:
                    print(f"- ... and {len(files) - 20} more")
            else:
                for f in files[:10]:
                    print(f"- `{os.path.basename(f)}`")
                if len(files) > 10:
                    print(f"- ... and {len(files) - 10} more")
            print()

def _parse_lca_json(path, fmt):
    import tempfile, shutil
    tmpdir = None
    if fmt == "lca-json-zip":
        tmpdir = tempfile.mkdtemp()
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmpdir)
        path = tmpdir
    try:
        _parse_lca_json_inner(path)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)

def _parse_lca_json_inner(path):

    print("## Categories\n")
    for cat in sorted(os.listdir(path)):
        cat_path = os.path.join(path, cat)
        if not os.path.isdir(cat_path):
            continue
        files = [f for f in os.listdir(cat_path) if f.endswith(".json")]
        if not files:
            continue
        print(f"### {cat} ({len(files)} datasets)\n")
        if cat == "processes":
            for f in files[:20]:
                try:
                    with open(os.path.join(cat_path, f)) as fh:
                        data = json.load(fh)
                    info = parse_lca_json_process(data)
                    print(f"- **{info['name']}** — {info['exchange_count']} exchanges — `{info['uuid'][:8]}...`")
                except Exception as e:
                    print(f"- {f}: parse error ({e})")
            if len(files) > 20:
                print(f"- ... and {len(files) - 20} more")
        else:
            for f in files[:10]:
                print(f"- `{f}`")
            if len(files) > 10:
                print(f"- ... and {len(files) - 10} more")
        print()


# ── Validation ──

def cmd_validate(path):
    """Validate a data package and generate report."""
    fmt = detect_format(path)
    report = {
        "path": path,
        "format": fmt,
        "timestamp": datetime.now().isoformat()[:19],
        "ok": True,
        "categories": [],
        "issues": [],
    }

    if fmt == "ilcd-zip":
        _validate_ilcd_zip(path, report)
    elif fmt == "jsonld-zip":
        _validate_jsonld_zip(path, report)
    elif fmt in ("lca-json-dir", "lca-json-zip"):
        _validate_lca_json(path, fmt, report)
    else:
        report["ok"] = False
        report["issues"].append({"severity": "error", "message": f"Unknown format: {fmt}"})

    # Print Markdown report
    ok_str = "PASS ✅" if report["ok"] else "FAIL ❌"
    print(f"# LCA Data Validation Report\n")
    print(f"- **Path**: `{path}`")
    print(f"- **Format**: {fmt}")
    print(f"- **Result**: {ok_str}")
    print(f"- **Generated**: {report['timestamp']}")
    print()

    if report["categories"]:
        print(f"## Category Summary\n")
        print(f"| Category | Files | Errors | Status |")
        print(f"|----------|-------|--------|--------|")
        for cat in report["categories"]:
            status = "✅" if cat["error_count"] == 0 else "❌"
            print(f"| {cat['name']} | {cat['file_count']} | {cat['error_count']} | {status} |")
        print()

    if report["issues"]:
        print(f"## Issues ({len(report['issues'])})\n")
        for issue in report["issues"][:50]:
            sev = "🔴" if issue["severity"] == "error" else "🟡"
            file_str = f" in `{issue.get('file', '')}`" if issue.get("file") else ""
            print(f"- {sev} **{issue.get('code', 'issue')}**{file_str}: {issue['message']}")
        if len(report["issues"]) > 50:
            print(f"\n... and {len(report['issues']) - 50} more issues")
    else:
        print("No issues found. ✅")

    # Also save JSON report
    report_path = (path[:-4] if path.endswith(".zip") else path.rstrip("/")) + "_validation_report.json"
    try:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n---\n📄 JSON report saved to: `{report_path}`")
    except Exception:
        pass

    return 0 if report["ok"] else 1

def _add_issue(report, severity, code, message, file=""):
    report["issues"].append({"severity": severity, "code": code, "message": message, "file": file})
    if severity == "error":
        report["ok"] = False

def _validate_ilcd_zip(path, report):
    with zipfile.ZipFile(path) as zf:
        categories = {}
        for name in zf.namelist():
            if name.endswith(".xml"):
                parts = name.replace("ILCD/", "").split("/")
                if len(parts) >= 2:
                    categories.setdefault(parts[0], []).append(name)

        for cat, files in sorted(categories.items()):
            cat_report = {"name": cat, "file_count": len(files), "error_count": 0}

            for f in files:
                try:
                    content = zf.read(f).decode("utf-8")
                    root = ET.fromstring(content)

                    # Check UUID exists
                    uuid_found = False
                    for elem in root.iter():
                        if elem.tag.endswith("}UUID"):
                            if elem.text and UUID_RE.match(elem.text.strip()):
                                uuid_found = True
                            elif elem.text:
                                _add_issue(report, "error", "invalid_uuid", f"Invalid UUID format: {elem.text}", f)
                                cat_report["error_count"] += 1
                            break
                    if not uuid_found:
                        _add_issue(report, "error", "missing_uuid", "Missing or invalid UUID", f)
                        cat_report["error_count"] += 1

                    # Check process-specific fields
                    if cat == "processes":
                        info = parse_ilcd_process_xml(content)
                        if not info["name"]:
                            _add_issue(report, "error", "missing_name", "Process missing name/baseName", f)
                            cat_report["error_count"] += 1
                        if not info["exchanges"]:
                            _add_issue(report, "warning", "no_exchanges", "Process has no exchanges", f)
                        # Check exchange references
                        for exc in info["exchanges"]:
                            if not exc["direction"]:
                                _add_issue(report, "error", "missing_direction", f"Exchange missing direction (ID: {exc['internal_id']})", f)
                                cat_report["error_count"] += 1

                    # Check flow-specific fields
                    elif cat == "flows":
                        info = parse_ilcd_flow_xml(content)
                        if not info["name"]:
                            _add_issue(report, "error", "missing_name", "Flow missing name/baseName", f)
                            cat_report["error_count"] += 1
                        if not info["flow_type"]:
                            _add_issue(report, "warning", "missing_flow_type", "Flow missing typeOfDataSet", f)

                except ET.ParseError as e:
                    _add_issue(report, "error", "xml_parse_error", f"XML parse error: {e}", f)
                    cat_report["error_count"] += 1
                except Exception as e:
                    _add_issue(report, "error", "unexpected_error", f"Unexpected error: {e}", f)
                    cat_report["error_count"] += 1

            report["categories"].append(cat_report)

def _validate_jsonld_zip(path, report):
    with zipfile.ZipFile(path) as zf:
        # Check olca-schema.json
        has_schema = any(n.endswith("olca-schema.json") for n in zf.namelist())
        if not has_schema:
            _add_issue(report, "warning", "missing_schema_version", "Missing olca-schema.json (version metadata)")

        categories = {}
        for name in zf.namelist():
            if name.endswith(".json") and "/" in name:
                cat = name.split("/")[0]
                if cat not in (".", "olca-schema.json"):
                    categories.setdefault(cat, []).append(name)

        for cat, files in sorted(categories.items()):
            cat_report = {"name": cat, "file_count": len(files), "error_count": 0}

            for f in files:
                try:
                    data = json.loads(zf.read(f))

                    # Check @id
                    obj_id = data.get("@id", "")
                    if not obj_id:
                        _add_issue(report, "error", "missing_id", "Missing @id field", f)
                        cat_report["error_count"] += 1
                    elif not UUID_RE.match(obj_id):
                        _add_issue(report, "error", "invalid_id", f"Invalid @id UUID format: {obj_id}", f)
                        cat_report["error_count"] += 1

                    # Check @type
                    if "@type" not in data:
                        _add_issue(report, "warning", "missing_type", "Missing @type field", f)

                    # Check name
                    if not data.get("name"):
                        _add_issue(report, "error", "missing_name", "Missing name field", f)
                        cat_report["error_count"] += 1

                    # Process-specific
                    if cat == "processes":
                        exchanges = data.get("exchanges", [])
                        if not exchanges:
                            _add_issue(report, "warning", "no_exchanges", "Process has no exchanges", f)
                        has_qref = any(e.get("isQuantitativeReference") for e in exchanges)
                        if exchanges and not has_qref:
                            _add_issue(report, "error", "no_quantitative_reference", "No exchange marked as quantitative reference", f)
                            cat_report["error_count"] += 1
                        for i, exc in enumerate(exchanges):
                            if not exc.get("flow"):
                                _add_issue(report, "error", "exchange_missing_flow", f"Exchange {i} missing flow reference", f)
                                cat_report["error_count"] += 1

                    # Flow-specific
                    elif cat == "flows":
                        if not data.get("flowType"):
                            _add_issue(report, "warning", "missing_flow_type", "Flow missing flowType", f)

                except json.JSONDecodeError as e:
                    _add_issue(report, "error", "json_parse_error", f"JSON parse error: {e}", f)
                    cat_report["error_count"] += 1
                except Exception as e:
                    _add_issue(report, "error", "unexpected_error", f"Unexpected error: {e}", f)
                    cat_report["error_count"] += 1

            report["categories"].append(cat_report)

def _load_schema_validator(category):
    """Load JSON Schema validator for an LCA JSON category."""
    if not HAS_JSONSCHEMA:
        return None
    schema_file = os.path.join(SCHEMAS_DIR, f"lca_{category.lower()}.json")
    if not os.path.isfile(schema_file):
        return None
    try:
        with open(schema_file) as f:
            schema = json.load(f)
        # Build registry: pre-load all schema files for $ref resolution
        registry = Registry()
        for sf in os.listdir(SCHEMAS_DIR):
            if sf.endswith(".json"):
                sf_path = os.path.join(SCHEMAS_DIR, sf)
                with open(sf_path) as rf:
                    sf_data = json.load(rf)
                sf_uri = f"file://{sf_path}"
                registry = registry.with_resource(sf_uri, DRAFT7.create_resource(sf_data))
                # Also register by bare filename for relative $ref
                registry = registry.with_resource(sf, DRAFT7.create_resource(sf_data))
        schema_uri = f"file://{schema_file}"
        return Draft7Validator(schema, registry=registry, format_checker=None)
    except Exception as e:
        print(f"[LCA Toolkit] Schema load failed for {category}: {e}", file=sys.stderr)
        return None

def _validate_lca_json(path, fmt, report):
    import tempfile, shutil
    tmpdir = None
    if fmt == "lca-json-zip":
        tmpdir = tempfile.mkdtemp()
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmpdir)
        path = tmpdir
    try:
        _validate_lca_json_inner(path, report)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)

def _validate_lca_json_inner(path, report):
    for cat in sorted(os.listdir(path)):
        cat_path = os.path.join(path, cat)
        if not os.path.isdir(cat_path):
            continue
        files = [f for f in os.listdir(cat_path) if f.endswith(".json")]
        if not files:
            continue

        cat_report = {"name": cat, "file_count": len(files), "error_count": 0}
        validator = _load_schema_validator(cat)

        for f in files:
            fpath = os.path.join(cat_path, f)
            try:
                with open(fpath) as fh:
                    data = json.load(fh)

                # 1. JSON Schema validation (full Draft-7)
                if validator:
                    for err in validator.iter_errors(data):
                        loc = "/".join(str(p) for p in err.path) if err.path else "<root>"
                        _add_issue(report, "error", "schema_error",
                                   f"Schema error at {loc}: {err.message}", fpath)
                        cat_report["error_count"] += 1

                # 2. UUID filename vs content check
                file_uuid = f.replace(".json", "")
                if UUID_RE.match(file_uuid):
                    content_uuid = _extract_lca_json_uuid(data, cat)
                    if content_uuid and content_uuid != file_uuid:
                        _add_issue(report, "error", "uuid_mismatch",
                                   f"Filename UUID ({file_uuid}) != content UUID ({content_uuid})", fpath)
                        cat_report["error_count"] += 1

                # 3. Structural check (fallback if no schema)
                if not validator:
                    root_key = _get_lca_json_root_key(cat)
                    if root_key and root_key not in data:
                        _add_issue(report, "error", "missing_root_key",
                                   f"Missing root key '{root_key}'", fpath)
                        cat_report["error_count"] += 1

                # 4. Language validation
                lang_errors = _validate_language(data)
                for msg in lang_errors:
                    _add_issue(report, "error", "language_error", msg, fpath)
                    cat_report["error_count"] += 1

            except json.JSONDecodeError as e:
                _add_issue(report, "error", "json_parse_error", f"JSON parse error: {e}", fpath)
                cat_report["error_count"] += 1

        report["categories"].append(cat_report)

def _extract_lca_json_uuid(data, category):
    root_key = _get_lca_json_root_key(category)
    if not root_key or root_key not in data:
        return None
    ds = data[root_key]
    # Try common paths
    for path_parts in [
        ["processInformation", "dataSetInformation", "common:UUID"],
        ["flowInformation", "dataSetInformation", "common:UUID"],
        ["flowPropertiesInformation", "dataSetInformation", "common:UUID"],
        ["unitGroupInformation", "dataSetInformation", "common:UUID"],
        ["sourceInformation", "dataSetInformation", "common:UUID"],
        ["contactInformation", "dataSetInformation", "common:UUID"],
    ]:
        node = ds
        for key in path_parts:
            if isinstance(node, dict):
                node = node.get(key)
            else:
                node = None
                break
        if node and isinstance(node, str):
            return node
    return None

def _get_lca_json_root_key(category):
    mapping = {
        "processes": "processDataSet",
        "flows": "flowDataSet",
        "flowproperties": "flowPropertyDataSet",
        "unitgroups": "unitGroupDataSet",
        "sources": "sourceDataSet",
        "contacts": "contactDataSet",
        "lciamethods": "LCIAMethodDataSet",
        "lifecyclemodels": "lifecycleModelDataSet",
    }
    return mapping.get(category)

def _validate_language(node, path=""):
    """Validate zh/en language constraints for TIDAS format."""
    errors = []
    if isinstance(node, dict):
        lang = node.get("@xml:lang")
        text = node.get("#text")
        if isinstance(lang, str) and isinstance(text, str):
            has_chinese = bool(CHINESE_RE.search(text))
            lang_lower = lang.lower()
            if (lang_lower == "zh" or lang_lower.startswith("zh-")) and not has_chinese:
                errors.append(f"Language error at {path or '<root>'}: zh text must contain Chinese characters")
            elif (lang_lower == "en" or lang_lower.startswith("en-")) and has_chinese:
                errors.append(f"Language error at {path or '<root>'}: en text must not contain Chinese characters")
        for key, value in node.items():
            errors.extend(_validate_language(value, f"{path}/{key}" if path else key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            errors.extend(_validate_language(value, f"{path}[{i}]" if path else f"[{i}]"))
    return errors


# ── Conversion ──

def cmd_convert(path, to_format):
    """Convert between XML and JSON formats."""
    fmt = detect_format(path)
    print(f"# LCA Data Conversion\n")
    print(f"- **Source**: `{path}` ({fmt})")
    print(f"- **Target**: {to_format}")
    print()

    if fmt == "ilcd-zip" and to_format == "json":
        _convert_ilcd_to_json(path)
    elif fmt == "ilcd-zip" and to_format == "jsonld":
        _convert_ilcd_to_jsonld(path)
    elif fmt == "jsonld-zip" and to_format in ("xml", "ilcd"):
        _convert_jsonld_to_ilcd(path)
    else:
        print(f"Conversion from {fmt} to {to_format} is not supported.")
        print("Supported: ILCD XML → JSON, ILCD XML → JSON-LD, JSON-LD → ILCD XML")
        return 1
    return 0

def _convert_ilcd_to_json(path):
    output_dir = path.replace(".zip", "_json")
    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(path) as zf:
        count = 0
        for name in zf.namelist():
            if not name.endswith(".xml"):
                continue
            try:
                content = zf.read(name).decode("utf-8")
                root = ET.fromstring(content)
                json_data = _xml_to_dict(root)

                json_path = os.path.join(output_dir, name.replace(".xml", ".json"))
                os.makedirs(os.path.dirname(json_path), exist_ok=True)
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                count += 1
            except Exception as e:
                print(f"- ❌ {name}: {e}")

    print(f"Converted {count} files to `{output_dir}/`")


def _convert_ilcd_to_jsonld(path):
    """Convert ILCD XML zip to openLCA JSON-LD zip."""
    output_zip = (path[:-4] if path.endswith(".zip") else path) + "_jsonld.zip"
    counts = {}

    with zipfile.ZipFile(path) as zf_in, zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf_out:
        # Write olca-schema.json
        zf_out.writestr("olca-schema.json", json.dumps({"version": 2}))

        for name in sorted(zf_in.namelist()):
            if not name.endswith(".xml"):
                continue
            parts = name.replace("ILCD/", "").split("/")
            if len(parts) < 2:
                continue
            cat = parts[0]

            try:
                content = zf_in.read(name).decode("utf-8")
                root = ET.fromstring(content)
                jsonld_data = None
                jsonld_cat = None

                if cat == "processes":
                    jsonld_data = _ilcd_process_to_jsonld(root)
                    jsonld_cat = "processes"
                elif cat == "flows":
                    jsonld_data = _ilcd_flow_to_jsonld(root)
                    jsonld_cat = "flows"
                elif cat == "flowproperties":
                    jsonld_data = _ilcd_flowproperty_to_jsonld(root)
                    jsonld_cat = "flow_properties"
                elif cat == "unitgroups":
                    jsonld_data = _ilcd_unitgroup_to_jsonld(root)
                    jsonld_cat = "unit_groups"
                elif cat == "sources":
                    jsonld_data = _ilcd_source_to_jsonld(root)
                    jsonld_cat = "sources"
                elif cat == "contacts":
                    jsonld_data = _ilcd_contact_to_jsonld(root)
                    jsonld_cat = "actors"
                elif cat == "lciamethods":
                    jsonld_data = _ilcd_lcia_to_jsonld(root)
                    jsonld_cat = "lcia_categories"

                if jsonld_data and jsonld_cat:
                    uid = jsonld_data.get("@id", "unknown")
                    zf_out.writestr(f"{jsonld_cat}/{uid}.json",
                                    json.dumps(jsonld_data, indent=2, ensure_ascii=False))
                    counts[jsonld_cat] = counts.get(jsonld_cat, 0) + 1
            except Exception as e:
                print(f"- ❌ {name}: {e}")

    total = sum(counts.values())
    print(f"## Conversion Result\n")
    print(f"Output: `{output_zip}`\n")
    print(f"| Category | Files |")
    print(f"|----------|-------|")
    for cat, n in sorted(counts.items()):
        print(f"| {cat} | {n} |")
    print(f"| **Total** | **{total}** |")


# ── ILCD XML → JSON-LD field mappers ──

def _find_uuid(root):
    for elem in root.iter():
        if elem.tag.endswith("}UUID") and elem.text:
            return elem.text.strip()
    return ""

def _find_name(root, tag="baseName"):
    for elem in root.iter():
        if elem.tag.endswith(f"}}{tag}") and elem.text:
            return elem.text.strip()
    return ""

def _find_any(root, *suffixes):
    for elem in root.iter():
        for suffix in suffixes:
            if elem.tag.endswith(f"}}{suffix}") and elem.text:
                return elem.text.strip()
    return ""


def _ilcd_process_to_jsonld(root):
    """Convert ILCD process XML to openLCA JSON-LD Process."""
    result = {
        "@type": "Process",
        "@id": _find_uuid(root),
        "name": _find_name(root),
    }

    # processType
    type_text = _find_any(root, "typeOfDataSet")
    if "unit process" in type_text.lower():
        result["processType"] = "UNIT_PROCESS"
    else:
        result["processType"] = "LCI_RESULT"

    # location
    for elem in root.iter():
        if "locationOfOperationSupplyOrProduction" in elem.tag:
            loc_code = elem.get("location", "")
            if loc_code:
                result["location"] = {"@type": "Location", "code": loc_code, "name": loc_code}
            break

    # description
    desc = _find_any(root, "generalComment")
    if desc:
        result["description"] = desc

    # exchanges
    exchanges = []
    ref_flow_elem = None
    for elem in root.iter():
        if elem.tag.endswith("}referenceToReferenceFlow") and elem.text:
            ref_flow_elem = elem.text.strip()
            break

    for elem in root.iter():
        if not (elem.tag.endswith("}exchange") and elem.get("dataSetInternalID") is not None):
            continue
        internal_id = elem.get("dataSetInternalID", "")
        exc = {"@type": "Exchange", "internalId": int(internal_id) if internal_id.isdigit() else 0}

        for child in elem.iter():
            if child.tag.endswith("}exchangeDirection") and child.text:
                exc["isInput"] = child.text.strip().lower() == "input"
            elif child.tag.endswith("}meanAmount") and child.text:
                try:
                    exc["amount"] = float(child.text.strip())
                except ValueError:
                    exc["amount"] = 0
            elif child.tag.endswith("}referenceToFlowDataSet"):
                flow_id = child.get("refObjectId", "")
                flow_name = ""
                for desc_elem in child.iter():
                    if desc_elem.tag.endswith("}shortDescription") and desc_elem.text:
                        flow_name = desc_elem.text.strip()
                        break
                exc["flow"] = {"@type": "Flow", "@id": flow_id, "name": flow_name}

        exc["isQuantitativeReference"] = (internal_id == ref_flow_elem)
        exchanges.append(exc)

    result["exchanges"] = exchanges
    return result


def _ilcd_flow_to_jsonld(root):
    """Convert ILCD flow XML to openLCA JSON-LD Flow."""
    result = {
        "@type": "Flow",
        "@id": _find_uuid(root),
        "name": _find_name(root),
    }

    type_text = _find_any(root, "typeOfDataSet")
    type_map = {
        "product flow": "PRODUCT_FLOW",
        "elementary flow": "ELEMENTARY_FLOW",
        "waste flow": "WASTE_FLOW",
    }
    result["flowType"] = type_map.get(type_text.lower(), "PRODUCT_FLOW")

    cas = _find_any(root, "CASNumber")
    if cas:
        result["cas"] = cas

    # flowProperties
    fps = []
    for elem in root.iter():
        if elem.tag.endswith("}flowProperty") and elem.get("dataSetInternalID") is not None:
            fpf = {"@type": "FlowPropertyFactor"}
            for child in elem.iter():
                if child.tag.endswith("}referenceToFlowPropertyDataSet"):
                    fp_id = child.get("refObjectId", "")
                    fp_name = ""
                    for d in child.iter():
                        if d.tag.endswith("}shortDescription") and d.text:
                            fp_name = d.text.strip()
                            break
                    fpf["flowProperty"] = {"@type": "FlowProperty", "@id": fp_id, "name": fp_name}
                elif child.tag.endswith("}meanValue") and child.text:
                    try:
                        fpf["conversionFactor"] = float(child.text.strip())
                    except ValueError:
                        fpf["conversionFactor"] = 1.0
                elif child.tag.endswith("}referenceFlowProperty") and child.text:
                    fpf["referenceFlowProperty"] = child.text.strip().lower() == "true"
            fps.append(fpf)
    if fps:
        result["flowProperties"] = fps

    return result


def _ilcd_flowproperty_to_jsonld(root):
    """Convert ILCD FlowProperty XML to openLCA JSON-LD FlowProperty."""
    result = {
        "@type": "FlowProperty",
        "@id": _find_uuid(root),
        "name": _find_any(root, "name"),
    }
    for elem in root.iter():
        if elem.tag.endswith("}referenceToReferenceUnitGroup"):
            ug_id = elem.get("refObjectId", "")
            ug_name = ""
            for d in elem.iter():
                if d.tag.endswith("}shortDescription") and d.text:
                    ug_name = d.text.strip()
                    break
            result["unitGroup"] = {"@type": "UnitGroup", "@id": ug_id, "name": ug_name}
            break
    return result


def _ilcd_unitgroup_to_jsonld(root):
    """Convert ILCD UnitGroup XML to openLCA JSON-LD UnitGroup."""
    result = {
        "@type": "UnitGroup",
        "@id": _find_uuid(root),
        "name": _find_any(root, "name"),
    }

    ref_unit_id = None
    for elem in root.iter():
        if elem.tag.endswith("}referenceToReferenceUnit") and elem.text:
            ref_unit_id = elem.text.strip()
            break

    units = []
    for elem in root.iter():
        if elem.tag.endswith("}unit") and elem.get("dataSetInternalID") is not None:
            internal_id = elem.get("dataSetInternalID", "")
            unit = {"@type": "Unit"}
            for child in elem.iter():
                if child.tag.endswith("}name") and child.text:
                    unit["name"] = child.text.strip()
                elif child.tag.endswith("}meanValue") and child.text:
                    try:
                        unit["conversionFactor"] = float(child.text.strip())
                    except ValueError:
                        unit["conversionFactor"] = 1.0
            unit["referenceUnit"] = (internal_id == ref_unit_id)
            units.append(unit)
    result["units"] = units
    return result


def _ilcd_source_to_jsonld(root):
    """Convert ILCD Source XML to openLCA JSON-LD Source."""
    result = {
        "@type": "Source",
        "@id": _find_uuid(root),
        "name": _find_any(root, "shortName"),
    }
    url = _find_any(root, "sourceCitation")
    if url:
        result["url"] = url
    return result


def _ilcd_contact_to_jsonld(root):
    """Convert ILCD Contact XML to openLCA JSON-LD Actor."""
    result = {
        "@type": "Actor",
        "@id": _find_uuid(root),
        "name": _find_any(root, "name", "shortName"),
    }
    email = _find_any(root, "email")
    if email:
        result["email"] = email
    return result


def _ilcd_lcia_to_jsonld(root):
    """Convert ILCD LCIAMethodDataSet to openLCA JSON-LD ImpactCategory."""
    result = {
        "@type": "ImpactCategory",
        "@id": _find_uuid(root),
        "name": _find_any(root, "name"),
    }

    desc = _find_any(root, "generalComment")
    if desc:
        result["description"] = desc

    ref_unit = _find_any(root, "referenceQuantity")
    if ref_unit:
        result["referenceUnitName"] = ref_unit

    factors = []
    for elem in root.iter():
        if elem.tag.endswith("}factor"):
            f = {}
            for child in elem.iter():
                if child.tag.endswith("}referenceToFlowDataSet"):
                    flow_id = child.get("refObjectId", "")
                    flow_name = ""
                    for d in child.iter():
                        if d.tag.endswith("}shortDescription") and d.text:
                            flow_name = d.text.strip()
                            break
                    f["flow"] = {"@type": "Flow", "@id": flow_id, "name": flow_name}
                elif child.tag.endswith("}exchangeDirection") and child.text:
                    f["flowDirection"] = "INPUT" if child.text.strip().lower() == "input" else "OUTPUT"
                elif child.tag.endswith("}meanValue") and child.text:
                    try:
                        f["value"] = float(child.text.strip())
                    except ValueError:
                        f["value"] = 0
            if f:
                factors.append(f)
    if factors:
        result["impactFactors"] = factors

    return result


def _xml_to_dict(elem):
    """Convert XML element to dict (simplified xmltodict equivalent)."""
    result = {}

    # Attributes
    for key, val in elem.attrib.items():
        result[f"@{key}"] = val

    # Text
    text = (elem.text or "").strip()

    # Children
    children = {}
    for child in elem:
        tag = child.tag
        # Strip namespace for readability
        if "}" in tag:
            ns, local = tag.split("}", 1)
            ns = ns.lstrip("{")
            # Map common ILCD namespaces to prefixes
            for prefix, uri in ILCD_NS.items():
                if ns == uri:
                    tag = f"{prefix}:{local}" if prefix != "process" else local
                    break
        child_dict = _xml_to_dict(child)
        if tag in children:
            if not isinstance(children[tag], list):
                children[tag] = [children[tag]]
            children[tag].append(child_dict)
        else:
            children[tag] = child_dict

    if children:
        result.update(children)
        if text:
            result["#text"] = text
    elif text:
        if result:  # has attributes
            result["#text"] = text
        else:
            return text

    return result


# ── JSON-LD → ILCD XML Conversion ──

def _convert_jsonld_to_ilcd(path):
    """Convert openLCA JSON-LD zip to ILCD XML zip."""
    output_zip = (path[:-4] if path.endswith(".zip") else path) + "_ilcd.zip"
    counts = {"processes": 0, "flows": 0, "flowproperties": 0, "unitgroups": 0,
              "sources": 0, "contacts": 0, "lciamethods": 0}

    with zipfile.ZipFile(path) as zf_in, zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf_out:
        for name in sorted(zf_in.namelist()):
            if not name.endswith(".json") or "/" not in name:
                continue
            cat = name.split("/")[0]
            try:
                data = json.loads(zf_in.read(name))
            except Exception:
                continue

            xml_str = None
            ilcd_cat = None
            obj_type = data.get("@type", "")

            if cat == "processes" or obj_type == "Process":
                xml_str = _jsonld_process_to_ilcd(data)
                ilcd_cat = "processes"
            elif cat == "flows" or obj_type == "Flow":
                xml_str = _jsonld_flow_to_ilcd(data)
                ilcd_cat = "flows"
            elif cat in ("flow_properties", "flowproperties") or obj_type == "FlowProperty":
                xml_str = _jsonld_flowproperty_to_ilcd(data)
                ilcd_cat = "flowproperties"
            elif cat in ("unit_groups", "unitgroups") or obj_type == "UnitGroup":
                xml_str = _jsonld_unitgroup_to_ilcd(data)
                ilcd_cat = "unitgroups"
            elif cat == "sources" or obj_type == "Source":
                xml_str = _jsonld_source_to_ilcd(data)
                ilcd_cat = "sources"
            elif cat == "actors" or obj_type == "Actor":
                xml_str = _jsonld_actor_to_ilcd(data)
                ilcd_cat = "contacts"
            elif cat == "lcia_categories" or obj_type == "ImpactCategory":
                xml_str = _jsonld_impactcategory_to_ilcd(data)
                ilcd_cat = "lciamethods"
            elif cat == "lcia_methods" or obj_type == "ImpactMethod":
                # ImpactMethod is a container in JSON-LD; ILCD has no direct equivalent.
                # Individual ImpactCategories are already converted above.
                continue

            if xml_str and ilcd_cat:
                uid = data.get("@id", "unknown")
                xml_path = f"ILCD/{ilcd_cat}/{uid}.xml"
                zf_out.writestr(xml_path, xml_str)
                counts[ilcd_cat] = counts.get(ilcd_cat, 0) + 1

    total = sum(counts.values())
    print(f"## Conversion Result\n")
    print(f"Output: `{output_zip}`\n")
    print(f"| Category | Files |")
    print(f"|----------|-------|")
    for cat, n in counts.items():
        if n > 0:
            print(f"| {cat} | {n} |")
    print(f"| **Total** | **{total}** |")

    if total == 0:
        print("\n⚠️ No datasets converted. Check input format.")


def _xml_header(root_tag, ns_uri, extra_ns=""):
    """Generate XML declaration + root element opening."""
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<{root_tag} xmlns="{ns_uri}" xmlns:common="http://lca.jrc.it/ILCD/Common"{extra_ns} version="1.1">\n'

def _xml_footer(root_tag):
    return f'</{root_tag}>\n'

def _x(text):
    """Escape XML special characters."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def _lang_elem(tag, text, lang="en", indent=""):
    """Create a localized text element."""
    if not text:
        return ""
    return f'{indent}<{tag} xml:lang="{lang}">{_x(text)}</{tag}>\n'

def _ref_elem(tag, ref_type, ref_id, desc="", indent=""):
    """Create a reference element."""
    if not ref_id:
        return ""
    desc_xml = f'\n{indent}  <common:shortDescription xml:lang="en">{_x(desc)}</common:shortDescription>\n{indent}' if desc else ""
    return f'{indent}<{tag} type="{ref_type}" refObjectId="{_x(ref_id)}">{desc_xml}</{tag}>\n'


def _jsonld_process_to_ilcd(data):
    """Convert an openLCA JSON-LD Process to ILCD XML."""
    uid = data.get("@id", "")
    name = data.get("name", "")
    desc = data.get("description", "")
    loc = data.get("location", {})
    loc_code = loc.get("code", loc.get("name", "")) if isinstance(loc, dict) else ""
    ptype = data.get("processType", "")
    ilcd_ptype = "Unit process, single operation" if ptype == "UNIT_PROCESS" else "LCI result"

    xml = _xml_header("processDataSet", ILCD_NS["process"])

    # processInformation
    xml += '  <processInformation>\n'
    xml += '    <dataSetInformation>\n'
    xml += f'      <common:UUID>{_x(uid)}</common:UUID>\n'
    xml += '      <name>\n'
    xml += _lang_elem("baseName", name, "en", "        ")
    xml += '      </name>\n'
    if desc:
        xml += _lang_elem("common:generalComment", desc, "en", "      ")
    xml += '    </dataSetInformation>\n'

    # quantitativeReference
    ref_flow_id = None
    for i, exc in enumerate(data.get("exchanges", [])):
        if exc.get("isQuantitativeReference"):
            ref_flow_id = str(i)
            break
    if ref_flow_id is not None:
        xml += '    <quantitativeReference type="Reference flow(s)">\n'
        xml += f'      <referenceToReferenceFlow>{ref_flow_id}</referenceToReferenceFlow>\n'
        xml += '    </quantitativeReference>\n'

    # time
    xml += '    <time>\n'
    xml += f'      <common:referenceYear>2024</common:referenceYear>\n'
    xml += '    </time>\n'

    # geography
    if loc_code:
        xml += '    <geography>\n'
        xml += f'      <locationOfOperationSupplyOrProduction location="{_x(loc_code)}"/>\n'
        xml += '    </geography>\n'

    # technology
    tech = data.get("description", "")
    if tech:
        xml += '    <technology>\n'
        xml += _lang_elem("technologyDescriptionAndIncludedProcesses", tech, "en", "      ")
        xml += '    </technology>\n'

    xml += '  </processInformation>\n'

    # modellingAndValidation
    xml += '  <modellingAndValidation>\n'
    xml += '    <LCIMethodAndAllocation>\n'
    xml += f'      <typeOfDataSet>{_x(ilcd_ptype)}</typeOfDataSet>\n'
    xml += '    </LCIMethodAndAllocation>\n'
    xml += '  </modellingAndValidation>\n'

    # administrativeInformation
    xml += '  <administrativeInformation>\n'
    xml += '    <dataEntryBy>\n'
    xml += f'      <common:timeStamp>{datetime.now().isoformat()}</common:timeStamp>\n'
    xml += '    </dataEntryBy>\n'
    xml += '    <publicationAndOwnership>\n'
    xml += '      <common:dataSetVersion>01.00.000</common:dataSetVersion>\n'
    xml += '    </publicationAndOwnership>\n'
    xml += '  </administrativeInformation>\n'

    # exchanges
    exchanges = data.get("exchanges", [])
    if exchanges:
        xml += '  <exchanges>\n'
        for i, exc in enumerate(exchanges):
            flow = exc.get("flow", {}) if isinstance(exc.get("flow"), dict) else {}
            flow_id = flow.get("@id", "")
            flow_name = flow.get("name", "")
            direction = "Input" if exc.get("isInput") else "Output"
            amount = exc.get("amount", 0)

            xml += f'    <exchange dataSetInternalID="{i}">\n'
            xml += _ref_elem("referenceToFlowDataSet", "flow data set", flow_id, flow_name, "      ")
            xml += f'      <exchangeDirection>{direction}</exchangeDirection>\n'
            xml += f'      <meanAmount>{amount}</meanAmount>\n'
            xml += f'      <resultingAmount>{amount}</resultingAmount>\n'
            xml += '    </exchange>\n'
        xml += '  </exchanges>\n'

    xml += _xml_footer("processDataSet")
    return xml


def _jsonld_flow_to_ilcd(data):
    """Convert an openLCA JSON-LD Flow to ILCD XML."""
    uid = data.get("@id", "")
    name = data.get("name", "")
    flow_type = data.get("flowType", "")
    cas = data.get("cas", "")

    type_map = {
        "PRODUCT_FLOW": "Product flow",
        "ELEMENTARY_FLOW": "Elementary flow",
        "WASTE_FLOW": "Waste flow",
    }
    ilcd_type = type_map.get(flow_type, "Product flow")

    xml = _xml_header("flowDataSet", ILCD_NS["flow"])

    xml += '  <flowInformation>\n'
    xml += '    <dataSetInformation>\n'
    xml += f'      <common:UUID>{_x(uid)}</common:UUID>\n'
    xml += '      <name>\n'
    xml += _lang_elem("baseName", name, "en", "        ")
    xml += '      </name>\n'
    if cas:
        xml += f'      <CASNumber>{_x(cas)}</CASNumber>\n'
    xml += '    </dataSetInformation>\n'
    xml += '  </flowInformation>\n'

    xml += '  <modellingAndValidation>\n'
    xml += '    <LCIMethod>\n'
    xml += f'      <typeOfDataSet>{_x(ilcd_type)}</typeOfDataSet>\n'
    xml += '    </LCIMethod>\n'
    xml += '  </modellingAndValidation>\n'

    xml += '  <administrativeInformation>\n'
    xml += '    <publicationAndOwnership>\n'
    xml += '      <common:dataSetVersion>01.00.000</common:dataSetVersion>\n'
    xml += '    </publicationAndOwnership>\n'
    xml += '  </administrativeInformation>\n'

    # flowProperties
    fp_list = data.get("flowProperties", [])
    if fp_list:
        xml += '  <flowProperties>\n'
        for i, fpf in enumerate(fp_list):
            fp = fpf.get("flowProperty", {}) if isinstance(fpf.get("flowProperty"), dict) else {}
            fp_id = fp.get("@id", "")
            fp_name = fp.get("name", "")
            factor = fpf.get("conversionFactor", 1.0)
            is_ref = fpf.get("referenceFlowProperty", False)

            xml += f'    <flowProperty dataSetInternalID="{i}">\n'
            xml += _ref_elem("referenceToFlowPropertyDataSet", "flow property data set", fp_id, fp_name, "      ")
            xml += f'      <meanValue>{factor}</meanValue>\n'
            if is_ref:
                xml += '      <referenceFlowProperty>true</referenceFlowProperty>\n'
            xml += '    </flowProperty>\n'
        xml += '  </flowProperties>\n'

    xml += _xml_footer("flowDataSet")
    return xml


def _jsonld_flowproperty_to_ilcd(data):
    """Convert an openLCA JSON-LD FlowProperty to ILCD XML."""
    uid = data.get("@id", "")
    name = data.get("name", "")
    ug = data.get("unitGroup", {}) if isinstance(data.get("unitGroup"), dict) else {}
    ug_id = ug.get("@id", "")
    ug_name = ug.get("name", "")

    xml = _xml_header("flowPropertyDataSet", ILCD_NS["flowproperty"])

    xml += '  <flowPropertiesInformation>\n'
    xml += '    <dataSetInformation>\n'
    xml += f'      <common:UUID>{_x(uid)}</common:UUID>\n'
    xml += _lang_elem("common:name", name, "en", "      ")
    xml += '    </dataSetInformation>\n'
    xml += '    <quantitativeReference>\n'
    xml += _ref_elem("referenceToReferenceUnitGroup", "unit group data set", ug_id, ug_name, "      ")
    xml += '    </quantitativeReference>\n'
    xml += '  </flowPropertiesInformation>\n'

    xml += '  <administrativeInformation>\n'
    xml += '    <publicationAndOwnership>\n'
    xml += '      <common:dataSetVersion>01.00.000</common:dataSetVersion>\n'
    xml += '    </publicationAndOwnership>\n'
    xml += '  </administrativeInformation>\n'

    xml += _xml_footer("flowPropertyDataSet")
    return xml


def _jsonld_unitgroup_to_ilcd(data):
    """Convert an openLCA JSON-LD UnitGroup to ILCD XML."""
    uid = data.get("@id", "")
    name = data.get("name", "")
    units = data.get("units", [])

    xml = _xml_header("unitGroupDataSet", ILCD_NS["unitgroup"])

    xml += '  <unitGroupInformation>\n'
    xml += '    <dataSetInformation>\n'
    xml += f'      <common:UUID>{_x(uid)}</common:UUID>\n'
    xml += _lang_elem("common:name", name, "en", "      ")
    xml += '    </dataSetInformation>\n'

    # Find reference unit
    ref_unit_id = None
    for i, u in enumerate(units):
        if u.get("referenceUnit"):
            ref_unit_id = str(i)
            break
    if ref_unit_id is not None:
        xml += '    <quantitativeReference>\n'
        xml += f'      <referenceToReferenceUnit>{ref_unit_id}</referenceToReferenceUnit>\n'
        xml += '    </quantitativeReference>\n'

    xml += '  </unitGroupInformation>\n'

    xml += '  <administrativeInformation>\n'
    xml += '    <publicationAndOwnership>\n'
    xml += '      <common:dataSetVersion>01.00.000</common:dataSetVersion>\n'
    xml += '    </publicationAndOwnership>\n'
    xml += '  </administrativeInformation>\n'

    if units:
        xml += '  <units>\n'
        for i, u in enumerate(units):
            uname = u.get("name", "")
            factor = u.get("conversionFactor", 1.0)
            xml += f'    <unit dataSetInternalID="{i}">\n'
            xml += f'      <name>{_x(uname)}</name>\n'
            xml += f'      <meanValue>{factor}</meanValue>\n'
            xml += '    </unit>\n'
        xml += '  </units>\n'

    xml += _xml_footer("unitGroupDataSet")
    return xml


def _jsonld_source_to_ilcd(data):
    """Convert an openLCA JSON-LD Source to ILCD XML."""
    uid = data.get("@id", "")
    name = data.get("name", "")
    desc = data.get("description", "")
    url = data.get("url", "")

    xml = _xml_header("sourceDataSet", ILCD_NS["source"])

    xml += '  <sourceInformation>\n'
    xml += '    <dataSetInformation>\n'
    xml += f'      <common:UUID>{_x(uid)}</common:UUID>\n'
    xml += _lang_elem("common:shortName", name, "en", "      ")
    if url:
        xml += f'      <sourceCitation>{_x(url)}</sourceCitation>\n'
    xml += '    </dataSetInformation>\n'
    xml += '  </sourceInformation>\n'

    xml += '  <administrativeInformation>\n'
    xml += '    <publicationAndOwnership>\n'
    xml += '      <common:dataSetVersion>01.00.000</common:dataSetVersion>\n'
    xml += '    </publicationAndOwnership>\n'
    xml += '  </administrativeInformation>\n'

    xml += _xml_footer("sourceDataSet")
    return xml


def _jsonld_actor_to_ilcd(data):
    """Convert an openLCA JSON-LD Actor to ILCD Contact."""
    uid = data.get("@id", "")
    name = data.get("name", "")
    email = data.get("email", "")

    xml = _xml_header("contactDataSet", ILCD_NS["contact"])

    xml += '  <contactInformation>\n'
    xml += '    <dataSetInformation>\n'
    xml += f'      <common:UUID>{_x(uid)}</common:UUID>\n'
    xml += _lang_elem("common:shortName", name, "en", "      ")
    xml += _lang_elem("common:name", name, "en", "      ")
    if email:
        xml += f'      <email>{_x(email)}</email>\n'
    xml += '    </dataSetInformation>\n'
    xml += '  </contactInformation>\n'

    xml += '  <administrativeInformation>\n'
    xml += '    <publicationAndOwnership>\n'
    xml += '      <common:dataSetVersion>01.00.000</common:dataSetVersion>\n'
    xml += '    </publicationAndOwnership>\n'
    xml += '  </administrativeInformation>\n'

    xml += _xml_footer("contactDataSet")
    return xml


def _jsonld_impactcategory_to_ilcd(data):
    """Convert an openLCA JSON-LD ImpactCategory to ILCD LCIAMethodDataSet.

    In openLCA: ImpactMethod contains ImpactCategories.
    In ILCD: each ImpactCategory becomes a standalone LCIAMethodDataSet
    with its own characterization factors.
    """
    uid = data.get("@id", "")
    name = data.get("name", "")
    desc = data.get("description", "")
    ref_unit = data.get("referenceUnitName", "")
    factors = data.get("impactFactors", [])

    xml = _xml_header("LCIAMethodDataSet", ILCD_NS["lcia"])

    xml += '  <LCIAMethodInformation>\n'
    xml += '    <dataSetInformation>\n'
    xml += f'      <common:UUID>{_x(uid)}</common:UUID>\n'
    xml += _lang_elem("common:name", name, "en", "      ")
    xml += '      <methodology>LCIA methodology</methodology>\n'
    xml += _lang_elem("impactIndicator", name, "en", "      ")
    if ref_unit:
        xml += f'      <referenceQuantity>{_x(ref_unit)}</referenceQuantity>\n'
    if desc:
        xml += _lang_elem("common:generalComment", desc, "en", "      ")
    xml += '    </dataSetInformation>\n'
    xml += '  </LCIAMethodInformation>\n'

    xml += '  <administrativeInformation>\n'
    xml += '    <publicationAndOwnership>\n'
    xml += '      <common:dataSetVersion>01.00.000</common:dataSetVersion>\n'
    xml += '    </publicationAndOwnership>\n'
    xml += '  </administrativeInformation>\n'

    if factors:
        xml += '  <characterisationFactors>\n'
        for f in factors:
            flow = f.get("flow", {}) if isinstance(f.get("flow"), dict) else {}
            flow_id = flow.get("@id", "")
            flow_name = flow.get("name", "")
            value = f.get("value", 0)
            direction = "Input" if f.get("flowDirection") == "INPUT" else "Output"

            xml += '    <factor>\n'
            xml += _ref_elem("referenceToFlowDataSet", "flow data set", flow_id, flow_name, "      ")
            xml += f'      <exchangeDirection>{direction}</exchangeDirection>\n'
            xml += f'      <meanValue>{value}</meanValue>\n'
            xml += '    </factor>\n'
        xml += '  </characterisationFactors>\n'

    xml += _xml_footer("LCIAMethodDataSet")
    return xml


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(description="LCA Format Validator — Parse, validate, convert LCA data packages")
    sub = parser.add_subparsers(dest="command")

    p_parse = sub.add_parser("parse", help="Parse and summarize a data package")
    p_parse.add_argument("path", help="Path to zip file or directory")

    p_validate = sub.add_parser("validate", help="Validate structure and generate report")
    p_validate.add_argument("path", help="Path to zip file or directory")

    p_convert = sub.add_parser("convert", help="Convert between formats")
    p_convert.add_argument("path", help="Path to zip file or directory")
    p_convert.add_argument("--to", choices=["json", "jsonld", "ilcd"], required=True, help="Target format: json (raw), jsonld (openLCA JSON-LD), ilcd (ILCD XML)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "parse":
        return cmd_parse(args.path)
    elif args.command == "validate":
        return cmd_validate(args.path)
    elif args.command == "convert":
        return cmd_convert(args.path, args.to)

if __name__ == "__main__":
    sys.exit(main() or 0)
