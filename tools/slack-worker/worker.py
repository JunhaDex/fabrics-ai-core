# tools/slack-worker/worker.py
# 요구사항 1~3 + 채널당 프로젝트 1개(A안) 동적 조회
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

load_dotenv(override=True)

LOADING_EMOJI = os.environ.get("SLACK_LOADING_EMOJI", "loading")

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = Path(__file__).resolve().parent / "state" / "threads.json"
CHANNELS_FILE = Path(__file__).resolve().parent / "channels.local.json"

RESUME_RE = re.compile(r"\bresume=(\S+)")
TODO_RE = re.compile(r"\btodo=(\S+)")

app = App(token=os.environ["SLACK_BOT_TOKEN"])
BOT_USER_ID = app.client.auth_test()["user_id"]


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def load_channels() -> dict:
    if CHANNELS_FILE.exists():
        return json.loads(CHANNELS_FILE.read_text())
    return {}


def resolve_project(channel_id: str) -> str | None:
    return load_channels().get(channel_id)


def project_dir_for(project_name: str) -> Path:
    return REPO_ROOT / "projects" / project_name


def referenced_files(claude_md_path: Path) -> list[str]:
    files = [str(claude_md_path.relative_to(REPO_ROOT))]
    if not claude_md_path.exists():
        return files
    for line in claude_md_path.read_text().splitlines():
        m = re.match(r"^@(\S+)", line.strip())
        if m:
            imported = (claude_md_path.parent / m.group(1)).resolve()
            files.append(str(imported.relative_to(REPO_ROOT)))
    return files


def run_claude(prompt: str, project_dir: Path, resume_id: str | None = None) -> tuple[str | None, str]:
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--permission-mode", "auto",
    ]
    if resume_id:
        cmd += ["--resume", resume_id]

    try:
        proc = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return None, "⚠️ 요청이 시간 초과되었습니다(600초). 작업 범위를 줄여서 다시 시도해주세요."
    except OSError as e:
        return None, f"⚠️ claude 실행 실패: {e}"

    session_id = None
    result_text = None
    for line in proc.stdout.splitlines():
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if evt.get("type") == "system" and evt.get("subtype") == "init":
            session_id = evt.get("session_id")
        if evt.get("type") == "result":
            result_text = evt.get("result", result_text)

    if proc.returncode != 0:
        stderr_excerpt = proc.stderr.strip()[:500]
        error_note = f"⚠️ 비정상 종료(code {proc.returncode}): {stderr_excerpt}"
        result_text = f"{result_text}\n\n{error_note}" if result_text else error_note
    elif result_text is None:
        result_text = "(응답을 받지 못했습니다)"

    return session_id, result_text


def is_reset(text: str) -> bool:
    return text.strip().lower() == "reset"


def reset_thread(thread_ts: str, say) -> None:
    state = load_state()
    if thread_ts not in state:
        say(text="이 스레드에는 연결된 세션이 없습니다.", thread_ts=thread_ts)
        return
    del state[thread_ts]
    save_state(state)
    say(text="세션 연결을 초기화했습니다. 새로 멘션하시면 새 세션이 시작됩니다.", thread_ts=thread_ts)


def parse_resume_tokens(text: str) -> tuple[str, str | None]:
    """멘션 텍스트에서 resume=/todo= 토큰을 뽑고, 남은 텍스트와 resume_id를 반환한다."""
    resume_match = RESUME_RE.search(text)
    if not resume_match:
        return text, None

    resume_id = resume_match.group(1)
    text = RESUME_RE.sub("", text)

    todo_match = TODO_RE.search(text)
    if todo_match:
        text = TODO_RE.sub("", text)
        text = f"(참고 TODO 파일: {todo_match.group(1)}) {text.strip()}"

    return text.strip(), resume_id


def add_reaction(client, channel_id: str, msg_ts: str) -> None:
    try:
        client.reactions_add(channel=channel_id, name=LOADING_EMOJI, timestamp=msg_ts)
    except SlackApiError as e:
        print(f"reactions_add 실패: {e.response.get('error')}", file=sys.stderr)


def remove_reaction(client, channel_id: str, msg_ts: str) -> None:
    try:
        client.reactions_remove(channel=channel_id, name=LOADING_EMOJI, timestamp=msg_ts)
    except SlackApiError as e:
        print(f"reactions_remove 실패: {e.response.get('error')}", file=sys.stderr)


def process(
    thread_ts: str,
    text: str,
    say,
    project_dir: Path,
    project_name: str,
    channel_id: str,
    msg_ts: str,
    client,
    resume_id: str | None = None,
):
    state = load_state()
    entry = state.get(thread_ts)
    is_first_in_thread = entry is None

    if resume_id is None and entry:
        resume_id = entry["session_id"]

    add_reaction(client, channel_id, msg_ts)
    try:
        session_id, result_text = run_claude(text, project_dir, resume_id=resume_id)
        final_id = session_id or resume_id

        if final_id:
            state[thread_ts] = {"session_id": final_id, "project": project_name}
            save_state(state)

        if is_first_in_thread and final_id:
            files = referenced_files(project_dir / "CLAUDE.md")
            verb = "세션 재개" if resume_id else "세션 시작"
            header = f"{verb}: `{final_id}`\n참조 파일: {', '.join(files)}"
            say(text=f"{header}\n\n{result_text}", thread_ts=thread_ts)
        else:
            say(text=result_text, thread_ts=thread_ts)
    finally:
        remove_reaction(client, channel_id, msg_ts)  # 타임아웃/실패 시에도 반응 제거


def unmapped_channel_notice(channel_id: str) -> str:
    return (
        f"채널 ID: {channel_id}.\n"
        f"채널을 프로젝트와 연결해주세요."
    )


@app.event("app_mention")
def handle_mention(event, say, client):
    text = re.sub(r"<@[^>]+>", "", event["text"]).strip()
    thread_ts = event.get("thread_ts", event["ts"])
    channel_id = event["channel"]

    if is_reset(text):
        reset_thread(thread_ts, say)
        return

    state = load_state()
    if thread_ts in state:
        project_name = state[thread_ts]["project"]
        resume_id = None
    else:
        project_name = resolve_project(channel_id)
        if project_name is None:
            say(text=unmapped_channel_notice(channel_id), thread_ts=thread_ts)
            return
        text, resume_id = parse_resume_tokens(text)

    process(
        thread_ts, text, say, project_dir_for(project_name), project_name,
        channel_id=channel_id, msg_ts=event["ts"], client=client, resume_id=resume_id,
    )


@app.event("message")
def handle_message(event, say, client):
    if event.get("subtype") is not None or event.get("bot_id"):
        return  # message_changed/deleted, 봇 메시지(자신 포함) 무시
    thread_ts = event.get("thread_ts")
    if not thread_ts:
        return  # 스레드 답글이 아니면 무시

    text = event.get("text", "")
    if f"<@{BOT_USER_ID}>" in text:
        return  # 멘션은 app_mention 핸들러가 이미 처리함

    state = load_state()
    entry = state.get(thread_ts)
    if not entry:
        return  # 추적 중인 세션이 아니면 무시

    if is_reset(text):
        reset_thread(thread_ts, say)
        return

    process(
        thread_ts, text, say, project_dir_for(entry["project"]), entry["project"],
        channel_id=event["channel"], msg_ts=event["ts"], client=client,
    )


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
