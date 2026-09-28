#include "xr_session.h"
#include <cmath>
#include <algorithm>
#include <cstdarg>

#define GL_FRAMEBUFFER_       0x8D40
#define GL_READ_FRAMEBUFFER_  0x8CA8
#define GL_DRAW_FRAMEBUFFER_  0x8CA9
#define GL_COLOR_ATTACHMENT0_ 0x8CE0
#define GL_SRGB8_ALPHA8_      0x8C43
#define GL_RGBA8_             0x8058

namespace xrs {

void Session::Say(const char* fmt, ...) {
    if (!mLog) return;
    char buf[512];
    va_list ap; va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap); va_end(ap);
    mLog("%s", buf);
}

bool Session::Check(XrResult r, const char* what) {
    if (XR_SUCCEEDED(r)) return true;
    char name[XR_MAX_RESULT_STRING_SIZE] = {0};
    if (pResultToString && mInstance) pResultToString(mInstance, r, name);
    const char* hint = "";
    switch ((int)r) {
        case  -2: hint = "runtime failure"; break;
        case  -3: hint = "out of memory"; break;
        case  -4: hint = "API version unsupported -- built against a newer SDK than the runtime"; break;
        case  -6: hint = "initialisation failed"; break;
        case  -8: hint = "feature unsupported"; break;
        case  -9: hint = "extension not present -- XR_KHR_opengl_enable may be missing"; break;
        case -12: hint = "handle invalid"; break;
        case -13: hint = "instance lost"; break;
        case -16: hint = "no runtime installed, or none set as active"; break;
        case -44: hint = "form factor unavailable -- headset not connected or asleep"; break;
        case -50: hint = "graphics requirements not queried before creating the session"; break;
        default:  hint = "see the OpenXR spec for this code"; break;
    }
    Say("  XR FAILED: %s -> %s (%d): %s", what, name[0] ? name : "?", (int)r, hint);
    return false;
}

bool Session::LoadLoader() {
    mLoaderDll = LoadLibraryA("openxr_loader.dll");
    if (!mLoaderDll) {
        Say("  openxr_loader.dll not found.");
        Say("  Put it beside Soma.exe, or install an OpenXR runtime");
        Say("  (SteamVR, Oculus and WMR all provide one).");
        return false;
    }
    xrGetInstanceProcAddr_ =
        (PFN_xrGetInstanceProcAddr)GetProcAddress(mLoaderDll, "xrGetInstanceProcAddr");
    if (!xrGetInstanceProcAddr_) { Say("  loader has no xrGetInstanceProcAddr"); return false; }
    // Bootstrap: these three are resolvable with a null instance.
    xrGetInstanceProcAddr_(XR_NULL_HANDLE, "xrCreateInstance", (PFN_xrVoidFunction*)&pCreateInstance);
    return pCreateInstance != nullptr;
}


