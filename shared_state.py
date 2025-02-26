# shared_state.py
from typing import Optional, Dict, Any
import asyncio

class SharedState:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedState, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._data: Dict[str, Any] = {}  # Stores responses by request ID
            self._lock = asyncio.Lock()
            self._initialized = True

    async def set_data(self, request_id: str, value: Any) -> None:
        """Set data for a specific request ID in a thread-safe manner."""
        async with self._lock:
            self._data[request_id] = value

    async def get_data(self, request_id: str) -> Optional[Any]:
        """Get data for a specific request ID in a thread-safe manner."""
        async with self._lock:
            return self._data.get(request_id)

    async def reset(self, request_id: str) -> None:
        """Reset data for a specific request ID in a thread-safe manner."""
        async with self._lock:
            if request_id in self._data:
                del self._data[request_id]

# Singleton instance for easy import
shared_state = SharedState()
