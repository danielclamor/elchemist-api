import enum

import strawberry

@strawberry.enum
class FeedbackStatusEnum(enum.Enum):
  SUCCESS = "success"
  FAILED = "failed"
  CANCELLED = "cancelled"

@strawberry.type
class Feedback:
  status: FeedbackStatusEnum
  message: str | None = None