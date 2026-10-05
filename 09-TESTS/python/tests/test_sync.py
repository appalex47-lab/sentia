from pathlib import Path
from python.pipeline.sync import canonical_external_id, deduplicate_rows, merge_sync_state, load_state, save_state, build_sync_run


def test_canonical_external_id_is_stable():
    assert canonical_external_id("linkedin-post", "urn:li:share:1") == "linkedin-post:urn:li:share:1"
    assert canonical_external_id("x", "123") == "x:123"


def test_deduplicate_rows_is_idempotent():
    rows=[{"id_mencion":"x:1","texto_original":"uno"},{"id_mencion":"x:1","texto_original":"uno"},{"id_mencion":"x:2","texto_original":"dos"}]
    unique, duplicates=deduplicate_rows(rows)
    assert len(unique)==2 and duplicates==1


def test_sync_state_records_error_without_erasing_last_success():
    previous=merge_sync_state(None,status="success",source_count=3)
    failed=merge_sync_state(previous,status="error",error="RATE_LIMIT")
    assert failed["last_sync_at"] == previous["last_sync_at"]
    assert failed["error"] == "RATE_LIMIT"


def test_sync_state_persists(tmp_path):
    p=tmp_path/"sync.json"
    save_state(p,{"x":{"status":"success"}})
    assert load_state(p)["x"]["status"] == "success"


def test_build_sync_run_success():
    run = build_sync_run("r1", 10, 11.25, ["x"], [{"provider":"x","ok":True,"source_count":4,"duplicate_count":2}], [])
    assert run["status"] == "success"
    assert run["duration_ms"] == 1250
    assert run["source_count"] == 4 and run["duplicate_count"] == 2


def test_build_sync_run_partial():
    run = build_sync_run("r2", 10, 11, ["x","youtube"], [{"provider":"x","ok":True,"source_count":1},{"provider":"youtube","ok":False,"error":"RATE_LIMIT"}], [{"provider":"youtube","error":"RATE_LIMIT"}])
    assert run["status"] == "partial"
    assert run["failure_count"] == 1


def test_build_sync_run_error():
    run = build_sync_run("r3", 10, 10.5, ["x"], [{"provider":"x","ok":False}], [{"provider":"x","error":"NOT_CONNECTED"}])
    assert run["status"] == "error"


def test_sync_run_is_bounded_by_consumer_limit():
    run = build_sync_run("r4", 1, 2, ["x"], [], [])
    assert run["requested_providers"] == ["x"]


def test_retry_sync_call_retries_transient_error_with_exponential_backoff():
    from python.pipeline.sync import retry_sync_call
    from python.connectors.social import SocialConnectorError
    attempts=[]; sleeps=[]
    def call():
        attempts.append(len(attempts)+1)
        if len(attempts) < 3:
            raise SocialConnectorError("HTTP_503")
        return "ok"
    value, used = retry_sync_call(call, attempts=3, base_delay=0.1, sleep=sleeps.append)
    assert value == "ok" and used == 3
    assert sleeps == [0.1, 0.2]


def test_retry_sync_call_does_not_retry_permanent_error():
    from python.pipeline.sync import retry_sync_call
    from python.connectors.social import SocialConnectorError
    calls=[]
    def call():
        calls.append(1)
        raise SocialConnectorError("HTTP_401")
    try:
        retry_sync_call(call, attempts=3, sleep=lambda _: None)
    except SocialConnectorError as exc:
        assert exc.code == "HTTP_401"
    else:
        raise AssertionError("expected permanent error")
    assert len(calls) == 1


def test_freshness_status_fresh_warning_stale_and_error():
    from python.pipeline.sync import freshness_status
    now = 1000.0
    assert freshness_status({"status":"success","last_sync_at":now-120}, now=now, interval_minutes=5)["status"] == "fresh"
    assert freshness_status({"status":"success","last_sync_at":now-420}, now=now, interval_minutes=5)["status"] == "warning"
    assert freshness_status({"status":"success","last_sync_at":now-700}, now=now, interval_minutes=5)["status"] == "stale"
    assert freshness_status({"status":"error","last_sync_at":now-10}, now=now, interval_minutes=5)["status"] == "error"


def test_freshness_status_never_sync():
    from python.pipeline.sync import freshness_status
    result = freshness_status({}, now=1000, interval_minutes=30)
    assert result["status"] == "never" and result["last_sync_at"] is None


def test_build_sync_health_overall_priority():
    from python.pipeline.sync import build_sync_health
    states = {
        "x": {"status":"success","last_sync_at":990},
        "youtube": {"status":"success","last_sync_at":100},
        "linkedin": {"status":"error","last_sync_at":999},
    }
    result = build_sync_health(states, now=1000, interval_minutes=5, providers=["x","youtube","linkedin","tiktok"])
    assert result["overall"] == "error"
    assert result["providers"]["x"]["status"] == "fresh"
    assert result["providers"]["youtube"]["status"] == "stale"
    assert result["providers"]["tiktok"]["status"] == "never"


