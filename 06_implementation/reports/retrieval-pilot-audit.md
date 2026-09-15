# Pilot status and technical verification

**Real pilot: not run.** The user chose to build and test runners while waiting for
reviewed corpus input. There are zero new real train/dev/test rankings. Current
corpus release has zero indexable documents/chunks; E5/BGE weights and the optional
Torch/Transformers runtime have not been provisioned or executed.

[Synthetic reproducibility evidence](retrieval-reproducibility.json) records actual
CLI commands, wall-clock durations, configuration/code/environment hashes and output
checksums. It proves the BM25 fixture repeats exactly, interrupted and complete resumes
preserve committed records, empty context stays empty, unavailable dense/hybrid
conditions stay explicit failures, and the notebook calls the same CLI successfully.
These durations concern tiny synthetic fixtures only and do not estimate pilot speed.

[Independent tests](retrieval-tests.json) cover hand-calculated BM25/RRF fixtures,
exact cosine with synthetic vectors, the real pinned E5 tokenizer and cache/checkpoint/
boundary/consumer behavior. Generic pair-truncation tests use the E5 fixture tokenizer;
they do not claim measured tokenization by the unavailable BGE tokenizer. Neural
forward passes, embedding-cache warm/cold performance and real E5/BGE rankings are
unverified. The code reports those missing resources explicitly.

Read the [runbook](../docs/retrieval-runbook.md) before the future pilot. Owner A/B
must supply the reviewed corpus and update pinned input hashes; B/C must provision
verified model assets/runtime; 06 supplies the five-incident train smoke, twenty-train
pilot and eighteen-dev allowlists. Record real repeat/resume evidence and consumer
review before accepting 05.runners. Plan08 owns dev selection, optional reranker
inclusion, F1 and actual test execution. No winner or quality score is recorded here.
