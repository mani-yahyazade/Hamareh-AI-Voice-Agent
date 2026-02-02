Stores Architectural Decision Records (ADRs).

This answers:

Why did we choose this approach instead of alternatives?

✅ What goes inside
Short decision documents:

text
Documents/Decisions/
├── 0001-use-vosk-for-stt.md 
├── 0002-ignore-models-in-git.md
├── 0003-use-sing-box-for-proxy.md
Each file usually explains:

Context
Options considered
Decision made
Consequences
Example:

md
# 0001 – Use Vosk for Speech Recognition

## Context
Need offline speech recognition.

## Options
- Vosk
- Whisper
- Cloud APIs

## Decision
Use Vosk for offline, low-latency recognition.

## Consequences
+ No internet required
- Larger local model size