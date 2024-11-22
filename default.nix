{
  lib,
  buildPythonPackage,
  setuptools,
  rerun-sdk,
}:

buildPythonPackage {
  pname = "gepetto-viewer-rerun";
  version = "0.1.0-unstable-2024-11-20";
  pyproject = true;

  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions [
      ./examples
      ./pyproject.toml
      ./README.md
      ./src
      ./uv.lock
    ];
  };

  build-system = [
    setuptools
  ];

  dependencies = [
    rerun-sdk
  ];

  pythonImportsCheck = [
    "gepetto_viewer_rerun"
  ];

  meta = {
    description = "Provide a `Client` class to visualize data with Rerun";
    homepage = "https://github.com/gepetto/gepetto-viewer-rerun";
    license = lib.licenses.bsd2;
    maintainers = with lib.maintainers; [ nim65s ];
  };
}
