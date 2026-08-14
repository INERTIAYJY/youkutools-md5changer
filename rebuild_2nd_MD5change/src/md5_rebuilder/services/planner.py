from __future__ import annotations

from pathlib import Path

from md5_rebuilder.core.models import RenderJob, RenderProfile, VideoMeta
from md5_rebuilder.core.naming import next_target_path


class JobPlanner:
    def plan(self, metas: list[VideoMeta], profile: RenderProfile) -> list[RenderJob]:
        jobs: list[RenderJob] = []
        for meta in metas:
            target = next_target_path(meta.path, profile)
            while any(job.target == target for job in jobs):
                target = _bump(target)
            jobs.append(
                RenderJob(
                    source=meta.path,
                    target=target,
                    profile=profile,
                    source_duration=meta.duration,
                )
            )
        return jobs


def _bump(path: Path) -> Path:
    stem = path.stem
    if "_" in stem and stem.rsplit("_", 1)[1].isdigit():
        base, number = stem.rsplit("_", 1)
        return path.with_name(f"{base}_{int(number) + 1}{path.suffix}")
    return path.with_name(f"{stem}_1{path.suffix}")

