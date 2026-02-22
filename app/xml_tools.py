from lxml import etree
from collections import Counter

def summarize_xml_for_llm(xml_bytes: bytes, max_sample_nodes: int = 8) -> str:
    """
    Parse XML and produce a compact summary:
    - root tag
    - most common tags
    - a few sample paths and example attributes/text snippets
    """
    parser = etree.XMLParser(recover=False, huge_tree=True)
    root = etree.fromstring(xml_bytes, parser=parser)

    tags = []
    paths = []
    samples = []

    def walk(node, path_prefix=""):
        tag = node.tag if isinstance(node.tag, str) else str(node.tag)
        path = f"{path_prefix}/{tag}"
        tags.append(tag)
        paths.append(path)

        # Collect limited samples
        if len(samples) < max_sample_nodes:
            attrs = dict(node.attrib) if node.attrib else {}
            text = (node.text or "").strip()
            if len(text) > 120:
                text = text[:120] + "…"
            samples.append({"path": path, "attributes": attrs, "text": text})

        for child in node:
            if isinstance(child.tag, str):
                walk(child, path)

    walk(root)

    tag_counts = Counter(tags).most_common(20)
    path_counts = Counter(paths).most_common(20)

    lines = []
    lines.append(f"ROOT: <{root.tag}>")
    lines.append("\nTOP TAGS (tag: count):")
    for t, c in tag_counts:
        lines.append(f"- {t}: {c}")

    lines.append("\nTOP PATHS (path: count):")
    for p, c in path_counts:
        lines.append(f"- {p}: {c}")

    lines.append("\nSAMPLES:")
    for s in samples:
        lines.append(f"- path: {s['path']}")
        if s["attributes"]:
            lines.append(f"  attributes: {s['attributes']}")
        if s["text"]:
            lines.append(f"  text: {s['text']}")

    return "\n".join(lines)