bool Session::CreateInstanceAndSystem() {
    const char* exts[] = { XR_KHR_OPENGL_ENABLE_EXTENSION_NAME };

    XrInstanceCreateInfo ici{XR_TYPE_INSTANCE_CREATE_INFO};
    ici.enabledExtensionCount = 1;
    ici.enabledExtensionNames = exts;
    strcpy(ici.applicationInfo.applicationName, "hpl3vr");
    strcpy(ici.applicationInfo.engineName, "HPL3");
    ici.applicationInfo.applicationVersion = 1;
    ici.applicationInfo.engineVersion = 3;
    // XR_CURRENT_API_VERSION comes from the SDK headers and can exceed what the
    // installed runtime accepts (-4, XR_ERROR_API_VERSION_UNSUPPORTED). Nothing
    // here needs beyond 1.0, so ask for the version every runtime supports.
    ici.applicationInfo.apiVersion = XR_MAKE_VERSION(1, 0, 0);

    if (!Check(pCreateInstance(&ici, &mInstance), "xrCreateInstance")) return false;

    // Everything else resolves against the live instance.
    auto R = [&](const char* n, void** out) {
        xrGetInstanceProcAddr_(mInstance, n, (PFN_xrVoidFunction*)out);
    };
    R("xrResultToString",                    (void**)&pResultToString);
    R("xrDestroyInstance",                   (void**)&pDestroyInstance);
    R("xrGetSystem",                         (void**)&pGetSystem);
    R("xrCreateSession",                     (void**)&pCreateSession);
    R("xrDestroySession",                    (void**)&pDestroySession);
    R("xrCreateReferenceSpace",              (void**)&pCreateReferenceSpace);
    R("xrDestroySpace",                      (void**)&pDestroySpace);
    R("xrEnumerateViewConfigurationViews",   (void**)&pEnumViewConfigViews);
    R("xrEnumerateSwapchainFormats",         (void**)&pEnumSwapchainFormats);
    R("xrCreateSwapchain",                   (void**)&pCreateSwapchain);
    R("xrDestroySwapchain",                  (void**)&pDestroySwapchain);
    R("xrEnumerateSwapchainImages",          (void**)&pEnumSwapchainImages);
    R("xrAcquireSwapchainImage",             (void**)&pAcquireSwapchainImage);
    R("xrWaitSwapchainImage",                (void**)&pWaitSwapchainImage);
    R("xrReleaseSwapchainImage",             (void**)&pReleaseSwapchainImage);
    R("xrBeginSession",                      (void**)&pBeginSession);
    R("xrEndSession",                        (void**)&pEndSession);
    R("xrWaitFrame",                         (void**)&pWaitFrame);
    R("xrBeginFrame",                        (void**)&pBeginFrame);
    R("xrEndFrame",                          (void**)&pEndFrame);
    R("xrLocateViews",                       (void**)&pLocateViews);
    R("xrPollEvent",                         (void**)&pPollEvent);

    XrSystemGetInfo sgi{XR_TYPE_SYSTEM_GET_INFO};
    sgi.formFactor = XR_FORM_FACTOR_HEAD_MOUNTED_DISPLAY;
    if (!Check(pGetSystem(mInstance, &sgi, &mSystem), "xrGetSystem")) {
        Say("  No headset found. Is the runtime running and the HMD connected?");
        return false;
    }
    Say("  system acquired");
    return true;
}

bool Session::LoadGL() {
    HMODULE gl = GetModuleHandleA("opengl32.dll");
    if (!gl) return false;
    typedef PROC (WINAPI *PFN_GPA)(LPCSTR);
    PFN_GPA gpa = (PFN_GPA)GetProcAddress(gl, "wglGetProcAddress");
    if (!gpa) return false;
    glGenFramebuffers_      = (PFN_GenFramebuffers)(void*)gpa("glGenFramebuffers");
    glBindFramebuffer_      = (PFN_BindFramebuffer)(void*)gpa("glBindFramebuffer");
    glFramebufferTexture2D_ = (PFN_FramebufferTexture2D)(void*)gpa("glFramebufferTexture2D");
    glBlitFramebuffer_      = (PFN_BlitFramebuffer)(void*)gpa("glBlitFramebuffer");
    return glGenFramebuffers_ && glBindFramebuffer_ &&
           glFramebufferTexture2D_ && glBlitFramebuffer_;
}

