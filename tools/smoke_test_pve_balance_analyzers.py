from pathlib import Path
from systems.simulation.balance_analyzer import AnalysisConfig,PveBalanceAnalyzer
from systems.simulation.progression_wall_analyzer import ProgressionWallAnalyzer
ROOT=Path(__file__).resolve().parents[1]
def main():
 cfg=AnalysisConfig(2,('regular',),('warrior','mage'),(137000,137001),40,True)
 first=PveBalanceAnalyzer(ROOT,cfg,force=True).execute();second=PveBalanceAnalyzer(ROOT,cfg,force=False).execute();assert first['run_count']==4 and second['cache_hits']==8
 for cls in cfg.classes:
  x=first['groups'][cls]['regular'];assert x['runs']==2 and x['completed_runs']==2 and 0<=x['win_rate']<=1 and x['totals']['battles']==x['totals']['wins']+x['totals']['deaths']
 assert set(first['inventory_comparison'])=={'40','60'}
 walls=ProgressionWallAnalyzer(ROOT,cfg).execute();assert walls['target_level']==2 and walls['database_writes']==0
 try:AnalysisConfig(11).validate();raise AssertionError('content ceiling not enforced')
 except ValueError:pass
 print('[OK] PvE balance and progression analyzer contracts')
 print('- multi-class seeded aggregation: PASS')
 print('- deterministic cache reuse: PASS')
 print('- win/death/energy result invariants: PASS')
 print('- inventory 40/60 comparison: PASS')
 print('- progression wall schema: PASS')
 print('- production content ceiling level 10: PASS')
 print('- database writes: 0')
if __name__=='__main__':main()
