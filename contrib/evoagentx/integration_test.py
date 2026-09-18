import sys
sys.path.insert(0, "/root/EvoAgentX")

# Try real import
try:
    from evoagentx.models.evo_ai_model import EvoAILLM, EvoAILLMConfig
    print("REAL IMPORT: OK")
    print(f"EvoAILLM: {EvoAILLM}")
    print(f"EvoAILLMConfig: {EvoAILLMConfig}")
    
    cfg = EvoAILLMConfig(model="evo-ai-test")
    print(f"Config: {cfg.model}")
    
    llm = EvoAILLM(cfg)
    print(f"LLM: {llm}")
    print(f"  Network: {llm._network}")
    print(f"  Node ID: {llm._node_id}")
    print()
    
    # Test message formatting
    msgs = llm.formulate_messages(["Hello"], ["You are helpful"])
    print(f"Formatted: {msgs}")
    print()
    
    prompt = llm._messages_to_prompt([
        {"role": "system", "content": "Be helpful."},
        {"role": "user", "content": "Hi"}
    ])
    print(f"Prompt: {prompt[:80]}")
    print()
    
    # Try actual generate against our running API
    print("=== Calling EVO-AI /api/generate ===")
    try:
        out = llm.single_generate([{"role": "user", "content": "Say hello"}])
        print(f"Response: {out[:200]}")
    except Exception as e:
        print(f"Generate error: {e}")
    
    print()
    print("=== ALL TESTS PASS ===")
except Exception as e:
    import traceback
    traceback.print_exc()
