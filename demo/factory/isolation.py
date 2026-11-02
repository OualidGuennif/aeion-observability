"""Qualified Docker isolation for protected candidate checks (brief item B6).

Candidate code runs in a disposable container with no network, no Docker socket, no host
home and no controller tree. Only the candidate repository and read-only toolchain caches
are mounted; the environment is fixed here, never inherited. A probe must pass before any
check runs, and its evidence is recorded with the check result. Missing Docker, a moved
image or a failed probe holds the build instead of falling back to the host.

The image is the local Maven/JDK image already used by the build; its identity is pinned by
the digest reported at qualification time. Nothing is pulled: an absent image is a hold.
"""
import os
import subprocess
import tempfile
from pathlib import Path

DEFAULT_IMAGE = "maven:3.9-eclipse-temurin-25"
CONTAINER_JAVA_HOME = "/opt/java/openjdk"
CONTAINER_PATH = CONTAINER_JAVA_HOME + "/bin:/usr/local/bin:/usr/bin:/bin"
PROBE_SENTINEL = "AEION_ISOLATION_PROBE_SENTINEL"


class IsolationError(RuntimeError):
    """The isolation boundary is not available or not proven."""


class DockerCheckRunner:
    def __init__(self, controller, image=DEFAULT_IMAGE, docker="docker",
                 tools_dir=None, cache_dir=None, user="65534:65534",
                 memory="3g", cpus=2, pids_limit=512):
        self.controller = Path(controller).resolve()
        self.controller_path = str(Path(controller))
        self.image = image
        self.docker = docker
        raw_tools = Path(tools_dir) if tools_dir else Path(self.controller_path) / "demo/.local/tools"
        self.tools_path = str(raw_tools)
        self.tools_dir = raw_tools.resolve()
        self.cache_dir = Path(cache_dir or self.controller / "demo/.local/gradle-home/caches").resolve()
        self.user = user
        self.memory = memory
        self.cpus = int(cpus)
        self.pids_limit = int(pids_limit)
        self._qualification = None

    # ------------------------------------------------------------- qualification
    def image_id(self):
        try:
            completed = subprocess.run(
                [self.docker, "image", "inspect", "--format", "{{.Id}}", self.image],
                capture_output=True, text=True, timeout=30,
                env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")})
        except (OSError, subprocess.TimeoutExpired):
            raise IsolationError("docker_unavailable") from None
        image_id = (completed.stdout or "").strip()
        if completed.returncode != 0 or not image_id.startswith("sha256:"):
            raise IsolationError("image_unavailable")
        return image_id

    def _flags(self, workspace, image=None):
        return [
            self.docker, "run", "--rm", "--network", "none", "--read-only",
            "--user", self.user, "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--pids-limit", str(self.pids_limit), "--memory", self.memory,
            "--cpus", str(self.cpus), "--tmpfs", "/tmp:rw,exec,size=1g",
            "-v", f"{workspace}:/workspace",
            "-v", f"{self.tools_dir}:/tools:ro",
            "-v", f"{self.cache_dir}:/ro-cache:ro",
            "-e", "HOME=/tmp", "-e", "TMPDIR=/tmp",
            "-e", "GRADLE_USER_HOME=/tmp/gradle", "-e", "GRADLE_RO_DEP_CACHE=/ro-cache",
            "-e", f"JAVA_HOME={CONTAINER_JAVA_HOME}", "-e", f"PATH={CONTAINER_PATH}",
            "-e", f"{PROBE_SENTINEL}=", "-w", "/workspace", image or self.image,
        ]

    def qualification(self, refresh=False):
        """Prove the boundary once per runner: non-root, no socket, no network, no host env."""
        if self._qualification is not None and not refresh:
            return self._qualification
        if not self.tools_dir.is_dir() or not self.cache_dir.is_dir():
            raise IsolationError("toolchain_cache_missing")
        image_id = self.image_id()
        script = (
            "set -eu; "
            "test \"$(id -u)\" != 0; "
            "test ! -e /var/run/docker.sock; "
            "test -z \"${" + PROBE_SENTINEL + ":-}\"; "
            "if timeout 2 bash -c 'exec 3<>/dev/tcp/1.1.1.1/443' 2>/dev/null; "
            "then echo network=reachable; exit 3; else echo network=denied; fi; "
            "echo probe=ok"
        )
        try:
            with tempfile.TemporaryDirectory(prefix="aeion-isolation-probe-") as workspace:
                completed = subprocess.run(
                    # Probe the same digest execution will use: a tag re-pointed between the
                    # inspect and this run must not qualify different bytes than it records.
                    self._flags(workspace, image=image_id) + ["bash", "-c", script],
                    capture_output=True, text=True, timeout=60,
                    env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")})
        except (OSError, subprocess.TimeoutExpired):
            raise IsolationError("probe_did_not_run") from None
        if completed.returncode != 0 or "probe=ok" not in (completed.stdout or ""):
            raise IsolationError("probe_failed")
        self._qualification = {
            "status": "qualified",
            "engine": "docker",
            "image": self.image,
            "image_id": image_id,
            "network": "none",
            "root_filesystem": "read_only",
            "user": self.user,
            "capabilities": "none",
            "mounts": ["candidate_workspace", "tools_read_only", "dependency_cache_read_only"],
            "limits": {"memory": self.memory, "cpus": self.cpus, "pids": self.pids_limit},
            "probe": {"network": "denied", "docker_socket": "absent",
                      "host_environment": "absent", "root": "no"},
        }
        return self._qualification

    # ----------------------------------------------------------------- execution
    def translate(self, argument, repo):
        """Map the manifest's controller/repository paths into the container's mounts."""
        text = str(argument)
        for prefix, mount in ((str(Path(repo)), "/workspace"),
                              (str(Path(repo).resolve()), "/workspace"),
                              (self.tools_path, "/tools"), (str(self.tools_dir), "/tools")):
            if text == prefix or text.startswith(prefix + os.sep):
                return mount + text[len(prefix):]
        if text.startswith(self.controller_path) or text.startswith(str(self.controller)):
            raise IsolationError("controller_path_not_mountable")
        return text

    def __call__(self, command, cwd, env=None, timeout=None, **kwargs):
        """subprocess.run-compatible call; the host environment and cwd are not forwarded."""
        qualification = self.qualification()
        repo = Path(cwd).resolve()
        try:
            translated = [self.translate(part, repo) for part in command]
        except IsolationError:
            raise
        # Run the digest the probe qualified, not the mutable tag: a re-tagged or re-pulled
        # tag after qualification must not silently execute different bytes.
        argv = self._flags(repo, image=qualification["image_id"]) + translated
        completed = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")})
        completed.qualification = qualification
        return completed
