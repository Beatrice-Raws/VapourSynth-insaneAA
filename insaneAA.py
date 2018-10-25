from vapoursynth import core, VideoNode, GRAY, YUV
import descale

__version__ = 0.6

"""
InsaneAA Anti-Aliasing Script (VS port) v0.6 (25.10.2018)

Original idea by tonik & tophf, edited and ported by DJATOM.
Use this script to fix ugly upscaled anime BDs.

Processing chain: 
    1) extract luma from clip;
    2) apply Descale to it;
    3) resize luma with Spline36 for smooth edges;
    4) merge "smooth" clip with Descale clip according to descale_str;
    5) re-upscale it back to 1080p (or clip's original resolution) using eedi3+nnedi3 method;
    6) merge rescaled clip with source clip using lines mask. This should prevent noise and textures distortion;
    7) combine merged clip with color planes. 

Prerequisites:
    eedi3/eedi3cl: https://github.com/HomeOfVapourSynthEvolution/VapourSynth-EEDI3
    nnedi3: https://github.com/dubhater/vapoursynth-nnedi3
    nnedi3cl: https://github.com/HomeOfVapourSynthEvolution/VapourSynth-NNEDI3CL
    descale: https://github.com/Irrational-Encoding-Wizardry/vapoursynth-descale
    havsfunc: https://github.com/HomeOfVapourSynthEvolution/havsfunc

Basic usage:
    import insaneAA
    insaneAA.insaneAA(clip, externalAA=None, externalMask=None, fasterAA=False, eedi3Mode='cpu', eedi3Device=-1, nnedi3Mode='nnedi3', nnedi3Device=-1, descale_str=0.3, kernel='bilinear', descale_h=720, descale_w=None, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0, nrad=2, mdis=20, opt=(0,0), outputMode=0, inputMode=0)
        externalAA: if clip is passed, will use it intead of making rescale.
        externalMask: pass external lines mask. Non-clip input will be ignored.
        fasterAA: slightly different upscaling routine, proposed by ZASTIN. Sometimes might produce worse results. But indeed it's faster, yeah.
        eedi3Mode: string with mode or tuple with two strings representing modes for first and second calls of eedi3.
        eedi3Device: integer or tuple with two integers representing device IDs for first and second calls of eedi3.
        eedi3Opt: Controls eedi3 opt related options. You can pass single value or tuple with two values for separated opt on the instances. Passed value should be int type.
        nnedi3Mode: string with mode or tuple with two strings representing modes for first and second calls of nnedi3.
        nnedi3Device: integer or tuple with two integers representing device IDs for first and second calls of nnedi3.
        nnedi3Opt: Controls nnedi3 opt related options. You can pass single value or tuple with two values for separated opt on the instances. znedi3 expects string, classic nnedi3 - int (0 - use opt, 1 - disable, use C functions), nnedi3cl ignores passed value. 
        descale_str: strength of mixing between descaled clip and Spline36 clip (for AA purposes). More strengh means more haloes, keep that in mind.
        kernel: descaling kernel. Use getnative.py for determining native resolution and try various kernels to find the best suitable.
        descale_height/descale_width: once you know native resolution, set descale_height. descale_width is almost useless, script will guess descaling width automatically. But you can set it, lol.
        pscrn: nnedi3's prescreener for faster operation.
        alpha: eedi3's alpha.
        beta: eedi3's beta.
        gamma: eedi3's gamma.
        nrad: eedi3's nrad.
        mdis: eedi3's mdis.
        outputMode: 1 - only rescale (GRAY), 2 - linemasked rescale (GRAY), 0 - linemasked rescale + untouched colors. This option useful for, say, processing all clip into lossless file and masking high resolution details later or for importing filtered luma into avisynth.
        inputMode: 1 - expect outputMode=1 like GRAY csp upscale. Anything else will skip applying lines mask.
    Please do something with FullHD details! At least mask them or somehow exclude from processing.

Changelog:
    version 0.6b
        Fix: nnedi3 mode used slow C routines by default (behaviour differs from classic avisynth option).
    version 0.6
        New: parameters eedi3Opt/nnedi3Opt. Controls eedi3/nnedi3 opt related options.
        New: expose nrad/mdis parameters from eedi3. It's possible to improve speed with nearly the same results (say, use mdis=12 for 720p rescales).
        New: parameter 'externalMask'. Overrides built-in mask clip.
        Change: eedi3/nnedi3 mode related configuration. Now you can pass single 'cpu' or 'opencl' for eedi3Mode and single 'nnedi3', 'znedi3' or 'opencl' for nnedi3Mode. 
                If you need to use non-default device, set eedi3Device and nnedi3Device with proper values. 
                If you have 2 GPUs or wanna run 1st instance on GPU and second on CPU (or vice versa), just pass tuple with 2 values.
        Change: parameter 'ref' is now 'externalAA'.
        Change: parameter 'fasterAA' is now False by default.
    version 0.5
        New: inputMode. If set to 1, line masking on ref will be performed.
    version 0.4
        New: ref paramenter. You can supply processed clip there, it will be used instead of calculating new rescale.
        Speed-ups for AA processing by ZASTIN.
    version 0.3
        Major change in eedi3/nnedi3 options: use dict(first=dict(mode='cpu', device=-1), second=dict(mode='cpu', device=-1)) for eedi3Mode/nnedi3Mode. More in usage.
        Now you can pick znedi3 for sclip. The fastest nnedi3 option on my observation, but in complex scripts it might be better to use opencl nnedi3 for saving cpu cycles for other stuff.
    version 0.2
        Turn off OpenCL plugins by default.
        Split eedi3Cl for every eedi3 call, may improve performance on cheap GPUs.
    version 0.1
        Initial release.
"""