bool Session::CreateSession() {
    // Bind to the context the game is already using. Must be called on the
    // render thread, with that context current.
    HDC   hdc = wglGetCurrentDC();
    HGLRC ctx = wglGetCurrentContext();
    if (!hdc || !ctx) { Say("  no current GL context on this thread"); return false; }

    // MANDATORY before xrCreateSession, even though we do not act on the answer.
    // Skipping it is what produced XR_ERROR_GRAPHICS_REQUIREMENTS_CALL_MISSING.
    {
        PFN_xrVoidFunction fn = nullptr;
        XrResult gr = xrGetInstanceProcAddr_(mInstance,
                          "xrGetOpenGLGraphicsRequirementsKHR", &fn);
        if (XR_FAILED(gr) || !fn) {
            Say("  could not resolve xrGetOpenGLGraphicsRequirementsKHR --"
                " is XR_KHR_opengl_enable enabled on the instance?");
            return false;
        }
        typedef XrResult (XRAPI_PTR *PFN_GetGLReq)(XrInstance, XrSystemId,
                                                   XrGraphicsRequirementsOpenGLKHR*);
        XrGraphicsRequirementsOpenGLKHR req{XR_TYPE_GRAPHICS_REQUIREMENTS_OPENGL_KHR};
        gr = ((PFN_GetGLReq)fn)(mInstance, mSystem, &req);
        if (!Check(gr, "xrGetOpenGLGraphicsRequirementsKHR")) return false;
        Say("  runtime wants OpenGL %d.%d - %d.%d (we have 4.6)",
            XR_VERSION_MAJOR(req.minApiVersionSupported),
            XR_VERSION_MINOR(req.minApiVersionSupported),
            XR_VERSION_MAJOR(req.maxApiVersionSupported),
            XR_VERSION_MINOR(req.maxApiVersionSupported));
    }

    XrGraphicsBindingOpenGLWin32KHR gb{XR_TYPE_GRAPHICS_BINDING_OPENGL_WIN32_KHR};
    gb.hDC = hdc; gb.hGLRC = ctx;

    XrSessionCreateInfo sci{XR_TYPE_SESSION_CREATE_INFO};
    sci.next = &gb;
    sci.systemId = mSystem;
    if (!Check(pCreateSession(mInstance, &sci, &mSession), "xrCreateSession")) return false;

    XrReferenceSpaceCreateInfo rs{XR_TYPE_REFERENCE_SPACE_CREATE_INFO};
    rs.referenceSpaceType = XR_REFERENCE_SPACE_TYPE_LOCAL;
    rs.poseInReferenceSpace.orientation.w = 1.0f;
    if (!Check(pCreateReferenceSpace(mSession, &rs, &mSpace), "xrCreateReferenceSpace"))
        return false;

    Say("  session + LOCAL reference space created");
    return true;
}

bool Session::CreateSwapchains() {
    uint32_t count = 0;
    pEnumViewConfigViews(mInstance, mSystem,
        XR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO, 0, &count, nullptr);
    if (count < 2) { Say("  runtime reported %u views, expected 2", count); return false; }

    XrViewConfigurationView views[2];
    for (int i = 0; i < 2; ++i) { views[i] = {XR_TYPE_VIEW_CONFIGURATION_VIEW}; }
    pEnumViewConfigViews(mInstance, mSystem,
        XR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO, 2, &count, views);

    // Prefer sRGB if the runtime offers it.
    uint32_t nfmt = 0;
    pEnumSwapchainFormats(mSession, 0, &nfmt, nullptr);
    int64_t fmts[64]; if (nfmt > 64) nfmt = 64;
    pEnumSwapchainFormats(mSession, nfmt, &nfmt, fmts);
    int64_t chosen = GL_RGBA8_;
    for (uint32_t i = 0; i < nfmt; ++i) if (fmts[i] == GL_SRGB8_ALPHA8_) { chosen = fmts[i]; break; }

    for (int eye = 0; eye < 2; ++eye) {
        XrSwapchainCreateInfo sc{XR_TYPE_SWAPCHAIN_CREATE_INFO};
        sc.usageFlags  = XR_SWAPCHAIN_USAGE_COLOR_ATTACHMENT_BIT |
                         XR_SWAPCHAIN_USAGE_TRANSFER_DST_BIT;
        sc.format      = chosen;
        sc.sampleCount = 1;
        // Match the swapchain to what the engine ACTUALLY renders, not the
        // runtime's recommendation. SOMA draws a 16:9 image; blitting that into
        // a 0.935 texture squashes it horizontally while we tell the runtime it
        // spans the full angle -- so the world slides against head motion. A
        // swapchain of the render size makes the blit 1:1 and the swim vanishes.
        // The runtime is free to scale this to the display; it does that well.
        uint32_t rw = views[eye].recommendedImageRectWidth;
        uint32_t rh = views[eye].recommendedImageRectHeight;
        if (mRenderW > 0 && mRenderH > 0) {
            rw = (uint32_t)mRenderW;
            rh = (uint32_t)mRenderH;
        }
        sc.width       = rw;
        sc.height      = rh;
        sc.faceCount   = 1;
        sc.arraySize   = 1;
        sc.mipCount    = 1;
        if (!Check(pCreateSwapchain(mSession, &sc, &mSwap[eye].handle), "xrCreateSwapchain"))
            return false;
        mSwap[eye].width  = (int32_t)sc.width;
        mSwap[eye].height = (int32_t)sc.height;

        uint32_t n = 0;
        pEnumSwapchainImages(mSwap[eye].handle, 0, &n, nullptr);
        mSwap[eye].images = new XrSwapchainImageOpenGLKHR[n];
        for (uint32_t i = 0; i < n; ++i)
            mSwap[eye].images[i] = {XR_TYPE_SWAPCHAIN_IMAGE_OPENGL_KHR};
        pEnumSwapchainImages(mSwap[eye].handle, n, &n,
            (XrSwapchainImageBaseHeader*)mSwap[eye].images);
        mSwap[eye].imageCount = n;

        Say("  eye %d swapchain %dx%d, %u images", eye, mSwap[eye].width, mSwap[eye].height, n);
    }
    return true;
}

