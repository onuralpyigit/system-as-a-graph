# ADR-0012: Source-repository acquisition and mandatory file set

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-11-03 |
| Deciders | CDR Board |
| Consulted | Development team, software unit owners |
| Kind | Ratify |
| Traces | MDG.17–21; SMM.12–13, 20–22; QA-05 |
| Closes | CDR-10 |
| Decide by | Wave A (2026-11-27) |
| Supersedes | — |

## Context and Problem Statement

MDG.19 requires a "missing data" status when any mandatory file is missing, "whose details will be determined during the critical design phase" (CDR-10). MDG.17 requires transferring source code, installation scripts and configuration files.

As built (`mdg/src/mdg/adapters/source_code/`, `adapters/source_data/`):

* Each software unit in the Software Unit Version Inventory is cloned by tag (ADR-0010).
* `MandatoryFiles` defines two mandatory files per unit:
  * a `Makefile` anywhere under the unit directory whose non-comment content contains one of the configured include patterns (`mdg.ini`: `include/Makefile_java.mk`);
  * a topic manifest `<unit_name>.xml`.
* The `SourceCodeParser` statically parses the topic manifest (published and consumed topics) and the Java sources (imports matching a configured domain prefix and dependency suffixes → `uses` relations).
* Topic definitions and QoS come from `TypeSupportParser`, which is still a mock returning the dev seed's topics with placeholder QoS.
* Optionally (`[build] run_regenerate_code`, off by default), `GmakeBuildRunner` runs `gmake regenerate_code` in the Makefile directory as a local subprocess, with a 300 s timeout, before parsing.

## Decision Drivers

* The mandatory set must be checkable mechanically and reported per unit (MDG.19–20).
* Extraction must be deterministic and must not depend on a build toolchain on the SaaG server.
* Running repository code on the SaaG server is a security risk: it is arbitrary code from many repositories.
* The parser rules must be configurable per project without code changes.

## Considered Options

* Static parsing of the manifest and sources, with the regeneration build off by default (as built)
* Always run the unit's build to generate code, then parse
* Static parsing, plus running the regeneration build in an isolated, throw-away container when enabled

## Decision Outcome

Chosen option: "Static parsing, with the regeneration build only in an isolated container when enabled". This ratifies the as-built static extraction and mandatory set, and it closes the security gap of running `gmake` directly on the host.

* **Mandatory file set (closes CDR-10):** per software unit, the following two files must be obtained. A missing one marks the unit `missing_data` and is recorded with an error record (ADR-0034).

  | File | Rule |
  |---|---|
  | `Makefile` | Any `Makefile` under the unit directory whose non-comment content includes one of `[mandatory_files] makefile_include_patterns` |
  | `<unit_name>.xml` | The topic manifest declaring the unit's published and consumed topics |

  The system repository additionally requires the topology file of ADR-0011. Installation scripts and configuration files are acquired when present, recorded per MDG.18, and not mandatory. Adding a file to the mandatory set is a change to this ADR.
* **Extraction:** static parsing only, with the parser settings in `mdg.ini` `[source_parser]`. Parsers are ports with fakes (ADR-0003). The mocked `TypeSupportParser` must be replaced by a real parser of the units' topic type definitions before R3's QoS rules (DVE.32–35) run on real data. Until then, its placeholder QoS values are marked as such in the Model Data (ADR-0014).
* **Regeneration build:** stays off by default. When enabled, it runs in a container started per unit from a configured build image with:
  * no network;
  * a read-write bind mount of only the unit's clone;
  * CPU, memory and time limits.

  The host `gmake` subprocess path is removed.
* **Record per file (MDG.18):** file name, path, package/version, update time (as built), plus the clone commit hash (ADR-0035).

### Consequences

* Good, because CDR-10 is closed with the rule already implemented and tested.
* Good, because enabling regeneration can no longer run untrusted code on the SaaG host.
* Bad, because the containerized build needs Docker access from the worker and a maintained build image.
* Bad, because a unit that only gets correct topics after code generation will be parsed incompletely while regeneration is off. This is visible as `missing_data` or parser warnings.

### Confirmation

* `mdg/tests/adapters/test_mandatory_files.py` and `test_acquire_source_code.py` cover present, missing and comment-only include cases.
* A test asserts that the build runner adapter never invokes `gmake` on the host.

## Pros and Cons of the Options

### Static parsing, regeneration off (as built)

* Good, because it is deterministic, fast and already implemented.
* Bad, because the opt-in regeneration runs on the host.

### Always build

* Good, because generated code is always present.
* Bad, because it needs the full toolchain on the server, it is slow, and it runs arbitrary code.

### Static parsing + isolated regeneration

* Good, because it keeps the defaults and makes the opt-in safe.
* Bad, because of the container plumbing.

## More Information

* Code: `mdg/src/mdg/adapters/source_code/mandatory_files.py`, `gmake_build_runner.py`, `mdg/src/mdg/adapters/source_data/`
* Related: ADR-0010, ADR-0011, ADR-0034, ADR-0035
