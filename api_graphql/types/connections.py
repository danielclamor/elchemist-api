from typing import Iterable, Optional

import strawberry
from strawberry import relay


@strawberry.type(name="Connection", description="A connection to a list of items.")
class ListConnectionWithTotalCount(relay.ListConnection[relay.NodeType]):
  nodes: strawberry.Private[Optional[Iterable[relay.NodeType]]] = None

  @strawberry.field(description="Total number of nodes, ignoring pagination.")
  def total_count(self) -> int:
    assert self.nodes is not None
    return len(list(self.nodes))

  @classmethod
  def resolve_connection(
    cls, nodes, *, info, before=None, after=None, first=None, last=None, max_results=None, **kwargs
  ):
    ret = super().resolve_connection(
      nodes, info=info, before=before, after=after,
      first=first, last=last, max_results=max_results, **kwargs,
    )
    ret.nodes = nodes
    return ret