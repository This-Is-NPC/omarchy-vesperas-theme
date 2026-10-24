# Making the wallpapers

The wallpapers combine images generated with OpenAI's GPT Image 2.5 Sunburst (through OpenRouter) and rain composited locally. The image model draws the stained glass well, but it could not draw rain seen *through* backlit glass from inside. It kept putting glossy drops on the near side of the window. So the model produces dry glass and a small local script adds the water.

## Pipeline

1. The angel in stained glass, filling the frame, seen from inside.
2. An edit of step 1 that moves the light behind the glass so it glows.
3. Two edits of step 2, one lit by sunrise and one by a lightning flash.
4. A close-up of the face. It takes two references: a crop of the face from step 3, so the face matches the full angel, and an earlier close-up that sets the framing and lighting.
5. An edit that removes any water the model drew in steps 3 and 4. A minimal edit like this keeps the face identical. The model also brightens the image, so the original's lighting is restored before the rain goes on.
6. The rain is added. The full-angel images use smaller, denser water than the close-up, with the same seed, so the rain falls in the same places in both.

The model returns 1536×864 images. The 4K wallpapers are Lanczos upscales.

## How the rain works

The rain is not painted over the image. A height map is built from static drops and from rivulets that wander down the glass, leaving beads behind. From that map comes how much light passes through each point:

- Wet glass transmits a little more light.
- The centre of a drop works as a lens and focuses light, so it gets brighter.
- The sloped rim of a drop bends light away, so it gets darker.

That light map is softened, because the water sits on the far side of the glass, and then multiplied into the image in linear light. The water shows up only where light comes through the glass, takes the colour of each piece, and disappears behind the lead and the painted lines. It reads as rain seen through the window from inside.

## How the lighting match works

Both the original and the edited image are blurred, one is divided by the other to get a smooth per-channel gain, and the edit is multiplied by it. Fine detail comes from the edit and broad light and colour come from the original. This undoes the brightening the model applies when it edits an image.
