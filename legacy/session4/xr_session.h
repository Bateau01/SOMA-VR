// xr_session.h — OpenXR session bound to SOMA's existing OpenGL context.
//
// Milestone 4: get SOMA's frame onto the headset. Stereo rendering is not
// solved yet, so both eyes receive the same image; what this establishes is the
// whole plumbing — instance, system, session, swapchains, frame loop, and real
// per-eye FOV and pose from the runtime.
//
// Loaded dynamically. openxr_loader.dll is resolved at runtime and every
// function goes through xrGetInstanceProcAddr, so the mod links against nothing
// and simply does nothing if no runtime is installed.
//
// The per-eye XrFovf this produces is the input PerspectiveOffAxis has been
// waiting for since v1: real asymmetric angles instead of a placeholder.

#pragma once
#include <windows.h>
#include <GL/gl.h>
#include <cstdio>
#include <cstring>

#define XR_USE_PLATFORM_WIN32
#define XR_USE_GRAPHICS_API_OPENGL
#include <openxr/openxr.h>
#include <openxr/openxr_platform.h>

namespace xrs {

struct EyeView {
    bool     valid = false;
    XrFovf   fov{};          // asymmetric angles, radians
    XrPosef  pose{};         // position + orientation in the reference space
};

struct Swap {
    XrSwapchain handle = XR_NULL_HANDLE;
    int32_t     width = 0, height = 0;
    uint32_t    imageCount = 0;
    XrSwapchainImageOpenGLKHR* images = nullptr;
};

class Session {
public:
    // Log callback so this module stays independent of the mod's logging.
    typedef void (*LogFn)(const char*, ...);

    bool Init(LogFn log);
    void Shutdown();

    // Call once per game frame, before the game's SwapBuffers.
    // Returns true when the runtime wants this frame rendered.
    bool BeginFrame();

    // Latest per-eye view. Valid only between BeginFrame and EndFrame.
    const EyeView& View(int eye) const { return mViews[eye]; }

    // Copy the game's default framebuffer into this eye's swapchain image.
    void SubmitEye(int eye, GLuint srcFbo, int srcW, int srcH);

    // The aspect the scene was actually rendered with. The submitted FOV must
    // describe what we drew, not what the runtime suggested, or the runtime
    // reprojects the wrong region and everything looks the wrong size.
    // The size the engine really renders at. Set BEFORE Start() so the
    // swapchain can match it and the capture blit stays 1:1.
    void  SetRenderSize(int w, int h) { mRenderW = w; mRenderH = h; }
    void  SetRenderAspect(float a) { mRenderAspect = a; }
    float RenderAspect() const     { return mRenderAspect; }

    // The headset's actual refresh rate, from predictedDisplayPeriod
    // (nanoseconds per frame). Headsets offer 72/90/120/144, so nothing about
    // the cadence should be assumed -- read it.
    // The pose the scene was actually rendered with, handed back by the
    // renderer so the submitted layer matches the image.
    void SetRenderedPose(int eye, const XrPosef& p) {
        if (eye >= 0 && eye < 2) { mRenderedPose[eye] = p; mHaveRendered[eye] = true; }
    }

    float DisplayRefreshHz() const {
        long long p = mFrameState.predictedDisplayPeriod;
        return (p > 0) ? (float)(1.0e9 / (double)p) : 0.0f;
    }

    void EndFrame();

    bool  Ready()   const { return mSessionRunning; }
    int32_t Width(int eye) const { return mSwap[eye].width; }
    int32_t Height(int eye) const { return mSwap[eye].height; }

    // Per-eye swapchain size, so the capture targets can match the headset
    // rather than the monitor. 2064x2208 against 2560x1440 squashes the image.
    bool SwapchainSize(int* w, int* h) const {
        if (!mSessionRunning || mSwap[0].width <= 0 || mSwap[0].height <= 0) return false;
        *w = (int)mSwap[0].width; *h = (int)mSwap[0].height; return true;
    }

private:
    bool LoadLoader();
    bool CreateInstanceAndSystem();
    bool CreateSession();
    bool CreateSwapchains();
    void PollEvents();

