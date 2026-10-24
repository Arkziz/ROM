import unittest
from rom_v2.application.guild_core_service import *
def identity(name="Варта",tag="ВРТ"):return GuildIdentity(name,name.casefold(),tag,tag.casefold(),"🏰")
class GuildCoreTest(unittest.TestCase):
 def setUp(self):self.u=MemoryGuildUow({1:100.0,2:100.0});self.s=GuildCoreService(self.u)
 def test_create_constants_and_retry(self):
  r=self.s.create(1,3,identity());self.assertTrue(r.success);self.assertEqual((r.gold_balance,r.guild.member_limit,r.guild.role_of(1)),(50.0,10,GuildRole.LEADER));self.assertEqual(self.s.create(1,3,identity("Друга","ДРГ")).reason,"already_in_guild");self.assertEqual(self.u.gold(1),50.0)
 def test_create_rejections(self):
  self.assertEqual(self.s.create(1,2,identity()).reason,"level_too_low");self.u.gold_balances[1]=49.99;self.assertEqual(self.s.create(1,3,identity()).reason,"insufficient_gold")
 def test_duplicate_identity(self):
  self.s.create(1,3,identity());self.assertEqual(self.s.create(2,3,identity()).reason,"duplicate_name");self.assertEqual(self.s.create(2,3,identity("Тінь","ВРТ")).reason,"duplicate_tag")
 def test_transfer_atomic_roles(self):
  g=self.s.create(1,3,identity()).guild;g=GuildCore(g.guild_id,g.identity,1,g.members+(GuildMember(2,GuildRole.MEMBER),));self.u.save(g);r=self.s.transfer(1,2);self.assertTrue(r.success);self.assertEqual((r.guild.leader_user_id,r.guild.role_of(1),r.guild.role_of(2)),(2,GuildRole.MEMBER,GuildRole.LEADER))
 def test_leader_leave_and_dissolve(self):
  g=self.s.create(1,3,identity()).guild;g=GuildCore(g.guild_id,g.identity,1,g.members+(GuildMember(2,GuildRole.MEMBER),));self.u.save(g);self.assertEqual(self.s.leave(1).reason,"leadership_transfer_required");self.assertTrue(self.s.leave(2).success);self.assertTrue(self.s.leave(1).dissolved);self.assertEqual(self.u.guilds,{})
 def test_permission_matrix(self):
  g=self.s.create(1,3,identity()).guild;g=GuildCore(g.guild_id,g.identity,1,g.members+(GuildMember(2,GuildRole.OFFICER),GuildMember(3,GuildRole.MEMBER)));self.assertTrue(g.can(1,"transfer"));self.assertTrue(g.can(2,"manage_applications"));self.assertFalse(g.can(2,"transfer"));self.assertFalse(g.can(3,"manage_applications"))
 def test_invariant_guard(self):
  with self.assertRaises(ValueError):GuildCore(1,identity(),1,(GuildMember(1,GuildRole.MEMBER),))
if __name__=="__main__":unittest.main()
