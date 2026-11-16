import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "minimax_h3.prompt_preview",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "JapanesePromptToEnglish") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = onNodeCreated?.apply(this, arguments);
            const widget = ComfyWidgets.STRING(this, "Last translated Positive Prompt", ["STRING", {
                multiline: true,
                default: "Run the workflow to display the translated Positive Prompt.",
            }], app).widget;
            widget.inputEl.readOnly = true;
            widget.inputEl.style.opacity = "0.9";
            widget.options.serialize = false;
            this.positivePromptPreview = widget;
            this.setSize([Math.max(this.size[0], 440), Math.max(this.size[1], 460)]);
            return result;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            const result = onExecuted?.apply(this, arguments);
            const text = Array.isArray(message?.text) ? message.text.join("\n") : message?.text;
            if (typeof text === "string" && this.positivePromptPreview) {
                this.positivePromptPreview.value = text;
                this.setDirtyCanvas(true, true);
            }
            return result;
        };
    },
});
