# InsaneAA Anti-Aliasing Script (VS port)

Original idea by tonik & tophf, edited and ported by DJATOM.
Use this script to fix ugly upscaled anime BDs.

# Processing chain: 
   1) extract luma from clip;
   2) apply Descale to it;
   3) resize luma with Spline36 for smooth edges;
   4) merge "smooth" clip with Descale clip according to descale_str;
   5) re-upscale it back to 1080p (or clip's original resolution) using eedi3+nnedi3 method;
   6) merge rescaled clip with source clip using lines mask. This should prevent noise and textures distortion;
   7) combine merged clip with color planes. 
 
# Prerequisites:
   - [eedi3/eedi3cl](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-EEDI3). You should build it from source, r1 is not working due to wrong namespace.
  - [nnedi3](https://github.com/dubhater/vapoursynth-nnedi3).
  - [nnedi3cl](https://github.com/HomeOfVapourSynthEvolution/VapourSynth-NNEDI3CL).
  - [descale](https://github.com/Irrational-Encoding-Wizardry/vapoursynth-descale).
  - [havsfunc](https://github.com/HomeOfVapourSynthEvolution/havsfunc).
  - [mvsfunc](https://github.com/HomeOfVapourSynthEvolution/mvsfunc).
 
# Basic usage:
```
import insaneAA
insaneAA.insaneAA(clip, eedi3Mode=dict(first=dict(mode='cpu', device=0), second=dict(mode='cpu', device=0)), nnedi3Mode=dict(first=dict(mode='opencl', device=0), second=dict(mode='znedi3', device=0)), descale_str=0.3, kernel='bilinear', descale_h=720, descale_w=None, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0, outputMode=0)
```
 - eedi3Mode: defaults - dict(first=dict(mode='cpu', device=-1), second=dict(mode='cpu', device=-1)). 'first' refers to 1st instance of filter call, 'second' - for 2nd call. Each call should have at least 'mode' key. You can specify 'device' if you need to use non-default GPU card. Valid values for 'mode' key: 'cpu', 'opencl'.
 - nnedi3Mode: defaults - dict(first=dict(mode='cpu', device=-1), second=dict(mode='cpu', device=-1)). 'first' refers to 1st instance of filter call, 'second' - for 2nd call. Each call should have at least 'mode' key. You can specify 'device' if you need to use non-default GPU card. Valid values for 'mode' key: 'cpu', 'znedi3', 'opencl'.
 - descale_str: strengh of mixing between descaled clip and Spline36 clip (for AA purposes). More strengh means more haloes, keep that in mind.
 - kernel: descaling kernel. Use getnative.py for determining native resolution and try various kernels to find the best suitable.
 - descale_h/descale_w: once you know native resolution, set descale_h. descale_w is almost useless, script will guess descaling width automaticaly. But you can set it, lol.
 - pscrn: nnedi3's prescreener for faster operation. Does nothing if nnedi3Cl is True.
 - alpha: eedi3's alpha.
 - beta: eedi3's beta.
 - gamma: eedi3's gamma.
 - outputMode: 1 - only rescale (GRAY), 2 - linemasked rescale (GRAY), 0 - linemasked rescale + UV. This option useful for, say, processing all clip into lossless file and masking high resolution details later or for imprting filtered luma into avisynth.
#### Please do something with FullHD captions, credits on OP/ED, etc! At least mask it or somehow exclude from processing. This script makes lines only worse there.
