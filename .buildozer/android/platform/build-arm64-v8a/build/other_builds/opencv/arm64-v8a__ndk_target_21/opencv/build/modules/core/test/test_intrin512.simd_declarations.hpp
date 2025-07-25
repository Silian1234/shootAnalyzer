#define CV_CPU_SIMD_FILENAME "/root/shootAnalyzer/.buildozer/android/platform/build-arm64-v8a/build/other_builds/opencv/arm64-v8a__ndk_target_21/opencv/modules/core/test/test_intrin512.simd.hpp"
#define CV_CPU_DISPATCH_MODE AVX512_SKX
#include "opencv2/core/private/cv_cpu_include_simd_declarations.hpp"

#define CV_CPU_DISPATCH_MODES_ALL AVX512_SKX, BASELINE

#undef CV_CPU_SIMD_FILENAME
