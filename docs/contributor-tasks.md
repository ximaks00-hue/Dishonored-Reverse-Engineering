# Small contributor tasks

These tasks are real, scoped GitHub issues. Check their prerequisites before starting: two can be done with Python and repository files only; the EXP-0114 reproduction requires the registered local build.

| Task | Access needed | Done when |
| --- | --- | --- |
| [#20 Independently reproduce the EXP-0014 report/index check](https://github.com/ximaks00-hue/Dishonored-Reverse-Engineering/issues/20) | Repository only; no game install or Ghidra | A review note records an independent method, source digest, checked rows and limits. |
| [#21 Add anchor parser regression cases](https://github.com/ximaks00-hue/Dishonored-Reverse-Engineering/issues/21) | Python 3.11; synthetic fixtures only | Tests cover headings, explicit IDs and code fences; repository validation passes. |
| [#22 Reproduce one EXP-0114 audit slice](https://github.com/ximaks00-hue/Dishonored-Reverse-Engineering/issues/22) | Exact registered Steam build `10256413` | A review note records one `BasedOn` and one path candidate with hash-checked inputs and no runtime claim. |

Use the issue's acceptance checklist and open a focused PR linked to it. If a prerequisite is unavailable, pick another task rather than weakening the build scope. For more examples and the review protocol, see the [contributor playbook](contributor-playbook.md).
