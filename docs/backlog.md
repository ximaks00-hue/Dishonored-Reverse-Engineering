# Research backlog

These are questions, not established facts. Priority reflects dependency and discriminating value, not expected completion time.

| Priority | Question | Evidence required | Suggested contribution |
| --- | --- | --- | --- |
| P0 | What exact installed build is studied? | Executable/module SHA-256, architecture, edition, OS and acquisition method | BUILD record and read-only inventory |
| P0 | Where are the locally reported experiments and scripts? | Audited files, commit provenance, reproducible outputs | Import with source verification |
| P1 | How is `BasedOn` resolved at runtime? | Controlled distinguishing observation or trace tied to a build | Hypothesis and EXP design |
| P1 | Which config candidates are ambiguous? | Full input manifest and deterministic match report | Re-run EXP-0114 if obtained |
| P1 | Can repository records be validated automatically? | Synthetic fixtures and CI | Extend validation script |
| P2 | Which package readers parse sampled files reliably? | Build-bound input hashes, parser versions and failure cases | Compatibility matrix |
| P2 | Which native function matters to a selected behavior? | Build/module hash, RVA, references and falsifying evidence | Function record |

A task is ready when it has a bounded question, accessible prerequisites, and testable completion criteria. Put execution details into issues rather than inflating this index. Close or supersede answered questions with evidence links.
