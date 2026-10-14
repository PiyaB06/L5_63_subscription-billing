"""Print Pylint score, Bandit counts and Flake8 count for a file."""
import json
import re
import subprocess
import sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else "billing_system.py"


def run(*args):
    """Run a tool module and return its stdout."""
    result = subprocess.run(
        [sys.executable, "-m", *args],
        capture_output=True, text=True, check=False,
    )
    return result.stdout


pylint_out = run("pylint", TARGET)
match = re.search(r"rated at ([\d.\-]+)/10", pylint_out)
score = match.group(1) if match else "n/a"

bandit = json.loads(run("bandit", "-q", "-f", "json", TARGET))
counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
for item in bandit["results"]:
    counts[item["issue_severity"]] += 1

flake8_count = len(run("flake8", TARGET).splitlines())

print(f"File:    {TARGET}")
print(f"Pylint:  {score}/10   (target > 9.5)")
print(f"Bandit:  High={counts['HIGH']}  Medium={counts['MEDIUM']}  "
      f"Low={counts['LOW']}   (target all 0)")
print(f"Flake8:  {flake8_count} issues   (target 0)")