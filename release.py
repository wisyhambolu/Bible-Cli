#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        if check:
            sys.exit(1)
        return None

def get_current_version():
    """Get the current version from pyproject.toml"""
    with open("pyproject.toml", "r") as f:
        content = f.read()
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return None

def update_version(version, bump_type):
    """Update version number based on bump type"""
    major, minor, patch = map(int, version.split("."))
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    
    return f"{major}.{minor}.{patch}"

def update_changelog(version, changes):
    """Update CHANGELOG.md with new version and changes"""
    changelog_path = Path("CHANGELOG.md")
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not changelog_path.exists():
        changelog_path.write_text(f"# Changelog\n\n")
    
    current_content = changelog_path.read_text()
    new_entry = f"\n## [{version}] - {today}\n\n{changes}\n"
    
    # Insert new entry after the first heading
    updated_content = re.sub(
        r"(# Changelog\n\n)",
        f"\\1{new_entry}",
        current_content
    )
    
    changelog_path.write_text(updated_content)

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ["major", "minor", "patch"]:
        print("Usage: python release.py [major|minor|patch]")
        print("  major: bump major version (1.0.0 -> 2.0.0)")
        print("  minor: bump minor version (1.0.0 -> 1.1.0)")
        print("  patch: bump patch version (1.0.0 -> 1.0.1)")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    current_version = get_current_version()
    
    if not current_version:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    
    new_version = update_version(current_version, bump_type)
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    # Update version in pyproject.toml
    with open("pyproject.toml", "r") as f:
        content = f.read()
    
    updated_content = re.sub(
        r'version\s*=\s*"' + current_version + '"',
        f'version = "{new_version}"',
        content
    )
    
    with open("pyproject.toml", "w") as f:
        f.write(updated_content)
    
    # Get changes from user
    print("\nEnter changelog entry (press Ctrl+D or Ctrl+Z when done):")
    changes = []
    try:
        while True:
            line = input()
            changes.append(line)
    except EOFError:
        pass
    
    changes_text = "\n".join(changes)
    
    # Update CHANGELOG.md
    update_changelog(new_version, changes_text)
    
    # Clean up build artifacts
    print("\nCleaning up build artifacts...")
    run_command("rm -rf dist/ build/ bible_cli.egg-info/")
    
    # Build the package
    print("\nBuilding package...")
    run_command("python -m build")
    
    # Run tests (if you have any)
    print("\nRunning tests...")
    test_result = run_command("python -m pytest", check=False)
    if test_result is None:
        print("Warning: Tests failed. Do you want to continue? (y/n)")
        if input().lower() != "y":
            sys.exit(1)
    
    # Create git tag
    print("\nCreating git tag...")
    run_command(f'git tag -a v{new_version} -m "Release v{new_version}"')
    
    # Push changes and tag
    print("\nPushing changes to git...")
    run_command("git add .")
    run_command(f'git commit -m "Release v{new_version}"')
    run_command("git push")
    run_command(f"git push origin v{new_version}")
    
    # Ask if user wants to publish to PyPI
    print("\nDo you want to publish to PyPI? (y/n)")
    if input().lower() == "y":
        print("\nPublishing to PyPI...")
        run_command("python -m twine upload dist/*")
    
    print(f"\nRelease v{new_version} completed successfully!")
    print("\nNext steps:")
    print("1. Review the changes in CHANGELOG.md")
    print("2. Update documentation if needed")
    print("3. Create a release on GitHub")

if __name__ == "__main__":
    main() 
