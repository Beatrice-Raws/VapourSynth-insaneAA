# InsaneAA Anti-Aliasing Script (VS port)

Original idea by tonik & tophf, edited and ported by DJATOM.
Use this script to fix ugly upscaled anime BDs.

# Processing chain: 
   1) extract luma from clip;
   2) apply Descale to it;
   3) resize luma with Spline36 for smooth edges;
   4) merge "smooth" clip with Descale clip according to descale_strength;
   5) re-upscale it back to 1080p (or clip's original resolution) using eedi3+nnedi3 method;
   6) merge rescaled clip with source clip using lines mask. This should prevent noise and textures distortion;
   7) combine merged clip with color planes. 
 
# Prerequisites:
  - [eedi3/eedi3cl](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-EEDI3).
  - [nnedi3](https://github.com/dubhater/vapoursynth-nnedi3).
  - [znedi3](https://github.com/sekrit-twc/znedi3).
  - [nnedi3cl](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-NNEDI3CL).
  - [descale](https://github.com/Irrational-Encoding-Wizardry/vapoursynth-descale).
 
# Basic usage:
```python3
import insaneAA
insaneAA(clip, externalAA=None, externalMask=None, fasterAA=False, eedi3Mode='cpu', eedi3Device=-1, eedi3Opt=0, nnedi3Mode='nnedi3', nnedi3Device=-1, nnedi3Opt=0, descale_strength=0.3, kernel='bilinear', bicubic_b=1/3, bicubic_c=1/3, descale_width=None, descale_height=720, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0, nrad=2, mdis=20, outputMode=0, inputMode=0)
```
  - externalAA: if clip is passed, will use it instead of making rescale.
  - externalMask: pass external lines mask. Non-clip input will be ignored.
  - fasterAA: slightly different upscaling routine, proposed by ZASTIN. Sometimes might produce worse results. But indeed it's faster, yeah.
  - eedi3Mode: string with mode or tuple with two strings representing modes for first and second calls of eedi3.
  - eedi3Device: integer or tuple with two integers representing device IDs for first and second calls of eedi3.
  - eedi3Opt: Controls eedi3 opt related options. You can pass single value or tuple with two values for separated opt on the instances. Passed value should be int type.
  - nnedi3Mode: string with mode or tuple with two strings representing modes for first and second calls of nnedi3.
  - nnedi3Device: integer or tuple with two integers representing device IDs for first and second calls of nnedi3.
  - nnedi3Opt: Controls nnedi3 opt related options. You can pass single value or tuple with two values for separated opt on the instances. znedi3 expects string, classic nnedi3 - int, nnedi3cl ignores passed value. 
  - descale_strength: strength of mixing between descaled clip and Spline36 clip (for AA purposes). More strengh means more haloes, keep that in mind.
  - kernel: descaling kernel. Use getnative.py for determining native resolution and try various kernels to find the best suitable.
  - descale_height/descale_width: once you know native resolution, set descale_height. descale_width is almost useless, script will guess descaling width automatically. But you can set it, lol.
  - pscrn: nnedi3's prescreener for faster operation.
  - alpha: eedi3's alpha.
  - beta: eedi3's beta.
  - gamma: eedi3's gamma.
  - nrad: eedi3's nrad.
  - mdis: eedi3's mdis.
  - outputMode: 1 - only rescale (GRAY), 2 - linemasked rescale (GRAY), 0 - linemasked rescale + untouched colors. This option useful for, say, processing all clip into lossless file and masking high resolution details later or for importing filtered luma into avisynth.
  - inputMode: 1 - expect outputMode=1 like GRAY csp upscale. Anything else will skip applying lines mask.
#### Please do something with FullHD captions, credits on OP/ED, etc! At least mask it or somehow exclude from processing. This script makes lines only worse there.
