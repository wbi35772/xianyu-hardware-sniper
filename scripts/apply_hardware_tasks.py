# -*- coding: utf-8 -*-
"""Replace all goofish monitor tasks with the new hardware sniper set."""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("SNIPER_API", "http://127.0.0.1:8086").rstrip("/")

TASKS = [
    {
        "task_name": "14600KF_无显卡半套机",
        "enabled": True,
        "keyword": "14600KF 无显卡",
        "description": "寻找个人出售的 i5-14600KF + B760M(优先D4版本) 不含显卡的半套主机/拔卡机，或板U+32G DDR4内存+散热电源打包。若主板是H610或卖家是电脑城装机商直接过滤。",
        "min_price": "1400",
        "max_price": "2500",
        "personal_only": True,
        "max_pages": 2,
        "cron": "*/4 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_14600kf_halfpc_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
    {
        "task_name": "9700X_无显卡半套机",
        "enabled": True,
        "keyword": "9700X B650",
        "description": "寻找个人出售的 AMD 9700X + B650M 板U套装或不含显卡的半套准系统（若带DDR5 16G/32G内存且总价低于2700元为神价）。过滤全新电商报价单。",
        "min_price": "1800",
        "max_price": "3000",
        "personal_only": True,
        "max_pages": 2,
        "cron": "*/5 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_9700x_b650_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
    {
        "task_name": "5060Ti_个人整机",
        "enabled": True,
        "keyword": "5060Ti 主机",
        "description": "寻找个人退坑的 RTX 5060 Ti 完整主机（搭配 14600KF/13600KF/9700X/5700X3D 等处理器）。必须有真实个人实拍图，严禁电商组装机贩子。",
        "min_price": "4800",
        "max_price": "6300",
        "personal_only": True,
        "max_pages": 2,
        "cron": "*/4 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_5060ti_fullpc_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
    {
        "task_name": "RTX5060Ti_单卡狙击",
        "enabled": True,
        "keyword": "RTX 5060Ti",
        "description": "寻找个人卖家双11拆机或升级换下的 RTX 5060 Ti 8G/16G 显卡现货。排除回收贴、置换贴、空盒子、定金链接。",
        "min_price": "3150",
        "max_price": "3850",
        "personal_only": True,
        "max_pages": 2,
        "cron": "*/3 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_5060ti_card_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
]


def request(method, path, payload=None, timeout=40):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, (json.loads(body) if body.strip() else None)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} {method} {path}: {body}")
        raise


def extract_tasks(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("tasks", "data", "items", "results"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def list_tasks():
    _, data = request("GET", "/api/tasks")
    return extract_tasks(data)


def delete_all(tasks):
    for task in tasks:
        task_id = task.get("id")
        name = task.get("task_name", "?")
        try:
            request("POST", f"/api/tasks/stop/{task_id}")
        except Exception:
            pass
        try:
            request("DELETE", f"/api/tasks/{task_id}")
            print(f"deleted id={task_id} name={name}")
        except Exception as exc:
            print(f"delete failed id={task_id} name={name}: {exc}")
        time.sleep(0.4)


def main():
    current = list_tasks()
    print(f"current tasks: {len(current)}")
    for task in current:
        print(f"  id={task.get('id')} name={task.get('task_name')} running={task.get('is_running')}")

    delete_all(current)
    remaining = list_tasks()
    if remaining:
        print(f"retrying delete for {len(remaining)} remaining task(s)")
        delete_all(remaining)
        remaining = list_tasks()
    if remaining:
        print("ERROR: tasks still remain after delete")
        for task in remaining:
            print(f"  id={task.get('id')} name={task.get('task_name')}")
        return 1

    created = []
    for payload in TASKS:
        status, data = request("POST", "/api/tasks/", payload)
        task = data.get("task", data) if isinstance(data, dict) else data
        task_id = task.get("id") if isinstance(task, dict) else None
        print(f"created id={task_id} name={payload['task_name']} http={status}")
        created.append(task_id)

    final = list_tasks()
    print(f"final tasks: {len(final)}")
    for task in final:
        print(
            "  id={id} name={name} keyword={keyword} price={min_price}-{max_price} "
            "cron={cron} pages={max_pages} criteria={criteria} running={running}".format(
                id=task.get("id"),
                name=task.get("task_name"),
                keyword=task.get("keyword"),
                min_price=task.get("min_price"),
                max_price=task.get("max_price"),
                cron=task.get("cron"),
                max_pages=task.get("max_pages"),
                criteria=task.get("ai_prompt_criteria_file"),
                running=task.get("is_running"),
            )
        )

    expected = {payload["task_name"] for payload in TASKS}
    actual = {task.get("task_name") for task in final}
    if expected != actual:
        print(f"ERROR: task name mismatch missing={expected - actual} extra={actual - expected}")
        return 1
    print("OK: 4 tasks replaced and verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
