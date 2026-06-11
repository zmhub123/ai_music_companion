"""聊天与荐歌编排。"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pycore.core.logger import get_logger
from src.api.errors import AppApiError
from src.db.models import ChatMessage, GuestSession
from src.integrations.dashscope_client import DashScopeClient, DashScopeError, get_dashscope_client
from src.integrations.music_provider import (
    SongCandidate,
    extract_song_search_keywords,
    is_direct_song_request,
    search_songs,
)

logger = get_logger()

RECOMMEND_TRIGGERS = (
    "推荐",
    "想听",
    "来几首",
    "荐歌",
    "歌曲",
    "民谣",
    "流行",
    "摇滚",
    "弹唱",
    "吉他",
    "安静",
    "治愈",
    "播放",
    "放一首",
    "点一首",
    "来一首",
)

CHAT_SYSTEM_PROMPT = """你是「音伴」，用户身边会弹吉他/尤克里里的音乐朋友。
语气治愈又活泼，像熟人微信聊天：简短（1-3句）、有共情、可带「嗯」「呀」「～」。
规则：
- 先接住对方情绪，再自然聊音乐，别生硬推销
- 本条回复不要列出具体歌名（荐歌由系统另做）
- 可温柔追问心情、场景、想听的感觉
- 结合上文，避免重复同一句套话"""

MOOD_RECOMMEND_COUNT = 10
DIRECT_RECOMMEND_COUNT = 3

MOCK_REASONS = [
    "旋律舒缓，适合此刻的心情",
    "和弦简单，适合边弹边唱",
    "氛围温暖，帮你慢慢放松",
    "节奏平稳，像晚风一样",
]

# 情绪/风格 → 网易云搜索词（避免用「今天很开心」这类整句误搜到带「今天」的歌名）
MOOD_STYLE_SEARCH: list[tuple[tuple[str, ...], str]] = [
    (("欢快", "轻快", "嗨", "活力", "元气"), "欢快 流行"),
    (("开心", "高兴", "快乐", "愉快"), "欢快 流行"),
    (("治愈", "安静", "舒缓", "放松", "平静", "温柔"), "治愈 民谣"),
    (("伤感", "难过", "伤心", "失恋", "低落", "丧", "emo"), "伤感 民谣"),
    (("浪漫", "甜蜜", "恋爱"), "甜蜜 流行"),
    (("励志", "加油", "奋斗"), "励志 流行"),
]

MUSIC_REQUEST_HINTS = ("歌", "听", "推荐", "曲", "音乐", "来首", "来几首", "放一首", "点一首")

CHEERFUL_TITLE_POSITIVE = ("快乐", "阳光", "晴", "甜", "笑", "开心", "欢", "甜", "美好", "夏天")
CHEERFUL_TITLE_NEGATIVE = (
    "难过",
    "伤心",
    "夜",
    "孤独",
    "哭",
    "分手",
    "不想",
    "麻烦",
    "丧",
    "痛",
    "累",
    "烦",
    "离开",
    "失去",
)


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def message_to_dict(message: ChatMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "metadata": message.message_metadata,
        "created_at": _iso(message.created_at),
    }


def _guest_style_hint(guest: GuestSession) -> str:
    styles = guest.style_preferences or []
    level = guest.skill_level or "beginner"
    if not styles:
        return f"弹唱水平：{level}"
    return f"弹唱水平：{level}，偏好风格：{', '.join(styles)}"


def _format_history(history: list[ChatMessage], *, limit: int = 6) -> str:
    lines: list[str] = []
    for msg in history[-limit:]:
        role = "用户" if msg.role == "user" else "音伴"
        lines.append(f"{role}：{msg.content}")
    return "\n".join(lines) if lines else "（暂无历史）"


def _last_recommendations(history: list[ChatMessage]) -> list[dict[str, Any]]:
    for msg in reversed(history):
        if msg.role != "assistant" or not msg.message_metadata:
            continue
        recs = msg.message_metadata.get("recommendations")
        if isinstance(recs, list) and recs:
            return recs
    return []


def _is_followup_song_request(content: str, history: list[ChatMessage]) -> bool:
    text = content.strip()
    if re.search(r"第[一二三四1-4]\s*首", text):
        return True
    last_recs = _last_recommendations(history)
    if not last_recs:
        return False
    for rec in last_recs:
        name = str(rec.get("song_name") or "")
        if name and (name in text or text in name):
            return True
    return False


def _heuristic_intent(content: str, history: list[ChatMessage] | None = None) -> str:
    text = content.strip()
    if is_direct_song_request(text):
        return "recommend_music"
    if any(trigger in text for trigger in RECOMMEND_TRIGGERS):
        return "recommend_music"
    if history and _is_followup_song_request(text, history):
        return "recommend_music"
    return "chat_only"


def _wants_music_recommendation(content: str) -> bool:
    text = content.strip()
    return any(hint in text for hint in MUSIC_REQUEST_HINTS) or any(
        trigger in text for trigger in RECOMMEND_TRIGGERS
    )


def _extract_mood_style_query(content: str) -> str | None:
    text = content.strip()
    if not text or not _wants_music_recommendation(text):
        return None

    for style in ("民谣", "流行", "摇滚", "古风", "独立", "爵士", "说唱"):
        if style in text:
            for triggers, query in MOOD_STYLE_SEARCH:
                if any(trigger in text for trigger in triggers):
                    return f"{query.split()[0]} {style}"
            return f"{style} 华语"

    for triggers, query in MOOD_STYLE_SEARCH:
        if any(trigger in text for trigger in triggers):
            return query
    return None


def _mood_title_bias(song_name: str, user_content: str) -> int:
    text = user_content.strip()
    name = song_name.strip()
    if not name:
        return 0

    cheerful_request = any(
        word in text for word in ("欢快", "轻快", "开心", "高兴", "快乐", "愉快", "元气")
    )
    if cheerful_request:
        score = 0
        for word in CHEERFUL_TITLE_POSITIVE:
            if word in name:
                score += 12
        for word in CHEERFUL_TITLE_NEGATIVE:
            if word in name:
                score -= 18
        return score

    sad_request = any(word in text for word in ("伤感", "难过", "伤心", "失恋", "低落", "丧", "emo"))
    if sad_request:
        score = 0
        for word in CHEERFUL_TITLE_NEGATIVE:
            if word in name:
                score += 10
        for word in ("快乐", "开心", "欢快", "甜"):
            if word in name:
                score -= 8
        return score
    return 0


def _sort_candidates_for_user(
    candidates: list[SongCandidate],
    user_content: str,
) -> list[SongCandidate]:
    return sorted(
        candidates,
        key=lambda song: (
            _mood_title_bias(song.song_name, user_content),
            -int(song.is_original or False),
        ),
        reverse=True,
    )


def _extract_keywords_heuristic(content: str, guest: GuestSession) -> str:
    mood_query = _extract_mood_style_query(content)
    if mood_query:
        return mood_query

    song_query = extract_song_search_keywords(content)
    if song_query and song_query != content.strip():
        return song_query
    if song_query and len(song_query) <= 12:
        return song_query

    for style in guest.style_preferences or []:
        if style in content:
            return style
    for trigger in ("民谣", "流行", "摇滚", "古风", "独立"):
        if trigger in content:
            return trigger
    return song_query or "治愈 民谣"


def _mock_chat_reply(content: str) -> str:
    text = content.strip()
    if any(w in text for w in ("累", "疲", "加班", "困", "忙")):
        return "辛苦啦～先喘口气，不用硬撑。想听点轻轻的歌缓缓吗？跟我说说现在什么感觉就好～"
    if any(w in text for w in ("开心", "高兴", "快乐", "哈哈")):
        return "哇，听起来状态不错呀！要不要来点儿节奏轻快的，把好心情续上～"
    if any(w in text.lower() for w in ("emo", "难过", "低落", "烦", "丧")):
        return "嗯嗯，我在呢。音乐有时候像抱抱一样——不急着选歌，先跟我说想安静一点，还是发泄一下？"
    return "我听见啦～像朋友聊天一样，跟我讲讲此刻的心情或想听的感觉，我来帮你找歌～"


async def _classify_intent(
    client: DashScopeClient,
    content: str,
    history: list[ChatMessage],
) -> str:
    heuristic = _heuristic_intent(content, history)
    if client.use_mock:
        return heuristic

    history_text = _format_history(history, limit=4)
    prompt = (
        "判断用户最新消息的意图。\n"
        "- recommend_music：想听歌、要点歌、要推荐、提到歌名/歌手/风格、或在上文荐歌后继续点歌\n"
        "- chat_only：纯闲聊、吐槽、问非音乐问题\n"
        "结合对话上下文理解指代（如「形容」「第二首」）。\n"
        '只返回 JSON：{"intent":"chat_only"} 或 {"intent":"recommend_music"}\n\n'
        f"对话：\n{history_text}\n"
        f"用户：{content}"
    )
    raw = await client.generate(prompt, temperature=0.0)
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0) if match else raw)
        intent = data.get("intent")
        if intent in {"chat_only", "recommend_music"}:
            return str(intent)
    except (json.JSONDecodeError, AttributeError):
        logger.warning("intent parse failed, fallback heuristic", raw=raw[:200])
    return heuristic


async def _extract_keywords(
    client: DashScopeClient,
    content: str,
    guest: GuestSession,
    history: list[ChatMessage],
) -> str:
    mood_query = _extract_mood_style_query(content)
    if mood_query:
        return mood_query

    if client.use_mock:
        return _extract_keywords_heuristic(content, guest)

    history_text = _format_history(history, limit=3)
    prompt = (
        "从用户消息提取适合网易云搜索歌曲的关键词（1-4 个词）。"
        "若用户表达情绪/风格（如开心想听欢快的歌），返回情绪搜索词如「欢快 流行」，"
        "不要返回整句或日期词（如「今天很开心」）。歌名/歌手优先。\n"
        '只返回 JSON：{"keywords":"关键词"}\n'
        f"用户背景：{_guest_style_hint(guest)}\n"
        f"近期对话：\n{history_text}\n"
        f"用户消息：{content}"
    )
    raw = await client.generate(prompt, temperature=0.0)
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0) if match else raw)
        keywords = str(data.get("keywords") or "").strip()
        if keywords:
            return keywords
    except (json.JSONDecodeError, AttributeError):
        logger.warning("keyword parse failed, fallback heuristic", raw=raw[:200])
    return _extract_keywords_heuristic(content, guest)


def _mock_recommendations(
    candidates: list[SongCandidate],
    guest: GuestSession,
    *,
    user_content: str = "",
    direct: bool = False,
    limit: int = MOOD_RECOMMEND_COUNT,
) -> list[dict[str, Any]]:
    if direct:
        picked = candidates[:limit]
    elif user_content:
        picked = _sort_candidates_for_user(candidates, user_content)[:limit]
    else:
        picked = candidates[:limit]
    recommendations: list[dict[str, Any]] = []
    for idx, song in enumerate(picked):
        reason = MOCK_REASONS[idx % len(MOCK_REASONS)]
        styles = guest.style_preferences or []
        if styles:
            reason = f"{reason}，也贴合你喜欢的{styles[0]}"
        recommendations.append(
            {
                "netease_song_id": song.netease_song_id,
                "song_name": song.song_name,
                "artist_name": song.artist_name,
                "cover_url": song.cover_url,
                "reason": reason,
                "is_original": song.is_original,
                "vip_only": song.vip_only,
                "playable": song.playable,
            }
        )
    return recommendations


async def _rerank_recommendations(
    client: DashScopeClient,
    content: str,
    guest: GuestSession,
    candidates: list[SongCandidate],
    *,
    direct: bool = False,
    limit: int = MOOD_RECOMMEND_COUNT,
) -> list[dict[str, Any]]:
    if not candidates:
        return []

    if direct:
        return _mock_recommendations(
            candidates,
            guest,
            direct=True,
            limit=min(limit, DIRECT_RECOMMEND_COUNT),
        )

    ranked_candidates = _sort_candidates_for_user(candidates, content)

    if client.use_mock:
        return _mock_recommendations(
            ranked_candidates,
            guest,
            user_content=content,
            limit=limit,
        )

    candidate_lines = [
        f"{idx}. {song.song_name} - {song.artist_name} (id={song.netease_song_id})"
        for idx, song in enumerate(ranked_candidates[:20])
    ]
    prompt = (
        f"根据用户消息的情绪与意图，从候选歌曲中挑选最多 {limit} 首并给出简短推荐理由。"
        "务必贴合用户情绪（如开心/欢快不要选伤感歌名）。"
        "优先原版原唱，排除翻唱/改编/Live/伴奏。"
        "只返回 JSON 数组，每项含 netease_song_id, reason。\n"
        f"用户背景：{_guest_style_hint(guest)}\n"
        f"用户消息：{content}\n"
        "候选歌曲：\n"
        + "\n".join(candidate_lines)
    )
    raw = await client.generate(prompt, temperature=0.3)
    try:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        parsed = json.loads(match.group(0) if match else raw)
        if isinstance(parsed, list):
            by_id = {song.netease_song_id: song for song in ranked_candidates}
            recommendations: list[dict[str, Any]] = []
            for item in parsed[:limit]:
                if not isinstance(item, dict):
                    continue
                song_id = item.get("netease_song_id")
                song = by_id.get(int(song_id)) if song_id is not None else None
                if song is None:
                    continue
                recommendations.append(
                    {
                        "netease_song_id": song.netease_song_id,
                        "song_name": song.song_name,
                        "artist_name": song.artist_name,
                        "cover_url": song.cover_url,
                        "reason": str(item.get("reason") or "为你精心挑选"),
                        "is_original": song.is_original,
                        "vip_only": song.vip_only,
                        "playable": song.playable,
                    }
                )
            if recommendations:
                return recommendations
    except (json.JSONDecodeError, AttributeError, ValueError, TypeError):
        logger.warning("rerank parse failed, fallback mock", raw=raw[:200])
    return _mock_recommendations(ranked_candidates, guest, user_content=content, limit=limit)


async def _generate_chat_reply(
    client: DashScopeClient,
    content: str,
    guest: GuestSession,
    history: list[ChatMessage],
) -> str:
    if client.use_mock:
        return _mock_chat_reply(content)

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": f"{CHAT_SYSTEM_PROMPT}\n用户背景：{_guest_style_hint(guest)}",
        },
    ]
    for msg in history[-8:]:
        role = "user" if msg.role == "user" else "assistant"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": content})
    return (await client.chat_completion(messages, temperature=0.85)).strip()


async def _generate_recommend_reply(
    client: DashScopeClient,
    content: str,
    guest: GuestSession,
    recommendations: list[dict[str, Any]],
    *,
    direct: bool = False,
) -> str:
    if not recommendations:
        return "唔，暂时没搜到特别合适的，换个歌名或风格再试试？"

    first_name = str(recommendations[0].get("song_name") or "这首")

    if client.use_mock:
        if direct:
            return f"找到啦！《{first_name}》给你放上，听听是不是这首～"
        return "好嘞～根据你说的，我先挑了几首，你看看哪首对味～"

    song_names = "、".join(item["song_name"] for item in recommendations[:3])
    if direct:
        prompt = (
            "你是音伴，用户点了具体歌，你刚搜到并准备播放。"
            "写一句简短活泼的确认语（≤35字），像朋友递歌，可提歌名，不要列清单。\n"
            f"用户背景：{_guest_style_hint(guest)}\n"
            f"用户消息：{content}\n"
            f"将播放：{first_name}\n"
            "回复："
        )
    else:
        prompt = (
            "你是音伴，刚为用户荐歌，写一句治愈又活泼的开场白（≤40字），像朋友分享歌单，不要列歌名清单。\n"
            f"用户背景：{_guest_style_hint(guest)}\n"
            f"用户消息：{content}\n"
            f"已选歌曲：{song_names}\n"
            "开场白："
        )
    return (await client.generate(prompt, temperature=0.75)).strip()


async def list_messages(
    db: AsyncSession,
    guest_id: str,
    *,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size

    total = int(
        await db.scalar(
            select(func.count()).select_from(ChatMessage).where(ChatMessage.guest_id == guest_id)
        )
        or 0
    )
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.guest_id == guest_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(page_size)
    )
    items = [message_to_dict(msg) for msg in result.scalars().all()]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def reset_messages(db: AsyncSession, guest_id: str) -> dict[str, Any]:
    count = int(
        await db.scalar(
            select(func.count()).select_from(ChatMessage).where(ChatMessage.guest_id == guest_id)
        )
        or 0
    )
    await db.execute(delete(ChatMessage).where(ChatMessage.guest_id == guest_id))
    await db.commit()
    return {"reset": True, "cleared_message_count": count}


async def send_message(
    db: AsyncSession,
    guest: GuestSession,
    content: str,
    *,
    client: DashScopeClient | None = None,
) -> dict[str, Any]:
    text = content.strip()
    if not text:
        raise AppApiError(40001, "消息内容不能为空")

    llm = client or get_dashscope_client()

    try:
        user_message = ChatMessage(guest_id=guest.guest_id, role="user", content=text)
        db.add(user_message)
        await db.flush()

        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.guest_id == guest.guest_id, ChatMessage.id != user_message.id)
            .order_by(ChatMessage.created_at.asc())
        )
        history = list(history_result.scalars().all())

        direct = is_direct_song_request(text)
        heuristic_intent = _heuristic_intent(text, history)
        if llm.use_mock or heuristic_intent == "recommend_music":
            intent = heuristic_intent
        else:
            intent = await _classify_intent(llm, text, history)

        if intent == "recommend_music":
            rec_limit = DIRECT_RECOMMEND_COUNT if direct else MOOD_RECOMMEND_COUNT
            search_limit = max(rec_limit * 2, 20)
            keywords = await _extract_keywords(llm, text, guest, history)
            candidates = await search_songs(keywords, limit=search_limit)
            if not candidates:
                candidates = await search_songs("民谣 治愈", limit=search_limit)
            recommendations = await _rerank_recommendations(
                llm, text, guest, candidates, direct=direct, limit=rec_limit
            )
            assistant_content = await _generate_recommend_reply(
                llm, text, guest, recommendations, direct=direct
            )
            metadata: dict[str, Any] | None = {
                "intent": "play_song" if direct else "recommend_music",
                "recommendations": recommendations,
                "auto_play": direct and bool(recommendations),
            }
        else:
            assistant_content = await _generate_chat_reply(llm, text, guest, history)
            metadata = {"intent": "chat_only"}

        assistant_message = ChatMessage(
            guest_id=guest.guest_id,
            role="assistant",
            content=assistant_content,
            message_metadata=metadata,
        )
        db.add(assistant_message)
        guest.last_active_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(user_message)
        await db.refresh(assistant_message)

        return {
            "user_message": message_to_dict(user_message),
            "assistant_message": message_to_dict(assistant_message),
        }
    except DashScopeError as exc:
        await db.rollback()
        logger.error("LLM service failed", error=str(exc))
        raise AppApiError(50001, "AI 服务暂时不可用，请稍后再试", http_status=500) from exc
