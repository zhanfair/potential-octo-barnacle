---
name: character-video-workflow
description: 人物拆解视频项目的分阶段创作路由 skill。用于用户要围绕名人、历史人物、创作者、企业家、思想家等制作人物拆解内容、人物口播视频、纪录片式观点视频、B站横屏人物视频、人物资料研究到脚本再到粗剪的完整流程时。它负责判断资料是否足够、规划资料池建设、提炼多个内容观点、组织结构稿和口播稿、安排配音、整理素材视频、匹配画面叙事、生成粗剪预览，并强制一步一审，不默认自动跑完全链路。
---

# Character Video Workflow

## Core Role

Use this skill as a staged router for character breakdown video projects. It does not replace research, writing, review, voice generation, or editing skills; it coordinates them in the right order and stops at review gates.

Default behavior: complete only the current stage and stop with a reviewable artifact. Continue to the next stage only when the user explicitly says to continue, next step, or directly finish the current stage.

## Non-Negotiable Rules

- Put evidence before interpretation. Do not enter deep character analysis without a usable source pool.
- Treat the workflow as staged creation, not a one-shot automation pipeline.
- Produce reviewable artifacts at every stage.
- Give multiple possible angles before locking the main thesis.
- Preserve uncertainty. Mark claims that need stronger sourcing.
- Prefer source-grounded details over generic personality analysis.
- For video projects, build the first preview as horizontal no-subtitles unless the user asks otherwise.
- For AI voice projects, prefer 3-5 larger voice sections over many tiny sections to keep vocal state continuous.
- Keep export records for generated scripts, audio, source tables, and preview videos.

## Workflow

1. Project kickoff
2. Character candidate judgment
3. Source pool building
4. Source state rating
5. Character deep breakdown
6. Content thesis extraction
7. Structure draft
8. Recording script
9. Review, humanization, and second pass
10. Voice planning and generation
11. Source video sorting and classification
12. Visual narrative matching
13. Horizontal no-subtitle rough preview
14. Feedback and local refinement
15. Publishing record and data retro

Stop after each stage unless the user explicitly asks to continue.

## Stage Outputs

| Stage | Output | Review Gate |
|---|---|---|
| Project kickoff | Project goal card | yes |
| Candidate judgment | Character feasibility judgment | yes |
| Source pool building | Source list, notes, evidence map | yes |
| Source state rating | thin / workable / strong source state | yes |
| Deep breakdown | contradictions, methods, turning points, evidence | yes |
| Thesis extraction | 3-5 candidate theses with support | yes |
| Structure draft | segment structure | yes |
| Recording script | 5-7 minute recordable script by default | yes |
| Review pass | revision notes and revised draft | yes |
| Voice planning | 3-5 voice sections and direction notes | yes |
| Video sorting | classified video asset table | yes |
| Visual matching | segment-to-visual matching table | yes |
| Rough preview | horizontal no-subtitle preview | yes |
| Refinement | local replacement list | yes |
| Retro | publishing data and workflow updates | yes |

## Source State Rating

Classify sources before deep analysis.

Thin source state:

- Only encyclopedic summaries, short posts, scattered secondary content, or unsourced clips.
- Allowed output: candidate judgment and research plan only.
- Do not write a deep breakdown script.

Workable source state:

- At least 2 high-value source categories are available.
- Allowed output: preliminary character breakdown and structure draft.
- Mark weak claims and missing evidence.

Strong source state:

- At least 3 high-value source categories are available.
- Preferably includes first-person material or process material.
- Allowed output: deep character breakdown, publishable script, and video planning.

High-value source categories:

- First-person material: interviews, autobiography, speeches, letters, diaries, creator notes.
- Process material: documentary, worksite footage, manuscripts, drafts, decisions, project retrospectives.
- Peer evaluation: collaborators, students, rivals, critics, researchers, historical witnesses.
- Controversy material: failures, criticism, misunderstanding, contradictions, conflicts.
- Historical background: era, industry, technology, institution, market, culture.
- Action evidence: works, decisions, results, key events, repeated behavior.

