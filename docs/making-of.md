# Making the wallpapers

The wallpapers combine images generated with OpenAI's GPT Image 2.5 Sunburst (through OpenRouter) and rain composited locally. The image model draws the stained glass well, but it could not draw rain seen *through* backlit glass from inside. It kept putting glossy drops on the near side of the window. So the model produces dry glass and `tools/rain.py` adds the water.

## Tools

| Tool | Purpose |
| --- | --- |
| `tools/generate.sh` | Sends a prompt, plus optional reference images, to the OpenRouter Images API. Saves the result and a 3840×2160 crop to `drafts/`. |
| `tools/rain.py` | Adds rain running down the outside of the glass. |
| `tools/match_light.py` | Gives an edited image the lighting of the original it was edited from. |
| `tools/prompts/` | The prompts behind the final images, numbered in the order they were used. |

`generate.sh` reads `OPENROUTER_KEY` from `.env` at the repository root. `MODEL` overrides the default model. The Python tools run with [uv](https://docs.astral.sh/uv/), which installs their dependencies from the inline script metadata:

```bash
tools/generate.sh tools/prompts/05-dry.txt refs/angel-dawn.png
uv run tools/rain.py drafts/dry.jpg backgrounds/2-dawn-rain.jpg --scale 0.6 --drops 1800 --rivulets 45
```

`drafts/`, `refs/` and `.env` are not committed.

## Pipeline

1. `01-angel.txt`: the angel in stained glass, filling the frame, seen from inside.
2. `02-angel-inside.txt`: an edit of step 1 that moves the light behind the glass so it glows.
3. `03-angel-dawn.txt` and `03-angel-lightning.txt`: two edits of step 2, one lit by sunrise and one by a lightning flash.
4. `04-face-closeup.txt`: a close-up of the face. It takes two references: a crop of the face from step 3, so the face matches the full angel, and an earlier close-up that sets the framing and lighting.
5. `05-dry.txt`: removes any water the model drew in steps 3 and 4. A minimal edit like this keeps the face identical. The model also brightens the image, so `match_light.py` restores the original's lighting before the rain goes on.
6. `rain.py` adds the rain. The close-up uses the default scale. The full-angel images use `--scale 0.6 --drops 1800 --rivulets 45` with the same seed, so the rain falls in the same places in both.

The model returns 1536×864 images. The 4K wallpapers are Lanczos upscales.

## How the rain works

`rain.py` does not paint water over the image. It builds a height map of static drops and of rivulets that wander down the glass, leaving beads behind. From that map it computes how much light passes through each point:

- Wet glass transmits a little more light.
- The centre of a drop works as a lens and focuses light, so it gets brighter.
- The sloped rim of a drop bends light away, so it gets darker.

That light map is softened, because the water sits on the far side of the glass, and then multiplied into the image in linear light. The water shows up only where light comes through the glass, takes the colour of each piece, and disappears behind the lead and the painted lines. It reads as rain seen through the window from inside.

| Option | Effect |
| --- | --- |
| `--scale` | Size of the water relative to a face close-up |
| `--drops`, `--rivulets` | Amount of static drops and running streams |
| `--wet`, `--glow`, `--rim` | Brightening under water, brightening of drop centres, darkening of drop rims |
| `--blur` | Softness of the water behind the painted layer |
| `--seed` | Placement of the drops |

## How the lighting match works

`match_light.py` blurs both the original and the edited image, divides one by the other to get a smooth per-channel gain, and multiplies the edit by it. Fine detail comes from the edit and broad light and colour come from the original. This undoes the brightening the model applies when it edits an image.
