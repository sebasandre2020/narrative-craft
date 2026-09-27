-- Narrative-Craft Relational Property Graph & Event Sourcing Schema
-- PostgreSQL 16+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Narrative World Sessions
CREATE TABLE IF NOT EXISTS worlds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL DEFAULT '{"max_reflection_attempts": 2, "temporal_decay": 0.05}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Timelines (Multiverse Branching DAG)
CREATE TABLE IF NOT EXISTS timelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    parent_timeline_id UUID REFERENCES timelines(id) ON DELETE SET NULL,
    fork_event_id UUID,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Immutable Narrative Events (Event Store)
CREATE TABLE IF NOT EXISTS narrative_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_id UUID NOT NULL REFERENCES timelines(id) ON DELETE CASCADE,
    sequence_number BIGINT NOT NULL,
    action_prompt TEXT NOT NULL,
    narrative_prose TEXT NOT NULL,
    graph_delta JSONB NOT NULL,
    lore_citations JSONB NOT NULL DEFAULT '[]'::jsonb,
    token_usage JSONB NOT NULL DEFAULT '{"prompt": 0, "completion": 0}'::jsonb,
    committed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_timeline_sequence UNIQUE (timeline_id, sequence_number)
);

-- 4. Property Graph Nodes (Active State Projection)
CREATE TABLE IF NOT EXISTS graph_nodes (
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,
    node_type VARCHAR(50) NOT NULL, -- 'character', 'location', 'item', 'faction'
    label VARCHAR(255) NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (world_id, node_id)
);

-- 5. Property Graph Edges (Active State Projection)
CREATE TABLE IF NOT EXISTS graph_edges (
    world_id UUID NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
    source_id VARCHAR(100) NOT NULL,
    target_id VARCHAR(100) NOT NULL,
    relation VARCHAR(100) NOT NULL, -- 'located_in', 'possesses', 'allied_with', 'adjacent_to'
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (world_id, source_id, target_id, relation)
);

-- 6. Periodic State Snapshots (Replay Acceleration)
CREATE TABLE IF NOT EXISTS timeline_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timeline_id UUID NOT NULL REFERENCES timelines(id) ON DELETE CASCADE,
    last_event_id UUID NOT NULL REFERENCES narrative_events(id) ON DELETE CASCADE,
    sequence_number BIGINT NOT NULL,
    graph_snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indices for Low-Latency Traversal & Event Streaming
CREATE INDEX IF NOT EXISTS idx_timelines_world ON timelines(world_id);
CREATE INDEX IF NOT EXISTS idx_events_timeline_seq ON narrative_events(timeline_id, sequence_number ASC);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON graph_nodes(world_id, node_type);
CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(world_id, source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(world_id, target_id);
CREATE INDEX IF NOT EXISTS idx_edges_relation ON graph_edges(world_id, relation);

-- Initial Dark Fantasy Sample Seed (World, Timeline, Seed Graph)
INSERT INTO worlds (id, title, description) 
VALUES ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Shadow of the Iron Citadel', 'A gothic dark fantasy world ruled by warring factions')
ON CONFLICT (id) DO NOTHING;

INSERT INTO timelines (id, world_id, name)
VALUES ('b2c3d4e5-f6a7-8901-bcde-f12345678901', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'Canonical Timeline (Prime)')
ON CONFLICT (id) DO NOTHING;

-- Seed Nodes
INSERT INTO graph_nodes (world_id, node_id, node_type, label, properties) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'char_vespera', 'character', 'Lady Vespera', '{"class": "Arcane Inquisitor", "hp": 100, "status": "alert"}'::jsonb),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'loc_crypt', 'location', 'Crypt of Ancients', '{"lighting": "dim", "terrain": "stone_catacombs"}'::jsonb),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'loc_antechamber', 'location', 'Damp Antechamber', '{"lighting": "dark", "terrain": "collapsed_tunnel"}'::jsonb),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'item_silver_key', 'item', 'Engraved Silver Key', '{"weight_kg": 0.1, "material": "silver", "magical": false}'::jsonb),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'gate_iron_portcullis', 'item', 'Rusted Iron Portcullis', '{"locked": true, "key_requirement": "item_silver_key"}'::jsonb)
ON CONFLICT DO NOTHING;

-- Seed Edges
INSERT INTO graph_edges (world_id, source_id, target_id, relation, properties) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'char_vespera', 'loc_crypt', 'located_in', '{}'::jsonb),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'char_vespera', 'item_silver_key', 'possesses', '{"equipped": true}'::jsonb),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'gate_iron_portcullis', 'loc_crypt', 'located_in', '{}'::jsonb),
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'loc_crypt', 'loc_antechamber', 'adjacent_to', '{"barrier": "gate_iron_portcullis"}'::jsonb)
ON CONFLICT DO NOTHING;
