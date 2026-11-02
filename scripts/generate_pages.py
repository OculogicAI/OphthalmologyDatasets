import csv
import re
from pathlib import Path
from collections import defaultdict
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CSV_FILE = ROOT / "datasets.csv"

BROWSE_DIR = ROOT / "browse"
DATASET_DIR = ROOT / "datasets"

BROWSE_DIR.mkdir(exist_ok=True)
DATASET_DIR.mkdir(exist_ok=True)


def clean(value):
    return (value or "").strip()


def split_tags(value):
    return [
        tag.strip()
        for tag in clean(value).split(";")
        if tag.strip()
    ]


def safe_filename(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip().rstrip(".")
    return name or "Unnamed"


def markdown_text(value):
    return clean(value).replace("|", "\\|").replace("\n", " ")


def markdown_link(label, url):
    if url.startswith(("https://", "http://")):
        return f"[{markdown_text(label)}]({url})"
    return markdown_text(label)


# Read CSV
with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as file:
    datasets = list(csv.DictReader(file))


# Generate dataset detail pages
for dataset in datasets:
    name = clean(dataset.get("Dataset"))

    if not name:
        continue

    filename = safe_filename(name) + ".md"
    output = DATASET_DIR / filename

    lines = [
        f"# {name}",
        "",
        "[← Back to Home](../README.md)",
        "",
        "## Basic Information",
        "",
        "| Field | Value |",
        "|---|---|",
    ]

    fields = [
        "Full Name",
        "Year",
        "Modality",
        "Anatomy",
        "Disease / Condition",
        "Task",
        "Data Type",
        "Annotation Type",
        "Data Structure",
        "Clinical Setting",
        "Size",
        "Patients / Eyes",
        "Access",
    ]

    for field in fields:
        value = markdown_text(dataset.get(field)) or "Not specified"
        lines.append(f"| {field} | {value} |")

    lines.extend([
        "",
        "## Resources",
        "",
    ])

    for label, field in [
        ("Dataset Website", "Dataset URL"),
        ("Paper", "Paper"),
        ("Code", "Code"),
    ]:
        url = clean(dataset.get(field))

        if url.startswith(("https://", "http://")):
            lines.append(f"- [{label}]({url})")
        else:
            lines.append(f"- {label}: Not available")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Generate browse pages
dimensions = {
    "Disease / Condition": "disease",
    "Modality": "modality",
    "Task": "task",
}

for column, page_name in dimensions.items():

    groups = defaultdict(list)

    for dataset in datasets:
        name = clean(dataset.get("Dataset"))

        if not name:
            continue

        for tag in split_tags(dataset.get(column)):
            groups[tag].append(dataset)

    lines = [
        f"# Browse by {page_name.title()}",
        "",
        "[← Back to Home](../README.md)",
        "",
    ]

    for tag in sorted(groups, key=str.casefold):
        lines.extend([
            f"## {tag}",
            "",
            "| Dataset | Modality | Disease | Task | Access |",
            "|---|---|---|---|---|",
        ])

        for dataset in sorted(
            groups[tag],
            key=lambda x: clean(x.get("Dataset")).casefold()
        ):
            name = clean(dataset.get("Dataset"))
            filename = safe_filename(name) + ".md"
            link = f"../datasets/{quote(filename)}"

            lines.append(
                f"| [{markdown_text(name)}]({link})"
                f" | {markdown_text(dataset.get('Modality'))}"
                f" | {markdown_text(dataset.get('Disease / Condition'))}"
                f" | {markdown_text(dataset.get('Task'))}"
                f" | {markdown_text(dataset.get('Access'))} |"
            )

        lines.append("")

    output = BROWSE_DIR / f"{page_name}.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Generated: {output}")

print(f"Generated detail pages for {len(datasets)} datasets.")
