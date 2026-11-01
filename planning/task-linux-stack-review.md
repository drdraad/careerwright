# Review: the local stack on a Linux Docker host (58c8f99..d7c5ac7)

Reviewer: the one independent reviewer (R16). Read-only. No Docker used, no tests run, no
secret or environment value read. The diff is 820 lines; read in two passes. Code outside the
diff was read only for the named risks below.

### Spec Compliance
- ✅ Spec compliant. All four dispatch rules hold in the code: host files stay owner-only
  (`localenv.py` untouched, the new stack test re-checks it); each container copies only what
  Compose gives it (Compose `secrets:` and `volumes:` lines unchanged); the Mac path is the
  same mechanism (root reads the bind mount, chown on a tmpfs); no value is printed, passed
  as an argument, put in the environment or in an image layer. The choice and why are in the
  ADR 0004 amendment.
- ⚠️ Cannot verify from diff: that it actually runs. Nothing here has run on Docker
  (`make acceptance`, integration and stack tests: not run; the controller is running
  acceptance now). In particular: that Compose accepts the short tmpfs option string, that
  postgres first-init reads the copies, that the new stack test passes, and that Docker
  Desktop on the Mac still works (not run, requires the Mac).

### The named risks, one by one
1. **Privilege drop complete and irreversible** (safety): holds.
   `entrypoint.py:80-85` calls `setgroups([])`, then `setgid`, then `setuid`, then `execvp`.
   `setuid` from root sets real, effective and saved uid, and clears every capability, so it
   cannot be undone. Python opens files non-inheritable and the copy closes each one, so no
   descriptor survives the exec. The copies are 0400 on a `nosuid,noexec` tmpfs, so nothing
   setuid is created. The stack test checks all four uid fields of the service process and
   its empty group list (`test_local_stack.py:446`). Postgres is unchanged in kind: the image
   always started as root and dropped through `gosu`. The image's stock setuid binaries
   (`su`, `mount` and so on) were reachable by the service user before this change too; see
   Minor 4.
2. **Each container copies only its own, into tmpfs, 0400/0500, owned by the service user**
   (safety): holds. The copy reads only `/run/secrets`, `/run/careerwright/keys` and
   `/run/careerwright/adzuna`, and a container has only what Compose mounted there. The
   acquisition worker still has no `secrets:` entry and one read-only mount (`adzuna`); the
   `edge`, `web` and `auth` services are unchanged. Files are created `O_EXCL` 0400 and
   `fchown`ed before any byte is written; folders end 0500. The tmpfs check is weaker in
   Python than in the postgres script (Minor 1).
3. **No value printed, logged, passed as an argument or in an image** (safety): holds. Both
   entrypoints copy file to file (`read_bytes`/`write`, `install`); no `set -x`; nothing
   logged; the Dockerfile is unchanged; the postgres script is a read-only bind mount, not
   baked in.
4. **Failure is loud** (safety): holds for every case I could build. Not root, or no mount
   at the private path: the container exits with a clear message. A secret root cannot read
   (for example under `userns-remap`): a `PermissionError` stops it. A missing host secret
   file: Compose refuses to start. A missing keys folder: `load_keyring` stops the api and
   worker. Postgres: `set -euo pipefail`, and an empty `/run/secrets` leaves the glob
   literal, so `install` fails. An empty password file behaves exactly as before. One quiet
   path: a non-regular entry is skipped (Minor 2).
5. **Key rotation and reseal reach the running api** (safety): holds. `tools/stack.py:155-163`
   restarts the api and worker with `compose restart`, which runs the entrypoint again, and
   the copy removes the old folder first (unit test `test_a_restart_copies_afresh...`). The
   api and worker load the keyring once at start (`api/main.py:25`, `worker.py:133`), so
   nothing relied on reading the bind mount live. Reseal runs in a fresh `migrate` container
   through `compose run`, which keeps the entrypoint and tmpfs.
6. **Docker Desktop on the Mac** (list): should work by reasoning, not run. Root in the
   Desktop VM reads virtiofs bind mounts, and chown on a tmpfs is local to the VM.
