import re
from typing import Dict, Any


TARGET_COMPRESSED_SIZE = 2000
COMPRESSION_THRESHOLD = 3000


def compress_tool_output(
    tool_name: str,
    tool_input: Dict[str, Any],
    output: str
) -> Dict[str, Any]:
    original_size = len(output)

    if original_size <= COMPRESSION_THRESHOLD:
        return {"compressed": output, "was_compressed": False, "original_size": original_size}

    compressed = _compress_by_tool_type(tool_name, tool_input, output)

    return {
        "compressed": _truncate_to_target(compressed),
        "was_compressed": True,
        "original_size": original_size
    }


def _compress_by_tool_type(tool_name: str, tool_input: Dict[str, Any], output: str) -> str:
    if tool_name == "Read":
        return _compress_file_read(tool_input, output)
    if tool_name == "Bash":
        return _compress_bash_output(tool_input, output)
    if tool_name == "Grep":
        return _compress_grep_output(tool_input, output)
    if tool_name == "Glob":
        return _compress_glob_output(tool_input, output)
    if tool_name in ("Edit", "Write"):
        return _compress_edit_output(tool_input, output)
    return _compress_generic(output)


def _compress_file_read(tool_input: Dict[str, Any], output: str) -> str:
    file_path = tool_input.get("file_path", "unknown") if tool_input else "unknown"
    file_name = file_path.split("/")[-1] if file_path else "file"
    lines = output.split("\n")
    total_lines = len(lines)

    imports = _extract_imports(output)
    exports = _extract_exports(output)
    functions = _extract_function_signatures(output)
    classes = _extract_class_names(output)
    errors = _extract_error_patterns(output)

    parts = [f"File: {file_name} ({total_lines} lines)"]

    if imports:
        parts.append(f"\nImports: {', '.join(imports[:10])}{f' (+{len(imports) - 10} more)' if len(imports) > 10 else ''}")

    if exports:
        parts.append(f"\nExports: {', '.join(exports[:10])}{f' (+{len(exports) - 10} more)' if len(exports) > 10 else ''}")

    if functions:
        parts.append(f"\nFunctions: {', '.join(functions[:10])}{f' (+{len(functions) - 10} more)' if len(functions) > 10 else ''}")

    if classes:
        parts.append(f"\nClasses: {', '.join(classes)}")

    if errors:
        parts.append(f"\nErrors/TODOs: {'; '.join(errors[:5])}")

    context_lines = [
        "\n--- First 10 lines ---",
        *lines[:10],
        "\n--- Last 5 lines ---",
        *lines[-5:]
    ]
    parts.append("\n".join(context_lines))

    return "".join(parts)


def _compress_bash_output(tool_input: Dict[str, Any], output: str) -> str:
    command = tool_input.get("command", "command") if tool_input else "command"
    short_cmd = command.split("\n")[0][:100]
    lines = output.split("\n")

    error_lines = [
        l for l in lines
        if any(kw in l.lower() for kw in ("error", "failed", "exception", "warning"))
    ]

    success_lines = [
        l for l in lines
        if any(kw in l.lower() for kw in ("success", "passed", "completed", "done"))
    ]

    parts = [f"Command: {short_cmd}"]

    if error_lines:
        parts.append(f"\nErrors ({len(error_lines)}):")
        parts.extend(error_lines[:10])

    if success_lines:
        parts.append(f"\nSuccess indicators:")
        parts.extend(success_lines[:5])

    parts.append(f"\nOutput: {len(lines)} lines total")

    if len(lines) > 20:
        parts.append("\n--- First 10 lines ---")
        parts.extend(lines[:10])
        parts.append("\n--- Last 5 lines ---")
        parts.extend(lines[-5:])
    else:
        parts.append("\n--- Full output ---")
        parts.extend(lines)

    return "\n".join(map(str, parts))


def _compress_grep_output(tool_input: Dict[str, Any], output: str) -> str:
    pattern = tool_input.get("pattern", "pattern") if tool_input else "pattern"
    lines = [l for l in output.split("\n") if l]

    files = set()
    for line in lines:
        m = re.match(r"^([^:]+):", line)
        if m:
            files.add(m.group(1))

    parts = [
        f'Grep: "{pattern[:50]}"',
        f"Found in {len(files)} files, {len(lines)} matches"
    ]

    if files:
        sample_files = list(files)[:15]
        parts.append(f"\nFiles: {', '.join(sample_files)}{f' (+{len(files) - 15} more)' if len(files) > 15 else ''}")

    parts.append("\n--- Top matches ---")
    parts.extend(lines[:10])

    if len(lines) > 10:
        parts.append(f"\n... and {len(lines) - 10} more matches")

    return "\n".join(parts)


