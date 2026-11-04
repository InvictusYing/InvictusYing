"""Pull the newest papers from the website's papers.bib into README.md.

Writes between <!-- PAPERS:START --> and <!-- PAPERS:END -->.
No third-party packages needed.
"""
import re
import sys
import urllib.request

BIB_URL = "https://raw.githubusercontent.com/InvictusYing/invictusying.github.io/master/_bibliography/papers.bib"
README = "README.md"
N_PAPERS = 5
ME = "Wang, Zhongying"


def read_braced(text, i):
    """Return (content, end_index) for a {...} block starting at text[i] == '{'."""
    depth, start = 0, i
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    raise ValueError("unbalanced braces")


def parse_fields(body, strings):
    fields = {}
    for m in re.finditer(r"(\w+)\s*=\s*", body):
        key, j = m.group(1).lower(), m.end()
        if key in fields:
            continue
        if j < len(body) and body[j] == "{":
            val, _ = read_braced(body, j)
        else:
            raw = re.match(r"[\w\-]+", body[j:])
            val = strings.get(raw.group(0), raw.group(0)) if raw else ""
        fields[key] = val
    return fields


def parse_bib(text):
    strings, entries = {}, []
    for m in re.finditer(r"@(\w+)\s*{", text):
        kind = m.group(1).lower()
        body, _ = read_braced(text, m.end() - 1)
        if kind == "string":
            k, v = body.split("=", 1)
            strings[k.strip()] = v.strip().strip("{}")
        elif kind not in ("comment", "preamble"):
            entries.append(parse_fields(body.split(",", 1)[1], strings))
    return entries


def clean(s):
    return re.sub(r"\s+", " ", s.replace("{", "").replace("}", "")).strip()


def short_authors(authors):
    names = []
    for a in clean(authors).split(" and "):
        a = a.strip()
        if a == "others":
            names.append("et al.")
            continue
        last, _, first = a.partition(",")
        initials = " ".join(p[0] + "." for p in first.split() if p)
        name = f"{last.strip()}, {initials}".strip(", ")
        names.append(f"**{name}**" if a == ME else name)
    if len(names) > 6:
        names = names[:5] + ["et al."]
    return ", ".join(names)


def link(e):
    if e.get("html"):
        return e["html"]
    if e.get("doi"):
        return "https://doi.org/" + e["doi"]
    if e.get("arxiv"):
        return "https://arxiv.org/abs/" + e["arxiv"]
    return ""


def main():
    with urllib.request.urlopen(BIB_URL, timeout=30) as r:
        entries = parse_bib(r.read().decode("utf-8"))
    # Newest year first; within a year, keep the order in papers.bib.
    entries.sort(key=lambda e: -int(re.sub(r"\D", "", e.get("year", "0")) or 0))

    lines = []
    for e in entries[:N_PAPERS]:
        venue = clean(e.get("journal") or e.get("booktitle") or "")
        title = clean(e.get("title", ""))
        url = link(e)
        title_md = f"[{title}]({url})" if url else title
        lines.append(f"- {title_md}  \n  {short_authors(e.get('author', ''))} · *{venue}*, {e.get('year', '')}")

    block = "\n".join(lines)
    with open(README, encoding="utf-8") as f:
        readme = f.read()
    new = re.sub(
        r"(<!-- PAPERS:START -->).*?(<!-- PAPERS:END -->)",
        lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}",
        readme,
        flags=re.S,
    )
    if new == readme:
        print("No change.")
        return
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)
    print("README updated.")


if __name__ == "__main__":
    sys.exit(main())
