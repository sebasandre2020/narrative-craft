# Subsystem: Vector Lore Retrieval & Context Fusion

## 1. Overview
While the Graph Engine tracks immediate relational proximity (e.g., who is holding what, which room connects to where), **Qdrant** provides long-term semantic lore retrieval. This ensures that narrative worldbuilding—ancient prophecies, historical wars, and character backstories—informs LLM generation without bloating context windows.

## 2. Qdrant Vector Collection Configuration
- **Collection Name**: `narrative_lore`
- **Vector Dimension**: 1536 (OpenAI `text-embedding-3-small`) or 384 (`bge-small-en-v1.5`)
- **Distance Metric**: Cosine Similarity
- **Payload Schema**:
  ```json
  {
    "world_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "lore_id": "lore_silver_sigil_origins",
    "category": "faction_history",
    "tags": ["silver_sigil", "knights", "holy_order"],
    "canonical_text": "The Order of the Silver Sigil was founded during the Siege of the Weeping Moon...",
    "created_at": "2026-09-27T15:00:00Z"
  }
  ```

## 3. Hybrid Context Fusion
When constructing the prompt for the LangGraph scene generation node, the context compiler merges two distinct modalities:

```text
=== ACTIVE SPATIAL & RELATIONAL GRAPH (Deterministic) ===
Current Location: Crypt of Ancients
Characters Present: Lady Vespera (HP: 100, Class: Arcane Inquisitor)
Items in Room: Rusted Iron Portcullis (Locked: False), Stone Sarcophagus
Inventory: Engraved Silver Key, Dagger of the Pale Moon
Connected Rooms: Damp Antechamber (Accessible via Portcullis)

=== RETRIEVED CANON LORE (Semantic Relevance > 0.82) ===
[Citadel Architecture Codex]: Lower portcullises were forged with dual tumblers keyed to imperial silver ward keys.
[Order of the Silver Sigil Annals]: Inquisitors carry engraved silver keys as symbols of their authority to unseal sealed catacombs.
```

By fusing strict relational facts with rich thematic lore, the LLM produces prose that is both atmospheric and 100% logically consistent.