def _compress_glob_output(tool_input: Dict[str, Any], output: str) -> str:
    pattern = tool_input.get("pattern", "pattern") if tool_input else "pattern"

    try:
        parsed = output if output.startswith("[") else f'["{output}"]'
        import json
        files = json.loads(parsed).get("filenames", []) if isinstance(parsed, str) else []
    except Exception:
        files = output.split("\n")

    if not isinstance(files, list):
        files = []

    by_dir: Dict[str, list] = {}
    for f in files:
        if isinstance(f, str):
            dir_path = "/".join(f.split("/")[:-1]) or "/"
            file_name = f.split("/")[-1] or f
            by_dir.setdefault(dir_path, []).append(file_name)

    parts = [
        f'Glob: "{pattern[:50]}"',
        f"Found {len(files)} files in {len(by_dir)} directories"
    ]

    top_dirs = sorted(by_dir.items(), key=lambda x: -len(x[1]))[:5]

    parts.append("\n--- Top directories ---")
    for dir_path, dir_files in top_dirs:
        short_dir = "/".join(dir_path.split("/")[-3:])
        parts.append(f"{short_dir}/ ({len(dir_files)} files)")

    parts.append("\n--- Sample files ---")
    sample_names = [f.split("/")[-1] for f in files[:15] if isinstance(f, str)]
    parts.append(", ".join(sample_names))

    return "\n".join(map(str, parts))


def _compress_edit_output(tool_input: Dict[str, Any], output: str) -> str:
    file_path = tool_input.get("file_path", "unknown") if tool_input else "unknown"
    file_name = file_path.split("/")[-1] if file_path else "file"

    return f"""Edited: {file_name}
Changes applied successfully
{output[:500]}"""


def _compress_generic(output: str) -> str:
    lines = output.split("\n")

    if len(lines) <= 30:
        return output

    return f"""Output: {len(lines)} lines
--- First 15 lines ---
{chr(10).join(lines[:15])}
--- Last 10 lines ---
{chr(10).join(lines[-10:])}"""


def _extract_imports(code: str) -> list:
    imports = []
    patterns = [
        (r"import\s+(?:{\s*([^}]+)\s*}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]", 3),
        (r"from\s+['\"]([^'\"]+)['\"]\s+import", 1),
        (r"require\s*\(['\"]([^'\"]+)['\"]\)", 1),
        (r"use\s+(\w+(?:::\w+)*)", 1),
    ]

    for pattern, group in patterns:
        for m in re.finditer(pattern, code):
            imports.append(m.group(group))

    return list(set(imports))


def _extract_exports(code: str) -> list:
    exports = []
    patterns = [
        r"export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)",
        r"export\s*{\s*([^}]+)\s*}",
        r"pub\s+(?:fn|struct|enum|trait|mod)\s+(\w+)",
    ]

    for pattern in patterns:
        for m in re.finditer(pattern, code):
            names = [n.strip() for n in m.group(1).split(",")] if "," in m.group(1) else [m.group(1)]
            exports.extend(n for n in names if n)

    return list(set(exports))


def _extract_function_signatures(code: str) -> list:
    functions = []
    patterns = [
        r"(?:async\s+)?function\s+(\w+)",
        r"(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>",
        r"(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
        r"fn\s+(\w+)",
        r"def\s+(\w+)",
    ]

    for pattern in patterns:
        functions.extend(m.group(1) for m in re.finditer(pattern, code))

    return list(set(functions))


def _extract_class_names(code: str) -> list:
    classes = []
    patterns = [
        r"class\s+(\w+)",
        r"struct\s+(\w+)",
        r"interface\s+(\w+)",
        r"type\s+(\w+)\s*=",
    ]

    for pattern in patterns:
        classes.extend(m.group(1) for m in re.finditer(pattern, code))

    return list(set(classes))


def _extract_error_patterns(code: str) -> list:
    errors = []
    keywords = ("TODO", "FIXME", "HACK", "XXX", "BUG")

    for line in code.split("\n"):
        if any(kw in line for kw in keywords):
            errors.append(line.strip()[:100])

    return errors[:10]


def _truncate_to_target(text: str) -> str:
    if len(text) <= TARGET_COMPRESSED_SIZE:
        return text
    return text[:TARGET_COMPRESSED_SIZE - 20] + "\n... (compressed)"


def get_compression_stats(original_size: int, compressed_size: int) -> Dict[str, Any]:
    saved = original_size - compressed_size
    ratio = original_size / compressed_size if compressed_size > 0 else 1
    saved_percent = f"{(saved / original_size * 100):.1f}" if original_size > 0 else "0.0"

    return {"ratio": round(ratio, 2), "saved": saved, "saved_percent": saved_percent}