bool Session::Init(LogFn log) {
    mLog = log;
    Say("");
    Say("OpenXR: initialising");
    if (!LoadLoader())            return false;
    if (!CreateInstanceAndSystem()) return false;
    if (!LoadGL())                { Say("  required GL entry points missing"); return false; }
    if (!CreateSession())         return false;
    if (!CreateSwapchains())      return false;
    glGenFramebuffers_(1, &mBlitFbo);
    Say("OpenXR: ready — waiting for the runtime to start the session");
    return true;
}

void Session::PollEvents() {
    XrEventDataBuffer ev{XR_TYPE_EVENT_DATA_BUFFER};
    while (pPollEvent && pPollEvent(mInstance, &ev) == XR_SUCCESS) {
        if (ev.type == XR_TYPE_EVENT_DATA_SESSION_STATE_CHANGED) {
            auto* s = (XrEventDataSessionStateChanged*)&ev;
            mState = s->state;
            if (mState == XR_SESSION_STATE_READY) {
                XrSessionBeginInfo bi{XR_TYPE_SESSION_BEGIN_INFO};
                bi.primaryViewConfigurationType = XR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO;
                if (Check(pBeginSession(mSession, &bi), "xrBeginSession")) {
                    mSessionRunning = true;
                    Say("OpenXR: session RUNNING — frames are going to the headset");
                }
            } else if (mState == XR_SESSION_STATE_STOPPING) {
                pEndSession(mSession);
                mSessionRunning = false;
                Say("OpenXR: session stopped");
            }
        }
        ev = {XR_TYPE_EVENT_DATA_BUFFER};
    }
}