def test_build_sync_alerts_are_actionable():
    from python.pipeline.sync import build_sync_alerts
    alerts = build_sync_alerts({"providers": {
        "x": {"status": "error"},
        "youtube": {"status": "stale"},
        "tiktok": {"status": "fresh"},
        "linkedin": {"status": "never"},
    }})
    by_provider = {a["provider"]: a for a in alerts}
    assert by_provider["x"]["action"] == "retry"
    assert by_provider["youtube"]["action"] == "sync"
    assert by_provider["linkedin"]["status"] == "never"


def test_build_sync_alerts_has_no_credentials():
    from python.pipeline.sync import build_sync_alerts
    alerts = build_sync_alerts({"providers": {"x": {"status": "error"}}})
    assert "token" not in str(alerts).lower()
    assert "secret" not in str(alerts).lower()



def test_build_sync_alerts_are_actionable():
    from python.pipeline.sync import build_sync_alerts
    alerts = build_sync_alerts({"providers": {
        "x": {"status": "error"},
        "youtube": {"status": "stale"},
        "tiktok": {"status": "fresh"},
        "linkedin": {"status": "never"},
    }})
    by_provider = {a["provider"]: a for a in alerts}
    assert by_provider["x"]["action"] == "retry"
    assert by_provider["youtube"]["action"] == "sync"
    assert by_provider["linkedin"]["status"] == "never"


def test_build_sync_alerts_has_no_credentials():
    from python.pipeline.sync import build_sync_alerts
    alerts = build_sync_alerts({"providers": {"x": {"status": "error"}}})
    assert "token" not in str(alerts).lower()
    assert "secret" not in str(alerts).lower()


def test_sync_diagnostic_report_is_safe_and_bounded():
    from python.pipeline.sync import build_sync_diagnostic_report
    runs=[{"run_id":"r1","status":"error","requested_providers":["x"],"providers":[{"provider":"x","ok":False,"error":"Authorization: Bearer secret-token"}],"source_count":0,"duplicate_count":0,"retry_count":1}] * 20
    report=build_sync_diagnostic_report({"x":{"status":"error","last_sync_at":900}}, runs, now=1000, interval_minutes=30, providers=["x"])
    assert len(report["recent_runs"]) == 10
    assert report["security"]["secrets_included"] is False
    assert "secret-token" not in str(report)
    assert "Bearer secret-token" not in str(report)


def test_checkpoint_two_phase_commit_preserves_committed_cursor_on_failure():
    from python.pipeline.sync import begin_checkpoint, commit_checkpoint, abandon_checkpoint
    base = {"checkpoint": {"status": "committed", "committed_cursor": "cursor-10", "sequence": 4, "run_id": "run-10", "page": 10}}
    pending = begin_checkpoint(base, run_id="run-11", cursor="cursor-11", page=11)
    assert pending["status"] == "pending"
    assert pending["committed_cursor"] == "cursor-10"
    interrupted = abandon_checkpoint({**base, "checkpoint": pending}, run_id="run-11", reason="NETWORK_ERROR")
    assert interrupted["status"] == "interrupted"
    assert interrupted["committed_cursor"] == "cursor-10"
    assert interrupted["pending_cursor"] == ""


def test_checkpoint_commit_increments_sequence_only_after_success():
    from python.pipeline.sync import begin_checkpoint, commit_checkpoint
    pending = begin_checkpoint({"checkpoint": {"status": "committed", "sequence": 2, "committed_cursor": "a"}}, run_id="run-3", cursor="b", page=3)
    committed = commit_checkpoint({"checkpoint": pending}, run_id="run-3", cursor="b", page=3)
    assert committed["status"] == "committed"
    assert committed["committed_cursor"] == "b"
    assert committed["sequence"] == 3
    assert committed["pending_cursor"] == ""


def test_checkpoint_rejects_foreign_run_commit():
    from python.pipeline.sync import commit_checkpoint
    try:
        commit_checkpoint({"checkpoint": {"status": "pending", "run_id": "run-a", "sequence": 1}}, run_id="run-b", cursor="b")
    except ValueError as exc:
        assert str(exc) == "CHECKPOINT_RUN_MISMATCH"
    else:
        raise AssertionError("expected checkpoint run mismatch")