def insaneAA(clip, externalAA=None, externalMask=None, fasterAA=False, eedi3Mode='cpu', eedi3Device=-1, eedi3Opt=0, nnedi3Mode='nnedi3', nnedi3Device=-1, nnedi3Opt=0, descale_str=0.3, kernel='bilinear', descale_width=None, descale_height=720, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0, nrad=2, mdis=20, outputMode=0, inputMode=0):
    if not isinstance(clip, VideoNode):
        raise TypeError('insaneAA: this is not a clip.')
    if clip.format.color_family != YUV:
        raise TypeError('insaneAA: clip must be YUV colorspace.')
    width = clip.width
    height = clip.height
    gray_clip = core.std.ShufflePlanes(clip, 0, GRAY)
    if not isinstance(externalAA, VideoNode):
        descale_clip = revert_upscale(gray_clip, descale_str, kernel, descale_width, descale_height)
        upscale = rescale(descale_clip, fasterAA, eedi3Mode, eedi3Device, eedi3Opt, nnedi3Mode, nnedi3Device, nnedi3Opt, width, height, pscrn, alpha, beta, gamma, nrad, mdis)
    else:
        upscale = externalAA
    if outputMode == 1:
        return upscale
    if not isinstance(externalAA, VideoNode) or inputMode == 1:
        if  not isinstance(externalMask, VideoNode):
            linemask = core.std.Sobel(gray_clip).std.Expr("x 2 *").std.Maximum()
        else:
            linemask = externalMask
        aa_clip = core.std.MaskedMerge(gray_clip, upscale, linemask)
    else:
        aa_clip = externalAA
    if outputMode == 2:
        return aa_clip
    return core.std.ShufflePlanes([aa_clip, clip], planes=[0, 1, 2], colorfamily=clip.format.color_family)

def revert_upscale(clip, descale_str=0.3, kernel='bilinear', descale_width=None, descale_height=720):
    width = clip.width
    height = clip.height
    descale_width = m4((width * descale_height) / height) if descale_width == None else descale_width
    descale_natural = descale.Descale(clip, descale_width, descale_height, kernel=kernel)
    descale_aa = core.resize.Spline36(clip, descale_width, descale_height)
    return core.std.Merge(clipb=descale_natural, clipa=descale_aa, weight=descale_str)

