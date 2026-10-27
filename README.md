# gsched

GPU airtime scheduling for one machine, plus `hwq`, a wrapper that runs queued jobs through [pueue](https://github.com/Nukesor/pueue) with a GPU lease.

Several people or agents sharing a few GPUs step on each other. `gsched` makes the GPU a booked resource:
a job books minutes and VRAM, is placed by priority class, waits in a queue when the card is busy, and can preempt a lower class
that opted in (`--restartable`, with an optional checkpoint command). `gsched run` executes the command in a systemd user unit
with `CUDA_VISIBLE_DEVICES` pinned and releases the lease on exit.

## Install

Needs Python 3.9+, `nvidia-smi`, and for `run` a systemd user session. For `hwq` also `pueue`.
Copy `bin/gsched` and `bin/hwq` onto your `PATH`.

## Configure

```
mkdir -p ~/.local/state/gsched
cp gsched.conf.example ~/.local/state/gsched/gsched.conf   # ROLE=CLASS lines
```

`GSCHED_DIR` moves the state directory, `GSCHED_SMI` replaces the `nvidia-smi` command. Run `gsched tick` from a timer every minute so queued bookings start and overdue ones end.
`hwq` reads `HWQ_MAX_C` (refuse above this GPU temperature, default 70) and `HWQ_WAIT` (seconds to wait for airtime, default 900).

## Example

```
gsched book training --vram 12 --mins 90 --reason "fine-tune run"      # prints: lease 1 active on gpu 0 ...
gsched run batch --vram 8 --mins 30 -- python3 job.py                    # books, runs, releases
hwq --role batch --vram 8 gpu0 nightly -- python3 job.py                 # same through pueue, group gpu0
gsched ls; gsched release 1
```

## Tests

`python3 -m unittest discover -s tests` uses a fake `nvidia-smi` and needs no GPU.

## License

Apache-2.0, see `LICENSE` and `NOTICE`.
