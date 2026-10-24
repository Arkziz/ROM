import unittest
from rom_v2.application.guild_management_service import *
from rom_v2.domain.guild_core import GuildIdentity
def guild():return GuildCore(1,GuildIdentity("Варта","варта","ВРТ","врт","🏰"),1,(GuildMember(1,GuildRole.LEADER),GuildMember(2,GuildRole.OFFICER),GuildMember(3,GuildRole.MEMBER)),10)
def application():return GuildApplication(1,1,4)
class ManagementTest(unittest.TestCase):
 def setUp(self):self.u=MemoryManagementUow([guild()],[application()],{4:3},{1:2});self.s=GuildManagementService(self.u)
 def test_accept_and_replay(self):
  r=self.s.accept(2,1);self.assertTrue(r.success);self.assertEqual(r.guild.role_of(4),GuildRole.MEMBER);self.assertEqual(self.s.accept(2,1).reason,"already_processed")
 def test_accept_rechecks(self):
  self.u.levels[4]=2;self.assertEqual(self.s.accept(1,1).reason,"level_too_low");self.u.levels[4]=3;self.u.cooldowns.add(4);self.assertEqual(self.s.accept(1,1).reason,"join_cooldown")
 def test_reject_replay(self):
  self.assertTrue(self.s.reject(2,1).success);self.assertEqual(self.s.reject(1,1).reason,"already_processed")
 def test_promote_limit_permission(self):
  self.assertTrue(self.s.promote(1,3).success);self.u.guilds[1]=guild();self.u.officer_limits[1]=1;self.assertEqual(self.s.promote(1,3).reason,"officer_limit_reached");self.assertEqual(self.s.promote(2,3).reason,"permission_denied")
 def test_kick_protections(self):
  self.assertEqual(self.s.kick(2,1).reason,"target_is_leader");self.assertEqual(self.s.kick(2,2).reason,"self_target");self.assertTrue(self.s.kick(2,3).success);self.assertEqual(self.u.departures,[(3,1,"kicked",2)])
 def test_application_invariant(self):
  with self.assertRaises(ValueError):GuildApplication(1,1,4,ApplicationStatus.ACCEPTED)
if __name__=="__main__":unittest.main()
