# Lazy English Reader

Use `SKILL.md` in this directory as the workflow spec when the user asks to process a book into a Chinese translation, chapter-by-chapter reading notes, an Obsidian reading vault, or theme notes.

Map the skill's capability names to the tools available in this agent:

- `Read` / `Write` / `Edit` -> file read/write/edit tools
- `Bash` -> shell or terminal command execution
- `Glob` / `Grep` -> file search
- `AskUserQuestion` -> ask the user in chat
- `Agent` -> background jobs, worker tasks, or sequential processing if no worker system is available

The Python scripts in `scripts/` are executable helpers. The Markdown files in `templates/` are plain templates. Preserve user-written notes and never overwrite existing Obsidian content unless the workflow explicitly says it is safe.
