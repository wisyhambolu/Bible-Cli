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
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error output: {e.stderr}")
        if check:
            raise
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
    today = datetime.now().strftime("%Y-%m-%d")
    
    with open("CHANGELOG.md", "r") as f:
        content = f.read()
    
    # Find the position after the header
    header_end = content.find("\n## [")
    if header_end == -1:
        header_end = content.find("\n\n")
    
    new_entry = f"\n## [{version}] - {today}\n\n{changes}\n"
    
    updated_content = content[:header_end] + new_entry + content[header_end:]
    
    with open("CHANGELOG.md", "w") as f:
        f.write(updated_content)

def update_version_in_file(file_path, current_version, new_version):
    """Update version in a file"""
    with open(file_path, "r") as f:
        content = f.read()
    
    # Update version in pyproject.toml format
    updated_content = re.sub(
        r'version\s*=\s*"' + current_version + '"',
        f'version = "{new_version}"',
        content
    )
    
    # Update version in __version__ format
    updated_content = re.sub(
        r'__version__\s*=\s*"' + current_version + '"',
        f'__version__ = "{new_version}"',
        updated_content
    )
    
    # Update version in setup.py format
    updated_content = re.sub(
        r'version\s*=\s*"' + current_version + '",',
        f'version="{new_version}",',
        updated_content
    )
    
    with open(file_path, "w") as f:
        f.write(updated_content)

def main():
    if len(sys.argv) != 2:
        print("Usage: python release.py <bump_type>")
        print("bump_type can be:")
        print("  major: bump major version (1.0.0 -> 2.0.0)")
        print("  minor: bump minor version (1.0.0 -> 1.1.0)")
        print("  patch: bump patch version (1.0.0 -> 1.0.1)")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    if bump_type not in ["major", "minor", "patch"]:
        print("Error: bump_type must be one of: major, minor, patch")
        sys.exit(1)
    
    current_version = get_current_version()
    if not current_version:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    
    new_version = update_version(current_version, bump_type)
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    # Update version in all relevant files
    files_to_update = [
        "pyproject.toml",
        "bible_cli/__init__.py",
        "setup.py",
        "bible_cli.py"
    ]
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            print(f"Updating version in {file_path}...")
            update_version_in_file(file_path, current_version, new_version)
    
    # Get changelog entries
    print("\nEnter changelog entries (press Ctrl+D when done):")
    changes = []
    try:
        while True:
            line = input()
            if line.strip():
                changes.append(line)
    except EOFError:
        pass
    
    changes_text = "\n".join(f"- {change}" for change in changes)
    
    # Update changelog
    update_changelog(new_version, changes_text)
    
    # Clean up build artifacts
    print("\nCleaning up build artifacts...")
    run_command("rm -rf dist/ build/ bible_cli.egg-info/")
    
    # Build the package
    print("\nBuilding package...")
    run_command("python -m build")
    
    # Run tests
    print("\nRunning tests...")
    test_result = run_command("python -m pytest", check=False)
    if test_result is None:
        print("\nTests failed. Do you want to continue anyway? (y/n)")
        if input().lower() != "y":
            print("Release aborted.")
            sys.exit(1)
    
    # Create and push git tag
    print("\nCreating git tag...")
    run_command(f'git tag -a v{new_version} -m "Release v{new_version}"')
    
    # Commit changes
    print("\nCommitting changes...")
    run_command("git add .")
    run_command(f'git commit -m "Release v{new_version}"')
    
    # Push changes
    print("\nPushing changes...")
    run_command("git push")
    run_command(f"git push origin v{new_version}")
    
    print(f"\nRelease v{new_version} completed successfully!")
    print("\nTo publish to PyPI, run:")
    print(f"python -m twine upload dist/bible_cli-{new_version}-py3-none-any.whl")

if __name__ == "__main__":
    main() 
