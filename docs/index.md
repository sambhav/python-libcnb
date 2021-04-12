# libcnb

Cloud Native Buildpack API bindings for Python


## Buildpack Interface

According to the CNB specification, the buildpack interface is composed of both
a detect and build phase. Each of these phases has a corresponding set of
libcnb primitives enable developers to easily implement a buildpack.

For more details see the [Cloud Native Buildpack Spec](https://buildpacks.io/docs/reference/spec/buildpack-api/)

### Detect Phase

The purpose of the detect phase is for buildpacks to declare dependencies
that are provided or required for the buildpack to execute. Implementing the
detect phase can be achieved by calling the `detect` function and providing a
`detector` callback to be invoked during that phase. Below is an example of
a simple detect phase that provides the "pip" dependency and requires the
"python" dependency.

```python linenums="1"
import libcnb


def detector(context: libcnb.DetectContext) -> libcnb.DetectResult:
    # The DetectContext includes an application_dir field that 
    # specifies the location of the application source code. 
    # This field can be combined with other paths to find and
    # inspect files included in the application source
    # code that is provided to the buildpack.
    has_requirements_file = (
        context.application_dir / "requirements.txt"
    ).exists()

    # Once the existence of a requirements.txt file has been confirmed,
    # the detect phase can return a result that indicates the provision
    # of pip and the requirement of python. As can be seen below,
    # the BuildPlanRequire may also include optional metadata information
    # such as the the version information for a given requirement.

    # By default the result is initialized to 
    # `passed` = False and has empty build plans
    result = libcnb.DetectResult()
    if has_requirements_file:
        result.passed = True
        # The detect phase provides pip and requires python.
        # When requiring python, it requests a version greater
        # than 3 as being acceptable by this buildpack.
        result.plans.append(
            libcnb.BuildPlan(
                provides=[
                    libcnb.BuildPlanProvide(name="pip"),
                ],
                requires=[
                    libcnb.BuildPlanRequire(
                        name="python",
                        metadata={"version": ">=3"},
                    ),
                ],
            )
        )
    return result


if __name__ == "__main__":
    # Calling libcnb.detect with the correct detector
    libcnb.detect(detector=detector)
```

### Build Phase

The purpose of the build phase is to perform the operation of providing
whatever dependencies were declared in the detect phase for the given
application code. Implementing the build phase can be achieved by calling
the `build` function and providing a `builder` callback to be invoked during
that phase. Below is an example that adds "pip" as a dependency to the
application source code.

```python linenums="1"
from pathlib import Path

import libcnb


def builder(context: libcnb.BuildContext) -> libcnb.BuildResult:
    # The BuildContext includes a BuildpackPlan with entries
    # that specify a requirement on a dependency provided by
    # the buildpack. This example simply chooses the first entry,
    # but more intelligent resolution processes can and likely
    # should be used in real implementations.
    entry = context.plan.entries[0]
    pip_version = entry.metadata["version"]

    # The BuildContext also provides a mechanism whereby
    # a layer can be created to store the results of a given
    # portion of the build process. This example creates a
    # layer called "pip" that will hold the pip cli.
    # We can also pass `load_all` to `get` set to `True`
    # to load all the existing layer metadata including env vars
    # and profile.d scripts if they exist.
    # Otherwise the layer is loaded only with the layer.metadata
    # hydrated from the <layer>.toml file.

    layer = context.layers.get("pip", load_all=False)

    # libcnb.Layer also provides some handy utilities to check
    # the expected metadata with the actual metadata and reset
    # the existing content from cache if it isn't what is expected.
    expected_metadata = {"pip_version": pip_version}
    if not layer.compare_metadata(expected_metadata, exact=False):
        # Clear all the existing content of the layer if the
        # version is not what we expect.
        layer.reset()
        layer.metadata = expected_metadata
        # We can also set env. variables
        layer.shared_env.default(
            "PIP_INDEX_URL", "http://mypypi.org/simple"
        )
        # Or add profile.d scripts
        layer.profile.add("pip.sh", "export PIP_USER=1")
        _install_pip(layer.path, pip_version)
    # We can also set the layer types and metadata easily
    layer.launch = True
    layer.build = True
    layer.cache = True
    # After the installation of the pip cli, a BuildResult
    # can be returned that included details of the executed
    # BuildpackPlan, the Layers to provide back to the lifecycle
    # and the Processes to execute at launch.
    
    # NOTE - Only the layers provided in the BuildResult will be exported.
    result = libcnb.BuildResult(
        layers=[layer],
        launch_metadata=libcnb.LaunchMetadata(
            labels=[libcnb.Label(key="pip-installed", value="true")],
        ),
    )
    result.launch_metadata.processes.append(
        libcnb.Process(
            type_="pip-installer",
            command="pip",
            args=["install"],
            direct=False,
        )
    )
    # We can also add a bom (Bill of Materials) to the output image.
    result.launch_metadata.bom.append(
        libcnb.BOMEntry(
            name="pip",
            metadata={"version": pip_version},
        )
    )
    result.build_metadata.bom.append(
        libcnb.BOMEntry(
            name="pip",
            metadata={"version": pip_version},
        )

    )
    return result


# Executes the process of installing the pip cli.
def _install_pip(layer_path: Path, version: str) -> None:
    # Implemention omitted.
    pass


if __name__ == "__main__":
    libcnb.build(builder)
```

### Run

Buildpacks can be created with a single entrypoint executable using the
`run` function. Here, you can combine both the `Detect` and `Build` phases
and `run` will ensure that the correct phase is called when the matching
executable is called by the Cloud Native Buildpack Lifecycle. Below is an
example that combines a simple `detect` and `build` into a single python script.

```python linenums="1"
import libcnb

def detector(context: libcnb.DetectContext) -> libcnb.DetectResult:
    return libcnb.DetectResult(passed=True)

def builder(context: libcnb.BuildContext) -> libcnb.BuildResult:
    return libcnb.BuildResult()

def main():
    libcnb.run(detector=detector, builder=detector)

if __name__ == "__main__":
    main()
```

### Summary

These examples show the very basics of what a buildpack implementation using
`libcnb` might entail. For more details, please consult the [API Reference](api.md) for
the types and functions declared within the `libcnb` package.