bool Session::BeginFrame() {
    if (!mSession) return false;
    PollEvents();
    if (!mSessionRunning) return false;

    XrFrameWaitInfo fwi{XR_TYPE_FRAME_WAIT_INFO};
    mFrameState = {XR_TYPE_FRAME_STATE};
    if (!Check(pWaitFrame(mSession, &fwi, &mFrameState), "xrWaitFrame")) return false;

    XrFrameBeginInfo fbi{XR_TYPE_FRAME_BEGIN_INFO};
    if (!Check(pBeginFrame(mSession, &fbi), "xrBeginFrame")) return false;
    mFrameBegun = true;

    if (!mFrameState.shouldRender) return false;

    XrViewLocateInfo vli{XR_TYPE_VIEW_LOCATE_INFO};
    vli.viewConfigurationType = XR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO;
    vli.displayTime = mFrameState.predictedDisplayTime;
    vli.space = mSpace;
    XrViewState vs{XR_TYPE_VIEW_STATE};
    XrView v[2]; for (int i=0;i<2;++i) v[i] = {XR_TYPE_VIEW};
    uint32_t got = 0;
    if (!Check(pLocateViews(mSession, &vli, &vs, 2, &got, v), "xrLocateViews")) return false;

    const bool ok = (vs.viewStateFlags & XR_VIEW_STATE_POSITION_VALID_BIT) &&
                    (vs.viewStateFlags & XR_VIEW_STATE_ORIENTATION_VALID_BIT);
    for (int i = 0; i < 2; ++i) {
        mViews[i].valid = ok;
        mViews[i].fov   = v[i].fov;
        mViews[i].pose  = v[i].pose;
    }
    return true;
}

void Session::SubmitEye(int eye, GLuint srcFbo, int srcW, int srcH) {
    if (!mSessionRunning || eye < 0 || eye > 1) return;
    Swap& s = mSwap[eye];

    uint32_t idx = 0;
    XrSwapchainImageAcquireInfo ai{XR_TYPE_SWAPCHAIN_IMAGE_ACQUIRE_INFO};
    if (!Check(pAcquireSwapchainImage(s.handle, &ai, &idx), "xrAcquireSwapchainImage")) return;
    XrSwapchainImageWaitInfo wi{XR_TYPE_SWAPCHAIN_IMAGE_WAIT_INFO};
    wi.timeout = XR_INFINITE_DURATION;
    if (!Check(pWaitSwapchainImage(s.handle, &wi), "xrWaitSwapchainImage")) return;

    // Blit the game's framebuffer into this eye's swapchain texture.
    glBindFramebuffer_(GL_DRAW_FRAMEBUFFER_, mBlitFbo);
    glFramebufferTexture2D_(GL_DRAW_FRAMEBUFFER_, GL_COLOR_ATTACHMENT0_,
                            GL_TEXTURE_2D, s.images[idx].image, 0);
    glBindFramebuffer_(GL_READ_FRAMEBUFFER_, srcFbo);
    glBlitFramebuffer_(0, 0, srcW, srcH, 0, 0, s.width, s.height,
                       GL_COLOR_BUFFER_BIT, GL_LINEAR);
    glBindFramebuffer_(GL_FRAMEBUFFER_, 0);

    XrSwapchainImageReleaseInfo ri{XR_TYPE_SWAPCHAIN_IMAGE_RELEASE_INFO};
    pReleaseSwapchainImage(s.handle, &ri);

    mProjViews[eye] = {XR_TYPE_COMPOSITION_LAYER_PROJECTION_VIEW};
    // Submit the pose the image was RENDERED with, not the newer one located
    // at the last swap. If these differ the runtime reprojects against a pose
    // the image never had, and the result jitters even at an even cadence.
    mProjViews[eye].pose = mHaveRendered[eye] ? mRenderedPose[eye] : mViews[eye].pose;
    // We DRAW a symmetric frustum, because SOMA's deferred pass reconstructs
    // position from depth using tan(fov/2) and aspect, which only describe a
    // centred frustum. But we must not ASK the runtime to accept those angles:
    // it clamps to the headset's own asymmetric frustum rather than cropping,
    // and the image then spans 98x100 deg while being displayed as 94x98 --
    // 7.3% horizontal and 3.6% vertical magnification. Unequal, so it reads as
    // stretched rather than merely large.
    //
    // Instead: submit the runtime's OWN asymmetric fov, plus the sub-rectangle
    // of our symmetric render that exactly covers it. Nothing to clamp, and the
    // deferred pass still gets its centred frustum.
    {
        const XrFovf& f = mViews[eye].fov;
        float hv = std::max(std::fabs(f.angleUp),   std::fabs(f.angleDown));
        float hh = std::max(std::fabs(f.angleLeft), std::fabs(f.angleRight));
        if (mRenderAspect > 0.01f) {
            float widened = std::atan(std::tan(hv) * mRenderAspect);
            if (widened > hh) hh = widened;     // never draw NARROWER than asked
        }
        const float th = std::tan(hh), tv = std::tan(hv);

        // Map an angle to a pixel across the symmetric frustum we drew.
        auto px = [&](float a, int n, float half) {
            float v = (std::tan(a) + half) / (2.0f * half) * (float)n;
            if (v < 0.0f) v = 0.0f;
            if (v > (float)n) v = (float)n;
            return (int32_t)(v + 0.5f);
        };
        int32_t x0 = px(f.angleLeft,  s.width,  th);
        int32_t x1 = px(f.angleRight, s.width,  th);
        int32_t y0 = px(f.angleDown,  s.height, tv);   // GL origin is bottom-left
        int32_t y1 = px(f.angleUp,    s.height, tv);
        if (x1 <= x0 || y1 <= y0) {           // degenerate: fall back to full
            x0 = 0; y0 = 0; x1 = s.width; y1 = s.height;
            mProjViews[eye].fov = XrFovf{-hh, hh, hv, -hv};
        } else {
            mProjViews[eye].fov = f;          // the runtime's own angles, exactly
        }
        mProjViews[eye].subImage.imageRect.offset = {x0, y0};
        mProjViews[eye].subImage.imageRect.extent = {x1 - x0, y1 - y0};
        if (!mRectLogged) {
            mRectLogged = true;
            Say("submitting sub-rect %dx%d at (%d,%d) of %dx%d with the runtime's"
                " own asymmetric FOV -- nothing for it to clamp, so no"
                " magnification and no stretch",
                x1 - x0, y1 - y0, x0, y0, s.width, s.height);
        }
    }
    mProjViews[eye].subImage.swapchain = s.handle;
}

