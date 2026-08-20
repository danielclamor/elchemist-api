import strawberry

from api_graphql.types.enums import FeedbackStatus

@strawberry.type
class Feedback:
  status: FeedbackStatus
  message: str | None = None