    LogFn mLog = nullptr;
    HMODULE mLoaderDll = nullptr;

    XrInstance mInstance = XR_NULL_HANDLE;
    XrSystemId mSystem   = XR_NULL_SYSTEM_ID;
    XrSession  mSession  = XR_NULL_HANDLE;
    XrSpace    mSpace    = XR_NULL_HANDLE;
    XrSessionState mState = XR_SESSION_STATE_UNKNOWN;
    bool mSessionRunning = false;

    Swap    mSwap[2];
    EyeView mViews[2];
    XrFrameState mFrameState{};
    XrCompositionLayerProjectionView mProjViews[2]{};
    bool mFrameBegun = false;
    bool mRectLogged = false;
    GLuint mBlitFbo = 0;

    // --- entry points, all resolved through xrGetInstanceProcAddr ---
    PFN_xrGetInstanceProcAddr            xrGetInstanceProcAddr_ = nullptr;
    PFN_xrCreateInstance                 pCreateInstance = nullptr;
    PFN_xrDestroyInstance                pDestroyInstance = nullptr;
    PFN_xrGetSystem                      pGetSystem = nullptr;
    PFN_xrCreateSession                  pCreateSession = nullptr;
    PFN_xrDestroySession                 pDestroySession = nullptr;
    PFN_xrCreateReferenceSpace           pCreateReferenceSpace = nullptr;
    PFN_xrDestroySpace                   pDestroySpace = nullptr;
    PFN_xrEnumerateViewConfigurationViews pEnumViewConfigViews = nullptr;
    PFN_xrEnumerateSwapchainFormats      pEnumSwapchainFormats = nullptr;
    PFN_xrCreateSwapchain                pCreateSwapchain = nullptr;
    PFN_xrDestroySwapchain               pDestroySwapchain = nullptr;
    PFN_xrEnumerateSwapchainImages       pEnumSwapchainImages = nullptr;
    PFN_xrAcquireSwapchainImage          pAcquireSwapchainImage = nullptr;
    PFN_xrWaitSwapchainImage             pWaitSwapchainImage = nullptr;
    PFN_xrReleaseSwapchainImage          pReleaseSwapchainImage = nullptr;
    PFN_xrBeginSession                   pBeginSession = nullptr;
    PFN_xrEndSession                     pEndSession = nullptr;
    PFN_xrWaitFrame                      pWaitFrame = nullptr;
    PFN_xrBeginFrame                     pBeginFrame = nullptr;
    PFN_xrEndFrame                       pEndFrame = nullptr;
    PFN_xrLocateViews                    pLocateViews = nullptr;
    PFN_xrPollEvent                      pPollEvent = nullptr;
    PFN_xrResultToString                 pResultToString = nullptr;

    // GL entry points needed for the blit, resolved via wglGetProcAddress.
    typedef void (APIENTRY *PFN_GenFramebuffers)(GLsizei, GLuint*);
    typedef void (APIENTRY *PFN_BindFramebuffer)(GLenum, GLuint);
    typedef void (APIENTRY *PFN_FramebufferTexture2D)(GLenum, GLenum, GLenum, GLuint, GLint);
    typedef void (APIENTRY *PFN_BlitFramebuffer)(GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLbitfield,GLenum);
    PFN_GenFramebuffers      glGenFramebuffers_ = nullptr;
    PFN_BindFramebuffer      glBindFramebuffer_ = nullptr;
    PFN_FramebufferTexture2D glFramebufferTexture2D_ = nullptr;
    PFN_BlitFramebuffer      glBlitFramebuffer_ = nullptr;
    bool LoadGL();

    void Say(const char* fmt, ...);
    bool Check(XrResult r, const char* what);

    float mRenderAspect = 0.0f;
    int   mRenderW = 0, mRenderH = 0;
    XrPosef mRenderedPose[2]{};
    bool    mHaveRendered[2]{false,false};
};

} // namespace xrs