def test_reconcile_detects_pending_and_legacy_checkpoint():
    from python.pipeline.sync import reconcile_sync_states
    report = reconcile_sync_states({
        "x": {"status": "running", "checkpoint": {"status": "pending", "run_id": "r1", "pending_cursor": "c2"}},
        "youtube": {"status": "success", "cursor": "legacy-cursor"},
        "tiktok": {"status": "success", "checkpoint": {"status": "committed", "sequence": 2, "run_id": "r2", "committed_cursor": "c2"}},
    }, providers=["x", "youtube", "tiktok"])
    assert report["ok"] is False
    codes = {(x["provider"], x["code"]) for x in report["issues"]}
    assert ("x", "PENDING_CHECKPOINT") in codes
    assert ("youtube", "LEGACY_CURSOR_WITHOUT_CHECKPOINT") in codes
    assert report["providers"]["tiktok"]["status"] == "ok"


def test_reconcile_local_manifests_detects_missing_and_count_mismatch():
    from python.pipeline.sync import reconcile_local_manifests
    runs = [{"run_id":"run-1","finished_at":10,"providers":[{"provider":"x","ok":True,"source_count":3,"duplicate_count":1}]}]
    missing = reconcile_local_manifests(runs, [], providers=["x"])
    assert missing["ok"] is False
    assert missing["issues"][0]["code"] == "LOCAL_MANIFEST_MISSING"
    mismatch = reconcile_local_manifests(runs, [{"run_id":"run-1","provider":"x","received_count":2,"persisted_count":2}], providers=["x"])
    codes = {x["code"] for x in mismatch["issues"]}
    assert "LOCAL_RECEIVED_COUNT_MISMATCH" in codes


def test_reconcile_local_manifests_accepts_confirmed_persistence():
    from python.pipeline.sync import reconcile_local_manifests
    runs = [{"run_id":"run-2","finished_at":20,"providers":[{"provider":"youtube","ok":True,"source_count":4,"duplicate_count":0}]}]
    local = [{"run_id":"run-2","provider":"youtube","received_count":4,"persisted_count":4}]
    result = reconcile_local_manifests(runs, local, providers=["youtube"])
    assert result["ok"] is True and result["issue_count"] == 0


def test_build_sync_repair_plan_only_resyncs_local_persistence_issues():
    from python.pipeline.sync import build_sync_repair_plan
    report = {"issues": [
        {"provider":"youtube","code":"LOCAL_MANIFEST_MISSING"},
        {"provider":"x","code":"PENDING_CHECKPOINT"},
    ]}
    plan = build_sync_repair_plan(report)
    by = {x["provider"]: x for x in plan["providers"]}
    assert "resync_provider" in by["youtube"]["actions"]
    assert "manual_review" in by["x"]["actions"]
    assert plan["requires_manual_review"] == ["x"]
    assert plan["safe"] is False


def test_build_sync_repair_plan_is_empty_for_clean_reconciliation():
    from python.pipeline.sync import build_sync_repair_plan
    plan = build_sync_repair_plan({"issues": []})
    assert plan["providers"] == []
    assert plan["safe"] is True


def test_reconcile_local_manifests_detects_content_missing_from_browser_db():
    from python.pipeline.sync import reconcile_local_manifests
    runs = [{"run_id":"run-content","finished_at":30,"providers":[{"provider":"x","ok":True,"source_count":2,"content_keys":["x:a","x:b"]}]}]
    local = [{"run_id":"run-content","provider":"x","received_count":2,"persisted_count":2,"content_keys":["x:a","x:b"],"db_content_keys":["x:a"]}]
    result = reconcile_local_manifests(runs, local, providers=["x"])
    codes = {x["code"] for x in result["issues"]}
    assert "LOCAL_CONTENT_MISSING" in codes


def test_reconcile_local_manifests_detects_manifest_content_mismatch():
    from python.pipeline.sync import reconcile_local_manifests
    runs = [{"run_id":"run-content-2","finished_at":31,"providers":[{"provider":"youtube","ok":True,"source_count":2,"content_keys":["yt:a","yt:b"]}]}]
    local = [{"run_id":"run-content-2","provider":"youtube","received_count":2,"persisted_count":2,"content_keys":["yt:a"],"db_content_keys":["yt:a","yt:b"]}]
    result = reconcile_local_manifests(runs, local, providers=["youtube"])
    assert any(x["code"] == "LOCAL_CONTENT_MANIFEST_MISMATCH" for x in result["issues"])


def test_build_sync_run_preserves_provider_content_keys():
    from python.pipeline.sync import build_sync_run
    run = build_sync_run("run-k", 1, 2, ["x"], [{"provider":"x","ok":True,"source_count":2,"content_keys":["x:a","x:b"]}], [])
    assert run["providers"][0]["content_keys"] == ["x:a", "x:b"]


