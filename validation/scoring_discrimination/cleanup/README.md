# Research artifact cleanup

`plan.json` records the selected paths before cleanup. `receipts.jsonl` records actual removals and archival checks; `status.json` records completed work and allocated bytes released.

Only old simulator build products are deleted. Verilator make/source-location metadata and any non-generated C++ sources from removed build directories are retained in `build_metadata.tar.gz`. RTL, mapped Verilog, accepted ALS circuits, numeric datasets, metrics, logs and reports remain in place. Simulator binaries and generated C++/objects can be recreated by the original synthesis/simulation scripts.

Large Yosys `mapped.json` and `all.json` files are compressed to adjacent `.json.gz` files. The original is removed only after decompression reproduces its SHA-256. Restore an individual file before a tool needs the uncompressed JSON:

```bash
gzip -dk /absolute/path/to/mapped.json.gz
```

The compressed copy remains available. See the per-file receipt for its original size and hash. Current benchmark experiments, active ALS runs, input datasets and final netlists are outside the deletion scope.
