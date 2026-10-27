"""
Anki TSV/CSV serialization and import utilities for StudyVault flashcards.
"""

from typing import List, Dict, Any


def serialize_cards_to_anki(cards: List[Dict[str, Any]], deck_name: str = "StudyVault") -> str:
    """
    Serializes a list of flashcards to Anki-compatible TSV format.
    Format: Front \t Back \t Tags
    """
    lines = [
        f"#separator:tab",
        f"#html:true",
        f"#deck:{deck_name}",
        f"#columns:Front\tBack\tTags"
    ]
    for card in cards:
        front = card.get("front", "").replace("\n", "<br>").replace("\t", " ")
        back = card.get("back", "").replace("\n", "<br>").replace("\t", " ")
        topic = card.get("topic", "").replace(" ", "_")
        lines.append(f"{front}\t{back}\t{topic}")

    return "\n".join(lines) + "\n"


def parse_anki_tsv(tsv_content: str) -> List[Dict[str, str]]:
    """
    Parses Anki-compatible TSV content back into flashcard items.
    """
    cards = []
    lines = tsv_content.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            front = parts[0].replace("<br>", "\n").strip()
            back = parts[1].replace("<br>", "\n").strip()
            topic = parts[2].replace("_", " ").strip() if len(parts) >= 3 else "General"
            cards.append({
                "front": front,
                "back": back,
                "topic": topic
            })
    return cards
