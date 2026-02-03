"""Optimization engine implementation."""

import platform
from typing import Any, Optional

try:
    import cpuinfo
    HAS_CPUINFO = True
except ImportError:
    HAS_CPUINFO = False

from spack_ext.optimize.models import CPUInfo


class OptimizationEngine:
    """Manages CPU optimization and architecture detection."""

    def __init__(self) -> None:
        """Initialize optimization engine."""
        self.cpu_info: Optional[CPUInfo] = None

    def detect_cpu(self) -> CPUInfo:
        """Detect current CPU information.

        Returns:
            CPU information
        """
        if HAS_CPUINFO:
            info = cpuinfo.get_cpu_info()
            self.cpu_info = CPUInfo(
                brand=info.get("brand_raw", "Unknown"),
                arch=info.get("arch", platform.machine()),
                features=info.get("flags", []),
                vendor=info.get("vendor_id_raw", "Unknown"),
                family=info.get("family", ""),
            )
        else:
            # Fallback if py-cpuinfo not available
            self.cpu_info = CPUInfo(
                brand=platform.processor() or "Unknown",
                arch=platform.machine(),
                features=[],
                vendor="Unknown",
            )

        return self.cpu_info

    def get_recommendations(
        self,
        package: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get optimization recommendations.

        Args:
            package: Optional package name for specific recommendations

        Returns:
            Dictionary of recommendations
        """
        if not self.cpu_info:
            self.detect_cpu()

        recommendations: dict[str, Any] = {
            "target": self._recommend_target(),
            "compiler_flags": self._recommend_compiler_flags(),
            "variants": self._recommend_variants(package),
        }

        return recommendations

    def _recommend_target(self) -> str:
        """Recommend Spack target architecture.

        Returns:
            Recommended target string
        """
        if not self.cpu_info:
            return "x86_64"

        arch = self.cpu_info.arch.lower()

        if "x86_64" in arch or "amd64" in arch:
            # Check for AVX512
            if "avx512" in " ".join(self.cpu_info.features).lower():
                return "x86_64_v4"
            # Check for AVX2
            elif "avx2" in " ".join(self.cpu_info.features).lower():
                return "x86_64_v3"
            # Check for AVX
            elif "avx" in " ".join(self.cpu_info.features).lower():
                return "x86_64_v2"
            else:
                return "x86_64"

        elif "aarch64" in arch or "arm64" in arch:
            return "aarch64"

        return arch

    def _recommend_compiler_flags(self) -> dict[str, str]:
        """Recommend compiler flags based on CPU.

        Returns:
            Dictionary of compiler flags by type
        """
        flags: dict[str, str] = {}

        if not self.cpu_info:
            return flags

        # Base optimization
        flags["cflags"] = "-O3"
        flags["cxxflags"] = "-O3"
        flags["fflags"] = "-O3"

        # Add architecture-specific flags
        if "x86_64" in self.cpu_info.arch.lower():
            if "avx512" in " ".join(self.cpu_info.features).lower():
                flags["cflags"] += " -march=skylake-avx512"
                flags["cxxflags"] += " -march=skylake-avx512"
            elif "avx2" in " ".join(self.cpu_info.features).lower():
                flags["cflags"] += " -march=haswell"
                flags["cxxflags"] += " -march=haswell"

        return flags

    def _recommend_variants(self, package: Optional[str]) -> list[str]:
        """Recommend package variants based on CPU.

        Args:
            package: Package name

        Returns:
            List of recommended variants
        """
        variants: list[str] = []

        if not package:
            return variants

        # Generic optimization variant
        variants.append("+optimization")

        # AVX variants if supported
        if self.cpu_info:
            features_str = " ".join(self.cpu_info.features).lower()
            if "avx512" in features_str:
                variants.append("+avx512")
            elif "avx2" in features_str:
                variants.append("+avx2")

        return variants
