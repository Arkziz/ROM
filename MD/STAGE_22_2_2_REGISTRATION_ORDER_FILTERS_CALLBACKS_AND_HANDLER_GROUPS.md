# Stage 22.2.2 registration order, filters, callbacks and handler groups

- Status: **PASS_READ_ONLY**
- Patch revision: **3**
- Parent: `dde953aa1ceb2b765dafa0cedf6e9a2a4881c22e`
- Registrations: **375**
- Handler groups: **371**
- Effective `register_*` definitions: **40**
- Registration modules: **32**
- Stage 22.2.1 exact semantic order parity: **PASS**
- Legacy fingerprint comparability: **NOT_COMPARABLE, predecessor derived-prefix defect isolated**
- Deletion authorized: **false**
- Production mutations: **NONE**
- Production SQLite opened: **false**

## Scope
Current-checkout AST audit of registration order, normalized filters, callback identities, public symbols and handler groups. Production modules were not imported and registration functions were not executed.

## Decision
`GO_TO_22_2_3_IMPORT_DIRECT_ATTRIBUTE_WRAPPER_AND_LATE_BINDING_CALL_PATH`
