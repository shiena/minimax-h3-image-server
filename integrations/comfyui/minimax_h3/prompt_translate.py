import os

import requests
from comfy_api.latest import io, ui


SYSTEM_PROMPT = """Translate the user's image description into an English prompt for an anime image generator.
Preserve all specified subjects, appearance, clothing, poses, camera angles, composition, lighting, and backgrounds.
Use clear descriptive sentences, not instructions addressed to an assistant.
Do not invent characters, clothing, poses, objects, or stylistic details not requested.
If the input is already English, preserve its meaning. Return only the English image description,
without explanations, headings, quotation marks, or reasoning."""


class JapanesePromptToEnglish(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="JapanesePromptToEnglish",
            display_name="Japanese Prompt to English (LLM)",
            category="MiniMax H3/Prompt",
            inputs=[
                io.String.Input("instruction", multiline=True, default=""),
                io.String.Input("base_url", default="http://127.0.0.1:1234/v1"),
                io.String.Input("model", default="prompt-translator"),
            ],
            outputs=[io.String.Output(display_name="english_prompt")],
        )

    @classmethod
    def execute(cls, instruction, base_url, model):
        if not instruction.strip():
            raise ValueError("Enter an image description in instruction.")
        if not model.strip():
            raise ValueError("Set model to the model ID provided by your LLM server.")
        headers = {}
        # Keep credentials out of workflows and generated image metadata.
        api_key = os.environ.get("COMFY_PROMPT_LLM_API_KEY", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        with requests.Session() as session:
            session.trust_env = False
            response = session.post(
                base_url.rstrip("/") + "/chat/completions",
                headers=headers,
                json={
                    "model": model.strip(),
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": instruction},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024,
                    "stream": False,
                },
                timeout=(10, 180),
            )
            response.raise_for_status()
            data = response.json()
        try:
            result = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("LLM returned no chat completion content.") from exc
        if not isinstance(result, str) or not result.strip():
            raise ValueError("LLM returned an empty translation.")
        if data["choices"][0].get("finish_reason") == "length":
            raise ValueError("LLM translation was truncated. Shorten the instruction.")
        return io.NodeOutput(result.strip(), ui=ui.PreviewText(result.strip()))
