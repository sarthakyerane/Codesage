"""
Runs the C++ static analyzer on uploaded source files.
Only works for C/C++ files.
"""
import subprocess, json, os
from pathlib import Path
from loguru import logger

ANALYZER_BIN = os.environ.get("ANALYZER_BIN", "/app/analyzer/analyzer")
CPP_EXTENSIONS = {".cpp", ".c", ".h", ".hpp", ".cc"}


def is_analyzable(filename: str) -> bool:
    return Path(filename).suffix.lower() in CPP_EXTENSIONS


async def analyze_file(file_path: str, source_code: str) -> list[dict]:
    """Run analyzer binary on a source file, return findings as dicts."""
    if not is_analyzable(file_path) or not os.path.isfile(ANALYZER_BIN):
        return []

    tmp = "/tmp/codesage_analyze.cpp"
    try:
        with open(tmp, "w") as f:
            f.write(source_code)
        result = subprocess.run([ANALYZER_BIN, tmp], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return []
        findings = json.loads(result.stdout)
        logger.info(f"Analyzer: {len(findings)} issue(s) in {file_path}")
        return findings
    except Exception as e:
        logger.warning(f"Analyzer failed: {e}")
        return []
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def format_findings_for_prompt(findings: list[dict]) -> str:
    """Format findings as text for the LLM prompt."""
    if not findings:
        return ""
    lines = ["## Static Analysis Findings:", ""]
    for f in findings:
        lines.append(f"- [{f['severity'].upper()}] Line {f['line']}: {f['detail']}")
    lines.append("\nUse these confirmed findings to provide more accurate fixes.")
    return "\n".join(lines)
