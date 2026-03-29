#!/usr/bin/env python3
"""
Bootstrap a new product repo from the pd-launchpad template.

Usage:
    python scripts/bootstrap_project.py \
        --name "architect-console" \
        --description "Visual tool for product architects" \
        --dest "C:/Users/nacho/Documents/ProductDirectionRoot/architect-console"
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {"node_modules", ".git"}
EXCLUDE_FILES = {"package-lock.json"}

PDOS_CONFIG_PATH = Path(
    "C:/Users/nacho/Documents/ProductDirectionRoot/ProductDirection-os"
    "/02_data_and_reports/content_analytics/config.json"
)

REPLACEABLE_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".ts", ".tsx", ".js", ".jsx"}


def copy_template(dest: Path):
    """Copy template to destination, excluding node_modules, .git, package-lock.json."""
    for item in TEMPLATE_DIR.iterdir():
        if item.name in EXCLUDE_DIRS:
            continue
        if item.name in EXCLUDE_FILES:
            continue
        src_path = item
        dst_path = dest / item.name
        if src_path.is_dir():
            shutil.copytree(
                src_path, dst_path,
                ignore=shutil.ignore_patterns(*EXCLUDE_DIRS, *EXCLUDE_FILES),
            )
        else:
            shutil.copy2(src_path, dst_path)


def replace_placeholders(dest: Path, name: str, description: str):
    """Replace all placeholders in project files."""
    replacements = {
        "[PROJECT_NAME]": name,
        "[PROJECT_DESCRIPTION]": description,
        "[project-name]": name,
    }
    count = 0
    for root, _dirs, files in os.walk(dest):
        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix not in REPLACEABLE_EXTENSIONS:
                continue
            try:
                text = fpath.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            original = text
            for placeholder, value in replacements.items():
                text = text.replace(placeholder, value)
            if text != original:
                fpath.write_text(text, encoding="utf-8")
                count += 1
    return count


def generate_env(dest: Path):
    """Generate .env with Supabase credentials from PD-OS config.json."""
    if not PDOS_CONFIG_PATH.exists():
        print(f"WARNING: PD-OS config not found at {PDOS_CONFIG_PATH}", file=sys.stderr)
        print("Creating .env with placeholder values. Edit manually.", file=sys.stderr)
        env_content = (
            "SUPABASE_URL=https://your-project.supabase.co\n"
            "SUPABASE_SERVICE_ROLE_KEY=your-service-role-key\n"
        )
    else:
        with open(PDOS_CONFIG_PATH, encoding="utf-8") as f:
            config = json.load(f)
        sb = config["supabase"]
        env_content = (
            f"SUPABASE_URL={sb['project_url']}\n"
            f"SUPABASE_SERVICE_ROLE_KEY={sb['service_role_key']}\n"
        )

    env_path = dest / ".env"
    env_path.write_text(env_content, encoding="utf-8")
    return env_path


def register_in_supabase(name: str, dest: Path, description: str):
    """Register the new project in Supabase repos table."""
    if not PDOS_CONFIG_PATH.exists():
        print("WARNING: Skipping Supabase registration (config not found).", file=sys.stderr)
        return False

    with open(PDOS_CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    sb = config["supabase"]
    url = f"{sb['project_url']}/rest/v1/repos"
    key = sb["service_role_key"]

    data = json.dumps({
        "name": name,
        "path": str(dest.resolve()),
        "description": description,
        "claude_md_exists": True,
    }).encode("utf-8")

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"WARNING: Supabase registration failed ({e.code}): {error_body}", file=sys.stderr)
        return False


def git_init(dest: Path):
    """Initialize git repo and create initial commit."""
    subprocess.run(["git", "init"], cwd=dest, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=dest, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit from pd-launchpad template"],
        cwd=dest, check=True, capture_output=True,
    )


def npm_install(dest: Path):
    """Run npm install in the new project."""
    print("Running npm install...")
    result = subprocess.run(
        ["npm", "install"],
        cwd=dest, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"WARNING: npm install failed:\n{result.stderr}", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap a new product repo from pd-launchpad template"
    )
    parser.add_argument("--name", required=True, help="Project name (kebab-case)")
    parser.add_argument("--description", required=True, help="One-line project description")
    parser.add_argument("--dest", required=True, help="Destination directory path")
    parser.add_argument("--skip-npm", action="store_true", help="Skip npm install")
    parser.add_argument("--skip-supabase", action="store_true", help="Skip Supabase registration")
    args = parser.parse_args()

    dest = Path(args.dest).resolve()

    # Idempotent check
    if dest.exists():
        print(f"ERROR: Destination already exists: {dest}", file=sys.stderr)
        print("Remove it first or choose a different path.", file=sys.stderr)
        sys.exit(1)

    print(f"Bootstrapping '{args.name}' at {dest}...")

    # 1. Copy template
    print("  1. Copying template files...")
    dest.mkdir(parents=True)
    copy_template(dest)

    # 2. Replace placeholders
    print("  2. Replacing placeholders...")
    files_changed = replace_placeholders(dest, args.name, args.description)
    print(f"     Updated {files_changed} files")

    # 3. Generate .env
    print("  3. Generating .env...")
    generate_env(dest)

    # 4. Register in Supabase
    if not args.skip_supabase:
        print("  4. Registering in Supabase repos table...")
        result = register_in_supabase(args.name, dest, args.description)
        if result:
            print("     Registered successfully")
    else:
        print("  4. Skipping Supabase registration")

    # 5. Git init
    print("  5. Initializing git repository...")
    git_init(dest)

    # 6. npm install
    if not args.skip_npm:
        print("  6. Installing npm dependencies...")
        npm_install(dest)
    else:
        print("  6. Skipping npm install")

    # Summary
    print("\n" + "=" * 60)
    print(f"Project '{args.name}' created successfully!")
    print("=" * 60)
    print(f"\n  Location: {dest}")
    print(f"\n  Next steps:")
    print(f"    cd {dest}")
    print(f"    npm run dev          # Start dev server")
    print(f"    claude               # Start Claude Code")
    print(f"\n  To push to GitHub:")
    print(f"    gh repo create ignaciobassino/{args.name} --public")
    print(f"    git remote add origin https://github.com/ignaciobassino/{args.name}.git")
    print(f"    git push -u origin main")


if __name__ == "__main__":
    main()
