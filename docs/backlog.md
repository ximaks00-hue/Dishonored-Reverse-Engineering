# Research backlog

These are questions, not established facts. Priority reflects dependency and discriminating value, not expected completion time.

| Priority | Question | Evidence required | Suggested contribution |
| --- | --- | --- | --- |
| P0 | Is the registered build identity reproducible from an available local install? | Exact executable and manifest hashes, architecture, edition and provenance | Re-run the build check without committing game files |
| P0 | Which parts of the published evidence can another contributor reproduce? | Source/input availability, tool versions, output hashes and known limits | Reproduce EXP-0114 or selected native catalog checks |
| P1 | How is `BasedOn` resolved at runtime? | Controlled distinguishing observation or trace tied to a build | Hypothesis and EXP design |
| P1 | How does the game resolve `BasedOn` and config path declarations at runtime? | Controlled observation that distinguishes candidate bases | Design and execute a build-matched runtime experiment |
| P1 | Can repository records be validated automatically? | Synthetic fixtures and CI | Extend validation script |
| P2 | Which package readers parse sampled files reliably? | Build-bound input hashes, parser versions and failure cases | Compatibility matrix |
| P2 | Which native function matters to a selected behavior? | Build/module hash, RVA, references and falsifying evidence | Function record |

A task is ready when it has a bounded question, accessible prerequisites, and testable completion criteria. Put execution details into issues rather than inflating this index. Close or supersede answered questions with evidence links.
