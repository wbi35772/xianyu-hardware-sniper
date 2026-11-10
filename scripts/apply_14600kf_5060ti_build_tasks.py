# -*- coding: utf-8 -*-
"""Replace the old goofish monitor tasks with the 14600KF + 5060Ti build set."""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("SNIPER_API", "http://127.0.0.1:8086").rstrip("/")

TASKS = [
    {
        "task_name": "14600KF_Z790板U套装",
        "enabled": True,
        "keyword": "14600KF Z790",
        "description": "寻找个人自用/升级换下的 i5-14600KF + Z790 大板套装（优先 DDR4，接受 DDR5），要求主板型号明确、价格约1500元、无暗病；过滤电脑城/装机商、ES/QS、坏件和引流贴。",
        "min_price": "1200",
        "max_price": "1900",
        "personal_only": True,
        "max_pages": 1,
        "cron": "*/12 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_14600kf_z790_kit_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
    {
        "task_name": "RTX5060Ti_8G单卡",
        "enabled": True,
        "keyword": "RTX 5060Ti 8G",
        "description": "寻找个人双11拆机/升级换下的 RTX 5060 Ti 8G 单卡（16G同价可接受），目标约3800元；要求箱说/发票/SN/防拆贴，排除矿卡、维修卡、假卡、空盒、定金和引流贴。",
        "min_price": "3300",
        "max_price": "3950",
        "personal_only": True,
        "max_pages": 1,
        "cron": "*/8 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_5060ti_8g_build_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
    {
        "task_name": "DDR4_32G套条",
        "enabled": True,
        "keyword": "DDR4 32G 套条",
        "description": "寻找个人升级换下的 DDR4 32GB（16G×2）套条，3200/3600MHz，目标约900元；要求品牌型号明确、有购买记录/原盒，排除服务器ECC、杂牌、假货、维修条和贩子。",
        "min_price": "600",
        "max_price": "1000",
        "personal_only": True,
        "max_pages": 1,
        "cron": "*/15 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_ddr4_32g_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
    {
        "task_name": "DDR5_16G单条",
        "enabled": True,
        "keyword": "DDR5 16G 内存",
        "description": "寻找个人升级换下的 DDR5 16GB 单根内存，6000MHz以上，目标约1500元；要求品牌型号明确、有购买记录/原盒，排除DDR4冒充、服务器ECC、杂牌、假货和贩子。",
        "min_price": "900",
        "max_price": "1600",
        "personal_only": True,
        "max_pages": 1,
        "cron": "*/30 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_ddr5_16g_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
    {
        "task_name": "致态三星_1T固态",
        "enabled": True,
        "keyword": "1T 固态",
        "description": "寻找个人升级换下的 1TB NVMe 固态，优先致态 TiPlus7100/TiPro7000 和三星 990 PRO/990 EVO/980 PRO，目标750-850元；要求健康度≥95%、写入量低、有购买记录/原盒，排除矿盘、杂牌、扩容盘和假货。",
        "min_price": "500",
        "max_price": "900",
        "personal_only": True,
        "max_pages": 1,
        "cron": "*/20 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_ssd_1t_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
    {
        "task_name": "2K_IPS显示器",
        "enabled": True,
        "keyword": "2K IPS 显示器",
        "description": "寻找个人自用/升级换下的 27英寸 2K IPS 显示器，165Hz优先，目标约700元；要求亮屏实拍、无坏点/亮点、配件齐全，排除1080P/VA/TN冒充、网吧批量、维修屏和贩子。",
        "min_price": "400",
        "max_price": "800",
        "personal_only": True,
        "max_pages": 1,
        "cron": "*/20 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_2k_ips_monitor_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
    {
        "task_name": "14600KF_5060Ti整机",
        "enabled": True,
        "keyword": "14600KF 5060Ti",
        "description": "寻找个人退坑/升级的 i5-14600KF + RTX 5060 Ti 完整主机，优先 Z790 DDR4 大板、32G DDR4、1TB SSD、750W金牌、PA120散热，目标7200-7800元；配置单必须逐项写清，排除电商整机商、矿卡、杂牌电源和模板文案。",
        "min_price": "6800",
        "max_price": "8500",
        "personal_only": True,
        "max_pages": 1,
        "cron": "*/15 * * * *",
        "analyze_images": True,
        "ai_prompt_base_file": "prompts/hardware_sniper_prompt.txt",
        "ai_prompt_criteria_file": "prompts/hw_14600kf_5060ti_build_criteria.txt",
        "account_state_file": None,
        "account_strategy": "auto",
        "free_shipping": False,
        "new_publish_option": "最新",
        "region": None,
        "decision_mode": "ai",
        "keyword_rules": [],
    },
]

NEW_NAMES = {payload["task_name"] for payload in TASKS}
NEW_KEYWORDS = {payload["keyword"] for payload in TASKS}


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


def disable_old(tasks):
    for task in tasks:
        if task.get("task_name") in NEW_NAMES:
            continue
        task_id = task.get("id")
        name = task.get("task_name", "?")
        try:
            request("POST", f"/api/tasks/stop/{task_id}")
        except Exception:
            pass
        if task.get("enabled"):
            try:
                request("PATCH", f"/api/tasks/{task_id}", {"enabled": False})
                print(f"disabled old task id={task_id} name={name}")
            except Exception as exc:
                print(f"disable failed id={task_id} name={name}: {exc}")
        else:
            print(f"old task already disabled id={task_id} name={name}")
        time.sleep(0.3)


def main():
    for payload in TASKS:
        path = payload["ai_prompt_criteria_file"]
        if not os.path.exists(path):
            print(f"WARNING: criteria file missing: {path}")

    current = list_tasks()
    print(f"current tasks: {len(current)}")
    for task in current:
        print(f"  id={task.get('id')} name={task.get('task_name')} enabled={task.get('enabled')} running={task.get('is_running')}")

    disable_old(current)

    remaining = list_tasks()
    old_enabled = [t for t in remaining if t.get("task_name") not in NEW_NAMES and t.get("enabled")]
    if old_enabled:
        print("ERROR: old tasks still enabled: " + ", ".join(str(t.get("task_name")) for t in old_enabled))
        return 1

    existing_names = {t.get("task_name") for t in remaining}
    for payload in TASKS:
        if payload["task_name"] in existing_names:
            print(f"skip existing id={payload['task_name']}")
            continue
        status, data = request("POST", "/api/tasks/", payload)
        task = data.get("task", data) if isinstance(data, dict) else data
        task_id = task.get("id") if isinstance(task, dict) else None
        print(f"created id={task_id} name={payload['task_name']} http={status}")
        time.sleep(0.3)

    final = list_tasks()
    print(f"final tasks: {len(final)}")
    by_name = {task.get("task_name"): task for task in final}
    for payload in TASKS:
        task = by_name.get(payload["task_name"])
        if not task:
            print(f"ERROR: missing task {payload['task_name']}")
            return 1
        print(
            "  id={id} name={name} keyword={keyword} price={min_price}-{max_price} "
            "cron={cron} enabled={enabled} next={next_run_at} criteria={criteria}".format(
                id=task.get("id"),
                name=task.get("task_name"),
                keyword=task.get("keyword"),
                min_price=task.get("min_price"),
                max_price=task.get("max_price"),
                cron=task.get("cron"),
                enabled=task.get("enabled"),
                next_run_at=task.get("next_run_at"),
                criteria=task.get("ai_prompt_criteria_file"),
            )
        )

    missing = NEW_NAMES - set(by_name)
    extra_new = [k for k in by_name if k in NEW_NAMES and not by_name[k].get("enabled")]
    if missing or extra_new:
        print(f"ERROR: missing={missing} disabled_new={extra_new}")
        return 1

    print("OK: old tasks disabled, 7 new build tasks created and enabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
