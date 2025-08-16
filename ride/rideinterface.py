from enum import Enum
from typing import Any, Dict


class RideType(str, Enum):
    REQUEST = "request"
    ACCEPT = "accept"
    ARRIVING = "arriving"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RideInterface:
    def __init__(self, data: Dict[str, Any], type: RideType):
        self.data = data
        self.type = RideType(type)

    def request(self):
        pass

    def accept(self):
        pass

    def arriving(self):
        pass

    def inprogress(self):
        pass

    def complete(self):
        pass

    def cancel(self):
        pass