7. **Health checks and `docker compose exec` now run as root** (safety): a small, acceptable
   widening for a loopback-only local app. Anyone who can `exec` already controls the Docker
   daemon, which is root on the host. The health checks are fixed image commands; the api and
   acquisition ones are a plain HTTP request. I checked the one route a compromised service
   could use to get root code run by a root check: `python -m` puts the working folder first
   on the import path. `/app` and `/app/src` are root-owned from the build and
   `PYTHONDONTWRITEBYTECODE=1` is set (`backend/Dockerfile`), so the service user cannot
   plant a module there. The exec-based stack tests (the secret scan, egress probes) now run
   as root, which can only see more, so they got stricter, not weaker.
8. **The two changed stack-test expectations** (truth): justified.
   - Acquisition mounts (`test_local_stack.py:304`): only `tmpfs` entries are dropped; the
     only host mount must still be the Adzuna folder, read-only. A tmpfs carries no host
     data. Short-syntax tmpfs does not appear in `Mounts` anyway, so the filter is a no-op
     today (Minor 3 for a tighter form).
   - Worker positive control: it now also expects the private copies. This adds to the
     control; the acquisition side still needs zero hits, and the scan now runs as root.
9. **ADR 0004's amendment is true**: mostly. Every mechanism it describes matches the code
   and compose. Two sentences overstate (Minor 5).

### Strengths
- The design is the right size: one stdlib module, one shell script, one Compose anchor. The
  keys folder, whose file count varies, is why Compose's secret `uid/gid/mode` could never be
  the whole answer; the ADR says so.
- The copy is careful: `O_EXCL`, owner set before content, folders closed to 0500 only after
  the copy, the old copy removed so a dropped key does not linger.
- The new stack test proves the drop on the real process (all uid fields, groups) and lists
  each container's copies exactly, including that the acquisition worker holds no secret or
  key copy.
- Postgres keeps its own entrypoint and drop; only a copy step runs first.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. `backend/src/careerwright/entrypoint.py:77` (safety). The check is `os.path.ismount`,
   so any mount passes, including a disk volume. Its message and the runbook
   (`docs/runbook.md:312`) say "is not a tmpfs mount". If a later change swapped the tmpfs
   for a volume, the copies would go to disk with no warning. The postgres script already
   checks the type through `/proc/mounts`. Fix: read the mount's type from `/proc/mounts`
   and require `tmpfs`, as the shell script does, with a unit test.
2. `backend/src/careerwright/entrypoint.py:46,55` (list). A location that is missing, and
   a non-regular entry (a folder, a broken link), are skipped silently. Downstream failures
   are loud today (`load_keyring`, the password-file read), so this is polish. Fix: name
   what was skipped on stderr (names only), or refuse a non-regular entry.
3. `backend/tests/stack/test_local_stack.py:304` and `:413-446` (list). The mount filter
   would accept a tmpfs at any path; and the privilege check reads `Uid` and `Groups` but
   not `Gid` or `CapEff`. Fix: assert the tmpfs destinations are exactly
   `/run/careerwright/private`, and add the `Gid` fields and `CapEff == 0` to the view.
4. `compose.yaml:35-36` (safety, list). The service user can still run the image's stock
   setuid binaries, as before this change. Now that the containers start as root, adding
   `security_opt: ["no-new-privileges:true"]` to the anchor costs nothing (the root-to-user
   drop and `gosu` both work under it). Not a regression; a hardening for the controller to
   weigh.
5. `docs/adr/0004-local-runtime-and-security-boundary.md:200,204-205` (truth). Line 204
   states as fact that Compose "has bind-mounted the file and ignored" `uid/gid/mode`, then
   line 205 says it is not proven. Say it is what Compose's documentation describes and was
   not tested here. Line 200's "under rootless Docker" is also untested; and under
   `userns-remap` (container root mapped to another host uid) root cannot read owner-only
   files, so the stack fails at start. Add that one sentence so the next reader knows it
   fails loudly there.

### Assessment
**Task quality:** Approved
**Reasoning:** The drop is complete and irreversible, each container copies only its own
files into memory for its service user, nothing leaks, and failures stop the container. It
stays unverified until the controller's acceptance run passes on this Linux host; the Mac is
not run and needs the product owner's machine.
