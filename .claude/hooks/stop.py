import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


PROJECT_ROOT = Path(__file__).parent.parent.parent
SUMMARY_DIR = PROJECT_ROOT / ".claude" / "summaries"
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

MIN_OBSERVATIONS_FOR_SUMMARY = 3


def read_transcript() -> list:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return []
        lines = [l for l in raw.strip().splitlines() if l.strip()]
        records = []
        for line in lines:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records
    except Exception:
        return []


def capture_file_changes_via_git(project_root: Path) -> Dict[str, Any]:
    all_changed_files: List[str] = []
    git_diff_content = ""

    try:
        diff_names = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3
        )
        if diff_names.returncode == 0:
            all_changed_files.extend(diff_names.stdout.strip().split("\n"))

        staged_names = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3
        )
        if staged_names.returncode == 0:
            all_changed_files.extend(staged_names.stdout.strip().split("\n"))

        all_changed_files = [f for f in all_changed_files if f]

        if all_changed_files:
            git_diff_stat = subprocess.run(
                ["git", "diff", "HEAD", "--stat"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=3
            )
            if git_diff_stat.returncode == 0:
                git_diff_content = git_diff_stat.stdout.strip()

    except Exception:
        pass

    try:
        recent_files = subprocess.run(
            ["find", ".", "-maxdepth", "4", "-type", "f",
             "(", "-name", "*.py", "-o", "-name", "*.ts", "-o", "-name", "*.js",
             "-o", "-name", "*.tsx", "-o", "-name", "*.jsx", "-o", "-name", "*.md",
             "-o", "-name", "*.json", "-o", "-name", "*.rs", "-o", "-name", "*.go", ")",
             "-mmin", "-30",
             "!", "-path", "*/node_modules/*",
             "!", "-path", "*/.git/*",
             "!", "-path", "*/dist/*",
             "!", "-path", "*/build/*",
             "!", "-path", "*/.next/*",
             "!", "-path", "*/target/*",
             "2>/dev/null", "|", "head", "-30"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
            shell=True
        )
        if recent_files.returncode == 0:
            recent_files_list = [f.replace("./", "") for f in recent_files.stdout.strip().split("\n") if f]
            for f in recent_files_list:
                if f not in all_changed_files:
                    all_changed_files.append(f)
    except Exception:
        pass

    all_changed_files = sorted(set(all_changed_files))

    return {
        "files": all_changed_files,
        "git_diff_stat": git_diff_content
    }


def generate_session_summary(records: list, file_changes: Dict[str, Any]) -> Dict[str, Any]:
    key_decisions: List[str] = []
    files_modified = set(file_changes.get("files", []))
    observation_counts: Dict[str, int] = {}

    user_messages = []
    for record in records:
        role = record.get("role") or (record.get("message") or {}).get("role")
        content = record.get("content") or (record.get("message") or {}).get("content", "")

        if role == "user":
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        user_messages.append(block.get("text", "")[:200])
            elif isinstance(content, str):
                user_messages.append(content[:200])

        if role == "assistant" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if any(kw in text.lower() for kw in ["chose", "decided", "selected", "going with"]):
                        key_decisions.append(text[:100])

    for record in records:
        role = record.get("role") or (record.get("message") or {}).get("role")
        content = record.get("content") or (record.get("message") or {}).get("content", "")

        if role == "assistant" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    if tool_name in ("Edit", "Write", "Read"):
                        tool_input = block.get("input", {})
                        file_path = tool_input.get("file_path", "")
                        if file_path:
                            files_modified.add(file_path)

    summary_parts = []
    if user_messages:
        summary_parts.append(f"Addressed {len(user_messages)} user request(s)")
    if files_modified:
        summary_parts.append(f"Modified {len(files_modified)} file(s)")
    if key_decisions:
        summary_parts.append(f"Made {len(key_decisions)} key decision(s)")

    summary = ". ".join(summary_parts) if summary_parts else "Session completed"

    return {
        "key_decisions": key_decisions[:10],
        "files_modified": sorted(list(files_modified))[:20],
        "summary": summary,
        "user_messages_count": len(user_messages),
        "file_changes_summary": file_changes
    }


def save_session_summary(summary: Dict[str, Any]) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = SUMMARY_DIR / f"summary_{timestamp}.json"

    summary["timestamp"] = datetime.now().isoformat()
    summary["id"] = f"summary_{timestamp}"

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    return str(summary_file)


def main():
    records = read_transcript()

    if not records:
        print(json.dumps({"status": "no_records"}))
        return

    file_changes = capture_file_changes_via_git(PROJECT_ROOT)

    summary = generate_session_summary(records, file_changes)

    if len(records) >= MIN_OBSERVATIONS_FOR_SUMMARY or file_changes.get("files"):
        summary_file = save_session_summary(summary)

    response = {
        "status": "success",
        "hook": "stop",
        "timestamp": datetime.now().isoformat(),
        "records_processed": len(records),
        "files_modified": len(file_changes.get("files", [])),
        "summary": summary.get("summary", "")
    }

    if file_changes.get("files"):
        response["file_changes"] = file_changes["files"][:10]

    print(json.dumps(response))


if __name__ == "__main__":
    main()
