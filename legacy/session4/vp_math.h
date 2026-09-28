#pragma once
#include <cmath>
#include <cstring>
namespace vpm {

// General 4x4 inverse (column-major, GL layout). Returns false if singular.
inline bool Invert4x4(const float* m, float* inv) {
    float t[16];
    t[0]  =  m[5]*m[10]*m[15] - m[5]*m[11]*m[14] - m[9]*m[6]*m[15]
           + m[9]*m[7]*m[14] + m[13]*m[6]*m[11] - m[13]*m[7]*m[10];
    t[4]  = -m[4]*m[10]*m[15] + m[4]*m[11]*m[14] + m[8]*m[6]*m[15]
           - m[8]*m[7]*m[14] - m[12]*m[6]*m[11] + m[12]*m[7]*m[10];
    t[8]  =  m[4]*m[9]*m[15] - m[4]*m[11]*m[13] - m[8]*m[5]*m[15]
           + m[8]*m[7]*m[13] + m[12]*m[5]*m[11] - m[12]*m[7]*m[9];
    t[12] = -m[4]*m[9]*m[14] + m[4]*m[10]*m[13] + m[8]*m[5]*m[14]
           - m[8]*m[6]*m[13] - m[12]*m[5]*m[10] + m[12]*m[6]*m[9];
    t[1]  = -m[1]*m[10]*m[15] + m[1]*m[11]*m[14] + m[9]*m[2]*m[15]
           - m[9]*m[3]*m[14] - m[13]*m[2]*m[11] + m[13]*m[3]*m[10];
    t[5]  =  m[0]*m[10]*m[15] - m[0]*m[11]*m[14] - m[8]*m[2]*m[15]
           + m[8]*m[3]*m[14] + m[12]*m[2]*m[11] - m[12]*m[3]*m[10];
    t[9]  = -m[0]*m[9]*m[15] + m[0]*m[11]*m[13] + m[8]*m[1]*m[15]
           - m[8]*m[3]*m[13] - m[12]*m[1]*m[11] + m[12]*m[3]*m[9];
    t[13] =  m[0]*m[9]*m[14] - m[0]*m[10]*m[13] - m[8]*m[1]*m[14]
           + m[8]*m[2]*m[13] + m[12]*m[1]*m[10] - m[12]*m[2]*m[9];
    t[2]  =  m[1]*m[6]*m[15] - m[1]*m[7]*m[14] - m[5]*m[2]*m[15]
           + m[5]*m[3]*m[14] + m[13]*m[2]*m[7] - m[13]*m[3]*m[6];
    t[6]  = -m[0]*m[6]*m[15] + m[0]*m[7]*m[14] + m[4]*m[2]*m[15]
           - m[4]*m[3]*m[14] - m[12]*m[2]*m[7] + m[12]*m[3]*m[6];
    t[10] =  m[0]*m[5]*m[15] - m[0]*m[7]*m[13] - m[4]*m[1]*m[15]
           + m[4]*m[3]*m[13] + m[12]*m[1]*m[7] - m[12]*m[3]*m[5];
    t[14] = -m[0]*m[5]*m[14] + m[0]*m[6]*m[13] + m[4]*m[1]*m[14]
           - m[4]*m[2]*m[13] - m[12]*m[1]*m[6] + m[12]*m[2]*m[5];
    t[3]  = -m[1]*m[6]*m[11] + m[1]*m[7]*m[10] + m[5]*m[2]*m[11]
           - m[5]*m[3]*m[10] - m[9]*m[2]*m[7] + m[9]*m[3]*m[6];
    t[7]  =  m[0]*m[6]*m[11] - m[0]*m[7]*m[10] - m[4]*m[2]*m[11]
           + m[4]*m[3]*m[10] + m[8]*m[2]*m[7] - m[8]*m[3]*m[6];
    t[11] = -m[0]*m[5]*m[11] + m[0]*m[7]*m[9] + m[4]*m[1]*m[11]
           - m[4]*m[3]*m[9] - m[8]*m[1]*m[7] + m[8]*m[3]*m[5];
    t[15] =  m[0]*m[5]*m[10] - m[0]*m[6]*m[9] - m[4]*m[1]*m[10]
           + m[4]*m[2]*m[9] + m[8]*m[1]*m[6] - m[8]*m[2]*m[5];

    float det = m[0]*t[0] + m[1]*t[4] + m[2]*t[8] + m[3]*t[12];
    if (fabsf(det) < 1e-20f) return false;
    det = 1.0f / det;
    for (int i = 0; i < 16; ++i) inv[i] = t[i] * det;
    return true;
}

// C = A * B, column-major
inline void Mul4x4(const float* A, const float* B, float* C) {
    for (int c = 0; c < 4; ++c)
        for (int r = 0; r < 4; ++r) {
            float s = 0;
            for (int k = 0; k < 4; ++k) s += A[k*4 + r] * B[c*4 + k];
            C[c*4 + r] = s;
        }
}

// Is V a rigid transform? Orthonormal 3x3 basis, bottom row (0,0,0,1).
inline bool IsRigid(const float* V, float tol = 0.01f) {
    if (fabsf(V[3]) > tol || fabsf(V[7]) > tol ||
        fabsf(V[11]) > tol || fabsf(V[15] - 1.0f) > tol) return false;
    for (int i = 0; i < 3; ++i) {
        float len = sqrtf(V[i*4]*V[i*4] + V[i*4+1]*V[i*4+1] + V[i*4+2]*V[i*4+2]);
        if (fabsf(len - 1.0f) > tol) return false;
    }
    // columns mutually perpendicular
    for (int a = 0; a < 3; ++a)
        for (int b = a + 1; b < 3; ++b) {
            float d = V[a*4]*V[b*4] + V[a*4+1]*V[b*4+1] + V[a*4+2]*V[b*4+2];
            if (fabsf(d) > tol) return false;
        }
    return true;
}

// THE DECISIVE TEST: given the known projection P, is M == P * V for a rigid V?
// If so, M is a view-projection matrix and V is the camera's view matrix.
inline bool IsViewProjectionOf(const float* M, const float* P, float* outView) {
    float Pinv[16];
    if (!Invert4x4(P, Pinv)) return false;
    float V[16];
    Mul4x4(Pinv, M, V);
    if (!IsRigid(V)) return false;
    if (outView) memcpy(outView, V, sizeof(V));
    return true;
}

// Camera world position from a view matrix: -R^T * t
inline void CameraPosFromView(const float* V, float* pos) {
    float tx = V[12], ty = V[13], tz = V[14];
    pos[0] = -(V[0]*tx + V[1]*ty + V[2]*tz);
    pos[1] = -(V[4]*tx + V[5]*ty + V[6]*tz);
    pos[2] = -(V[8]*tx + V[9]*ty + V[10]*tz);
}
} // namespace vpm

