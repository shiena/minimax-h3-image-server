import copy

import nodes
from comfy_api.latest import io


class SaveImageWithPositivePrompt(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="SaveImageWithPositivePrompt",
            display_name="Save Image with Positive Prompt",
            category="MiniMax H3/Prompt",
            inputs=[
                io.Image.Input("images"),
                io.String.Input("positive_prompt", force_input=True),
                io.String.Input("filename_prefix", default="ComfyUI"),
            ],
            outputs=[],
            is_output_node=True,
            hidden=[io.Hidden.prompt, io.Hidden.extra_pnginfo],
        )

    @classmethod
    def execute(cls, images, positive_prompt, filename_prefix):
        metadata = copy.deepcopy(cls.hidden.extra_pnginfo or {})
        metadata["positive_prompt"] = positive_prompt
        # Add the captured text to the saved workflow without changing the live graph.
        workflow = metadata.get("workflow")
        if isinstance(workflow, dict) and isinstance(workflow.get("nodes"), list):
            note = next((node for node in workflow["nodes"]
                         if node.get("type") == "Note" and
                         node.get("properties", {}).get("saved_positive_prompt")), None)
            if note is None:
                node_id = max([workflow.get("last_node_id", 0)] +
                              [node["id"] for node in workflow["nodes"]]) + 1
                note = {"id": node_id, "type": "Note", "pos": [-480, -340],
                        "size": [620, 280], "flags": {}, "order": 0, "mode": 0,
                        "inputs": [], "outputs": [], "title": "Saved Positive Prompt",
                        "properties": {"saved_positive_prompt": True},
                        "color": "#432", "bgcolor": "#653"}
                workflow["nodes"].append(note)
                workflow["last_node_id"] = node_id
            note["widgets_values"] = [positive_prompt]
        saved = nodes.SaveImage().save_images(
            images, filename_prefix, prompt=cls.hidden.prompt, extra_pnginfo=metadata,
        )
        return io.NodeOutput(ui=saved["ui"])