def test_two_phase_sync_waits_for_browser_confirmation(tmp_path):
    from python.connection_server import sync_payload_result, SYNC_STATE, SYNC_RUNS, persist_sync_run, build_sync_run, confirm_sync_persistence
    import python.connection_server as cs
    old_state = dict(cs.SYNC_STATE)
    old_runs = list(cs.SYNC_RUNS)
    try:
        cs.SYNC_STATE.clear(); cs.SYNC_RUNS.clear()
        cs.SYNC_STATE["x"] = {"status":"success","cursor":"old","checkpoint":{"status":"committed","committed_cursor":"old","sequence":4,"run_id":"old-run","page":4}}
        result,count,dups = sync_payload_result("x", [{"id_mencion":"x:a","fuente":"x","texto_original":"hola"}], cursor="new", run_id="run-new", page=5)
        assert cs.SYNC_STATE["x"]["status"] == "awaiting_persistence"
        assert cs.SYNC_STATE["x"]["cursor"] == "old"
        assert cs.SYNC_STATE["x"]["checkpoint"]["status"] == "pending"
        run = build_sync_run("run-new", 1, 2, ["x"], [{"provider":"x","ok":True,"source_count":count,"duplicate_count":dups,"content_keys":["x:a"],"cursor":"new","page":5}], [])
        persist_sync_run(run)
        confirmed = confirm_sync_persistence("x","run-new",1,["x:a"])
        assert confirmed["status"] == "committed"
        assert cs.SYNC_STATE["x"]["status"] == "success"
        assert cs.SYNC_STATE["x"]["cursor"] == "new"
        assert cs.SYNC_STATE["x"]["checkpoint"]["status"] == "committed"
    finally:
        cs.SYNC_STATE.clear(); cs.SYNC_STATE.update(old_state)
        cs.SYNC_RUNS.clear(); cs.SYNC_RUNS.extend(old_runs)


def test_persistence_confirmation_rejects_content_mismatch():
    import python.connection_server as cs
    from python.connection_server import build_sync_run, persist_sync_run, confirm_sync_persistence
    old_state = dict(cs.SYNC_STATE); old_runs = list(cs.SYNC_RUNS)
    try:
        cs.SYNC_STATE.clear(); cs.SYNC_RUNS.clear()
        cs.SYNC_STATE["youtube"] = {"status":"awaiting_persistence","checkpoint":{"status":"pending","run_id":"r1","pending_cursor":"c1"}}
        persist_sync_run(build_sync_run("r1",1,2,["youtube"],[{"provider":"youtube","ok":True,"source_count":1,"content_keys":["yt:a"],"cursor":"c1","page":1}],[]))
        try:
            confirm_sync_persistence("youtube","r1",1,["yt:wrong"])
        except ValueError as exc:
            assert str(exc) == "SYNC_CONTENT_CONFIRMATION_MISMATCH"
        else:
            raise AssertionError("expected content mismatch")
    finally:
        cs.SYNC_STATE.clear(); cs.SYNC_STATE.update(old_state)
        cs.SYNC_RUNS.clear(); cs.SYNC_RUNS.extend(old_runs)


def test_retention_policy_is_bounded_and_does_not_target_business_data():
    from python.pipeline.sync import retention_policy
    policy = retention_policy({"sync_runs_days": 0, "sync_runs_max": 999999, "sync_manifests_days": 10})
    assert policy["sync_runs_days"] == 1
    assert policy["sync_runs_max"] == 10000
    assert policy["sync_manifests_days"] == 10
    assert "mentions" not in policy


def test_prune_operational_records_keeps_newest_and_removes_old():
    from python.pipeline.sync import prune_operational_records
    rows = [{"run_id":"new","started_at":89900}, {"run_id":"old","started_at":1000}, {"run_id":"new2","started_at":89800}]
    kept, report = prune_operational_records(rows, now=90000, days=1, max_records=10)
    assert [x["run_id"] for x in kept] == ["new","new2"]
    assert report["removed_by_age"] == 1


def test_prune_operational_records_applies_maximum():
    from python.pipeline.sync import prune_operational_records
    rows = [{"run_id":str(i),"started_at":1000-i} for i in range(5)]
    kept, report = prune_operational_records(rows, now=1000, days=100, max_records=2)
    assert [x["run_id"] for x in kept] == ["0","1"]
    assert report["removed_by_limit"] == 3


def test_fetch_comments_parallel_preserves_source_order():
    from python.connection_server import fetch_comments_parallel
    import time
    def fetch(identifier):
        if identifier == "slow": time.sleep(0.03)
        return {"items":[{"id": identifier}]}
    rows = fetch_comments_parallel(fetch, ["slow", "fast"], item_key="items")
    assert [row["id"] for row in rows] == ["slow", "fast"]


def test_fetch_comments_parallel_tolerates_individual_failure():
    from python.connection_server import fetch_comments_parallel
    def fetch(identifier):
        if identifier == "bad": raise RuntimeError("provider error")
        return {"items":[{"id": identifier}]}
    rows = fetch_comments_parallel(fetch, ["ok", "bad", "ok2"], item_key="items")
    assert [row["id"] for row in rows] == ["ok", "ok2"]