## Content Thesis Extraction

Use "content thesis extraction" rather than only "video thesis extraction" because not every character has video material.

Always produce 3-5 candidate theses before choosing one. For each thesis include:

- Core judgment
- 3-5 support points
- Available evidence
- Best content format: video, article, thread, short post, or later reserve angle
- Estimated length
- Visual feasibility, if video is planned
- Risk or missing evidence

If the character has strong video/process material, evaluate whether the thesis can be carried by images. If the character has mostly written material, prioritize intellectual tension, narrative tension, and verbal clarity.

## Script Principles

- Start from the character's central contradiction or creative system, not a biography timeline.
- Use life details only when they prove a larger point.
- Build a structure before full prose.
- Keep one main thesis per video, but preserve unused theses for later content expansion.
- After drafting, run a review pass for AI-like phrasing, overclaiming, weak transitions, and missing evidence.

## Voice Planning

For cloned voice or AI narration:

- Prefer 3-5 larger sections instead of many short fragments.
- Give each section a voice direction: pace, emotional state, pause style, and sentence ending behavior.
- Split only at natural breath or emotional turns.
- After generation, normalize loudness and use short fades at joins.
- If the user needs local replaceability more than continuity, allow smaller segments and note the tradeoff.

## Video Asset Sorting

When the user provides video source files, first classify before matching.

Use these classes:

- A: directly character-related material. The person, works, interviews, documentary, work process, historical footage.
- B: theme-related material. Similar space, action, industry, era, tool, environment, or background.
- C: emotional or behavioral support material. Office, writing, walking, reading, sea, window, hands, city, room, silence.

For each usable file or clip, record:

- File name or source
- Relation to the character
- Usable time range
- Visual type
- What appears on screen
- Mood and color
- Matching script segment
- Can be main image or only supporting image
- Risk notes

Use A material for main narrative, B material for explanation and background, and C material only for atmosphere, action support, transitions, or abstract passages. Never let support footage weaken or replace the character main line.

## Visual Narrative Matching

Do not merely assign "one sentence = one clip." Decide the visual job of each segment:

- Does this segment need the character on screen?
- Does it need action evidence?
- Does it need a specific object, space, or behavior?
- Can it use support footage without harming the main narrative?
- Will the next shot connect smoothly?
- Does this image clarify or distract from the spoken argument?

When the script mentions a concrete action or scene, prefer matching concrete footage: writing, drawing, office work, walking, speaking, reading, handling paper, looking at drafts, staying silent, or entering a space.

## Rough Preview Defaults

For the first watchable preview:

- Use 1920x1080 horizontal format by default for documentary or B站-style projects.
- Do not add subtitles in the first preview unless requested.
- Combine voice and visuals first; check whether the story works without text overlays.
- Use subtitles later as a separate design stage.
- Produce a preview record with path, duration, audio version, visual source, and known issues.

## Skill Routing Suggestions

When available, route sub-work to specialized skills:

- Source gathering: agent-reach, content-scraper, notes-research, notebooklm.
- Character/system analysis: hv-analysis, best-minds, insight.
- Writing: khazix-writer, original-writing, write-draft.
- Review and humanization: draft-review, ai-polish, humanizer-zh.
- Content calibration: cheat-score, cheat-predict, cheat-retro.
- Project memory: context-engineering-agent, neat-freak.

Use the minimum set of extra skills needed for the current stage. Do not load every related skill at once.

## Stop Conditions

Stop and ask for review when:

- A stage output is complete.
- Source state is thin but the user asks for deep conclusions.
- The main thesis choices are materially different.
- The script is ready for recording.
- Voice sections are ready to generate.
- Video assets need user-provided material.
- A rough preview has been exported.

If the user explicitly says "directly do this stage," finish that stage end-to-end, then stop.
