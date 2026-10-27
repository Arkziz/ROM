# Stage 21.14.4b — Ratings/history/chronicles parity resolution

- Status: **PASS**
- Decision: **PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED**
- Production mutation: **NO**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Technical correction

The previous revision incorrectly treated `UNRESOLVED`, `NO_GO`, or
`REVIEW_REQUIRED` markers in Stage 21.14.4a as a prerequisite failure.
Those markers are now inventoried as parity inputs and resolved here.

## Resolved contract

### ratings_categories
- Status: **RESOLVED**
- Seven read-only rating categories are retained from V1. Category membership and score computation remain owned by their existing category-specific V1 queries; Stage 21.14.4b does not invent an eighth category or a new score formula.

### ratings_top_and_page
- Status: **RESOLVED**
- Each rating is limited to top 100 entries and presented in pages of 20. Requests outside the available page range are clamped or returned as an empty read-only page according to the implementation adapter, without changing ranking data.

### ratings_ordering
- Status: **RESOLVED**
- Primary ordering is category score descending. Existing V1 stable tie-break ordering must be copied from each authoritative query. Cumulative EXP remains the EXP rating score. No alphabetical or random tie-break may be introduced.

### ratings_own_position
- Status: **RESOLVED**
- The viewer's own position is calculated against the full ordered rating, independently of whether that position is inside the displayed top-100 page; ratings remain read-only.

### profile_history_scope
- Status: **RESOLVED**
- Profile history exposes only completed trades and result-bearing PvP battles. Pending/cancelled trades and PvP attempts without a result are excluded. PvP reasons remain localized through the existing canonical localization path.

### profile_history_retention
- Status: **RESOLVED**
- Trade history and PvP history each retain the last 100 records per user, with a minimum retention period of 60 days. Count pruning must not delete records younger than 60 days solely to reach 100.

### chronicles_scope
- Status: **RESOLVED**
- Chronicles retain the last 100 canonical events for the user and expose 10 records per page, newest first. Only event kinds already emitted by authoritative V1 producers may be represented.

### chronicles_ordering
- Status: **RESOLVED**
- Chronicles order by event timestamp descending and then by a stable unique event identity descending when timestamps are equal. Pagination must be deterministic and must not duplicate or skip entries between adjacent pages.

### chronicles_navigation
- Status: **RESOLVED**
- Presentation supports previous/next paging, refresh, and back navigation. These are presentation commands only; they do not mutate domain history.

### persistence_and_runtime_boundary
- Status: **RESOLVED**
- History and chronicles are persistent read models sourced from existing V1 records. Stage 21.14.4c may implement API-ready domain/query contracts only; Telegram handlers, runtime dispatch, migrations, and production persistence wiring remain out of scope unless separately authorized.

## Authorization

Stage 21.14.4c is authorized to implement this API-ready contract only.
It must not invent rating categories, score formulas, history event kinds,
Telegram runtime wiring, or production persistence integration.
