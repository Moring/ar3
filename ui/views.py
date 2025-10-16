from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from config.health import get_git_version, run_checks, uptime_seconds

def healthz(request):
    """Lightweight probe used by container orchestrators for liveness checks."""
    return HttpResponse("ok", content_type="text/plain")


def health(request):
    """Expose aggregated system health details for operators and dashboards."""
    outcomes = run_checks()
    checks_payload = {
        outcome.name: {"status": outcome.status, **outcome.details} for outcome in outcomes
    }

    statuses = {outcome.status for outcome in outcomes}
    if "error" in statuses:
        overall_status = "error"
    elif "ok" in statuses and "skipped" in statuses:
        overall_status = "degraded"
    elif statuses == {"skipped"}:
        overall_status = "unknown"
    else:
        overall_status = "ok"

    payload = {
        "status": overall_status,
        "version": get_git_version(),
        "uptime": uptime_seconds(),
        "checks": checks_payload,
    }
    return JsonResponse(payload)

def index(request):
    return render(request, "ui/index.html")

@user_passes_test(lambda u: u.is_staff, login_url="/accounts/login/")
def admin_portal(request):
    return render(request, "ui/admin_portal.html")

def partial_example(request):
    if request.headers.get("HX-Request") == "true" or request.headers.get("Hx-Request") == "true":
        return HttpResponse("<div>HTMX fragment ok</div>")
    return HttpResponse(status=400)
