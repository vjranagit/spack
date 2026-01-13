import os
import sys
import timeit

from spack.spec import Spec

# Add spack to the python path
spack_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(spack_root, "lib"))


def benchmark_spec_init():
    specs = [
        "python",
        "python@3.11.0",
        "python@3.11.0%gcc@12.2.0",
        "python+debug~shared",
        "python ^openssl@3.0.0",
        "python@3.11.0%gcc@12.2.0+debug~shared ^openssl@3.0.0%gcc@12.2.0",
        "mvapich2@2.3%gcc@8.3.0+cuda cuda_arch=70 ^cuda@10.1.243%gcc@8.3.0",
        "trilinos@12.12.1%gcc@8.3.0+dtk+intrepid2+shards+teuchos gotype=long_long",
        # From test_spec_syntax.py
        "mvapich",
        "@2.7",
        "+foo",
        "platform=test",
        "%intel",
        "^zlib",
        "openmpi ^hwloc ^libunwind",
        "foo @2.0 %bar@1.0",
        "openmpi ^hwloc@1.2e6:1.4b7-rc3",
        "mvapich_foo ^_openmpi@1.2:1.4,1.6+debug~qt_4 %intel@12.1 ^stackwalker@8.1_1e",
        "yaml-cpp@0.1.8%intel@12.1 ^boost@3.1.4",
        "builtin.yaml-cpp@0.1.8%gcc@7.2.0 ^boost@3.1.4",
        "x ^y@foo ^y+bar",
        "develop-branch-version@git.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=develop+var1+var2",
        "%gcc@:8.4.3,10.2.1:12.1.0",
        "cflags=='-O3 -g'",
        "^[virtuals=mpi] openmpi",
        "^[deptypes=link,build] zlib",
        "zlib %c,cxx=gcc@14.1",
    ]

    print(f"{'Spec String':<100} | {'Time (us)':<10}")
    print("-" * 113)

    # Warmup
    Spec("python")

    for s in specs:
        # Warmup
        Spec(s)
        # Run 1000 times
        t = timeit.timeit(lambda: Spec(s), number=1000)
        # Average time in microseconds
        avg_time_us = (t / 1000) * 1e6
        print(f"{s:<100} | {avg_time_us:<10.2f}")


if __name__ == "__main__":
    benchmark_spec_init()
