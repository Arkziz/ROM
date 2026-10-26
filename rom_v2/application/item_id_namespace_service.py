from __future__ import annotations
from dataclasses import dataclass, field
from rom_v2.domain.item_id_namespace import EVENT_BLOCK_COUNT,GENERATED_RANGE,PREVIEW_RANGE,STATIC_ASSIGNED,V2EventBlock,V2PreviewPromotion,event_block

@dataclass(slots=True)
class V2ItemIdNamespaceState:
    event_blocks: dict[str,list[V2EventBlock]] = field(default_factory=dict)
    retired_event_ordinals: set[int] = field(default_factory=set)
    next_generated_id: int = GENERATED_RANGE.start
    allocated_generated_ids: set[int] = field(default_factory=set)
    retired_generated_ids: set[int] = field(default_factory=set)
    next_preview_id: int = PREVIEW_RANGE.start
    allocated_preview_ids: set[int] = field(default_factory=set)
    preview_promotions: dict[int,V2PreviewPromotion] = field(default_factory=dict)

class V2ItemIdNamespaceService:
    def __init__(self,state:V2ItemIdNamespaceState|None=None):self.state=state or V2ItemIdNamespaceState()
    def allocate_event_block(self,event_key:str,*,additional:bool=False)->V2EventBlock:
        key=event_key.strip()
        if not key:raise ValueError("invalid_event_key")
        existing=self.state.event_blocks.get(key,[])
        if existing and not additional:return existing[0]
        used={b.ordinal for blocks in self.state.event_blocks.values() for b in blocks}|self.state.retired_event_ordinals
        ordinal=next((i for i in range(EVENT_BLOCK_COUNT) if i not in used),None)
        if ordinal is None:raise ValueError("event_namespace_exhausted")
        block=event_block(ordinal,key);self.state.event_blocks.setdefault(key,[]).append(block);return block
    def retire_event(self,event_key:str)->None:
        for block in self.state.event_blocks.get(event_key,[]):self.state.retired_event_ordinals.add(block.ordinal)
    def allocate_generated_id(self)->int:
        candidate=self.state.next_generated_id
        while candidate in self.state.allocated_generated_ids or candidate in self.state.retired_generated_ids:candidate+=1
        if not GENERATED_RANGE.contains(candidate):raise ValueError("generated_namespace_exhausted")
        self.state.allocated_generated_ids.add(candidate);self.state.next_generated_id=candidate+1;return candidate
    def retire_generated_id(self,item_id:int)->None:
        self.state.allocated_generated_ids.discard(item_id);self.state.retired_generated_ids.add(item_id)
    def allocate_preview_id(self)->int:
        candidate=self.state.next_preview_id
        while candidate in self.state.allocated_preview_ids or candidate in self.state.preview_promotions:candidate+=1
        if not PREVIEW_RANGE.contains(candidate):raise ValueError("preview_namespace_exhausted")
        self.state.allocated_preview_ids.add(candidate);self.state.next_preview_id=candidate+1;return candidate
    def plan_preview_promotion(self,preview_id:int)->V2PreviewPromotion:
        # Exact-once replay must be checked before active-preview membership because
        # the successful first promotion removes the temporary preview allocation.
        existing=self.state.preview_promotions.get(preview_id)
        if existing is not None:return existing
        if preview_id not in self.state.allocated_preview_ids:raise ValueError("unknown_preview_id")
        promotion=V2PreviewPromotion(preview_id,self.allocate_generated_id())
        self.state.preview_promotions[preview_id]=promotion
        self.state.allocated_preview_ids.remove(preview_id)
        return promotion
    @staticmethod
    def static_id_is_assigned(item_id:int)->bool:return item_id in STATIC_ASSIGNED
