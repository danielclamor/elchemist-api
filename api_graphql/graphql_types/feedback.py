import strawberry

from api_graphql.graphql_types.enums import FeedbackStatus

@strawberry.type
class Feedback:
  status: FeedbackStatus
  message: str | None = None