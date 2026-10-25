"""Application service for API-ready V2 Story navigation."""
from __future__ import annotations
from collections.abc import Callable,Iterable,Mapping,Sequence
from rom_v2.domain.story_navigation import StoryQuestState,StoryQuestStatus,StoryQuestView,StorySectionView,StoryView,ensure_safe_ui_text

LOCATION_LABELS={"start_path":"Початок Шляху","dark_forest":"Темний Бір"}
SECTION_TITLES={"start_path":("Перші кроки","Сліди небезпеки","Шлях найманця","Перед вирішальним походом","Ватажок зграї"),"dark_forest":("На межі Темного Бору","Глибше в хащу","Сліди культу","Спотворені землі","Фінал Темного Бору")}
class StoryNavigationService:
 def __init__(self,quests:Iterable[object],title_resolver:Callable[[object,str,int],str]|None=None):
  ordered=tuple(sorted(quests,key=lambda q:int(q.number)))
  if len(ordered)!=100 or tuple(int(q.number) for q in ordered)!=tuple(range(1,101)):raise ValueError("story_navigation_requires_quests_1_100")
  if len({q.quest_id for q in ordered})!=100:raise ValueError("duplicate_story_quest_id")
  self._quests=ordered;self._by_number={int(q.number):q for q in ordered};self._title_resolver=title_resolver or self._default_title
 @staticmethod
 def _default_title(quest:object,status:str,quest_item_quantity:int)->str:
  if str(getattr(quest,"quest_type","")).upper()=="QUEST_ITEM" and status not in {"COMPLETED","SKIPPED"} and quest_item_quantity<=0:return "Невідома знахідка"
  return str(quest.title)
 @staticmethod
 def derive_status(number:int,states:Mapping[int,StoryQuestState],player_level:int)->StoryQuestStatus:
  row=states.get(number)
  if row:return row.status
  previous=states.get(number-1) if number>1 else None
  chain_open=number==1 or (previous is not None and previous.status in {StoryQuestStatus.COMPLETED,StoryQuestStatus.SKIPPED})
  quest_level=((number-1)//10)+1
  return StoryQuestStatus.AVAILABLE if chain_open and player_level>=quest_level else StoryQuestStatus.LOCKED
 def build(self,states:Mapping[int,StoryQuestState],player_level:int)->tuple[StoryView,...]:
  stories=[]
  for location_id,start in (("start_path",1),("dark_forest",51)):
   sections=[]
   for offset,title in enumerate(SECTION_TITLES[location_id]):
    first=start+offset*10;views=[]
    for number in range(first,first+10):
     q=self._by_number[number];st=self.derive_status(number,states,player_level);row=states.get(number);qty=row.quest_item_quantity if row else 0
     presented=ensure_safe_ui_text(self._title_resolver(q,st.value,qty));progress=row.progress if row and st==StoryQuestStatus.ACTIVE else 0;target=row.target_quantity if row else int(q.target_quantity)
     views.append(StoryQuestView(number,q.quest_id,presented,st,progress,target,st==StoryQuestStatus.AVAILABLE))
    section=StorySectionView(f"{location_id}_{offset+1:02d}",location_id,offset+1,title,(first-1)//10+1,tuple(views));ensure_safe_ui_text(section.display_title);sections.append(section)
   stories.append(StoryView(location_id,location_id,ensure_safe_ui_text(LOCATION_LABELS[location_id]),"🧭" if location_id=="start_path" else "🌲",tuple(sections)))
  return tuple(stories)
 def active_target(self,states:Mapping[int,StoryQuestState])->dict|None:
  active=[s for s in states.values() if s.status==StoryQuestStatus.ACTIVE]
  if len(active)>1:raise ValueError("multiple_active_story_quests")
  if not active:return None
  state=active[0];q=self._by_number[state.quest_number];objective=ensure_safe_ui_text(str(q.objective_text));return {"quest_number":state.quest_number,"title":ensure_safe_ui_text(str(q.title)),"objective":objective,"progress":state.progress,"target_quantity":state.target_quantity}
