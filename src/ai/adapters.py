"""Foundation Model LLM Adapters supporting MiniMax, OpenAI, and Mock providers."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx

from src.core.config import settings
from src.domain.models import GraphMutation, WorldDelta

logger = logging.getLogger("LLMAdapters")


class BaseLLMAdapter(ABC):
    """Abstract interface for LLM narrative generation and delta extraction."""

    @abstractmethod
    async def stream_prose(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        """Streams narrative prose token by token."""
        pass

    @abstractmethod
    async def generate_delta(
        self,
        prose: str,
        graph_yaml: str,
        action: str,
        critique: Optional[str] = None,
    ) -> WorldDelta:
        """Extracts structured graph mutations from the generated narrative scene."""
        pass


class MiniMaxAdapter(BaseLLMAdapter):
    """MiniMax LLM Adapter using OpenAI-compatible Chat Completions API."""

    def __init__(self, api_key: str, base_url: str = "https://api.minimax.io/v1", model: str = "MiniMax-M3"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def stream_prose(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "stream": True,
        }

        in_think = False
        async with httpx.AsyncClient(timeout=45.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if not content:
                                    continue
                                
                                if "<think>" in content:
                                    in_think = True
                                    content = content.split("<think>")[0]
                                if in_think:
                                    if "</think>" in content:
                                        in_think = False
                                        content = content.split("</think>")[1]
                                    else:
                                        content = ""
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def generate_delta(
        self,
        prose: str,
        graph_yaml: str,
        action: str,
        critique: Optional[str] = None,
    ) -> WorldDelta:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        critique_block = f"\nAddress this previous critique: {critique}" if critique else ""
        system_instruction = (
            "You are a strict World State Machine compiler. Given the world graph, player action, and narrative prose, "
            "determine what discrete mutations occurred. Do not output reasoning or thinking blocks. "
            "Respond ONLY in valid JSON matching this schema:\n"
            "{\n"
            '  "mutations": [\n'
            '    {"action": "UPDATE_NODE_PROPERTY", "node_id": "string", "key": "string", "value": any},\n'
            '    {"action": "ADD_EDGE", "source": "string", "target": "string", "relation": "string", "value": {}}\n'
            "  ],\n"
            '  "new_facts": [\n'
            '    {"entity_id": "string", "fact": "string"}\n'
            "  ]\n"
            "}"
        )

        user_content = f"""World Graph Context (YAML):
{graph_yaml}

Player Action:
{action}

Narrative Prose:
{prose}
{critique_block}

Produce the structured mutations:"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            raw_text = resp.json()["choices"][0]["message"]["content"].strip()
            
            # Strip <think>...</think> tags if present
            import re
            cleaned_json = re.sub(r"<think>[\s\S]*?</think>", "", raw_text).strip()

            # Extract JSON block
            if "```" in cleaned_json:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_json)
                if match:
                    cleaned_json = match.group(1).strip()
            
            if "{" in cleaned_json and "}" in cleaned_json:
                start = cleaned_json.find("{")
                end = cleaned_json.rfind("}") + 1
                cleaned_json = cleaned_json[start:end]

            try:
                parsed = json.loads(cleaned_json)
                return WorldDelta.model_validate(parsed)
            except Exception as e:
                logger.warning("Failed to parse LLM delta JSON (%s). Raw: %s", e, raw_text)
                return WorldDelta(mutations=[], new_facts=[])


class MockLLMAdapter(BaseLLMAdapter):
    """Deterministic offline adapter for unit testing and local development without API keys."""

    async def stream_prose(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        tokens = [
            "You ", "draw ", "the ", "engraved ", "silver ", "key ", "from ", "your ", "satchel. ",
            "The ", "rusted ", "iron ", "lock ", "groans ", "as ", "the ", "tumblers ", "shift ",
            "with ", "a ", "heavy ", "click. ", "The ", "iron ", "portcullis ", "creaks ", "upward, ",
            "granting ", "passage ", "into ", "the ", "antechamber."
        ]
        for token in tokens:
            yield token

    async def generate_delta(
        self,
        prose: str,
        graph_yaml: str,
        action: str,
        critique: Optional[str] = None,
    ) -> WorldDelta:
        action_lower = action.lower()
        mutations: List[GraphMutation] = []
        new_facts = []

        if any(w in action_lower for w in ["unlock", "open", "silver key"]):
            mutations.append(
                GraphMutation(
                    action="UPDATE_NODE_PROPERTY",
                    node_id="gate_iron_portcullis",
                    key="locked",
                    value=False,
                )
            )
            new_facts.append({"entity_id": "gate_iron_portcullis", "fact": "The rusted iron portcullis was unlocked using the engraved silver key."})
        elif any(w in action_lower for w in ["move", "enter", "go"]):
            mutations.append(
                GraphMutation(
                    action="ADD_EDGE",
                    source="char_vespera",
                    target="loc_antechamber",
                    relation="located_in",
                )
            )
            mutations.append(
                GraphMutation(
                    action="REMOVE_EDGE",
                    source="char_vespera",
                    target="loc_crypt",
                    relation="located_in",
                )
            )

        return WorldDelta(mutations=mutations, new_facts=new_facts)


class LLMAdapterFactory:
    """Factory to instantiate the appropriate LLM provider adapter."""

    @staticmethod
    def get_adapter() -> BaseLLMAdapter:
        if settings.MINIMAX_API_KEY and settings.LLM_PROVIDER.lower() == "minimax":
            logger.info("Initializing MiniMaxAdapter (model=%s)", settings.MINIMAX_MODEL)
            return MiniMaxAdapter(
                api_key=settings.MINIMAX_API_KEY,
                base_url=settings.MINIMAX_BASE_URL,
                model=settings.MINIMAX_MODEL,
            )
        else:
            logger.info("Initializing MockLLMAdapter for deterministic offline execution")
            return MockLLMAdapter()
