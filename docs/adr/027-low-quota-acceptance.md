# ADR-027: Explicit low-quota acceptance mode

Status: Accepted for implementation following the user's request to test at
Lambda regional concurrency 10. Date: 2026-09-29. Task: TASK-021.

Default behavior stays ADR-022: monitor reserved concurrency 1. Only an explicit
`acceptance_low_concurrency=true` dev/session setting removes this reservation
(Terraform value -1), sharing the regional unreserved pool with other functions.
Zero is never used because it disables invocation. No provisioned concurrency,
paid capacity, quota modification or service replacement is introduced.

The monitor remains read-only, scheduled every five minutes, with timeout 60s,
bounded projected Scan, alarms, tracing and existing delivery retries. This mode
does not guarantee a single monitor invocation: retries may overlap and repeat
bounded reads/approximate metrics. Use synthetic tiny tables and sequential case
journeys; retain the explicit two-request claim race. No load/concurrency-SLA
claim is valid from this mode. Throttling is possible across asynchronous fan-out;
record it, allow existing retries, and stop/clean up on failure rather than loop.

The operator guard requires at least 10 currently unreserved executions in this
mode; normal mode retains its conservative 101 headroom requirement. No guarantee
of future capacity is implied. Mode is carried into deploy and cleanup tfvars and
covered by the config/source/saved-plan fingerprints. Changing it after plan needs
a new reviewed plan. Keep application resources fresh and state bucket retained.

This is a documented temporary deviation for short acceptance, not an unnoticed
change to the normal monitor concurrency contract. Cloud evidence must name the
mode; it cannot prove default reservation isolation. All broader/long-duration
acceptance criteria remain mandatory or NOT RUN. Separate bounded deployment,
email and cleanup authorization is required under AGENTS 3.1 before execution.

Reference: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function
