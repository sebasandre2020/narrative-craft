# Subsystem: Event Sourcing & Multiverse Engine

## 1. Event Sourcing Philosophy
In traditional applications, state mutations overwrite existing database rows. In Narrative-Craft, **time and causality are first-class architectural concepts**. State is never overwritten; instead, every turn produces an immutable `NarrativeEvent` record.

The current world graph is simply a materialized projection of all previous events in the active timeline:
$$\text{State}_N = \text{Fold}(\text{InitialState}, [E_1, E_2, \dots, E_N])$$

## 2. Event Log Schema & Guarantees
- **Immutability**: Once an event is written to `narrative_events`, it can never be modified or deleted.
- **Strict Ordering**: Sequence numbers are strictly monotonically increasing (`1, 2, 3, ...`) enforced by a `UNIQUE(timeline_id, sequence_number)` database constraint.
- **Atomic Persistence**: Event log append and active graph projection updates execute inside a single PostgreSQL ACID transaction.

## 3. Multiverse Branching (Timeline DAG)
Creating an alternate reality (e.g. "What if Lady Vespera joined the Cult instead of fighting them?") does not copy or clone previous events:
1. A new timeline row is created with `parent_timeline_id` and `fork_event_id`.
2. When querying state or history for the child timeline, the replay engine reads events from the root timeline up to `fork_event_id`, followed by the events unique to the child timeline.
3. This creates a lightweight tree of timelines with zero redundant storage.

## 4. Replay & Snapshot Optimization
- **Periodic Snapshots**: Every 25 turns, the engine saves a complete JSON snapshot of the world graph into `timeline_snapshots`.
- **Replay Performance**: When a timeline state must be reconstructed (e.g. after a rollback or cache eviction), the engine loads the nearest snapshot before the target event and replays only the delta events between the snapshot and the target event, achieving sub-100ms state reconstruction even in 1,000+ turn campaigns.
