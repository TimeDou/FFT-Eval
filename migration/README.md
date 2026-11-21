# Repository migration

All pre-migration FFT-Bench branch tips and reachable commits are retained in FFT-Eval, including local experimental branches. `HISTORY_MANIFEST.json` records the exact refs, object IDs and backup bundle hash. Archive tags preserve original commit IDs without rewriting history. Main's archive merge also makes every old reachable commit an ancestor.

FFT-Eval must remain private and unavailable to evaluated agents. Agent result branches are operator-maintained records, not independently protected read scopes. The public FFT-Bench will contain only a new clean main commit with the current public task/tools and no evaluator history, submissions, scores or private test state.

Deletion of remote branches and a new root commit remove access through normal clones/history. They cannot revoke existing clones or guarantee immediate removal of cached GitHub objects addressed by old SHA. Use fresh clones and separate operator credentials/mounts.
