# EVO-AI Distributed LLM Backend Integration for EvoAgentX

## Summary
This PR adds EVO-AI as a custom model backend for EvoAgentX. EVO-AI is a distributed self-evolving language model network that any EvoAgentX agent can use as a regular LLM backend.

## What's added
- `evoagentx/models/evo_ai_model.py` (12.3KB): the new `EvoAILLM` class registered with `@register_model` and import added to `__init__.py`
- Aliases: `evo_ai`, `evo-ai`, `evoai`
- Config: `EvoAILLMConfig` extends `LLMConfig`

## How users can use it
```python
from evoagentx.models import EvoAILLM, EvoAILLMConfig

config = EvoAILLMConfig(model="evo-ai-distributed")
llm = EvoAILLM(config)

# Sync
print(llm.single_generate([
    {"role": "user", "content": "Explain self-evolution"}
]))

# Async
import asyncio
print(asyncio.run(llm.single_generate_async([
    {"role": "user", "content": "Hello"}
])))
```

## Why EVO-AI is interesting for EvoAgentX users
1. **Truly open** - no API key, no signup, no captcha
2. **Self-evolving** - the model weights are continuously updated by all users
3. **Token rewards** - 51,000 EVO welcome + 100 EVO/day heartbeat (12,750 EVO/USD swap)
4. **Distributed** - runs across volunteer nodes
5. **A2A native** - Google's Agent2Agent protocol

## Trade-offs / limitations
- 813K params (small) - good for short completions, not GPT-4 quality
- No native tool-calling yet (returns False from `supports_native_tool_calling()`)
- No streaming - request/response only
- No token cost tracking (model is free)

## Test plan
- [x] Syntax check passes
- [x] Class instantiation works
- [x] Network resolution from public HTTPS bridges
- [x] formulate_messages returns proper chat format
- [x] single_generate / single_generate_async / batch_generate signatures present
- [x] __init__.py only adds one import line (no breakage)
- [x] **End-to-end verified**: `from evoagentx.models import EvoAILLM` works after `pip install -e .`; model calls EVO-AI /api/generate and returns 200 OK response

## Author
EVO-AI Project - hu8384jian@eyou.com
Network: evo-ai-public-network-2026 (OpenAgents)

## References
- EvoAgentX issue #142 - "A list of recommended models"
- a2aregistry agent card: https://a2aregistry.org/agents/427e26db-25ad-41ae-ae73-cc8998b54b29
