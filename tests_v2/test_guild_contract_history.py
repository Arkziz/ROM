import unittest
from rom_v2.application.guild_contract_history_service import *
from rom_v2.domain.guild_contract_history import *
from rom_v2.domain.guild_core import GuildCore,GuildIdentity,GuildMember,GuildRole
def guild():return GuildCore(1,GuildIdentity("Варта","варта","ВРТ","врт","🏰"),1,(GuildMember(1,GuildRole.LEADER),GuildMember(2,GuildRole.MEMBER)),10)
class ContractHistoryTest(unittest.TestCase):
 def setUp(self):self.u=MemoryContractHistoryUow([guild()]);self.s=GuildContractHistoryService(self.u)
 def test_legacy_target_order(self):
  c=completion_from_legacy("k1",1,{"target_mob_name":"Вовк","name":"Інше"});self.assertEqual(c.target_name,"Вовк")
 def test_missing_target_fails(self):
  with self.assertRaisesRegex(ValueError,"missing_target_name"):completion_from_legacy("k1",1,{})
 def test_apply_and_replay(self):
  c=GuildContractCompletion("k1",1,"Вовк","Герой");a=self.s.apply(c);b=self.s.apply(c);self.assertTrue(a.success);self.assertTrue(b.already_applied);self.assertEqual((len(self.u.progress),len(self.u.history_rows)),(1,1))
 def test_non_member(self):self.assertEqual(self.s.apply(GuildContractCompletion("k",9,"Вовк")).reason,"not_in_guild")
 def test_history_permissions_and_paging(self):
  for n in ("Вовк","Кабан","Павук"):self.s.apply(GuildContractCompletion("k"+n,1,n))
  page,reason=self.s.history(2,1,2,0);self.assertIsNone(reason);self.assertEqual(([x.target_name for x in page.items],page.total),(["Павук","Кабан"],3));self.assertEqual(self.s.history(9,1)[1],"permission_denied");self.assertEqual(self.s.history(1,99)[1],"guild_not_found")
 def test_page_clamp_and_out_of_range(self):
  page,_=self.s.history(1,1,500,99);self.assertEqual((page.limit,page.items),(100,()))
if __name__=="__main__":unittest.main()
