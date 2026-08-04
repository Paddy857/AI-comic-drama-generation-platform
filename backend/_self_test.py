#!/usr/bin/env python3
"""
项目完整端到端自测脚本：
1. 后台启动uvicorn 8000端口
2. 依次调用：health / register / login / templates(categories+list+detail+favorite)
             projects(list+stats+create+detail+update) / characters / scenes / shots
             generate(ai-fill-variables + create_task + list_tasks + task_detail)
             assets list
3. 全部通过则输出PASS及统计报告
"""
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

os.chdir(os.path.dirname(os.path.abspath(__file__)))
PY = "./venv/bin/python"
HOST = "http://127.0.0.1:8000"
SERVER_LOG = "server_self_test.log"


def start_server():
    # 杀旧的8000进程
    subprocess.run(["pkill", "-f", "uvicorn app.main:app"], capture_output=True)
    time.sleep(1)
    proc = subprocess.Popen(
        f"nohup {PY} -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > {SERVER_LOG} 2>&1 &",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def wait_for_server(timeout=20):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            req("/api/health", method="GET", token=None, expect_ok=True)
            return True
        except Exception:
            time.sleep(0.8)
    print(f"[ERROR] 服务器在{timeout}s内未启动，日志：")
    if os.path.exists(SERVER_LOG):
        print(open(SERVER_LOG).read())
    return False


def req(path, method="GET", token=None, data=None, expect_ok=True):
    url = f"{HOST}{path}"
    headers = {}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, method=method, headers=headers, data=body)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if expect_ok:
            print(f"    HTTP {e.code}: {e.read().decode()[:400]}")
        return e.code, None
    except Exception as e:
        if expect_ok:
            print(f"    Request failed: {e}")
        return 0, None


