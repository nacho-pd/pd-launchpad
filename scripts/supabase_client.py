#!/usr/bin/env python3
"""
Lightweight Supabase work_item client for pd-launchpad product repos.

Reads credentials from .env file in project root.
Required env vars: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

Usage:
    python scripts/supabase_client.py list [--status STATUS] [--limit N]
    python scripts/supabase_client.py get WORK_ITEM_ID
    python scripts/supabase_client.py update WORK_ITEM_ID --field value [--field value ...]
    python scripts/supabase_client.py log-tokens --session-type TYPE --model MODEL --input N --output N
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


def load_env():
    """Load .env file from project root."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        print(f"ERROR: .env file not found at {env_path}", file=sys.stderr)
        print("Create .env with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY", file=sys.stderr)
        sys.exit(1)

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_config():
    """Get Supabase configuration from environment."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        sys.exit(1)
    return url, key


def supabase_request(method, endpoint, data=None, params=None):
    """Make a request to Supabase REST API."""
    url, key = get_config()
    full_url = f"{url}/rest/v1/{endpoint}"

    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        full_url = f"{full_url}?{query}"

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(full_url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            response_body = resp.read().decode("utf-8")
            return json.loads(response_body) if response_body else None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"ERROR {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)


def get_repo_name():
    """Get the repository name from package.json or directory name."""
    pkg_path = Path(__file__).resolve().parent.parent / "package.json"
    if pkg_path.exists():
        with open(pkg_path, encoding="utf-8") as f:
            pkg = json.load(f)
            name = pkg.get("name", "")
            if name and not name.startswith("["):
                return name
    return Path(__file__).resolve().parent.parent.name


def cmd_list(args):
    """List work items for this repo."""
    repo = get_repo_name()
    params = {
        "target_repo": f"eq.{repo}",
        "order": "priority.asc,created_at.desc",
        "limit": str(args.limit),
    }
    if args.status:
        params["status"] = f"eq.{args.status}"

    items = supabase_request("GET", "work_items", params=params)
    if not items:
        print("No work items found.")
        return

    print(f"{'ID':<36}  {'Status':<15}  {'Priority':<8}  {'Title'}")
    print("-" * 100)
    for item in items:
        print(f"{item['id']:<36}  {item['status']:<15}  {item.get('priority', '-'):<8}  {item.get('title', 'Untitled')}")


def cmd_get(args):
    """Get a specific work item."""
    params = {"id": f"eq.{args.work_item_id}"}
    items = supabase_request("GET", "work_items", params=params)
    if not items:
        print(f"Work item {args.work_item_id} not found.")
        return
    print(json.dumps(items[0], indent=2, ensure_ascii=False))


def cmd_update(args):
    """Update a work item."""
    update_data = {}
    if args.status:
        update_data["status"] = args.status
    if args.pr_url:
        update_data["pr_url"] = args.pr_url
    if args.preview_url:
        update_data["preview_url"] = args.preview_url
    if args.agent_notes:
        update_data["agent_notes"] = args.agent_notes

    if not update_data:
        print("ERROR: No fields to update. Use --status, --pr-url, --preview-url, or --agent-notes", file=sys.stderr)
        sys.exit(1)

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    params = {"id": f"eq.{args.work_item_id}"}
    result = supabase_request("PATCH", "work_items", data=update_data, params=params)
    if result:
        print(f"Updated work item {args.work_item_id}:")
        print(json.dumps(result[0], indent=2, ensure_ascii=False))


def cmd_log_tokens(args):
    """Log token usage to Supabase."""
    data = {
        "repo": get_repo_name(),
        "session_type": args.session_type,
        "model": args.model,
        "input_tokens": args.input,
        "output_tokens": args.output,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = supabase_request("POST", "token_usage", data=data)
    if result:
        print(f"Logged token usage: {args.input} in / {args.output} out ({args.model})")


def main():
    parser = argparse.ArgumentParser(description="Supabase work_item client for pd-launchpad repos")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    list_parser = subparsers.add_parser("list", help="List work items for this repo")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument("--limit", type=int, default=20, help="Max items to return")
    list_parser.set_defaults(func=cmd_list)

    # get
    get_parser = subparsers.add_parser("get", help="Get a specific work item")
    get_parser.add_argument("work_item_id", help="Work item UUID")
    get_parser.set_defaults(func=cmd_get)

    # update
    update_parser = subparsers.add_parser("update", help="Update a work item")
    update_parser.add_argument("work_item_id", help="Work item UUID")
    update_parser.add_argument("--status", help="New status")
    update_parser.add_argument("--pr-url", help="PR URL")
    update_parser.add_argument("--preview-url", help="Preview deployment URL")
    update_parser.add_argument("--agent-notes", help="Agent notes (JSON string)")
    update_parser.set_defaults(func=cmd_update)

    # log-tokens
    tokens_parser = subparsers.add_parser("log-tokens", help="Log token usage")
    tokens_parser.add_argument("--session-type", required=True, choices=["heartbeat", "task", "judge", "ad_hoc"])
    tokens_parser.add_argument("--model", required=True, help="Model used")
    tokens_parser.add_argument("--input", type=int, required=True, help="Input tokens")
    tokens_parser.add_argument("--output", type=int, required=True, help="Output tokens")
    tokens_parser.set_defaults(func=cmd_log_tokens)

    args = parser.parse_args()
    load_env()
    args.func(args)


if __name__ == "__main__":
    main()
