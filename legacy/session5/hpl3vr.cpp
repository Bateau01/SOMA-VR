// hpl3vr.dll — SOMA / HPL3 VR mod
//
// Replaces recon v1..v20. Those were diagnostics; this is the mod skeleton.
// Everything here rests on facts established by that work and by Ghidra:
//
//   Soma.exe+0x2B46E0  SetProjectionMatrix(ctx, float* proj)
//                      Every projection the engine uses passes through here.
//                      The matrix arrives BY POINTER from the frustum (+0xd8),
//                      and the function early-outs on pointer identity, so we
//                      must write in place AND hand it a fresh pointer.
//   cFrustum           +0x18 far, +0x1c near, +0x20 aspect, +0x24 fov(rad)
//                      (HPL2 member order, confirmed intact in HPL3)
//
// Per-eye stereo needs no second hook: the engine computes MVP = P * V * M, so
// folding an eye translation into P as P*T places it in VIEW space, which is
// where eye separation belongs. Verified in stereo_test.cpp -- correct 1/d
// disparity falloff and zero vertical disparity.
//
// What is NOT done yet: rendering the scene twice per frame. Until that exists
// this alternates eyes on successive frames, which is enough to prove per-eye
// camera control end to end.

#include <windows.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <GL/gl.h>
#include <cstdio>
#include <cstring>
#include <cmath>
#include <cstdint>
#include <cstdarg>
#include "MinHook.h"
#include "hpl_vr_projection.h"
#include "xr_session.h"
#include "vp_math.h"

// ---------------------------------------------------------------- logging
static CRITICAL_SECTION g_lock;
static HMODULE g_selfModule = nullptr;
static FILE* g_log = nullptr;
static long  g_lines = 0;
static char  g_logPath[MAX_PATH] = {0};
static const long kMaxLines = 3000;

static void Log(const char* fmt, ...) {
    EnterCriticalSection(&g_lock);
    if (g_log && g_lines < kMaxLines) {
        va_list ap; va_start(ap, fmt);
        vfprintf(g_log, fmt, ap); va_end(ap);
        fputc('\n', g_log); fflush(g_log);
        if (++g_lines == kMaxLines) fprintf(g_log, "\n[log cap reached]\n");
    }
    LeaveCriticalSection(&g_lock);
}

static LONGLONG g_qpcFreq = 0;
static inline LONGLONG Now() { LARGE_INTEGER v; QueryPerformanceCounter(&v); return v.QuadPart; }

// Wall-clock seconds since the first call. Anything that should behave the same
// at 60 and 600 fps must be driven from this, not from a frame counter.
static LONGLONG g_t0 = 0;
static double NowSeconds() {
    LONGLONG n = Now();
    if (!g_t0) g_t0 = n;
    if (!g_qpcFreq) { LARGE_INTEGER f; QueryPerformanceFrequency(&f); g_qpcFreq = f.QuadPart; }
    return (double)(n - g_t0) / (double)g_qpcFreq;
}


static void OpenLog(HMODULE self) {
    char dir[MAX_PATH];
    if (GetModuleFileNameA(self, dir, MAX_PATH)) {
        char* slash = strrchr(dir, '\\');
        if (slash) { *(slash + 1) = '\0';
                     snprintf(g_logPath, MAX_PATH, "%shpl3vr.log", dir);
                     g_log = fopen(g_logPath, "w"); }
    }
    if (!g_log && GetTempPathA(MAX_PATH, dir)) {
        snprintf(g_logPath, MAX_PATH, "%shpl3vr.log", dir);
        g_log = fopen(g_logPath, "w");
    }
}

// ------------------------------------------------------------ mod state
struct Camera {                       // learned from the engine's own projection
    bool  known = false;
    float nearZ = 0.03f, farZ = 1000.0f;
    float aspect = 1.7778f, fovYDeg = 82.286f;
};
static Camera g_cam;

static volatile LONG g_hookOn    = 0;   // F2  substitution active
static volatile LONG g_stereoOn  = 0;   // F1  alternate eyes per frame
static volatile LONG g_fovPulse  = 0;   // F8  sanity check
static volatile LONG g_frame     = 0;
static volatile LONG g_eye       = 0;   // 0 = left, 1 = right
static float g_ipdMetres = 0.064f;      // DEAD: swept 64->800mm with no effect;
// the eye offset comes entirely from the OpenXR pose positions (steady 0.063 m)
// and 'applied translation term' stayed 0.00000 throughout. Kept only so the
// existing log lines still compile.
//
// WORLD SCALE. Separation, FOV and resolution are all verified correct, and the
// world still reads ~1.3x too large -- which points at SOMA's world unit not
// being a metre. We hand the runtime's pose translation (metres) straight to the
// camera, so if one SOMA unit is ~0.77 m the real parallax is short by that
// factor and the brain reads a bigger world. This multiplies the translation
// only; rotation is unitless and must not be touched.
// F1 / F4 now drive this live, since they did nothing as IPD controls.
static float g_worldScale = 1.0f;
// Multiplier on the per-eye offset, so the stereo can be verified live.
static float g_eyeOffsetScale = 1.0f;
// Apply the per-eye TRANSLATION in the frustum even when the camera hook owns
// the rotation. This is the only path that runs per pass with the right g_eye.
static bool g_eyeTranslateInFrustum = true;
// The camera object, so the render loop can force a view rebuild per eye pass.
static void* volatile g_cameraObj = nullptr;
static volatile LONG g_forcedRebuilds = 0;
// Eye and head measurements are deliberately separate.  The old build stored
// both in p[0], so a head lean contaminated the reported eye separation.
static volatile float g_dbgOff[2] = {0,0};
static volatile float g_dbgMag[2] = {0,0};
static volatile float g_dbgHead[3] = {0,0,0};
static volatile float g_dbgHeadRaw[3] = {0,0,0};
static volatile float g_dbgHeadDeltaT[3] = {0,0,0};
static volatile LONG g_frustumEyeOnlyHits = 0;
static volatile LONG g_frustumHeadSuppressed = 0;
// Automatic low-rate trace: two samples/second for roughly one minute.  It is
// reset when the XR origin latches or DELETE re-centres, and uses no new key.
static volatile LONG g_headTraceDiv = 0;
static volatile LONG g_headTraceBudget = 120;
// 6DOF head translation. The XR origin is latched on the first valid pose so
// the displacement is measured from where you started, not from XR's origin.
static bool  g_headTranslation = true;
static float g_headTransScale  = 1.0f;
// 0 raw, 1 raw -Z, 2 raw -X, 3 swap XZ, 4 RotY(+oY), 5 RotY(-oY), 6 off.
static volatile LONG g_headMode = 0;
static volatile float g_xrOrigin[3] = {0,0,0};
static volatile LONG  g_xrOriginSet = 0;
static volatile LONG  g_originDelay = 0;
static volatile LONG  g_dbgHits[2] = {0,0};
static volatile LONG g_eyeOffsetLogged = 0;
// Head pose, in view space. Rotation folds into the projection just as the eye
// offset does -- verified exact -- so no view-matrix setter is needed. But P*R
// is NOT projection-shaped, so it cannot be decoded back, which is why the
// projection is now rebuilt from the frustum's own fields instead of from the
// matrix we were handed (and have already overwritten).
static volatile LONG g_headTest = 0;    // F12: automatic yaw sweep
static float g_headYaw = 0.0f, g_headPitch = 0.0f;
// cFrustum, confirmed against the HPL2 member order
static const int kFrustumFar = 0x18, kFrustumNear = 0x1c,
                 kFrustumAspect = 0x20, kFrustumFov = 0x24, kFrustumProj = 0xd8;
static volatile LONG g_frustumChecked = 0;

// World-space UI recon. SOMA draws its HUD, notes and terminals in screen space
// with an ORTHOGRAPHIC projection, and every projection passes through this
// hook. Orthographic matrices are trivially distinguishable: the bottom row is
// (0,0,0,1) rather than (0,0,-1,0), because there is no perspective divide.
// Cataloguing them tells us which passes are UI before we touch anything.
struct OrthoSeen { float l, r, b, t; long n; };
static OrthoSeen g_orthoSeen[8];
static volatile LONG g_orthoCount = 0;
static CRITICAL_SECTION g_orthoLock;

static bool IsOrthographic(const float* m, int layout) {
    // layout 1 = column-major, 2 = row-major
    float w_z = (layout == 2) ? m[14] : m[11];   // perspective term
    float w_w = m[15];
    return fabsf(w_z) < 1e-5f && fabsf(w_w - 1.0f) < 1e-3f;
}

static void NoteOrtho(const float* m, int layout) {
    // Recover the ortho bounds. Column-major: x' = 2x/(r-l) + (l+r)/(l-r)
    float sx = (layout == 2) ? m[0]  : m[0];
    float sy = (layout == 2) ? m[5]  : m[5];
    float tx = (layout == 2) ? m[3]  : m[12];
    float ty = (layout == 2) ? m[7]  : m[13];
    if (fabsf(sx) < 1e-8f || fabsf(sy) < 1e-8f) return;
    float halfW = 1.0f / sx, halfH = 1.0f / sy;
    float cx = -tx * halfW, cy = -ty * halfH;
    float l = cx - halfW, r = cx + halfW, b = cy - halfH, t = cy + halfH;

    EnterCriticalSection(&g_orthoLock);
    for (int i = 0; i < 8; ++i) {
        if (g_orthoSeen[i].n) {
            if (fabsf(g_orthoSeen[i].r - r) < 1.0f && fabsf(g_orthoSeen[i].t - t) < 1.0f)
                { g_orthoSeen[i].n++; break; }
        } else {
            g_orthoSeen[i].l=l; g_orthoSeen[i].r=r;
            g_orthoSeen[i].b=b; g_orthoSeen[i].t=t; g_orthoSeen[i].n=1;
            InterlockedIncrement(&g_orthoCount);
            break;
        }
    }
    LeaveCriticalSection(&g_orthoLock);
}
static void* g_ctxPtr = nullptr;   // render context
static volatile LONG g_viewRot = 0;

// ctx+0x250 was NOT the view matrix. FUN_1402b46e0 does
// MatrixMul(out, ctx+0x250, ctx+0x190) with +0x190 the projection, and since
// MatrixMul(A,B) = A*B under HPL's column-vector convention, +0x250 is applied
// AFTER projection -- a post-projection matrix. Rotating it shifted each eye
// slightly in opposite directions, which is exactly what was observed.
//
// The real one is in cFrustum, and HPL2's declaration order gives the offsets:
//     cMatrixf m_mtxProj;      +0xd8   (already known)
//     cMatrixf m_mtxViewProj;  +0x118
//     cMatrixf m_mtxView;      +0x158
// which matches the reflection pass doing MatrixMul(frustum+0x158, reflect).
static const int kFrustumViewProj = 0x118;
static const int kFrustumView     = 0x158;
// cPlanef mPlane[6] follows m_mtxView. cPlanef is {a,b,c,d} floats = 16 bytes,
// and the three matrices before it are 64 each, so the array starts at +0x198.
// Culling used these unchanged while we rotated the view, which is why geometry
// popped at the edges.
static const int kFrustumPlanes   = 0x198;
static volatile LONG g_planesChecked = 0, g_planesOk = 0;

// Gribb-Hartmann, exactly as HPL2's cFrustum::UpdatePlanes does it:
// row3 +/- rowN of m_mtxViewProj, then normalise. vp is ROW-major, so
// m[r][c] == vp[r*4+c].
static void RebuildFrustumPlanes(void* frustum, const float* vp) {
    float* planes = (float*)((char*)frustum + kFrustumPlanes);

    if (!InterlockedExchange(&g_planesChecked, 1)) {
        // Confirm the offset before writing: a normalised plane has a unit
        // (a,b,c). If these are not planes, do not touch them.
        int good = 0;
        for (int i = 0; i < 6; ++i) {
            const float* q = planes + i * 4;
            float len = sqrtf(q[0]*q[0] + q[1]*q[1] + q[2]*q[2]);
            if (len > 0.9f && len < 1.1f) ++good;
        }
        InterlockedExchange(&g_planesOk, good >= 5 ? 1 : 0);
        Log("frustum+0x198: %d of 6 entries are unit-length planes -> %s",
            good, good >= 5 ? "plane array confirmed, culling will follow rotation"
                            : "NOT planes, leaving culling alone");
    }
    if (!InterlockedCompareExchange(&g_planesOk, 0, 0)) return;

    const int rowFor[6] = { 0, 0, 1, 1, 2, 2 };      // L R B T N F
    const float sign[6] = { +1, -1, +1, -1, +1, -1 };
    for (int i = 0; i < 6; ++i) {
        const float* r3 = vp + 12;
        const float* rN = vp + rowFor[i] * 4;
        float a = r3[0] + sign[i]*rN[0];
        float b = r3[1] + sign[i]*rN[1];
        float c = r3[2] + sign[i]*rN[2];
        float d = r3[3] + sign[i]*rN[3];
        float len = sqrtf(a*a + b*b + c*c);
        if (len > 1e-8f) { float inv = 1.0f/len; a*=inv; b*=inv; c*=inv; d*=inv; }
        float* q = planes + i * 4;
        q[0]=a; q[1]=b; q[2]=c; q[3]=d;
    }
}

// Apply the head rotation to the engine's own view matrix. Rotation belongs
// here, not in the projection: shadows and the deferred passes invert the
// projection to reconstruct position, so a rotated P breaks them, while a
// rotated V is exactly what they expect.
static volatile LONG g_viewChecked = 0;
// SetProjectionMatrix runs ~5 times per eye pass, and each call multiplied the
// view by R AGAIN -- the rotation compounded, and unevenly between eyes, which
// is why one side swung far harder than the other. Apply it once per pass.
static volatile LONG g_viewRotDone = 0;
// The engine refreshes the view once per FRAME, not per pass. Rotating in place
// therefore leaves pass 1 starting from pass 0's already-rotated matrix, so the
// right eye received R twice. Snapshot before the passes, restore before each.
static void* g_frustumPtr = nullptr;
static float g_pristineView[16], g_pristineVP[16], g_pristinePlanes[24];
static void* g_pristineFrustum = nullptr;  // exact top-level render frustum captured for this eye pair
static volatile LONG g_pristineValid = 0;
// The view before our head pose, captured wherever the pose is applied.
static float g_preRotView[16];
static volatile LONG g_preRotValid = 0;
// Three attempts to reason out why the right eye rotates further have failed.
// Trace the view's forward vector at every point it can change instead. The
// third row of the 3x3 is the camera's forward axis, so its yaw is a direct
// read of where the view is pointing.
static volatile LONG g_traceLeft = 0;
static void DumpForward(const char* when, const void* frustum) {
    if (!frustum || InterlockedCompareExchange(&g_traceLeft, 0, 0) <= 0) return;
    InterlockedDecrement(&g_traceLeft);
    const float* V = (const float*)((const char*)frustum + kFrustumView);
    // row-major cMatrixf: third ROW of the 3x3 is indices 8,9,10
    float fx = V[8], fy = V[9], fz = V[10];
    Log("    [trace] %-22s forward (%+.4f %+.4f %+.4f)  yaw %+7.2f deg",
        when, fx, fy, fz, atan2f(fx, fz) * 57.29577951f);
}

// True whenever something is rotating the view this frame -- the F12 sweep OR
// a live headset. Both need the pristine view restored between eye passes.
// Defined below, once the OpenXR session object exists.
static bool HeadPoseActive();
// Set once the camera hook is installed AND enabled.
static bool g_cameraHookActive = false;

// Fill q/pos with the current head pose for this eye. Shared so the early
// (pre-Render) and late (SetProjectionMatrix) applications cannot diverge.
static bool CurrentHeadPose(float* q, float* pos);

// Apply the head pose to the frustum right now, before the engine starts
// rendering. Returns true if it did.
static bool RotateFrustumEarly(void* frustum);

static void SnapshotView(void* frustum) {
    if (!frustum) return;
    const char* f = (const char*)frustum;
    memcpy(g_pristineView,   f + kFrustumView,     64);
    memcpy(g_pristineVP,     f + kFrustumViewProj, 64);
    memcpy(g_pristinePlanes, f + kFrustumPlanes,   96);
    g_pristineFrustum = frustum;
    InterlockedExchange(&g_pristineValid, 1);
}
static void RestoreView() {
    if (!g_pristineFrustum || !InterlockedCompareExchange(&g_pristineValid, 0, 0)) return;
    char* f = (char*)g_pristineFrustum;
    memcpy(f + kFrustumView,     g_pristineView,   64);
    memcpy(f + kFrustumViewProj, g_pristineVP,     64);
    memcpy(f + kFrustumPlanes,   g_pristinePlanes, 96);
}

// Rotate cFrustum's view matrix, and recompute m_mtxViewProj to match. The
// engine builds ViewProj during frustum setup, before this hook runs, so
// rotating the view alone would leave it stale.
// The grab is now identifiable: a body taking sustained horizontal force near
// the 300 N clamp. Taking it over means substituting our own spring-damper
// toward a target of our choosing -- which is exactly what a VR hand is.
static volatile LONG g_handOn = 0;
static const void*   g_heldBody = nullptr;
static float g_heldLastPos[3] = {0,0,0};
static bool  g_heldHavePos = false;
static float g_camWorld[3] = {0,0,0};      // camera position, from the view matrix
static float g_camFwd[3] = {0,0,-1}, g_camRight[3] = {1,0,0}, g_camUp[3] = {0,1,0};
// Where the right hand's fingers close to, in world space. Computed from the
// mesh each frame, so the grab target is always within finger reach.
static float g_gripCentre[3] = {0,0,0};
static volatile LONG g_gripCentreValid = 0;
// Alyx-style hands are standalone meshes at the controller pose -- no arms, no
// IK. So we draw our own geometry rather than unhiding Simon's body. First prove
// we can put a marker at a world position that tracks the camera correctly.
static float g_viewProjCM[16] = {1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1};
static volatile LONG g_haveVP = 0;
static volatile LONG g_handForces = 0;
// 50 N was far too low -- debris and doors cross it constantly, so the latch
// hopped between bodies and the hand drove whatever had most recently been
// pushed. The real grab runs 200-1200 N. Latch ONCE, hold it, and release only
// after the body has been quiet for a while.
static const float kGrabThreshold = 150.0f;   // legacy, no longer used to latch
static const float kMinHoriz      = 1.0f;     // enough to notice, any mass
static const double kHoldSeconds  = 0.33;     // sustained evidence before latching
static const double kQuietSeconds = 2.0;      // silence before letting go
static volatile LONG g_heldSawForce = 0;      // set by the hook, cleared each frame
static double g_heldQuiet = 0.0;
// Latching on "strongest this frame" was a competition, and a gently-held
// pencil (~2 N) always loses to anything else moving in the room -- which is why
// it only worked if you shook it. Track duration PER BODY instead, so a light
// object qualifies on its own merits.
static const double kStaleSeconds = 0.5;   // no evidence for this long -> drop
struct Cand { const void* body; double held; double lastSeen; bool seen; float horiz; };
static Cand g_cand[16];

static void NoteCandidate(const void* body, float horiz) {
    int slot = -1, weakest = 0;
    for (int i = 0; i < 16; ++i) {
        if (g_cand[i].body == body) { slot = i; break; }
        if (!g_cand[i].body) { slot = i; break; }
        if (g_cand[i].held < g_cand[weakest].held) weakest = i;
    }
    if (slot < 0) slot = weakest;
    if (g_cand[slot].body != body) {
        g_cand[slot].body = body; g_cand[slot].held = 0.0;
        g_cand[slot].lastSeen = 0.0;
    }
    g_cand[slot].seen = true;
    if (horiz > g_cand[slot].horiz) g_cand[slot].horiz = horiz;
}
static float g_handWantVel[3] = {0,0,0};
static volatile LONG g_velSubbed = 0;
static float g_handDist = 0, g_handDistMin = 1e9f, g_handDistMax = 0;
// Feed-forward state: commanding velocity from position error alone means the
// object only moves once it is already behind, so it trails a moving hand.
// Adding the hand's own velocity makes the error term a correction rather than
// the whole signal.
static float g_prevHand[3] = {0,0,0};
static bool  g_prevHandValid = false;
static LONGLONG g_prevHandTick = 0;
static float g_handSpeed = 0.0f;

// Our force reaches Newton (600 substitutions/window) yet the body moves 3 cm
// in ten seconds. Something is overriding it. SetVelocity would cancel any
// force; SetMatrix would make force irrelevant. Watch both on the held body.
static volatile LONG g_velCalls = 0, g_mtxCalls = 0, g_velOnHeld = 0, g_mtxOnHeld = 0;
static float g_lastVelSet[3] = {0,0,0};

// Per-eye pose as the runtime gives it, plus the forward vector it produces.
static float g_poseQ[2][4] = {{0,0,0,1},{0,0,0,1}};
static float g_posePos[2][3] = {{0,0,0},{0,0,0}};
// Mid-point between the two eyes, published where the poses are read so
// ApplyHeadPose can subtract it without needing the XR session declared yet.
static volatile float g_eyeMid[3] = {0,0,0};
// True interocular distance, refreshed from the live eye poses every frame.
static volatile float g_latchedSep = 0.063f;
static volatile LONG  g_eyeMidValid = 0;
static float g_poseFwd[2][3] = {{0,0,0},{0,0,0}};
static volatile LONG g_poseLog = 0;

// Quaternion -> column-major rotation.
static void QuatToMat(float x, float y, float z, float w, float* m) {
    float xx=x*x,yy=y*y,zz=z*z, xy=x*y,xz=x*z,yz=y*z, wx=w*x,wy=w*y,wz=w*z;
    m[0]=1-2*(yy+zz); m[1]=2*(xy+wz);   m[2]=2*(xz-wy);   m[3]=0;
    m[4]=2*(xy-wz);   m[5]=1-2*(xx+zz); m[6]=2*(yz+wx);   m[7]=0;
    m[8]=2*(xz+wy);   m[9]=2*(yz-wx);   m[10]=1-2*(xx+yy);m[11]=0;
    m[12]=0;m[13]=0;m[14]=0;m[15]=1;
}

// Full 6DOF head pose. V maps world -> camera, so inserting a head pose
// (Rh, th) means composing with its INVERSE: X = [Rh^T | -Rh^T*th], V' = X*V.
// Verified in pose_test.cpp: head position maps to the view origin, and
// rotation and translation stay independent.
static bool ApplyHeadPose(void* frustum, const float* quat, const float* pos) {
    if (!frustum) return false;
    // The camera hook supplies the ROTATION, and applying it here as well would
    // double it. But it CANNOT supply the per-eye translation: measured, the
    // camera hook runs ~3x per frame and every call reads g_eye == 0, because
    // the engine builds its view matrix outside the eye passes and both passes
    // reuse the cache. Eye 1 got zero hits, so the left eye's offset was drawn
    // to both images -- a camera slide, never parallax.
    //
    // THIS function is the one path that runs per pass with the correct g_eye
    // (RotateFrustumEarly is called inside the loop, after g_eye is set), and
    // FUN_1401FD540 confirms the frustum arrives as an ARGUMENT to Render
    // rather than living on the renderer, so per-eye state belongs here.
    //
    // So: skip the rotation when the camera hook owns it, but still apply the
    // eye TRANSLATION. That is the piece nothing else can deliver.
    const bool translateOnly = g_cameraHookActive;
    if (translateOnly && !g_eyeTranslateInFrustum) return false;
    if (InterlockedExchange(&g_viewRotDone, 1)) return false;   // once per pass

    char* f = (char*)frustum;
    float* Vp  = (float*)(f + kFrustumView);
    float* VPp = (float*)(f + kFrustumViewProj);

    // The view exactly as the engine had it, before we touch it. Available on
    // every path, unlike the render hook's snapshot.
    memcpy(g_preRotView, Vp, 64);
    InterlockedExchange(&g_preRotValid, 1);
    const float* Pp = (const float*)(f + kFrustumProj);

    float V[16]; memcpy(V, Vp, sizeof(V));
    if (!InterlockedExchange(&g_viewChecked, 1)) {
        bool bottomRow = fabsf(V[12])<1e-3f && fabsf(V[13])<1e-3f &&
                         fabsf(V[14])<1e-3f && fabsf(V[15]-1.0f)<1e-3f;
        float r0 = sqrtf(V[0]*V[0]+V[1]*V[1]+V[2]*V[2]);
        Log("frustum+0x158: bottom row %s, basis length %.3f -> %s",
            bottomRow ? "(0,0,0,1)" : "not (0,0,0,1)", r0,
            (bottomRow && fabsf(r0-1)<0.01f) ? "IS a rigid view matrix"
                                             : "NOT rigid, offset probably wrong");
    }
    // Camera world position = -R^T * t, needed to place a hand relative to the
    // player. V is row-major here: rotation in the 3x3, translation in the last column.
    {
        float t0=V[3], t1=V[7], t2=V[11];
        g_camWorld[0] = -(V[0]*t0 + V[4]*t1 + V[8]*t2);
        g_camWorld[1] = -(V[1]*t0 + V[5]*t1 + V[9]*t2);
        g_camWorld[2] = -(V[2]*t0 + V[6]*t1 + V[10]*t2);
    }
    hpl3vr::TransposeInPlace(V);                    // cMatrixf is row-major

    float R[16];
    if (translateOnly) {
        // Identity rotation: the camera hook already put the head orientation
        // into the view. Only the eye displacement is added here.
        memset(R, 0, sizeof(R));
        R[0] = R[5] = R[10] = R[15] = 1.0f;
    } else {
        QuatToMat(quat[0], quat[1], quat[2], quat[3], R);
    }
    float X[16];
    for (int r = 0; r < 3; ++r)
        for (int c = 0; c < 3; ++c) X[c*4+r] = R[r*4+c];         // Rh^T
    X[3]=X[7]=X[11]=0; X[15]=1;
    // In translate-only mode the camera has already been moved to the head
    // centre, so subtract the mid-point and pass just this eye's displacement.
    float p[3] = { pos[0], pos[1], pos[2] };
    if (translateOnly) {
        if (InterlockedCompareExchange(&g_eyeMidValid, 0, 0)) {
            // NO ROTATION. The eye offset in the CAMERA's own view space is by
            // definition (+-halfSep, 0, 0): the camera has already been
            // oriented by the time this runs, so its X axis IS the interocular
            // axis. Writing that directly removes the frame question entirely.
            //
            // Rotating the XR displacement by the head quaternion was wrong
            // because the camera's final orientation is playerYaw + headPose,
            // not headPose alone. The leftover showed up as the X component
            // swinging from 0.004 to 0.031 with view direction while the
            // magnitude stayed a correct 0.0315 -- the offset was being pushed
            // into Y and Z. That is why the eyes would not fuse (vertical and
            // depth misalignment) and why the world swam when you turned.
            // halfSep MUST come from the two eye poses, which are always
            // current. It used to be |pos - g_eyeMid|, and g_eyeMid is the
            // 6DOF ORIGIN mid-point -- so the "eye separation" grew with how
            // far you had moved from where the origin latched. At 0.63 m from
            // origin it read 0.667 m instead of 0.0315: a 1.3 m interocular
            // distance. That is the jitter and the broken lighting, and it
            // also means every mode comparison so far was made through a
            // corrupted stereo baseline.
            float halfSep = 0.5f * g_latchedSep;
            if (halfSep < 1e-4f) halfSep = 0.0315f;   // sane fallback
            int ei = (int)InterlockedCompareExchange(&g_eye, 0, 0);
            float sgn = (ei == 0) ? -1.0f : +1.0f;      // eye 0 = left

            // This path owns ONLY the per-eye displacement.  Head-centre
            // translation is already written once, upstream, into camera+0x74.
            // Mixing the two here was the double-writer that made a fixed lean
            // depend on pitch and roll: the same XR displacement was transformed
            // once by the camera path and again by this frustum path.
            const float eyeOffset = sgn * halfSep * g_eyeOffsetScale;
            p[0] = eyeOffset;
            p[1] = 0.0f;
            p[2] = 0.0f;

            if (ei >= 0 && ei < 2) {
                g_dbgOff[ei] = eyeOffset;
                g_dbgMag[ei] = fabsf(eyeOffset);
                InterlockedIncrement(&g_dbgHits[ei]);
            }
            InterlockedIncrement(&g_frustumEyeOnlyHits);

            // Positive control for the suppression diagnostic: this counter can
            // only increment after ApplyHeadPose has reached the live per-pass
            // eye path.  A non-zero value therefore proves the code ran, while
            // p[1]/p[2] and the head component remain exactly zero here.
            LONG hm = InterlockedCompareExchange(&g_headMode, 0, 0);
            if (g_headTranslation
                && InterlockedCompareExchange(&g_xrOriginSet, 0, 0)
                && hm != 6)
                InterlockedIncrement(&g_frustumHeadSuppressed);
        } else {
            p[0] = p[1] = p[2] = 0.0f;
        }
    }
    for (int r = 0; r < 3; ++r)
        X[12+r] = -(X[r]*p[0] + X[4+r]*p[1] + X[8+r]*p[2]);

    float Vn[16]; vpm::Mul4x4(X, V, Vn);            // V' = X * V

    // UNIFORM WORLD SCALE. V'' = Scale(1/S) * V' divides every world distance
    // by S, so the world shrinks and recedes together -- which is what makes
    // objects look smaller WITHOUT touching the FOV. Because the frustum still
    // matches what we submit to the runtime, angular correspondence is intact
    // and head rotation stays locked to the world. This is the same thing a
    // natively-authored VR build gets for free by modelling at metric scale.
    //
    // Column-major at this point (after the transpose above), so the first
    // three columns are the basis and the fourth is the translation; scaling
    // all four rows of the upper 3x4 scales the whole view uniformly.
    if (g_worldScale > 0.01f && fabsf(g_worldScale - 1.0f) > 0.001f) {
        const float inv = 1.0f / g_worldScale;
        for (int c = 0; c < 4; ++c) {
            Vn[c*4+0] *= inv; Vn[c*4+1] *= inv; Vn[c*4+2] *= inv;
        }
    }

    float P[16]; memcpy(P, Pp, sizeof(P)); hpl3vr::TransposeInPlace(P);
    float VPn[16]; vpm::Mul4x4(P, Vn, VPn);         // ViewProj' = P * V'

    DumpForward("pose: before", frustum);
    hpl3vr::TransposeInPlace(Vn);  memcpy(Vp,  Vn,  sizeof(Vn));
    DumpForward("pose: after", frustum);
    {   // forward = -Z row of the row-major view
        const float* Vn2 = (const float*)((const char*)frustum + kFrustumView);
        int ei = (int)InterlockedCompareExchange(&g_eye,0,0);
        if (ei >= 0 && ei < 2) {
            g_poseFwd[ei][0] = -Vn2[8]; g_poseFwd[ei][1] = -Vn2[9]; g_poseFwd[ei][2] = -Vn2[10];
        }
    }
    hpl3vr::TransposeInPlace(VPn); memcpy(VPp, VPn, sizeof(VPn));
    RebuildFrustumPlanes(frustum, VPn);   // VPn is row-major here
    InterlockedIncrement(&g_viewRot);
    return true;
}
// The frustum's stored layout, sampled ONCE while it is still pristine. HPL's
// cMatrixf is row-major, and BuildFromFrustum produces column-major, so writing
// without converting hands the engine a transposed projection -- which is what
// brought the blue wash back.
static volatile LONG g_frustumLayout = 0;   // 1 = column-major, 2 = row-major

static void UpdateCameraWorld(const void* frustum) {
    if (!frustum) return;
    const float* V = (const float*)((const char*)frustum + kFrustumView);
    // Row-major view: rotation in the 3x3, translation in the last column.
    // Camera world position = -R^T * t.
    float t0 = V[3], t1 = V[7], t2 = V[11];
    g_camWorld[0] = -(V[0]*t0 + V[4]*t1 + V[8]*t2);
    g_camWorld[1] = -(V[1]*t0 + V[5]*t1 + V[9]*t2);
    g_camWorld[2] = -(V[2]*t0 + V[6]*t1 + V[10]*t2);
    // Rows of the row-major view are the camera's world-space axes; forward is
    // -Z under HPL's right-handed convention.
    g_camRight[0]=V[0]; g_camRight[1]=V[1]; g_camRight[2]=V[2];
    g_camUp[0]=V[4];    g_camUp[1]=V[5];    g_camUp[2]=V[6];
    g_camFwd[0]=-V[8];  g_camFwd[1]=-V[9];  g_camFwd[2]=-V[10];

    // Keep the ViewProj for drawing our own geometry. cMatrixf is row-major;
    // GL wants column-major, so transpose on the way out.
    const float* VP = (const float*)((const char*)frustum + kFrustumViewProj);
    for (int r = 0; r < 4; ++r)
        for (int c = 0; c < 4; ++c) g_viewProjCM[c*4+r] = VP[r*4+c];
    InterlockedExchange(&g_haveVP, 1);
}

// Aspect we wrote into the frustum for the headset. FrustumIsMain must accept
// it, or the camera stops being recognised the frame after we widen it.
static float g_xrAspect = 0.0f;
// How much wider than the headset FOV to cull. The engine decides visibility
// from its own camera direction, so head rotation can look at geometry that was
// already discarded; a wider cone keeps more of it alive at some GPU cost.
static float g_cullMargin = 1.0f;   // RETIRED. Widening these fields breaks the
                                    // deferred lighting; ',' and '.' now do nothing.
static volatile LONG g_projXrPath = 0, g_projFallback = 0;
// FOV implied by the matrix we hand the engine, recovered from its own terms.
static float g_projFovH = 0, g_projFovV = 0, g_wantFovH = 0, g_wantFovV = 0;
static volatile LONG g_vpW = 0, g_vpH = 0;
static volatile LONG g_srcFboW = 0, g_srcFboH = 0;
static volatile LONG g_capRectLogged = 0;
static volatile LONG g_rejNotStereo = 0, g_rejXrOff = 0, g_rejNotReady = 0, g_rejInvalid = 0;

static bool FrustumIsMain(const void* frustum) {
    if (!frustum || !g_cam.known) return false;
    const char* f = (const char*)frustum;
    float nearZ  = *(const float*)(f + kFrustumNear);
    float aspect = *(const float*)(f + kFrustumAspect);
    float fovRad = *(const float*)(f + kFrustumFov);
    if (!(nearZ > 0.0005f && nearZ < 10.0f && aspect > 0.1f && aspect < 10.0f &&
          fovRad > 0.2f && fovRad < 3.0f)) return false;
    if (fabsf(nearZ - g_cam.nearZ) > 0.20f * g_cam.nearZ) return false;
    // The original aspect, OR the headset aspect we may have written into this
    // same frustum. Matching only the original made the camera unrecognisable
    // one frame after widening it, which stopped the right eye being substituted.
    if (fabsf(aspect - g_cam.aspect) < 0.02f * g_cam.aspect) return true;
    float widened = g_xrAspect;
    return widened > 0.0f && fabsf(aspect - widened) < 0.02f * widened;
}
// Alternating every frame blurs the two eye positions together, so the effect
// is visible but its MAGNITUDE is not. Hold each eye for a while instead: the
// view then steps left, holds, steps right, holds, and the size of that step
// is obvious. F5 / F6 adjust it.
static volatile LONG g_eyeHoldFrames = 45;
static volatile LONG g_projEyeLogged = 0;
static volatile LONG g_appliedShift  = 0;   // last translation term, x1e6

static volatile LONG g_calls = 0, g_subbed = 0, g_rotPassOnly = 0;
// Declared here because BuildEyeProjection below needs them; the double-render
// machinery itself lives further down.
static volatile LONG g_doubleOn = 0, g_sbsOn = 0;
// F10 substituted only 60 of 3602 calls, and the split never fired. Measure
// both rather than guess: count why IsMainCamera rejects, and record which
// viewport sizes the engine actually sets during a render pass.
static volatile LONG g_rejAspect = 0, g_rejNear = 0, g_rejShape = 0, g_passMain = 0;
// Left image on the left is standard side-by-side, which needs parallel
// (wall-eyed) viewing. Most people find crossing their eyes easier, and that
// requires the halves swapped -- otherwise depth comes out inverted.
static volatile LONG g_swapHalves = 0;
static volatile LONG g_inEyePass = 0;
struct VpSeen { int w, h; long n; };
static VpSeen g_vpSeen[12];
static CRITICAL_SECTION g_vpLock;
// The aspect of the projection we are actually rendering with, published by
// the XR path so the viewport and the capture can match it.
static volatile LONG g_projAspectBits = 0;
static volatile LONG g_vpFitW = 0, g_vpFitH = 0, g_vpFitX = 0, g_vpFitY = 0;
static volatile LONG g_vpFitLogged = 0, g_renderAspectLogged = 0, g_wideFovLogged = 0;
// Retired: cropping the viewport to the projection aspect fixed the stretch
// but threw away resolution (14.0 px/deg vs 19.8 for widening). The
// projection is matched to the render target instead. R still toggles it
// for comparison.
// ON by default now: the projection uses the headset's true aspect, so the
// viewport must match it or the image is stretched instead.
// OFF by default. Fitting the viewport DOES correct the aspect -- verified,
// the log shows 1381x1431 inside 2560x1431 -- but it breaks SOMA's screen-space
// passes, whose full-screen quads assume the viewport covers the whole render
// target. Shrinking it desynchronises every post pass from the textures it
// samples, which is the flickering, non-overlapping stereo. The handover
// warned about exactly this. R still toggles it for A/B testing.
static bool g_fitViewport = false;     // R toggles

static float ProjAspect() {
    LONG b = InterlockedCompareExchange(&g_projAspectBits, 0, 0);
    if (!b) return 0.0f;
    float f; memcpy(&f, &b, 4); return f;
}

static void NoteViewport(int w, int h) {
    EnterCriticalSection(&g_vpLock);
    for (int i = 0; i < 12; ++i) {
        if (g_vpSeen[i].n && g_vpSeen[i].w == w && g_vpSeen[i].h == h) { g_vpSeen[i].n++; break; }
        if (!g_vpSeen[i].n) { g_vpSeen[i].w = w; g_vpSeen[i].h = h; g_vpSeen[i].n = 1; break; }
    }
    LeaveCriticalSection(&g_vpLock);
}

// ---- OpenXR (F7) ----------------------------------------------------------
// Milestone 4: SOMA's frame on the headset. Stereo rendering is not solved, so
// both eyes get the same image -- what this proves is the plumbing, and it
// gives us REAL per-eye XrFovf to feed PerspectiveOffAxis instead of guesses.
static xrs::Session g_xr;
static volatile LONG g_xrOn = 0, g_xrTried = 0;
static bool  g_xrFovLogged = false;
static volatile LONG g_xrStereoLogged = 0, g_xrMonoLogged = 0;
static volatile LONG g_fovWidened = 0;
// Rotate the frustum BEFORE iRenderer::Render rather than inside
// SetProjectionMatrix. If SOMA culls inside Render, this lands ahead of it.
static bool g_rotateEarly = true;
// V freezes the head pose to identity while leaving stereo and the headset
// projection alone -- splits "rotation breaks lighting" from "substitution
// breaks lighting", which need different fixes.
static bool g_freezePose = false;
// ; holds the F12 sweep at its current angle (V snaps to identity instead,
// which is a different pose and cannot reproduce the artefact).
static bool  g_sweepHold = false;
static float g_sweepHeldT = 0.0f;
// Which framebuffer to capture each eye from. 0 = whatever is bound when
// Render returns (the raw scene, pre-post). Anything else forces that FBO.
// The engine's post chain writes somewhere else, and this is how we find it.
static volatile LONG g_captureFbo = 0;
static volatile LONG g_altCaptures = 0;
static volatile LONG g_vpRefreshed = 0;
static volatile LONG g_skippedNonEye = 0;
static volatile LONG g_fieldsWritten = 0;
// Set once GetFrustum is hooked: the camera is widened at the source,
// so the legacy frustum-field write must stand down.
static bool g_widenAtCamera = false;
// E toggles. With the camera hook live the engine already produces a correct
// projection; substituting on top of it may be the remaining conflict.
static bool g_substituteProj = true;   // now SYMMETRIC per-eye, so safe
static volatile LONG g_substSkipped = 0;
// Distinct frustum objects passing FrustumIsMain, with the FOV each had on
// arrival. If this is more than one or two, we are substituting into passes
// that are not the camera.
struct FrustSeen { void* ptr; float fovIn; float aspIn; LONG hits; };
static FrustSeen g_frustSeen[12];
static volatile LONG g_frustSeenN = 0;

static void NoteFrustum(void* f, float fovRad, float aspect) {
    LONG n = InterlockedCompareExchange(&g_frustSeenN, 0, 0);
    for (LONG i = 0; i < n && i < 12; ++i) {
        if (g_frustSeen[i].ptr == f) { InterlockedIncrement(&g_frustSeen[i].hits); return; }
    }
    if (n >= 12) return;
    g_frustSeen[n].ptr = f;
    g_frustSeen[n].fovIn = fovRad;
    g_frustSeen[n].aspIn = aspect;
    g_frustSeen[n].hits = 1;
    InterlockedExchange(&g_frustSeenN, n + 1);
}
// The frustum the eye pass renders with, learned from the render hook.
static void* volatile g_eyeFrustum = nullptr;
// Z: one eye per frame, captured after the engine's full frame (post included)
// instead of two raw eyes per frame. Correct colour, half the per-eye rate.
static volatile LONG g_altEyes = 0;
static volatile LONG g_earlyRot = 0;
static volatile LONG g_subL = 0, g_subR = 0;

static bool HeadPoseActive() {
    if (InterlockedCompareExchange(&g_headTest, 0, 0)) return true;
    return InterlockedCompareExchange(&g_xrOn, 0, 0) != 0 && g_xr.Ready();
}

// Both eyes must be drawn from ONE head sample. xrLocateViews refreshes at the
// swap, so without this the second pass can pick up a newer pose than the first
// and the image shears when you turn -- the "world moves" symptom.
// Set when d_Render has acquired an OpenXR frame, so the swap hook knows not to
// acquire a second one and that EndFrame is owed.
static volatile LONG g_xrFrameBegun = 0;
static volatile LONG g_latchedFrame = -1;
static float g_latchQ[2][4], g_latchPos[2][3];
static volatile LONG g_latchValid = 0;
static volatile LONG g_latchReused = 0;

// --- cLogicTimer, via FUN_1403B90C0 ---------------------------------------
// cEngine::Run calls it every frame as the inner-loop condition, with the timer
// object in RCX. cLogicTimer+0x30 is updates-per-second (60). The engine already
// computes stepsPerFrame = ceil(updatesPerSec / refreshHz), so raising it to the
// headset rate makes the logic and render cadences agree instead of the engine
// repeating frames unevenly.
typedef char (*PFN_TimerDue)(void* timer, unsigned long long stepsPerFrame);
static PFN_TimerDue o_LogicTimerDue = nullptr;
static void* volatile g_logicTimer = nullptr;
static const int kTimerUpdatesPerSec = 0x30;
static volatile LONG g_timerLogged = 0;

static char d_LogicTimerDue(void* timer, unsigned long long stepsPerFrame) {
    if (timer && !InterlockedCompareExchangePointer((void* volatile*)&g_logicTimer,
                                                    timer, nullptr)) {
        int ups = *(int*)((char*)timer + kTimerUpdatesPerSec);
        Log(">>> cLogicTimer found at %p -- updates per second = %d."
            " Press Y to retune it to the headset refresh so logic and rendering"
            " share one cadence.", timer, ups);
        InterlockedExchange(&g_timerLogged, 1);
    }
    return o_LogicTimerDue(timer, stepsPerFrame);
}

typedef BOOL (APIENTRY *PFN_SwapInterval)(int);
static PFN_SwapInterval p_SwapInterval = nullptr;
static volatile LONG g_vsyncOff = 0;
static volatile LONG g_hzLogged = 0;
// Left ON by default: uncapping was reported to disturb physics and the
// hands, so the cadence is not changed without an explicit opt-in.
// DEFAULT ON. At 60 fps into a 120 Hz headset the compositor synthesises every
// second frame, and that reprojection is the most likely cause of the world
// appearing to swim with head movement -- it persisted even with head
// translation switched OFF, so it is not the 6DOF code. GPU is ~3.6 ms of a
// 16.8 ms frame, so there is headroom to render faster; vsync was the cap.
static bool g_wantVsyncOff = true;      // PAGE UP toggles

// Called once the XR session is live: the headset, not the monitor, should
// decide the cadence.
static void ApplyVsyncForXr() {
    if (!g_wantVsyncOff || InterlockedCompareExchange(&g_vsyncOff, 0, 0)) return;
    if (!p_SwapInterval) {
        HMODULE gl = GetModuleHandleA("opengl32.dll");
        if (!gl) return;
        typedef PROC (WINAPI *PFN_GPA)(LPCSTR);
        PFN_GPA gpa = (PFN_GPA)GetProcAddress(gl, "wglGetProcAddress");
        if (gpa) p_SwapInterval = (PFN_SwapInterval)(void*)gpa("wglSwapIntervalEXT");
    }
    if (p_SwapInterval && p_SwapInterval(0)) {
        InterlockedExchange(&g_vsyncOff, 1);
        Log(">>> VSYNC OFF: the game was capped at the monitor's 60 Hz while the"
            " headset runs at 90. 60 into 90 repeats frames unevenly, which is"
            " what makes head turning jitter. The runtime now sets the pace.");
    }
}

static bool CurrentHeadPose(float* q, float* pos) {
    if (g_freezePose) {
        q[0]=q[1]=q[2]=0.0f; q[3]=1.0f;
        pos[0]=pos[1]=pos[2]=0.0f;
        return true;                    // identity: no rotation, no translation
    }
    if (InterlockedCompareExchange(&g_xrOn, 0, 0) && g_xr.Ready()) {
        int ei = (int)InterlockedCompareExchange(&g_eye, 0, 0);
        if (ei < 0 || ei > 1 || !g_xr.View(ei).valid) return false;

        // First pass of this frame latches BOTH eyes; the second reuses it.
        LONG fr = InterlockedCompareExchange(&g_frame, 0, 0);
        if (InterlockedCompareExchange(&g_latchedFrame, 0, 0) != fr) {
            for (int e = 0; e < 2; ++e) {
                if (!g_xr.View(e).valid) continue;
                const XrPosef& p = g_xr.View(e).pose;
                g_latchQ[e][0]=p.orientation.x; g_latchQ[e][1]=p.orientation.y;
                g_latchQ[e][2]=p.orientation.z; g_latchQ[e][3]=p.orientation.w;
                g_latchPos[e][0]=p.position.x; g_latchPos[e][1]=p.position.y;
                g_latchPos[e][2]=p.position.z;
            }
            // Tell the session which pose the renderer is about to use, so the
            // submitted layer describes the image we actually draw.
            for (int e = 0; e < 2; ++e) {
                if (!g_xr.View(e).valid) continue;
                g_xr.SetRenderedPose(e, g_xr.View(e).pose);
            }
            InterlockedExchange(&g_latchValid, 1);
            InterlockedExchange(&g_latchedFrame, fr);
        } else {
            InterlockedIncrement(&g_latchReused);
        }
        {   // publish the eye mid-point for ApplyHeadPose
            const XrPosef& a = g_xr.View(0).pose;
            const XrPosef& b = g_xr.View(1).pose;
            if (g_xr.View(0).valid && g_xr.View(1).valid) {
                g_eyeMid[0] = 0.5f*(a.position.x + b.position.x);
                g_eyeMid[1] = 0.5f*(a.position.y + b.position.y);
                g_eyeMid[2] = 0.5f*(a.position.z + b.position.z);
                InterlockedExchange(&g_eyeMidValid, 1);
                {   // live separation, independent of where the origin is
                    float sx = b.position.x - a.position.x;
                    float sy = b.position.y - a.position.y;
                    float sz = b.position.z - a.position.z;
                    g_latchedSep = sqrtf(sx*sx + sy*sy + sz*sz);
                }
                // The first valid pose is not a good reference: tracking has
                // not settled, and the log showed a persistent ~0.5 m Z offset
                // from a bad latch that no axis convention could fix. Wait for
                // a couple of hundred frames, then latch. F6 re-centres.
                if (InterlockedIncrement(&g_originDelay) > 200
                    && !InterlockedExchange(&g_xrOriginSet, 1)) {
                    g_xrOrigin[0] = g_eyeMid[0];
                    g_xrOrigin[1] = g_eyeMid[1];
                    g_xrOrigin[2] = g_eyeMid[2];
                    InterlockedExchange(&g_headTraceDiv, 0);
                    InterlockedExchange(&g_headTraceBudget, 120);
                    Log(">>> 6DOF origin latched at (%.3f %.3f %.3f) -- head"
                        " translation is measured from here.",
                        g_xrOrigin[0], g_xrOrigin[1], g_xrOrigin[2]);
                }
            }
        }
        if (InterlockedCompareExchange(&g_latchValid, 0, 0)) {
            memcpy(q, g_latchQ[ei], 16);
            memcpy(pos, g_latchPos[ei], 12);
            memcpy(g_poseQ[ei], q, 16);
            memcpy(g_posePos[ei], pos, 12);
            return true;
        }
        const XrPosef& po = g_xr.View(ei).pose;
        q[0]=po.orientation.x; q[1]=po.orientation.y;
        q[2]=po.orientation.z; q[3]=po.orientation.w;
        pos[0]=po.position.x; pos[1]=po.position.y; pos[2]=po.position.z;
        memcpy(g_poseQ[ei], q, 16);
        memcpy(g_posePos[ei], pos, 12);
        return true;
    }
    if (InterlockedCompareExchange(&g_headTest, 0, 0)) {
        float t = g_sweepHold ? g_sweepHeldT : (float)NowSeconds();
        if (!g_sweepHold) g_sweepHeldT = t;
        float yaw = 0.35f*sinf(t*1.2f), pitch = 0.12f*sinf(t*0.78f), roll = 0.20f*sinf(t*1.02f);
        float cy=cosf(yaw*0.5f), sy=sinf(yaw*0.5f);
        float cp=cosf(pitch*0.5f), sp=sinf(pitch*0.5f);
        float cr=cosf(roll*0.5f), sr=sinf(roll*0.5f);
        q[0]=sp*cy*cr+cp*sy*sr; q[1]=cp*sy*cr-sp*cy*sr;
        q[2]=cp*cy*sr-sp*sy*cr; q[3]=cp*cy*cr+sp*sy*sr;
        pos[0]=0.25f*sinf(t*0.66f); pos[1]=0.15f*sinf(t*1.38f); pos[2]=0.25f*sinf(t*0.54f);
        return true;
    }
    return false;
}

static bool RotateFrustumEarly(void* frustum) {
    if (!g_rotateEarly || !frustum || !HeadPoseActive()) return false;
    if (!FrustumIsMain(frustum)) return false;
    float q[4], pos[3];
    if (!CurrentHeadPose(q, pos)) return false;
    if (!ApplyHeadPose(frustum, q, pos)) return false;
    InterlockedIncrement(&g_earlyRot);
    return true;
}

// Build this eye's projection: off-axis frustum with the eye offset folded in.
// outColMajor receives P * T, still projection-shaped (verified).
// UNUSED. The live path is BuildFromFrustum; this remains only because it is
// referenced by the offline projection tests. Editing it changes nothing at
// runtime -- a fix applied here once appeared to do nothing for exactly that
// reason.
// DEAD CODE -- nothing calls this. Verified by grep: the only other mention is
// a comment. The LIVE projection path is BuildFromFrustum below. This function
// still contains the OLD widening design (hh = atan(tan(hv)*ra) plus
// SetRenderAspect(ra)), which is self-consistent and therefore reads as
// correct, which is precisely why it keeps attracting fixes. The roadmap
// already records two builds lost to editing dead functions. Edit
// BuildFromFrustum instead, or delete this.
static bool BuildEyeProjection(const hpl3vr::ProjParams& in, float* outColMajor) {
    if (!InterlockedCompareExchange(&g_hookOn, 0, 0)) return false;
    // F1 alternates per frame so it applies everywhere; F10 renders twice, so
    // its offset must apply ONLY inside an eye pass.
    // One render per frame now, so the eye applies for the entire frame.
    const bool stereo = InterlockedCompareExchange(&g_stereoOn, 0, 0) != 0
                     || InterlockedCompareExchange(&g_sbsOn, 0, 0) != 0;
    const bool pulse  = InterlockedCompareExchange(&g_fovPulse, 0, 0) != 0;
    if (!stereo && !pulse) return false;

    float fovY = in.fFovYDeg;
    if (pulse) {
        float t = (float)NowSeconds();      // seconds: the pulse rate should not
        fovY = 55.0f + 45.0f * (0.5f + 0.5f * sinf(t * 3.0f));   // follow framerate
    }

    // With a live session the runtime's own asymmetric angles replace the
    // symmetric approximation. This is what the off-axis path was built for.
    if (!stereo) InterlockedIncrement(&g_rejNotStereo);
    else if (!InterlockedCompareExchange(&g_xrOn, 0, 0)) InterlockedIncrement(&g_rejXrOff);
    else if (!g_xr.Ready()) InterlockedIncrement(&g_rejNotReady);

    if (stereo && InterlockedCompareExchange(&g_xrOn, 0, 0) && g_xr.Ready()) {
        int eye = (int)InterlockedCompareExchange(&g_eye, 0, 0);
        const xrs::EyeView& ev = g_xr.View(eye);
        if (!ev.valid) InterlockedIncrement(&g_rejInvalid);
        if (ev.valid) {
            InterlockedIncrement(&g_projXrPath);
            // SYMMETRIC, not off-axis. SOMA's deferred pass rebuilds world
            // position from depth using tan(fov/2) and aspect, which cannot
            // express an off-centre frustum -- an asymmetric matrix misplaces
            // every pixel and breaks the lighting and shadows. Verified: with
            // substitution off, the engine's own symmetric matrix is correct.
            // We render a symmetric frustum that CONTAINS the eye's asymmetric
            // one and submit the same angles to the runtime, which reprojects.
            float hv = fmaxf(fabsf(ev.fov.angleUp),   fabsf(ev.fov.angleDown));
            float hh = fmaxf(fabsf(ev.fov.angleLeft), fabsf(ev.fov.angleRight));
            // Draw with the RENDER TARGET's aspect, not the headset's. The
            // engine renders into a 16:9 buffer; forcing a 0.935 projection into
            // it stretches everything by 1.9x, which is what made objects look
            // oversized. Widening instead keeps the full 2560x1440 (19.8 px/deg
            // horizontally vs 14.0 if we cropped) and the runtime crops to the
            // true optics, because we submit the FOV we actually drew.
            {
                LONG vw = InterlockedCompareExchange(&g_vpW, 0, 0);
                LONG vh = InterlockedCompareExchange(&g_vpH, 0, 0);
                float ra = (vw > 0 && vh > 0) ? (float)vw / (float)vh : 0.0f;
                if (ra > 0.01f) {
                    hh = atanf(tanf(hv) * ra);
                    g_xr.SetRenderAspect(ra);
                    if (!InterlockedExchange(&g_renderAspectLogged, 1))
                        Log("projection drawn at the RENDER aspect %.3f (%ldx%ld):"
                            " %.1f x %.1f deg. Wider than the headset's 94x98 on"
                            " purpose -- the runtime crops, and this keeps full"
                            " resolution instead of cropping the viewport.",
                            ra, vw, vh, hh*2*57.2957795f, hv*2*57.2957795f);
                }
                float a = tanf(hh) / tanf(hv);
                LONG bits; memcpy(&bits, &a, 4);
                InterlockedExchange(&g_projAspectBits, bits);
            }
            hpl3vr::Mat4 P = hpl3vr::PerspectiveOffAxis(
                in.fNear, in.bInfiniteFar ? 1000.0f : in.fFar,
                -hh, hh, hv, -hv, in.bInfiniteFar);
            hpl3vr::Mat4ColMajor cm = hpl3vr::ToColMajor(P);
            memcpy(outColMajor, cm.v, 64);
            // NO IPD term here. The runtime's per-eye pose already places each
            // eye, and ApplyHeadPose puts that into the view matrix. Adding the
            // offset again separates the eyes twice.
            InterlockedExchange(&g_appliedShift, 0);
            return true;
        }
    }

    const float halfV = fovY * 0.5f * 0.01745329252f;
    const float tH    = in.fAspect * tanf(halfV);

    // Per-eye horizontal asymmetry. With a real headset these come straight
    // from XrFovf; for now derive a plausible pair from the eye offset.
    // No per-eye frustum asymmetry here: with a real headset that comes from
    // XrFovf, and a fixed placeholder value would add a constant component
    // that does not scale with IPD, muddying exactly the thing being tested.
    const float sway = 0.0f;

    hpl3vr::Mat4 P = hpl3vr::PerspectiveOffAxis(
        in.fNear, in.bInfiniteFar ? 1000.0f : in.fFar,
        atanf(-tH + sway), atanf(tH + sway), halfV, -halfV, in.bInfiniteFar);
    hpl3vr::Mat4ColMajor cm = hpl3vr::ToColMajor(P);
    memcpy(outColMajor, cm.v, 64);

    if (stereo) {
        InterlockedIncrement(&g_projFallback);
        // P * Translate(+-ipd/2, 0, 0). Only [0][3] changes, so the result is
        // still projection-shaped and the engine handles it unchanged.
        int eye = (int)InterlockedCompareExchange(&g_eye, 0, 0);
        float tx = (eye == 0 ? +1.0f : -1.0f) * (g_ipdMetres * 0.5f);
        float term = outColMajor[0] * tx;         // A * tx, lands in [0][3]
        outColMajor[12] += term;
        InterlockedExchange(&g_appliedShift, (LONG)(term * 1e6f));
    }
    return true;
}

// ------------------------------------------------- engine SetProjectionMatrix
static const uintptr_t kRVA_SetProjectionMatrix = 0x2b46e0;

// --- iLowLevelGraphics::SetMatrix, VIEW (RVA 0x2B4380) --------------------
// From the log-string dump: FUN_1402B4380 logs "Setting view matrix: %s". It is
// the sibling of SetProjectionMatrix at 0x2B46E0, and it is what actually
// transforms geometry for the GPU.
//
// Scaling frustum+0x158 was not enough: that copy feeds CULLING and the LIGHT
// SETUP cache, which is why the only visible effect was the scene getting
// brighter or dimmer while nothing moved. The log said so outright --
// "cached view matrix DOES NOT MATCH the frustum's current view" appeared the
// moment the scale left 1.0.
//
// V' = Scale(1/S) * V shrinks every world distance by S with the FOV untouched,
// so angular correspondence holds and head tracking stays locked.
typedef void (*PFN_SetView)(void* ctx, float* view);
static PFN_SetView o_SetView = nullptr;
static volatile LONG g_setViewCount = 0, g_setViewLogged = 0;

static void d_SetView(void* ctx, float* view) {
    if (view && g_worldScale > 0.01f && fabsf(g_worldScale - 1.0f) > 0.001f &&
        InterlockedCompareExchange(&g_xrOn, 0, 0)) {
        float V[16]; memcpy(V, view, 64);
        const float inv = 1.0f / g_worldScale;
        // Row-major, translation in column 3: scaling rows 0..2 entirely scales
        // the basis and the translation together, which is the uniform scale.
        for (int i = 0; i < 12; ++i) V[i] *= inv;
        if (!InterlockedExchange(&g_setViewLogged, 1))
            Log(">>> world scale %.2f applied at SetMatrix(VIEW) -- this is the"
                " matrix geometry is actually drawn with, unlike frustum+0x158"
                " which only feeds culling and lighting.", g_worldScale);
        InterlockedIncrement(&g_setViewCount);
        o_SetView(ctx, V);
        return;
    }
    o_SetView(ctx, view);
}

typedef void (*PFN_SetProj)(void* ctx, float* proj);
static PFN_SetProj o_SetProj = nullptr;

static float g_pool[16][16];
static volatile LONG g_poolIdx = 0;

static bool PlausibleCamera(const hpl3vr::ProjParams& p) {
    return p.fNear > 0.001f && p.fNear < 10.0f
        && p.fFovYDeg > 20.0f && p.fFovYDeg < 150.0f
        && p.fAspect > 0.3f && p.fAspect < 4.0f;
}
static bool IsMainCamera(const hpl3vr::ProjParams& p) {
    if (!g_cam.known) return false;
    bool aspectOk = fabsf(p.fAspect - g_cam.aspect) < 0.02f * g_cam.aspect;
    bool nearOk   = fabsf(p.fNear   - g_cam.nearZ)  < 0.20f * g_cam.nearZ;
    if (aspectOk && nearOk) { InterlockedIncrement(&g_passMain); return true; }
    if (!aspectOk) InterlockedIncrement(&g_rejAspect);
    else           InterlockedIncrement(&g_rejNear);
    return false;
}

// Build this eye's projection from the frustum's parameters, then fold in the
// head pose and eye offset. Reading the frustum rather than the matrix means an
// in-place write can never cost us the original.
static int g_fullW = 0, g_fullH = 0;   // backbuffer size, sampled at swap

// The half-angles we actually RENDER with. The projection and the culling cone
// must both use these: they diverged once (draw 129.5, cull 98) and the missing
// 31.5 deg margin brought the geometry and lighting bugs straight back.
static void RenderHalfAngles(const xrs::EyeView& ev, float* outHH, float* outHV) {
    float hv = fmaxf(fabsf(ev.fov.angleUp),   fabsf(ev.fov.angleDown));
    float hh = fmaxf(fabsf(ev.fov.angleLeft), fabsf(ev.fov.angleRight));
    LONG vw = InterlockedCompareExchange(&g_vpW, 0, 0);
    LONG vh = InterlockedCompareExchange(&g_vpH, 0, 0);
    (void)vw; (void)vh;
    // WORLD SCALE, applied where it actually changes apparent size.
    //
    // Parallax was ruled out by measurement: separation swept 0.063 -> 0.0945 m
    // with no perceived change. The remaining lever is angular size. Rendering a
    // frustum WIDER than the one we submit compresses more world into the same
    // angular span, so everything shrinks -- which is what a game whose world
    // unit is not a metre needs.
    //
    // This is safe now, and was not before. The old widening failed because we
    // also submitted the widened angles and the runtime CLAMPED them. We now
    // submit the runtime's own asymmetric FOV with a sub-rect, computed
    // independently of these values, so the two no longer interact.
    //
    // Scale the TANGENTS, not the angles: doubling an angle is not doubling a
    // frustum, and the error grows badly toward 90 degrees.
    // The FOV is NOT scaled. Widening the rendered frustum beyond what we
    // submit does shrink objects, but the compositor then reprojects against
    // angles the image does not have, so the world slides as the head turns.
    // World scale is applied to the VIEW MATRIX instead -- see below.
    *outHH = hh; *outHV = hv;
}

static bool BuildFromFrustum(void* frustum, float* outColMajor) {
    if (!frustum) return false;
    const char* f = (const char*)frustum;
    float farZ   = *(const float*)(f + kFrustumFar);
    float nearZ  = *(const float*)(f + kFrustumNear);
    float aspect = *(const float*)(f + kFrustumAspect);
    float fovRad = *(const float*)(f + kFrustumFov);
    if (!(nearZ > 0.0f && farZ > nearZ && aspect > 0.1f && aspect < 10.0f &&
          fovRad > 0.2f && fovRad < 3.0f)) return false;

    const bool stereo = InterlockedCompareExchange(&g_stereoOn,0,0) != 0
                     || InterlockedCompareExchange(&g_sbsOn,0,0) != 0;
    const bool pulse  = InterlockedCompareExchange(&g_fovPulse,0,0) != 0;
    const bool head   = InterlockedCompareExchange(&g_headTest,0,0) != 0;
    if (!stereo && !pulse && !head) return false;

    float fovY = fovRad * 57.29577951f;
    if (pulse) {
        float t = (float)InterlockedCompareExchange(&g_frame,0,0);
        fovY = 55.0f + 45.0f * (0.5f + 0.5f * sinf(t * 0.05f));
        // Keep the frustum's own FOV field in step with the pulsed matrix. The
        // deferred pass rebuilds view-space position from depth using this
        // field; leaving it stale is what makes F8 alone break the lighting.
        if (frustum) *(float*)((char*)frustum + kFrustumFov) = fovY * 0.01745329252f;
    }
    float halfV = fovY * 0.5f * 0.01745329252f;
    float tH    = aspect * tanf(halfV);

    // Real per-eye angles when a headset is driving us.
    hpl3vr::Mat4 P;
    int eye = (int)InterlockedCompareExchange(&g_eye,0,0);
    if (stereo && InterlockedCompareExchange(&g_xrOn,0,0) && g_xr.Ready() &&
        g_xr.View(eye).valid) {
        const xrs::EyeView& ev = g_xr.View(eye);
        // SYMMETRIC, at the RENDER TARGET's aspect. Two reasons, both verified:
        //  - SOMA's deferred pass rebuilds position from depth via tan(fov/2)
        //    and aspect, which cannot describe an off-centre frustum, so an
        //    asymmetric matrix misplaces every pixel and breaks the lighting.
        //  - the engine draws into a 16:9 buffer; forcing a 0.935 projection
        //    into it stretches everything ~1.9x, which is the "objects look
        //    oversized" effect.
        // Drawing wider than the headset asked for keeps the full 2560x1440
        // (19.8 px/deg vs 14.0 if we cropped the viewport instead). The FOV we
        // actually drew is handed to the runtime, which crops to the optics.
        float hv, hh;
        RenderHalfAngles(ev, &hh, &hv);
        LONG vw = InterlockedCompareExchange(&g_vpW, 0, 0);
        LONG vh = InterlockedCompareExchange(&g_vpH, 0, 0);
        if (vw <= 0 || vh <= 0) { vw = g_fullW; vh = g_fullH; }
        float ra = (vw > 0 && vh > 0) ? (float)vw / (float)vh : 0.0f;
        // Widening to the render aspect covers ordinary headsets, but very wide
        // ones (Pimax: 120-150 deg horizontal) can ask for MORE than 16:9 gives.
        // Never draw narrower than the runtime asked for -- a small stretch is
        // recoverable, missing FOV at the edges is not. Take the larger.
        // The submitted FOV must describe THE IMAGE WE DREW. RenderHalfAngles
        // no longer widens (that was reverted after it caused magnification),
        // so handing the session the raw render aspect makes it submit
        // atan(tan(hv)*ra) -- WIDER than we drew. The runtime then spreads the
        // image over a larger angular span, which magnifies everything and
        // makes the world sweep faster than the head. At 2560x1440 that is
        // 1.9x; at the headset's own 2064x2208 it is 1.003x, which is why the
        // symptom tracks whether the resolution override fired.
        // tan(hh)/tan(hv) IS the aspect of what we drew, by construction.
        if (ra > 0.01f) {
            float widened = atanf(tanf(hv) * ra);
            if (widened < hh && !InterlockedExchange(&g_wideFovLogged, 1))
                Log("wide-FOV headset: it wants %.1f deg horizontally but a"
                    " %.3f render target only reaches %.1f at this aspect.",
                    hh*2*57.2957795f, ra, widened*2*57.2957795f);
        }
        g_xr.SetRenderAspect(tanf(hh) / tanf(hv));
        {   // Publish the drawn aspect so d_Viewport can match the viewport to
            // it. This was previously published ONLY from BuildEyeProjection,
            // which nothing calls -- so ProjAspect() returned 0, the fitting
            // branch never ran, and the image kept the full 1.789 viewport
            // stretch. No "viewport fitted" line ever appeared in the log,
            // which is what gave it away.
            float a = tanf(hh) / tanf(hv);
            LONG bits; memcpy(&bits, &a, 4);
            InterlockedExchange(&g_projAspectBits, bits);
        }
        P = hpl3vr::PerspectiveOffAxis(nearZ, farZ, -hh, hh, hv, -hv, false);
        if (!InterlockedExchange(&g_renderAspectLogged, 1))
            Log("projection: SYMMETRIC %.1f x %.1f deg (headset asked %.1f x %.1f)."
                " Submitted aspect %.4f == drawn aspect, so the runtime reprojects"
                " 1:1 with no magnification. Render target %ldx%ld (aspect %.3f);"
                " if that aspect is far from %.4f the resolution override did not"
                " fire and pixels are being wasted -- but the SCALE is now correct"
                " either way.",
                hh*2*57.2957795f, hv*2*57.2957795f,
                (ev.fov.angleRight-ev.fov.angleLeft)*57.2957795f,
                (ev.fov.angleUp-ev.fov.angleDown)*57.2957795f,
                tanf(hh)/tanf(hv), vw, vh, ra, tanf(hh)/tanf(hv));
        InterlockedIncrement(&g_projXrPath);
        g_wantFovH = hh * 2 * 57.2957795f;
        g_wantFovV = hv * 2 * 57.2957795f;
    } else {
        InterlockedIncrement(&g_projFallback);
        P = hpl3vr::PerspectiveOffAxis(nearZ, farZ, atanf(-tH), atanf(tH), halfV, -halfV, false);
    }
    hpl3vr::Mat4ColMajor cm = hpl3vr::ToColMajor(P);
    float cur[16]; memcpy(cur, cm.v, 64);
    // Recover the FOV from the matrix: A = 2n/(r-l) so the full angle is
    // 2*atan(1/A) once the off-centre term is accounted for.
    {
        float A = P.m[0][0], B = P.m[1][1], S = P.m[0][2], T = P.m[1][2];
        float rl = 2.0f / A, tb = 2.0f / B;          // (r-l)/n and (t-b)/n
        float r = 0.5f*(rl*(1.0f+S)), l = r - rl;
        float t = 0.5f*(tb*(1.0f+T)), b = t - tb;
        g_projFovH = (atanf(r) - atanf(l)) * 57.2957795f;
        g_projFovV = (atanf(t) - atanf(b)) * 57.2957795f;
    }

    // X = T_eye * R_head, applied in view space: P' = P * X
    // Rotation now goes into the VIEW matrix, not here. Keeping it out of the
    // projection is what lets shadows and the deferred passes stay correct.
    float yaw = 0.0f, pitch = 0.0f;
    if (yaw != 0.0f || pitch != 0.0f || stereo) {
        float cy=cosf(yaw), sy=sinf(yaw), cp=cosf(pitch), sp=sinf(pitch);
        float Ry[16] = { cy,0,-sy,0,  0,1,0,0,  sy,0,cy,0,  0,0,0,1 };
        float Rx[16] = { 1,0,0,0,  0,cp,sp,0,  0,-sp,cp,0,  0,0,0,1 };
        float R[16];  vpm::Mul4x4(Rx, Ry, R);
        // The XR guard here was suppressing the only per-eye offset that
        // actually reaches the image. Its reasoning -- "xrLocateViews gives
        // each eye its own position and ApplyHeadPose puts that into the view
        // matrix" -- is false in practice: MEASURED, the camera hook runs
        // 3 times a frame and EVERY call reads g_eye == 0. Eye 1 got zero hits.
        // The engine builds its view matrix outside the eye passes and both
        // passes reuse the cache, so the camera can never carry a per-eye
        // offset. That is why the eyes were never separated and why increasing
        // the offset only slid the whole camera sideways.
        //
        // This path DOES alternate correctly -- the census reads left 4200 /
        // right 4200 every frame -- so the offset belongs here. Magnitude comes
        // from the runtime's own eye positions when a session is live, so it
        // stays physically correct rather than using the nominal IPD.
        float halfSep = g_ipdMetres * 0.5f;
        const bool xrLive = InterlockedCompareExchange(&g_xrOn,0,0) != 0
                         && g_xr.Ready() && g_xr.View(0).valid && g_xr.View(1).valid;
        if (xrLive) {
            const XrPosef& a = g_xr.View(0).pose;
            const XrPosef& b = g_xr.View(1).pose;
            float ex = b.position.x - a.position.x;
            float ey = b.position.y - a.position.y;
            float ez = b.position.z - a.position.z;
            halfSep = 0.5f * sqrtf(ex*ex + ey*ey + ez*ez);
        }
        halfSep *= g_eyeOffsetScale;
        // DOUBLE-COUNTING. ApplyHeadPose now puts the eye displacement into the
        // frustum's VIEW matrix, which is the geometrically correct place and
        // holds steady at 0.0315 m in head-local space. Adding it here as well
        // gave twice the parallax: at x4 that is a quarter-metre of separation,
        // past what the eyes can fuse -- the double vision -- and doubled
        // parallax also reads as a world that is too near, hence too small.
        //
        // Keep this ONLY for the monitor fallback, where there is no frustum
        // translation because there is no XR pose to derive one from.
        const bool frustumOwnsEyes = g_eyeTranslateInFrustum
                                  && InterlockedCompareExchange(&g_xrOn,0,0) != 0
                                  && g_xr.Ready();
        float tx = (stereo && !frustumOwnsEyes)
                 ? ((eye == 0 ? +1.0f : -1.0f) * halfSep) : 0.0f;
        if (stereo && !InterlockedExchange(&g_projEyeLogged, 1))
            Log(">>> per-eye offset now applied in the PROJECTION: eye %d tx"
                " %+.4f m (half separation %.4f). The camera hook could not do"
                " this -- it only ever ran with eye 0.", eye, tx, halfSep);
        float T[16] = { 1,0,0,0, 0,1,0,0, 0,0,1,0, tx,0,0,1 };
        float X[16]; vpm::Mul4x4(T, R, X);
        float PX[16]; vpm::Mul4x4(cur, X, PX);
        memcpy(cur, PX, 64);
        InterlockedExchange(&g_appliedShift, (LONG)(cur[12] * 1e6f));
    }
    memcpy(outColMajor, cur, 64);
    return true;
}

// Rebuild m_mtxViewProj (+0x118) from the projection we just substituted and
// the current view. Both are row-major in the frustum. Without this the
// composite still describes the projection the engine originally had, and the
// culling planes and deferred pass both read it.
static void RefreshViewProj(void* frustum, const float* projRowMajor) {
    if (!frustum) return;
    // Same class of bug as the retired frustum-field write: this overwrites the
    // engine's cached ViewProj AFTER it has built the frustum and its planes
    // from the widened camera. With the camera hook live the engine's own value
    // is already consistent, so touching it here can only desync it.
    if (g_widenAtCamera) return;
    char* f = (char*)frustum;
    const float* V = (const float*)(f + kFrustumView);
    float* VP = (float*)(f + kFrustumViewProj);
    float r[16];
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j)
            r[i*4+j] = projRowMajor[i*4+0]*V[0*4+j] + projRowMajor[i*4+1]*V[1*4+j]
                     + projRowMajor[i*4+2]*V[2*4+j] + projRowMajor[i*4+3]*V[3*4+j];
    memcpy(VP, r, sizeof(r));
    InterlockedIncrement(&g_vpRefreshed);
}

static void d_SetProj(void* ctx, float* proj) {
    InterlockedIncrement(&g_calls);

    // Catalogue orthographic projections -- these are the UI passes.
    if (proj) {
        float probe[16]; memcpy(probe, proj, sizeof(probe));
        int lay = hpl3vr::ClassifyProjection(probe);
        if (!lay && IsOrthographic(probe, 1)) NoteOrtho(probe, 1);
        else if (IsOrthographic(probe, 2))    NoteOrtho(probe, 2);
    }

    // Primary path: identify and rebuild from the FRUSTUM. Deliberately does
    // not look at the incoming matrix -- once a rotated projection has been
    // written in place it can no longer be classified or decoded, which is
    // exactly what stalled substitution at 600 of 6000 calls.
    if (ctx) g_ctxPtr = ctx;
    if (ctx) g_frustumPtr = *(void**)((char*)ctx + 0x10);

    // Rotate the view before the engine reads it. Only on the main camera, and
    // only once per pass -- the guard is the frustum check further down.
    // Head pose: from the runtime when a session is live, otherwise the F12
    // sweep. Both drive the same view-matrix path.
    bool xrPose = InterlockedCompareExchange(&g_xrOn, 0, 0) && g_xr.Ready();
    if (ctx && (xrPose || InterlockedCompareExchange(&g_headTest, 0, 0))) {
        void* fr = *(void**)((char*)ctx + 0x10);
        if (fr && (((char*)fr + kFrustumProj) == (char*)proj) && FrustumIsMain(fr)) {
            float q[4], pos[3];
            if (xrPose) {
                // The runtime gives each EYE a full pose, so roll and position
                // come through with no extra work.
                int ei = (int)InterlockedCompareExchange(&g_eye,0,0);
                const XrPosef& po = g_xr.View(ei).pose;
                q[0]=po.orientation.x; q[1]=po.orientation.y;
                q[2]=po.orientation.z; q[3]=po.orientation.w;
                // THE LIVE PATH. The two copies of this in GetHeadPose are not
                // the ones that run during substitution -- scaling them left the
                // reported separation pinned at 0.0630 m while world scale swept
                // 1.00 to 1.50, which is how this was caught. Rotation is
                // unitless and must not be scaled; only the translation.
                // NOT scaled. g_worldScale now widens the rendered frustum
                // instead, and applying it here as well double-counts: head
                // translation was being amplified 1.3x on top of the zoom,
                // which is part of why tracking felt wrong.
                pos[0]=po.position.x;
                pos[1]=po.position.y;
                pos[2]=po.position.z;
                if (ei >= 0 && ei < 2) {
                    memcpy(g_poseQ[ei], q, sizeof(q));
                    memcpy(g_posePos[ei], pos, sizeof(pos));
                }
            } else {
                // Sweep all six degrees of freedom so each is separately visible.
                // Seconds, not frames, so the sweep runs at one speed everywhere.
                float t = (float)NowSeconds();
                float yaw   = 0.35f * sinf(t * 1.2f);
                float pitch = 0.12f * sinf(t * 0.78f);
                float roll  = 0.20f * sinf(t * 1.02f);
                float cy=cosf(yaw*0.5f), sy=sinf(yaw*0.5f);
                float cp=cosf(pitch*0.5f), sp=sinf(pitch*0.5f);
                float cr=cosf(roll*0.5f), sr=sinf(roll*0.5f);
                q[0] = sp*cy*cr + cp*sy*sr;
                q[1] = cp*sy*cr - sp*cy*sr;
                q[2] = cp*cy*sr - sp*sy*cr;
                q[3] = cp*cy*cr + sp*sy*sr;
                pos[0] = 0.25f * sinf(t * 0.66f);    // lean left/right
                pos[1] = 0.15f * sinf(t * 1.38f);    // crouch/rise
                pos[2] = 0.25f * sinf(t * 0.54f);    // lean in/out
            }
            ApplyHeadPose(fr, q, pos);
        }
    }
    void* frustum = ctx ? *(void**)((char*)ctx + 0x10) : nullptr;
    bool  frustumOwnsProj = frustum && (((char*)frustum + kFrustumProj) == (char*)proj);

    if (frustumOwnsProj && !g_cam.known) {
        const char* f = (const char*)frustum;
        float aspect = *(const float*)(f + kFrustumAspect);
        float nearZ  = *(const float*)(f + kFrustumNear);
        float fovRad = *(const float*)(f + kFrustumFov);
        if (aspect > 1.2f && aspect < 4.0f && nearZ > 0.001f && fovRad > 0.2f && fovRad < 3.0f) {
            g_cam.known = true;
            g_cam.nearZ = nearZ; g_cam.aspect = aspect;
            g_cam.fovYDeg = fovRad * 57.29577951f;
            g_cam.farZ = *(const float*)(f + kFrustumFar);
            Log("");
            Log("main camera learned FROM THE FRUSTUM: near %.4f far %.1f fovY %.3f aspect %.5f",
                g_cam.nearZ, g_cam.farZ, g_cam.fovYDeg, g_cam.aspect);
        }
    }

    if (frustumOwnsProj && !InterlockedExchange(&g_frustumChecked, 1)) {
        const char* f = (const char*)frustum;
        Log("frustum at ctx+0x10 = %p, proj == frustum+0xd8 (confirmed)", frustum);
        Log("  fields: near %.4f far %.1f aspect %.5f fov %.4f rad (%.3f deg)",
            *(const float*)(f+kFrustumNear), *(const float*)(f+kFrustumFar),
            *(const float*)(f+kFrustumAspect), *(const float*)(f+kFrustumFov),
            *(const float*)(f+kFrustumFov) * 57.29577951f);
    }

    // Sample the layout before anything has been written over it.
    if (frustumOwnsProj && !InterlockedCompareExchange(&g_frustumLayout, 0, 0)) {
        float probe[16]; memcpy(probe, proj, sizeof(probe));
        int lay = hpl3vr::ClassifyProjection(probe);
        if (lay) {
            InterlockedExchange(&g_frustumLayout, lay);
            Log("frustum matrix layout: %s", lay == 1 ? "column-major" : "row-major");
        }
    }

    if (frustumOwnsProj && FrustumIsMain(frustum)) {
        // Shadow, reflection and cubemap frusta can share the main camera's
        // aspect and near plane. Reject them BEFORE changing any fields: once
        // FOV/aspect are overwritten, even forwarding the original projection
        // leaves the auxiliary pass internally inconsistent.
        // DIAGNOSTIC (E): let the engine's own projection stand, so its planes
        // and the drawn geometry come from exactly one matrix.
        if (!g_substituteProj && g_widenAtCamera) {
            InterlockedIncrement(&g_substSkipped);
            o_SetProj(ctx, proj);
            return;
        }

        void* mainF = (void*)InterlockedCompareExchangePointer(
                          (void* volatile*)&g_eyeFrustum, nullptr, nullptr);
        if (mainF && frustum != mainF) {
            InterlockedIncrement(&g_skippedNonEye);
            o_SetProj(ctx, proj);
            return;
        }

        UpdateCameraWorld(frustum);      // every frame, not just under F12
        // Culling uses the frustum's FOV FIELDS, not the matrix we substitute.
        // A headset sees wider than SOMA's 83 deg, so without this the engine
        // culls away geometry the wider projection then tries to draw -- the
        // missing ceiling.
        if (InterlockedCompareExchange(&g_xrOn, 0, 0) && g_xr.Ready()) {
            const xrs::EyeView& ev = g_xr.View((int)InterlockedCompareExchange(&g_eye,0,0));
            if (ev.valid) {
                float vFov = ev.fov.angleUp - ev.fov.angleDown;      // radians
                float hFov = ev.fov.angleRight - ev.fov.angleLeft;
                char* f = (char*)frustum;
                float* pFov    = (float*)(f + kFrustumFov);
                float* pAspect = (float*)(f + kFrustumAspect);
                // A little margin so edge geometry is not clipped by rounding.
                // EXACTLY the projection we substitute -- no margin. The
                // deferred pass reads these to rebuild position from depth, so
                // any discrepancy misplaces all lighting and shadows.
                // Only when the camera hook is NOT available. With GetFrustum
                // hooked, the engine builds the fields AND the culling planes
                // from the widened camera in one consistent step; stamping the
                // fields again here afterwards is precisely the desync that
                // broke lighting and shadows all session.
                if (!g_widenAtCamera) {
                    *pFov    = vFov;
                    *pAspect = (tanf(ev.fov.angleRight) - tanf(ev.fov.angleLeft))
                             / (tanf(ev.fov.angleUp)    - tanf(ev.fov.angleDown));
                    g_xrAspect = *pAspect;
                    InterlockedIncrement(&g_fieldsWritten);
                }
                if (!InterlockedExchange(&g_fovWidened, 1))
                    Log("frustum fields matched to the substituted projection:"
                        " %.1f deg vertical, aspect %.3f (was 83.0 / 1.778)."
                        " These drive the deferred pass's depth->position"
                        " reconstruction, so they must agree with the matrix.",
                        (*pFov) * 57.2957795f, *pAspect);
            }
        }
        {   // record which frustum object this is, before anything is changed
            const char* ff = (const char*)frustum;
            NoteFrustum(frustum, *(const float*)(ff + kFrustumFov),
                        *(const float*)(ff + kFrustumAspect));
        }
        InterlockedIncrement(&g_passMain);
        float out[16];
        if (BuildFromFrustum(frustum, out)) {
            if (InterlockedCompareExchange(&g_frustumLayout, 0, 0) == 2)
                hpl3vr::TransposeInPlace(out);       // match the engine's storage

            // Write in place ONLY when the result is still a well-formed
            // projection. A rotated matrix is not, and overwriting the frustum
            // with one destroys the original irrecoverably -- which is what
            // stalled substitution at 600 of 6000 last build.
            bool rotated = InterlockedCompareExchange(&g_headTest, 0, 0) != 0
                        || g_headYaw != 0.0f || g_headPitch != 0.0f;
            if (!rotated) {
                memcpy(proj, out, sizeof(out));
                // The frustum now holds this projection, so its cached
                // ViewProj must be rebuilt or it still describes the old one.
                float rm[16];
                memcpy(rm, out, sizeof(rm));
                if (InterlockedCompareExchange(&g_frustumLayout, 0, 0) != 2)
                    hpl3vr::TransposeInPlace(rm);   // RefreshViewProj wants row-major
                RefreshViewProj(frustum, rm);
            }
            LONG i = InterlockedIncrement(&g_poolIdx) & 15;
            memcpy(g_pool[i], out, sizeof(out));
            InterlockedIncrement(&g_subbed);
            if (rotated) InterlockedIncrement(&g_rotPassOnly);
            if (InterlockedCompareExchange(&g_stereoOn, 0, 0) ||
                InterlockedCompareExchange(&g_sbsOn, 0, 0))
                (InterlockedCompareExchange(&g_eye, 0, 0) == 0)
                    ? InterlockedIncrement(&g_subL) : InterlockedIncrement(&g_subR);
            o_SetProj(ctx, g_pool[i]);
            return;
        }
    }

    o_SetProj(ctx, proj);
}

// --- cGraphics::Init (RVA 0x210FF0) ---------------------------------------
// Recovered from its own log string: "Init lowlevel graphics: %dx%d bpp:%d ...".
// param_2/param_3 are width/height, passed straight to the low-level init, and
// every render target the engine allocates derives from them. Overriding them
// makes SOMA render natively at the headset resolution -- no capture rescale.
typedef unsigned long long (*PFN_GfxInit)(
    void* self, unsigned int w, unsigned int h, unsigned int bpp, unsigned int rr,
    unsigned int fs, unsigned int ms, unsigned int drv, void* cap, void* pos,
    void* res, void* p12, unsigned int flags);
static PFN_GfxInit o_GraphicsInit = nullptr;
static volatile LONG g_nativeW = 0, g_nativeH = 0;   // set once XR reports a size
// OFF for this build. The override is ALL-OR-NOTHING and this build had it
// half applied: the low-level patch lands BEFORE the renderers are built, so
// their G-buffers are allocated at 2064x2208 -- then the value reverts, the
// engine believes 2560x1431, and it sets that viewport on 2208-tall textures.
// Rendering a smaller region of a larger attachment, composited over itself,
// is a strong candidate for the "semi-transparent second render". Turning the
// override off makes the whole pipeline consistently 2560x1431 again, which is
// the only true baseline available.
// ON for this run. The write watch is useless with the override off: nothing
// ever writes the field, so there is nothing to catch. The revert only exists
// relative to OUR patch, so the patch has to be applied for the watch to fire.
// Expect the ghost to return -- this build is for the log, not for looking at.
static bool g_nativeRes = true;
// Independent of the override: find WHO writes the screen size.
static bool g_watchSize = true;
static void* volatile g_llSelfWatch = nullptr;
// The size the render targets were forced to, for the diagnostics.
static volatile LONG g_offscreenW = 0, g_offscreenH = 0;
static volatile LONG g_sdlWinLogged = 0;
// Resizing the WINDOW is retired -- see d_LowLevelInit. The window is
// left at whatever SOMA asked for; only the engine's stored size moves.
static bool g_resizeWindow = false;

// Defined below; forward-declared because both init hooks need it and they run
// earlier in the file.
static bool ProbeHeadsetResolution(int* outW, int* outH);

// Make sure a headset size is known, probing on the CALLING thread if the
// load-time probe has not produced one. Safe to call repeatedly: it only does
// work while the size is still unknown.
static bool EnsureHeadsetSize(const char* where) {
    if (!g_nativeRes) return false;
    if (InterlockedCompareExchange(&g_nativeW, 0, 0) > 0) return true;
    int pw = 0, ph = 0;
    if (ProbeHeadsetResolution(&pw, &ph)) {
        InterlockedExchange(&g_nativeW, pw);
        InterlockedExchange(&g_nativeH, ph);
        Log(">>> headset probed AT %s: %dx%d per eye. The load-time probe had not"
            " finished -- Init runs on its own thread and the injector resumes"
            " the game immediately, so it can lose that race and leave the game"
            " at its configured resolution with no error.", where, pw, ph);
        return true;
    }
    Log(">>> headset probe FAILED at %s. Is the runtime already running? The game"
        " will fall back to its configured resolution.", where);
    return false;
}

static unsigned long long d_GraphicsInit(
    void* self, unsigned int w, unsigned int h, unsigned int bpp, unsigned int rr,
    unsigned int fs, unsigned int ms, unsigned int drv, void* cap, void* pos,
    void* res, void* p12, unsigned int flags)
{
    // Probe HERE if the load-time probe has not produced a size yet. This call
    // is on the GAME's thread at the exact moment the size is needed, so it
    // cannot lose the startup race.
    EnsureHeadsetSize("GRAPHICS INIT");

    // Deliberately passes through untouched. The resolution is now forced in
    // d_LowLevelInit by patching the engine's stored screen size after init,
    // which does not require the window to change size. Substituting here as
    // well only altered what SOMA asked the OS for, and the OS said no.
    return o_GraphicsInit(self, w, h, bpp, rr, fs, ms, drv, cap, pos, res, p12, flags);
}

// Ask the runtime for the per-eye resolution WITHOUT starting a session. Needs
// only an instance + system, so it is safe to call during graphics init.
static bool ProbeHeadsetResolution(int* outW, int* outH) {
    HMODULE lo = LoadLibraryA("openxr_loader.dll");
    if (!lo) return false;

    typedef XrResult (XRAPI_PTR *PFN_GIPA)(XrInstance, const char*, PFN_xrVoidFunction*);
    PFN_GIPA gipa = (PFN_GIPA)GetProcAddress(lo, "xrGetInstanceProcAddr");
    if (!gipa) return false;

    PFN_xrCreateInstance             crI  = nullptr;
    PFN_xrDestroyInstance            dsI  = nullptr;
    PFN_xrGetSystem                  gSys = nullptr;
    PFN_xrEnumerateViewConfigurationViews eVC = nullptr;
    gipa(XR_NULL_HANDLE, "xrCreateInstance", (PFN_xrVoidFunction*)&crI);
    if (!crI) return false;

    XrInstanceCreateInfo ici{XR_TYPE_INSTANCE_CREATE_INFO};
    strcpy_s(ici.applicationInfo.applicationName, "hpl3vr-probe");
    ici.applicationInfo.apiVersion = XR_MAKE_VERSION(1, 0, 0);
    const char* exts[] = { "XR_KHR_opengl_enable" };
    ici.enabledExtensionCount = 1;
    ici.enabledExtensionNames = exts;

    XrInstance inst = XR_NULL_HANDLE;
    if (XR_FAILED(crI(&ici, &inst)) || inst == XR_NULL_HANDLE) return false;

    gipa(inst, "xrDestroyInstance", (PFN_xrVoidFunction*)&dsI);
    gipa(inst, "xrGetSystem",       (PFN_xrVoidFunction*)&gSys);
    gipa(inst, "xrEnumerateViewConfigurationViews", (PFN_xrVoidFunction*)&eVC);

    bool ok = false;
    if (gSys && eVC) {
        XrSystemGetInfo sgi{XR_TYPE_SYSTEM_GET_INFO};
        sgi.formFactor = XR_FORM_FACTOR_HEAD_MOUNTED_DISPLAY;
        XrSystemId sys = XR_NULL_SYSTEM_ID;
        if (XR_SUCCEEDED(gSys(inst, &sgi, &sys)) && sys != XR_NULL_SYSTEM_ID) {
            uint32_t n = 0;
            XrViewConfigurationView v[2]{{XR_TYPE_VIEW_CONFIGURATION_VIEW},
                                        {XR_TYPE_VIEW_CONFIGURATION_VIEW}};
            if (XR_SUCCEEDED(eVC(inst, sys,
                    XR_VIEW_CONFIGURATION_TYPE_PRIMARY_STEREO, 2, &n, v)) && n >= 1) {
                *outW = (int)v[0].recommendedImageRectWidth;
                *outH = (int)v[0].recommendedImageRectHeight;
                ok = (*outW > 0 && *outH > 0);
            }
        }
    }
    if (dsI && inst) dsI(inst);
    return ok;
}

// --- SDL_CreateWindow --------------------------------------------------
typedef void* (*PFN_SDLCreateWindow)(const char*, int, int, int, int, unsigned int);
typedef void  (*PFN_SDLSetWindowSize)(void*, int, int);
static PFN_SDLCreateWindow  o_SDL_CreateWindow = nullptr;
static PFN_SDLSetWindowSize p_SDL_SetWindowSize = nullptr;

static void* d_SDL_CreateWindow(const char* title, int x, int y, int w, int h,
                                unsigned int flags) {
    EnsureHeadsetSize("SDL_CreateWindow");
    // Observe only. Forcing the window larger than the desktop does not work:
    // Windows clamps it, SDL_GetWindowSize reports the clamp, and the engine
    // believes the clamp. The render targets are resized in d_LowLevelInit
    // instead, which needs no cooperation from the window manager.
    void* wnd = o_SDL_CreateWindow(title, x, y, w, h, flags);
    if (!InterlockedExchange(&g_sdlWinLogged, 1))
        Log("SDL_CreateWindow %dx%d flags 0x%x -- left alone on purpose;"
            " the window size no longer determines the render resolution",
            w, h, flags);
    return wnd;
}

// --- cLowLevelGraphicsSDL::Init (RVA 0x442E00) ----------------------------
typedef char (*PFN_LLInit)(void* self, unsigned int w, unsigned int h,
                           unsigned int bpp, unsigned int rr, unsigned int fs,
                           unsigned int ms, unsigned int drv, void* cap, void* pos);
static PFN_LLInit o_LowLevelInit = nullptr;


// ===================== WRITE WATCH ON THE SCREEN SIZE =====================
// Every previous attempt held values down after something reverted them. This
// finds the reverter instead. A hardware write breakpoint (DR0) on the 4 bytes
// at lowlevel+0x10 fires only on a WRITE to exactly that dword, so unlike a
// PAGE_GUARD it does not trip on the constant reads of the same object.
//
// DR7 layout used: L0 (bit 0) enables the breakpoint locally; R/W0 (bits 16-17)
// = 01 means break on data write; LEN0 (bits 18-19) = 11 means 4 bytes. The
// address must be 4-byte aligned, which +0x10 is.
static void*         g_watchAddr    = nullptr;
static volatile LONG g_watchHits    = 0;
static PVOID         g_vehHandle    = nullptr;
static uintptr_t     g_exeBase      = 0;

static LONG CALLBACK WatchVeh(EXCEPTION_POINTERS* ep) {
    if (ep->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP)
        return EXCEPTION_CONTINUE_SEARCH;
    CONTEXT* c = ep->ContextRecord;
    if (!(c->Dr6 & 0x1)) return EXCEPTION_CONTINUE_SEARCH;   // not our DR0

    LONG n = InterlockedIncrement(&g_watchHits);
    if (n <= 8) {
        // Rip is the instruction AFTER the write, which is what we want to
        // look up: the store is the instruction just before it.
        uintptr_t rip = (uintptr_t)c->Rip;
        // rip - exeBase is only meaningful if the write came FROM the exe.
        // The frustum run produced values like 0x46229BA04 and a kernel
        // address, which are that subtraction applied to a rip that lives in
        // some other module -- meaningless as a Ghidra address. Resolve the
        // containing module first and report module+offset, so the number can
        // actually be looked up.
        HMODULE mod = nullptr;
        char modName[MAX_PATH] = {0};
        const char* shortName = "<unknown>";
        uintptr_t modBase = 0;
        if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS
                             | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                               (LPCSTR)rip, &mod) && mod) {
            modBase = (uintptr_t)mod;
            if (GetModuleFileNameA(mod, modName, MAX_PATH)) {
                const char* sl = strrchr(modName, '\\');
                shortName = sl ? sl + 1 : modName;
            }
        }
        const float* m = (const float*)g_watchAddr;
        if (modBase) {
            Log(">>> WRITE #%ld to the watched address from %s+0x%llX"
                "  (translation now %.3f %.3f %.3f)",
                n, shortName, (unsigned long long)(rip - modBase),
                m ? m[12] : 0.f, m ? m[13] : 0.f, m ? m[14] : 0.f);
            // The writer turned out to be memcpy inside the CRT: the engine
            // does not compose the view matrix in place, it copies it in
            // wholesale every frame. So the REAL matrix lives at the copy's
            // SOURCE, which on the x64 convention is RSI. Log it, and read the
            // translation row from it -- that is the engine's own eye position,
            // the thing three write targets failed to find.
            if (modBase != g_exeBase) {
                // RIP is inside the CRT, so it names memcpy, not the caller --
                // and RSI turned out to be the frustum itself, so the earlier
                // "source view matrix" reading was wrong. What identifies the
                // engine code is the RETURN ADDRESS. Walk the stack for the
                // first slot pointing into Soma.exe rather than assuming how
                // many frames the CRT pushed.
                uintptr_t exeLo = g_exeBase, exeHi = g_exeBase + 0x2000000;
                uintptr_t* sp = (uintptr_t*)(uintptr_t)c->Rsp;
                int found = 0;
                for (int i = 0; i < 64 && found < 3; ++i) {
                    if (IsBadReadPtr(sp + i, sizeof(uintptr_t))) break;
                    uintptr_t v = sp[i];
                    if (v > exeLo && v < exeHi) {
                        Log("    CALLER #%d: Soma.exe+0x%llX  (Ghidra"
                            " 0x%llX) -- this is engine code that reached the"
                            " CRT copy. The nearest one is the function that"
                            " fills the view matrix.",
                            found + 1,
                            (unsigned long long)(v - g_exeBase),
                            (unsigned long long)(v - g_exeBase + 0x140000000ULL));
                        ++found;
                    }
                }
                if (!found)
                    Log("    no Soma.exe return address found on the stack --"
                        " the caller may be a tail call or the frame is not"
                        " walkable from here.");
            }
            if (modBase == g_exeBase)
                Log("    ^ this one IS the game module: add 0x140000000 to that"
                    " offset for the Ghidra address. The STORE is the"
                    " instruction immediately before it.");
        } else {
            Log(">>> WRITE #%ld from rip %p, which is in NO loaded module"
                " (kernel or JIT). Not a Ghidra address; ignore it.",
                n, (void*)rip);
        }
    }
    c->Dr6 = 0;                       // acknowledge
    return EXCEPTION_CONTINUE_EXECUTION;
}

// Arm DR0 on every thread in this process except our own.
static int ArmWatchAllThreads(void* addr) {
    g_watchAddr = addr;
    int armed = 0;
    DWORD me = GetCurrentThreadId(), pid = GetCurrentProcessId();
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snap == INVALID_HANDLE_VALUE) return 0;
    THREADENTRY32 te; te.dwSize = sizeof(te);
    if (Thread32First(snap, &te)) {
        do {
            if (te.th32OwnerProcessID != pid || te.th32ThreadID == me) continue;
            HANDLE th = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT |
                                   THREAD_SUSPEND_RESUME, FALSE, te.th32ThreadID);
            if (!th) continue;
            SuspendThread(th);
            CONTEXT c; memset(&c, 0, sizeof(c));
            c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
            if (GetThreadContext(th, &c)) {
                c.Dr0 = (DWORD64)(uintptr_t)addr;
                c.Dr7 &= ~(DWORD64)0xF0003;      // clear L0/G0 and R/W0+LEN0
                c.Dr7 |=  (DWORD64)0x1;          // L0
                c.Dr7 |=  (DWORD64)0x1 << 16;    // R/W0 = 01, break on write
                c.Dr7 |=  (DWORD64)0x3 << 18;    // LEN0 = 11, 4 bytes
                c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
                if (SetThreadContext(th, &c)) ++armed;
            }
            ResumeThread(th);
            CloseHandle(th);
        } while (Thread32Next(snap, &te));
    }
    CloseHandle(snap);
    return armed;
}
// ========================================================================


// --- cLowLevelGraphicsSDL::SetScreenSize (RVA 0x43EFE0) -------------------
// FOUND BY WRITE WATCH, not by guessing. This is what reverted the size:
//     *(int  *)(param_1 + 0x10) = local_res10[0];   // from the ARGUMENTS
//     *(uint *)(param_1 + 0x14) = local_res18[0];
//     *(u32  *)(param_1 + 0x5c) = *(u32 *)(param_1 + 0x10);   // scissor w
//     *(u32  *)(param_1 + 0x60) = *(u32 *)(param_1 + 0x14);   // scissor h
//     glScissor(..., +0x5c, +0x60);
// One call resets the screen size AND the scissor from its arguments. That is
// why holding +0x10 down never worked, and why the extra copies kept coming
// back: they are all recomputed here from the same two ints.
//
// So substitute the ARGUMENTS instead of chasing the fields. Everything this
// function derives then comes out at the headset size in one consistent step,
// including the scissor rect -- which the earlier hold-downs never corrected,
// and which is the most likely source of the torn, ghosted image.
typedef void (*PFN_SetScreenSize)(void*, int, unsigned int);
static PFN_SetScreenSize o_SetScreenSize = nullptr;
static volatile LONG g_sssCount = 0;

static void d_SetScreenSize(void* self, int w, unsigned int h) {
    LONG nw = InterlockedCompareExchange(&g_nativeW, 0, 0);
    LONG nh = InterlockedCompareExchange(&g_nativeH, 0, 0);
    LONG k = InterlockedIncrement(&g_sssCount);
    if (g_nativeRes && nw > 0 && nh > 0 &&
        (w != (int)nw || h != (unsigned)nh)) {
        if (k <= 4)
            Log(">>> SetScreenSize(%d, %u) -> (%ld, %ld). This is the call the"
                " write watch caught at RVA 0x43F12A. It sets the screen size"
                " AND the scissor from these arguments, so overriding them here"
                " keeps every derived value consistent instead of leaving the"
                " scissor at the old size.", w, h, nw, nh);
        w = (int)nw; h = (unsigned)nh;
    } else if (k <= 4) {
        Log(">>> SetScreenSize(%d, %u) -- left alone", w, h);
    }
    o_SetScreenSize(self, w, h);
}

static char d_LowLevelInit(void* self, unsigned int w, unsigned int h,
                           unsigned int bpp, unsigned int rr, unsigned int fs,
                           unsigned int ms, unsigned int drv, void* cap, void* pos)
{
    LONG nw = InterlockedCompareExchange(&g_nativeW, 0, 0);
    LONG nh = InterlockedCompareExchange(&g_nativeH, 0, 0);
    if (nw <= 0 || nh <= 0) {     // no session yet -- ask the runtime directly
        int pw = 0, ph = 0;
        if (ProbeHeadsetResolution(&pw, &ph)) {
            InterlockedExchange(&g_nativeW, pw);
            InterlockedExchange(&g_nativeH, ph);
            nw = pw; nh = ph;
            Log("    headset probed WITHOUT a session: %dx%d per eye", pw, ph);
        }
    }
    Log(">>> lowlevel graphics init: asked for %ux%u bpp %u fs %u"
        "  (headset wants %ldx%ld)", w, h, bpp, fs, nw, nh);

    // Let the WINDOW be created exactly as SOMA wanted it. Trying to make the
    // window headset-sized was the wrong approach for six builds: Windows
    // clamps a window to the display, SDL_GetWindowSize reports the clamp, and
    // the engine sizes everything from that. Proven by the last run --
    // fs:2, flags:18, "Creating window: 2064 x 2208", drawable still 2560x1431.
    //
    // Other VR mods never resize the window. They render OFFSCREEN. An FBO has
    // no relationship to display modes or work areas; the only ceiling is
    // GL_MAX_RENDERBUFFER_SIZE (>=16384 here). What actually has to change is
    // not the window but the SIZE THE ENGINE BELIEVES IT HAS, because that is
    // what every render target is allocated from.
    char r = o_LowLevelInit(self, w, h, bpp, rr, fs, ms, drv, cap, pos);

    // From FUN_140442E00, after SDL_CreateWindow:
    //     SDL_GetWindowSize(lVar5, local_res10, local_res18);
    //     *(int  *)(param_1 + 2)              = local_res10[0];   // +0x10
    //     *(uint *)((longlong)param_1 + 0x14) = local_res18[0];   // +0x14
    // param_1 is longlong*, so (param_1 + 2) is byte offset 0x10. Those two
    // fields are the engine's idea of its screen size. Overwrite them here,
    // AFTER init has stored the clamped values, and the G-buffer chain is built
    // at headset resolution while the window stays an ordinary desktop window.
    if (g_nativeRes && nw > 0 && nh > 0 && self) {
        volatile int*  pw = (volatile int*) ((char*)self + 0x10);
        volatile unsigned* ph = (volatile unsigned*)((char*)self + 0x14);
        int  gotW = *pw; unsigned gotH = *ph;
        if (gotW > 0 && gotH > 0 && gotW < 32768 && gotH < 32768) {
            *pw = (int)nw; *ph = (unsigned)nh;
            Log("    OFFSCREEN RESOLUTION: engine screen size %dx%u -> %ldx%ld,"
                " patched at self+0x10/+0x14 AFTER init stored the clamped"
                " window size. The window stays %ux%u; only the render targets"
                " change. Verify below: 'engine viewport during the eye pass'"
                " must now read %ldx%ld.", gotW, gotH, nw, nh, w, h, nw, nh);
            InterlockedExchange(&g_offscreenW, nw);
            InterlockedExchange(&g_offscreenH, nh);
        } else {
            Log("    OFFSCREEN RESOLUTION: self+0x10/+0x14 held %dx%u, which is"
                " not a plausible screen size -- the offsets are wrong for this"
                " build. NOT patching; re-read FUN_140442E00 before trusting"
                " them.", gotW, gotH);
        }
    }

    // Arm the write watch regardless of whether the override is on. Knowing WHO
    // reverts the size is useful either way, and with the override off there is
    // no risk of the ghost confusing the picture.
    if (g_watchSize && self && !g_vehHandle) {
        g_exeBase = (uintptr_t)GetModuleHandleA(NULL);
        g_vehHandle = AddVectoredExceptionHandler(1, WatchVeh);
        int armed = ArmWatchAllThreads((char*)self + 0x10);
        g_llSelfWatch = self;
        Log("");
        Log(">>> WRITE WATCH armed on lowlevel+0x10 (%p) across %d thread(s).",
            (char*)self + 0x10, armed);

        // POSITIVE CONTROL. Without this, "no hits" is worthless: it cannot be
        // distinguished from a watch that never worked. Arm this thread too and
        // write the field ourselves. If SELFTEST does not appear immediately,
        // the mechanism is broken and any later silence means nothing.
        {
            CONTEXT c; memset(&c, 0, sizeof(c));
            c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
            HANDLE me = GetCurrentThread();
            if (GetThreadContext(me, &c)) {
                c.Dr0 = (DWORD64)(uintptr_t)((char*)self + 0x10);
                c.Dr7 &= ~(DWORD64)0xF0003;
                c.Dr7 |=  (DWORD64)0x1;
                c.Dr7 |=  (DWORD64)0x1 << 16;
                c.Dr7 |=  (DWORD64)0x3 << 18;
                c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
                SetThreadContext(me, &c);
            }
            LONG before = InterlockedCompareExchange(&g_watchHits, 0, 0);
            volatile int* probe = (volatile int*)((char*)self + 0x10);
            int keep = *probe;
            *probe = keep;                     // a real write, same value
            LONG after = InterlockedCompareExchange(&g_watchHits, 0, 0);
            if (after > before)
                Log("    SELFTEST OK: the watch fired on our own write."
                    " Silence from here really does mean nobody writes it.");
            else
                Log("    SELFTEST FAILED: our own write did NOT trigger the"
                    " watch. The breakpoint is not working -- something else"
                    " owns the debug registers, or the VEH is not reached."
                    " DISREGARD any 'no writes' conclusion from this run.");
        }
        Log("    A hardware write breakpoint, so it fires ONLY on writes to"
            " those 4 bytes -- not on the constant reads of this object.");
        Log("    Whatever reverts the size to the window size will now name"
            " itself, instead of us guessing which copy to hold down.");
        Log("");
    }
    return r;
}

// --- cCamera3D::UpdateViewMatrix (RVA 0x277630) ---------------------------
// Layout recovered from its decompilation:
//   +0x10/14/18  position      +0x44 pitch   +0x48 yaw   +0x4C roll
//   +0x74 view   +0xB4 inverse view   +0xF4 projection   +0x3F8 cFrustum
// It negates each euler and composes three axis rotations onto -position.
// Injecting here puts the head pose AHEAD of culling, unlike every previous
// attempt which ran after visibility was already decided.
typedef void (*PFN_UpdateView)(void* camera);
static PFN_UpdateView o_UpdateViewMatrix = nullptr;
static bool g_cameraHook = true;              // N toggles once proven
static volatile LONG g_camHookHits = 0;
static volatile LONG g_camTransHits = 0;
static volatile LONG g_camTransEntered = 0;
static volatile LONG g_camTransVerified = 0;
static volatile LONG g_camTransVerifyFailed = 0;
static volatile LONG g_cameraPosHeadSuppressed = 0;
static volatile float g_camTransLastError = 0.0f;
static volatile float g_camTransMaxError = 0.0f;
static volatile float g_dbgViewT[3] = {0,0,0};
static volatile LONG g_viewDumped = 0;
static volatile float g_playerYaw = 0.0f;
static float g_camTestYaw = 0.0f;             // [ and ] nudge, for the 30-deg test

static const int kCamPitch = 0x44, kCamYaw = 0x48, kCamRoll = 0x4C;
// From FUN_1402771d0: projection built from (+0x34 fov, +0x30 aspect,
// +0x28 near, +0x2c far).
// Located by value, not by guessing the argument order.
static int kCamFov = -1, kCamAspect = -1;
static volatile LONG g_camFovSet = 0, g_camFieldsFound = 0;
static float g_camFovDeg = 0.0f, g_camAspectSet = 0.0f;

static void FindCameraFovFields(const char* C) {
    if (InterlockedExchange(&g_camFieldsFound, 1)) return;
    Log("");
    Log(">>> CAMERA FIELDS (searching +0x20..+0x40 by value)");
    for (int off = 0x20; off <= 0x40; off += 4) {
        float v = *(const float*)(C + off);
        const char* what = "";
        // FOV is a radian angle; that range is stable whatever the render
        // target is. ASPECT was matched on 1.70-1.85 -- i.e. hardcoded 16:9 --
        // which broke the moment the headset's 0.935 aspect reached the camera:
        // identification failed, kCamAspect stayed -1, and the whole mod
        // silently disabled itself. Accept any plausible aspect instead.
        if (v > 1.30f && v < 1.60f) { what = "  <-- FOV (radians, 83 deg)"; kCamFov = off; }
        else if (kCamFov >= 0 && off == kCamFov + 4 && v > 0.20f && v < 4.00f) {
            what = "  <-- ASPECT (whatever the target is)"; kCamAspect = off; }
        else if (v > 0.01f && v < 0.10f) what = "  <-- near plane";
        else if (v > 500.0f)             what = "  <-- far plane";
        Log("    +0x%02x = %10.4f%s", off, v, what);
    }
    if (kCamFov < 0 || kCamAspect < 0)
        Log("    COULD NOT IDENTIFY both -- not widening the camera");
    else
        Log("    using FOV at +0x%02x, aspect at +0x%02x", kCamFov, kCamAspect);
    Log("");
}


// --- 6DOF head translation, written into camera+0x74 ------------------------
// The write watch settled this. FUN_1402760b0 (the frustum setup) does:
//     memcpy((void*)(param_1 + 0x158), param_3, 0x40);
// so the frustum NEVER composes the view matrix -- it stores whatever it is
// handed. And FUN_140277d80 (cCamera3D::GetFrustum) is the caller that hands it
// over, passing camera+0x74:
//     if (camera[0x709]) FUN_140277630();        // UpdateViewMatrix, only if dirty
//     FUN_1402765f0(camera+0x3f8, proj, camera+0x74, ...);
//
// The measured ownership chain is therefore:
//   * writing frustum+0x158 was pointless -- the memcpy overwrites it,
//   * direct probes at camera+0x10 and renderer+0xbd4 did not move the view,
//   * camera+0x74 is the only measured address that did.
//
// So the head position belongs in camera+0x74 itself, which is exactly where
// the rotation already goes -- and rotation is the one thing that has worked
// all along.
//
// A view matrix holds -R*eye in its translation, so displacing the eye by d in
// world space means subtracting R*d from that translation.
static void ApplyHeadTranslationToCameraView(void* camera) {
    InterlockedIncrement(&g_camTransEntered);
    if (!camera || !g_headTranslation) return;
    if (!InterlockedCompareExchange(&g_xrOriginSet, 0, 0)) return;

    float d[3] = { g_eyeMid[0] - g_xrOrigin[0],
                   g_eyeMid[1] - g_xrOrigin[1],
                   g_eyeMid[2] - g_xrOrigin[2] };
    LONG hm = InterlockedCompareExchange(&g_headMode, 0, 0);
    if (hm == 6) return;                              // OFF
    if (hm == 7) { d[0] = 1.0f; d[1] = 0.0f; d[2] = 0.0f; }
    if (hm == 8) { d[0] = 0.0f; d[1] = 0.0f; d[2] = 1.0f; }

    // XR stage space -> SOMA world space.  This conversion is retained only as
    // the already-tested mode mapping; the ownership fix below is independent
    // of which mapping ultimately proves correct.
    float cy = cosf(g_playerYaw), sy = sinf(g_playerYaw);
    float gx =  cy*d[0] + sy*d[2];
    float gy =  d[1];
    float gz = -sy*d[0] + cy*d[2];
    float wx, wy = gy, wz;
    switch (hm) {
      case 1: wx =  gx; wz = -gz; break;
      case 2: wx = -gx; wz =  gz; break;
      case 3: wx =  gz; wz =  gx; break;
      case 4: wx = -gx; wy = -gy; wz = -gz; break;
      case 5: wx =  d[0]; wy = d[1]; wz = d[2]; break;
      default: wx = gx; wz = gz; break;
    }
    wx *= g_headTransScale; wy *= g_headTransScale; wz *= g_headTransScale;

    float* V = (float*)((char*)camera + 0x74);
    if (!InterlockedExchange(&g_viewDumped, 1)) {
        const float* C10 = (const float*)((char*)camera + 0x10);
        Log("");
        Log(">>> camera+0x74 RAW (before any of our edits this call):");
        for (int r = 0; r < 4; ++r)
            Log("      [%2d..%2d]  %9.4f %9.4f %9.4f %9.4f",
                r*4, r*4+3, V[r*4+0], V[r*4+1], V[r*4+2], V[r*4+3]);
        Log("    camera+0x10 world position: %.4f %.4f %.4f", C10[0], C10[1], C10[2]);
    }

    const float t0[3] = { V[3], V[7], V[11] };
    const float eye0[3] = {
        -(V[0]*t0[0] + V[4]*t0[1] + V[8]*t0[2]),
        -(V[1]*t0[0] + V[5]*t0[1] + V[9]*t0[2]),
        -(V[2]*t0[0] + V[6]*t0[1] + V[10]*t0[2])
    };

    // Sole head-centre writer.  For row-major V=[R|-R*C], moving the camera by
    // w requires t' = t - R*w.
    const float dt[3] = {
        -(V[0]*wx + V[1]*wy + V[2]*wz),
        -(V[4]*wx + V[5]*wy + V[6]*wz),
        -(V[8]*wx + V[9]*wy + V[10]*wz)
    };
    V[3]  += dt[0];
    V[7]  += dt[1];
    V[11] += dt[2];

    // Runtime positive control: recover the camera position from the matrix and
    // verify that it moved by exactly w.  A zero/near-zero error proves both that
    // this code executed and that the write had the intended geometric effect.
    const float t1[3] = { V[3], V[7], V[11] };
    const float eye1[3] = {
        -(V[0]*t1[0] + V[4]*t1[1] + V[8]*t1[2]),
        -(V[1]*t1[0] + V[5]*t1[1] + V[9]*t1[2]),
        -(V[2]*t1[0] + V[6]*t1[1] + V[10]*t1[2])
    };
    float err = 0.0f;
    err = fmaxf(err, fabsf((eye1[0] - eye0[0]) - wx));
    err = fmaxf(err, fabsf((eye1[1] - eye0[1]) - wy));
    err = fmaxf(err, fabsf((eye1[2] - eye0[2]) - wz));
    g_camTransLastError = err;
    if (err > g_camTransMaxError) g_camTransMaxError = err;
    if (err < 0.0001f) InterlockedIncrement(&g_camTransVerified);
    else               InterlockedIncrement(&g_camTransVerifyFailed);

    g_dbgViewT[0] = t0[0]; g_dbgViewT[1] = t0[1]; g_dbgViewT[2] = t0[2];
    g_dbgHeadRaw[0] = d[0]; g_dbgHeadRaw[1] = d[1]; g_dbgHeadRaw[2] = d[2];
    g_dbgHead[0] = wx; g_dbgHead[1] = wy; g_dbgHead[2] = wz;
    g_dbgHeadDeltaT[0] = dt[0]; g_dbgHeadDeltaT[1] = dt[1]; g_dbgHeadDeltaT[2] = dt[2];
    InterlockedIncrement(&g_camTransHits);

    // Low-rate, finite trace.  The raw position, converted displacement, basis,
    // and actual translation delta are logged together so a fixed lean while
    // rotating can be judged from one record rather than correlated variables.
    LONG div = InterlockedIncrement(&g_headTraceDiv);
    if ((div % 120) == 0) {
        LONG budget = InterlockedCompareExchange(&g_headTraceBudget, 0, 0);
        if (budget > 0 &&
            InterlockedCompareExchange(&g_headTraceBudget, budget - 1, budget) == budget) {
            Log("6DOF TRACE mode %ld | dXR(%+.4f %+.4f %+.4f) wGame(%+.4f %+.4f %+.4f)"
                " | R0(%+.4f %+.4f %+.4f) R1(%+.4f %+.4f %+.4f)"
                " R2(%+.4f %+.4f %+.4f) | dt(%+.4f %+.4f %+.4f) verify %.6f",
                hm, d[0], d[1], d[2], wx, wy, wz,
                V[0], V[1], V[2], V[4], V[5], V[6], V[8], V[9], V[10],
                dt[0], dt[1], dt[2], err);
        }
    }
}

static void d_UpdateViewMatrix(void* camera) {
    if (camera) g_cameraObj = camera;
    if (g_cameraHook && camera) {
        float q[4] = {0,0,0,1}, pos[3] = {0,0,0};
        bool live = HeadPoseActive() && CurrentHeadPose(q, pos);
        // The test yaw must apply with NO VR active, or the verification is
        // impossible. Run whenever either the pose or the test offset is set.
        if (live || g_camTestYaw != 0.0f) {
            // Quaternion -> euler, in the same convention the engine uses.
            float yaw   = atan2f(2*(q[3]*q[1] + q[0]*q[2]), 1 - 2*(q[1]*q[1] + q[0]*q[0]));
            float pitch = asinf(fmaxf(-1.0f, fminf(1.0f, 2*(q[3]*q[0] - q[1]*q[2]))));
            float roll  = atan2f(2*(q[3]*q[2] + q[0]*q[1]), 1 - 2*(q[0]*q[0] + q[2]*q[2]));

            char* C = (char*)camera;
            float* pP = (float*)(C + kCamPitch);
            float* pY = (float*)(C + kCamYaw);
            float* pR = (float*)(C + kCamRoll);

            // Compose onto the game's own look direction, then restore, so the
            // player's mouse-look is untouched between frames.
            float oP = *pP, oY = *pY, oR = *pR;
            *pP = oP + pitch;
            *pY = oY + yaw + g_camTestYaw;
            g_playerYaw = oY;   // the game's own yaw, without the head pose
            *pR = oR + roll;

            // No position write is allowed on camera+0x10/+0x14/+0x18 here.
            // The previous build temporarily wrote head Y (and attempted X/Z)
            // before UpdateViewMatrix, then wrote the full displacement again to
            // camera+0x74 and once more in ApplyHeadPose.  This counter is a
            // positive control: non-zero proves the old third writer was reached
            // and deliberately suppressed in this build.
            LONG hm = InterlockedCompareExchange(&g_headMode, 0, 0);
            if (g_headTranslation
                && InterlockedCompareExchange(&g_xrOriginSet, 0, 0)
                && hm != 6)
                InterlockedIncrement(&g_cameraPosHeadSuppressed);

            // Match the camera's FOV to what we actually render with, or the
            // engine culls a narrower cone than we draw.
            FindCameraFovFields(C);
            // The FOV is widened in the GetFrustum hook instead -- that is
            // where the culling planes are actually built.
            float* pF = nullptr; float* pA = nullptr;
            float oF = 0.0f, oA = 0.0f;
            bool widened = false;
            if (false) {
                const xrs::EyeView& ev = g_xr.View((int)InterlockedCompareExchange(&g_eye,0,0));
                if (ev.valid) {
                    float vF = ev.fov.angleUp - ev.fov.angleDown;
                    float hF = ev.fov.angleRight - ev.fov.angleLeft;
                    *pF = vF;
                    *pA = tanf(hF*0.5f) / tanf(vF*0.5f);
                    widened = true;
                    if (!InterlockedExchange(&g_camFovSet, 1)) {
                        g_camFovDeg = vF * 57.2957795f;
                        g_camAspectSet = *pA;
                        Log("camera FOV widened to the headset: %.1f deg, aspect %.3f"
                            " (was %.1f / %.3f) -- the engine now CULLS what we DRAW",
                            g_camFovDeg, g_camAspectSet, oF * 57.2957795f, oA);
                    }
                }
            }

            // +0x70A view dirty, +0x70C frustum dirty. Force both so the
            // engine rebuilds from the values we just wrote.
            //
            // +0x709 MATTERS TOO, and it was the missing one. GetFrustum
            // (FUN_140277d80) gates the rebuild on it specifically:
            //     if (*(char *)(param_1 + 0x709) != '\0') FUN_140277630();
            // With it clear, UpdateViewMatrix early-outs and camera+0x74 keeps
            // whatever it had -- so the head translation we add lands on a
            // matrix that ALREADY carries the previous frame's translation and
            // compounds. That is the drift: the eye separation degraded from a
            // clean +-0.0315 to +0.0866 / +0.1496 in proportion to how far the
            // head had moved, which a common translation can never do unless it
            // is being applied repeatedly to its own result.
            *(unsigned char*)(C + 0x709) = 1;
            *(unsigned char*)(C + 0x70A) = 1;
            *(unsigned char*)(C + 0x70C) = 1;

            o_UpdateViewMatrix(camera);
            // 6DOF goes HERE, not after the fallback call at the bottom of this
            // function: this branch ends with `return`, so the tail is never
            // reached when the camera hook is active -- the counter read 0 of
            // 1214 calls. The matrix has just been rebuilt above, so this is the
            // moment its translation can be displaced before GetFrustum hands
            // camera+0x74 to the frustum's memcpy.
            ApplyHeadTranslationToCameraView(camera);

            if (widened) { *pF = oF; *pA = oA; }
            *pP = oP; *pY = oY; *pR = oR;
            InterlockedIncrement(&g_camHookHits);
            return;
        }
    }
    o_UpdateViewMatrix(camera);
    ApplyHeadTranslationToCameraView(camera);
}

// --- Setup Light Instancing (RVA 0x406560) --------------------------------
// It caches a matrix built from frustum+0x158 into renderer+0x96c, once per
// frame, and the deferred lighting uses that cache afterwards. If it is built
// from a view we later change, the lighting works in a stale space. Identify
// what the cache actually is rather than assuming.
// cCamera3D::GetFrustum (RVA 0x277D80): lazily rebuilds the frustum at +0x3F8
// from the camera's FOV/aspect/near/far. This is where the culling planes come
// from, so this is where the headset FOV has to be in place.
typedef void* (*PFN_GetFrustum)(void* camera, char param2);
static PFN_GetFrustum o_GetFrustum = nullptr;
static volatile LONG g_worldScaleLogged = 0;
static volatile LONG g_frustumWidened = 0, g_coneLogged = 0;

static void* d_GetFrustum(void* camera, char param2) {
    if (!camera || kCamFov < 0 || kCamAspect < 0 ||
        !InterlockedCompareExchange(&g_xrOn, 0, 0) || !g_xr.Ready())
        return o_GetFrustum(camera, param2);

    const xrs::EyeView& ev = g_xr.View((int)InterlockedCompareExchange(&g_eye, 0, 0));
    if (!ev.valid) return o_GetFrustum(camera, param2);

    char* C = (char*)camera;
    float* pF = (float*)(C + kCamFov);
    float* pA = (float*)(C + kCamAspect);
    float oF = *pF, oA = *pA;

    // The headset frustum is ASYMMETRIC but cCamera3D can only express a
    // symmetric cone. Sizing it from the total span uses the AVERAGE half-angle,
    // which does not contain the wider side: 2 deg horizontally and 1 deg
    // vertically get rendered but culled away, and the deficient side swaps
    // between eyes. Size it from the MAXIMUM half-angle so the culling cone
    // fully contains the render frustum.
    float hhR, hvR;
    RenderHalfAngles(ev, &hhR, &hvR);      // exactly what the projection uses
    float vF = 2.0f * hvR;
    float hF = 2.0f * hhR;
    *pF = vF;
    *pA = tanf(hF*0.5f) / tanf(vF*0.5f);
    g_xrAspect = *pA;   // publish it so FrustumIsMain still recognises the camera
    if (!InterlockedExchange(&g_coneLogged, 1))
        Log("culling cone sized to CONTAIN the asymmetric eye frustum:"
            " %.1f x %.1f deg (was %.1f x %.1f -- short by %.1f deg horizontally,"
            " which is what vanished at the edges)",
            hF*57.2957795f, vF*57.2957795f,
            (ev.fov.angleRight-ev.fov.angleLeft)*57.2957795f,
            (ev.fov.angleUp-ev.fov.angleDown)*57.2957795f,
            (hF-(ev.fov.angleRight-ev.fov.angleLeft))*57.2957795f);
    *(unsigned char*)(C + 0x70C) = 1;      // force the frustum to rebuild

    void* r = o_GetFrustum(camera, param2);

    // UNIFORM WORLD SCALE, applied to the FRUSTUM's copy of the view matrix.
    //
    // From FUN_140277630: the camera keeps its view at camera+0x74 and the
    // inverse at camera+0xb4, and rows +0x74/+0x84/+0x94 are read elsewhere as
    // the right/up/forward BASIS VECTORS (FUN_140277C80, ...CF0, ...D30).
    // Scaling those would make them non-unit and corrupt gameplay that asks the
    // camera which way it is facing. The frustum's copy at +0x158 is read only
    // by rendering, so that is the safe place to scale.
    //
    // V' = Scale(1/S) * V shrinks every world distance by S. The FOV is
    // untouched and still matches what we submit to the runtime, so angular
    // correspondence holds and head rotation stays locked to the world -- which
    // is what the FOV-widening version could not do.
    if (r && g_worldScale > 0.01f && fabsf(g_worldScale - 1.0f) > 0.001f) {
        char* F = (char*)r;
        float* V = (float*)(F + kFrustumView);
        const float inv = 1.0f / g_worldScale;
        // Row-major: rows 0..2 are the basis, column 3 is the translation.
        // Scaling all of rows 0..2 scales basis and translation together.
        for (int i = 0; i < 12; ++i) V[i] *= inv;
        // ViewProj must be rebuilt or the two disagree and the depth pass
        // reconstructs positions from a matrix the geometry never used.
        const float* P = (const float*)(F + kFrustumProj);
        float Vt[16], Pt[16], VP[16];
        memcpy(Vt, V, 64); hpl3vr::TransposeInPlace(Vt);
        memcpy(Pt, P, 64); hpl3vr::TransposeInPlace(Pt);
        vpm::Mul4x4(Pt, Vt, VP);
        hpl3vr::TransposeInPlace(VP);
        memcpy(F + kFrustumViewProj, VP, 64);
        if (!InterlockedExchange(&g_worldScaleLogged, 1))
            Log(">>> world scale %.2f applied to frustum+0x158 (and ViewProj at"
                " +0x118 rebuilt). FOV untouched, so tracking stays locked.",
                g_worldScale);
    }

    *pF = oF; *pA = oA;
    InterlockedIncrement(&g_frustumWidened);
    return r;
}

typedef void (*PFN_LightSetup)(void* renderer);
static PFN_LightSetup o_LightSetup = nullptr;
static volatile LONG g_lightSetupHits = 0, g_lightSetupChecked = 0;
static bool g_cacheIsInverse = false, g_cacheIsTranspose = false, g_cacheMatches = false;

static void Mat4InverseRigid(const float* m, float* out) {
    // Row-major rigid inverse: transpose the 3x3, negate the translation.
    for (int r = 0; r < 3; ++r)
        for (int c = 0; c < 3; ++c) out[r*4+c] = m[c*4+r];
    for (int r = 0; r < 3; ++r)
        out[r*4+3] = -(m[0*4+r]*m[0*4+3] + m[1*4+r]*m[1*4+3] + m[2*4+r]*m[2*4+3]);
    out[12]=out[13]=out[14]=0.0f; out[15]=1.0f;
}

// World position implied by a row-major view matrix: -R^T * t.
static void CamPosFromView(const float* V, float* out) {
    out[0] = -(V[0*4+0]*V[0*4+3] + V[1*4+0]*V[1*4+3] + V[2*4+0]*V[2*4+3]);
    out[1] = -(V[0*4+1]*V[0*4+3] + V[1*4+1]*V[1*4+3] + V[2*4+1]*V[2*4+3]);
    out[2] = -(V[0*4+2]*V[0*4+3] + V[1*4+2]*V[1*4+3] + V[2*4+2]*V[2*4+3]);
}

// Look through the renderer object for a float3 that still holds the camera
// position from BEFORE our head pose was applied. Anything the lighting reads
// from such a copy is working with a camera that never moved.
static volatile LONG g_livePosOff = -1;
static bool g_frustumWatchOn = false;
static volatile LONG g_stalePosOff = -1;
static volatile LONG g_stalePosScanned = 0;
static bool g_fixStalePos = true;      // Q toggles, for A/B comparison
static volatile LONG g_stalePosFixes = 0;
static volatile LONG g_poseBeforeLightsHits = 0;

static void ScanForStaleCamPos(char* R, const float* wantStale, const float* wantLive) {
    if (InterlockedCompareExchange(&g_stalePosScanned, 1, 0)) return;
    float d = 0.0f;
    for (int i = 0; i < 3; ++i) { float e = wantStale[i]-wantLive[i]; d += e*e; }
    if (d < 0.0004f) {                      // need >2 cm of movement to tell them apart
        InterlockedExchange(&g_stalePosScanned, 0);
        static volatile LONG once = 0;
        if (!InterlockedExchange(&once, 1))
            Log("    (camera position scan waiting: the head pose has moved us"
                " only %.3f m so far; needs 0.02 m to distinguish the copies)",
                sqrtf(d));
        return;
    }
    int foundStale = 0, foundLive = 0;
    for (int off = 0; off + 12 <= 0x3000; off += 4) {
        const float* f = (const float*)(R + off);
        float ds = 0.0f, dl = 0.0f;
        for (int i = 0; i < 3; ++i) {
            float a = f[i]-wantStale[i]; ds += a*a;
            float b = f[i]-wantLive[i];  dl += b*b;
        }
        if (ds < 1e-6f) {
            Log("    renderer+0x%04x holds the PRE-pose camera position"
                " (%.3f %.3f %.3f)  <-- stale", off, f[0], f[1], f[2]);
            if (foundStale == 0) InterlockedExchange(&g_stalePosOff, off);
            ++foundStale;
        } else if (dl < 1e-6f) {
            Log("    renderer+0x%04x holds the LIVE camera position"
                " (%.3f %.3f %.3f)  -- tracks correctly", off, f[0], f[1], f[2]);
            // Remember it: the probe proved camera+0x10 is NOT the viewpoint
            // (a full metre there moved nothing), so this is where the head
            // displacement has to go instead.
            if (foundLive == 0) InterlockedExchange(&g_livePosOff, off);
            ++foundLive;
        }
    }
    Log(">>> CAMERA POSITION IN THE RENDERER: %d stale copies, %d live",
        foundStale, foundLive);
    if (foundStale == 0 && foundLive == 0)
        Log("    neither found -- the lighting does not keep the camera position"
            " in the first 12 KB of the renderer, so this is not the cause");
    Log("");
}

static bool g_poseBeforeLights = true;   // W toggles

static void d_LightSetup(void* renderer) {
    // Rotate BEFORE the lights are set up, so their view-space positions and
    // the pixel positions reconstructed later agree on where the camera is.
    if (g_poseBeforeLights && renderer && HeadPoseActive()) {
        void* fr = *(void**)((char*)renderer + 0x20);
        if (fr && FrustumIsMain(fr)) {
            float q[4], pos[3];
            if (CurrentHeadPose(q, pos) && ApplyHeadPose(fr, q, pos)) {
                InterlockedIncrement(&g_poseBeforeLightsHits);
            }
        }
    }
    o_LightSetup(renderer);            // let it build its cache as usual
    InterlockedIncrement(&g_lightSetupHits);
    if (!renderer) return;

    char* R = (char*)renderer;
    void* fr = *(void**)(R + 0x20);
    if (!fr) return;
    const float* V = (const float*)((char*)fr + kFrustumView);
    const float* C = (const float*)(R + 0x96c);

    float inv[16], tr[16];
    Mat4InverseRigid(V, inv);
    for (int r = 0; r < 4; ++r)
        for (int c = 0; c < 4; ++c) tr[r*4+c] = V[c*4+r];

    float dInv = 0.0f, dTr = 0.0f;
    for (int i = 0; i < 16; ++i) {
        float a = C[i] - inv[i]; if (a < 0) a = -a; if (a > dInv) dInv = a;
        float b = C[i] - tr[i];  if (b < 0) b = -b; if (b > dTr)  dTr  = b;
    }
    g_cacheIsInverse   = (dInv < 0.001f);
    g_cacheIsTranspose = (dTr  < 0.001f);
    g_cacheMatches     = g_cacheIsInverse || g_cacheIsTranspose;

    // Refresh the stale copy the scan found, so the lighting uses the camera
    // position we are actually rendering from.
    LONG off = InterlockedCompareExchange(&g_stalePosOff, -1, -1);
    if (g_fixStalePos && off >= 0) {
        float live[3];
        CamPosFromView(V, live);
        memcpy(R + off, live, sizeof(live));
        InterlockedIncrement(&g_stalePosFixes);
    }

    // Once the head pose has actually moved us, look for a stale position copy.
    if (InterlockedCompareExchange(&g_preRotValid, 0, 0)) {
        float live[3], stale[3];
        CamPosFromView(V, live);
        CamPosFromView(g_preRotView, stale);
        ScanForStaleCamPos(R, stale, live);
    }

    if (!InterlockedExchange(&g_lightSetupChecked, 1)) {
        Log("");
        Log(">>> LIGHT SETUP cache at renderer+0x96c, built from frustum+0x158:");
        Log("    matches inverse(view):   %s  (max diff %.6f)",
            g_cacheIsInverse ? "YES" : "no", dInv);
        Log("    matches transpose(view): %s  (max diff %.6f)",
            g_cacheIsTranspose ? "YES" : "no", dTr);
        if (!g_cacheMatches)
            Log("    matches NEITHER -- derived some other way, or from a view"
                " that differs from the one in the frustum right now");
        Log("");
    }
}

// ==========================================================================
// DOUBLE RENDER  (F9 = re-entrancy probe, F10 = side-by-side stereo)
// ==========================================================================
// Native stereo needs the scene drawn twice per frame. iRenderer::Render takes
// the frustum and render target as PARAMETERS, which is the shape that makes a
// second call plausible -- but whether HPL3 tolerates it is an empirical
// question, so this escalates in two steps rather than one leap.
//
//   F9  call Render twice with identical arguments. No eye flip, no viewport
//       split. Answers only: does the engine survive re-entrancy?
//   F10 adds the per-eye projection and splits the viewport left/right, giving
//       genuine side-by-side stereo on a flat monitor -- no headset needed.
//
// HPL2's equivalent is:
//   Render(float afFrameTime, cFrustum*, cWorld*, cRenderSettings*,
//          cRenderTarget*, bool abSendFrameBufferToPostEffects,
//          tRendererCallbackList*)
// HPL3 carries two extra arguments. Ghidra gives the shape; the float lands in
// XMM1 under the MS x64 ABI, which mingw also uses on Windows.
// 0x1FD540 is BeginRendering -- only the first line of the real thing. Ghidra
// on its caller gives:
//     FUN_1401ffbf0(this):
//         BeginRendering(...)          <- 0x1FD540, what I was doubling
//         (*vtable[0x80])(this)        <- RenderObjects, the actual drawing
//         (*vtable[0x88])(this)        <- second draw pass
//         EndRendering(this, 1)        <- 0x1FA1F0
// Doubling BeginRendering was nearly free and drew nothing, which is exactly
// what the logs showed: no framebuffer binds inside it, one image on screen.
// This is the whole sequence.
static const uintptr_t kRVA_Render = 0x1ffbf0;

// From the listing it reads four stack slots and supplies abAtStartOfRendering
// itself, so: this + 7 arguments. The float lands in XMM1 under the MS x64 ABI.
static const uintptr_t kRVA_Reflection = 0x3f8f50;

// No orthographic projections reached SetProjectionMatrix even with a terminal
// and the menu open, so the UI uses a different path. iLowLevelGraphics::SetMatrix
// is the one everything goes through -- from the first Ghidra dump:
//     FUN_14043da66(this, eMatrix type, const cMatrixf& mtx)
//         type 0 (ModelView)  -> this+0x14c
//         type 1 (Projection) -> this+0x18c
static const uintptr_t kRVA_SetMatrix = 0x43da66;
typedef void (*PFN_SetMatrix)(void* self, int type, const float* mtx);
static PFN_SetMatrix o_SetMatrix = nullptr;
static volatile LONG g_uiHookOn = 0;
static volatile LONG g_smCalls = 0, g_smProj = 0, g_smOrtho = 0, g_smPersp = 0;
// Also record the distinct perspective FOVs seen, in case the GUI draws with a
// perspective matrix rather than an orthographic one.
struct ProjSeen { float fov, aspect; long n; };
static ProjSeen g_smSeen[8];

typedef void (*PFN_Render)(void* self, float frameTime, void* frustum, void* world,
                           void* settings, void* target, unsigned char toPost,
                           void* callbacks);
static PFN_Render o_Render = nullptr;

static volatile LONG g_renderDepth = 0;
static volatile LONG g_splitActive = 0;
static volatile LONG g_dblCount = 0, g_nestedRenders = 0;
// Before optimising the halved framerate, find out where the time actually
// goes. If the second pass is already much cheaper than the first, shadow maps
// and culling are being reused and there is less to win than assumed.
static LONGLONG g_passTicks[2] = {0,0};
static LONGLONG g_frameTicks = 0, g_lastSwap = 0;
static LONG     g_timedFrames = 0;
// The CPU timing above measures COMMAND SUBMISSION, not drawing: o_Render
// returns once the calls are queued, and the GPU work surfaces later as a stall
// in SwapBuffers. With vsync on, the frame time just reads the refresh rate.
// GL timestamp queries measure the GPU directly. Results are read back a few
// frames late so nothing stalls the pipeline.
// mingw's gl.h predates GL 1.5, so these are not declared there.
#ifndef GL_VERSION_1_5
typedef unsigned long long GLuint64ARB_;
#endif
typedef unsigned long long GLuint64_;
#define GL_TIMESTAMP_       0x8E28
#define GL_QUERY_RESULT_    0x8866
#define GL_QUERY_RESULT_AVAILABLE_ 0x8867
typedef void (APIENTRY *PFN_GenQueries)(GLsizei, GLuint*);
typedef void (APIENTRY *PFN_QueryCounter)(GLuint, GLenum);
typedef void (APIENTRY *PFN_GetQueryObjectui64v)(GLuint, GLenum, GLuint64_*);
typedef void (APIENTRY *PFN_GetQueryObjectuiv)(GLuint, GLenum, GLuint*);
static PFN_GenQueries          p_GenQueries = nullptr;
static PFN_QueryCounter        p_QueryCounter = nullptr;
static PFN_GetQueryObjectui64v p_GetQueryObjectui64v = nullptr;
static PFN_GetQueryObjectuiv   p_GetQueryObjectuiv = nullptr;

static const int kQRing = 4;          // frames of latency before readback
static GLuint g_gpuBlit[4][2];        // around capture+composite
static bool   g_blitUsed[4] = {false,false,false,false};
static double g_gpuBlitMs = 0; static long g_gpuBlitSamples = 0;
static GLuint g_gpuQuery[kQRing][3];  // start, after pass0, after pass1
static bool   g_qUsed[kQRing] = {false,false,false,false};
static int    g_qSlot = 0;
static bool   g_qReady = false;
static double g_gpuPass0 = 0, g_gpuPass1 = 0; static long g_gpuSamples = 0;

static bool InitGpuQueries() {
    if (g_qReady) return true;
    HMODULE gl = GetModuleHandleA("opengl32.dll");
    if (!gl) return false;
    typedef PROC (WINAPI *PFN_GPA)(LPCSTR);
    PFN_GPA gpa = (PFN_GPA)GetProcAddress(gl, "wglGetProcAddress");
    if (!gpa) return false;
    p_GenQueries          = (PFN_GenQueries)(void*)gpa("glGenQueries");
    p_QueryCounter        = (PFN_QueryCounter)(void*)gpa("glQueryCounter");
    p_GetQueryObjectui64v = (PFN_GetQueryObjectui64v)(void*)gpa("glGetQueryObjectui64v");
    p_GetQueryObjectuiv   = (PFN_GetQueryObjectuiv)(void*)gpa("glGetQueryObjectuiv");
    if (!p_GenQueries || !p_QueryCounter || !p_GetQueryObjectui64v || !p_GetQueryObjectuiv) {
        Log("GPU timer queries unavailable; timing will be CPU-side only");
        return false;
    }
    for (int i = 0; i < kQRing; ++i) { p_GenQueries(3, g_gpuQuery[i]);
                                      p_GenQueries(2, g_gpuBlit[i]); }
    g_qReady = true;
    Log("GPU timer queries ready (%d-frame readback latency)", kQRing);
    return true;
}

static void GpuMark(int which) {           // 0 = start, 1 = after pass0, 2 = after pass1
    if (g_qReady) p_QueryCounter(g_gpuQuery[g_qSlot][which], GL_TIMESTAMP_);
}

static void GpuBlitMark(int which) {
    if (g_qReady) p_QueryCounter(g_gpuBlit[g_qSlot][which], GL_TIMESTAMP_);
}

static void GpuCollect() {
    if (!g_qReady) return;
    int old = (g_qSlot + 1) % kQRing;      // oldest slot, most likely complete
    if (g_blitUsed[old]) {
        GLuint avail = 0;
        p_GetQueryObjectuiv(g_gpuBlit[old][1], GL_QUERY_RESULT_AVAILABLE_, &avail);
        if (avail) {
            GLuint64_ b0=0,b1=0;
            p_GetQueryObjectui64v(g_gpuBlit[old][0], GL_QUERY_RESULT_, &b0);
            p_GetQueryObjectui64v(g_gpuBlit[old][1], GL_QUERY_RESULT_, &b1);
            g_gpuBlitMs += (double)(b1 - b0) * 1e-6;
            ++g_gpuBlitSamples;
            g_blitUsed[old] = false;
        }
    }
    g_blitUsed[g_qSlot] = true;
    if (g_qUsed[old]) {
        GLuint avail = 0;
        p_GetQueryObjectuiv(g_gpuQuery[old][2], GL_QUERY_RESULT_AVAILABLE_, &avail);
        if (avail) {
            GLuint64_ t0=0,t1=0,t2=0;
            p_GetQueryObjectui64v(g_gpuQuery[old][0], GL_QUERY_RESULT_, &t0);
            p_GetQueryObjectui64v(g_gpuQuery[old][1], GL_QUERY_RESULT_, &t1);
            p_GetQueryObjectui64v(g_gpuQuery[old][2], GL_QUERY_RESULT_, &t2);
            g_gpuPass0 += (double)(t1 - t0) * 1e-6;   // ns -> ms
            g_gpuPass1 += (double)(t2 - t1) * 1e-6;
            ++g_gpuSamples;
            g_qUsed[old] = false;
        }
    }
    g_qUsed[g_qSlot] = true;
    g_qSlot = (g_qSlot + 1) % kQRing;
}

// Only remap viewports that cover the whole backbuffer. Shadow maps and other
// offscreen passes use their own sizes and must be left alone.
typedef void (APIENTRY *PFN_Viewport)(GLint,GLint,GLsizei,GLsizei);
static PFN_Viewport o_Viewport = nullptr;

static void APIENTRY d_Viewport(GLint x, GLint y, GLsizei w, GLsizei h) {
    if (InterlockedCompareExchange(&g_splitActive, 0, 0)) NoteViewport((int)w, (int)h);
    if (InterlockedCompareExchange(&g_inEyePass, 0, 0)) {
        InterlockedExchange(&g_vpW, (LONG)w);
        InterlockedExchange(&g_vpH, (LONG)h);
    }
    // With a headset attached, each eye owns the whole target: the swapchain
    // gets a full-resolution eye image, not half a monitor.
    const bool toHeadset = InterlockedCompareExchange(&g_xrOn, 0, 0) && g_xr.Ready();
    if (!toHeadset &&
        InterlockedCompareExchange(&g_splitActive, 0, 0) &&
        g_fullW > 0 && w == g_fullW && h == g_fullH) {
        GLsizei half = (GLsizei)(g_fullW / 2);
        LONG eye = InterlockedCompareExchange(&g_eye, 0, 0);
        if (InterlockedCompareExchange(&g_swapHalves, 0, 0)) eye = 1 - eye;
        o_Viewport((GLint)(eye * half), y, half, h);
        return;
    }
    // Render into a region whose aspect MATCHES the projection, or the image is
    // stretched by (viewport aspect / projection aspect) -- 1.778/0.965 = 1.84x,
    // which is the "everything looks too big and 4:3" effect.
    // Only the full-target viewport, never shadow or reflection passes -- those
    // have their own sizes and reshaping them would break them.
    float pa = ProjAspect();
    const bool fullTarget = (g_fullW > 0 && w == g_fullW && h == g_fullH);
    if (g_fitViewport && fullTarget && pa > 0.01f && w > 0 && h > 0) {
        float va = (float)w / (float)h;
        if (fabsf(va - pa) > 0.01f * pa) {
            int nw = w, nh = h;
            if (va > pa) nw = (int)(h * pa + 0.5f);   // too wide: narrow it
            else         nh = (int)(w / pa + 0.5f);   // too tall: shorten it
            int nx = x + (w - nw) / 2, ny = y + (h - nh) / 2;
            InterlockedExchange(&g_vpFitW, nw);
            InterlockedExchange(&g_vpFitH, nh);
            InterlockedExchange(&g_vpFitX, nx);
            InterlockedExchange(&g_vpFitY, ny);
            if (!InterlockedExchange(&g_vpFitLogged, 1))
                Log("viewport fitted to the projection: %dx%d (aspect %.3f) inside"
                    " %dx%d (was %.3f) -- this is what made everything look"
                    " oversized and stretched", nw, nh, pa, w, h, va);
            o_Viewport(nx, ny, nw, nh);
            return;
        }
    }
    o_Viewport(x, y, w, h);
}

// ==========================================================================
// PER-EYE FRAMEBUFFER CAPTURE + COMPOSITE
// ==========================================================================
// The viewport split was the wrong mechanism twice over: HPL3 never calls
// glViewport during a render pass (measured -- the histogram came back empty),
// and half a screen is not what a headset wants anyway.
//
// This captures instead. After each eye's Render returns, blit whatever the
// engine just produced into that eye's own texture. Nothing needs to be known
// about cRenderTarget, and the same two textures serve both purposes: composite
// them side by side for monitor testing now, or blit them into the OpenXR
// swapchain images once a headset is present.
static GLuint  g_eyeTex[2] = {0,0}, g_eyeFbo[2] = {0,0};
static int     g_eyeW = 0, g_eyeH = 0;
static volatile LONG g_captured = 0;      // bit 0 = left ready, bit 1 = right
// Capturing from whatever was bound when Render returned read framebuffer 0,
// which still held LAST frame's composite -- so each frame split the previous
// split and collapsed to black. Track the last non-zero framebuffer the engine
// binds during a pass and read from that instead.
static volatile LONG g_lastPassFbo = 0;
static volatile LONG g_capLogged = 0;
// The hook recorded nothing during either pass, which cannot be right for a
// deferred renderer. SOMA uses GLEW, and GLEW-era code often calls the
// EXT_framebuffer_object entry points -- wglGetProcAddress returns a DIFFERENT
// address for glBindFramebufferEXT, so a hook on the core name never fires.
// Hook both, and count fires so "not hooked" is distinguishable from
// "hooked but the engine only ever binds 0".
static volatile LONG g_bindFires = 0, g_bindFiresExt = 0;
struct FboSeen { GLuint fb; long n; };
static FboSeen g_fboSeen[10];
static void NoteFbo(GLuint fb) {
    for (int i = 0; i < 10; ++i) {
        if (g_fboSeen[i].n && g_fboSeen[i].fb == fb) { g_fboSeen[i].n++; return; }
        if (!g_fboSeen[i].n) { g_fboSeen[i].fb = fb; g_fboSeen[i].n = 1; return; }
    }
}

typedef void (APIENTRY *PFN_GenFramebuffersT)(GLsizei, GLuint*);
typedef void (APIENTRY *PFN_BindFramebufferT)(GLenum, GLuint);
typedef void (APIENTRY *PFN_FramebufferTexture2DT)(GLenum, GLenum, GLenum, GLuint, GLint);
typedef void (APIENTRY *PFN_BlitFramebufferT)(GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLbitfield,GLenum);
typedef void (APIENTRY *PFN_DeleteFramebuffersT)(GLsizei, const GLuint*);
static PFN_GenFramebuffersT      p_GenFramebuffers = nullptr;
static PFN_BindFramebufferT      p_BindFramebuffer = nullptr;
static PFN_FramebufferTexture2DT p_FramebufferTexture2D = nullptr;
static PFN_BlitFramebufferT      p_BlitFramebuffer = nullptr;
static PFN_DeleteFramebuffersT   p_DeleteFramebuffers = nullptr;

#define GL_READ_FB_   0x8CA8
#define GL_DRAW_FB_   0x8CA9
#define GL_FB_        0x8D40
#define GL_COLOR_AT0_ 0x8CE0
#define GL_DRAW_FB_BINDING_ 0x8CA6

static PFN_BindFramebufferT o_BindFramebufferHook = nullptr;
static PFN_BindFramebufferT o_BindFramebufferExt  = nullptr;

static void RecordBind(GLenum target, GLuint fb) {
    if (!InterlockedCompareExchange(&g_inEyePass, 0, 0)) return;
    NoteFbo(fb);
    if (fb != 0 && (target == GL_FB_ || target == GL_DRAW_FB_))
        InterlockedExchange(&g_lastPassFbo, (LONG)fb);
}
static void APIENTRY d_BindFramebufferHook(GLenum target, GLuint fb) {
    InterlockedIncrement(&g_bindFires);
    RecordBind(target, fb);
    o_BindFramebufferHook(target, fb);
}
static void APIENTRY d_BindFramebufferExt(GLenum target, GLuint fb) {
    InterlockedIncrement(&g_bindFiresExt);
    RecordBind(target, fb);
    o_BindFramebufferExt(target, fb);
}

#define GL_COLOR_ATTACH0_       0x8CE0
#define GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE_ 0x8CD0
#define GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME_ 0x8CD1
typedef void (APIENTRY *PFN_GetFbAttachParamT)(GLenum,GLenum,GLenum,GLint*);
static PFN_GetFbAttachParamT p_GetFbAttachParam = nullptr;

static bool ResolveFboFns() {
    if (p_BlitFramebuffer) return true;
    HMODULE gl = GetModuleHandleA("opengl32.dll");
    if (!gl) return false;
    typedef PROC (WINAPI *PFN_GPA)(LPCSTR);
    PFN_GPA gpa = (PFN_GPA)GetProcAddress(gl, "wglGetProcAddress");
    if (!gpa) return false;
    p_GenFramebuffers      = (PFN_GenFramebuffersT)(void*)gpa("glGenFramebuffers");
    p_BindFramebuffer      = (PFN_BindFramebufferT)(void*)gpa("glBindFramebuffer");
    p_FramebufferTexture2D = (PFN_FramebufferTexture2DT)(void*)gpa("glFramebufferTexture2D");
    p_BlitFramebuffer      = (PFN_BlitFramebufferT)(void*)gpa("glBlitFramebuffer");
    p_DeleteFramebuffers   = (PFN_DeleteFramebuffersT)(void*)gpa("glDeleteFramebuffers");
    p_GetFbAttachParam     = (PFN_GetFbAttachParamT)(void*)gpa("glGetFramebufferAttachmentParameteriv");
    if (p_BindFramebuffer && !o_BindFramebufferHook) {
        if (MH_CreateHook((void*)p_BindFramebuffer, (void*)d_BindFramebufferHook,
                          (void**)&o_BindFramebufferHook) == MH_OK) {
            MH_EnableHook((void*)p_BindFramebuffer);
            Log("glBindFramebuffer (core) hooked");
        }
    }
    void* ext = (void*)gpa("glBindFramebufferEXT");
    if (ext && ext != (void*)p_BindFramebuffer && !o_BindFramebufferExt) {
        if (MH_CreateHook(ext, (void*)d_BindFramebufferExt,
                          (void**)&o_BindFramebufferExt) == MH_OK) {
            MH_EnableHook(ext);
            Log("glBindFramebufferEXT hooked at a DIFFERENT address (%p vs core %p)",
                ext, (void*)p_BindFramebuffer);
        }
    } else if (ext == (void*)p_BindFramebuffer) {
        Log("glBindFramebufferEXT shares the core address, one hook covers both");
    }
    return p_GenFramebuffers && p_BindFramebuffer && p_FramebufferTexture2D && p_BlitFramebuffer;
}

static void DestroyEyeTargets() {
    if (p_DeleteFramebuffers && g_eyeFbo[0]) p_DeleteFramebuffers(2, g_eyeFbo);
    if (g_eyeTex[0]) glDeleteTextures(2, g_eyeTex);
    g_eyeFbo[0]=g_eyeFbo[1]=g_eyeTex[0]=g_eyeTex[1]=0;
}

static bool EnsureEyeTargets(int w, int h) {
    if (w <= 0 || h <= 0) return false;
    if (g_eyeFbo[0] && g_eyeW == w && g_eyeH == h) return true;
    if (!ResolveFboFns()) return false;
    DestroyEyeTargets();

    glGenTextures(2, g_eyeTex);
    p_GenFramebuffers(2, g_eyeFbo);
    for (int i = 0; i < 2; ++i) {
        glBindTexture(GL_TEXTURE_2D, g_eyeTex[i]);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        p_BindFramebuffer(GL_FB_, g_eyeFbo[i]);
        p_FramebufferTexture2D(GL_FB_, GL_COLOR_AT0_, GL_TEXTURE_2D, g_eyeTex[i], 0);
    }
    p_BindFramebuffer(GL_FB_, 0);
    glBindTexture(GL_TEXTURE_2D, 0);
    g_eyeW = w; g_eyeH = h;
    Log("per-eye capture targets created: 2 x %dx%d%s", w, h,
        (g_xr.Ready() ? "  (matched to the headset swapchain)" : ""));
    return true;
}

// Copy whatever the engine just rendered into this eye's texture.
static void CaptureEye(int eye) {
    int capW = g_fullW, capH = g_fullH;
    if (g_xr.Ready() && g_xr.SwapchainSize(&capW, &capH)) { /* match the headset */ }
    if (!EnsureEyeTargets(capW, capH)) return;
    GLint prevDraw = 0;
    glGetIntegerv(GL_DRAW_FB_BINDING_, &prevDraw);

    // Prefer the last offscreen target the engine bound during this pass.
    // Reading framebuffer 0 is what caused the recursive split.
    GLuint src = (GLuint)InterlockedExchange(&g_lastPassFbo, 0);
    if (src == 0) src = (GLuint)prevDraw;

    if (InterlockedIncrement(&g_capLogged) <= 4)
        Log("  capture eye %d: reading FBO %u (binding at return was %d)%s",
            eye, src, prevDraw,
            src == 0 ? "  <-- framebuffer 0, recursive split likely" : "");

    p_BindFramebuffer(GL_READ_FB_, src);
    p_BindFramebuffer(GL_DRAW_FB_, g_eyeFbo[eye]);
    LONG forced = InterlockedCompareExchange(&g_captureFbo, 0, 0);
    if (forced) p_BindFramebuffer(GL_READ_FB_, (GLuint)forced);
    int srcX = 0, srcY = 0, srcW = g_fullW, srcH = g_fullH;
    if (g_fitViewport) {
        LONG fw = InterlockedCompareExchange(&g_vpFitW, 0, 0);
        LONG fh = InterlockedCompareExchange(&g_vpFitH, 0, 0);
        if (fw > 0 && fh > 0) {        // capture ONLY what we rendered into
            srcX = InterlockedCompareExchange(&g_vpFitX, 0, 0);
            srcY = InterlockedCompareExchange(&g_vpFitY, 0, 0);
            srcW = (int)fw; srcH = (int)fh;
        }
    }
    p_BlitFramebuffer(srcX, srcY, srcX + srcW, srcY + srcH,
                      0, 0, g_eyeW,  g_eyeH,       // scale into the eye target
                      GL_COLOR_BUFFER_BIT, GL_LINEAR);   // LINEAR: this now resizes
    if (!InterlockedExchange(&g_capRectLogged, 1))
        Log("  capture blit: source %dx%d at (%d,%d) -> eye target %dx%d",
            srcW, srcH, srcX, srcY, g_eyeW, g_eyeH);

    p_BindFramebuffer(GL_FB_, (GLuint)prevDraw);
    // Only mark the eye ready if it came from a real offscreen target. Marking
    // it after reading framebuffer 0 is what let the split compound.
    if (src != 0) InterlockedOr(&g_captured, 1 << eye);
}


// Draw both eyes into the back buffer, side by side, just before the game swaps.
// Monitor mirror while the headset has the eyes: show the left eye whole,
// letterboxed, rather than two mismatched halves.
static void CompositeMirror() {
    if (!ResolveFboFns() || !g_eyeFbo[0] || !p_BlitFramebuffer) return;
    if (InterlockedCompareExchange(&g_captured, 0, 0) != 3) return;
    float srcA = (float)g_eyeW / (float)g_eyeH;
    int dw = g_fullW, dh = (int)(g_fullW / srcA);
    if (dh > g_fullH) { dh = g_fullH; dw = (int)(g_fullH * srcA); }
    int dx = (g_fullW - dw) / 2, dy = (g_fullH - dh) / 2;
    p_BindFramebuffer(GL_DRAW_FB_, 0);
    glClearColor(0,0,0,1); glClear(GL_COLOR_BUFFER_BIT);
    p_BindFramebuffer(GL_READ_FB_, g_eyeFbo[0]);
    p_BlitFramebuffer(0, 0, g_eyeW, g_eyeH, dx, dy, dx+dw, dy+dh,
                      GL_COLOR_BUFFER_BIT, GL_LINEAR);
    p_BindFramebuffer(GL_FB_, 0);
}

static void CompositeSideBySide() {
    if (InterlockedCompareExchange(&g_captured, 0, 0) != 3) return;
    if (!p_BlitFramebuffer || !g_eyeFbo[0]) return;
    const int half = g_fullW / 2;
    const bool swap = InterlockedCompareExchange(&g_swapHalves, 0, 0) != 0;

    for (int e = 0; e < 2; ++e) {
        int slot = swap ? (1 - e) : e;
        p_BindFramebuffer(GL_READ_FB_, g_eyeFbo[e]);
        p_BindFramebuffer(GL_DRAW_FB_, 0);
        p_BlitFramebuffer(0, 0, g_eyeW, g_eyeH,
                          slot * half, 0, slot * half + half, g_fullH,
                          GL_COLOR_BUFFER_BIT, GL_LINEAR);
    }
    p_BindFramebuffer(GL_FB_, 0);
    // Deliberately NOT clearing g_captured: each eye refreshes on alternate
    // frames, so the other half must persist or it would flash black.
}

// ==========================================================================
// PHYSICS RECON  (F5)
// ==========================================================================
// SOMA's grab is a PID controller driving force toward a goal point:
//     mtxGoal   = camTransform * translate(grabOffset + (0,0,-depth)) * bodyRot
//     vError    = mtxGoal.translation - body.position
//     body->AddForce(pid.Output(vError) * massSum * forceMul)
// plus matching torque for orientation. The object is never welded to the
// camera; it chases a target through the solver, which is why it collides and
// has inertia -- and exactly what makes VR grabbing feel physical.
//
// Replace the camera transform with a controller pose and that becomes a hand.
//
// HPL accumulates into mvTotalForce, then a per-body callback issues
// NewtonBodyAddForce / NewtonBodyAddTorque. Newton is a separate DLL, so those
// are exported by name -- potentially hookable with no Ghidra at all. First
// find out what is actually exported.
// ==========================================================================
// LOGIC TIMER  (T = scan, Y = set rate)
// ==========================================================================
// HPL paces game logic and physics on a fixed-timestep timer:
//     mlLocalTimeAdd = 1000.0 / updatesPerSec;     // a DOUBLE, 16.6667 for 60
// Rendering runs free, so at 90 fps the 3:2 ratio against 60 Hz logic produces
// visible judder. That constant is distinctive enough to find in memory, and
// the physics rate we already count via AddForce verifies whether a change took.
static const double kLogicAdd60 = 1000.0 / 60.0;

// HPL2 stores 1000/rate as a double. SOMA returned zero hits for that, so scan
// the whole family of plausible encodings and rates at once: the result tells us
// both the format and the actual rate, instead of guessing one at a time.
struct TimerHit { void* addr; int rate; int kind; };   // kind 0=d ms,1=d s,2=f s,3=int
static TimerHit g_timerHits[64];
static int g_timerHitCount = 0;
static const int kRates[] = { 30, 50, 60, 72, 90, 100, 120, 144, 200 };
static const int kNRates = (int)(sizeof(kRates)/sizeof(kRates[0]));
static const char* kKindName[4] = { "double ms", "double s", "float s", "int rate" };

static void ScanLogicTimer() {
    g_timerHitCount = 0;
    long found[4][16] = {{0}};
    SYSTEM_INFO si; GetSystemInfo(&si);
    unsigned char* addr = (unsigned char*)si.lpMinimumApplicationAddress;
    unsigned char* end  = (unsigned char*)si.lpMaximumApplicationAddress;
    size_t scanned = 0;
    while (addr < end) {
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQuery(addr, &mbi, sizeof(mbi))) break;
        // Include image data and copy-on-write this time, not just private heap.
        bool writable = (mbi.Protect == PAGE_READWRITE) ||
                        (mbi.Protect == PAGE_WRITECOPY) ||
                        (mbi.Protect == PAGE_EXECUTE_READWRITE);
        if (mbi.State == MEM_COMMIT && writable && mbi.RegionSize < (256u<<20)) {
            unsigned char* p = (unsigned char*)mbi.BaseAddress;
            size_t n = mbi.RegionSize;
            scanned += n;
            for (size_t off = 0; off + 8 <= n; off += 4) {
                double dv = *(double*)(p + off);
                float  fv = *(float*)(p + off);
                int    iv = *(int*)(p + off);
                for (int r = 0; r < kNRates; ++r) {
                    int rate = kRates[r];
                    if (dv == 1000.0/rate)      { ++found[0][r]; if (g_timerHitCount<64) g_timerHits[g_timerHitCount++] = { p+off, rate, 0 }; }
                    else if (dv == 1.0/rate)    { ++found[1][r]; if (g_timerHitCount<64) g_timerHits[g_timerHitCount++] = { p+off, rate, 1 }; }
                    else if (fv == (float)(1.0/rate)) { ++found[2][r]; if (g_timerHitCount<64) g_timerHits[g_timerHitCount++] = { p+off, rate, 2 }; }
                    else if (iv == rate && rate >= 60) { ++found[3][r]; }
                }
            }
        }
        addr = (unsigned char*)mbi.BaseAddress + mbi.RegionSize;
    }
    Log(""); Log(">>> T: scanned %.0f MB", scanned/1048576.0);
    Log("    rate |  double ms |  double s  |  float s   |  int");
    for (int r = 0; r < kNRates; ++r) {
        if (!found[0][r] && !found[1][r] && !found[2][r] && !found[3][r]) continue;
        Log("    %4d | %10ld | %10ld | %10ld | %ld", kRates[r],
            found[0][r], found[1][r], found[2][r], found[3][r]);
    }
    Log("    recorded %d patchable candidates (int matches are too common to patch)",
        g_timerHitCount);
    for (int i = 0; i < g_timerHitCount && i < 12; ++i)
        Log("      [%d] %p  %s  rate %d", i, g_timerHits[i].addr,
            kKindName[g_timerHits[i].kind], g_timerHits[i].rate);
    if (g_timerHitCount == 0)
        Log("    nothing matched -- the step is computed rather than stored,"
            " or uses a rate not in the list");
}

static const int kMaxSafePatch = 4;

static void SetLogicRate(double hz) {
    if (g_timerHitCount == 0) { Log("  scan first (T)"); return; }
    if (g_timerHitCount > kMaxSafePatch) {
        Log(""); Log(">>> Y: REFUSING to patch %d candidates.", g_timerHitCount);
        Log("    1/60 as a float is a common round number -- the scan found"
            " hundreds of them across the process, and only one is the logic");
        Log("    timer. Rewriting them all would corrupt unrelated state for no"
            " reliable gain. This needs the timer located properly in Ghidra.");
        return;
    }
    int done = 0;
    for (int i = 0; i < g_timerHitCount; ++i) {
        DWORD old; void* a = g_timerHits[i].addr;
        size_t sz = (g_timerHits[i].kind == 2) ? 4 : 8;
        if (!VirtualProtect(a, sz, PAGE_READWRITE, &old)) continue;
        switch (g_timerHits[i].kind) {
            case 0: *(double*)a = 1000.0/hz; break;
            case 1: *(double*)a = 1.0/hz;    break;
            case 2: *(float*)a  = (float)(1.0/hz); break;
        }
        VirtualProtect(a, sz, old, &old);
        ++done;
    }
    Log(""); Log(">>> Y: rewrote %d candidate(s) for %.0f Hz", done, hz);
    Log("    watch 'physics ~N steps/sec' in the census: it should move from ~60");
    Log("    to ~%.0f if the right value was found. Revert by pressing T then Y again", hz);
    Log("    with the game restarted if anything misbehaves.");
}

static void DumpNewtonExports() {
    const char* names[] = { "newton.dll", "Newton.dll", "newton64.dll" };
    HMODULE nd = nullptr; const char* used = nullptr;
    for (const char* n : names) { nd = GetModuleHandleA(n); if (nd) { used = n; break; } }
    if (!nd) { Log(">>> F5: Newton DLL not loaded (tried newton.dll / Newton.dll)"); return; }

    Log(""); Log(">>> F5: %s loaded at %p", used, (void*)nd);
    BYTE* base = (BYTE*)nd;
    IMAGE_DOS_HEADER* dos = (IMAGE_DOS_HEADER*)base;
    IMAGE_NT_HEADERS* nt = (IMAGE_NT_HEADERS*)(base + dos->e_lfanew);
    DWORD rva = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT].VirtualAddress;
    if (!rva) { Log("    no export directory"); return; }
    IMAGE_EXPORT_DIRECTORY* ed = (IMAGE_EXPORT_DIRECTORY*)(base + rva);
    DWORD* nameRvas = (DWORD*)(base + ed->AddressOfNames);

    Log("    %lu exports; the ones that matter for grabbing:", ed->NumberOfNames);
    const char* wanted[] = { "AddForce", "AddTorque", "SetForce", "BodySetMatrix",
                             "BodyGetMatrix", "BodySetVelocity", "BodyGetPosition",
                             "SetForceAndTorqueCallback", "BodyGetMass" };
    int shown = 0;
    for (DWORD i = 0; i < ed->NumberOfNames; ++i) {
        const char* nm = (const char*)(base + nameRvas[i]);
        for (const char* w : wanted) {
            if (strstr(nm, w)) {
                void* fn = (void*)GetProcAddress(nd, nm);
                Log("      %-40s @ %p", nm, fn);
                ++shown; break;
            }
        }
    }
    if (!shown) Log("      none matched -- Newton may be statically linked into Soma.exe");
    Log("    Hooking NewtonBodyAddForce would let us see every force the grab");
    Log("    applies, and eventually retarget it from camera to controller.");
}

// Every dynamic body gets gravity plus its accumulated force each step, so
// AddForce is a hot path. The grabbed object is distinguishable: its force is
// PID-driven, so it is large and changes frame to frame, while a resting body
// sees a steady gravity-cancelling value. Track the busiest bodies and see
// which one spikes when something is picked up.
typedef void (*PFN_NewtonAddForce)(const void* body, const float* force);
typedef void (*PFN_NewtonGetMatrix)(const void* body, float* matrix);
typedef void (*PFN_NewtonGetMass)(const void* body, float* mass, float* Ix, float* Iy, float* Iz);
static PFN_NewtonAddForce  o_NewtonAddForce = nullptr;
static PFN_NewtonGetMatrix p_NewtonGetMatrix = nullptr;
static PFN_NewtonGetMass   p_NewtonGetMass = nullptr;
static volatile LONG g_physScan = 0, g_physCalls = 0;
// Distinct bodies touched between our census samples, used to convert AddForce
// call counts into an actual step rate.
static long g_physStepBodies = 0;
static const void* g_seenBodies[256];
static int g_seenBodyCount = 0;

// Gravity is purely vertical, so horizontal force is the giveaway: a resting
// body has none, a body being carried around has a lot. That is a far better
// discriminator than magnitude (a heavy crate outweighs a held can) or
// variation (which reads zero when the force is a steady gravity value).
static CRITICAL_SECTION g_physLock;
static volatile LONG g_horizPeak = 0;   // scaled x1000, for the census line

static const void* g_bestBody = nullptr;
static float g_bestHoriz = 0.0f, g_bestVert = 0.0f;
static float g_maxHorizAny = 0.0f;
static long  g_forcedBodies = 0;

static void NoteForce(const void* body, const float* f) {
    float horiz = sqrtf(f[0]*f[0] + f[2]*f[2]);
    if (horiz < 0.001f) return;                 // pure gravity, ignore
    EnterCriticalSection(&g_physLock);
    ++g_forcedBodies;
    if (horiz > g_maxHorizAny) g_maxHorizAny = horiz;
    if (horiz > g_bestHoriz) {
        g_bestHoriz = horiz; g_bestVert = fabsf(f[1]); g_bestBody = body;
    }
    LeaveCriticalSection(&g_physLock);
}

static void d_NewtonAddForce(const void* body, const float* f) {
    if (InterlockedCompareExchange(&g_physScan, 0, 0) && body && f) {
        InterlockedIncrement(&g_physCalls);
        if (g_seenBodyCount < 256) {
            bool known = false;
            for (int i = 0; i < g_seenBodyCount; ++i)
                if (g_seenBodies[i] == body) { known = true; break; }
            if (!known) g_seenBodies[g_seenBodyCount++] = body;
        }
        NoteForce(body, f);
    }

    // Take over the held object: replace the engine's camera-driven force with
    // our own toward a target point. Prove the mechanism with a synthetic hand
    // now; substitute controller coordinates when the hardware arrives.
    if (InterlockedCompareExchange(&g_handOn, 0, 0) && body && f &&
        p_NewtonGetMatrix && p_NewtonGetMass) {
        float horiz = sqrtf(f[0]*f[0] + f[2]*f[2]);

        // The force-based latch lived here and was a mass filter: the grab force
        // is pid*massSum, so 150 N only ever caught objects above ~2 kg. It now
        // just records this frame's most horizontally-driven body, and
        // DriveHeldBody latches by DURATION instead -- mass-independent.
        if (horiz > kMinHoriz) NoteCandidate(body, horiz);
        // Just record that the held body is still being driven; the release
        // decision is made once per frame, and uses the same small threshold as
        // the latch so it is not a mass filter.
        if (body == g_heldBody && horiz > kMinHoriz)
            InterlockedExchange(&g_heldSawForce, 1);

        if (body == g_heldBody) {
            // Cancel the engine's grab, but keep the object's weight: zeroing
            // every force including gravity is what made heavy things float.
            InterlockedIncrement(&g_handForces);
            float mass=0, ix=0, iy=0, iz=0;
            if (p_NewtonGetMass) p_NewtonGetMass(body, &mass, &ix, &iy, &iz);
            alignas(16) float grav[4] = { 0.0f, -9.81f * mass, 0.0f, 0.0f };
            o_NewtonAddForce(body, grav);
            return;
        }
        if (false) {
            float m[16]; p_NewtonGetMatrix(body, m);
            float px = m[12], py = m[13], pz = m[14];
            float mass=0, ix=0, iy=0, iz=0; p_NewtonGetMass(body, &mass, &ix, &iy, &iz);
            if (mass < 0.001f) mass = 1.0f;

            // Synthetic hand: a point orbiting in front of the player.
            float t = (float)InterlockedCompareExchange(&g_frame, 0, 0) * 0.05f;
            float tx = g_camWorld[0] + 0.9f * sinf(t);
            float ty = g_camWorld[1] + 0.35f * sinf(t * 1.7f);
            float tz = g_camWorld[2] + 0.9f * cosf(t);

            float vx=0, vy=0, vz=0;
            if (g_heldHavePos) {                       // velocity from position delta
                vx = (px - g_heldLastPos[0]) * 60.0f;
                vy = (py - g_heldLastPos[1]) * 60.0f;
                vz = (pz - g_heldLastPos[2]) * 60.0f;
            }
            g_heldLastPos[0]=px; g_heldLastPos[1]=py; g_heldLastPos[2]=pz;
            g_heldHavePos = true;

            // Spring-damper toward the target, plus gravity cancellation.
            const float kp = 60.0f, kd = 12.0f;
            float nf[3] = {
                (kp*(tx-px) - kd*vx) * mass,
                (kp*(ty-py) - kd*vy) * mass + 9.81f*mass,
                (kp*(tz-pz) - kd*vz) * mass
            };
            // Desired velocity toward the target, for the SetVelocity override.
            const float kApproach = 4.0f, kMaxSpeed = 6.0f;
            float dvx = (tx-px)*kApproach, dvy = (ty-py)*kApproach, dvz = (tz-pz)*kApproach;
            float dsp = sqrtf(dvx*dvx+dvy*dvy+dvz*dvz);
            if (dsp > kMaxSpeed) { float k = kMaxSpeed/dsp; dvx*=k; dvy*=k; dvz*=k; }
            g_handWantVel[0]=dvx; g_handWantVel[1]=dvy; g_handWantVel[2]=dvz;

            float mag = sqrtf(nf[0]*nf[0]+nf[1]*nf[1]+nf[2]*nf[2]);
            const float maxF = 300.0f;               // the engine's own clamp
            if (mag > maxF) { float k = maxF/mag; nf[0]*=k; nf[1]*=k; nf[2]*=k; }

            InterlockedIncrement(&g_handForces);
            o_NewtonAddForce(body, nf);
            return;                                   // ours replaces theirs
        }
    }
    o_NewtonAddForce(body, f);
}

// The grab force may arrive through SetForce rather than AddForce: HPL likely
// composes gravity + accumulated force and sets it once per step.
static PFN_NewtonAddForce o_NewtonSetForce = nullptr;
static volatile LONG g_setForceCalls = 0;
static void d_NewtonSetForce(const void* body, const float* f) {
    if (InterlockedCompareExchange(&g_physScan, 0, 0) && body && f) {
        InterlockedIncrement(&g_setForceCalls);
        NoteForce(body, f);
    }
    o_NewtonSetForce(body, f);
}

typedef void (*PFN_NewtonSetVel)(const void* body, const float* vel);
typedef void (*PFN_NewtonSetMtx)(const void* body, const float* mtx);
static PFN_NewtonSetVel o_NewtonSetVel = nullptr;
typedef void (*PFN_NewtonGetVel)(const void* body, float* vel);
typedef void (*PFN_NewtonGetAABB)(const void* body, float* p0, float* p1);
static PFN_NewtonGetAABB p_NewtonGetAABB = nullptr;
typedef int  (*PFN_NewtonGetSleep)(const void* body);
static PFN_NewtonGetVel   p_NewtonGetVel = nullptr;
static PFN_NewtonGetSleep p_NewtonGetSleep = nullptr;
// Commanded vs actual, averaged over a census window.
static double g_cmdSpeedSum = 0, g_actSpeedSum = 0; static long g_velSamples = 0;
static long g_sleepSamples = 0, g_asleepCount = 0;
static long g_posMoved = 0, g_posChecks = 0;
static float g_lastBodyPos[3] = {0,0,0};
static PFN_NewtonSetMtx o_NewtonSetMtx = nullptr;

static void d_NewtonSetVelocity(const void* body, const float* v) {
    if (InterlockedCompareExchange(&g_physScan, 0, 0)) {
        InterlockedIncrement(&g_velCalls);
        if (body == g_heldBody && g_heldBody) {
            InterlockedIncrement(&g_velOnHeld);
            g_lastVelSet[0]=v[0]; g_lastVelSet[1]=v[1]; g_lastVelSet[2]=v[2];
        }
    }
    // SOMA clamps the held object's speed (the repeated 2.00 values), which no
    // force can beat. Substitute the velocity we want instead of fighting it.
    if (InterlockedCompareExchange(&g_handOn, 0, 0) && body && body == g_heldBody) {
        InterlockedIncrement(&g_velSubbed);
        o_NewtonSetVel(body, g_handWantVel);
        return;
    }
    o_NewtonSetVel(body, v);
}

static void d_NewtonSetMatrix(const void* body, const float* m) {
    if (InterlockedCompareExchange(&g_physScan, 0, 0)) {
        InterlockedIncrement(&g_mtxCalls);
        if (body == g_heldBody && g_heldBody) InterlockedIncrement(&g_mtxOnHeld);
    }
    o_NewtonSetMtx(body, m);
}

// Waiting for the engine to call SetVelocity gave control only when its clamp
// happened to fire -- roughly 3% of frames. Drive the body ourselves instead,
// once per frame, and suppress the engine's grab force entirely. Intermittent
// control was what made heavy objects feel weightless and light ones go wild.
static void GetHandPose(int hand, float* outPos);   // defined with the hand renderer

static void DriveHeldBody() {
    if (!InterlockedCompareExchange(&g_handOn, 0, 0)) return;
    if (!o_NewtonSetVel || !p_NewtonGetMatrix) return;

    // Latch by DURATION, not force. Mass-independent, so a cup qualifies as
    // readily as a chair.
    // Advance every candidate independently: seen this frame counts up, unseen
    // decays. No competition, so mass and neighbours are irrelevant.
    // Accumulate in SECONDS. The physics steps at a fixed wall-clock rate while
    // this runs per frame, so counting frames made latching impossible above 60 fps.
    static double lastCandTick = 0.0;
    double nowS = NowSeconds();
    double candDt = (lastCandTick > 0.0) ? (nowS - lastCandTick) : 0.0;
    if (candDt > 0.25) candDt = 0.25;       // ignore hitches
    lastCandTick = nowS;

    if (!g_heldBody) {
        int best = -1;
        for (int i = 0; i < 16; ++i) {
            if (!g_cand[i].body) continue;
            if (g_cand[i].seen) {
                // Credit the real interval since this body was last seen, so the
                // total is elapsed time regardless of how many frames passed.
                if (g_cand[i].lastSeen > 0.0) {
                    double gap = nowS - g_cand[i].lastSeen;
                    if (gap > kStaleSeconds) gap = kStaleSeconds;
                    g_cand[i].held += gap;
                }
                g_cand[i].lastSeen = nowS;
                if (g_cand[i].held >= kHoldSeconds &&
                    (best < 0 || g_cand[i].held > g_cand[best].held)) best = i;
            } else if (g_cand[i].lastSeen > 0.0 &&
                       nowS - g_cand[i].lastSeen > kStaleSeconds) {
                g_cand[i].body = nullptr; g_cand[i].held = 0.0;
                g_cand[i].lastSeen = 0.0; g_cand[i].horiz = 0;
            }
            g_cand[i].seen = false;
        }
        if (best >= 0) {
            g_heldBody = g_cand[best].body;
            g_heldQuiet = 0.0;
            InterlockedExchange(&g_heldSawForce, 1);
            float mass=0,ix=0,iy=0,iz=0;
            if (p_NewtonGetMass) p_NewtonGetMass(g_heldBody, &mass, &ix, &iy, &iz);
            Log("  hand latched onto body %p (%.2f kg, %.0f N sustained %.2f s)",
                g_heldBody, mass, g_cand[best].horiz, g_cand[best].held);
            for (int i = 0; i < 16; ++i) { g_cand[i].body = nullptr; g_cand[i].held = 0.0;
                                          g_cand[i].lastSeen = 0.0;
                                          g_cand[i].horiz = 0; g_cand[i].seen = false; }
        }
    } else {
        for (int i = 0; i < 16; ++i) g_cand[i].seen = false;
    }

    // Release once per FRAME, on whether the engine is still driving it at all.
    if (g_heldBody) {
        // Timestamp, not a per-frame counter: at 540 fps most frames contain no
        // physics step, so counting "quiet frames" released objects still held.
        if (InterlockedExchange(&g_heldSawForce, 0)) g_heldQuiet = nowS;
        else if (g_heldQuiet > 0.0 && nowS - g_heldQuiet > kQuietSeconds) {
            Log("  hand released body %p (no force for %.1f s)",
                g_heldBody, kQuietSeconds);
            g_heldBody = nullptr; g_heldQuiet = 0.0;
        }
    }

    if (!g_heldBody) return;

    float m[16]; p_NewtonGetMatrix(g_heldBody, m);
    float px = m[12], py = m[13], pz = m[14];

    // Refuse to drive anything if the camera position is unknown, rather than
    // silently orbiting the world origin.
    if (fabsf(g_camWorld[0]) < 1e-6f && fabsf(g_camWorld[1]) < 1e-6f &&
        fabsf(g_camWorld[2]) < 1e-6f) {
        static LONG warned = 0;
        if (!InterlockedExchange(&warned, 1))
            Log("  hand INERT: camera position unknown. The projection hook must be"
                " running -- press F2, or reinject.");
        return;
    }

    // Grab toward a point just OUT from the palm, where a held object actually
    // rests. Driving it to the palm origin buried it in the hand, so every
    // fingertip started inside its sphere and contact fired at the first step.
    float hp[3]; GetHandPose(1, hp);
    float tx = hp[0], ty = hp[1], tz = hp[2];
    if (InterlockedCompareExchange(&g_gripCentreValid, 0, 0)) {
        tx = g_gripCentre[0]; ty = g_gripCentre[1]; tz = g_gripCentre[2];
    }

    // Hand velocity from REAL elapsed time -- with the refresh setting fixed the
    // frame rate is no longer 60, so a hardcoded step would be wrong.
    LONGLONG now = Now();
    float dt = 1.0f/60.0f;
    if (g_prevHandTick && g_qpcFreq)
        dt = (float)((double)(now - g_prevHandTick) / (double)g_qpcFreq);
    if (dt < 1e-4f) dt = 1e-4f;
    if (dt > 0.1f)  dt = 0.1f;          // ignore hitches and loading pauses
    float hvx = 0, hvy = 0, hvz = 0;
    if (g_prevHandValid) {
        hvx = (tx - g_prevHand[0]) / dt;
        hvy = (ty - g_prevHand[1]) / dt;
        hvz = (tz - g_prevHand[2]) / dt;
    }
    g_prevHand[0]=tx; g_prevHand[1]=ty; g_prevHand[2]=tz;
    g_prevHandTick = now; g_prevHandValid = true;
    g_handSpeed = sqrtf(hvx*hvx + hvy*hvy + hvz*hvz);

    // Feed-forward carries the object with the hand; the error term only closes
    // the residual gap. Position error alone always trails a moving target.
    const float kApproach = 8.0f, kMaxSpeed = 20.0f;
    float vx = (tx - px) * kApproach + hvx;
    float vy = (ty - py) * kApproach + hvy;
    float vz = (tz - pz) * kApproach + hvz;
    float sp = sqrtf(vx*vx + vy*vy + vz*vz);
    if (sp > kMaxSpeed) { float k = kMaxSpeed/sp; vx*=k; vy*=k; vz*=k; }

    alignas(16) float vel[4] = { vx, vy, vz, 0.0f };
    o_NewtonSetVel(g_heldBody, vel);
    InterlockedIncrement(&g_velSubbed);

    // Did the body actually take the velocity we gave it?
    if (p_NewtonGetVel) {
        alignas(16) float got[4] = {0,0,0,0};
        p_NewtonGetVel(g_heldBody, got);
        g_cmdSpeedSum += sqrtf(vx*vx + vy*vy + vz*vz);
        g_actSpeedSum += sqrtf(got[0]*got[0] + got[1]*got[1] + got[2]*got[2]);
        ++g_velSamples;
    }
    if (p_NewtonGetSleep) {
        ++g_sleepSamples;
        if (p_NewtonGetSleep(g_heldBody)) ++g_asleepCount;
    }
    // And is it moving at all between our sets?
    ++g_posChecks;
    float d = fabsf(px-g_lastBodyPos[0]) + fabsf(py-g_lastBodyPos[1])
            + fabsf(pz-g_lastBodyPos[2]);
    if (d > 1e-5f) ++g_posMoved;
    g_lastBodyPos[0]=px; g_lastBodyPos[1]=py; g_lastBodyPos[2]=pz;

    // Track whether our control is achieving anything: if the distance to the
    // target does not shrink, the velocity is not taking effect.
    float dx = tx-px, dy = ty-py, dz = tz-pz;
    g_handDist = sqrtf(dx*dx + dy*dy + dz*dz);
    if (g_handDistMin > g_handDist) g_handDistMin = g_handDist;
    if (g_handDistMax < g_handDist) g_handDistMax = g_handDist;
}

static bool InstallPhysicsHook() {
    if (o_NewtonAddForce) return true;
    const char* names[] = { "newton.dll", "Newton.dll", "newton64.dll" };
    HMODULE nd = nullptr;
    for (const char* n : names) { nd = GetModuleHandleA(n); if (nd) break; }
    if (!nd) { Log("Newton DLL not loaded"); return false; }
    void* addF = (void*)GetProcAddress(nd, "NewtonBodyAddForce");
    p_NewtonGetMatrix = (PFN_NewtonGetMatrix)GetProcAddress(nd, "NewtonBodyGetMatrix");
    p_NewtonGetMass   = (PFN_NewtonGetMass)GetProcAddress(nd, "NewtonBodyGetMassMatrix");
    if (!addF) { Log("NewtonBodyAddForce not found"); return false; }
    if (MH_CreateHook(addF, (void*)d_NewtonAddForce, (void**)&o_NewtonAddForce) != MH_OK ||
        MH_EnableHook(addF) != MH_OK) {
        Log("FAILED to hook NewtonBodyAddForce"); o_NewtonAddForce = nullptr; return false;
    }
    Log("NewtonBodyAddForce hooked at %p", addF);
    void* setF = (void*)GetProcAddress(nd, "NewtonBodySetForce");
    if (setF && MH_CreateHook(setF, (void*)d_NewtonSetForce, (void**)&o_NewtonSetForce) == MH_OK) {
        MH_EnableHook(setF);
        Log("NewtonBodySetForce hooked at %p (the grab may use this instead)", setF);
    }
    p_NewtonGetAABB  = (PFN_NewtonGetAABB)GetProcAddress(nd, "NewtonBodyGetAABB");
    Log("  GetAABB %s (needed for fingers to stop at the object's surface)",
        p_NewtonGetAABB ? "available" : "MISSING");
    p_NewtonGetVel   = (PFN_NewtonGetVel)GetProcAddress(nd, "NewtonBodyGetVelocity");
    p_NewtonGetSleep = (PFN_NewtonGetSleep)GetProcAddress(nd, "NewtonBodyGetSleepState");
    Log("  GetVelocity %s, GetSleepState %s",
        p_NewtonGetVel ? "available" : "MISSING",
        p_NewtonGetSleep ? "available" : "MISSING");
    void* setV = (void*)GetProcAddress(nd, "NewtonBodySetVelocity");
    if (setV && MH_CreateHook(setV, (void*)d_NewtonSetVelocity, (void**)&o_NewtonSetVel) == MH_OK)
        { MH_EnableHook(setV); Log("NewtonBodySetVelocity hooked at %p", setV); }
    void* setM = (void*)GetProcAddress(nd, "NewtonBodySetMatrix");
    if (setM && MH_CreateHook(setM, (void*)d_NewtonSetMatrix, (void**)&o_NewtonSetMtx) == MH_OK)
        { MH_EnableHook(setM); Log("NewtonBodySetMatrix hooked at %p", setM); }
    Log("  GetMatrix %s, GetMassMatrix %s",
        p_NewtonGetMatrix ? "available" : "MISSING",
        p_NewtonGetMass ? "available" : "MISSING");
    return true;
}

static void d_SetMatrix(void* self, int type, const float* mtx) {
    if (InterlockedCompareExchange(&g_uiHookOn, 0, 0)) {
        InterlockedIncrement(&g_smCalls);
        if (mtx && type == 1) {
            InterlockedIncrement(&g_smProj);
            float m[16]; memcpy(m, mtx, sizeof(m));
            bool orthoCM = fabsf(m[11]) < 1e-5f && fabsf(m[15]-1.0f) < 1e-3f;
            bool orthoRM = fabsf(m[14]) < 1e-5f && fabsf(m[15]-1.0f) < 1e-3f;
            if (orthoCM || orthoRM) {
                InterlockedIncrement(&g_smOrtho);
                NoteOrtho(m, orthoRM ? 2 : 1);
            } else {
                InterlockedIncrement(&g_smPersp);
                int lay = hpl3vr::ClassifyProjection(m);
                if (lay) {
                    if (lay == 2) hpl3vr::TransposeInPlace(m);
                    hpl3vr::ProjParams pp = hpl3vr::DecodeProjectionColMajor(m);
                    EnterCriticalSection(&g_orthoLock);
                    for (int i = 0; i < 8; ++i) {
                        if (g_smSeen[i].n) {
                            if (fabsf(g_smSeen[i].fov - pp.fFovYDeg) < 0.5f) { g_smSeen[i].n++; break; }
                        } else { g_smSeen[i].fov=pp.fFovYDeg; g_smSeen[i].aspect=pp.fAspect;
                                 g_smSeen[i].n=1; break; }
                    }
                    LeaveCriticalSection(&g_orthoLock);
                }
            }
        }
    }
    o_SetMatrix(self, type, mtx);
}

static bool InstallUiHook() {
    if (o_SetMatrix) return true;
    HMODULE exe = GetModuleHandleA(nullptr);
    if (!exe) return false;
    void* addr = (void*)((uintptr_t)exe + kRVA_SetMatrix);
    if (MH_CreateHook(addr, (void*)d_SetMatrix, (void**)&o_SetMatrix) != MH_OK ||
        MH_EnableHook(addr) != MH_OK) {
        Log("FAILED to hook iLowLevelGraphics::SetMatrix at 0x%p", addr);
        o_SetMatrix = nullptr; return false;
    }
    Log("iLowLevelGraphics::SetMatrix hooked at 0x%p (RVA 0x%llX)", addr,
        (unsigned long long)kRVA_SetMatrix);
    Log("  every matrix passes through here, including the UI's");
    return true;
}

static void DrawHands();   // defined below, near the GL helpers

static void d_Render(void* self, float frameTime, void* frustum, void* world,
                     void* settings, void* target, unsigned char toPost,
                     void* callbacks) {
    // Only split at the top level. HPL3 may render nested views (reflections,
    // cubemaps); doubling those would multiply, not stereo-ise.
    // FUN_1403F8F50, the reflection pass, calls this same function. Doubling a
    // reflection would be wrong, and the depth guard covers it as long as the
    // reflection renders inside the main pass.
    LONG depth = InterlockedIncrement(&g_renderDepth);
    bool top = (depth == 1);
    if (depth > 1) InterlockedIncrement(&g_nestedRenders);
    bool dbl = top && InterlockedCompareExchange(&g_doubleOn, 0, 0);
    bool sbs = top && InterlockedCompareExchange(&g_sbsOn, 0, 0);

    // Acquire the OpenXR frame HERE, before any camera matrix is built.
    // BeginFrame runs xrWaitFrame/xrBeginFrame/xrLocateViews, and it used to be
    // called from the swap hook -- AFTER both eye passes. So frame N was drawn
    // from the pose located at the end of frame N-1, and xrWaitFrame's display
    // prediction described the wrong frame too. That is a full frame of pose
    // lag, which reads as the world sliding when the head turns.
    if (top && InterlockedCompareExchange(&g_xrOn, 0, 0) &&
        !InterlockedCompareExchange(&g_xrFrameBegun, 0, 0)) {
        if (g_xr.BeginFrame()) {
            InterlockedExchange(&g_xrFrameBegun, 1);
            // Force a fresh latch: both eyes must use this frame's pose.
            InterlockedExchange(&g_latchedFrame, -1);
            InterlockedExchange(&g_latchValid, 0);
        }
    }

    if (!dbl && !sbs) {
        LONGLONG t0 = Now();
        o_Render(self, frameTime, frustum, world, settings, target, toPost, callbacks);
        if (top) { g_passTicks[0] += Now() - t0; DrawHands(); }
        InterlockedDecrement(&g_renderDepth);
        return;
    }

    // Capture the engine's own view BEFORE either pass touches it. Without
    // this, RestoreView had nothing to restore -- g_pristineValid stayed 0 and
    // the whole snapshot/restore fix was dead code.
    if (HeadPoseActive()) {
        DumpForward("before snapshot", frustum);
        SnapshotView(frustum);
    }

    // g_inEyePass brackets each pass. Without it the eye flag stayed at 1 after
    // the second Render returned, so post-processing, UI and the next frame's
    // shadow passes all counted as "right eye" -- which is why the census read
    // 600 left against 3015 right instead of an even split.
    const bool alt = InterlockedCompareExchange(&g_altEyes, 0, 0) != 0;
    const int  eyeLo = alt ? (int)(InterlockedCompareExchange(&g_frame,0,0) & 1) : 0;
    const int  eyeHi = alt ? eyeLo : 1;
    for (int eye = eyeLo; eye <= eyeHi; ++eye) {
        InterlockedExchange(&g_eye, eye);
        // 6DOF at the RENDERER's camera position. camera+0x10 was measured not
        // to be the viewpoint; this offset is the one the scan found tracking
        // correctly, and it is what the lighting reads too.
        LONG lpo = InterlockedCompareExchange(&g_livePosOff, 0, 0);
        float* rp = nullptr; float rp0[3] = {0,0,0};
        // DISABLED: renderer+0xbd4 was measured not to be the viewpoint -- a
        // full metre there produced no movement. Kept only for reference.
        if (false && lpo > 0 && g_headTranslation
            && InterlockedCompareExchange(&g_xrOriginSet,0,0)) {
            rp = (float*)((char*)self + lpo);
            rp0[0]=rp[0]; rp0[1]=rp[1]; rp0[2]=rp[2];
            rp[0] += g_dbgHead[0]; rp[1] += g_dbgHead[1]; rp[2] += g_dbgHead[2];
        }
        // FORCE A VIEW REBUILD FOR THIS EYE.
        //
        // Measured: the camera hook only ever ran with g_eye == 0 -- eye 1 got
        // ZERO hits -- so the left eye's offset was applied to both images,
        // which is the uniform sideways slide rather than stereo.
        //
        // FUN_140277630 clears its own dirty flag at +0x709 on the way out, and
        // our hook restores the camera's angles and position afterwards. By the
        // second pass the view matrix looks clean, so the engine never calls
        // UpdateViewMatrix again and the second eye inherits the first eye's
        // camera. Setting the flags here makes each pass rebuild with its own
        // g_eye. +0x709 = view dirty, +0x70A/+0x70C = view/frustum dirty.
        if (void* C = g_cameraObj) {
            *(volatile unsigned char*)((char*)C + 0x709) = 1;
            *(volatile unsigned char*)((char*)C + 0x70A) = 1;
            *(volatile unsigned char*)((char*)C + 0x70C) = 1;
            InterlockedIncrement(&g_forcedRebuilds);
        }
        InterlockedExchange(&g_lastPassFbo, 0);
        InterlockedExchange(&g_viewRotDone, 0);   // one view rotation per pass
        if (HeadPoseActive()) {
            RestoreView();
            DumpForward(eye == 0 ? "pass0 after restore" : "pass1 after restore", frustum);
        }
        // Rotate the frustum BEFORE the engine renders. SetProjectionMatrix
        // runs partway through Render, which is after visibility has been
        // decided -- doing it here gives culling and lighting a chance to
        // follow the head instead of the mouse.
        // Remember which frustum this eye pass uses, so the projection hook can
        // tell it apart from the shadow frusta rendered inside the same call.
        InterlockedExchangePointer((void* volatile*)&g_eyeFrustum, frustum);
        RotateFrustumEarly(frustum);

        InterlockedExchange(&g_inEyePass, 1);
        if (eye == 0) { InitGpuQueries(); GpuMark(0); }
        LONGLONG t0 = Now();
        o_Render(self, frameTime, frustum, world, settings, target, toPost, callbacks);
        g_passTicks[eye] += Now() - t0;
        // Put the renderer's camera position back so the engine's own logic is
        // not left displaced between frames.
        if (rp) { rp[0]=rp0[0]; rp[1]=rp0[1]; rp[2]=rp0[2]; }
        DrawHands();                     // inside the pass: depth is valid here
        GpuMark(eye == 0 ? 1 : 2);
        InterlockedExchange(&g_inEyePass, 0);
        if (sbs && !InterlockedCompareExchange(&g_altEyes, 0, 0))
            CaptureEye(eye);   // raw scene; alternating mode grabs FBO 0 at swap
    }
    if (HeadPoseActive()) {
        RestoreView();                       // hand the engine back what it had
        InterlockedExchange(&g_pristineValid, 0);
        g_pristineFrustum = nullptr;
    }
    InterlockedExchange(&g_eye, 0);
    InterlockedIncrement(&g_dblCount);
    InterlockedDecrement(&g_renderDepth);
}

static bool InstallRenderHook() {
    if (o_Render) return true;
    HMODULE exe = GetModuleHandleA(nullptr);
    if (!exe) return false;
    void* addr = (void*)((uintptr_t)exe + kRVA_Render);
    if (MH_CreateHook(addr, (void*)d_Render, (void**)&o_Render) != MH_OK ||
        MH_EnableHook(addr) != MH_OK) {
        Log("FAILED to hook iRenderer::Render at 0x%p", addr);
        o_Render = nullptr; return false;
    }
    Log("iRenderer::Render hooked at 0x%p (RVA 0x%llX)", addr,
        (unsigned long long)kRVA_Render);
    Log("  this is the Begin/RenderObjects/End sequence, not just Begin");

    HMODULE gl = GetModuleHandleA("opengl32.dll");
    void* vp = gl ? (void*)GetProcAddress(gl, "glViewport") : nullptr;
    if (vp && MH_CreateHook(vp, (void*)d_Viewport, (void**)&o_Viewport) == MH_OK)
        { MH_EnableHook(vp); Log("glViewport hooked (for the side-by-side split)"); }
    else Log("WARNING: glViewport not hooked, F10 cannot split the screen");
    return true;
}



// ------------------------------------------------------------ frame + keys
typedef BOOL (WINAPI *PFN_wglSwapBuffers)(HDC);
static PFN_wglSwapBuffers o_Swap = nullptr;
typedef void (APIENTRY *PFN_BindFramebuffer)(GLenum, unsigned);
static PFN_BindFramebuffer g_BindFBO = nullptr;


// ==========================================================================
// HAND MARKER RENDERING  (F4)
// ==========================================================================
// SOMA runs a GL 4.6 core profile, so no immediate mode: this needs a shader,
// a VAO and a VBO of its own. Unlit and drawn last for now -- the point is to
// establish that geometry can be placed at a world position and tracks the
// camera. Lighting and correct occlusion come after.
typedef GLuint (APIENTRY *PFN_CreateShader)(GLenum);
typedef void (APIENTRY *PFN_ShaderSource)(GLuint,GLsizei,const char* const*,const GLint*);
typedef void (APIENTRY *PFN_CompileShader)(GLuint);
typedef GLuint (APIENTRY *PFN_CreateProgram)(void);
typedef void (APIENTRY *PFN_AttachShader)(GLuint,GLuint);
typedef void (APIENTRY *PFN_LinkProgram)(GLuint);
typedef void (APIENTRY *PFN_UseProgram)(GLuint);
typedef void (APIENTRY *PFN_GenVertexArrays)(GLsizei,GLuint*);
typedef void (APIENTRY *PFN_BindVertexArray)(GLuint);
typedef void (APIENTRY *PFN_GenBuffers)(GLsizei,GLuint*);
typedef void (APIENTRY *PFN_BindBufferT)(GLenum,GLuint);
typedef void (APIENTRY *PFN_BufferDataT)(GLenum,ptrdiff_t,const void*,GLenum);
typedef void (APIENTRY *PFN_VertexAttribPointer)(GLuint,GLint,GLenum,GLboolean,GLsizei,const void*);
typedef void (APIENTRY *PFN_EnableVertexAttribArray)(GLuint);
typedef GLint (APIENTRY *PFN_GetUniformLocation)(GLuint,const char*);
typedef void (APIENTRY *PFN_UniformMatrix4fvT)(GLint,GLsizei,GLboolean,const GLfloat*);
typedef void (APIENTRY *PFN_Uniform4f)(GLint,GLfloat,GLfloat,GLfloat,GLfloat);
typedef void (APIENTRY *PFN_GetShaderiv)(GLuint,GLenum,GLint*);

static PFN_CreateShader p_CreateShader; static PFN_ShaderSource p_ShaderSource;
static PFN_CompileShader p_CompileShader; static PFN_CreateProgram p_CreateProgram;
static PFN_AttachShader p_AttachShader; static PFN_LinkProgram p_LinkProgram;
static PFN_UseProgram p_UseProgram; static PFN_GenVertexArrays p_GenVertexArrays;
static PFN_BindVertexArray p_BindVertexArray; static PFN_GenBuffers p_GenBuffers;
static PFN_BindBufferT p_BindBufferGL; static PFN_BufferDataT p_BufferDataGL;
static PFN_VertexAttribPointer p_VertexAttribPointer;
static PFN_EnableVertexAttribArray p_EnableVertexAttribArray;
static PFN_GetUniformLocation p_GetUniformLocation;
static PFN_UniformMatrix4fvT p_UniformMatrix4fvGL; static PFN_Uniform4f p_Uniform4f;
static PFN_GetShaderiv p_GetShaderiv;

#define GL_TEXTURE0_            0x84C0
#define GL_ARRAY_BUFFER_        0x8892
#define GL_STATIC_DRAW_         0x88E4
#define GL_VERTEX_SHADER_       0x8B31
#define GL_FRAGMENT_SHADER_     0x8B30
#define GL_COMPILE_STATUS_      0x8B81

static GLuint g_handProg = 0, g_handVao = 0, g_handVbo = 0;
// Simon's own hand meshes, converted from hands_human.dae. Both hands live in
// one Collada geometry, split by X sign so each can follow its own controller.
static GLuint g_meshVao[2] = {0,0}, g_meshVbo[2] = {0,0};
static int    g_meshVerts[2] = {0,0};
// Grip correction: the fixed rotation from the mesh's authored orientation into
// the pose convention a controller reports. Needed even with perfect tracking,
// because the tracking is right and the mesh is misaligned relative to it.
// Position offsets, by contrast, disappear once controllers supply the position.
// Per-hand rotation. [0] = left, [1] = right. Mirroring only the roll could not
// express a natural pose, so each hand carries its own three angles.
static float g_handRot[2][3] = {
    { 1.5708f, 0.0f, -1.5708f },   // left
    { 1.5708f, 0.0f,  1.5708f },   // right
};
static volatile LONG g_handSel = 1;   // which hand the keys adjust; 2 = both
static float g_handReach = 0.40f, g_handSpread = 0.18f, g_handDrop = -0.18f;

// Single source of truth for where a hand is, in world space. hand: 0 = left,
// 1 = right. Both the drawn mesh and the physics grab target read this, so they
// cannot drift apart -- and a controller pose will later replace only the body
// of this function.
static void GetHandPose(int hand, float* outPos) {
    float t = (float)NowSeconds();          // seconds, so the motion is framerate-independent
    float side = (hand == 0) ? -g_handSpread : g_handSpread;
    float fwd  = g_handReach + 0.10f * sinf(t * 1.8f + hand * 1.7f);
    float up   = g_handDrop  + 0.08f * cosf(t * 2.3f + hand);
    outPos[0] = g_camWorld[0] + g_camFwd[0]*fwd + g_camRight[0]*side + g_camUp[0]*up;
    outPos[1] = g_camWorld[1] + g_camFwd[1]*fwd + g_camRight[1]*side + g_camUp[1]*up;
    outPos[2] = g_camWorld[2] + g_camFwd[2]*fwd + g_camRight[2]*side + g_camUp[2]*up;
}

#define kMaxBones 32
static GLint  g_handTexLoc = -1, g_handHasTexLoc = -1;
static GLint  g_handBonesLoc = -1, g_handPivotLoc = -1, g_handSkinnedLoc = -1;

// Skeleton for one hand. Joints arrive parents-first, so world transforms
// accumulate in a single forward pass.
// flags: bit0 = finger segment, bits4-7 = finger id, bits8-11 = segment number
struct HandJoint { int parent; int flags; float bendAxis[3];
                   float local[16]; float invBind[16]; };
struct HandSkin {
    int        jointCount;
    HandJoint  joints[kMaxBones];
    float      pivot[3];
    bool       valid;
};
static HandSkin g_skin[2];
static float g_gripCurl = 0.0f;      // manual grip, used when nothing is held
// Per-finger curl, so a finger further from the object closes further. Index
// 0 thumb .. 4 pinky.
static float g_fingerCurl[2][5] = {{0,0,0,0,0},{0,0,0,0,0}};
static bool  g_contactGrip = true;   // stop fingers at the object's surface
static float g_lastObjRadius = 0.0f;
static float g_lastObjCentre[3] = {0,0,0};
static float g_lastObjExtent[3] = {0,0,0};
static long  g_gripFramesHeld = 0, g_gripFramesFree = 0, g_gripContacts = 0;
static float g_lastCurls[5] = {0,0,0,0,0};
static float g_lastTipDist = 0.0f;
static float g_aabbOffset = 0.0f;
// Hand origin, index fingertip and object centre, all in world space. If the
// tip is far from the hand it drew at, the mesh-to-world transform is wrong.
static float g_dbgTip[3]={0,0,0}, g_dbgHand[3]={0,0,0}, g_dbgObj[3]={0,0,0};
static float g_curlProfile[6] = {0,0,0,0,0,0};
static float g_tipTravel = 0.0f;
static int   g_curlAxis = 2;         // 0 = X, 1 = Y, 2 = Z (Z is this rig's bend axis)
static float g_curlSign = -1.0f;     // fingers curl toward the palm, not away
static int   g_thumbAxis = 0;        // thumb opposes on a different axis to the fingers
static float g_thumbSign = -1.0f;
static float g_thumbAdduct = 0.9f;   // swing across the palm
// Finger joints get the curl; wrist and arm do not.
static bool  g_isFinger[2][kMaxBones];
// SOMA's own skin texture, lifted straight out of the DDS mip chain as DXT5 and
// uploaded compressed -- no decode needed.
static GLuint g_handTex = 0;
typedef void (APIENTRY *PFN_CompressedTexImage2D)(GLenum,GLint,GLenum,GLsizei,GLsizei,
                                                  GLint,GLsizei,const void*);
typedef void (APIENTRY *PFN_ActiveTextureT)(GLenum);
typedef void (APIENTRY *PFN_Uniform1iT)(GLint,GLint);
typedef void (APIENTRY *PFN_GenerateMipmapT)(GLenum);
static PFN_CompressedTexImage2D p_CompressedTexImage2D = nullptr;
static PFN_ActiveTextureT       p_ActiveTexture = nullptr;
static PFN_Uniform1iT           p_Uniform1i = nullptr;
typedef void (APIENTRY *PFN_Uniform3fT)(GLint,GLfloat,GLfloat,GLfloat);
static PFN_Uniform3fT           p_Uniform3f = nullptr;

#define GL_COMPRESSED_RGBA_S3TC_DXT1_ 0x83F1
#define GL_COMPRESSED_RGBA_S3TC_DXT3_ 0x83F2
#define GL_COMPRESSED_RGBA_S3TC_DXT5_ 0x83F3
#define GL_TEXTURE_MAX_LEVEL_         0x813D

// Read SOMA's own .dds. Uploading the whole mip chain gives full resolution and
// avoids the shimmer a single high-res level produces on moving geometry -- and
// it removes the conversion step, so hand variants can just be copied in.
static bool LoadDDS(const char* path) {
    FILE* f = fopen(path, "rb");
    if (!f) return false;
    fseek(f, 0, SEEK_END); long total = ftell(f); fseek(f, 0, SEEK_SET);
    if (total < 128) { fclose(f); return false; }
    unsigned char* buf = (unsigned char*)malloc(total);
    if (!buf || (long)fread(buf,1,total,f) != total) { free(buf); fclose(f); return false; }
    fclose(f);

    if (memcmp(buf, "DDS ", 4) != 0) { Log("  %s: not a DDS", path); free(buf); return false; }
    unsigned h    = *(unsigned*)(buf+12);
    unsigned w    = *(unsigned*)(buf+16);
    unsigned mips = *(unsigned*)(buf+28);
    char fourcc[5] = {0};
    memcpy(fourcc, buf+84, 4);        // copy out: buf is freed before we log it
    if (mips == 0) mips = 1;

    GLenum fmt = 0; unsigned blockBytes = 16;
    if      (!memcmp(fourcc,"DXT1",4)) { fmt = GL_COMPRESSED_RGBA_S3TC_DXT1_; blockBytes = 8; }
    else if (!memcmp(fourcc,"DXT3",4)) { fmt = GL_COMPRESSED_RGBA_S3TC_DXT3_; }
    else if (!memcmp(fourcc,"DXT5",4)) { fmt = GL_COMPRESSED_RGBA_S3TC_DXT5_; }
    else {
        // DX10 carries the real format in an extra header; the normal map uses it.
        Log("  %s: fourcc '%.4s' unsupported (DX10 needs the extended header)",
            path, fourcc);
        free(buf); return false;
    }
    if (!p_CompressedTexImage2D) { Log("  glCompressedTexImage2D unavailable");
                                   free(buf); return false; }

    Log("  %s: %ux%u '%s', %u mips, %ld bytes -- uploading", path, w, h, fourcc,
        mips, total);
    glGenTextures(1, &g_handTex);
    glBindTexture(GL_TEXTURE_2D, g_handTex);
    unsigned off = 128, lw = w, lh = h, uploaded = 0;
    for (unsigned i = 0; i < mips; ++i) {
        unsigned sz = ((lw+3)/4) * ((lh+3)/4) * blockBytes;
        if (off + sz > (unsigned)total) break;              // truncated chain
        p_CompressedTexImage2D(GL_TEXTURE_2D, (GLint)i, fmt, (GLsizei)lw, (GLsizei)lh,
                               0, (GLsizei)sz, buf + off);
        off += sz; ++uploaded;
        if (lw > 1) lw /= 2; if (lh > 1) lh /= 2;
    }
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                    uploaded > 1 ? GL_LINEAR_MIPMAP_LINEAR : GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL_, (GLint)(uploaded-1));
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glBindTexture(GL_TEXTURE_2D, 0);
    free(buf);
    Log("  loaded: %u of %u mip levels, %.1f MB", uploaded, mips, off/1048576.0);
    return true;
}

// Fallback: the small pre-extracted .tex, if the .dds is not present.
static bool LoadHandTexture(const char* path) {
    FILE* f = fopen(path, "rb");
    if (!f) return false;
    unsigned hdr[5];
    if (fread(hdr,4,5,f) != 5 || hdr[0] != 0x48545831u) { fclose(f); return false; }
    unsigned w = hdr[1], h = hdr[2], fmt = hdr[3], bytes = hdr[4];
    void* data = malloc(bytes);
    if (!data || fread(data,1,bytes,f) != bytes) { free(data); fclose(f); return false; }
    fclose(f);
    if (!p_CompressedTexImage2D) { free(data); return false; }
    glGenTextures(1, &g_handTex);
    glBindTexture(GL_TEXTURE_2D, g_handTex);
    p_CompressedTexImage2D(GL_TEXTURE_2D, 0, (GLenum)fmt, (GLsizei)w, (GLsizei)h,
                           0, (GLsizei)bytes, data);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glBindTexture(GL_TEXTURE_2D, 0);
    free(data);
    Log("  loaded %s: %ux%u single level, %u KB", path, w, h, bytes/1024);
    return true;
}

// Column-major 4x4 multiply, out = a * b.
static void Mat4Mul(const float* a, const float* b, float* out) {
    for (int c = 0; c < 4; ++c)
        for (int r = 0; r < 4; ++r)
            out[c*4+r] = a[0*4+r]*b[c*4+0] + a[1*4+r]*b[c*4+1]
                       + a[2*4+r]*b[c*4+2] + a[3*4+r]*b[c*4+3];
}
static void Mat4FromRowMajor(const float* rm, float* cm) {
    for (int r = 0; r < 4; ++r)
        for (int c = 0; c < 4; ++c) cm[c*4+r] = rm[r*4+c];
}

// HND3: pos(3) nrm(3) uv(2) jointIdx(4 int) weights(4) per vertex, then
// parent + local + inverse-bind per joint. Verified offline: bone matrices
// come out as identity at bind pose on both hands.
static bool LoadHandSkin(int idx, const char* file) {
    FILE* f = fopen(file, "rb");
    if (!f) return false;
    unsigned magic=0, nverts=0, njoints=0;
    if (fread(&magic,4,1,f)!=1 || fread(&nverts,4,1,f)!=1 || fread(&njoints,4,1,f)!=1
        || magic != 0x484E4435u) { fclose(f); return false; }
    if (njoints > kMaxBones) {
        Log("  %s: %u joints exceeds the %d-bone limit", file, njoints, kMaxBones);
        fclose(f); return false;
    }
    HandSkin& hs = g_skin[idx];
    hs.jointCount = (int)njoints;
    if (fread(hs.pivot, 4, 3, f) != 3) { fclose(f); return false; }

    size_t vbytes = (size_t)nverts * 16 * sizeof(float);   // 8 float + 4 int + 4 float
    float* vdata = (float*)malloc(vbytes);
    if (!vdata || fread(vdata,1,vbytes,f) != vbytes) { free(vdata); fclose(f); return false; }

    for (unsigned j = 0; j < njoints; ++j) {
        int par, flg; float loc[16], inv[16];
        float ax[3];
        if (fread(&par,4,1,f)!=1 || fread(&flg,4,1,f)!=1 || fread(ax,4,3,f)!=3
            || fread(loc,4,16,f)!=16 || fread(inv,4,16,f)!=16) {
            free(vdata); fclose(f); return false;
        }
        hs.joints[j].parent = par;
        hs.joints[j].flags  = flg;
        memcpy(hs.joints[j].bendAxis, ax, sizeof(ax));
        Mat4FromRowMajor(loc, hs.joints[j].local);      // file is row-major
        Mat4FromRowMajor(inv, hs.joints[j].invBind);
    }
    fclose(f);

    p_GenVertexArrays(1,&g_meshVao[idx]); p_BindVertexArray(g_meshVao[idx]);
    p_GenBuffers(1,&g_meshVbo[idx]);
    p_BindBufferGL(GL_ARRAY_BUFFER_, g_meshVbo[idx]);
    p_BufferDataGL(GL_ARRAY_BUFFER_, (ptrdiff_t)vbytes, vdata, GL_STATIC_DRAW_);
    const GLsizei stride = 16*sizeof(float);
    p_VertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,stride,(const void*)0);
    p_EnableVertexAttribArray(0);
    p_VertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,stride,(const void*)(3*sizeof(float)));
    p_EnableVertexAttribArray(1);
    p_VertexAttribPointer(2,2,GL_FLOAT,GL_FALSE,stride,(const void*)(6*sizeof(float)));
    p_EnableVertexAttribArray(2);
    // Joint indices are int32 in the file. normalized must be FALSE so the
    // value converts to its actual number rather than being divided by INT_MAX.
    p_VertexAttribPointer(3,4,GL_INT,GL_FALSE,stride,(const void*)(8*sizeof(float)));
    p_EnableVertexAttribArray(3);
    p_VertexAttribPointer(4,4,GL_FLOAT,GL_FALSE,stride,(const void*)(12*sizeof(float)));
    p_EnableVertexAttribArray(4);
    p_BindVertexArray(0);
    g_meshVerts[idx] = (int)nverts;
    free(vdata);
    // Classified by NAME in the converter. The previous depth heuristic caught
    // the forearm twist chain as well, which is what rolled the whole hand.
    int nf = 0;
    for (int n = 0; n < hs.jointCount; ++n) {
        g_isFinger[idx][n] = (hs.joints[n].flags & 1) != 0;
        if (g_isFinger[idx][n]) ++nf;
    }
    Log("    %d of %d joints are finger segments (from the rig's own names)",
        nf, hs.jointCount);
    hs.valid = true;
    Log("  loaded %s: %u verts, %u joints (skinned)", file, nverts, njoints);
    return true;
}

static bool LoadHandMesh(int idx, const char* file) {
    char path[MAX_PATH]; 
    snprintf(path, MAX_PATH, "%s", file);
    FILE* f = fopen(path, "rb");
    if (!f) { Log("  could not open %s", path); return false; }
    unsigned magic = 0, nverts = 0;
    if (fread(&magic,4,1,f)!=1 || fread(&nverts,4,1,f)!=1 || magic != 0x484E4432u) {
        Log("  %s: bad header (magic 0x%08X)", path, magic); fclose(f); return false;
    }
    size_t bytes = (size_t)nverts * 8 * sizeof(float);   // pos, normal, uv
    float* data = (float*)malloc(bytes);
    if (!data || fread(data,1,bytes,f) != bytes) {
        Log("  %s: truncated", path); free(data); fclose(f); return false;
    }
    fclose(f);

    p_GenVertexArrays(1,&g_meshVao[idx]); p_BindVertexArray(g_meshVao[idx]);
    p_GenBuffers(1,&g_meshVbo[idx]);
    p_BindBufferGL(GL_ARRAY_BUFFER_, g_meshVbo[idx]);
    p_BufferDataGL(GL_ARRAY_BUFFER_, (ptrdiff_t)bytes, data, GL_STATIC_DRAW_);
    p_VertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,8*sizeof(float),(const void*)0);
    p_EnableVertexAttribArray(0);
    p_VertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,8*sizeof(float),
                          (const void*)(3*sizeof(float)));
    p_EnableVertexAttribArray(1);
    p_VertexAttribPointer(2,2,GL_FLOAT,GL_FALSE,8*sizeof(float),
                          (const void*)(6*sizeof(float)));
    p_EnableVertexAttribArray(2);
    p_BindVertexArray(0);
    g_meshVerts[idx] = (int)nverts;
    free(data);
    Log("  loaded %s: %u verts (%zu KB)", path, nverts, bytes/1024);
    return true;
}
static GLint  g_handMvpLoc = -1, g_handColLoc = -1, g_handModelLoc = -1;
static volatile LONG g_handDraw = 0;
// A control marker at a FIXED world position. The hand cubes are camera-relative
// so they follow you by design -- which means they cannot prove the transform.
// This one should stay anchored in the room as you walk away from it.
static float g_anchor[3] = {0,0,0};
static volatile LONG g_anchorSet = 0;
static volatile LONG g_drawHandCalls = 0, g_drawHandDrawn = 0;


static const char* kHandVS =
  "#version 330 core\n"
  "layout(location=0) in vec3 aPos;\n"
  "layout(location=1) in vec3 aNrm;\n"
  "layout(location=2) in vec2 aUV;\n"
  "layout(location=3) in vec4 aJoints;\n"
  "layout(location=4) in vec4 aWeights;\n"
  "uniform mat4 uMVP;\n"
  "uniform mat4 uModel;\n"
  "uniform mat4 uBones[32];\n"
  "uniform vec3 uPivot;\n"      // palm centre, in the mesh's own cm units
  "uniform int  uSkinned;\n"
  "out vec3 vN;\n"
  "out vec2 vUV;\n"
  "void main(){\n"
  "  vec3 p = aPos; vec3 n = aNrm;\n"
  "  if (uSkinned != 0) {\n"
  // Linear blend skinning. Bones are identity at bind pose, so a zero curl
  // reproduces the original mesh exactly.
  "    vec3 sp = vec3(0.0); vec3 sn = vec3(0.0);\n"
  "    for (int i = 0; i < 4; ++i) {\n"
  "      float w = aWeights[i];\n"
  "      if (w <= 0.0) continue;\n"
  "      mat4 B = uBones[int(aJoints[i])];\n"
  "      sp += w * (B * vec4(aPos,1.0)).xyz;\n"
  "      sn += w * (mat3(B) * aNrm);\n"
  "    }\n"
  "    p = sp; n = normalize(sn);\n"
  "    p = (p - uPivot) * 0.01;\n"   // cm -> m, pivot on the palm
  "  }\n"
  "  vN = mat3(uModel) * n; vUV = aUV;\n"
  "  gl_Position = uMVP * vec4(p,1.0);\n"
  "}\n";
static const char* kHandFS =
  "#version 330 core\n"
  "in vec3 vN;\n"
  "in vec2 vUV;\n"
  "uniform vec4 uCol;\n"
  "uniform sampler2D uTex;\n"
  "uniform int uHasTex;\n"
  "out vec4 oFrag;\n"
  "void main(){\n"
  "  vec3 n = normalize(vN);\n"
  "  if (!gl_FrontFacing) n = -n;\n"
  "  float d = max(dot(n, normalize(vec3(0.4,0.8,0.3))), 0.0);\n"
  "  vec3 base = (uHasTex != 0) ? texture(uTex, vUV).rgb : uCol.rgb;\n"
  "  oFrag = vec4(base * (0.35 + 0.65*d), uCol.a);\n"
  "}\n";

static bool InitHandGL() {
    if (g_handProg) return true;
    HMODULE gl = GetModuleHandleA("opengl32.dll");
    if (!gl) return false;
    typedef PROC (WINAPI *PFN_GPA)(LPCSTR);
    PFN_GPA gpa = (PFN_GPA)GetProcAddress(gl, "wglGetProcAddress");
    if (!gpa) return false;
    #define R(v,n) v = (decltype(v))(void*)gpa(n); if(!v){ Log("  missing %s", n); return false; }
    R(p_CreateShader,"glCreateShader") R(p_ShaderSource,"glShaderSource")
    R(p_CompileShader,"glCompileShader") R(p_CreateProgram,"glCreateProgram")
    R(p_AttachShader,"glAttachShader") R(p_LinkProgram,"glLinkProgram")
    R(p_UseProgram,"glUseProgram") R(p_GenVertexArrays,"glGenVertexArrays")
    R(p_BindVertexArray,"glBindVertexArray") R(p_GenBuffers,"glGenBuffers")
    R(p_BindBufferGL,"glBindBuffer") R(p_BufferDataGL,"glBufferData")
    R(p_VertexAttribPointer,"glVertexAttribPointer")
    R(p_EnableVertexAttribArray,"glEnableVertexAttribArray")
    R(p_GetUniformLocation,"glGetUniformLocation")
    R(p_UniformMatrix4fvGL,"glUniformMatrix4fv") R(p_Uniform4f,"glUniform4f")
    R(p_GetShaderiv,"glGetShaderiv")
    #undef R
    p_CompressedTexImage2D = (PFN_CompressedTexImage2D)(void*)gpa("glCompressedTexImage2D");
    p_ActiveTexture        = (PFN_ActiveTextureT)(void*)gpa("glActiveTexture");
    p_Uniform1i            = (PFN_Uniform1iT)(void*)gpa("glUniform1i");
    p_Uniform3f            = (PFN_Uniform3fT)(void*)gpa("glUniform3f");

    GLuint vs = p_CreateShader(GL_VERTEX_SHADER_);
    p_ShaderSource(vs,1,&kHandVS,nullptr); p_CompileShader(vs);
    GLint ok=0; p_GetShaderiv(vs, GL_COMPILE_STATUS_, &ok);
    if(!ok){ Log("  hand vertex shader failed to compile"); return false; }
    GLuint fs = p_CreateShader(GL_FRAGMENT_SHADER_);
    p_ShaderSource(fs,1,&kHandFS,nullptr); p_CompileShader(fs);
    p_GetShaderiv(fs, GL_COMPILE_STATUS_, &ok);
    if(!ok){ Log("  hand fragment shader failed to compile"); return false; }

    g_handProg = p_CreateProgram();
    p_AttachShader(g_handProg, vs); p_AttachShader(g_handProg, fs);
    p_LinkProgram(g_handProg);
    g_handMvpLoc = p_GetUniformLocation(g_handProg, "uMVP");
    g_handModelLoc = p_GetUniformLocation(g_handProg, "uModel");
    g_handTexLoc    = p_GetUniformLocation(g_handProg, "uTex");
    g_handHasTexLoc = p_GetUniformLocation(g_handProg, "uHasTex");
    g_handBonesLoc   = p_GetUniformLocation(g_handProg, "uBones");
    g_handPivotLoc   = p_GetUniformLocation(g_handProg, "uPivot");
    g_handSkinnedLoc = p_GetUniformLocation(g_handProg, "uSkinned");
    g_handColLoc = p_GetUniformLocation(g_handProg, "uCol");

    // A unit cube, 12 triangles, centred on the origin.
    const float h = 0.5f;
    const float v[] = {
      -h,-h,-h,  h,-h,-h,  h, h,-h,   -h,-h,-h,  h, h,-h, -h, h,-h,
      -h,-h, h,  h, h, h,  h,-h, h,   -h,-h, h, -h, h, h,  h, h, h,
      -h,-h,-h, -h, h, h, -h,-h, h,   -h,-h,-h, -h, h,-h, -h, h, h,
       h,-h,-h,  h,-h, h,  h, h, h,    h,-h,-h,  h, h, h,  h, h,-h,
      -h,-h,-h, -h,-h, h,  h,-h, h,   -h,-h,-h,  h,-h, h,  h,-h,-h,
      -h, h,-h,  h, h, h, -h, h, h,   -h, h,-h,  h, h,-h,  h, h, h };
    p_GenVertexArrays(1,&g_handVao); p_BindVertexArray(g_handVao);
    p_GenBuffers(1,&g_handVbo);
    p_BindBufferGL(GL_ARRAY_BUFFER_, g_handVbo);
    p_BufferDataGL(GL_ARRAY_BUFFER_, sizeof(v), v, GL_STATIC_DRAW_);
    p_VertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,3*sizeof(float),(const void*)0);
    p_EnableVertexAttribArray(0);
    p_BindVertexArray(0);
    // Cube VBO also needs the normal attribute now that the shader expects it.
    p_VertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,3*sizeof(float),(const void*)0);
    p_EnableVertexAttribArray(1);

    Log("hand renderer ready");
    char dir[MAX_PATH] = {0};
    if (GetModuleFileNameA(g_selfModule, dir, MAX_PATH)) {
        char* sl = strrchr(dir, '\\'); if (sl) *(sl+1) = 0;
    }
    char lp[MAX_PATH], rp[MAX_PATH];
    snprintf(lp, MAX_PATH, "%shand_left.bin", dir);
    snprintf(rp, MAX_PATH, "%shand_right.bin", dir);
    // Prefer SOMA's own .dds at full resolution; fall back to the small .tex.
    char dp[MAX_PATH], tp[MAX_PATH];
    snprintf(dp, MAX_PATH, "%shands_human_skin.dds", dir);
    snprintf(tp, MAX_PATH, "%shand_skin.tex", dir);
    if (!LoadDDS(dp) && !LoadHandTexture(tp))
        Log("  no hand texture found (looked for hands_human_skin.dds, then"
            " hand_skin.tex) -- hands stay flat-coloured");
    char ls[MAX_PATH], rs[MAX_PATH];
    snprintf(ls, MAX_PATH, "%shand_left.skin",  dir);
    snprintf(rs, MAX_PATH, "%shand_right.skin", dir);
    bool okL = LoadHandSkin(0, ls) || LoadHandMesh(0, lp);
    bool okR = LoadHandSkin(1, rs) || LoadHandMesh(1, rp);
    if (!okL || !okR)
        Log("  hand meshes missing -- falling back to cubes."
            " Place hand_left.bin and hand_right.bin beside the DLL.");
    return true;
}

// Draw a cube at a world position, scaled, using the scene's ViewProj.
// Draw one of the loaded hand meshes at a world position.
// Build the bone palette. world[n] = world[parent] * local[n] * curl[n], and
// bone[n] = world[n] * invBind[n], which is identity at rest.
static void CurlRotation(const HandJoint& j, float curl, float* R);

static void BuildBones(int idx, float* out /*kMaxBones*16*/) {
    const HandSkin& hs = g_skin[idx];
    static float world[kMaxBones][16];
    for (int n = 0; n < hs.jointCount; ++n) {
        float posed[16];
        if (g_isFinger[idx][n] && g_gripCurl > 0.0001f) {
            // Curl about one local axis; which axis a rig uses varies, so it is
            // selectable rather than assumed.
            int finger = (hs.joints[n].flags >> 4) & 0xF;
            int seg    = (hs.joints[n].flags >> 8) & 0xF;
            float R[16]; CurlRotation(hs.joints[n], g_fingerCurl[idx][finger], R);
            Mat4Mul(hs.joints[n].local, R, posed);
        } else {
            memcpy(posed, hs.joints[n].local, sizeof(posed));
        }
        if (hs.joints[n].parent < 0) memcpy(world[n], posed, sizeof(posed));
        else Mat4Mul(world[hs.joints[n].parent], posed, world[n]);
    }
    for (int n = 0; n < hs.jointCount; ++n)
        Mat4Mul(world[n], hs.joints[n].invBind, out + n*16);
    for (int n = hs.jointCount; n < kMaxBones; ++n) {
        float* m = out + n*16;
        memset(m, 0, 16*sizeof(float)); m[0]=m[5]=m[10]=m[15]=1.0f;
    }
}

// Single definition of a joint's curl rotation, used by both the bone builder
// and the contact search so the two cannot disagree about the pose.
static void AxisRot(int axis, float a, float* R) {
    float c = cosf(a), s2 = sinf(a);
    for (int i = 0; i < 16; ++i) R[i] = 0.0f;
    R[0]=R[5]=R[10]=R[15]=1.0f;
    if (axis == 0)      { R[5]=c; R[6]=s2; R[9]=-s2; R[10]=c; }
    else if (axis == 1) { R[0]=c; R[2]=-s2; R[8]=s2; R[10]=c; }
    else                { R[0]=c; R[1]=s2; R[4]=-s2; R[5]=c; }
}

// Rotate about an arbitrary unit axis (Rodrigues), column-major.
static void AxisAngle(const float* n, float a, float* R) {
    float c = cosf(a), s2 = sinf(a), t = 1.0f - c;
    float x=n[0], y=n[1], z=n[2];
    R[0]=t*x*x+c;    R[1]=t*x*y+s2*z; R[2]=t*x*z-s2*y; R[3]=0;
    R[4]=t*x*y-s2*z; R[5]=t*y*y+c;    R[6]=t*y*z+s2*x; R[7]=0;
    R[8]=t*x*z+s2*y; R[9]=t*y*z-s2*x; R[10]=t*z*z+c;   R[11]=0;
    R[12]=R[13]=R[14]=0; R[15]=1;
}

// Each joint carries its own bend axis, derived from the rig: perpendicular to
// the bone and to the palm plane. That is correct for the thumb as well, so no
// axis needs guessing or cycling.
static void CurlRotation(const HandJoint& j, float curl, float* R) {
    int finger = (j.flags >> 4) & 0xF;
    int seg    = (j.flags >> 8) & 0xF;
    float segScale = (seg <= 1) ? 0.7f : (seg == 2 ? 1.0f : 1.2f);
    float a = curl * 1.4f * ((finger == 0) ? 0.55f : 1.0f) * segScale * g_curlSign;
    // Rotation about a world axis. j.bendAxis is present in the file but NOT
    // used: deriving it produced worse fists, and the offline check that
    // "verified" it shared the code's own wrong assumption about which frame
    // the axis lives in. It needs a visual check before being trusted.
    float c = cosf(a), s2 = sinf(a);
    for (int i = 0; i < 16; ++i) R[i] = 0.0f;
    R[0]=R[5]=R[10]=R[15]=1.0f;
    if (g_curlAxis == 0)      { R[5]=c; R[6]=s2; R[9]=-s2; R[10]=c; }
    else if (g_curlAxis == 1) { R[0]=c; R[2]=-s2; R[8]=s2; R[10]=c; }
    else                      { R[0]=c; R[1]=s2; R[4]=-s2; R[5]=c; }
}

// Forward-kinematic tip position for one finger at a given curl, in mesh cm
// space. Uses the same joint chain the shader will, so what we test is what
// gets drawn.
static bool FingerTipAt(int idx, int finger, float curl, float* outCm) {
    const HandSkin& hs = g_skin[idx];
    static float w[kMaxBones][16];
    int tip = -1, tipSeg = -1;
    for (int n = 0; n < hs.jointCount; ++n) {
        float posed[16];
        int f = (hs.joints[n].flags >> 4) & 0xF;
        int seg = (hs.joints[n].flags >> 8) & 0xF;
        bool isThis = (hs.joints[n].flags & 1) && f == finger;
        if (isThis && curl > 0.0001f) {
            float R[16]; CurlRotation(hs.joints[n], curl, R);
            Mat4Mul(hs.joints[n].local, R, posed);
        } else memcpy(posed, hs.joints[n].local, sizeof(posed));
        if (hs.joints[n].parent < 0) memcpy(w[n], posed, sizeof(posed));
        else Mat4Mul(w[hs.joints[n].parent], posed, w[n]);
        if (isThis && seg > tipSeg) { tipSeg = seg; tip = n; }
    }
    if (tip < 0) return false;
    outCm[0] = w[tip][12]; outCm[1] = w[tip][13]; outCm[2] = w[tip][14];
    return true;
}

// Close each finger until its tip reaches the held object, then stop. Fingers
// at different distances stop at different angles, which is what makes a grip
// look like it is holding something rather than making a fist.
// Mean fingertip position at half curl: the point the hand closes around.
static void UpdateGripCentre(int idx, const float* model) {
    if (idx != 1 || !g_skin[idx].valid) return;
    float sum[3] = {0,0,0}; int n = 0;
    for (int fi = 0; fi < 5; ++fi) {
        float tipCm[3];
        if (!FingerTipAt(idx, fi, 0.5f, tipCm)) continue;
        float lx = (tipCm[0]-g_skin[idx].pivot[0])*0.01f;
        float ly = (tipCm[1]-g_skin[idx].pivot[1])*0.01f;
        float lz = (tipCm[2]-g_skin[idx].pivot[2])*0.01f;
        sum[0] += model[0]*lx + model[4]*ly + model[8]*lz  + model[12];
        sum[1] += model[1]*lx + model[5]*ly + model[9]*lz  + model[13];
        sum[2] += model[2]*lx + model[6]*ly + model[10]*lz + model[14];
        ++n;
    }
    if (!n) return;
    // Halfway between the palm and where the fingertips meet.
    for (int i = 0; i < 3; ++i)
        g_gripCentre[i] = 0.5f * (sum[i]/n) + 0.5f * model[12+i];
    InterlockedExchange(&g_gripCentreValid, 1);
}

static void UpdateContactGrip(int idx, const float* model) {
    float target[5];
    // The grab targets the RIGHT hand, so only that hand can contact-grip.
    // Testing the empty hand against the held object was why the two
    // hand-to-object distances disagreed (0.07 m vs 0.40 m in one frame).
    bool holding = g_contactGrip && (idx == 1) && g_heldBody
                && p_NewtonGetAABB && g_skin[idx].valid;

    float centre[3] = {0,0,0}, radius = 0.0f;
    if (holding) {
        alignas(16) float p0[4] = {0,0,0,0}, p1[4] = {0,0,0,0};
        p_NewtonGetAABB(g_heldBody, p0, p1);
        // Cross-check: the AABB centre should sit on the body. GetMatrix is
        // known good (the grab uses it), so a large gap means the AABB read is
        // wrong rather than the object being genuinely huge.
        if (p_NewtonGetMatrix) {
            float m[16]; p_NewtonGetMatrix(g_heldBody, m);
            float cx=0.5f*(p0[0]+p1[0]), cy=0.5f*(p0[1]+p1[1]), cz=0.5f*(p0[2]+p1[2]);
            g_aabbOffset = sqrtf((cx-m[12])*(cx-m[12]) + (cy-m[13])*(cy-m[13])
                               + (cz-m[14])*(cz-m[14]));
        }
        for (int i = 0; i < 3; ++i) centre[i] = 0.5f*(p0[i]+p1[i]);
        // Newton reports ~1 m extents for a 50 g object while the CENTRE is
        // correct to within 8 cm, so the volume is inflated and unusable for
        // sizing. Smallest half-extent is the least-bad signal, clamped to a
        // range a hand can actually close around.
        float hx=0.5f*(p1[0]-p0[0]), hy=0.5f*(p1[1]-p0[1]), hz=0.5f*(p1[2]-p0[2]);
        float smallest = hx < hy ? (hx < hz ? hx : hz) : (hy < hz ? hy : hz);
        radius = smallest;
        if (radius < 0.03f) radius = 0.03f;
        if (radius > 0.10f) radius = 0.10f;
        g_lastObjRadius = radius;
        g_lastObjExtent[0] = p1[0]-p0[0];
        g_lastObjExtent[1] = p1[1]-p0[1];
        g_lastObjExtent[2] = p1[2]-p0[2];
        memcpy(g_lastObjCentre, centre, sizeof(centre));
    }

    if (holding) ++g_gripFramesHeld; else ++g_gripFramesFree;

    // Profile the index finger across the whole curl range, unconditionally, so
    // the shape is never truncated by the contact break below.
    if (holding) {
        for (int k = 0; k < 6; ++k) {
            float c = k / 5.0f;
            float tipCm[3];
            if (!FingerTipAt(idx, 1, c, tipCm)) break;
            float lx = (tipCm[0]-g_skin[idx].pivot[0])*0.01f;
            float ly = (tipCm[1]-g_skin[idx].pivot[1])*0.01f;
            float lz = (tipCm[2]-g_skin[idx].pivot[2])*0.01f;
            float wx = model[0]*lx + model[4]*ly + model[8]*lz  + model[12];
            float wy = model[1]*lx + model[5]*ly + model[9]*lz  + model[13];
            float wz = model[2]*lx + model[6]*ly + model[10]*lz + model[14];
            float dx = wx-centre[0], dy = wy-centre[1], dz = wz-centre[2];
            g_curlProfile[k] = sqrtf(dx*dx+dy*dy+dz*dz);
        }
        // Where does the fingertip actually go, relative to the palm?
        float t0[3], t1[3];
        if (FingerTipAt(idx, 1, 0.0f, t0) && FingerTipAt(idx, 1, 1.0f, t1)) {
            g_tipTravel = sqrtf((t1[0]-t0[0])*(t1[0]-t0[0])
                              + (t1[1]-t0[1])*(t1[1]-t0[1])
                              + (t1[2]-t0[2])*(t1[2]-t0[2])) * 0.01f;
        }
    }

    for (int fi = 0; fi < 5; ++fi) {
        if (!holding) { target[fi] = g_gripCurl; continue; }
        target[fi] = 1.0f;                       // close fully unless something stops it
        for (int step = 1; step <= 16; ++step) {
            float c = step / 16.0f;
            float tipCm[3];
            if (!FingerTipAt(idx, fi, c, tipCm)) break;
            // mesh cm -> metres about the palm -> world
            float lx = (tipCm[0]-g_skin[idx].pivot[0])*0.01f;
            float ly = (tipCm[1]-g_skin[idx].pivot[1])*0.01f;
            float lz = (tipCm[2]-g_skin[idx].pivot[2])*0.01f;
            float wx = model[0]*lx + model[4]*ly + model[8]*lz  + model[12];
            float wy = model[1]*lx + model[5]*ly + model[9]*lz  + model[13];
            float wz = model[2]*lx + model[6]*ly + model[10]*lz + model[14];
            if (fi == 1 && step == 6) {
                g_dbgTip[0]=wx; g_dbgTip[1]=wy; g_dbgTip[2]=wz;
                g_dbgHand[0]=model[12]; g_dbgHand[1]=model[13]; g_dbgHand[2]=model[14];
                memcpy(g_dbgObj, centre, sizeof(g_dbgObj));
            }
            float dx = wx-centre[0], dy = wy-centre[1], dz = wz-centre[2];
            float d = sqrtf(dx*dx+dy*dy+dz*dz);
            if (fi == 1 && step == 8) g_lastTipDist = d;
            if (d <= radius) { target[fi] = c; ++g_gripContacts; break; }
        }
    }
    // ease toward the target so contact does not snap
    for (int fi = 0; fi < 5; ++fi) {
        float d = target[fi] - g_fingerCurl[idx][fi];
        g_fingerCurl[idx][fi] += d * 0.25f;
        if (idx == 1) g_lastCurls[fi] = g_fingerCurl[idx][fi];
    }
}

static void DrawHandMesh(int idx, const float* pos, float scale) {
    if (!g_meshVerts[idx]) return;
    // Mesh orientation, then the camera basis, then position. Mirrored in X for
    // the left hand so one mesh convention serves both.
    const float* rot = g_handRot[idx];
    float cx=cosf(rot[0]), sx=sinf(rot[0]);
    float cy=cosf(rot[1]), sy=sinf(rot[1]);
    float cz=cosf(rot[2]), sz=sinf(rot[2]);
    float Rx[16]={1,0,0,0, 0,cx,sx,0, 0,-sx,cx,0, 0,0,0,1};
    float Ry[16]={cy,0,-sy,0, 0,1,0,0, sy,0,cy,0, 0,0,0,1};
    float Rz[16]={cz,sz,0,0, -sz,cz,0,0, 0,0,1,0, 0,0,0,1};
    float R1[16]; vpm::Mul4x4(Rz, Ry, R1);
    float R[16];  vpm::Mul4x4(R1, Rx, R);

    // Orient into the camera's frame so the hands turn with the view.
    float B[16] = { g_camRight[0], g_camRight[1], g_camRight[2], 0,
                    g_camUp[0],    g_camUp[1],    g_camUp[2],    0,
                    -g_camFwd[0], -g_camFwd[1],  -g_camFwd[2],   0,
                    0,0,0,1 };
    float BR[16]; vpm::Mul4x4(B, R, BR);
    float M[16];
    for (int i = 0; i < 12; ++i) M[i] = BR[i] * scale;
    M[3]=M[7]=M[11]=0;
    M[12]=pos[0]; M[13]=pos[1]; M[14]=pos[2]; M[15]=1;

    float mvp[16]; vpm::Mul4x4(g_viewProjCM, M, mvp);
    p_UseProgram(g_handProg);
    p_UniformMatrix4fvGL(g_handModelLoc, 1, GL_FALSE, M);
    p_UniformMatrix4fvGL(g_handMvpLoc, 1, GL_FALSE, mvp);
    p_Uniform4f(g_handColLoc, 0.85f, 0.68f, 0.58f, 1.0f);   // fallback tint
    bool textured = (g_handTex != 0) && p_ActiveTexture && p_Uniform1i;
    GLint prevTex = 0;
    if (textured) {
        p_ActiveTexture(GL_TEXTURE0_);
        glGetIntegerv(GL_TEXTURE_BINDING_2D, &prevTex);   // put the engine's back after
        glBindTexture(GL_TEXTURE_2D, g_handTex);
        p_Uniform1i(g_handTexLoc, 0);          // sampler reads texture unit 0
    }
    if (p_Uniform1i) p_Uniform1i(g_handHasTexLoc, textured ? 1 : 0);

    UpdateGripCentre(idx, M);
    UpdateContactGrip(idx, M);

    bool skinned = g_skin[idx].valid && g_handBonesLoc >= 0;
    if (p_Uniform1i) p_Uniform1i(g_handSkinnedLoc, skinned ? 1 : 0);
    if (skinned) {
        static float bones[kMaxBones*16];
        BuildBones(idx, bones);
        p_UniformMatrix4fvGL(g_handBonesLoc, kMaxBones, GL_FALSE, bones);
        if (p_Uniform3f) p_Uniform3f(g_handPivotLoc, g_skin[idx].pivot[0],
                                     g_skin[idx].pivot[1], g_skin[idx].pivot[2]);
    }
    p_BindVertexArray(g_meshVao[idx]);
    glDrawArrays(GL_TRIANGLES, 0, g_meshVerts[idx]);
    p_BindVertexArray(0);
    p_UseProgram(0);
    if (textured) glBindTexture(GL_TEXTURE_2D, (GLuint)prevTex);
}

static void DrawMarker(const float* pos, float size, float r, float g, float b) {
    float M[16] = { size,0,0,0,  0,size,0,0,  0,0,size,0,
                    pos[0],pos[1],pos[2],1 };
    float mvp[16]; vpm::Mul4x4(g_viewProjCM, M, mvp);
    p_UseProgram(g_handProg);
    p_UniformMatrix4fvGL(g_handMvpLoc, 1, GL_FALSE, mvp);
    p_Uniform4f(g_handColLoc, r, g, b, 1.0f);
    p_BindVertexArray(g_handVao);
    glDrawArrays(GL_TRIANGLES, 0, 36);
    p_BindVertexArray(0);
    p_UseProgram(0);
}

static void DrawHands() {
    if (!InterlockedCompareExchange(&g_handDraw, 0, 0)) return;
    InterlockedIncrement(&g_drawHandCalls);
    if (!InterlockedCompareExchange(&g_haveVP, 0, 0)) return;
    if (!InitHandGL()) { InterlockedExchange(&g_handDraw, 0); return; }

    // Drawn inside the render pass now, where the scene's depth buffer exists,
    // so geometry occludes the markers properly.
    GLboolean depthWas = glIsEnabled(GL_DEPTH_TEST);
    GLboolean cullWas  = glIsEnabled(GL_CULL_FACE);
    GLboolean maskWas  = GL_TRUE;
    glGetBooleanv(GL_DEPTH_WRITEMASK, &maskWas);
    GLint cullModeWas = GL_BACK, frontFaceWas = GL_CCW;
    glGetIntegerv(GL_CULL_FACE_MODE, &cullModeWas);
    glGetIntegerv(GL_FRONT_FACE, &frontFaceWas);

    glEnable(GL_DEPTH_TEST);
    glDepthMask(GL_TRUE);          // engine may have writes off; without this the
                                   // far surface overdraws the near one
    glEnable(GL_CULL_FACE);        // winding verified consistent on every triangle
    glCullFace(GL_BACK);
    glFrontFace(GL_CCW);

    // World-anchored control: dropped where you stood when F9 was pressed.
    if (InterlockedCompareExchange(&g_anchorSet, 0, 0)) {
        float a[3] = { g_anchor[0], g_anchor[1] - 0.3f, g_anchor[2] };
        DrawMarker(a, 0.14f, 0.2f, 1.0f, 0.3f);
    }

    // Two synthetic hands about where a person's would be.
    for (int i = 0; i < 2; ++i) {
        float p[3]; GetHandPose(i, p);
        if (g_meshVerts[i]) DrawHandMesh(i, p, 1.0f);
        else DrawMarker(p, 0.09f, i==0 ? 1.0f : 0.2f, 0.4f, i==0 ? 0.2f : 1.0f);
        InterlockedIncrement(&g_drawHandDrawn);
    }
    if (!depthWas) glDisable(GL_DEPTH_TEST);
    if (!cullWas)  glDisable(GL_CULL_FACE);
    glDepthMask(maskWas);
    glCullFace((GLenum)cullModeWas);
    glFrontFace((GLenum)frontFaceWas);
}

static void Marker() {
    GLint prev = 0;
    if (g_BindFBO) { glGetIntegerv(0x8CA6, &prev); if (prev) g_BindFBO(0x8D40, 0); }
    GLboolean was = glIsEnabled(GL_SCISSOR_TEST);
    GLint box[4]; glGetIntegerv(GL_SCISSOR_BOX, box);
    GLfloat clr[4]; glGetFloatv(GL_COLOR_CLEAR_VALUE, clr);
    glEnable(GL_SCISSOR_TEST);
    glScissor(16, 16, 48, 48);
    if (InterlockedCompareExchange(&g_stereoOn, 0, 0))
        // red = left eye, blue = right eye, so alternation is visible
        (InterlockedCompareExchange(&g_eye, 0, 0) == 0)
            ? glClearColor(1.0f, 0.15f, 0.15f, 1.0f)
            : glClearColor(0.15f, 0.35f, 1.0f, 1.0f);
    else if (InterlockedCompareExchange(&g_hookOn, 0, 0))
        glClearColor(0.1f, 0.4f, 1.0f, 1.0f);
    else
        glClearColor(0.0f, 1.0f, 0.35f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    glClearColor(clr[0], clr[1], clr[2], clr[3]);
    glScissor(box[0], box[1], box[2], box[3]);
    if (!was) glDisable(GL_SCISSOR_TEST);
    if (g_BindFBO && prev) g_BindFBO(0x8D40, (unsigned)prev);
}

static bool InstallEngineHook() {
    // The camera itself: apply the head pose before the view matrix is built,
    // so culling and everything downstream follow it.
    if (!o_UpdateViewMatrix) {
        void* uv = (void*)((char*)GetModuleHandleA(NULL) + 0x277630);
        if (MH_CreateHook(uv, (void*)d_UpdateViewMatrix, (void**)&o_UpdateViewMatrix) == MH_OK &&
            MH_EnableHook(uv) == MH_OK) {
            g_cameraHookActive = true;
            Log("cCamera3D::UpdateViewMatrix hooked at %p (RVA 0x277630)"
                "  <-- head pose now reaches the camera BEFORE culling;"
                " the old frustum rotation is now disabled", uv);
        } else {
            o_UpdateViewMatrix = nullptr;
        }
    }

    if (!o_LogicTimerDue) {
        void* lt = (void*)((char*)GetModuleHandleA(NULL) + 0x3B90C0);
        if (MH_CreateHook(lt, (void*)d_LogicTimerDue, (void**)&o_LogicTimerDue) == MH_OK &&
            MH_EnableHook(lt) == MH_OK)
            Log("logic-timer step check hooked at %p (RVA 0x3B90C0)", lt);
        else
            o_LogicTimerDue = nullptr;
    }

    if (!o_GraphicsInit) {
        void* gi = (void*)((char*)GetModuleHandleA(NULL) + 0x210FF0);
        if (MH_CreateHook(gi, (void*)d_GraphicsInit, (void**)&o_GraphicsInit) == MH_OK &&
            MH_EnableHook(gi) == MH_OK)
            Log("cGraphics::Init hooked at %p (RVA 0x210FF0)"
                "  <-- render resolution is set here", gi);
        else
            o_GraphicsInit = nullptr;
    }

    if (!o_SetView) {
            void* sv = (void*)((char*)GetModuleHandleA(NULL) + 0x2B4380);
            bool okv = (MH_CreateHook(sv, (void*)d_SetView, (void**)&o_SetView) == MH_OK)
                       && (MH_EnableHook(sv) == MH_OK);
            if (!okv) o_SetView = nullptr;
            Log("SetMatrix VIEW (RVA 0x2B4380) hook %s -- world scale is applied"
                " here, on the matrix geometry is drawn with", okv ? "ok" : "FAILED");
    }

    // The frustum rebuild: the culling planes are built here, so the headset
    // FOV must be in place for THIS call, not just the view-matrix one.
    if (!o_GetFrustum) {
        void* gf = (void*)((char*)GetModuleHandleA(NULL) + 0x277D80);
        if (MH_CreateHook(gf, (void*)d_GetFrustum, (void**)&o_GetFrustum) == MH_OK &&
            MH_EnableHook(gf) == MH_OK) {
            g_widenAtCamera = true;
            Log("cCamera3D::GetFrustum hooked at %p (RVA 0x277D80)"
                "  <-- the culling planes are built here;"
                " the old frustum-field write is now disabled", gf);
        } else {
            o_GetFrustum = nullptr;
        }
    }

    // Light setup: verify what it caches and whether it tracks our view.
    if (!o_LightSetup) {
        void* ls = (void*)((char*)GetModuleHandleA(NULL) + 0x406560);
        if (MH_CreateHook(ls, (void*)d_LightSetup, (void**)&o_LightSetup) == MH_OK &&
            MH_EnableHook(ls) == MH_OK)
            Log("Setup Light Instancing hooked at %p (RVA 0x406560)", ls);
        else
            o_LightSetup = nullptr;
    }
    if (o_SetProj) return true;
    HMODULE exe = GetModuleHandleA(nullptr);
    if (!exe) { Log("could not resolve Soma.exe base"); return false; }
    void* addr = (void*)((uintptr_t)exe + kRVA_SetProjectionMatrix);
    if (MH_CreateHook(addr, (void*)d_SetProj, (void**)&o_SetProj) != MH_OK ||
        MH_EnableHook(addr) != MH_OK) {
        Log("FAILED to hook SetProjectionMatrix at 0x%p", addr);
        o_SetProj = nullptr; return false;
    }
    Log("SetProjectionMatrix hooked at 0x%p (base 0x%p + 0x%llX)",
        addr, (void*)exe, (unsigned long long)kRVA_SetProjectionMatrix);
    return true;
}

static void Keys() {
    static bool d1=false,d2=false,d3=false,d4=false,d5=false,d6=false,d7=false,d8=false,d9=false,d10=false,d11=false,d12=false;
    bool k;

    k = (GetAsyncKeyState(VK_F2) & 0x8000) != 0;
    if (k && !d2) {
        if (InstallEngineHook()) {
            LONG on = InterlockedCompareExchange(&g_hookOn,0,0) ? 0 : 1;
            InterlockedExchange(&g_hookOn, on);
            Log(""); Log(">>> F2: engine projection substitution %s", on?"ON":"OFF");
        }
    }
    d2 = k;



    k = (GetAsyncKeyState(VK_F1) & 0x8000) != 0;
    if (k && !d1) { g_eyeOffsetScale = fmaxf(-8.0f, g_eyeOffsetScale - 0.25f);
                    InterlockedExchange(&g_worldScaleLogged, 0);
        InterlockedExchange(&g_setViewLogged, 0);
                    InterlockedExchange(&g_eyeOffsetLogged, 0);
                    Log(">>> F1: eye offset x%.2f", g_eyeOffsetScale); }
    d1 = k;
    k = (GetAsyncKeyState(VK_F9) & 0x8000) != 0;
    if (k && !d9) {
        LONG on = InterlockedCompareExchange(&g_handDraw,0,0) ? 0 : 1;
        InterlockedExchange(&g_handDraw, on);
        if (!o_SetProj) InstallEngineHook();      // ViewProj comes from here
        if (!o_Render)  InstallRenderHook();      // DrawHands runs inside this
        Log("    hooks: projection %s, render %s",
            o_SetProj ? "installed" : "MISSING", o_Render ? "installed" : "MISSING");
        if (on) {
            g_anchor[0]=g_camWorld[0]; g_anchor[1]=g_camWorld[1]; g_anchor[2]=g_camWorld[2];
            InterlockedExchange(&g_anchorSet, 1);
        } else InterlockedExchange(&g_anchorSet, 0);
        Log(""); Log(">>> F9: HAND MARKERS %s", on ? "ON" : "OFF");
        if (on) {
            Log("    RED/BLUE cubes are camera-relative, so they follow you --");
            Log("    that is correct for hands, and says nothing about the maths.");
            Log("    The GREEN cube is dropped at your current position and should");
            Log("    STAY THERE as you walk away. That is the real test, and it");
            Log("    should also be hidden when geometry gets between you and it.");
        }
    }
    d9 = k;

    {
        static bool dHM = false;
        bool kh = (GetAsyncKeyState(VK_INSERT) & 0x8000) != 0;
        if (kh && !dHM) {
            LONG m = (InterlockedCompareExchange(&g_headMode,0,0) + 1) % 9;
            InterlockedExchange(&g_headMode, m);
            InterlockedExchange(&g_headTraceDiv, 0);
            InterlockedExchange(&g_headTraceBudget, 120);
            static const char* kNames[9] = {
                "game-world", "-Z", "-X", "swap XZ", "negated",
                "unconverted XR",
                "OFF (no head translation)",
                "PROBE: fixed +1m on X -- the view MUST jump",
                "PROBE: fixed +1m on Z -- the view MUST jump" };
            Log(">>> [INSERT] HEAD TRANSLATION MODE %ld: %s -- lean forward and left;"
                " when the world holds still instead of sliding, that is it.",
                m, kNames[m]);
        }
        dHM = kh;
    }
    {   // DELETE: re-centre 6DOF here and now
        static bool dRC = false;
        bool kr = (GetAsyncKeyState(VK_DELETE) & 0x8000) != 0;
        if (kr && !dRC) {
            InterlockedExchange(&g_xrOriginSet, 0);
            InterlockedExchange(&g_originDelay, 200);
            InterlockedExchange(&g_headTraceDiv, 0);
            InterlockedExchange(&g_headTraceBudget, 120);
            Log(">>> [DELETE] 6DOF RE-CENTRED -- your current head position is now"
                " the neutral point. Sit still for a moment before pressing.");
        }
        dRC = kr;
    }
    k = (GetAsyncKeyState(VK_F4) & 0x8000) != 0;
    if (k && !d4) {
        g_eyeOffsetScale = fminf(8.0f, g_eyeOffsetScale + 0.25f);
        InterlockedExchange(&g_eyeOffsetLogged, 0);
        InterlockedExchange(&g_projEyeLogged, 0);
        Log(">>> F4: eye offset x%.2f -- multiplies the per-eye camera"
            " displacement. At 0 the eyes coincide (mono); above 1 the world"
            " should look SMALLER because parallax says it is nearer.",
            g_eyeOffsetScale);
    }
    d4 = k;


    k = (GetAsyncKeyState(VK_F7) & 0x8000) != 0;
    if (k && !d7) {
        if (!InterlockedExchange(&g_xrTried, 1)) {
            // Hand the engine's real render size over BEFORE Init, so the
            // swapchain matches it. Blitting a 16:9 image into a 0.935 texture
            // squashes it while we tell the runtime it spans the full angle,
            // which is what made the world slide against head motion.
            if (g_fullW > 0 && g_fullH > 0) {
                g_xr.SetRenderSize(g_fullW, g_fullH);
                Log("  swapchain will match SOMA's render size %dx%d"
                    " (no rescale, no squash)", g_fullW, g_fullH);
            }
            if (g_xr.Init(Log)) InterlockedExchange(&g_xrOn, 1);
            else Log(">>> F7: OpenXR unavailable, continuing on the monitor only");
        } else {
            LONG on = InterlockedCompareExchange(&g_xrOn,0,0) ? 0 : 1;
            InterlockedExchange(&g_xrOn, on);
            Log(">>> F7: OpenXR submission %s", on ? "ON" : "OFF");
        }
    }
    d7 = k;


    k = (GetAsyncKeyState(VK_F10) & 0x8000) != 0;
    if (k && !d10) {
        if (InstallRenderHook()) {
            LONG on = InterlockedCompareExchange(&g_sbsOn,0,0) ? 0 : 1;
            InterlockedExchange(&g_sbsOn, on);
            if (on) InterlockedExchange(&g_doubleOn, 0);
            Log("");
            Log(">>> F10: SIDE-BY-SIDE STEREO %s", on ? "ON" : "OFF");
            if (on) {
                Log("    Left eye into the left half, right eye into the right.");
                Log("    This is NATIVE stereo -- two renders per frame -- shown on");
                Log("    a flat screen instead of a headset. Cross your eyes to fuse");
                Log("    the halves and it should have real depth.");
                Log("    Requires F2 on for the per-eye projection to apply.");
                Log("    Eyes now ALTERNATE per frame and are captured at swap,");
                Log("    where framebuffer 0 is known to hold the finished image.");
                Log("    Each half refreshes every other frame, so this is not yet");
                Log("    native stereo -- but the picture is geometrically correct");
                Log("    and the same textures will feed the OpenXR swapchains.");
                if (!InterlockedCompareExchange(&g_hookOn,0,0))
                    Log("    NOTE: F2 is OFF, so both halves will be identical.");
            }
        }
    }
    d10 = k;

    k = (GetAsyncKeyState(VK_F11) & 0x8000) != 0;
    if (k && !d11) {
        LONG on = InterlockedCompareExchange(&g_swapHalves,0,0) ? 0 : 1;
        InterlockedExchange(&g_swapHalves, on);
        Log(">>> F11: halves %s  (%s viewing)", on ? "SWAPPED" : "normal",
            on ? "cross-eyed" : "parallel / wall-eyed");
    }
    d11 = k;

    k = (GetAsyncKeyState(VK_F12) & 0x8000) != 0;
    if (k && !d12) {
        LONG on = InterlockedCompareExchange(&g_headTest,0,0) ? 0 : 1;
        InterlockedExchange(&g_headTest, on);
        Log("");
        Log(">>> F12: HEAD POSE SWEEP %s", on ? "ON" : "OFF");
        if (on) { InterlockedExchange(&g_traceLeft, 24);
                  Log("    tracing the view's forward vector for a few frames"); }
        if (on) {
            Log("    All SIX degrees of freedom now sweep: yaw, pitch, ROLL, and");
            Log("    position (leaning left/right, up/down, in/out). Roll should");
            Log("    tilt the horizon; leaning should shift near objects against");
            Log("    far ones -- that motion parallax is what makes VR feel solid.");
            Log("    The view should move on its own, as if you were");
            Log("    looking around -- proving view CONTROL, which is what head");
            Log("    tracking needs. Requires F2.");
            Log("    Rotation now goes into cFrustum's m_mtxView at +0x158, with");
            Log("    m_mtxViewProj at +0x118 recomputed to match. HPL2's member");
            Log("    order gives those offsets, and the reflection pass uses");
            Log("    +0x158 the same way.");
            Log("    The six culling planes at +0x198 are now rebuilt from the");
            Log("    rotated ViewProj, the same Gribb-Hartmann extraction HPL2");
            Log("    uses, so geometry should no longer pop at the edges.");
        }
    }
    d12 = k;

    {
        static bool dT=false, dY=false;
        bool bt=(GetAsyncKeyState('T')&0x8000)!=0;
        bool by=(GetAsyncKeyState('Y')&0x8000)!=0;
        if (bt && !dT) ScanLogicTimer();
        if (by && !dY) {
            void* lt = InterlockedCompareExchangePointer(
                           (void* volatile*)&g_logicTimer, nullptr, nullptr);
            float hz = g_xr.Ready() ? g_xr.DisplayRefreshHz() : 0.0f;
            if (!lt) {
                Log("  logic timer not seen yet -- it is captured on the first"
                    " frame after F2; try again in a moment.");
            } else if (hz < 30.0f || hz > 200.0f) {
                Log("  no usable headset refresh yet (%.1f Hz) -- press F7 first"
                    " so the rate can be read from the runtime.", hz);
            } else {
                int* pUps = (int*)((char*)lt + kTimerUpdatesPerSec);
                int oldUps = *pUps;
                int newUps = (oldUps == (int)(hz + 0.5f)) ? 60 : (int)(hz + 0.5f);
                *pUps = newUps;
                Log("  logic rate %d -> %d Hz. The engine derives its fixed step"
                    " from this, so game speed is unchanged; what changes is that"
                    " logic and rendering now share a cadence. Press Y again to"
                    " go back to %d. TEST PHYSICS AND GRABBING at this setting.",
                    oldUps, newUps, 60);
            }
        }
        dT=bt; dY=by;
    }

    // G / H = close / open the grip, J = cycle the curl axis.
    {
        static bool dG=false, dH=false, dJ=false;
        bool bg=(GetAsyncKeyState('G')&0x8000)!=0;
        bool bh=(GetAsyncKeyState('H')&0x8000)!=0;
        bool bj=(GetAsyncKeyState('J')&0x8000)!=0;
        if (bg) { g_gripCurl += 0.02f; if (g_gripCurl > 1.0f) g_gripCurl = 1.0f; }
        if (bh) { g_gripCurl -= 0.02f; if (g_gripCurl < 0.0f) g_gripCurl = 0.0f; }
        if ((bg && !dG) || (bh && !dH))
            Log("  grip %.2f (axis %c)", g_gripCurl, "XYZ"[g_curlAxis]);
        if (bj && !dJ) {
            g_curlAxis = (g_curlAxis + 1) % 3;
            Log("  curl axis -> %c", "XYZ"[g_curlAxis]);
        }
        {
            static bool dLB=false, dRB=false;
            bool blb=(GetAsyncKeyState(VK_OEM_COMMA)&0x8000)!=0;   // ','
            bool brb=(GetAsyncKeyState(VK_OEM_PERIOD)&0x8000)!=0;  // '.'
            if (blb && !dLB) { g_cullMargin -= 0.15f;
                               if (g_cullMargin < 1.05f) g_cullMargin = 1.05f;
                               InterlockedExchange(&g_fovWidened, 0);
                               Log("  cull margin %.2f", g_cullMargin); }
            if (brb && !dRB) { g_cullMargin += 0.15f;
                               if (g_cullMargin > 2.5f) g_cullMargin = 2.5f;
                               InterlockedExchange(&g_fovWidened, 0);
                               Log("  cull margin %.2f  (wider keeps more geometry"
                                   " alive when you look away from the game camera)",
                                   g_cullMargin); }
            dLB=blb; dRB=brb;
        }

        {   // C: dump the addresses to breakpoint, for finding the camera
            static bool dC=false;
            bool bc=(GetAsyncKeyState('C')&0x8000)!=0;
            if (bc && !dC) {
                void* fr = g_frustumPtr;
                if (!fr) Log("  no frustum yet -- press F2 and let a frame run first");
                else {
                    HMODULE base = GetModuleHandleA(NULL);
                    Log("");
                    Log(">>> WATCH ADDRESSES (set hardware WRITE breakpoints on these)");
                    Log("    Soma.exe base   %p   (Ghidra shows 0x140000000)", base);
                    Log("    cFrustum        %p", fr);
                    Log("    +0x24 mfFOV     %p   <-- who writes this is cFrustum::SetFOV;"
                        " its caller is the camera", (char*)fr + kFrustumFov);
                    Log("    +0x20 mfAspect  %p", (char*)fr + kFrustumAspect);
                    Log("    +0x158 m_mtxView %p  <-- written when the camera's"
                        " orientation is applied", (char*)fr + kFrustumView);
                    Log("    +0xd8 m_mtxProj %p   <-- written by SetProjectionMatrix"
                        " (already known, use as a sanity check)", (char*)fr + kFrustumProj);
                    Log("    In x64dbg: Memory Breakpoint -> Write on each, run one");
                    Log("    frame, and read the call stack. The frame ABOVE the");
                    Log("    setter is the camera update we need to hook.");
                    Log("    Subtract the base to get the RVA for Ghidra.");
                    Log("");
                }
            }
            dC=bc;
        }

        {
            static bool dZ=false;
            bool bz=(GetAsyncKeyState('Z')&0x8000)!=0;
            if (bz && !dZ) {
                LONG on = InterlockedCompareExchange(&g_altEyes,0,0) ? 0 : 1;
                InterlockedExchange(&g_altEyes, on);
                Log("  %s", on
                    ? "ONE EYE PER FRAME, captured after the engine's full frame."
                      " Colour and lighting should now match the monitor, but each"
                      " eye only refreshes every other frame."
                    : "two raw eyes per frame (full rate, but before post processing)");
            }
            dZ=bz;
        }

        {   // X cycles the capture source through the FBOs the engine actually
            // uses, so we can find the one holding the post-processed image.
            static const LONG kCand[] = {0, 56, 54, 13, 11, 1, 63, 62};
            static int ci = 0;
            static bool dX=false;
            bool bx=(GetAsyncKeyState('X')&0x8000)!=0;
            if (bx && !dX) {
                ci = (ci + 1) % (int)(sizeof(kCand)/sizeof(kCand[0]));
                InterlockedExchange(&g_captureFbo, kCand[ci]);
                if (kCand[ci] == 0)
                    Log("  capture source: whatever Render leaves bound (raw scene)");
                else
                    Log("  capture source: FBO %ld  -- if the picture brightens to"
                        " match the monitor, this is the post-processed buffer",
                        kCand[ci]);
            }
            dX=bx;
        }

        {   // PAGE DOWN: arm the hardware write watch on frustum+0x158, the view
        // matrix the renderer actually draws with. Three candidate positions
        // have now been eliminated by measurement -- camera+0x10 and
        // renderer+0xbd4 move nothing, and writing frustum+0x158 translates the
        // SCENE rather than the eye (the world drags along with the probe).
        // So stop guessing where the eye position lives and let the engine name
        // whoever composes this matrix, exactly as the watch named SetScreenSize.
        static bool dFW = false;
        bool kf = (GetAsyncKeyState(VK_NEXT) & 0x8000) != 0;
        if (kf && !dFW) {
            void* fr = g_frustumPtr;
            if (!fr) {
                Log(">>> [PGDN] no main frustum yet -- press F2 and let a frame"
                    " render first.");
            } else if (g_frustumWatchOn) {
                Log(">>> [PGDN] frustum watch already armed.");
            } else {
                if (!g_vehHandle) {
                    g_exeBase = (uintptr_t)GetModuleHandleA(NULL);
                    g_vehHandle = AddVectoredExceptionHandler(1, WatchVeh);
                }
                int armed = ArmWatchAllThreads((char*)fr + 0x158);
                g_frustumWatchOn = true;
                Log("");
                Log(">>> [PGDN] WRITE WATCH armed on frustum+0x158 (%p) across"
                    " %d thread(s). Every RVA reported below is a writer of the"
                    " view matrix. The one that is NOT our ApplyHeadPose is the"
                    " engine's own composer -- read it in Ghidra and it will"
                    " show which position field the eye is built from.",
                    (char*)fr + 0x158, armed);

                // POSITIVE CONTROL -- the last run armed this watch and saw
                // zero writes, while our own ApplyHeadPose demonstrably wrote
                // the matrix 1200 times in the same window. Without a
                // self-test, "no hits" cannot be told apart from "the trap
                // never worked", and that is exactly what happened. Arm this
                // thread and write the field ourselves before believing
                // anything.
                {
                    CONTEXT c; memset(&c, 0, sizeof(c));
                    c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
                    HANDLE me = GetCurrentThread();
                    if (GetThreadContext(me, &c)) {
                        c.Dr0 = (DWORD64)(uintptr_t)((char*)fr + 0x158);
                        c.Dr7 &= ~(DWORD64)0xF0003;
                        c.Dr7 |=  (DWORD64)0x1;
                        c.Dr7 |=  (DWORD64)0x1 << 16;
                        c.Dr7 |=  (DWORD64)0x3 << 18;
                        c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
                        SetThreadContext(me, &c);
                    }
                    LONG before = InterlockedCompareExchange(&g_watchHits, 0, 0);
                    volatile float* probe = (volatile float*)((char*)fr + 0x158);
                    float keep = *probe;
                    *probe = keep;                 // a real write, same value
                    LONG after = InterlockedCompareExchange(&g_watchHits, 0, 0);
                    if (after > before)
                        Log("    SELFTEST OK: the frustum watch fired on our own"
                            " write. Silence from here really does mean nobody"
                            " else writes it.");
                    else
                        Log("    SELFTEST FAILED: our own write did NOT trigger"
                            " the frustum watch, so the trap is not working and"
                            " the previous run's 'zero writes' meant nothing."
                            " Most likely the render thread is not among the"
                            " threads armed, or something re-arms DR7 after us.");
                }
            }
        }
        dFW = kf;
    }
    {   // PAGE UP: vsync on/off, to A/B the jitter
            static bool dK3=false;
            bool bk3=(GetAsyncKeyState(VK_PRIOR)&0x8000)!=0;
            if (bk3 && !dK3) {
                g_wantVsyncOff = !g_wantVsyncOff;
                if (p_SwapInterval) {
                    p_SwapInterval(g_wantVsyncOff ? 0 : 1);
                    InterlockedExchange(&g_vsyncOff, g_wantVsyncOff ? 1 : 0);
                }
                Log("  vsync %s", g_wantVsyncOff
                    ? "OFF -- the headset paces the frame (smoother head turning)"
                    : "ON  -- capped at the monitor's refresh (jitter at 90 Hz)");
            }
            dK3=bk3;
        }

        {   // R: fit the render viewport to the projection aspect
            static bool dR2=false;
            bool br2=(GetAsyncKeyState('R')&0x8000)!=0;
            if (br2 && !dR2) {
                g_fitViewport = !g_fitViewport;
                InterlockedExchange(&g_vpFitLogged, 0);
                Log("  viewport fitting %s", g_fitViewport
                    ? "ON  -- render aspect matches the projection (correct scale)"
                    : "OFF -- full viewport (objects look oversized)");
            }
            dR2=br2;
        }

        {   // E: let the engine's own projection stand (camera hook only)
            static bool dE=false;
            bool be=(GetAsyncKeyState('E')&0x8000)!=0;
            if (be && !dE) {
                g_substituteProj = !g_substituteProj;
                Log("  projection substitution %s", g_substituteProj
                    ? "ON  -- our per-eye matrix (asymmetric, correct stereo)"
                    : "OFF -- the engine's own matrix from the widened camera."
                      " Stereo asymmetry is lost; this is a DIAGNOSTIC. If the"
                      " lighting goes correct now, substitution is the conflict.");
            }
            dE=be;
        }

        {
            static bool dW=false;
            bool bw=(GetAsyncKeyState('W')&0x8000)!=0;
            if (bw && !dW) {
                g_poseBeforeLights = !g_poseBeforeLights;
                Log("  head pose applied %s light setup", g_poseBeforeLights
                    ? "BEFORE (lights and pixels agree on the camera)"
                    : "after, as before");
            }
            dW=bw;
        }

        {   // [ and ] add a constant yaw at the camera: the verification test.
            // A constant offset with NO VR should turn the world and leave
            // culling, shadows and lighting intact.
            static bool dK2=false;
            bool bk2=(GetAsyncKeyState(VK_OEM_5)&0x8000)!=0;   // backslash
            if (bk2 && !dK2) {
                g_cameraHook = !g_cameraHook;
                g_cameraHookActive = g_cameraHook && o_UpdateViewMatrix != nullptr;
                Log("  camera hook %s", g_cameraHook
                    ? "ON  -- pose applied at the camera, culling follows"
                    : "OFF -- back to rotating the frustum after culling");
            }
            dK2=bk2;

            static bool dLB2=false, dRB2=false;
            bool blb=(GetAsyncKeyState(VK_OEM_4)&0x8000)!=0;   // [
            bool brb=(GetAsyncKeyState(VK_OEM_6)&0x8000)!=0;   // ]
            if (blb && !dLB2) { g_camTestYaw -= 0.5236f;       // 30 deg
                                Log("  camera test yaw %.1f deg -- world should turn with"
                                    " NOTHING vanishing at the edges",
                                    g_camTestYaw * 57.2957795f); }
            if (brb && !dRB2) { g_camTestYaw += 0.5236f;
                                Log("  camera test yaw %.1f deg -- world should turn with"
                                    " NOTHING vanishing at the edges",
                                    g_camTestYaw * 57.2957795f); }
            dLB2=blb; dRB2=brb;
        }

        {
            static bool dQ=false;
            bool bq=(GetAsyncKeyState('Q')&0x8000)!=0;
            if (bq && !dQ) {
                g_fixStalePos = !g_fixStalePos;
                Log("  stale camera position %s", g_fixStalePos
                    ? "REFRESHED after light setup (lighting follows your head)"
                    : "left as the engine wrote it (original behaviour)");
            }
            dQ=bq;
        }

        {   // ; = hold the sweep here, ' = nudge it forward slowly
            static bool dSemi=false, dQuote=false;
            bool bs=(GetAsyncKeyState(VK_OEM_1)&0x8000)!=0;      // ;
            bool bq2=(GetAsyncKeyState(VK_OEM_7)&0x8000)!=0;     // '
            if (bs && !dSemi) {
                g_sweepHold = !g_sweepHold;
                Log("  sweep %s at t=%.2f -- park it on the bad angle, then the"
                    " scene is statically wrong and can be captured",
                    g_sweepHold ? "HELD" : "running again", g_sweepHeldT);
            }
            if (bq2 && g_sweepHold) {
                g_sweepHeldT += 0.01f;      // creep through the band
            }
            dSemi=bs; dQuote=bq2;
        }

        {
            static bool dV=false;
            bool bv=(GetAsyncKeyState('V')&0x8000)!=0;
            if (bv && !dV) {
                g_freezePose = !g_freezePose;
                Log("  head pose %s -- stereo and the headset FOV are unchanged."
                    " If lighting looks right now, the ROTATION is what breaks it;"
                    " if it still looks wrong, the PROJECTION SUBSTITUTION is.",
                    g_freezePose ? "FROZEN to identity" : "live again");
            }
            dV=bv;
        }

        {
            static bool dM=false;
            bool bm=(GetAsyncKeyState('M')&0x8000)!=0;
            if (bm && !dM) {
                g_rotateEarly = !g_rotateEarly;
                Log("  head rotation applied %s",
                    g_rotateEarly ? "BEFORE Render (culling may follow the head)"
                                  : "inside SetProjectionMatrix (original)");
            }
            dM=bm;
        }

        static bool dU=false, dI=false;
        bool bu=(GetAsyncKeyState('U')&0x8000)!=0;
        bool bi=(GetAsyncKeyState('I')&0x8000)!=0;
        if (bu && !dU) { g_thumbAxis = (g_thumbAxis+1)%3;
                         Log("  thumb axis -> %c", "XYZ"[g_thumbAxis]); }
        if (bi && !dI) { g_thumbSign = -g_thumbSign;
                         Log("  thumb direction -> %s",
                             g_thumbSign < 0 ? "toward the palm" : "away"); }
        static bool dO=false, dP2=false;
        bool bo=(GetAsyncKeyState('O')&0x8000)!=0;
        bool bp2=(GetAsyncKeyState(VK_OEM_4)&0x8000)!=0;   // '['
        if (bo && !dO)  { g_thumbAdduct += 0.15f;
                          Log("  thumb wrap %.2f", g_thumbAdduct); }
        if (bp2 && !dP2){ g_thumbAdduct -= 0.15f;
                          Log("  thumb wrap %.2f", g_thumbAdduct); }
        dO=bo; dP2=bp2;
        dU=bu; dI=bi;
        static bool dN=false;
        bool bn=(GetAsyncKeyState('N')&0x8000)!=0;
        if (bn && !dN) {
            g_contactGrip = !g_contactGrip;
            Log("  contact grip %s", g_contactGrip
                ? "ON  - fingers stop at the held object"
                : "OFF - G/H drives all fingers together");
        }
        dN=bn;
        static bool dK=false;
        bool bk=(GetAsyncKeyState('K')&0x8000)!=0;
        if (bk && !dK) {
            g_curlSign = -g_curlSign;
            Log("  curl direction -> %s", g_curlSign < 0 ? "toward the palm" : "away from the palm");
        }
        dK=bk;
        dG=bg; dH=bh; dJ=bj;
    }

    k = (GetAsyncKeyState(VK_F5) & 0x8000) != 0;
    if (k && !d5) {
        if (!o_NewtonAddForce) { DumpNewtonExports(); InstallPhysicsHook(); }
        LONG on = InterlockedCompareExchange(&g_physScan,0,0) ? 0 : 1;
        InterlockedExchange(&g_physScan, on);
        Log(""); Log(">>> F5: physics force scan %s", on ? "ON" : "OFF");
        if (on) Log("    Pick something up and CARRY IT AROUND. Gravity is purely\n                    vertical, so the held body is the one with horizontal force.");
    }
    d5 = k;

    k = (GetAsyncKeyState(VK_F3) & 0x8000) != 0;
    if (k && !d3) {
        if (!o_NewtonAddForce) { DumpNewtonExports(); InstallPhysicsHook(); }
        // The camera position comes from the SetProjectionMatrix hook, which
        // previously only F2 installed. Install it here too, leaving projection
        // substitution off -- the hand only needs to know where the player is.
        if (!o_SetProj) {
            Log("  installing the projection hook for camera position"
                " (F2's substitution stays off)");
            InstallEngineHook();
        }
        LONG on = InterlockedCompareExchange(&g_handOn,0,0) ? 0 : 1;
        InterlockedExchange(&g_handOn, on);
        if (!on) { g_heldBody = nullptr; g_heldHavePos = false;
                   g_prevHandValid = false;
                   g_prevHandValid = false; }
        Log(""); Log(">>> F3: SYNTHETIC HAND %s", on ? "ON" : "OFF");
        if (on) {
            Log("    Pick something up and hold it briefly. Latching is by DURATION");
            Log("    (%.2f s of sustained horizontal force), not force size, so a", kHoldSeconds);
            Log("    pencil qualifies as readily as a chair.");
            Log("    and from then on it chases a point ORBITING the player rather");
            Log("    than following your view. If it circles you while you stand");
            Log("    still, object physics can be driven from an arbitrary point --");
            Log("    which is the whole mechanism VR hands need.");
        }
    }
    d3 = k;

    k = (GetAsyncKeyState(VK_F6) & 0x8000) != 0;
    if (k && !d6) {
        if (InstallUiHook()) {
            LONG on = InterlockedCompareExchange(&g_uiHookOn,0,0) ? 0 : 1;
            InterlockedExchange(&g_uiHookOn, on);
            Log(""); Log(">>> F6: UI projection scan %s", on ? "ON" : "OFF");
            if (on) Log("    Open a menu, read a note, use a terminal. Distinct"
                        " orthographic projections will be listed each census.");
        }
    }
    d6 = k;

    // Grip orientation and placement. L / R / B select which hand the rotation
    // keys affect, since mirrored-only control could not express a real pose.
    {
        static bool dL=false, dR=false, dB=false;
        bool bl=(GetAsyncKeyState('L')&0x8000)!=0;
        bool br=(GetAsyncKeyState('R')&0x8000)!=0;
        bool bb=(GetAsyncKeyState('B')&0x8000)!=0;
        if (bl && !dL) { InterlockedExchange(&g_handSel,0); Log("  adjusting LEFT hand"); }
        if (br && !dR) { InterlockedExchange(&g_handSel,1); Log("  adjusting RIGHT hand"); }
        if (bb && !dB) { InterlockedExchange(&g_handSel,2); Log("  adjusting BOTH hands"); }
        dL=bl; dR=br; dB=bb;

        struct Adj { int vk; int alt; int axis; float step; const char* name; };
        static Adj adj[] = {
            { '1', VK_NUMPAD1, 0, +0.2618f, "rotX" },   // 15 degrees
            { '2', VK_NUMPAD2, 0, -0.2618f, "rotX" },
            { '3', VK_NUMPAD4, 1, +0.2618f, "rotY" },
            { '4', VK_NUMPAD5, 1, -0.2618f, "rotY" },
            { '5', VK_NUMPAD7, 2, +0.2618f, "rotZ" },
            { '6', VK_NUMPAD8, 2, -0.2618f, "rotZ" },
        };
        const int kN = (int)(sizeof(adj)/sizeof(adj[0]));
        static bool down[kN] = {false};
        LONG sel = InterlockedCompareExchange(&g_handSel,0,0);
        for (int i = 0; i < kN; ++i) {
            bool d = ((GetAsyncKeyState(adj[i].vk) & 0x8000) != 0) ||
                     ((GetAsyncKeyState(adj[i].alt) & 0x8000) != 0);
            if (d && !down[i]) {
                if (sel == 2) { g_handRot[0][adj[i].axis] += adj[i].step;
                                g_handRot[1][adj[i].axis] += adj[i].step; }
                else            g_handRot[sel][adj[i].axis] += adj[i].step;
                Log("  %s (%s) | L(%.4f %.4f %.4f)  R(%.4f %.4f %.4f)", adj[i].name,
                    sel==0?"left":sel==1?"right":"both",
                    g_handRot[0][0],g_handRot[0][1],g_handRot[0][2],
                    g_handRot[1][0],g_handRot[1][1],g_handRot[1][2]);
            }
            down[i] = d;
        }

        struct Pos { int vk; int alt; float* v; float step; const char* name; };
        static Pos pos[] = {
            { '7', VK_NUMPAD3, &g_handReach, +0.05f, "reach"  },
            { '8', VK_NUMPAD6, &g_handReach, -0.05f, "reach"  },
            { '9', VK_NUMPAD9, &g_handSpread,+0.03f, "spread" },
            { '0', VK_DIVIDE,  &g_handSpread,-0.03f, "spread" },
            { VK_OEM_PLUS,  VK_MULTIPLY, &g_handDrop, +0.03f, "height" },
            { VK_OEM_MINUS, VK_SUBTRACT, &g_handDrop, -0.03f, "height" },
        };
        const int kP = (int)(sizeof(pos)/sizeof(pos[0]));
        static bool downP[kP] = {false};
        for (int i = 0; i < kP; ++i) {
            bool d = ((GetAsyncKeyState(pos[i].vk) & 0x8000) != 0) ||
                     ((GetAsyncKeyState(pos[i].alt) & 0x8000) != 0);
            if (d && !downP[i]) {
                *pos[i].v += pos[i].step;
                Log("  %s = %+.3f  (reach %.2f spread %.2f height %.2f)",
                    pos[i].name, *pos[i].v, g_handReach, g_handSpread, g_handDrop);
            }
            downP[i] = d;
        }

        static bool dP = false;
        bool dp = ((GetAsyncKeyState('P') & 0x8000) != 0) ||
                  ((GetAsyncKeyState(VK_NUMPAD0) & 0x8000) != 0);
        if (dp && !dP) {
            Log("");
            Log(">>> bake these in as defaults:");
            Log("    { %.4ff, %.4ff, %.4ff },   // left",
                g_handRot[0][0], g_handRot[0][1], g_handRot[0][2]);
            Log("    { %.4ff, %.4ff, %.4ff },   // right",
                g_handRot[1][0], g_handRot[1][1], g_handRot[1][2]);
            Log("    (reach %.2f spread %.2f height %.2f -- replaced by tracking)",
                g_handReach, g_handSpread, g_handDrop);
        }
        dP = dp;
    }

    k = (GetAsyncKeyState(VK_F8) & 0x8000) != 0;
    if (k && !d8) {
        LONG on = InterlockedCompareExchange(&g_fovPulse,0,0) ? 0 : 1;
        InterlockedExchange(&g_fovPulse, on);
        Log(">>> F8: FOV pulse %s", on?"ON":"OFF");
    }
    d8 = k;
}

static BOOL WINAPI d_Swap(HDC hdc) {
    LONG n = InterlockedIncrement(&g_frame);

    if (!g_qpcFreq) { LARGE_INTEGER f; QueryPerformanceFrequency(&f); g_qpcFreq = f.QuadPart; }
    LONGLONG nowT = Now();
    if (g_lastSwap) { g_frameTicks += nowT - g_lastSwap; ++g_timedFrames; }
    g_lastSwap = nowT;

    if (n == 1) {
        const char* v = (const char*)glGetString(GL_VERSION);
        Log("first frame, GL_VERSION %s", v ? v : "(null)");
        HMODULE gl = GetModuleHandleA("opengl32.dll");
        typedef PROC (WINAPI *PFN_GPA)(LPCSTR);
        PFN_GPA gpa = gl ? (PFN_GPA)GetProcAddress(gl, "wglGetProcAddress") : nullptr;
        if (gpa) g_BindFBO = (PFN_BindFramebuffer)(void*)gpa("glBindFramebuffer");
    }

    // One eye per frame until the scene can be rendered twice.
    // With double-rendering the eye is chosen per render pass, not per frame,
    // so leave it alone in that mode.
    if (InterlockedCompareExchange(&g_stereoOn, 0, 0) &&
        !InterlockedCompareExchange(&g_doubleOn, 0, 0) &&
        !InterlockedCompareExchange(&g_sbsOn, 0, 0)) {
        LONG hold = InterlockedCompareExchange(&g_eyeHoldFrames, 0, 0);
        if (hold < 1) hold = 1;
        InterlockedExchange(&g_eye, (n / hold) & 1);
    }

    if (!InterlockedCompareExchange(&g_sbsOn, 0, 0) &&
        !InterlockedCompareExchange(&g_doubleOn, 0, 0))
        InterlockedExchange(&g_viewRotDone, 0);

    // Backbuffer size, needed to recognise full-screen viewports for the split.
    { GLint vp[4]; glGetIntegerv(GL_VIEWPORT, vp);
      if (vp[2] > 0 && vp[3] > 0 && !InterlockedCompareExchange(&g_splitActive,0,0))
        { g_fullW = vp[2]; g_fullH = vp[3]; } }

    if (InterlockedCompareExchange(&g_sbsOn, 0, 0)) { GpuCollect(); GpuBlitMark(0); }

    if (InterlockedCompareExchange(&g_sbsOn, 0, 0)) {
        // Capture what was just rendered, THEN composite. Order matters: the
        // composite overwrites framebuffer 0, and capturing after it would feed
        // the split back into itself.
        // THE CAPTURE MUST RUN UNDER XR TOO. This used to sit in the else of
        // the CompositeMirror test, so with a session live AND alternating mode
        // on -- the default after F10 -- the render loop skipped CaptureEye
        // (because g_altEyes is set) and the swap hook skipped this (because XR
        // was ready). Nothing wrote the eye textures at all: both eyes kept
        // showing whatever was captured before F7, which is why swapping the
        // halves changed nothing and why the per-eye offset produced a uniform
        // shift instead of parallax. Capture FIRST, then composite.
        if (InterlockedCompareExchange(&g_altEyes, 0, 0) && ResolveFboFns()
        && g_eyeFbo[0] && g_eyeFbo[1]) {
        // Framebuffer 0 now holds the finished frame for THIS eye, post included.
        int e = (int)(InterlockedCompareExchange(&g_frame,0,0) & 1);
        p_BindFramebuffer(GL_READ_FB_, 0);
        glReadBuffer(GL_BACK);          // required when reading the default FB;
                                        // omitting this is what hung the driver
        p_BindFramebuffer(GL_DRAW_FB_, g_eyeFbo[e]);
        p_BlitFramebuffer(0, 0, g_fullW, g_fullH, 0, 0, g_eyeW, g_eyeH,
                          GL_COLOR_BUFFER_BIT, GL_LINEAR);
        p_BindFramebuffer(GL_FB_, 0);
        InterlockedExchange(&g_captured, 3);
        InterlockedIncrement(&g_altCaptures);
    }
    if (InterlockedCompareExchange(&g_xrOn, 0, 0) && g_xr.Ready())
            CompositeMirror();  // headset owns the eyes; mirror one to the monitor
        else
            CompositeSideBySide();
        GpuBlitMark(1);
    }

    DriveHeldBody();

    Marker();
    Keys();

    // Drive the XR frame loop from the game's own frame boundary. The game has
    // just finished drawing into the default framebuffer, so that is what gets
    // sent to both eyes for now.
    if (InterlockedCompareExchange(&g_xrOn, 0, 0)) {
        // d_Render normally acquires the frame so the pose is current. Fall
        // back to acquiring here only if it did not run this frame (menus,
        // loading screens) -- otherwise a second xrWaitFrame would stall and
        // the frame counts would not pair with EndFrame.
        bool begun = InterlockedExchange(&g_xrFrameBegun, 0) != 0;
        if (!begun) begun = g_xr.BeginFrame();
        if (begun) {
            if (!InterlockedExchange(&g_hzLogged, 1)) {
                float hz = g_xr.DisplayRefreshHz();
                int sw = 0, sh = 0; g_xr.SwapchainSize(&sw, &sh);
                Log("");
                Log(">>> HEADSET CALIBRATION (read from the runtime, nothing assumed)");
                Log("    per-eye resolution : %dx%d", sw, sh);
                Log("    refresh rate       : %.1f Hz", hz);
                Log("    per-eye FOV        : %.1f x %.1f deg",
                    (g_xr.View(0).fov.angleRight - g_xr.View(0).fov.angleLeft)*57.2957795f,
                    (g_xr.View(0).fov.angleUp    - g_xr.View(0).fov.angleDown)*57.2957795f);
                if (hz > 1.0f) {
                    float ratio = hz / 60.0f;
                    if (fabsf(ratio - floorf(ratio + 0.5f)) > 0.02f)
                        Log("    the game runs at 60 fps and %.1f/60 = %.2f is not a whole"
                            " number, so frames repeat unevenly -- that is the head-turn"
                            " jitter. Press K to uncap and let the headset set the pace.",
                            hz, ratio);
                    else
                        Log("    %.1f/60 = %.0f exactly, so the cadence is even and 60 fps"
                            " should look smooth here.", hz, ratio);
                }
                Log("");
            }
            if (!g_xrFovLogged) {
                g_xrFovLogged = true;
                const xrs::EyeView& l = g_xr.View(0);
                const xrs::EyeView& r = g_xr.View(1);
                Log("");
                Log("OpenXR per-eye FOV (radians, asymmetric as expected):");
                Log("  left  L%.4f R%.4f U%.4f D%.4f",
                    l.fov.angleLeft, l.fov.angleRight, l.fov.angleUp, l.fov.angleDown);
                Log("  right L%.4f R%.4f U%.4f D%.4f",
                    r.fov.angleLeft, r.fov.angleRight, r.fov.angleUp, r.fov.angleDown);
                Log("  swapchain %dx%d per eye", g_xr.Width(0), g_xr.Height(0));
    {   // Publish it for the graphics-init hook. SOMA only reads the resolution
        // when graphics (re)initialises, so this applies on the NEXT init --
        // change any video setting, or relaunch with the mod already injected.
        int sw = 0, sh = 0;
        if (g_xr.SwapchainSize(&sw, &sh) && sw > 0 && sh > 0) {
            InterlockedExchange(&g_nativeW, sw);
            InterlockedExchange(&g_nativeH, sh);
            LONG cw = InterlockedCompareExchange(&g_vpW, 0, 0);
            LONG ch = InterlockedCompareExchange(&g_vpH, 0, 0);
            if (cw != sw || ch != sh)
                Log("  NATIVE RESOLUTION armed: %dx%d. SOMA is currently rendering"
                    " %ldx%ld, so the image is being rescaled. Change any video"
                    " setting in the options menu to force a graphics re-init and"
                    " it will render at the headset's own resolution.",
                    sw, sh, cw, ch);
        }
    }
                Log("  these now drive PerspectiveOffAxis directly");
            }
            // With stereo running, send each eye its OWN captured texture.
            // Without it, both eyes get the same framebuffer (mono in VR).
            if (InterlockedCompareExchange(&g_sbsOn, 0, 0) &&
                InterlockedCompareExchange(&g_captured, 0, 0) == 3 && g_eyeFbo[0]) {
                g_xr.SubmitEye(0, g_eyeFbo[0], g_eyeW, g_eyeH);
                g_xr.SubmitEye(1, g_eyeFbo[1], g_eyeW, g_eyeH);
                if (!InterlockedExchange(&g_xrStereoLogged, 1))
                    Log("OpenXR: submitting per-eye textures (%dx%d each) -- true stereo",
                        g_eyeW, g_eyeH);
            } else {
                GLint vp[4]; glGetIntegerv(GL_VIEWPORT, vp);
                g_xr.SubmitEye(0, 0, vp[2], vp[3]);
                g_xr.SubmitEye(1, 0, vp[2], vp[3]);
                if (!InterlockedExchange(&g_xrMonoLogged, 1))
                    Log("OpenXR: both eyes receiving the same image (turn F10 on for stereo)");
            }
        }
        g_xr.EndFrame();
    }

    // Re-arm: debug registers are per-thread, and threads created after the
    // initial arming would otherwise write the field unwatched. Cheap at this
    // interval, and it also reports if the field has drifted without a hit,
    // which would mean the writer is on a thread we never caught.
    if (g_watchSize && g_llSelfWatch && (n % 300) == 0) {
        static volatile LONG s_lastW = 0;
        int cw = *(volatile int*)((char*)g_llSelfWatch + 0x10);
        LONG prev = InterlockedExchange(&s_lastW, cw);
        if (prev != 0 && prev != cw && InterlockedCompareExchange(&g_watchHits,0,0) == 0)
            Log(">>> the size changed %ld -> %d with NO watch hit. The writer is"
                " on a thread that was not armed, or writes 8 bytes at once from"
                " an address we are not covering.", prev, cw);
        ArmWatchAllThreads((char*)g_llSelfWatch + 0x10);
    }

    if ((n % 600) == 0) {
        LONG c = InterlockedExchange(&g_calls, 0), s = InterlockedExchange(&g_subbed, 0);
        LONG l = InterlockedExchange(&g_subL, 0), r = InterlockedExchange(&g_subR, 0);
        LONG dc = InterlockedExchange(&g_dblCount, 0);
        LONG nr = InterlockedExchange(&g_nestedRenders, 0);
        if (dc) Log("[frame %ld] double renders %ld (%.2f per frame), nested %ld"
                    " (reflections, not doubled)", n, dc, dc/600.0f, nr);
        if (g_timedFrames > 0 && g_qpcFreq &&
            !InterlockedCompareExchange(&g_sbsOn, 0, 0)) {
            double ms = 1000.0 / (double)g_qpcFreq;
            double frame = (double)g_frameTicks / g_timedFrames * ms;
            Log("           CPU: frame %.2f ms (%.0f fps)  <-- BASELINE, stereo off",
                frame, 1000.0/frame);
            g_frameTicks = 0; g_passTicks[0] = g_passTicks[1] = 0; g_timedFrames = 0;
        }
        if (g_timedFrames > 0 && g_qpcFreq) {
            double ms = 1000.0 / (double)g_qpcFreq;
            double frame = (double)g_frameTicks / g_timedFrames * ms;
            double p0 = (double)g_passTicks[0] / g_timedFrames * ms;
            double p1 = (double)g_passTicks[1] / g_timedFrames * ms;
            Log("           CPU: frame %.2f ms (%.0f fps)%s | submit pass0 %.2f pass1 %.2f ms",
                frame, 1000.0/frame,
                (frame > 16.0 && frame < 17.4) ? "  <-- 60Hz VSYNC, not a real limit" : "",
                p0, p1);
            if (g_gpuSamples > 0) {
                double gp0 = g_gpuPass0 / g_gpuSamples, gp1 = g_gpuPass1 / g_gpuSamples;
                Log("           GPU: pass0 %.2f ms | pass1 %.2f ms | both %.2f ms"
                    " (%ld samples)", gp0, gp1, gp0 + gp1, g_gpuSamples);
                if (gp0 > 0.01)
                    Log("                pass1/pass0 = %.0f%% (pass0 usually reads short:"
                        " its commands overlap the previous frame's tail)", 100.0*gp1/gp0);
                if (g_gpuBlitSamples > 0)
                    Log("                my capture + composite: %.2f ms  (4 blits at %dx%d)",
                        g_gpuBlitMs / g_gpuBlitSamples, g_fullW, g_fullH);
                bool capped = (frame > 16.0 && frame < 17.4) ||
                              (frame > 11.0 && frame < 11.4) ||
                              (frame > 8.0  && frame < 8.6);
                if (capped)
                    Log("                => scene costs %.2f ms GPU; frame is VSYNC-CAPPED at"
                        " %.2f ms, so ~%.2f ms of headroom remains", gp0 + gp1, frame,
                        frame - (gp0 + gp1));
                else
                    Log("                => passes %.2f ms of a %.2f ms frame (%.0f%%);"
                        " %.2f ms elsewhere", gp0 + gp1, frame,
                        100.0*(gp0+gp1)/frame, frame - (gp0+gp1));
                g_gpuPass0 = g_gpuPass1 = 0; g_gpuSamples = 0;
                g_gpuBlitMs = 0; g_gpuBlitSamples = 0;
            }
            g_frameTicks = 0; g_passTicks[0] = g_passTicks[1] = 0; g_timedFrames = 0;
        }
        LONG pm = InterlockedExchange(&g_passMain, 0);
        LONG ra = InterlockedExchange(&g_rejAspect, 0);
        LONG rn = InterlockedExchange(&g_rejNear, 0);
        if (InterlockedCompareExchange(&g_handDraw, 0, 0)) {
            LONG dc = InterlockedExchange(&g_drawHandCalls, 0);
            LONG dd = InterlockedExchange(&g_drawHandDrawn, 0);
            Log("           HAND MARKERS: DrawHands reached %ld times, %ld cubes drawn%s",
                dc, dd, (dc == 0) ? "   <-- never called; the render hook is missing"
                      : (dd == 0) ? "   <-- called but drew nothing; GL init failed" : "");
        }
        if (InterlockedCompareExchange(&g_physScan, 0, 0)) {
            LONG pc = InterlockedExchange(&g_physCalls, 0);
            g_physStepBodies = g_seenBodyCount; g_seenBodyCount = 0;
            EnterCriticalSection(&g_physLock);
            LONG sc = InterlockedExchange(&g_setForceCalls, 0);
            // AddForce calls per second / calls per step gives the step rate.
            static LONGLONG lastPhysTick = 0;
            static long lastPhysCalls = 0;
            double physRate = 0.0;
            LONGLONG nowT = Now();
            if (lastPhysTick && g_qpcFreq && g_physStepBodies > 0) {
                double secs = (double)(nowT - lastPhysTick) / (double)g_qpcFreq;
                if (secs > 0.01) physRate = (double)pc / (double)g_physStepBodies / secs;
            }
            lastPhysTick = nowT; lastPhysCalls = pc;
            Log("           PHYSICS: %ld AddForce + %ld SetForce | %ld calls had ANY"
                " horizontal force", pc, sc, g_forcedBodies);
            if (physRate > 1.0)
                Log("             physics ~%.0f steps/sec (bodies seen per step: %ld)",
                    physRate, g_physStepBodies);
            if (g_bestBody) {
                float pos[3] = {0,0,0}, mass = 0, ix=0, iy=0, iz=0;
                if (p_NewtonGetMatrix) { float m[16]; p_NewtonGetMatrix(g_bestBody, m);
                                         pos[0]=m[12]; pos[1]=m[13]; pos[2]=m[14]; }
                if (p_NewtonGetMass) p_NewtonGetMass(g_bestBody, &mass, &ix, &iy, &iz);
                Log("             strongest horizontal: body %p  %.1f N horiz, %.1f N vert",
                    g_bestBody, g_bestHoriz, g_bestVert);
                Log("               mass %.2f kg, at (%.2f %.2f %.2f)%s", mass,
                    pos[0], pos[1], pos[2],
                    (g_bestHoriz > 2.0f) ? "   <-- candidate for the held object" : "");
            } else {
                Log("             no body received ANY horizontal force this window.");
                Log("             If you were carrying something, the grab does not go");
                Log("             through NewtonBodyAddForce at all.");
            }
            if (g_contactGrip && g_heldBody)
                Log("             grip: object %.2fx%.2fx%.2f m, r=%.2f, finger curls "
                    "%.2f %.2f %.2f %.2f %.2f",
                    g_lastObjExtent[0], g_lastObjExtent[1], g_lastObjExtent[2],
                    g_lastObjRadius,
                    g_fingerCurl[1][0], g_fingerCurl[1][1], g_fingerCurl[1][2],
                    g_fingerCurl[1][3], g_fingerCurl[1][4]);
            if (g_gripFramesHeld || g_gripFramesFree) {
                Log("           GRIP: %ld frames with an object, %ld without,"
                    " %ld finger contacts", g_gripFramesHeld, g_gripFramesFree,
                    g_gripContacts);
                if (g_gripFramesHeld)
                    Log("             last object %.3fx%.3fx%.3f m, r=%.3f;"
                        " index tip %.3f m from centre; AABB centre is %.3f m"
                        " from the body%s",
                        g_lastObjExtent[0], g_lastObjExtent[1], g_lastObjExtent[2],
                        g_lastObjRadius, g_lastTipDist, g_aabbOffset,
                        (g_aabbOffset > 0.3f)
                          ? "   <-- AABB READ IS WRONG, not a big object" : "");
                if (g_gripFramesHeld) {
                    float th = sqrtf((g_dbgTip[0]-g_dbgHand[0])*(g_dbgTip[0]-g_dbgHand[0])
                                   + (g_dbgTip[1]-g_dbgHand[1])*(g_dbgTip[1]-g_dbgHand[1])
                                   + (g_dbgTip[2]-g_dbgHand[2])*(g_dbgTip[2]-g_dbgHand[2]));
                    float ho = sqrtf((g_dbgHand[0]-g_dbgObj[0])*(g_dbgHand[0]-g_dbgObj[0])
                                   + (g_dbgHand[1]-g_dbgObj[1])*(g_dbgHand[1]-g_dbgObj[1])
                                   + (g_dbgHand[2]-g_dbgObj[2])*(g_dbgHand[2]-g_dbgObj[2]));
                    Log("             hand at (%.2f %.2f %.2f), object at (%.2f %.2f %.2f),"
                        " tip at (%.2f %.2f %.2f)",
                        g_dbgHand[0],g_dbgHand[1],g_dbgHand[2],
                        g_dbgObj[0],g_dbgObj[1],g_dbgObj[2],
                        g_dbgTip[0],g_dbgTip[1],g_dbgTip[2]);
                    // Full profile, sampled without an early exit.
                    int best = 0;
                    for (int k = 1; k < 6; ++k)
                        if (g_curlProfile[k] < g_curlProfile[best]) best = k;
                    Log("             index tip vs curl 0.0-1.0: %.3f %.3f %.3f %.3f"
                        " %.3f %.3f m (closest at curl %.1f, r=%.3f)",
                        g_curlProfile[0], g_curlProfile[1], g_curlProfile[2],
                        g_curlProfile[3], g_curlProfile[4], g_curlProfile[5],
                        best/5.0f, g_lastObjRadius);
                    Log("             fingertip travels %.3f m from open to closed%s",
                        g_tipTravel,
                        (g_curlProfile[0] < g_lastObjRadius)
                          ? "   <-- object already touching at curl 0" : "");
                    Log("             tip is %.3f m from the hand origin; the RIGHT hand"
                        " is %.3f m from the object%s", th, ho,
                        (th > 0.3f) ? "   <-- TIP TRANSFORM IS WRONG"
                                    : (ho > 0.35f) ? "   <-- object too far to grip" : "");
                }
                Log("             curls %.2f %.2f %.2f %.2f %.2f%s",
                    g_lastCurls[0], g_lastCurls[1], g_lastCurls[2],
                    g_lastCurls[3], g_lastCurls[4],
                    (g_gripFramesHeld && g_gripContacts == 0)
                      ? "   <-- held but NO contact: fingertips never reach the object"
                      : "");
                g_gripFramesHeld = g_gripFramesFree = g_gripContacts = 0;
            }
            LONG hf = InterlockedExchange(&g_handForces, 0);
            if (hf) Log("             SYNTHETIC HAND: %ld forces substituted on body %p",
                        hf, g_heldBody);
            LONG vc = InterlockedExchange(&g_velCalls, 0);
            LONG mc = InterlockedExchange(&g_mtxCalls, 0);
            LONG vh = InterlockedExchange(&g_velOnHeld, 0);
            LONG mh = InterlockedExchange(&g_mtxOnHeld, 0);
            if (vc || mc)
                Log("             SetVelocity %ld (%ld on held), SetMatrix %ld (%ld on held)%s",
                    vc, vh, mc, mh,
                    (vh > 0) ? "   <-- velocity is being overridden, forces cannot win"
                             : (mh > 0) ? "   <-- position set directly, forces are ignored" : "");
            if (vh > 0) Log("             last velocity set on held body: (%.2f %.2f %.2f)",
                            g_lastVelSet[0], g_lastVelSet[1], g_lastVelSet[2]);
            LONG vs = InterlockedExchange(&g_velSubbed, 0);
            if (vs) {
                Log("             velocity substituted %ld times, latched body %p",
                    vs, g_heldBody);
                Log("             camera at (%.2f %.2f %.2f)%s", g_camWorld[0], g_camWorld[1],
                g_camWorld[2],
                (fabsf(g_camWorld[0]) < 1e-6f && fabsf(g_camWorld[2]) < 1e-6f)
                  ? "   <-- UNKNOWN, hand disabled" : "");
            Log("             distance to hand target: now %.2f m (%.2f-%.2f);"
                    " hand moving at %.2f m/s", g_handDist, g_handDistMin,
                    g_handDistMax, g_handSpeed);
                if (g_velSamples > 0) {
                    double cmd = g_cmdSpeedSum/g_velSamples, act = g_actSpeedSum/g_velSamples;
                    Log("             commanded %.2f m/s, body actually has %.2f m/s"
                        " (%.0f%% applied)", cmd, act,
                        cmd > 0.01 ? 100.0*act/cmd : 0.0);
                }
                if (g_sleepSamples > 0)
                    Log("             body asleep on %ld of %ld checks%s",
                        g_asleepCount, g_sleepSamples,
                        (g_asleepCount > g_sleepSamples/2)
                          ? "   <-- ASLEEP: velocity is ignored" : "");
                if (g_posChecks > 0)
                    Log("             body moved on %ld of %ld frames"
                        " (physics runs ~60/s, so a low ratio at high fps is expected)",
                        g_posMoved, g_posChecks);
                g_cmdSpeedSum = g_actSpeedSum = 0; g_velSamples = 0;
                g_sleepSamples = g_asleepCount = 0;
                g_posMoved = g_posChecks = 0;
                g_handDistMin = 1e9f; g_handDistMax = 0;
            }
            g_bestBody = nullptr; g_bestHoriz = 0; g_bestVert = 0;
            g_maxHorizAny = 0; g_forcedBodies = 0;
            LeaveCriticalSection(&g_physLock);
        }
        if (InterlockedCompareExchange(&g_uiHookOn, 0, 0)) {
            LONG c = InterlockedExchange(&g_smCalls, 0);
            LONG pr = InterlockedExchange(&g_smProj, 0);
            LONG orp = InterlockedExchange(&g_smOrtho, 0);
            LONG pe = InterlockedExchange(&g_smPersp, 0);
            Log("           SetMatrix: %ld calls, %ld were projections (%ld ortho, %ld perspective)%s",
                c, pr, orp, pe,
                (c == 0) ? "   <-- HOOK NOT FIRING, wrong function" : "");
            EnterCriticalSection(&g_orthoLock);
            for (int i = 0; i < 8 && g_smSeen[i].n; ++i) {
                Log("             perspective fovY %.2f aspect %.4f  x%ld", g_smSeen[i].fov,
                    g_smSeen[i].aspect, g_smSeen[i].n);
                g_smSeen[i].n = 0;
            }
            LeaveCriticalSection(&g_orthoLock);
        }
        if (InterlockedCompareExchange(&g_orthoCount, 0, 0)) {
            EnterCriticalSection(&g_orthoLock);
            Log("           ORTHOGRAPHIC projections (UI passes):");
            for (int i = 0; i < 8 && g_orthoSeen[i].n; ++i) {
                float w = g_orthoSeen[i].r - g_orthoSeen[i].l;
                float h = g_orthoSeen[i].t - g_orthoSeen[i].b;
                Log("             %.0f x %.0f units  (l %.0f r %.0f b %.0f t %.0f)  x%ld%s",
                    w, h, g_orthoSeen[i].l, g_orthoSeen[i].r,
                    g_orthoSeen[i].b, g_orthoSeen[i].t, g_orthoSeen[i].n,
                    (fabsf(w - 800.0f) < 50.0f) ? "   <-- looks like HPL's virtual GUI size"
                                                : "");
                g_orthoSeen[i].n = 0;
            }
            InterlockedExchange(&g_orthoCount, 0);
            LeaveCriticalSection(&g_orthoLock);
        }
        LONG ro = InterlockedExchange(&g_rotPassOnly, 0);
        LONG vr = InterlockedExchange(&g_viewRot, 0);
        if (vr) Log("           view rotations: %ld (%.2f per frame; expect ~2 in stereo)", vr, vr/600.0f);
        {
            {
                LONG n = InterlockedExchange(&g_frustSeenN, 0);
                if (n > 0) {
                    Log("           DISTINCT FRUSTA substituted this window: %ld%s", n,
                        (n > 2) ? "   <-- more than the camera; some of these are"
                                  " other passes that should keep their own projection"
                                : "");
                    for (LONG i = 0; i < n; ++i)
                        Log("             %p  arrived with fovY %.1f deg aspect %.3f,"
                            " substituted %ld times", g_frustSeen[i].ptr,
                            g_frustSeen[i].fovIn * 57.2957795f,
                            g_frustSeen[i].aspIn, g_frustSeen[i].hits);
                    memset((void*)g_frustSeen, 0, sizeof(g_frustSeen));
                }
            }
            {
                LONG fw = InterlockedExchange(&g_fieldsWritten, 0);
                LONG sk = InterlockedExchange(&g_skippedNonEye, 0);
                if (fw || sk)
                    Log("           FOV fields written on %ld frusta, %ld auxiliary"
                        " frusta left untouched (%.2f / %.2f per frame)",
                        fw, sk, fw/600.0f, sk/600.0f);
            }
            {
                LONG sk2 = InterlockedExchange(&g_substSkipped, 0);
                if (sk2) Log("           substitution SKIPPED %ld times (%.2f per frame)"
                             " -- the engine's own projection is being used",
                             sk2, sk2/600.0f);
            }
            {
                LONG lr = InterlockedExchange(&g_latchReused, 0);
                if (lr) Log("           head pose latched once per frame, reused by the"
                            " second eye %ld times (%.2f per frame) -- both eyes now"
                            " drawn from ONE sample", lr, lr/600.0f);
            }
            {
                LONG fw2 = InterlockedExchange(&g_frustumWidened, 0);
                if (fw2) Log("           FRUSTUM rebuilt at the headset FOV %ld times"
                             " (%.2f per frame) -- culling cone now matches the"
                             " projection", fw2, fw2/600.0f);
            }
            {
                LONG ch = InterlockedExchange(&g_camHookHits, 0);
                if (ch) Log("           CAMERA HOOK: head pose applied at the camera"
                            " %ld times (%.2f per frame) -- culling follows it",
                            ch, ch/600.0f);
            }
            {
                LONG pb = InterlockedExchange(&g_poseBeforeLightsHits, 0);
                if (pb) Log("           head pose applied before light setup:"
                            " %ld times (%.2f per frame)", pb, pb/600.0f);
            }
            {
                LONG sf = InterlockedExchange(&g_stalePosFixes, 0);
                LONG so = InterlockedCompareExchange(&g_stalePosOff, -1, -1);
                if (so >= 0)
                    Log("           stale camera position at renderer+0x%04lx"
                        " refreshed %ld times (%.2f per frame)%s", so, sf, sf/600.0f,
                        g_fixStalePos ? "" : "   [OFF -- press Q to enable]");
            }
            {
                LONG ls = InterlockedExchange(&g_lightSetupHits, 0);
                if (ls) Log("           light setup ran %ld times (%.2f per frame);"
                            " its cached view matrix %s the frustum's current view",
                            ls, ls/600.0f,
                            g_cacheMatches ? "MATCHES" : "DOES NOT MATCH");
            }
            LONG vpr = InterlockedExchange(&g_vpRefreshed, 0);
            LONG skp = InterlockedExchange(&g_skippedNonEye, 0);
            if (vpr) Log("           ViewProj rebuilt: %ld (%.2f per frame)",
                         vpr, vpr/600.0f);
            if (skp) Log("           left alone (shadow/reflection frusta): %ld"
                         " (%.2f per frame) -- these keep the engine's own"
                         " projection", skp, skp/600.0f);
        }
        {
            LONG er = InterlockedExchange(&g_earlyRot, 0);
            if (er || HeadPoseActive())
                Log("           rotation applied %s: %ld times (%.2f per frame)",
                    g_rotateEarly ? "BEFORE Render" : "inside SetProjectionMatrix",
                    er, er/600.0f);
        }
        {
            LONG xp = InterlockedExchange(&g_projXrPath, 0);
            LONG fp = InterlockedExchange(&g_projFallback, 0);
            LONG r1 = InterlockedExchange(&g_rejNotStereo, 0);
            LONG r2 = InterlockedExchange(&g_rejXrOff, 0);
            LONG r3 = InterlockedExchange(&g_rejNotReady, 0);
            LONG r4 = InterlockedExchange(&g_rejInvalid, 0);
            {
                LONG ac = InterlockedExchange(&g_altCaptures, 0);
                if (ac) Log("           alternating-eye captures: %ld (%.2f per frame,"
                            " so each eye refreshes at half the frame rate)",
                            ac, ac/600.0f);
            }
            if (xp > 0) {
                LONG vw = InterlockedCompareExchange(&g_vpW,0,0);
                LONG vh = InterlockedCompareExchange(&g_vpH,0,0);
                Log("           FOV: matrix gives %.1f x %.1f deg, headset wants"
                    " %.1f x %.1f%s", g_projFovH, g_projFovV, g_wantFovH, g_wantFovV,
                    (fabsf(g_projFovH-g_wantFovH) > 2.0f ||
                     fabsf(g_projFovV-g_wantFovV) > 2.0f)
                      ? "   <-- MISMATCH: the projection is not what the headset expects" : "");
                Log("             engine viewport during the eye pass: %ldx%ld"
                    " (aspect %.3f); swapchain %dx%d (aspect %.3f)",
                    vw, vh, vh ? (float)vw/(float)vh : 0.0f,
                    g_eyeW, g_eyeH, g_eyeH ? (float)g_eyeW/(float)g_eyeH : 0.0f);
            }
            if (xp || fp)
                Log("           PROJECTION: %ld via the headset FOV, %ld via the monitor"
                    " fallback%s", xp, fp,
                    (fp > 0 && xp == 0)
                      ? "   <-- ALL FALLBACK: the headset FOV is not being used" : "");
            if (r1 || r2 || r3 || r4)
                Log("             rejected: not-stereo %ld, xr-off %ld, not-ready %ld,"
                    " view-invalid %ld", r1, r2, r3, r4);
        }

        if (InterlockedCompareExchange(&g_xrOn, 0, 0) && g_xr.Ready()) {
            for (int e = 0; e < 2; ++e) {
                float* q = g_poseQ[e];
                // yaw/pitch/roll purely for reading; the code uses the quaternion
                float yaw   = atan2f(2*(q[3]*q[1] + q[0]*q[2]), 1 - 2*(q[1]*q[1] + q[0]*q[0]));
                float pitch = asinf(fmaxf(-1.f, fminf(1.f, 2*(q[3]*q[0] - q[1]*q[2]))));
                float roll  = atan2f(2*(q[3]*q[2] + q[0]*q[1]), 1 - 2*(q[0]*q[0] + q[2]*q[2]));
                Log("           eye %d pose q(%.3f %.3f %.3f %.3f) = yaw %.1f pitch %.1f"
                    " roll %.1f deg | pos(%.3f %.3f %.3f) | view fwd(%.3f %.3f %.3f)",
                    e, q[0],q[1],q[2],q[3],
                    yaw*57.2957795f, pitch*57.2957795f, roll*57.2957795f,
                    g_posePos[e][0], g_posePos[e][1], g_posePos[e][2],
                    g_poseFwd[e][0], g_poseFwd[e][1], g_poseFwd[e][2]);
            }
            float dq = 0;
            for (int i = 0; i < 4; ++i) dq += fabsf(g_poseQ[0][i] - g_poseQ[1][i]);
            // The eyes separate along the head's own right-vector, which is only
            // the world X axis when facing down Z. Measuring |dx| alone reported
            // 0.9-6.3 cm and sent three sessions hunting a pose-timing bug that
            // does not exist: the true magnitude is a steady 0.063 m.
            float sx = g_posePos[0][0]-g_posePos[1][0];
            float sy = g_posePos[0][1]-g_posePos[1][1];
            float sz = g_posePos[0][2]-g_posePos[1][2];
            float dp = sqrtf(sx*sx + sy*sy + sz*sz);
            float df = fabsf(g_poseFwd[0][0]-g_poseFwd[1][0])
                     + fabsf(g_poseFwd[0][1]-g_poseFwd[1][1])
                     + fabsf(g_poseFwd[0][2]-g_poseFwd[1][2]);
            if (df > 0.05f)
                Log("           WARNING: the two eyes' view directions differ by %.3f --"
                    " the head rotation is compounding between passes", df);
            {
                LONG h0 = InterlockedExchange(&g_dbgHits[0], 0);
                LONG h1 = InterlockedExchange(&g_dbgHits[1], 0);
                LONG rebuilds = InterlockedExchange(&g_forcedRebuilds, 0);
                LONG entered = InterlockedExchange(&g_camTransEntered, 0);
                LONG applied = InterlockedExchange(&g_camTransHits, 0);
                LONG verified = InterlockedExchange(&g_camTransVerified, 0);
                LONG verifyFailed = InterlockedExchange(&g_camTransVerifyFailed, 0);
                float maxVerifyError = g_camTransMaxError;
                g_camTransMaxError = 0.0f;
                LONG eyeOnly = InterlockedExchange(&g_frustumEyeOnlyHits, 0);
                LONG frustumSuppressed = InterlockedExchange(&g_frustumHeadSuppressed, 0);
                LONG cameraPosSuppressed = InterlockedExchange(&g_cameraPosHeadSuppressed, 0);

                Log("           forced view rebuilds: %ld (%.2f per frame --"
                    " should be ~2, one per eye pass)",
                    rebuilds, rebuilds/600.0f);
                Log("           HEAD WRITER CENSUS: camera+0x74 entered %ld, applied %ld;"
                    " frustum eye-only %ld; frustum head suppressed %ld;"
                    " camera-position head suppressed %ld",
                    entered, applied, eyeOnly, frustumSuppressed, cameraPosSuppressed);
                if (applied == 0)
                    Log("           *** DO NOT INTERPRET 6DOF BEHAVIOUR: the sole"
                        " camera+0x74 head writer had ZERO hits in this window.");
                if (eyeOnly == 0 || h0 == 0 || h1 == 0)
                    Log("           *** DO NOT INTERPRET STEREO: the per-pass eye-only"
                        " path did not execute for both eyes (eye0 %ld, eye1 %ld).", h0, h1);
                Log("           camera+0x74 write positive control: %ld verified, %ld"
                    " failed; last/max recovered-position error %.6f / %.6f m",
                    verified, verifyFailed, g_camTransLastError, maxVerifyError);
                Log("           view translation BEFORE our delta: %.3f %.3f %.3f",
                    g_dbgViewT[0], g_dbgViewT[1], g_dbgViewT[2]);
                Log("           HEAD raw XR d: %+.3f %+.3f %+.3f m | game-world w:"
                    " %+.3f %+.3f %+.3f m | matrix dt: %+.3f %+.3f %+.3f",
                    g_dbgHeadRaw[0], g_dbgHeadRaw[1], g_dbgHeadRaw[2],
                    g_dbgHead[0], g_dbgHead[1], g_dbgHead[2],
                    g_dbgHeadDeltaT[0], g_dbgHeadDeltaT[1], g_dbgHeadDeltaT[2]);
                Log("           EYE OFFSETS (frustum eye-only path): eye0 %+.4f m"
                    " (%ld hits) | eye1 %+.4f m (%ld hits); magnitudes %.4f / %.4f",
                    g_dbgOff[0], h0, g_dbgOff[1], h1, g_dbgMag[0], g_dbgMag[1]);
                Log("           ^ eye values are no longer shared with head"
                    " displacement. They must remain opposite and near 0.0315 m.");
            }
            Log("           world scale %.2f -- if the separation below does not"
                " track this, the scale is being applied to a path that does not"
                " run", g_worldScale);
            Log("           eyes differ: orientation %.4f (should be ~0),"
                " separation %.4f m, 3D (should be ~%.3f)%s",
                dq, dp, g_ipdMetres,
                (dq > 0.01f) ? "   <-- EYES HAVE DIFFERENT ORIENTATIONS" : "");
        }

        {   // A collapse in per-eye substitution is invisible in the numbers
            // above but ruins the stereo, so call it out directly.
            LONG l = InterlockedCompareExchange(&g_subL, 0, 0);
            LONG r = InterlockedCompareExchange(&g_subR, 0, 0);
            if ((l == 0) != (r == 0))
                Log("           WARNING: only one eye substituted (L %ld R %ld) --"
                    " the other is using the game's own projection", l, r);
        }
        if (pm) Log("           main-frustum matches: %ld (aspect %.5f near %.4f fovY %.3f)"
                    " | layout %s%s", pm, g_cam.aspect, g_cam.nearZ, g_cam.fovYDeg,
                    InterlockedCompareExchange(&g_frustumLayout,0,0)==2 ? "row-major" : "column-major",
                    ro ? "  | rotated: passed by pointer only, frustum left intact" : "");
        if (InterlockedCompareExchange(&g_sbsOn, 0, 0)) {
            Log("           capture targets %dx%d, composite %s", g_eyeW, g_eyeH,
                (g_eyeFbo[0] && p_BlitFramebuffer) ? "ready" : "NOT READY");
            LONG bf = InterlockedExchange(&g_bindFires, 0);
            LONG be = InterlockedExchange(&g_bindFiresExt, 0);
            Log("           glBindFramebuffer calls: core %ld, EXT %ld%s", bf, be,
                (bf == 0 && be == 0) ? "   <-- NEITHER hook fires, wrong entry point" : "");
            Log("           framebuffers bound during eye passes:");
            for (int i = 0; i < 10 && g_fboSeen[i].n; ++i) {
                Log("             FBO %-4u  x%ld%s", g_fboSeen[i].fb, g_fboSeen[i].n,
                    g_fboSeen[i].fb == 0 ? "   (default / screen)" : "   <-- offscreen target");
                g_fboSeen[i].n = 0;
            }
        }
        if (InterlockedCompareExchange(&g_sbsOn, 0, 0)) {
            EnterCriticalSection(&g_vpLock);
            Log("           split target %dx%d | viewports the engine set:", g_fullW, g_fullH);
            for (int i = 0; i < 12 && g_vpSeen[i].n; ++i) {
                Log("             %5dx%-5d  x%ld%s", g_vpSeen[i].w, g_vpSeen[i].h, g_vpSeen[i].n,
                    (g_vpSeen[i].w == g_fullW && g_vpSeen[i].h == g_fullH) ? "   <-- MATCHED, split applied" : "");
                g_vpSeen[i].n = 0;
            }
            LeaveCriticalSection(&g_vpLock);
        }
        if (c) Log("[frame %ld] SetProjectionMatrix %ld calls, %ld substituted | "
                   "stereo %s (left eye %ld, right eye %ld) | ipd %.0fmm"
                   " | applied translation term %.5f | eye hold %ld frames", n, c, s,
                   InterlockedCompareExchange(&g_stereoOn,0,0) ? "ON" : "off",
                   l, r, g_ipdMetres * 1000.0f,
                   (float)InterlockedCompareExchange(&g_appliedShift,0,0) / 1e6f,
                   InterlockedCompareExchange(&g_eyeHoldFrames,0,0));
    }
    return o_Swap(hdc);
}

// ------------------------------------------------------------------ startup
static DWORD WINAPI Init(LPVOID param) {
    InitializeCriticalSection(&g_lock);
    InitializeCriticalSection(&g_vpLock);
    InitializeCriticalSection(&g_orthoLock);
    InitializeCriticalSection(&g_physLock);
    OpenLog((HMODULE)param);
    Log("hpl3vr - build %s %s", __DATE__, __TIME__);
    Log("EXPERIMENT: SESSION5_SINGLE_HEAD_WRITER -- camera+0x74 owns head centre;"
        " frustum path is eye-only");
    Log("log: %s", g_logPath);
    Log("");
    Log("Keys:  F2  = engine hook (enable this first)");
    Log("       F10 = native stereo, side by side     F11 = swap halves");
    Log("       F1 / F4 = IPD down / up               F8  = FOV pulse (sanity check)");

    Log("       F12 = head pose sweep (full 6DOF: yaw, pitch, roll, position)");
    Log("       F6  = census every projection the engine submits (not just UI)");
    Log("       F5  = physics force scan (VR hands groundwork)");
    Log("       T   = find SOMA's logic-timer step   Y = set it to 90 Hz");
    Log("       F3  = synthetic hand: held object follows a point, not your view");
    Log("       F9  = draw Simon's hand meshes in the world");
    Log("       G / H = close / open the fingers   J = curl axis   K = curl direction");
    Log("       N   = contact grip (fingers stop where they touch the object)");
    Log("       M   = rotate the view before Render vs during it (culling test)");
    Log("       V   = freeze the head pose (isolates rotation from projection)");
    Log("       ;   = HOLD the F12 sweep at its current angle   \' = creep forward");
    Log("       [ / ] = camera-level yaw test, 30 deg steps (works with F2 alone)");
    Log("       \\   = camera hook on/off (A/B against the old frustum path)");
    Log("       Q   = refresh the stale camera position the lighting reads");
    Log("       W   = apply the head pose before light setup (lighting test)");
    Log("       E   = projection substitution on/off (diagnostic, camera hook only)");
    Log("       R   = fit the render viewport to the projection (object scale)");
    Log("       X   = cycle which framebuffer the eyes are captured from");
    Log("       Z   = one eye per frame WITH post processing vs two without");
    Log("       C   = print the addresses to breakpoint (finding the camera)");
    Log("       , / . = cull margin down / up (fixes objects vanishing when you");
    Log("               look away from where the game camera points)");
    Log("       U / I = thumb axis / direction    O / [ = thumb wrap across palm");
    Log("       L / R / B = adjust left hand, right hand, or both");
    Log("       1/2 3/4 5/6 = rotate selected hand X / Y / Z   P = print values");
    Log("       7/8 = reach, 9/0 = spread, +/- = height  (numpad also works)");
    Log("       F7  = start OpenXR session (headset + runtime required)");
    Log("");
    Log("Retired: F1 alternating-eye (superseded by F10), F9 double-BeginRendering");
    Log("(rested on a misreading), F5/F6 (only affected F1).");
    Log("");
    Log("Nothing is reported until F2 installs the engine hook -- silence before");
    Log("that is expected, not a fault. A marker square should appear at once:");
    Log("  GREEN = injected and the frame hook is live");
    Log("  BLUE  = F2 on, engine hook installed");
    Log("  RED / BLUE alternating = F1 stereo (blends to purple at high fps)");
    Log("");

    if (MH_Initialize() != MH_OK) { Log("MinHook init failed"); return 0; }
    HMODULE gl = GetModuleHandleA("opengl32.dll");
    void* swap = gl ? (void*)GetProcAddress(gl, "wglSwapBuffers") : nullptr;
    if (swap && MH_CreateHook(swap, (void*)d_Swap, (void**)&o_Swap) == MH_OK) {
        MH_EnableHook(swap);
        Log("wglSwapBuffers hooked");
    } else Log("FAILED to hook wglSwapBuffers");

    // The render resolution is read ONCE, during graphics init, which happens
    // long before F2. So these two must be hooked here at DLL load -- installing
    // them with the rest of the engine hooks was always too late, even when the
    // DLL was injected at launch.
    {
        HMODULE exe = GetModuleHandleA(NULL);
        void* ll = (void*)((char*)exe + 0x442E00);
        void* ss = (void*)((char*)exe + 0x43EFE0);
        bool d = (MH_CreateHook(ss, (void*)d_SetScreenSize, (void**)&o_SetScreenSize) == MH_OK)
                 && (MH_EnableHook(ss) == MH_OK);
        if (!d) o_SetScreenSize = nullptr;
        Log("SetScreenSize (RVA 0x43EFE0) hook %s -- the write watch identified"
            " this as what reverts the size and the scissor", d ? "ok" : "FAILED");
        void* gi = (void*)((char*)exe + 0x210FF0);
        bool a = (MH_CreateHook(ll, (void*)d_LowLevelInit, (void**)&o_LowLevelInit) == MH_OK)
                 && (MH_EnableHook(ll) == MH_OK);
        bool b = (MH_CreateHook(gi, (void*)d_GraphicsInit, (void**)&o_GraphicsInit) == MH_OK)
                 && (MH_EnableHook(gi) == MH_OK);
        if (!a) o_LowLevelInit = nullptr;
        if (!b) o_GraphicsInit = nullptr;
        HMODULE sdl = GetModuleHandleA("SDL2.dll");
        if (!sdl) sdl = LoadLibraryA("SDL2.dll");
        if (sdl) {
            void* cw = (void*)GetProcAddress(sdl, "SDL_CreateWindow");
            p_SDL_SetWindowSize = (PFN_SDLSetWindowSize)
                                  (void*)GetProcAddress(sdl, "SDL_SetWindowSize");
            if (cw && MH_CreateHook(cw, (void*)d_SDL_CreateWindow,
                                    (void**)&o_SDL_CreateWindow) == MH_OK
                   && MH_EnableHook(cw) == MH_OK)
                Log("SDL_CreateWindow hooked -- the window can now exceed the"
                    " desktop size, which is what caps vertical resolution");
            else
                o_SDL_CreateWindow = nullptr;
        }
        Log("graphics-init hooks installed AT LOAD (lowlevel %s, cGraphics %s)"
            " -- needed because the resolution is read before F2 is ever pressed",
            a ? "ok" : "FAILED", b ? "ok" : "FAILED");
        if (a || b) {
            int pw = 0, ph = 0;
            if (ProbeHeadsetResolution(&pw, &ph)) {
                InterlockedExchange(&g_nativeW, pw);
                InterlockedExchange(&g_nativeH, ph);
                Log("headset probed at load: %dx%d per eye -- graphics init will"
                    " use this instead of the configured resolution", pw, ph);
            } else {
                Log("headset probe found nothing yet (runtime not up?) -- the game"
                    " will start at its configured resolution");
            }
        }
    }
    return 0;
}

BOOL APIENTRY DllMain(HMODULE h, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(h);
        g_selfModule = h;
        CreateThread(nullptr, 0, Init, (LPVOID)h, 0, nullptr);
    }
    return TRUE;
}