def main():
    results = []
    passed = 0
    failed = 0

    def test(name, fn):
        nonlocal passed, failed
        print(f"\n[TEST] {name} ... ", end="", flush=True)
        try:
            ok = fn()
            if ok:
                passed += 1
                print("✅ PASS")
            else:
                failed += 1
                print("❌ FAIL")
            results.append((name, ok))
        except Exception as e:
            failed += 1
            print(f"❌ FAIL with exception: {e}")
            results.append((name, False))

    # ── 启动服务 ─────────────────────────────────────
    start_server()
    print("等待服务启动...", flush=True)
    if not wait_for_server():
        print("\n服务启动失败，中止测试。")
        return 1

    # ── 认证测试 ─────────────────────────────────────
    token_box = {}

    def t_health():
        s, d = req("/api/health")
        return s == 200 and d and d.get("status") == "ok"
    test("健康检查 /api/health", t_health)

    def t_register():
        s, d = req("/api/auth/register", "POST", None, {
            "username": "tester", "email": "tester@aigc.com",
            "password": "test123456", "nickname": "测试用户"
        })
        if s == 200 and d and d.get("access_token"):
            token_box["user"] = d["access_token"]
            return True
        # 可能用户已存在，再尝试登录
        s2, d2 = req("/api/auth/login", "POST", None, {
            "username": "tester", "password": "test123456"
        })
        if s2 == 200 and d2 and d2.get("access_token"):
            token_box["user"] = d2["access_token"]
            return True
        return False
    test("注册/登录获得JWT", t_register)

    # 用admin登录一下（init_db预置的）
    s_admin, d_admin = req("/api/auth/login", "POST", None, {
        "username": "admin", "password": "admin123"
    })
    if s_admin == 200 and d_admin and d_admin.get("access_token"):
        token_box["admin"] = d_admin["access_token"]
        print(f"\n[INFO] 管理员admin登录成功，使用admin身份进行后续测试")
    use_token = token_box.get("admin") or token_box.get("user")

    def t_me():
        s, d = req("/api/auth/me", "GET", use_token)
        return s == 200 and d and d.get("id") and d.get("username")
    test("获取当前用户 /api/auth/me", t_me)

    # ── 模板中心测试 ──────────────────────────────────
    tpl_ids = []
    def t_tpl_categories():
        s, d = req("/api/templates/categories", "GET", use_token)
        return s == 200 and isinstance(d, list) and len(d) >= 5
    test("模板分类 /api/templates/categories", t_tpl_categories)

    def t_tpl_list():
        s, d = req("/api/templates/?beginner_only=true&limit=10", "GET", use_token)
        if s == 200 and isinstance(d, list) and len(d) >= 3:
            for t in d:
                if t.get("id"):
                    tpl_ids.append(t["id"])
            print(f"(取到{len(d)}个模板,id示例{tpl_ids[:3]})", end=" ")
            return True
        return False
    test("模板列表(新手推荐) /api/templates/", t_tpl_list)

    def t_tpl_detail():
        if not tpl_ids:
            return False
        s, d = req(f"/api/templates/{tpl_ids[0]}", "GET", use_token)
        return s == 200 and d and d.get("variables") is not None and d.get("fixed_shots") is not None
    test("模板详情(含变量+固定分镜) /api/templates/{id}", t_tpl_detail)

    def t_tpl_favorite():
        if not tpl_ids:
            return False
        s, d = req(f"/api/templates/{tpl_ids[0]}/favorite", "POST", use_token)
        return s == 200 and d and "is_favorited" in d
    test("收藏/取消收藏模板", t_tpl_favorite)

    # ── 项目管理测试 ──────────────────────────────────
    project_ids = []
    def t_stats():
        s, d = req("/api/projects/stats", "GET", use_token)
        return s == 200 and d and "total_projects" in d
    test("统计面板 /api/projects/stats", t_stats)

    def t_project_create():
        s, d = req("/api/projects/", "POST", use_token, {
            "title": "测试-赘婿变体01", "category": "都市",
            "style": "国漫水彩", "description": "自测创建",
            "template_id": tpl_ids[0] if tpl_ids else None,
        })
        if s == 200 and d and d.get("id"):
            project_ids.append(d["id"])
            return True
        return False
    test("创建项目 /api/projects/", t_project_create)

    def t_project_list():
        s, d = req("/api/projects/?keyword=测试", "GET", use_token)
        return s == 200 and isinstance(d, list) and len(d) >= 1
    test("查询项目列表(含筛选)", t_project_list)

    def t_project_update():
        if not project_ids:
            return False
        s, d = req(f"/api/projects/{project_ids[0]}", "PUT", use_token, {
            "status": "in_progress", "title": "测试-赘婿变体01(已改名)"
        })
        return s == 200 and d and d.get("status") == "in_progress"
    test("更新项目(状态+改名)", t_project_update)

    # ── 角色库测试 ────────────────────────────────────
    char_ids = []
    def t_char_create():
        s, d = req("/api/characters/", "POST", use_token, {
            "name": "测试男主", "role_type": "main", "role_label": "主角",
            "appearance": "剑眉星目，高大英俊", "personality": "外冷内热",
            "project_id": project_ids[0] if project_ids else None,
        })
        if s == 200 and d and d.get("id"):
            char_ids.append(d["id"])
            return True
        return False
    test("创建角色 /api/characters/", t_char_create)

    def t_char_list():
        s, d = req("/api/characters/?keyword=测试", "GET", use_token)
        return s == 200 and isinstance(d, list) and len(d) >= 1
    test("查询角色列表", t_char_list)

    # ── 场景库测试 ────────────────────────────────────
    def t_scene_create_list():
        s1, d1 = req("/api/scenes/", "POST", use_token, {
            "name": "自测场景-古街雨夜", "scene_type": "室外",
            "time_of_day": "夜晚", "weather": "雨", "description": "雨打青石板"
        })
        if s1 != 200:
            return False
        s2, d2 = req("/api/scenes/?keyword=自测", "GET", use_token)
        return s2 == 200 and isinstance(d2, list) and len(d2) >= 1
    test("创建+查询场景", t_scene_create_list)

    # ── 分镜管理测试 ──────────────────────────────────
    shot_ids = []
    def t_shot_crud():
        if not project_ids:
            return False
        s1, d1 = req("/api/shots/", "POST", use_token, {
            "project_id": project_ids[0], "order": 1, "shot_type": "特写",
            "camera_move": "推", "duration_sec": 5, "script_content": "他握紧了拳头...",
            "mood": "冲突升级", "mood_intensity": 7,
        })
        if s1 != 200 or not d1 or not d1.get("id"):
            return False
        shot_ids.append(d1["id"])
        s2, d2 = req(f"/api/shots/project/{project_ids[0]}", "GET", use_token)
        if s2 != 200:
            return False
        s3, d3 = req(f"/api/shots/{shot_ids[0]}", "PUT", use_token, {
            "script_content": "他握紧了拳头，眼神变得冰冷...", "status": "done",
        })
        return s3 == 200 and d3 and "冰冷" in (d3.get("script_content") or "")
    test("分镜-创建/列出/更新 全链路", t_shot_crud)

    # ── AI生成测试 ────────────────────────────────────
    task_ids = []
    def t_ai_fill_vars():
        s, d = req("/api/generate/ai-fill-variables", "POST", use_token, {
            "required_vars": {
                "hero_name": "萧战", "heroine_name": "苏沐雪",
                "punchline": "三年之期已满！"
            }
        })
        return s == 200 and d and "generated_vars" in d and "punchline_suggestions" in d
    test("AI补全变量 /api/generate/ai-fill-variables", t_ai_fill_vars)

    def t_create_gen_task():
        if not tpl_ids or not project_ids:
            return False
        s, d = req("/api/generate/", "POST", use_token, {
            "project_id": project_ids[0], "template_id": tpl_ids[0],
            "task_name": "自测-赘婿三年之约",
            "task_type": "from_template",
            "variables_snapshot": {
                "hero_name": "萧战", "heroine_name": "苏沐雪",
                "punchline": "三年之期已满，龙神归位！"
            },
            "style": "国漫水彩", "voice_combo": "标准组合",
        })
        if s == 200 and d and d.get("id"):
            task_ids.append(d["id"])
            print(f"(任务id={d['id']}, 初始状态={d.get('status')})", end=" ")
            return True
        return False
    test("创建AI生成任务(后台模拟执行)", t_create_gen_task)

    def t_poll_gen_task():
        """后台任务用time.sleep模拟，所以这里轮询最多等30秒直到done"""
        if not task_ids:
            return False
        tid = task_ids[0]
        for _ in range(40):  # 40 * 1s = 40s
            s, d = req(f"/api/generate/tasks/{tid}", "GET", use_token)
            if s != 200 or not d:
                return False
            status = d.get("status")
            progress = d.get("progress", 0)
            if status == "done":
                print(f"(progress={progress} status={status})", end=" ")
                return True
            if status == "failed":
                print(f"(FAILED {d.get('error_msg')})", end=" ")
                return False
            time.sleep(1)
        return False
    test("轮询生成任务完成(后台模拟管线+逐镜写入)", t_poll_gen_task)

    def t_gen_list():
        s, d = req("/api/generate/tasks?limit=5", "GET", use_token)
        return s == 200 and isinstance(d, list) and len(d) >= 1
    test("生成任务队列列表", t_gen_list)

    # ── 素材管理测试 ──────────────────────────────────
    def t_assets_list():
        s, d = req("/api/assets/?limit=20", "GET", use_token)
        return s == 200 and isinstance(d, list)
    test("素材列表(空数据也ok) /api/assets/", t_assets_list)

    # ── OpenAPI文档端点 ──────────────────────────────
    def t_openapi():
        s, d = req("/api/openapi.json", "GET", None)
        return s == 200 and isinstance(d, dict) and d.get("paths") and len(d["paths"]) >= 20
    test("OpenAPI规范端点(验证所有路由已注册)", t_openapi)

    # ── 收尾 ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"📊 测试结果: 共{len(results)}项, 通过✅ {passed}, 失败❌ {failed}")
    for name, ok in results:
        print(f"  {'✅' if ok else '❌'}  {name}")
    print("=" * 60)

    # 清理：保留服务进程让用户可以直接访问，不kill
    if failed == 0:
        print("🎉 全部测试通过！项目已完整跑起来。")
        print(f"👉 API文档(Swagger): http://localhost:8000/api/docs")
        print(f"👉 管理员默认账号: admin / admin123")
        return 0
    else:
        print(f"⚠️  {failed}项失败，请检查上方日志。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
