from __future__ import annotations
from rom_v2.domain.npc_dialogue_model import V2NpcAcceptCommand,V2NpcAction,V2NpcActionKind,V2NpcDefinition,V2NpcInteractionResult,V2NpcView

class InMemoryV2NpcRegistry:
    def __init__(self, definitions: tuple[V2NpcDefinition, ...]):
        ids=[x.npc_id for x in definitions]
        if len(ids)!=len(set(ids)):raise ValueError("duplicate_npc_id")
        self._items={x.npc_id:x for x in definitions}
    def get(self,npc_id:str)->V2NpcDefinition|None:return self._items.get(npc_id)

class InMemoryV2QuestNpcPort:
    def __init__(self, quests: dict[int, tuple[bool,int,str]] | None=None):self.quests=quests or {};self.accepted=[]
    def action(self,quest_id:int):return self.quests.get(quest_id)
    def accept(self,user_id:int,quest_id:int,expected_revision:int):
        state=self.quests.get(quest_id)
        if state is None or not state[0]:return False,"quest_unavailable"
        if state[1]!=expected_revision:return False,"stale_revision"
        self.accepted.append((user_id,quest_id,expected_revision));return True,"accepted"

class V2NpcDialogueService:
    def __init__(self,registry:InMemoryV2NpcRegistry,quest_port:InMemoryV2QuestNpcPort):self.registry=registry;self.quest_port=quest_port
    def view(self,npc_id:str,player_location_id:str)->V2NpcInteractionResult:
        npc=self.registry.get(npc_id)
        if npc is None:return V2NpcInteractionResult(False,"unknown_npc")
        if npc.location_id!=player_location_id:return V2NpcInteractionResult(False,"wrong_location")
        actions=[]
        for quest_id in npc.quest_ids:
            state=self.quest_port.action(quest_id)
            if state is not None and state[0]:actions.append(V2NpcAction(f"story_quest:{quest_id}",V2NpcActionKind.STORY_QUEST,quest_id,state[1],state[2]))
        return V2NpcInteractionResult(True,view=V2NpcView(npc.npc_id,npc.display_name,npc.location_id,tuple(actions)))
    def accept(self,command:V2NpcAcceptCommand,player_location_id:str)->V2NpcInteractionResult:
        npc=self.registry.get(command.npc_id)
        if npc is None:return V2NpcInteractionResult(False,"unknown_npc")
        if npc.location_id!=player_location_id:return V2NpcInteractionResult(False,"wrong_location")
        if command.quest_id not in npc.quest_ids:return V2NpcInteractionResult(False,"quest_not_linked")
        ok,reason=self.quest_port.accept(command.user_id,command.quest_id,command.expected_revision)
        return V2NpcInteractionResult(ok,reason,quest_result=reason)
