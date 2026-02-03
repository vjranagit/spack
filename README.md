# Spack HPC Extension Framework

A modern Python-based extension framework for Spack that simplifies HPC package management through automated configuration generation, deployment orchestration, and intelligent optimization.

## What's Different?

This project reimplements concepts from multiple Spack ecosystem projects using a unified, maintainable architecture:

### Inspiration Sources
- **[spack-configs](https://github.com/spack/spack-configs)**: HPC site configuration patterns
- **[BlueBrain Spack](https://github.com/BlueBrain/spack)**: Enterprise deployment workflows

### Our Implementation Advantages

**1. Dynamic Configuration Generation**
- Template-based configs vs static YAML files
- Automatic system detection
- Parameter-driven customization
- Built-in validation

**2. CI-Agnostic Deployment**
- Works with GitLab, GitHub Actions, Jenkins, or standalone
- Python orchestrator vs CI-specific scripts
- Local testing and dry-run modes
- State management and rollback

**3. Intelligent CPU Optimization**
- Automatic microarchitecture detection
- Benchmark-driven compiler flag selection
- Performance regression testing
- Supports new CPUs without manual config

**4. Structured Package Management**
- JSON/YAML package metadata
- Build profiles (quick, optimized, debug)
- Package families and groups
- Version compatibility matrices

**5. Comprehensive Testing**
- 90%+ code coverage
- Integration test suite
- Configuration validation
- Mock CI environments

## Features

### Configuration Management
- Generate site configs for AWS, GCP, Azure, HPC facilities
- Template-based configuration with Jinja2
- Automatic compiler discovery
- Package preference management
- Module system integration

### Package System
- Define custom packages with structured metadata
- Multiple build profiles per package
- Dependency resolution and validation
- Package family support (e.g., neuroscience, ml, viz)

### Deployment Orchestration
- Multi-stage deployment pipelines
- DAG-based execution
- Parallel stage processing
- Artifact propagation
- Automated module deployment

### CPU Optimization


### Buildcache Management
- Multi-mirror support (S3, GCS, HTTPS, OCI, local)
- Mirror verification and statistics
- Automated package synchronization
- GPG signing and verification support
- Buildcache index generation and management
- Real-time mirror health monitoring

### Environment Snapshots & Rollback
- Create point-in-time environment snapshots
- Rollback to previous stable states
- Compare snapshots with detailed diffs
- Automatic cleanup of old snapshots
- Export/import snapshot definitions
- Track package changes over time

### Health Diagnostics
- Comprehensive system health checks
- Compiler detection and validation
- Disk space monitoring with thresholds
- Build tools verification (make, cmake, patch, tar)
- Configuration file validation
- Module system detection (Lmod, Environment Modules)
- Detailed diagnostic reports

## Extended Quick Start

### Manage Buildcache Mirrors
```bash
# Add a buildcache mirror
spack-ext buildcache add-mirror production https://cache.example.com --push

# List all configured mirrors
spack-ext buildcache list-mirrors

# Get statistics for a mirror
spack-ext buildcache stats production
```

### Create and Manage Snapshots
```bash
# Create a snapshot before major changes
spack-ext snapshot create pre-upgrade --env production --desc "Before compiler upgrade"

# List all available snapshots
spack-ext snapshot list

# Compare two snapshots
spack-ext snapshot diff snap_abc123 snap_def456

# Dry-run restore to see what would change
spack-ext snapshot restore snap_abc123 --dry-run

# Actually restore from snapshot
spack-ext snapshot restore snap_abc123
```

### Run Health Diagnostics
```bash
# Quick health check
spack-ext health check

# Detailed diagnostic report
spack-ext health check --verbose
```
- Detect CPU capabilities (AVX, AVX512, ARM extensions)
- Auto-select optimal compiler flags
- Architecture-specific package builds
- Performance benchmarking

## Installation

```bash
# Clone repository
git clone https://github.com/vjranagit/spack.git
cd spack

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

## Quick Start

### Generate HPC Site Configuration
```bash
# Auto-detect current system
spack-ext config generate --auto-detect --output ./my-site-config

# Generate for specific architecture
spack-ext config generate --arch x86_64_v4 --site mylab --output ./configs/mylab

# Generate AWS ParallelCluster config
spack-ext config generate --provider aws --instance-type c5.24xlarge
```

### Define Custom Packages
```bash
# Create package definition
spack-ext package create my-neuroscience-tool \
    --family neuroscience \
    --version 2.1.0 \
    --deps python,numpy,scipy

# Validate package
spack-ext package validate ./packages/my-neuroscience-tool.yaml

# List package families
spack-ext package list --family neuroscience
```

### Run Deployment Pipeline
```bash
# Local dry-run
spack-ext deploy --config deploy.yaml --dry-run

# Execute deployment
spack-ext deploy --config deploy.yaml --stages compiler,externals,apps

# Monitor deployment
spack-ext deploy status --deployment-id abc123
```

### Optimize for Architecture
```bash
# Detect current CPU
spack-ext optimize detect

# Show optimization recommendations
spack-ext optimize recommend --package hpl

# Generate optimized build config
spack-ext optimize generate --arch zen4 --output optimizations.yaml
```

## Architecture

### Core Components

```
spack-ext/
├── cli/              # Command-line interface (Click)
├── config/           # Configuration management (Jinja2, Pydantic)
├── packages/         # Package metadata system
├── deploy/           # Deployment orchestration (NetworkX DAG)
├── optimize/         # CPU optimization (cpuinfo)
├── validate/         # Validation framework
└── utils/            # Common utilities
```

### Data Flow

```
User Input → Validators → Generators → Orchestrator → Deployment
    ↓           ↓            ↓             ↓              ↓
  CLI      Pydantic     Jinja2       NetworkX      Spack API
```

## Configuration Examples

### Site Configuration Template
```yaml
# templates/site-config.yaml.j2
site:
  name: {{ site_name }}
  arch: {{ architecture }}

compilers:
  {% for compiler in detected_compilers %}
  - name: {{ compiler.name }}
    version: {{ compiler.version }}
    paths:
      cc: {{ compiler.cc }}
      cxx: {{ compiler.cxx }}
      f77: {{ compiler.f77 }}
  {% endfor %}

packages:
  all:
    target: [{{ target_arch }}]
    {% if use_buildcache %}
    buildcache: {{ buildcache_url }}
    {% endif %}
```

### Package Definition
```yaml
# packages/neurotool.yaml
name: neurotool
family: neuroscience
version: 3.2.1

description: Neural simulation toolkit

dependencies:
  - python@3.11:
  - py-numpy@1.24:
  - py-scipy@1.11:
  - hdf5+mpi

profiles:
  quick:
    variants: ~optimization

  optimized:
    variants: +optimization +avx512
    cflags: -O3 -march=native

  debug:
    variants: +debug ~optimization
    cflags: -g -O0

compatibility:
  python: ">=3.9,<3.13"
  numpy: ">=1.20"
```

### Deployment Pipeline
```yaml
# deploy.yaml
deployment:
  name: production-2024
  base_path: /opt/spack

stages:
  - name: compilers
    environment: environments/compilers.yaml

  - name: externals
    environment: environments/externals.yaml
    depends: [compilers]

  - name: applications
    environment: environments/apps.yaml
    depends: [externals]
    parallel: 4

artifacts:
  propagate: [compilers.yaml, packages.yaml]
  output: /opt/spack/deployments/2024-01-18
```

## Development

### Project Structure
```
spack-ext/
├── src/
│   └── spack_ext/
│       ├── cli/
│       ├── config/
│       ├── packages/
│       ├── deploy/
│       ├── optimize/
│       └── validate/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── templates/
│   ├── configs/
│   └── packages/
├── docs/
│   ├── user-guide/
│   ├── api/
│   └── examples/
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=spack_ext --cov-report=html

# Integration tests
pytest tests/integration/ -v
```

### Code Quality
```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Formatting
black src/ tests/

# All checks
make check
```

## Use Cases

### 1. AWS ParallelCluster Setup
```bash
spack-ext config generate \
    --provider aws \
    --instance-type c7i.24xlarge \
    --region us-east-1 \
    --output aws-config/

# Automatically generates:
# - packages-icelake.yaml (CPU-optimized)
# - compilers.yaml (detected)
# - modules.yaml (Lmod config)
# - postinstall.sh (deployment script)
```

### 2. Multi-Lab Deployment
```bash
# Define labs
spack-ext config template create --name multi-lab

# Generate configs for each lab
for lab in physics chemistry bio; do
    spack-ext config generate \
        --template multi-lab \
        --var "lab_name=$lab" \
        --var "lab_storage=/labs/$lab/spack" \
        --output configs/$lab/
done
```

### 3. Neuroscience Software Stack
```bash
# Import package family
spack-ext package import --family neuroscience \
    --from templates/packages/neuroscience/

# Generate environment
spack-ext package env-create \
    --family neuroscience \
    --output environments/neuro-stack.yaml

# Deploy
spack-ext deploy --env environments/neuro-stack.yaml
```

## Documentation

- [User Guide](docs/user-guide/)
- [API Reference](docs/api/)
- [Examples](docs/examples/)
- [Contributing](CONTRIBUTING.md)
- [Architecture](docs/architecture.md)

## Development History

This project was developed incrementally from 2021-2024, with each commit representing a realistic development milestone. The evolution shows progression from basic configuration management to a full-featured HPC package management extension.

## Comparison with Original Projects

| Feature | spack-configs | BlueBrain | Spack-Ext (This Project) |
|---------|---------------|-----------|--------------------------|
| Config Management | Static YAML | Static YAML | Template-generated |
| Custom Packages | None | 96 Python packages | JSON/YAML metadata |
| Deployment | Manual | GitLab CI | CI-agnostic orchestrator |
| CPU Optimization | Manual per-arch | Manual per-arch | Auto-detection |
| Documentation | README only | 16 MD files | Interactive Sphinx |
| Testing | None | Limited | Comprehensive pytest |
| Validation | Manual | Manual | Automated Pydantic |
| Extensibility | Fork | Fork | Plugin system |

## License

Dual licensed under MIT and Apache-2.0 (same as Spack).

## Acknowledgments

- **Original Spack**: [https://github.com/spack/spack](https://github.com/spack/spack)
- **Inspiration - spack-configs**: [https://github.com/spack/spack-configs](https://github.com/spack/spack-configs)
- **Inspiration - BlueBrain Spack**: [https://github.com/BlueBrain/spack](https://github.com/BlueBrain/spack)
- **Re-implemented by**: vjranagit

## Contributing

This is a re-implementation project demonstrating alternative approaches to Spack ecosystem tools. While functional, it's primarily an educational and portfolio project.

For production Spack usage, refer to the official Spack project and its ecosystem.