def rescale(clip, fasterAA=False, eedi3Mode='cpu', eedi3Device=-1, eedi3Opt=0, nnedi3Mode='nnedi3', nnedi3Device=-1, nnedi3Opt=0, dx=None, dy=None, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0, nrad=2, mdis=20):
    ux = clip.width * 2
    uy = clip.height * 2
    if dx is None:
        raise ValueError('insaneAA: rescale lacks "dx" parameter.')
    if dy is None:
        raise ValueError('insaneAA: rescale lacks "dy" parameter.')
    eedi3Mode1,       eedi3Mode2 = validateInput(eedi3Mode,        str, 'insaneAA: eedi3Mode should be a string with valid mode or tuple with 2 strings providing valid modes.')
    nnedi3Mode1,     nnedi3Mode2 = validateInput(nnedi3Mode,       str, 'insaneAA: nnedi3Mode should be a string with valid mode or tuple with 2 strings providing valid modes.')
    eedi3Device1,   eedi3Device2 = validateInput(eedi3Device,      int, 'insaneAA: eedi3Device should be integer with valid device ID or tuple with 2 integers providing valid device IDs.')
    nnedi3Device1, nnedi3Device2 = validateInput(nnedi3Device,     int, 'insaneAA: nnedi3Device should be integer with valid device ID or tuple with 2 integers providing valid device IDs.')
    eedi3Opt1,         eedi3Opt2 = validateInput(eedi3Opt,         int, 'insaneAA: eedi3Opt should be integer with valid eedi3/eedi3cl opt value or tuple with 2 integers providing valid values.')
    nnedi3Opt1,       nnedi3Opt2 = validateInput(nnedi3Opt, (int, str), 'insaneAA: nnedi3Opt should be integer with valid eedi3/eedi3cl opt value or tuple with 2 integers providing valid values.')
    if fasterAA:
        clip = core.std.Transpose(clip)
        clip = eedi3_instance(clip, eedi3Mode1, eedi3Device1, eedi3Opt1, nnedi3Mode1, nnedi3Device1, nnedi3Opt1, pscrn, alpha, beta, gamma, nrad, mdis)
        clip = core.resize.Spline36(clip, height=dx, src_top=-0.5, src_height=ux)
        clip = core.std.Transpose(clip)
        clip = eedi3_instance(clip, eedi3Mode2, eedi3Device2, eedi3Opt2, nnedi3Mode2, nnedi3Device2, nnedi3Opt2, pscrn, alpha, beta, gamma, nrad, mdis)
        return core.resize.Spline36(clip, height=dy, src_top=-0.5, src_height=uy)
    else:
        clip = eedi3_instance(clip, eedi3Mode1, eedi3Device1, eedi3Opt1, nnedi3Mode1, nnedi3Device1, nnedi3Opt1, pscrn, alpha, beta, gamma, nrad, mdis)
        clip = core.std.Transpose(clip)
        clip = eedi3_instance(clip, eedi3Mode2, eedi3Device2, eedi3Opt2, nnedi3Mode2, nnedi3Device2, nnedi3Opt2, pscrn, alpha, beta, gamma, nrad, mdis)
        clip = core.std.Transpose(clip)
        return core.resize.Spline36(clip, dx, dy, src_left=-0.5, src_top=-0.5, src_width=ux, src_height=uy)

def eedi3_instance(clip, eedi3Mode='cpu', eedi3Device=-1, eedi3Opt=0, nnedi3Mode='nnedi3', nnedi3Device=-1, nnedi3Opt=0, pscrn=1, alpha=0.2, beta=0.25, gamma=1000.0, nrad=2, mdis=20):
    if eedi3Mode == 'opencl':
        return core.eedi3m.EEDI3CL(clip, field=1, dh=True, alpha=alpha, beta=beta, gamma=gamma, vcheck=3, nrad=nrad, mdis=mdis, sclip=nnedi3_superclip(clip, nnedi3Mode, nnedi3Device, nnedi3Opt, pscrn), device=nnedi3Device, opt=eedi3Opt)
    elif eedi3Mode == 'cpu':
        return core.eedi3m.EEDI3(clip, field=1, dh=True, alpha=alpha, beta=beta, gamma=gamma, vcheck=3, nrad=nrad, mdis=mdis, sclip=nnedi3_superclip(clip, nnedi3Mode, nnedi3Device, nnedi3Opt, pscrn), opt=eedi3Opt)
    else:
        raise ValueError('insaneAA: invalid eedi3 mode.')

def nnedi3_superclip(clip, nnedi3Mode='nnedi3', nnedi3Device=-1, opt=0, pscrn=1):
    if nnedi3Mode == 'opencl':
        return core.nnedi3cl.NNEDI3CL(clip, field=1, dh=True, nsize=0, nns=4, pscrn=pscrn, device=nnedi3Device)
    elif nnedi3Mode == 'znedi3':
        if opt == 0:
            _opt = True
            _x_cpu = ""
        elif opt == 1:
            _opt = False
            _x_cpu = ""
        else:
            _opt = True
            _x_cpu = str(opt)
        return core.znedi3.nnedi3(clip, field=1, dh=True, nsize=0, nns=4, pscrn=pscrn, opt=_opt, x_cpu=_x_cpu)
    elif nnedi3Mode == 'nnedi3':
        # swap 0 and 1 for nnedi3 to behave like a classic avisynth: 0 - use best available functions and 1 - use C functions
        if opt == 0:
            _opt = 1
        elif opt == 1:
            _opt = 0
        else:
            raise ValueError('insaneAA: invalid nnedi3 opt.')
        return core.nnedi3.nnedi3(clip, field=1, dh=True, nsize=0, nns=4, pscrn=pscrn, opt=_opt)
    else:
        raise ValueError('insaneAA: invalid nnedi3 mode.')

def validateInput(var, varType, errorString):
    if isinstance(var, varType):
        return var, var
    elif isinstance(var, tuple):
        if len(var) == 2 and isinstance(var[0], varType) and isinstance(var[1], varType):
            return var
        else:
            raise ValueError(errorString)
    else:
        raise ValueError(errorString)

def m4(x):
    return 16 if x < 16 else int(x // 4 + 0.5) * 4
