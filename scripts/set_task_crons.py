# -*- coding: utf-8 -*-
"""Set staggered cron schedules for the 7 hardware sniper tasks."""
import json
import os
import urllib.request

BASE = os.environ.get("SNIPER_API", "http://127.0.0.1:8000").rstrip("/")

CRONS = {
    4: "2-59/10 * * * *",
    5: "4-59/8 * * * *",
    6: "6-59/13 * * * *",
    7: "1-59/23 * * * *",
    8: "3-59/15 * * * *",
    9: "5-59/17 * * * *",
    10: "7-59/19 * * * *",
}


def patch_task(task_id, cron):
    payload = json.dumps({"cron": cron}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/tasks/{task_id}",
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    task = data.get("task", data)
    print(
        f"id={task_id} cron={task.get('cron')} enabled={task.get('enabled')} "
        f"next={task.get('next_run_at')}"
    )


def main():
    for task_id, cron in CRONS.items():
        patch_task(task_id, cron)
    with urllib.request.urlopen(f"{BASE}/api/tasks", timeout=20) as resp:
        tasks = json.loads(resp.read().decode("utf-8"))
    for task in tasks:
        if task.get("id") in CRONS:
            print(
                f"FINAL id={task['id']} {task['task_name']} cron={task.get('cron')} "
                f"next={task.get('next_run_at')} running={task.get('is_running')}"
            )


if __name__ == "__main__":
    main()