// ---------------------------------------------------------------------------
// Retarget any matrix of the form M = P*X onto a new projection: M' = P'*X,
// WITHOUT knowing X and WITHOUT inverting anything.
//
// With P (row-major rows) = [A 0 S 0; 0 B T 0; 0 0 Z C; 0 0 -1 0] and X affine
// (last row 0,0,0,1), the product rows satisfy:
//     M0 = A*X0 + S*X2      M2 = Z*X2 + (0,0,0,C)
//     M1 = B*X1 + T*X2      M3 = -X2
// so X2 = -M3, which gives an exact detection test:
//     M2 == -Z*M3 + (0,0,0,C)
// Four comparisons. This fires on per-object ModelViewProjection matrices,
// which is what actually draws the world -- ClassifyProjection only ever saw
// the bare P used by water and depth reconstruction.
namespace vpm {

struct ProjTerms { float A, B, S, T, Z, C; };

inline ProjTerms TermsOf(const float* P) {   // P is column-major
    ProjTerms t; t.A=P[0]; t.B=P[5]; t.S=P[8]; t.T=P[9]; t.Z=P[10]; t.C=P[14];
    return t;
}

// Row r of a column-major 4x4 lives at indices r, r+4, r+8, r+12.
inline bool IsProductOfProjection(const float* M, const ProjTerms& p, float rel = 0.01f) {
    if (fabsf(p.Z) < 1e-6f) return false;
    float scale = 0.0f;
    for (int c = 0; c < 4; ++c) scale = fmaxf(scale, fabsf(M[c*4 + 2]));
    if (scale < 1e-6f) return false;
    float tol = rel * fmaxf(scale, 1.0f);
    for (int c = 0; c < 4; ++c) {
        float want = -p.Z * M[c*4 + 3] + ((c == 3) ? p.C : 0.0f);
        if (fabsf(M[c*4 + 2] - want) > tol) return false;
    }
    return true;
}

// Rewrite M in place as P'*X. Returns false if M is not of the form P*X.
inline bool RetargetProduct(float* M, const float* P, const float* Pn, float rel = 0.01f) {
    ProjTerms p = TermsOf(P), q = TermsOf(Pn);
    if (fabsf(p.A) < 1e-9f || fabsf(p.B) < 1e-9f) return false;
    if (!IsProductOfProjection(M, p, rel)) return false;

    float out[16];
    for (int c = 0; c < 4; ++c) {
        float m0 = M[c*4 + 0], m1 = M[c*4 + 1], m3 = M[c*4 + 3];
        // X0 = (M0 + S*M3)/A ; X1 = (M1 + T*M3)/B ; X2 = -M3
        float x0 = (m0 + p.S * m3) / p.A;
        float x1 = (m1 + p.T * m3) / p.B;
        float x2 = -m3;
        out[c*4 + 0] = q.A * x0 + q.S * x2;
        out[c*4 + 1] = q.B * x1 + q.T * x2;
        out[c*4 + 2] = q.Z * x2 + ((c == 3) ? q.C : 0.0f);
        out[c*4 + 3] = m3;
    }
    memcpy(M, out, sizeof(out));
    return true;
}
} // namespace vpm

