import strawberry
from strawberry import relay
from typing import List

@strawberry.type
class BrandEdge:
  cursor: str
  node: str

@strawberry.type
class BrandConnection:
  edges: List[BrandEdge]
  page_info: relay.PageInfo