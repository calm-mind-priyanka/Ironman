# Per-user temporary input states. These are process-local and intentionally
# kept separate from message handlers so command routing stays deterministic.
INPUT = {}
SEARCH_CACHE = {}
