"""Session-based conversation memory (in-process; one entry per browser session)."""
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import config


@dataclass
class Session:
    id: str
    location: Optional[dict] = None          # {"lat", "lon", "name"}
    soil_profile: Optional[dict] = None      # normalised SoilGrids profile (see backend/soilgrids)
    analysis: Optional[dict] = None          # latest CropSense analysis (photo soil type, district NPK, weather, crops)
    history: List[dict] = field(default_factory=list)   # [{"role", "content"}]
    last_crops: List[str] = field(default_factory=list)  # crops recommended in the last answers
    last_sources: List[dict] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)

    def location_changed(self, lat: float, lon: float) -> bool:
        if not self.location:
            return True
        return abs(self.location["lat"] - lat) > 1e-3 or abs(self.location["lon"] - lon) > 1e-3

    def add_turn(self, user: str, assistant: str):
        self.history += [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]
        self.history = self.history[-config.MAX_HISTORY_TURNS * 2:]
        self.updated_at = time.time()


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()

    def get(self, session_id: Optional[str]) -> Session:
        with self._lock:
            self._evict()
            sid = session_id if session_id and len(session_id) <= 64 else str(uuid.uuid4())
            s = self._sessions.get(sid)
            if s is None:
                s = self._sessions[sid] = Session(id=sid)
            s.updated_at = time.time()
            return s

    def reset(self, session_id: str):
        with self._lock:
            self._sessions.pop(session_id, None)

    def _evict(self):
        now = time.time()
        for sid in [k for k, s in self._sessions.items() if now - s.updated_at > config.SESSION_TTL_S]:
            del self._sessions[sid]
        while len(self._sessions) >= config.MAX_SESSIONS:
            oldest = min(self._sessions.values(), key=lambda s: s.updated_at)
            del self._sessions[oldest.id]


sessions = SessionStore()
