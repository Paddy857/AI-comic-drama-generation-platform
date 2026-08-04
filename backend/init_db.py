#!/usr/bin/env python3
"""
数据库初始化脚本：创建所有表 + 插入种子数据（模板、示例角色、场景）
运行方式: cd backend && python init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import Base, engine, SessionLocal
from app.models import (
    User, Project, Character, Scene, Shot,
    Template, TemplateVariable, TemplateShot,
    GenerationTask, GeneratedShot, Asset, UserFavorite,
)
from app.core.security import get_password_hash

print("🚀 开始初始化数据库...")
Base.metadata.create_all(bind=engine)
print("✅ 数据库表创建完成")

db = SessionLocal()

# ─── 1. 创建默认管理员用户 ───────────────────────────────────────────
existing_user = db.query(User).filter(User.username == "admin").first()
if not existing_user:
    admin = User(
        username="admin",
        email="admin@aigc.com",
        hashed_password=get_password_hash("admin123"),
        nickname="创作者小明",
        is_vip=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"✅ 创建默认用户: admin / admin123 (id={admin.id})")
else:
    admin = existing_user
    print("ℹ️  默认用户已存在，跳过创建")

# ─── 2. 模板种子数据 ─────────────────────────────────────────────────
TEMPLATES_SEED = [
    {
        "template_code": "TPL_URBAN_XUZHU_001",
        "name": "都市赘婿·三年之约",
        "category": "都市",
        "description": "经典赘婿打脸爽文模板，必填3个字段即可快速量产，新手友好",
        "total_shots": 10,
        "total_duration_sec": 180,
        "required_var_count": 3,
        "avg_play": "1200万",
        "avg_finish_rate": "42%",
        "is_beginner_friendly": True,
        "tags": ["新手友好", "赘婿", "打脸爽文", "都市"],
        "sort_order": 100,
        "emotion_curve": [
            {"shot": "1-2", "mood": "压抑铺垫", "intensity": 3},
            {"shot": "3-4", "mood": "冲突升级", "intensity": 6},
            {"shot": "5-6", "mood": "忍无可忍", "intensity": 8},
            {"shot": "7-8", "mood": "反转爆发", "intensity": 10},
            {"shot": "9-10", "mood": "爽感收尾+钩子", "intensity": 9},
        ],
        "variables": [
            {"key": "hero_name", "label": "男主名字", "var_type": "text", "is_required": True,
             "default_value": "萧战", "hint": "2-3字，都市常用名", "examples": ["叶凡", "林辰", "萧战"], "sort_order": 1},
            {"key": "heroine_name", "label": "女主名字", "var_type": "text", "is_required": True,
             "default_value": "苏沐雪", "hint": "清冷感女主名", "examples": ["苏沐雪", "沈清歌", "顾若曦"], "sort_order": 2},
            {"key": "punchline", "label": "打脸金句", "var_type": "textarea", "is_required": True,
             "default_value": "三年之期已满，龙神归位！", "hint": "第7镜男主爆发时说的关键句，15字以内最佳", "sort_order": 3},
            {"key": "hero_appearance", "label": "男主外貌", "var_type": "text", "is_required": False,
             "ai_generated": True, "hint": "AI可自动补全", "sort_order": 4},
            {"key": "villain_name", "label": "反派名字", "var_type": "text", "is_required": False,
             "default_value": "王少", "sort_order": 5},
            {"key": "scene1_location", "label": "开场场景", "var_type": "text", "is_required": False,
             "default_value": "豪华酒店宴会厅", "sort_order": 6},
            {"key": "bgm_style", "label": "BGM风格", "var_type": "select", "is_required": False,
             "default_value": "都市爽感", "options": ["都市爽感", "古风大气", "电子燃"], "sort_order": 7},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "大全景", "camera_move": "固定", "duration_sec": 8,
             "script_template": "${scene1_location}内，觥筹交错，${villain_name}正在羞辱${hero_name}...",
             "mood": "压抑铺垫", "mood_intensity": 3},
            {"shot_no": 2, "shot_type": "特写", "camera_move": "推", "duration_sec": 5,
             "script_template": "${hero_name}紧握拳头，指甲嵌入掌心，忍耐着眼前的一切...",
             "mood": "压抑铺垫", "mood_intensity": 4},
            {"shot_no": 3, "shot_type": "中景", "camera_move": "摇", "duration_sec": 6,
             "script_template": "${villain_name}将酒杯摔在${hero_name}脚边：「废物，给我滚！」",
             "mood": "冲突升级", "mood_intensity": 6},
            {"shot_no": 4, "shot_type": "近景", "camera_move": "固定", "duration_sec": 5,
             "script_template": "${heroine_name}拉住${hero_name}的袖子，眼中含着泪水...",
             "mood": "冲突升级", "mood_intensity": 6},
            {"shot_no": 5, "shot_type": "特写", "camera_move": "推", "duration_sec": 4,
             "script_template": "${hero_name}的眼神逐渐变冷，往日的委屈如洪水决堤...",
             "mood": "忍无可忍", "mood_intensity": 8},
            {"shot_no": 6, "shot_type": "全景", "camera_move": "拉", "duration_sec": 5,
             "script_template": "众人哄笑，${hero_name}缓缓站起身来，周身气势陡然一变...",
             "mood": "忍无可忍", "mood_intensity": 8},
            {"shot_no": 7, "shot_type": "仰拍中景", "camera_move": "快速推", "duration_sec": 6,
             "script_template": "${hero_name}站起，冷笑着说出：「${punchline}」",
             "mood": "反转爆发", "mood_intensity": 10},
            {"shot_no": 8, "shot_type": "反应镜头", "camera_move": "摇", "duration_sec": 5,
             "script_template": "全场震惊，${villain_name}面色煞白，跌坐在椅子上...",
             "mood": "反转爆发", "mood_intensity": 10},
            {"shot_no": 9, "shot_type": "中景", "camera_move": "推", "duration_sec": 6,
             "script_template": "${hero_name}转身，对${heroine_name}温柔地说：「委屈你了，以后再不会了。」",
             "mood": "爽感收尾", "mood_intensity": 9},
            {"shot_no": 10, "shot_type": "全景", "camera_move": "拉远", "duration_sec": 8,
             "script_template": "【下集预告】${hero_name}的真实身份即将公开，敬请期待...",
             "mood": "钩子结尾", "mood_intensity": 9},
        ],
    },
    {
        "template_code": "TPL_ANCIENT_SWEET_002",
        "name": "古风甜宠·王爷的小医妃",
        "category": "古风",
        "description": "古风甜宠经典模板，王爷×医女设定，填2个字即可上手",
        "total_shots": 8,
        "total_duration_sec": 150,
        "required_var_count": 2,
        "avg_play": "800万",
        "avg_finish_rate": "48%",
        "is_beginner_friendly": True,
        "tags": ["新手友好", "古风", "甜宠", "王爷"],
        "sort_order": 95,
        "emotion_curve": [
            {"shot": "1-2", "mood": "相遇铺垫", "intensity": 4},
            {"shot": "3-5", "mood": "甜蜜互动", "intensity": 7},
            {"shot": "6-7", "mood": "矛盾爆发", "intensity": 9},
            {"shot": "8", "mood": "甜蜜收尾", "intensity": 10},
        ],
        "variables": [
            {"key": "hero_name", "label": "王爷名号", "var_type": "text", "is_required": True,
             "default_value": "墨渊王爷", "hint": "古风名号，如：冷王、摄政王", "sort_order": 1},
            {"key": "heroine_name", "label": "女主名字", "var_type": "text", "is_required": True,
             "default_value": "苏锦", "hint": "古风女名，如：苏锦、云舒", "sort_order": 2},
            {"key": "skill_type", "label": "女主技能", "var_type": "text", "is_required": False,
             "default_value": "医术", "sort_order": 3},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "全景", "camera_move": "固定", "duration_sec": 8,
             "script_template": "古镇药铺，${heroine_name}正在研磨药材，突然门外传来急促脚步声...",
             "mood": "相遇铺垫", "mood_intensity": 4},
            {"shot_no": 2, "shot_type": "特写", "camera_move": "推", "duration_sec": 6,
             "script_template": "${hero_name}倒地，额头染血，${heroine_name}上前查看...",
             "mood": "相遇铺垫", "mood_intensity": 5},
            {"shot_no": 3, "shot_type": "近景", "camera_move": "固定", "duration_sec": 8,
             "script_template": "${heroine_name}施展${skill_type}，${hero_name}睁眼，见到她的第一眼便怔住了...",
             "mood": "甜蜜互动", "mood_intensity": 7},
            {"shot_no": 4, "shot_type": "特写", "camera_move": "推", "duration_sec": 5,
             "script_template": "「你叫什么名字？」${hero_name}问道。「民女${heroine_name}。」",
             "mood": "甜蜜互动", "mood_intensity": 7},
            {"shot_no": 5, "shot_type": "中景", "camera_move": "跟", "duration_sec": 8,
             "script_template": "${hero_name}起身，将自己的玉佩塞给${heroine_name}：「算是本王的谢礼。」",
             "mood": "甜蜜互动", "mood_intensity": 8},
            {"shot_no": 6, "shot_type": "全景", "camera_move": "摇", "duration_sec": 6,
             "script_template": "侍卫闯入，指着${heroine_name}：「刺客！拿下！」",
             "mood": "矛盾爆发", "mood_intensity": 9},
            {"shot_no": 7, "shot_type": "仰拍", "camera_move": "固定", "duration_sec": 5,
             "script_template": "${hero_name}一步挡在${heroine_name}前：「谁敢动她？」",
             "mood": "矛盾爆发", "mood_intensity": 10},
            {"shot_no": 8, "shot_type": "特写", "camera_move": "推", "duration_sec": 6,
             "script_template": "${heroine_name}泪盈于睫，${hero_name}低声：「本王保你周全。」",
             "mood": "甜蜜收尾", "mood_intensity": 10},
        ],
    },
    {
        "template_code": "TPL_SCHOOL_SWEET_003",
        "name": "校园甜宠·同桌的你",
        "category": "校园",
        "description": "清新校园甜宠，同桌互动萌点十足，新人首选",
        "total_shots": 8,
        "total_duration_sec": 120,
        "required_var_count": 2,
        "avg_play": "600万",
        "avg_finish_rate": "52%",
        "is_beginner_friendly": True,
        "tags": ["新手友好", "校园", "甜宠", "同桌"],
        "sort_order": 90,
        "emotion_curve": [
            {"shot": "1-2", "mood": "日常相遇", "intensity": 4},
            {"shot": "3-5", "mood": "小甜甜", "intensity": 7},
            {"shot": "6-7", "mood": "误会矛盾", "intensity": 8},
            {"shot": "8", "mood": "和好甜蜜", "intensity": 10},
        ],
        "variables": [
            {"key": "hero_name", "label": "男主名字", "var_type": "text", "is_required": True,
             "default_value": "顾以深", "hint": "清爽男生名", "sort_order": 1},
            {"key": "heroine_name", "label": "女主名字", "var_type": "text", "is_required": True,
             "default_value": "林晚晴", "hint": "清甜女生名", "sort_order": 2},
            {"key": "subject", "label": "科目", "var_type": "text", "is_required": False,
             "default_value": "数学", "sort_order": 3},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "全景", "camera_move": "固定", "duration_sec": 6,
             "script_template": "教室，${heroine_name}坐在${hero_name}旁边，两人默默做${subject}作业...",
             "mood": "日常相遇", "mood_intensity": 4},
            {"shot_no": 2, "shot_type": "特写", "camera_move": "推", "duration_sec": 5,
             "script_template": "${heroine_name}皱眉看着题目，${hero_name}悄悄把答案推过去...",
             "mood": "日常相遇", "mood_intensity": 5},
            {"shot_no": 3, "shot_type": "近景", "camera_move": "固定", "duration_sec": 7,
             "script_template": "${heroine_name}惊喜地看向${hero_name}，两人四目相对...",
             "mood": "小甜甜", "mood_intensity": 7},
            {"shot_no": 4, "shot_type": "特写", "camera_move": "推", "duration_sec": 5,
             "script_template": "${hero_name}耳尖微红，低头继续假装写作业...",
             "mood": "小甜甜", "mood_intensity": 7},
            {"shot_no": 5, "shot_type": "中景", "camera_move": "摇", "duration_sec": 7,
             "script_template": "下课，${hero_name}把自己的外套盖在睡着的${heroine_name}身上...",
             "mood": "小甜甜", "mood_intensity": 8},
            {"shot_no": 6, "shot_type": "全景", "camera_move": "固定", "duration_sec": 6,
             "script_template": "${heroine_name}误以为${hero_name}讨厌自己，收拾书包准备换座位...",
             "mood": "误会矛盾", "mood_intensity": 8},
            {"shot_no": 7, "shot_type": "近景", "camera_move": "快速推", "duration_sec": 5,
             "script_template": "${hero_name}拉住${heroine_name}：「我不是那个意思。」",
             "mood": "误会矛盾", "mood_intensity": 9},
            {"shot_no": 8, "shot_type": "特写", "camera_move": "推", "duration_sec": 6,
             "script_template": "${hero_name}小声道：「你能不能...一直坐我旁边？」",
             "mood": "和好甜蜜", "mood_intensity": 10},
        ],
    },
    {
        "template_code": "TPL_URBAN_REBORN_004",
        "name": "重生之我是首富",
        "category": "都市",
        "description": "重生爽文经典套路，前世冤屈今生报仇，爽感拉满",
        "total_shots": 12,
        "total_duration_sec": 240,
        "required_var_count": 4,
        "avg_play": "2000万",
        "avg_finish_rate": "38%",
        "is_beginner_friendly": False,
        "tags": ["重生", "首富", "都市", "商战"],
        "sort_order": 85,
        "emotion_curve": [
            {"shot": "1-3", "mood": "重生冲击", "intensity": 5},
            {"shot": "4-6", "mood": "布局反击", "intensity": 7},
            {"shot": "7-9", "mood": "复仇高潮", "intensity": 10},
            {"shot": "10-12", "mood": "新篇章开启", "intensity": 8},
        ],
        "variables": [
            {"key": "hero_name", "label": "男主名字", "var_type": "text", "is_required": True,
             "default_value": "江辰", "sort_order": 1},
            {"key": "company_name", "label": "公司名称", "var_type": "text", "is_required": True,
             "default_value": "江氏集团", "sort_order": 2},
            {"key": "villain_name", "label": "反派名字", "var_type": "text", "is_required": True,
             "default_value": "陈总", "sort_order": 3},
            {"key": "punchline", "label": "打脸台词", "var_type": "textarea", "is_required": True,
             "default_value": "你曾经踩过我的人生，现在我来亲手结束你的。", "sort_order": 4},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "特写", "camera_move": "推", "duration_sec": 6,
             "script_template": "${hero_name}猛地睁眼——重生了！回到了十年前...",
             "mood": "重生冲击", "mood_intensity": 5},
            {"shot_no": 2, "shot_type": "全景", "camera_move": "固定", "duration_sec": 8,
             "script_template": "熟悉的场景，${hero_name}握紧双拳：「这次，我绝不会重蹈覆辙。」",
             "mood": "重生冲击", "mood_intensity": 6},
            {"shot_no": 3, "shot_type": "中景", "camera_move": "跟", "duration_sec": 7,
             "script_template": "${hero_name}打开手机，看到了十年前的账户余额，嘴角微扬...",
             "mood": "布局反击", "mood_intensity": 7},
        ],
    },
    {
        "template_code": "TPL_FANTASY_SWORD_005",
        "name": "斗破苍穹式退婚",
        "category": "玄幻",
        "description": "玄幻退婚爽文，废柴逆袭，一剑震苍穹",
        "total_shots": 15,
        "total_duration_sec": 300,
        "required_var_count": 4,
        "avg_play": "1500万",
        "avg_finish_rate": "35%",
        "is_beginner_friendly": False,
        "tags": ["玄幻", "退婚", "逆袭", "修炼"],
        "sort_order": 80,
        "emotion_curve": [
            {"shot": "1-3", "mood": "退婚羞辱", "intensity": 3},
            {"shot": "4-7", "mood": "机缘获得", "intensity": 6},
            {"shot": "8-12", "mood": "实力爆发", "intensity": 9},
            {"shot": "13-15", "mood": "震撼收场", "intensity": 10},
        ],
        "variables": [
            {"key": "hero_name", "label": "男主名字", "var_type": "text", "is_required": True,
             "default_value": "叶辰", "sort_order": 1},
            {"key": "heroine_name", "label": "退婚女主", "var_type": "text", "is_required": True,
             "default_value": "慕容雪", "sort_order": 2},
            {"key": "realm", "label": "最高境界", "var_type": "text", "is_required": True,
             "default_value": "破虚境", "sort_order": 3},
            {"key": "punchline", "label": "震场金句", "var_type": "textarea", "is_required": True,
             "default_value": "你说我是废材？那你们所谓的天才，在我眼中不过是蝼蚁！", "sort_order": 4},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "大全景", "camera_move": "固定", "duration_sec": 8,
             "script_template": "慕容家宗祠，${heroine_name}当众退婚，众人嘲笑${hero_name}是废材...",
             "mood": "退婚羞辱", "mood_intensity": 3},
            {"shot_no": 2, "shot_type": "特写", "camera_move": "推", "duration_sec": 5,
             "script_template": "${hero_name}沉默接受，暗暗攥紧退婚书...",
             "mood": "退婚羞辱", "mood_intensity": 4},
        ],
    },
    {
        "template_code": "TPL_SWEET_FLASH_006",
        "name": "闪婚老公是豪门",
        "category": "甜宠",
        "description": "闪婚甜宠，意外嫁给豪门总裁，甜虐双修",
        "total_shots": 10,
        "total_duration_sec": 180,
        "required_var_count": 3,
        "avg_play": "900万",
        "avg_finish_rate": "45%",
        "is_beginner_friendly": False,
        "tags": ["甜宠", "闪婚", "豪门", "总裁"],
        "sort_order": 75,
        "variables": [
            {"key": "hero_name", "label": "总裁名字", "var_type": "text", "is_required": True,
             "default_value": "霍司晟", "sort_order": 1},
            {"key": "heroine_name", "label": "女主名字", "var_type": "text", "is_required": True,
             "default_value": "宋微", "sort_order": 2},
            {"key": "punchline", "label": "表白金句", "var_type": "textarea", "is_required": True,
             "default_value": "你是我唯一一次失控的意外。", "sort_order": 3},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "全景", "camera_move": "固定", "duration_sec": 6,
             "script_template": "民政局，${heroine_name}稀里糊涂地和${hero_name}领了证...",
             "mood": "相遇", "mood_intensity": 5},
        ],
    },
    {
        "template_code": "TPL_MYSTERY_CALL_007",
        "name": "午夜来电",
        "category": "悬疑",
        "description": "悬疑惊悚模板，午夜神秘来电引发的连环事件",
        "total_shots": 14,
        "total_duration_sec": 360,
        "required_var_count": 5,
        "avg_play": "1100万",
        "avg_finish_rate": "40%",
        "is_beginner_friendly": False,
        "tags": ["悬疑", "惊悚", "烧脑", "反转"],
        "sort_order": 70,
        "variables": [
            {"key": "hero_name", "label": "主角名字", "var_type": "text", "is_required": True,
             "default_value": "方铭", "sort_order": 1},
            {"key": "victim_name", "label": "受害者名字", "var_type": "text", "is_required": True,
             "default_value": "李雪", "sort_order": 2},
            {"key": "mystery_item", "label": "神秘物件", "var_type": "text", "is_required": True,
             "default_value": "旧手机", "sort_order": 3},
            {"key": "location", "label": "关键地点", "var_type": "text", "is_required": True,
             "default_value": "废弃医院", "sort_order": 4},
            {"key": "twist_line", "label": "反转揭秘台词", "var_type": "textarea", "is_required": True,
             "default_value": "这个电话，来自三年前已经死去的人。", "sort_order": 5},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "特写", "camera_move": "推", "duration_sec": 6,
             "script_template": "深夜，${hero_name}的手机突然响起，显示的号码却是${victim_name}的...",
             "mood": "悬疑开场", "mood_intensity": 6},
        ],
    },
    {
        "template_code": "TPL_ANCIENT_EMPRESS_008",
        "name": "嫡女归来",
        "category": "古风",
        "description": "古风复仇，嫡女重生复仇，一步步踏上权力顶峰",
        "total_shots": 16,
        "total_duration_sec": 320,
        "required_var_count": 4,
        "avg_play": "1300万",
        "avg_finish_rate": "36%",
        "is_beginner_friendly": False,
        "tags": ["古风", "复仇", "嫡女", "宫廷"],
        "sort_order": 65,
        "variables": [
            {"key": "heroine_name", "label": "嫡女名字", "var_type": "text", "is_required": True,
             "default_value": "顾婉宁", "sort_order": 1},
            {"key": "villain_name", "label": "主要反派", "var_type": "text", "is_required": True,
             "default_value": "顾侧妃", "sort_order": 2},
            {"key": "hero_name", "label": "男主名字", "var_type": "text", "is_required": True,
             "default_value": "摄政王", "sort_order": 3},
            {"key": "punchline", "label": "复仇宣言", "var_type": "textarea", "is_required": True,
             "default_value": "你们欠我的，我会一分不少地要回来。", "sort_order": 4},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "大全景", "camera_move": "固定", "duration_sec": 8,
             "script_template": "顾府，${heroine_name}睁眼——她重生了，回到了被害死的前一天...",
             "mood": "重生冲击", "mood_intensity": 5},
        ],
    },
    {
        "template_code": "TPL_URBAN_BOSS_009",
        "name": "我的总裁老婆",
        "category": "都市",
        "description": "反转甜宠，落魄男被总裁老婆宠上天",
        "total_shots": 10,
        "total_duration_sec": 180,
        "required_var_count": 3,
        "avg_play": "700万",
        "avg_finish_rate": "50%",
        "is_beginner_friendly": False,
        "tags": ["都市", "甜宠", "总裁", "反转"],
        "sort_order": 60,
        "variables": [
            {"key": "hero_name", "label": "男主名字", "var_type": "text", "is_required": True,
             "default_value": "陈默", "sort_order": 1},
            {"key": "heroine_name", "label": "总裁老婆", "var_type": "text", "is_required": True,
             "default_value": "林诗音", "sort_order": 2},
            {"key": "punchline", "label": "宠溺台词", "var_type": "textarea", "is_required": True,
             "default_value": "你只需要负责帅就行了，其他的有我。", "sort_order": 3},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "全景", "camera_move": "固定", "duration_sec": 6,
             "script_template": "${hero_name}落魄打工，却意外收到一张结婚证——他结婚了？",
             "mood": "反转开场", "mood_intensity": 6},
        ],
    },
    {
        "template_code": "TPL_ENDWORLD_ZOMBIE_010",
        "name": "末日求生指南",
        "category": "末世",
        "description": "末世丧尸流，硬核求生，成长逆袭",
        "total_shots": 18,
        "total_duration_sec": 360,
        "required_var_count": 5,
        "avg_play": "1800万",
        "avg_finish_rate": "33%",
        "is_beginner_friendly": False,
        "tags": ["末世", "丧尸", "求生", "逆袭"],
        "sort_order": 55,
        "variables": [
            {"key": "hero_name", "label": "主角名字", "var_type": "text", "is_required": True,
             "default_value": "陈刚", "sort_order": 1},
            {"key": "companion_name", "label": "队友名字", "var_type": "text", "is_required": True,
             "default_value": "苏芸", "sort_order": 2},
            {"key": "base_name", "label": "据点名称", "var_type": "text", "is_required": True,
             "default_value": "新城基地", "sort_order": 3},
            {"key": "weapon", "label": "标志性武器", "var_type": "text", "is_required": True,
             "default_value": "改装砍刀", "sort_order": 4},
            {"key": "punchline", "label": "觉醒台词", "var_type": "textarea", "is_required": True,
             "default_value": "末日里活着就是胜利，但我要的不只是活着。", "sort_order": 5},
        ],
        "shots": [
            {"shot_no": 1, "shot_type": "大全景", "camera_move": "航拍俯冲", "duration_sec": 8,
             "script_template": "末日第三天，城市已沦陷，${hero_name}独自在废墟中求生...",
             "mood": "末日开局", "mood_intensity": 7},
        ],
    },
]

# Insert templates
existing_codes = {t.template_code for t in db.query(Template.template_code).all()}

for tpl_data in TEMPLATES_SEED:
    if tpl_data["template_code"] in existing_codes:
        print(f"  ℹ️  模板已存在: {tpl_data['name']}")
        continue

    variables_data = tpl_data.pop("variables", [])
    shots_data = tpl_data.pop("shots", [])

    template = Template(**tpl_data)
    db.add(template)
    db.flush()

    for var_data in variables_data:
        var = TemplateVariable(template_id=template.id, **var_data)
        db.add(var)

    for shot_data in shots_data:
        shot = TemplateShot(template_id=template.id, **shot_data)
        db.add(shot)

    db.commit()
    print(f"  ✅ 模板已插入: {template.name}")

# ─── 3. 示例角色 ─────────────────────────────────────────────────────
if db.query(Character).filter(Character.user_id == admin.id).count() == 0:
    sample_characters = [
        Character(user_id=admin.id, name="李星河", role_type="main", role_label="主角",
                  appearance="剑眉星目，气宇轩昂", project_name="赛博江湖"),
        Character(user_id=admin.id, name="苏小沫", role_type="female_main", role_label="女主角",
                  appearance="清冷御姐，眸若星辰", project_name="赛博江湖"),
        Character(user_id=admin.id, name="墨渊", role_type="villain", role_label="反派",
                  appearance="深沉阴郁，城府极深", project_name="赛博江湖"),
        Character(user_id=admin.id, name="林婉儿", role_type="supporting", role_label="配角",
                  appearance="活泼可爱，笑靥如花", project_name="古风奇缘"),
        Character(user_id=admin.id, name="阿明", role_type="main", role_label="主角",
                  appearance="少年感十足，眼神坚定", project_name="末日求生"),
    ]
    for c in sample_characters:
        db.add(c)
    db.commit()
    print("✅ 示例角色创建完成")

# ─── 4. 示例场景 ─────────────────────────────────────────────────────
if db.query(Scene).filter(Scene.user_id == admin.id).count() == 0:
    sample_scenes = [
        Scene(user_id=admin.id, name="赛博江湖街道", scene_type="室外",
              time_of_day="夜晚", weather="霓虹雨夜", description="霓虹灯闪烁的赛博朋克风格街道"),
        Scene(user_id=admin.id, name="豪华宴会厅", scene_type="室内",
              time_of_day="夜晚", description="金碧辉煌的五星级酒店宴会厅"),
        Scene(user_id=admin.id, name="古风竹林", scene_type="自然",
              time_of_day="清晨", weather="薄雾", description="晨雾缭绕的古风竹林小径"),
        Scene(user_id=admin.id, name="末日废墟", scene_type="室外",
              time_of_day="白天", weather="阴霾", description="末日后的城市废墟，残垣断壁"),
    ]
    for s in sample_scenes:
        db.add(s)
    db.commit()
    print("✅ 示例场景创建完成")

# ─── 5. 示例项目 ─────────────────────────────────────────────────────
if db.query(Project).filter(Project.user_id == admin.id).count() == 0:
    sample_projects = [
        Project(user_id=admin.id, title="赛博江湖", status="in_progress",
                category="都市", style="赛博", total_pages=36, current_page=12,
                description="赛博朋克风格的江湖恩怨故事"),
        Project(user_id=admin.id, title="星际迷航：深渊", status="review",
                category="玄幻", style="日漫", total_pages=24, current_page=24,
                description="宇宙深处的文明碰撞"),
        Project(user_id=admin.id, title="古风奇缘", status="in_progress",
                category="古风", style="古风", total_pages=20, current_page=8,
                description="古代王朝的宫廷爱恨情仇"),
        Project(user_id=admin.id, title="末日求生指南", status="draft",
                category="末世", style="赛博", total_pages=16, current_page=3,
                description="末世中的人性挣扎与救赎"),
    ]
    for p in sample_projects:
        db.add(p)
    db.commit()
    print("✅ 示例项目创建完成")

db.close()
print("\n🎉 数据库初始化完成！")
print("=" * 50)
print("默认账号: admin / admin123")
print("API文档: http://localhost:8000/api/docs")
print("=" * 50)
