# Corpus debugger findings and resolution

Final technical result: **pass**, with no outstanding implementation defect in the exercised contract. [Tests](corpus-tests.json) bind the final code and candidate `5c038293ce2ee69a42277170e18dd9c88417aff7e5c0aa127f034438803e23f3` to 60 passing corpus checks. The final candidate's eight artifact hashes equal a fresh test build and a separate isolated-process replay. The 100 existing data/protocol checks also pass.

The initial preflight independently reran the plan02 source, inference, and receipt checks. Its technical contract passed for 90 incidents and 360 source inventory files. Requiring human review correctly failed `HUMAN_REVIEW_PENDING`. The user's subsequent instruction authorized the local corpus candidate while retaining that release boundary. No upstream human receipt was replaced or signed.

| Finding during implementation/review | Resolution and evidence |
|---|---|
| Outer hashes alone would not reject semantic lineage/ID/provenance tampering | Validator recomputes chunk identities and source/citation joins, old/new lineage spans and relations; rehashed negative fixtures now fail |
| Citation metadata needed complete agreement with chunks | Rehashed attacks on applicability, attribution, license, source identity, review state and offset units fail |
| Removing a chunk could be concealed by rebuilding derivative summaries and lineage | Validator checks content coverage; the full-rehash dropped-chunk fixture fails despite consistent summaries |
| Initial license stripping could consume adjacent technical comments | Normalization stops at the license footer; YAML and proto fixtures retain the following technical comment exactly |
| Fenced code and indented YAML include comments needed parser boundaries | Trailing-text fences stay open; source origin at the actual heading marker prevents YAML comments becoming Markdown sections |
| Configuration could advertise unsupported transform behavior | Unsupported normalization settings and incompatible decision versions are rejected |

Implementation fixes were made by their owning agents; the tester only changed its two new test files and reports. The first full run passed 47 tests; the final suite expanded to 60 after review findings. An early tokenizer fixture transcription mistake was corrected against the previously recorded exact provisioning token IDs. The atomic publication fixture was adjusted to the builder's documented stage naming rule. Neither adjustment removed an assertion or changed an implementation acceptance condition.

Raw/corpus source files, existing labels, data/protocol code and upstream receipts remained unchanged. Synthetic receipt tests clearly identify fixture actors and never write a human approval. Technical offsets, hashes and coverage of stored text do not establish incident relevance, deployment compatibility, semantic evidence coverage, or release authorization.
