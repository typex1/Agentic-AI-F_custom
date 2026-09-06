# Task: make your chat agent survive a restart

Your chat agent forgets everything when the process exits. Fix that with
**session persistence**.

1. Extend your chat agent (from task 02/03) with a
   `FileSessionManager(session_id=..., storage_dir=...)` passed to
   `Agent(session_manager=...)`. Use a fixed `session_id` (e.g. `"student"`)
   and a storage dir like `/tmp/strands_sessions`.
2. Run the agent, tell it two facts ("My name is ...", "I am building ..."),
   then **exit the program**.
3. Start the program again (same session id) and ask: "What is my name and
   what am I building?" — the agent must answer from the restored session.
4. Look inside the storage dir: find where your messages are stored on disk.
5. Bonus: add a `--new` CLI flag that generates a fresh `session_id` (UUID),
   starting a clean conversation.

Demo to study first: `04-production/10_session_management.py`.

## 📖 Official documentation

- [Session Management](https://strandsagents.com/docs/user-guide/concepts/agents/session-management/) — `FileSessionManager`, S3, custom backends
