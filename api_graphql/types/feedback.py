import enum

import strawberry

@strawberry.enum
class FeedbackStatus(enum.Enum):
  SUCCESS = "success"
  FAILED = "failed"
  CANCELLED = "cancelled"

@strawberry.type
class Feedback:
  status: FeedbackStatus
  message: str | None = None