// ---------------------------------------------------------------------------
// Discriminating a genuine geometry matrix from an accidental match.
//
// IsProductOfProjection only inspects rows 2 and 3, which depend on Z and C --
// and those come from near/far alone. Every projection sharing the same clip
// planes passes, regardless of FOV or aspect. That is why v8 also clobbered
// shadow, reflection and fullscreen passes.
//
// Stronger test: recover X's 3x3 and check its COLUMNS are mutually
// perpendicular. For X = View*Model the 3x3 is R*S with R orthonormal and S a
// diagonal scale, so the columns stay perpendicular under non-uniform scale.
// If M came from a different projection, the recovered columns are wrongly
// scaled in x and y and orthogonality breaks.
//
// The same test gives idempotency for free: after retargeting, X recovered
// against P' is orthogonal and X recovered against P is not, so an
// already-patched matrix is recognisable and can be skipped.
namespace vpm {

inline bool RecoveredBasisIsOrthogonal(const float* M, const ProjTerms& p, float tol = 0.0005f) {
    if (fabsf(p.A) < 1e-9f || fabsf(p.B) < 1e-9f) return false;
    float col[3][3], len[3];
    for (int c = 0; c < 3; ++c) {
        float m0 = M[c*4 + 0], m1 = M[c*4 + 1], m3 = M[c*4 + 3];
        col[c][0] = (m0 + p.S * m3) / p.A;
        col[c][1] = (m1 + p.T * m3) / p.B;
        col[c][2] = -m3;
        len[c] = sqrtf(col[c][0]*col[c][0] + col[c][1]*col[c][1] + col[c][2]*col[c][2]);
        if (len[c] < 1e-6f) return false;
    }
    for (int a = 0; a < 3; ++a)
        for (int b = a + 1; b < 3; ++b) {
            float d = (col[a][0]*col[b][0] + col[a][1]*col[b][1] + col[a][2]*col[b][2])
                      / (len[a] * len[b]);
            if (fabsf(d) > tol) return false;
        }
    return true;
}

// Retarget only genuine geometry matrices, and never twice.
inline bool RetargetProductSafe(float* M, const float* P, const float* Pn,
                                float rel = 0.01f, float ortho = 0.0005f) {
    ProjTerms p = TermsOf(P), q = TermsOf(Pn);
    if (!IsProductOfProjection(M, p, rel))          return false;  // wrong clip planes
    if (RecoveredBasisIsOrthogonal(M, q, ortho))    return false;  // ALREADY retargeted
    if (!RecoveredBasisIsOrthogonal(M, p, ortho))   return false;  // not a view-model basis
    return RetargetProduct(M, P, Pn, rel);
}
} // namespace vpm

