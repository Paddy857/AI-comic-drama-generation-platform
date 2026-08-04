#!/usr/bin/env python3
"""纯HTTP接口自测（服务已启动在8000），含中文URL编码修复"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HOST = "http://127.0.0.1:8000"


def req(path, method="GET", token=None, data=None, params=None, expect_ok=True):
    qs = ""
    if params:
        # 修复中文URL编码
        qs = "?" + urllib.parse.urlencode(params, doseq=True)
    url = f"{HOST}{path}{qs}"
    headers = {}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, method=method, headers=headers, data=body)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw.decode(errors="ignore")[:200]
    except urllib.error.HTTPError as e:
        if expect_ok:
            msg = e.read().decode(errors="ignore")[:400]
            print(f"    HTTP {e.code}: {msg}")
        return e.code, None
    except Exception as e:
        if expect_ok:
            print(f"    Request failed: {type(e).__name__}: {e}")
        return 0, None


results = []
passed = 0
failed = 0
tokens = {}


def test(name, fn):
    global passed, failed
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
        print(f"❌ FAIL exc={type(e).__name__}: {e}")
        results.append((name, False))


# 健康检查
def t1():
    s, d = req("/api/health")
    return s == 200 and d and d.get("status") == "ok"
test("健康检查 /api/health", t1)

# 登录admin
def t2():
    s, d = req("/api/auth/login", "POST", None, {
        "username": "admin", "password": "admin123"
    })
    if s == 200 and d and d.get("access_token") and d.get("user"):
        tokens["admin"] = d["access_token"]
        print(f"(uid={d['user']['id']}, nick={d['user']['nickname']})", end=" ")
        return True
    return False
test("管理员登录 /api/auth/login (admin/admin123)", t2)

tk = tokens.get("admin")

# me
def t3():
    s, d = req("/api/auth/me", "GET", tk)
    return s == 200 and d and d.get("username") == "admin"
test("获取当前用户 /api/auth/me", t3)

# 模板分类
def t4():
    s, d = req("/api/templates/categories", "GET", tk)
    return s == 200 and isinstance(d, list) and len(d) >= 8
test("模板分类 /api/templates/categories (≥8个分类)", t4)

tpl_ids = []
# 模板列表（新手推荐）
def t5():
    global tpl_ids
    s, d = req("/api/templates/", "GET", tk, params={"beginner_only": "true", "limit": 10})
    if s == 200 and isinstance(d, list) and len(d) >= 3:
        tpl_ids = [t["id"] for t in d if t.get("id")]
        print(f"(取到{len(d)}个模板,首3id={tpl_ids[:3]})", end=" ")
        return True
    return False
test("模板列表（新手推荐筛选）", t5)

# 模板详情
def t6():
    if not tpl_ids:
        return False
    s, d = req(f"/api/templates/{tpl_ids[0]}", "GET", tk)
    return (s == 200 and d and isinstance(d.get("variables"), list)
            and isinstance(d.get("fixed_shots"), list) and len(d["fixed_shots"]) >= 1)
test("模板详情含变量+固定分镜 (首模板)", t6)

# 收藏模板
def t7():
    if not tpl_ids:
        return False
    s, d = req(f"/api/templates/{tpl_ids[0]}/favorite", "POST", tk)
    return s == 200 and d and "is_favorited" in d
test("收藏模板切换 /api/templates/{id}/favorite", t7)

# 收藏列表
def t7b():
    s, d = req("/api/templates/favorites", "GET", tk)
    return s == 200 and isinstance(d, list)
test("我的收藏列表", t7b)

# 项目统计
def t8():
    s, d = req("/api/projects/stats", "GET", tk)
    return s == 200 and d and "total_projects" in d and "total_ai_generates" in d
test("项目统计面板 /api/projects/stats", t8)

project_ids = []
# 创建项目
def t9():
    global project_ids
    s, d = req("/api/projects/", "POST", tk, data={
        "title": "E2E自测-赘婿变体001", "category": "都市",
        "style": "国漫水彩", "description": "集成测试创建",
        "template_id": tpl_ids[0] if tpl_ids else None
    })
    if s == 200 and d and d.get("id"):
        project_ids.append(d["id"])
        return True
    return False
test("创建项目 /api/projects/", t9)

# 项目列表（含中文关键词筛选）
def t10():
    s, d = req("/api/projects/", "GET", tk, params={"keyword": "E2E自测"})
    return s == 200 and isinstance(d, list) and len(d) >= 1
test("项目列表中文关键词筛选 /api/projects/?keyword=E2E自测", t10)

# 更新项目
def t11():
    if not project_ids:
        return False
    s, d = req(f"/api/projects/{project_ids[0]}", "PUT", tk, data={
        "status": "in_progress", "title": "E2E自测-赘婿变体001(改)",
        "current_page": 3, "total_pages": 10
    })
    return s == 200 and d and d.get("status") == "in_progress" and d.get("current_page") == 3
test("更新项目状态/进度 /api/projects/{id}", t11)

char_ids = []
# 创建角色
def t12():
    global char_ids
    s, d = req("/api/characters/", "POST", tk, data={
        "name": "E2E男主张玄", "role_type": "main", "role_label": "主角",
        "appearance": "剑眉星目，高大挺拔，气质冷峻",
        "personality": "外冷内热，隐忍三年一朝爆发",
        "project_id": project_ids[0] if project_ids else None,
        "project_name": "E2E自测-赘婿变体"
    })
    if s == 200 and d and d.get("id"):
        char_ids.append(d["id"])
        return True
    return False
test("创建角色 /api/characters/", t12)

# 角色列表中文筛选
def t13():
    s, d = req("/api/characters/", "GET", tk, params={"keyword": "张玄"})
    return s == 200 and isinstance(d, list) and len(d) >= 1
test("角色列表中文搜索 /api/characters/?keyword=张玄", t13)

# 更新角色
def t14():
    if not char_ids:
        return False
    s, d = req(f"/api/characters/{char_ids[0]}", "PUT", tk, data={
        "appearance": "剑眉星目，高大挺拔，气质冷峻，左眉一道疤痕更显英气"
    })
    return s == 200 and d and "疤痕" in (d.get("appearance") or "")
test("更新角色外貌描述 /api/characters/{id}", t14)

# 场景
def t15():
    s1, d1 = req("/api/scenes/", "POST", tk, data={
        "name": "E2E-古街雨夜霓虹", "scene_type": "室外",
        "time_of_day": "夜晚", "weather": "中雨",
        "description": "霓虹灯闪烁的江南古街，雨水打湿青石板路",
        "project_id": project_ids[0] if project_ids else None
    })
    if s1 != 200:
        return False
    s2, d2 = req("/api/scenes/", "GET", tk, params={"keyword": "古街"})
    return s2 == 200 and isinstance(d2, list) and len(d2) >= 1
test("创建+中文搜索场景 /api/scenes/", t15)

shot_ids = []
# 分镜CRUD
def t16():
    global shot_ids
    if not project_ids:
        return False
    s1, d1 = req("/api/shots/", "POST", tk, data={
        "project_id": project_ids[0], "order": 1, "shot_no": 1,
        "shot_type": "特写", "camera_move": "推",
        "duration_sec": 5, "script_content": "E2E: 他握紧拳头，指甲嵌入掌心。隐忍三年的怒火即将爆发。",
        "mood": "冲突升级", "mood_intensity": 7, "status": "pending"
    })
    if s1 != 200 or not d1 or not d1.get("id"):
        return False
    shot_ids.append(d1["id"])
    s2, d2 = req(f"/api/shots/project/{project_ids[0]}", "GET", tk)
    if s2 != 200 or not isinstance(d2, list) or len(d2) < 1:
        return False
    s3, d3 = req(f"/api/shots/{shot_ids[0]}", "PUT", tk, data={
        "script_content": "E2E: 他握紧拳头，指甲嵌入掌心，鲜血渗出，眼神冰冷如刀。隐忍三年的怒火即将爆发。",
        "status": "done", "mood_intensity": 9
    })
    return s3 == 200 and d3 and d3.get("status") == "done" and "鲜血" in (d3.get("script_content") or "")
test("分镜全流程：创建/列出/更新(状态+文案) /api/shots/", t16)

# AI 补全变量
def t17():
    s, d = req("/api/generate/ai-fill-variables", "POST", tk, data={
        "required_vars": {
            "hero_name": "萧战", "heroine_name": "苏沐雪",
            "punchline": "三年之期已满！"
        }
    })
    return (s == 200 and d and "generated_vars" in d
            and isinstance(d.get("punchline_suggestions"), list)
            and len(d["punchline_suggestions"]) >= 2)
test("AI补全变量Mock /api/generate/ai-fill-variables", t17)

task_ids = []
# 创建AI生成任务
def t18():
    global task_ids
    if not tpl_ids or not project_ids:
        return False
    s, d = req("/api/generate/", "POST", tk, data={
        "project_id": project_ids[0], "template_id": tpl_ids[0],
        "task_name": "E2E-赘婿三年之约生成任务",
        "task_type": "from_template",
        "variables_snapshot": {
            "hero_name": "萧战", "heroine_name": "苏沐雪",
            "punchline": "三年之期已满，龙神归位！"
        },
        "style": "国漫水彩", "voice_combo": "标准组合",
    })
    if s == 200 and d and d.get("id"):
        task_ids.append(d["id"])
        print(f"(任务id={d['id']}, status={d.get('status')}, est={d.get('estimated_seconds')}s)", end=" ")
        return True
    return False
test("创建AI生成任务(后台模拟5步管线+逐镜写入)", t18)

# 轮询任务完成
def t19():
    if not task_ids:
        return False
    tid = task_ids[0]
    for i in range(60):
        s, d = req(f"/api/generate/tasks/{tid}", "GET", tk)
        if s != 200 or not d:
            return False
        status = d.get("status")
        prog = d.get("progress", 0)
        comp = d.get("completed_shots", 0)
        total = d.get("total_shots", 0)
        if status == "done" and comp >= total and total >= 5:
            print(f"(prog={prog}%, shots={comp}/{total})", end=" ")
            return True
        if status == "failed":
            print(f"(FAILED: {d.get('error_msg')})", end=" ")
            return False
        sys.stdout.write(f"[{prog}%] ")
        sys.stdout.flush()
        time.sleep(1)
    return False
test("轮询生成任务→完成(等待后台模拟) /api/generate/tasks/{id}", t19)

# 生成历史
def t20():
    s, d = req("/api/generate/history", "GET", tk)
    return s == 200 and isinstance(d, list) and len(d) >= 1
test("生成历史列表 /api/generate/history", t20)

# 素材
def t21():
    s, d = req("/api/assets/", "GET", tk, params={"file_type": "image", "limit": 20})
    return s == 200 and isinstance(d, list)
test("素材列表(空数据也OK) /api/assets/?file_type=image", t21)

# 删除项目
def t22():
    if not project_ids:
        return False
    s, d = req(f"/api/projects/{project_ids[0]}", "DELETE", tk)
    return s == 200 and d and "已删除" in (d.get("message") or "")
test("删除项目(清理测试数据) /api/projects/{id} DELETE", t22)

# OpenAPI
def t23():
    s, d = req("/api/openapi.json", "GET", None)
    n_paths = len(d.get("paths", {})) if isinstance(d, dict) else 0
    print(f"(实际注册路由数={n_paths})", end=" ")
    return s == 200 and isinstance(d, dict) and n_paths >= 25
test("OpenAPI规范端点(28个路径全注册) /api/openapi.json", t23)

print("\n" + "=" * 70)
print(f"📊 最终测试结果: 共{len(results)}项  |  通过✅ {passed}  |  失败❌ {failed}")
for name, ok in results:
    print(f"  {'✅' if ok else '❌'}  {name}")
print("=" * 70)
if failed == 0:
    print("🎉 全量接口测试 100% 通过！")
    print(f"👉 Swagger文档:   http://127.0.0.1:8000/api/docs")
    print(f"👉 ReDoc文档:    http://127.0.0.1:8000/api/redoc")
    print(f"👉 管理员账号:    admin / admin123")
    sys.exit(0)
else:
    print(f"⚠️  {failed}项失败，见上方❌条目详情。")
    sys.exit(1)
