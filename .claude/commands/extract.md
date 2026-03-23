---
description: Multi-dimensional analysis of a diary entry or session event to extract high-quality memories
---

# Multi-Dimensional Memory Extraction

Run three parallel analytical lenses on a diary entry or described event, synthesize with epistemic humility, then store the result via `store_memory`.

## Input

The user provides one of:
- A diary entry path: `/extract .claude/diary/YYYY-MM-DD-session-N.md`
- A free-form description of an event: `/extract "I spent 20 minutes debugging X before realizing Y"`
- "last" to process the most recent diary entry automatically

If "last":
```bash
ls -t /home/hung/MCPs/memory/.claude/diary/*.md 2>/dev/null | head -1
```

## Stage 1: Three Parallel Analyses

Run these three lenses mentally in parallel on the input:

### Lens A — Root Cause (Five Whys)

Ask why five times to find the fundamental cause:
1. What happened on the surface?
2. Why did that happen? (immediate cause)
3. Why did *that* happen? (contributing factor)
4. Why did *that* happen? (systemic cause)
5. Why did *that* happen? (root cause)

**Extract:** The deepest "why" — what fundamental pattern or assumption caused this?

### Lens B — Psychological Driver (Hidden Motivation)

Uncover the real motivation behind the behavior:
- What was I trying to achieve?
- What insecurity or assumption might be driving this?
- What would never be admitted out loud?
- What need is being served by this pattern?

**Extract:** The hidden motivation that explains why this pattern persists.

### Lens C — Prevention Strategy (Systems Thinking)

Identify feedback loops and build a gate function:
- What incentive structure caused this behavior?
- What feedback loop reinforced it?
- What corrective mechanism was missing?
- **Gate function:** What check would have prevented this?

**Extract:** A concrete prevention strategy — what to check *before* acting to avoid this mistake.

## Stage 2: Epistemic Humility Check

Before concluding, verify:

1. **Confidence** (1–5): How certain am I?
2. **Assumptions**: What am I assuming is true?
3. **Alternatives**: Could this be interpreted differently?
4. **Evidence**: What would make me wrong?
5. **Ambiguity**: Is this a genuine tradeoff where both approaches have merit?
6. **Lesson type**: Is this about HOW we solved it (methodology) or WHAT the solution was (technical)?

**If confidence < 4 OR genuine tradeoff detected:**
Acknowledge uncertainty. "This appears to be [X], but there are valid arguments for [Y]. The lesson depends on [context]."

**Critical distinction — methodology vs technical:**
- Methodology: "Gather evidence before hypothesizing" ✅
- Technical: "The hasResult check was too narrow" ❌ (implementation detail, context-specific)

When debugging shows multiple user corrections: the lesson is almost always **methodology**, not the specific technical fix.

## Stage 3: Synthesize the Memory

From the three lenses + epistemic check, write the final memory:

```
Title: [Clear, specific, actionable]

[2-4 sentence insight. Include enough context to apply it later. Be specific about WHY.]

Root Cause: [The fundamental why from Five Whys]

Psychological Driver: [The hidden motivation or assumption]

Prevention Gate:
  BEFORE [action]: Check [condition]. If fails: [alternative].

Why This Matters: [Time saved, errors avoided, understanding gained]

When to Apply:
- [Specific trigger condition]
- [Related scenario]

Epistemic Notes:
  Confidence: [1-5] — [reason]
  Lesson type: [Methodology / Technical]
  Assumptions: [what I'm assuming]
  Alternative reading: [if any]
```

## Stage 4: Store the Memory

Call `store_memory` with:
- `content`: the synthesized insight (full text from Stage 3)
- `trigger`: the "When to Apply" conditions as a short phrase
- `memory_type`: one of `rule | preference | pattern | case_study | constraint`
- `has_user_correction`: `true` if the event involved a user correction ("no", "wrong", "actually", "that's not right")
- `confidence`: map from epistemic scale (1=0.3, 2=0.5, 3=0.7, 4=0.85, 5=0.95)
- `tags`: comma-separated relevant tags

Example call:
```
store_memory(
  content="[full synthesis]",
  trigger="before adding features without usage evidence",
  memory_type="rule",
  has_user_correction=true,
  confidence=0.9,
  tags="anti-pattern,overengineering"
)
```

## Stage 5: Confirm

Show:
- The memory_id returned
- A one-line summary of what was extracted
- The trigger condition stored
- Whether `has_user_correction` was set

## Guidelines

- **Default to extracting** — when uncertain, capture with appropriate confidence
- **Failure > success** — mistakes and corrections are the most valuable lessons
- **Methodology > technical** — when multiple user corrections appear, extract the process pattern
- **Specific > generic** — "npm test failed silently when .env.test was missing" not "tests need environment"
- **Preserve the why** — include why this matters for future work, not just what happened
- **Acknowledge genuine tradeoffs** — don't force certainty when both approaches have merit

## Handling User Corrections

If the event contains user corrections ("no", "wrong", "actually", "that's not right"):
- Set `has_user_correction = true`
- These are high-confidence lessons (user explicitly identified the failure)
- Preserve the user's specific phrasing when it matters
- Extract what NOT to do as much as what TO do