// ---------------------------------------------------------------------------
// Identify WHICH projection produced a matrix that passed the clip-plane test
// but failed the orthogonality test.
//
// The recovered columns are (m0/A', m1/B', -m3). Requiring them mutually
// perpendicular gives, for each of the 3 column pairs:
//     (m0a*m0b)/A'^2 + (m1a*m1b)/B'^2 + (m3a*m3b) = 0
// Three equations, two unknowns (1/A'^2, 1/B'^2) -> least squares. Recovering
// A' and B' gives the FOV and aspect of the pass that really wrote it, which
// turns "295 rejected matrices per frame" into a named list of render passes.
namespace vpm {

// Raw form: returns the A',B' terms rather than FOV/aspect, so the caller can
// rebuild the source projection and retarget it by the same ratio as the main
// camera -- keeping every pass mutually consistent.
inline bool InferSourceTerms(const float* M, float& outA, float& outB);

inline bool InferSourceProjection(const float* M, float& outFovYDeg, float& outAspect) {
    double U[3], V[3], W[3];
    int i = 0;
    for (int a = 0; a < 3; ++a)
        for (int b = a + 1; b < 3; ++b) {
            U[i] = (double)M[a*4+0] * M[b*4+0];
            V[i] = (double)M[a*4+1] * M[b*4+1];
            W[i] = (double)M[a*4+3] * M[b*4+3];
            ++i;
        }
    double a11=0, a12=0, a22=0, b1=0, b2=0;
    for (int k = 0; k < 3; ++k) {
        a11 += U[k]*U[k]; a12 += U[k]*V[k]; a22 += V[k]*V[k];
        b1  -= U[k]*W[k]; b2  -= V[k]*W[k];
    }
    // Conditioning matters: an axis-aligned object makes two of the three
    // equations collapse to 0=0, leaving the system underdetermined. Reject
    // those rather than returning a fabricated answer.
    double det = a11*a22 - a12*a12;
    double scale = (a11 + a22);
    if (scale < 1e-18 || fabs(det) < 1e-6 * scale * scale) return false;
    double p = (b1*a22 - a12*b2) / det;
    double q = (a11*b2 - b1*a12) / det;
    if (p <= 1e-12 || q <= 1e-12) return false;
    double Ap = 1.0 / sqrt(p), Bp = 1.0 / sqrt(q);
    if (!(Ap > 1e-6 && Bp > 1e-6) || Ap > 1e6 || Bp > 1e6) return false;
    outFovYDeg = (float)(2.0 * atan(1.0 / Bp) * 57.29577951);
    outAspect  = (float)(Bp / Ap);
    return true;
}

inline bool InferSourceTerms(const float* M, float& outA, float& outB) {
    float fov, asp;
    if (!InferSourceProjection(M, fov, asp)) return false;
    float B = 1.0f / tanf(fov * 0.5f * 0.01745329252f);
    outB = B;
    outA = B / asp;
    return (outA > 1e-6f && outB > 1e-6f);
}

// Retarget using explicit term sets rather than full matrices.
inline bool RetargetWithTerms(float* M, const ProjTerms& p, const ProjTerms& q) {
    if (fabsf(p.A) < 1e-9f || fabsf(p.B) < 1e-9f) return false;
    float out[16];
    for (int c = 0; c < 4; ++c) {
        float m0 = M[c*4+0], m1 = M[c*4+1], m3 = M[c*4+3];
        float x0 = (m0 + p.S * m3) / p.A;
        float x1 = (m1 + p.T * m3) / p.B;
        float x2 = -m3;
        out[c*4+0] = q.A * x0 + q.S * x2;
        out[c*4+1] = q.B * x1 + q.T * x2;
        out[c*4+2] = q.Z * x2 + ((c == 3) ? q.C : 0.0f);
        out[c*4+3] = m3;
    }
    memcpy(M, out, sizeof(out));
    return true;
}
} // namespace vpm