void Session::EndFrame() {
    if (!mFrameBegun) return;
    mFrameBegun = false;

    XrCompositionLayerProjection layer{XR_TYPE_COMPOSITION_LAYER_PROJECTION};
    layer.space = mSpace;
    layer.viewCount = 2;
    layer.views = mProjViews;
    const XrCompositionLayerBaseHeader* layers[] = { (XrCompositionLayerBaseHeader*)&layer };

    XrFrameEndInfo fei{XR_TYPE_FRAME_END_INFO};
    fei.displayTime = mFrameState.predictedDisplayTime;
    fei.environmentBlendMode = XR_ENVIRONMENT_BLEND_MODE_OPAQUE;
    fei.layerCount = mFrameState.shouldRender ? 1 : 0;
    fei.layers     = mFrameState.shouldRender ? layers : nullptr;
    pEndFrame(mSession, &fei);
}

void Session::Shutdown() {
    for (int i = 0; i < 2; ++i) {
        if (mSwap[i].handle && pDestroySwapchain) pDestroySwapchain(mSwap[i].handle);
        delete[] mSwap[i].images; mSwap[i].images = nullptr;
        mSwap[i].handle = XR_NULL_HANDLE;
    }
    if (mSpace && pDestroySpace)       pDestroySpace(mSpace);
    if (mSession && pDestroySession)   pDestroySession(mSession);
    if (mInstance && pDestroyInstance) pDestroyInstance(mInstance);
    mSpace = XR_NULL_HANDLE; mSession = XR_NULL_HANDLE; mInstance = XR_NULL_HANDLE;
    mSessionRunning = false;
    if (mLoaderDll) { FreeLibrary(mLoaderDll); mLoaderDll = nullptr; }
    Say("OpenXR: shut down");
}

} // namespace xrs
