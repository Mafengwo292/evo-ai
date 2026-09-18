"""
core/llm.py
------------
模型加载与推理封装。

W1 阶段：使用 Hugging Face transformers 本地加载一个小模型。
W2+ 可以扩展为支持 OpenAI / DeepSeek / Claude API。
"""

from __future__ import annotations
from typing import List, Dict, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class LocalLLM:
    """本地 Hugging Face 模型封装"""

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ):
        self.model_name = model_name
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        print(f"[LLM] Loading model: {model_name} on {device} ...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32 if device == "cpu" else torch.float16,
            device_map=device,
        )
        self.model.eval()
        print("[LLM] Model loaded.")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
    ) -> str:
        """
        多轮对话推理。

        messages: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        system: 可选的 system prompt，会被加到最前面
        """
        # 把 system 拼到 messages 开头（如果 tokenizer 支持）
        if system and (not messages or messages[0].get("role") != "system"):
            messages = [{"role": "system", "content": system}] + messages

        # 用 chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # 只取新生成的部分
        new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
        response = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        return response.strip()
