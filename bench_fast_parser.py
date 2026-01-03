import os
import sys
import timeit

# Ensure we can import spack
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib", "spack"))


def benchmark_fast_parser():
    specs = [
        "libelf@0.8.13",
        "libelf@0.8.13:0.8.19",
        "libelf@0.8.13,0.8.15,0.8.19",
        "libelf@git.master",
        "libelf@git.a0b1c2d3e4f5a0b1c2d3e4f5a0b1c2d3e4f5a0b1",
        "libelf@git.master=1.2.3",
        "libelf@1.2.3 +variant arch=x86_64",
        "hdf5@1.10.7+cxx~fortran+hl+mpi+shared api=default build_type=RelWithDebInfo",
        "libelf^foo",
        "libelf^foo^bar",
        "libelf^foo%bar",
        "libelf%gcc",
        "hdf5+mpi ^mpich@3.0.4",
    ]

    print(f"{'Spec':<60} | {'Original (ms)':<15} | {'Fast (ms)':<15}")
    print("-" * 95)

    # Warmup
    setup_warmup = "from spack.spec_parser import SpecParser; s = 'libelf'"
    test_warmup = "SpecParser(s).next_spec()"
    timeit.timeit(test_warmup, setup=setup_warmup, number=100)
    timeit.timeit(
        "FastSpecParser('libelf').next_spec()",
        setup="from spack.spec_parser import FastSpecParser",
        number=100,
    )

    for spec_str in specs:
        # Benchmark Original
        setup_orig = f"from spack.spec_parser import SpecParser; s = '{spec_str}'"
        test_orig = "SpecParser(s).next_spec()"
        time_orig = timeit.timeit(test_orig, setup=setup_orig, number=1000) * 1000

        # Benchmark Fast
        setup_fast = f"from spack.spec_parser import FastSpecParser; s = '{spec_str}'"
        test_fast = "FastSpecParser(s).next_spec()"
        time_fast = timeit.timeit(test_fast, setup=setup_fast, number=1000) * 1000

        print(f"{spec_str:<60} | {time_orig:<15.4f} | {time_fast:<15.4f}")


if __name__ == "__main__":
    benchmark_fast_parser()
