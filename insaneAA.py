import vapoursynth as vs
import havsfunc as haf
import mvsfunc as mvf
import descale as dsc

# InsaneAA Anti-Aliasing Script (VS port) v0.1 (27.09.2017)
# 
# Original idea by tonik & toph, edited and ported by DJATOM.
# Use this script to fix ugly upscaled anime BDs.
# 
# Processing chain: 
#   1) extract luma from clip;
#   2) apply Descale to it;
#   3) resize luma with Spline36 for smooth edges;
#   4) merge "smooth" clip with Descale clip according to descale_str;
#   5) re-upscale it back to 1080p (or clip's original resolution) using eedi3+nnedi3 method;
#   6) merge rescaled clip with source clip using lines mask. This should prevent noise and textures distortion;
#   7) combine merged clip with color planes. 
# 
# Prerequisites:
#   eedi3/eedi3cl: https://github.com/HomeOfVapourSynthEvolution/VapourSynth-EEDI3 (you should build it from source, r1 is not working due to wrong namespace)
#   nnedi3: https://github.com/dubhater/vapoursynth-nnedi3
#   nnedi3cl: https://github.com/HomeOfVapourSynthEvolution/VapourSynth-NNEDI3CL
#   descale: https://github.com/Irrational-Encoding-Wizardry/vapoursynth-descale
#   havsfunc: https://github.com/HomeOfVapourSynthEvolution/havsfunc
#   mvsfunc: https://github.com/HomeOfVapourSynthEvolution/mvsfunc
# 
# Basic usage:
#   import insaneAA
#   insaneAA.insaneAA(clip, eedi3Cl=False, nnedi3Cl=True, descale_str=0.3, kernel='bilinear', descale_h=720, descale_w=None, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0, outputMode=0)
#     eedi3Cl/nnedi3Cl: switches between CL/CPU versions
#     descale_str: strengh of mixing between descaled clip and Spline36 clip (for AA purposes). More strengh means more haloes, keep that in mind.
#     kernel: descaling kernel. Use getnative.py for determining native resolution and try various kernels to find the best suitable.
#     descale_h/descale_w: once you know native resolution, set descale_h. descale_w is almost useless, script will guess descaling width automaticaly. But you can set it, lol.
#     pscrn: nnedi3's prescreener for faster operation. Does nothing if nnedi3Cl is True.
#     alpha: eedi3's alpha.
#     beta: eedi3's beta.
#     gamma: eedi3's gamma.
#     outputMode: 1 - only rescale (GRAY), 2 - linemasked rescale (GRAY), 0 - linemasked rescale + UV. This option useful for, say, processing all clip into lossless file and masking high resolution details later or for imprting filtered luma into avisynth.
#   Please do something with FullHD captions, credits on OP/ED, etc! At least mask it or somehow exclude from processing. This script makes lines worse there.
# 
# Changelog:
#   version 0.1
#     Initial release.

def insaneAA(c, eedi3Cl=False, nnedi3Cl=True, descale_str=0.3, kernel='bilinear', descale_h=720, descale_w=None, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0, outputMode=0):
    core = vs.get_core()
    if not isinstance(c, vs.VideoNode):
        raise TypeError('insaneAA: This is not a clip')
    w = c.width
    h = c.height
    gray_c = mvf.GetPlane(c, 0)
    descale_w = haf.m4((w * descale_h) / h) if descale_w is None else descale_w
    descale_natural = dsc.Descale(gray_c, descale_w, descale_h, kernel=kernel)
    descale_aa = core.resize.Spline36(gray_c, descale_w, descale_h)
    descale_clp = core.std.Merge(clipb=descale_natural, clipa=descale_aa, weight=descale_str)
    upscale = rescale(descale_clp, eedi3Cl, nnedi3Cl, w, h, pscrn, alpha, beta, gamma)
    if outputMode is 1:
        return upscale
    linemask = core.std.Maximum(core.std.Expr(core.std.Sobel(gray_c), "x 2 *"))
    merged_aa = core.std.MaskedMerge(gray_c, upscale, linemask)
    if outputMode is 2:
        return merged_aa
    return core.std.ShufflePlanes([merged_aa, mvf.GetPlane(c, 1), mvf.GetPlane(c, 2)], planes=[0, 0, 0], colorfamily=c.format.color_family)

def rescale(c, eedi3Cl=False, nnedi3Cl=True, dx=1920, dy=1080, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0):
    core = vs.get_core()
    ux = c.width * 2
    uy = c.height * 2
    c = eedi3_instance(c, eedi3Cl, nnedi3Cl, pscrn, alpha, beta, gamma)
    c = core.std.Transpose(clip=c)
    c = eedi3_instance(c, eedi3Cl, nnedi3Cl, pscrn, alpha, beta, gamma)
    c = core.std.Transpose(clip=c)
    return core.resize.Spline36(c, dx, dy, src_left=-0.5, src_top=-0.5, src_width=ux, src_height=uy)

def eedi3_instance(c, eedi3Cl=False, nnedi3Cl=True, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0):
    core = vs.get_core()
    if (eedi3Cl is True):
        return core.eedi3m.EEDI3CL(c, field=1, dh=True, alpha=alpha, beta=beta, gamma=gamma, vcheck=3, sclip=nnedi3_superclip(c, nnedi3Cl, pscrn))
    else:
        return core.eedi3m.EEDI3(c, field=1, dh=True, alpha=alpha, beta=beta, gamma=gamma, vcheck=3, sclip=nnedi3_superclip(c, nnedi3Cl, pscrn))

def nnedi3_superclip(c, nnedi3Cl=True, pscrn=1):
    core = vs.get_core()
    if (nnedi3Cl is True):
        return core.nnedi3cl.NNEDI3CL(c, field=1, dh=True, nsize=0, nns=4)
    else:
        return core.nnedi3.nnedi3(c, field=1, dh=True, nsize=0, nns=4, pscrn=pscrn)
