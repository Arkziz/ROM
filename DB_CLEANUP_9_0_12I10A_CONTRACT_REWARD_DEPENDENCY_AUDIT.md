# ROM 9.0.12i10a - Contract Reward Dependency Audit

## Structural result

- db.py definitions: 2; lines: [1722, 7106]
- Base signature: `(user_id)`
- Public signature: `(user_id)`
- System signature: `(user_id)`
- Capture block count: 1
- Final db calls: ['_base_claim_contract_reward_before_guild_reward_v1', '_guild_contract_reward_append_message_v1', '_guild_contract_reward_result_success_v1', 'award_guild_contract_completion', 'get', 'get_active_contract', 'print']
- System calls: ['_claim_contract_reward_base', '_contract_result_success', 'award_guild_contract_completion', 'get', 'get_active_contract', 'get_guild_activity_reward_text', 'isinstance', 'print', 'rstrip', 'str', 'strip']
- Consumers: ['handlers/contracts.py:273']

## Runtime read-only result

- Missing-user public/system/base comparisons: 2
- Mismatches: 0
- Database rows created: 0

## Conclusion

`systems.contract_system.claim_contract_reward` already contains a direct base claim plus Guild reward hook. The final db.py override still depends on an obsolete capture of the earlier db.py implementation.

Recommended sequence:

1. i10b: switch final db.py claim_contract_reward to a thin contract_system facade and run isolated mutation equivalence tests while retaining the old implementation/capture for rollback.
2. i10c: remove the earlier db.py definition and obsolete capture, leaving a single facade definition.
