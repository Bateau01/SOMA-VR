// hpl_vr_projection.h
//
// Off-axis (VR) projection matrix construction matching HPL's conventions,
// derived from cMath::MatrixPerspectiveProjection in the HPL2 source
// (HPL2/core/sources/math/Math.cpp:2616) and verified against it.
//
// Conventions, confirmed from HPL2:
//   - cMatrixf stores ROW-major, applied as column vectors (v' = M * v)
//   - OpenGL depth range [-1, 1]
//   - Right-handed eye space, looking down -Z
//
// Verified by vr_proj_test.cpp: reduces exactly to HPL's original for a
// symmetric frustum, maps asymmetric frustum bounds to NDC edges, and
// produces correct depth for both the finite and infinite far-plane paths.

#pragma once
#include <cmath>

namespace hpl3vr {

// 4x4 in HPL's row-major order. m[row][col].
struct Mat4 {
    float m[4][4];
};

// Column-major flat array, ready for glUniformMatrix4fv with transpose=GL_FALSE.
struct Mat4ColMajor {
    float v[16];
};

// Build an off-axis projection from OpenXR's XrFovf angles (radians).
// angleLeft and angleDown are negative; angleRight and angleUp positive.
//
// Pass the SAME near/far the engine is already using, unless you are
// deliberately pulling the near plane in for hands (~0.02 is reasonable;
// going much below that costs depth precision).
inline Mat4 PerspectiveOffAxis(float afNear, float afFar,
                               float afAngleLeft, float afAngleRight,
                               float afAngleUp,   float afAngleDown,
                               bool abInfFarPlane = false)
{
    const float fNear = afNear, fFar = afFar;
    const float fLeft   = std::tan(afAngleLeft)  * fNear;
    const float fRight  = std::tan(afAngleRight) * fNear;
    const float fTop    = std::tan(afAngleUp)    * fNear;
    const float fBottom = std::tan(afAngleDown)  * fNear;

    const float fA = (2.0f * fNear) / (fRight - fLeft);
    const float fB = (2.0f * fNear) / (fTop - fBottom);
    const float fS = (fRight + fLeft) / (fRight - fLeft);  // horizontal off-centre
    const float fT = (fTop + fBottom) / (fTop - fBottom);  // vertical off-centre
    const float fD = -1.0f;

    float fC, fZ;
    if (abInfFarPlane) { fC = -2.0f * fNear;                     fZ = -1.0f; }
    else               { fC = -(2.0f*fFar*fNear)/(fFar - fNear); fZ = -(fFar + fNear)/(fFar - fNear); }

    Mat4 r;
    r.m[0][0]=fA; r.m[0][1]=0;  r.m[0][2]=fS; r.m[0][3]=0;
    r.m[1][0]=0;  r.m[1][1]=fB; r.m[1][2]=fT; r.m[1][3]=0;
    r.m[2][0]=0;  r.m[2][1]=0;  r.m[2][2]=fZ; r.m[2][3]=fC;
    r.m[3][0]=0;  r.m[3][1]=0;  r.m[3][2]=fD; r.m[3][3]=0;
    return r;
}

// Transpose HPL row-major into the column-major layout GL expects.
inline Mat4ColMajor ToColMajor(const Mat4& a) {
    Mat4ColMajor o;
    for (int c = 0; c < 4; ++c)
        for (int r = 0; r < 4; ++r)
            o.v[c*4 + r] = a.m[r][c];
    return o;
}

// ---------------------------------------------------------------------------
// Inverse operation: recover human-readable parameters from a projection
// matrix found in memory. Used by the recon DLL to report what SOMA is
// actually using, and useful later for sanity-checking your own output.
// ---------------------------------------------------------------------------
struct ProjParams {
    float fNear, fFar;      // fFar is INFINITY for the infinite-far-plane path
    float fFovYDeg;         // vertical FOV in degrees
    float fAspect;
    float fShiftX, fShiftY; // 0,0 for a symmetric (flat-screen) frustum
    bool  bInfiniteFar;
};

// Decode from a column-major float[16] (GL memory layout).
inline ProjParams DecodeProjectionColMajor(const float* v) {
    const float fA = v[0], fB = v[5], fS = v[8], fT = v[9], fZ = v[10], fC = v[14];
    ProjParams p;
    p.bInfiniteFar = (std::fabs(fZ + 1.0f) < 1e-5f);
    p.fNear   = fC / (fZ - 1.0f);
    p.fFar    = p.bInfiniteFar ? INFINITY : fC / (fZ + 1.0f);
    p.fFovYDeg = 2.0f * std::atan(1.0f / fB) * 57.2957795f;
    p.fAspect = fB / fA;
    p.fShiftX = fS;
    p.fShiftY = fT;
    return p;
}

// Structural signature of a GL perspective projection matrix. The w-row being
// (0,0,-1,0) with m[15]==0 is distinctive: view, model, and normal matrices
// all have m[15]==1, and orthographic has m[11]==0. False positives are rare.
//
// Returns 0 for no match, 1 for column-major layout, 2 for row-major.
inline int ClassifyProjection(const float* v) {
    const float eps = 1e-4f;
    if (std::fabs(v[15]) > eps) return 0;              // not a projection
    const bool bColMajor = (std::fabs(v[11] + 1.0f) < eps) && (std::fabs(v[14]) > eps);
    const bool bRowMajor = (std::fabs(v[14] + 1.0f) < eps) && (std::fabs(v[11]) > eps);
    if (!bColMajor && !bRowMajor) return 0;
    if (std::fabs(v[0]) < eps || std::fabs(v[5]) < eps) return 0;  // degenerate
    return bColMajor ? 1 : 2;
}

inline void TransposeInPlace(float* v) {
    for (int r = 0; r < 4; ++r)
        for (int c = r + 1; c < 4; ++c) {
            float t = v[r*4+c]; v[r*4+c] = v[c*4+r]; v[c*4+r] = t;
        }
}

} // namespace hpl3vr
