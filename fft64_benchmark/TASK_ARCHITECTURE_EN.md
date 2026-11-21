# FFT64-Quant architecture and precision optimization

Follow TASK_EN.md. In v0.5 the default task already uses the paper's 60% area / 30% measured sustained throughput / 10% maximum first-output latency objective.

Every FFT remains 64 points. Public numerical tests use at least 1,024 independent nonzero frames; every officially tested II uses at least 1,024 consecutive frames. Capacity comes from measured passing intervals, not a design_config declaration. Failure at an optional shorter II does not invalidate mandatory II=384 service.

Use public numerical and sustained-protocol validation, then hardware measurements, and update the design plan from actual results. See SCORING.md.
