"""Remove the 🔒 marker from README table rows whose repositories are now public.

A repository counts as public when https://github.com/<owner>/<repo> answers
HTTP 200 to an anonymous request (private repositories answer 404).
Rows that link several repositories lose the lock only when ALL are public.
"""
import pathlib
import re
import urllib.error
import urllib.request

OWNER = "God-Gamer-Manyu"
README = pathlib.Path("README.md")
PREFIX = "| 🔒 "

_cache = {}


def is_public(repo):
    if repo not in _cache:
        req = urllib.request.Request(
            f"https://github.com/{OWNER}/{repo}",
            method="HEAD",
            headers={"User-Agent": "readme-lock-updater"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                _cache[repo] = resp.status == 200
        except urllib.error.HTTPError as err:
            _cache[repo] = False if err.code == 404 else None  # None = unknown
        except Exception:
            _cache[repo] = None
    return _cache[repo]


def main():
    text = README.read_text(encoding="utf-8")
    lines = []
    for line in text.split("\n"):
        if line.startswith(PREFIX):
            repos = set(re.findall(rf"https://github\.com/{OWNER}/([A-Za-z0-9._-]+)", line))
            if repos and all(is_public(r) is True for r in repos):
                line = "| " + line[len(PREFIX):]
                print("now public:", ", ".join(sorted(repos)))
        lines.append(line)
    new = "\n".join(lines)

    # Once every row is public, drop the explanatory note as well.
    if not re.search(r"^\| 🔒 ", new, flags=re.M):
        new = re.sub(r"^> 🔒 These repositories.*\n\n", "", new, flags=re.M)

    if new != text:
        README.write_text(new, encoding="utf-8")


if __name__ == "__main__":
    main()
