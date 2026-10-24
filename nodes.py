from pathlib import Path
import os
import folder_paths
import re

# Import ComfyUI files
import comfy.sd
import comfy.utils

class LoraTagLoader:
    def __init__(self):
        self.loaded_lora = None
        self.tag_pattern = "\<[0-9a-zA-Z\:\_\-\.\s\/\(\)\\\\]+\>"

    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "model": ("MODEL",),
                              "text": ("STRING", {"multiline": True}),
                              }}
    RETURN_TYPES = ("MODEL", "STRING")
    RETURN_NAMES = ("MODEL", "STRING")
    FUNCTION = "load_lora"

    CATEGORY = "loaders"

    def load_lora(self, model, text):
        # print(f"\nLoraTagLoader input text: { text }")

        founds = re.findall(self.tag_pattern, text)
        # print(f"\nfoound lora tags: { founds }")

        if len(founds) < 1:
            return (model, text)

        model_lora = model
        
        lora_files = folder_paths.get_filename_list("loras")
        for f in founds:
            tag = f[1:-1]
            pak = tag.split(":")
            type = pak[0]
            if type != 'lora':
                continue
            name = None
            if len(pak) > 1 and len(pak[1]) > 0:
                name = pak[1]
            else:
                continue
            wModel = 0
            try:
                if len(pak) > 2 and len(pak[2]) > 0:
                    wModel = float(pak[2])
            except ValueError:
                continue
            if name == None:
                continue
            # exact match on file name (with or without extension) or relative path, like A1111/Forge
            name = name.replace("\\", "/")
            lora_name = None
            for lora_file in lora_files:
                rel = lora_file.replace("\\", "/")
                if name in (Path(rel).stem, Path(rel).name, os.path.splitext(rel)[0], rel):
                    lora_name = lora_file
                    break
            if lora_name == None:
                print(f"bypassed lora tag: { (type, name, wModel) } >> { lora_name }")
                continue
            print(f"detected lora tag: { (type, name, wModel) } >> { lora_name }")

            lora_path = folder_paths.get_full_path("loras", lora_name)
            lora = None
            if self.loaded_lora is not None:
                if self.loaded_lora[0] == lora_path:
                    lora = self.loaded_lora[1]
                else:
                    temp = self.loaded_lora
                    self.loaded_lora = None
                    del temp

            if lora is None:
                lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
                self.loaded_lora = (lora_path, lora)

            model_lora, _ = comfy.sd.load_lora_for_models(model_lora, None, lora, wModel, 0)

        plain_prompt = re.sub(self.tag_pattern, "", text)
        return (model_lora, plain_prompt)

NODE_CLASS_MAPPINGS = {
    "LoraTagLoader": LoraTagLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # Loaders
    "LoraTagLoader": "Load LoRA Tag",
}
