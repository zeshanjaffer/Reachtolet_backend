#!/usr/bin/env python
"""
Smoke-test main HTTP routes and print response times (median of 3 requests).

Usage:
  Postgres (default settings):  .\\env\\Scripts\\python.exe manage.py migrate
                                .\\env\\Scripts\\python.exe scripts\\api_smoke_benchmark.py
  Local SQLite:  $env:DJANGO_USE_SQLITE='1'; .\\env\\Scripts\\python.exe manage.py migrate
  Optional seed (minimal user + approved billboard for authed routes):
                 $env:API_BENCH_SEED='1' (with DJANGO_USE_SQLITE if using SQLite)

Uses Django's APIClient (no running runserver required).
"""
from __future__ import annotations

import os
import statistics
import sys
import time

# Project root on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")


def _timed(client, method: str, path: str, *, auth_user=None, data=None, format=None):
    if auth_user is not None:
        client.force_authenticate(user=auth_user)
    else:
        client.force_authenticate(user=None)

    durations_ms = []
    last_status = None
    for _ in range(3):
        t0 = time.perf_counter()
        fn = getattr(client, method.lower())
        if method == "GET":
            response = fn(path, format=format)
        else:
            response = fn(path, data=data or {}, format=format or "json")
        durations_ms.append((time.perf_counter() - t0) * 1000)
        last_status = response.status_code
    return {
        "status": last_status,
        "median_ms": round(statistics.median(durations_ms), 2),
        "min_ms": round(min(durations_ms), 2),
        "max_ms": round(max(durations_ms), 2),
    }


def main() -> int:
    import django

    django.setup()

    from django.conf import settings
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient

    from billboards.models import Billboard

    User = get_user_model()
    client = APIClient()

    if os.environ.get("API_BENCH_SEED") == "1":
        u, created = User.objects.get_or_create(
            email="api-bench@local.test",
            defaults={
                "full_name": "API Bench",
                "country_code": "US",
                "phone": "+12025550123",
                "user_type": "media_owner",
                "is_active": True,
            },
        )
        if created:
            u.set_password("bench-pass-not-for-prod")
            u.save()
        if not Billboard.objects.filter(city="BenchCity").exists():
            Billboard.objects.create(
                user=u,
                city="BenchCity",
                description="Bench",
                ooh_media_type="Digital",
                type="Roadside",
                approval_status="approved",
                is_active=True,
                latitude=1.0,
                longitude=1.0,
                images=["https://example.com/bench.jpg"],
            )

    billboard_id = (
        Billboard.objects.filter(is_active=True, approval_status="approved")
        .values_list("id", flat=True)
        .first()
    )
    if billboard_id is None:
        billboard_id = Billboard.objects.values_list("id", flat=True).first()

    user = User.objects.filter(is_active=True).first()

    tests: list[tuple[str, str, dict]] = [
        ("GET", "/api/users/health/", {}),
        ("GET", "/api/users/country-codes/", {}),
        ("GET", "/api/billboards/", {}),
    ]

    if billboard_id is not None:
        tests.append(("GET", f"/api/billboards/{billboard_id}/", {}))

    if user is not None:
        tests.extend(
            [
                ("GET", "/api/users/profile/", {"auth_user": user}),
                ("GET", "/api/notifications/notifications/", {"auth_user": user}),
                ("GET", "/api/notifications/stats/", {"auth_user": user}),
                ("GET", "/api/notifications/preferences/", {"auth_user": user}),
                ("GET", "/api/billboards/my-billboards/", {"auth_user": user}),
                ("GET", "/api/billboards/wishlist/", {"auth_user": user}),
                ("GET", "/api/admin-panel/admin/campaigns/", {"auth_user": user}),
                ("GET", "/api/admin-panel/admin/templates/", {"auth_user": user}),
                ("GET", "/api/admin-panel/admin/users/", {"auth_user": user}),
            ]
        )

    print(f"Database engine: {settings.DATABASES['default']['ENGINE']}")
    print(f"Billboard sample id: {billboard_id!r}  User sample: {getattr(user, 'email', None)!r}\n")
    print(f"{'METHOD':<6} {'STATUS':>6} {'med(ms)':>8} {'min':>8} {'max':>8}  PATH")
    print("-" * 72)

    failures = 0
    for method, path, kwargs in tests:
        try:
            r = _timed(client, method, path, **kwargs)
        except Exception as e:
            print(f"{method:<6} {'ERR':>6} {'—':>8} {'—':>8} {'—':>8}  {path}  ({e})")
            failures += 1
            continue
        # 403/401 often expected (role, token); 404 if empty resource
        ok = r["status"] in (200, 201, 204, 301, 302, 401, 403, 404)
        if not ok:
            failures += 1
        print(
            f"{method:<6} {r['status']:>6} {r['median_ms']:>8} {r['min_ms']:>8} {r['max_ms']:>8}  {path}"
        )

    print("-" * 72)
    if failures:
        print(f"Done with {failures} failing or non-2xx/3xx routes (403/401 may be expected for role).")
    else:
        print("All reported routes returned success (2xx) or expected auth/role codes.")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
