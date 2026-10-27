"""
StudyVault Semantic Knowledge Graph & Concept Relational Network Builder.
Constructs concept entities and typed relational links from academic text.
"""

import re
from typing import List, Dict, Any
from ai_generator import extract_key_concepts


RELATION_PATTERNS = [
    (r"\b([A-Za-z\s]+?)\s+(?:is\s+a|is\s+an)\s+([A-Za-z\s]+?)(?:\.|\,|$)", "is_a"),
    (r"\b([A-Za-z\s]+?)\s+(?:uses|employs|utilizes)\s+([A-Za-z\s]+?)(?:\.|\,|$)", "uses"),
    (r"\b([A-Za-z\s]+?)\s+(?:depends\s+on|requires)\s+([A-Za-z\s]+?)(?:\.|\,|$)", "depends_on"),
    (r"\b([A-Za-z\s]+?)\s+(?:contains|consists\s+of)\s+([A-Za-z\s]+?)(?:\.|\,|$)", "contains"),
    (r"\b([A-Za-z\s]+?)\s+(?:is\s+equivalent\s+to|evaluates\s+to)\s+([A-Za-z\s]+?)(?:\.|\,|$)", "equivalent_to")
]


def build_knowledge_graph(title: str, text: str) -> Dict[str, Any]:
    """
    Synthesizes a directed knowledge network with concept nodes and semantic relation edges.
    """
    concepts = extract_key_concepts(f"{title}\n{text}", max_terms=10)
    node_map = {}
    edges = []

    # Root note node
    root_id = re.sub(r"[^\w-]", "", title.lower()).replace(" ", "-") or "root"
    node_map[root_id] = {
        "id": root_id,
        "label": title,
        "category": "root",
        "weight": 3
    }

    # Add concept nodes
    for c in concepts:
        c_label = c["concept"]
        c_id = re.sub(r"[^\w-]", "", c_label.lower()).replace(" ", "-")
        if not c_id or c_id == root_id:
            continue
        node_map[c_id] = {
            "id": c_id,
            "label": c_label,
            "category": "concept",
            "weight": c.get("frequency", 1)
        }
        # Edge from root to concept
        edges.append({
            "source": root_id,
            "target": c_id,
            "relation": "discusses"
        })

    # Detect relational clauses between concepts
    for pattern, rel_type in RELATION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for src, tgt in matches:
            s_clean = src.strip().title()
            t_clean = tgt.strip().title()
            if len(s_clean.split()) <= 4 and len(t_clean.split()) <= 4:
                s_id = re.sub(r"[^\w-]", "", s_clean.lower()).replace(" ", "-")
                t_id = re.sub(r"[^\w-]", "", t_clean.lower()).replace(" ", "-")
                if s_id and t_id and s_id != t_id:
                    if s_id not in node_map:
                        node_map[s_id] = {"id": s_id, "label": s_clean, "category": "entity", "weight": 1}
                    if t_id not in node_map:
                        node_map[t_id] = {"id": t_id, "label": t_clean, "category": "entity", "weight": 1}
                    edges.append({
                        "source": s_id,
                        "target": t_id,
                        "relation": rel_type
                    })

    return {
        "nodes": list(node_map.values()),
        "edges": edges[:25]
    }
