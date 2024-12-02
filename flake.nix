{
  description = "Provide a `Client` class to visualize data with Rerun";

  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      systems = inputs.nixpkgs.lib.systems.flakeExposed;
      perSystem =
        {
          pkgs,
          self',
          ...
        }:
        {
          apps.default = {
            type = "app";
            program = pkgs.python3.withPackages (_: [ self'.packages.default ]);
          };
          devShells.default = pkgs.mkShell {
            inputsFrom = [ self'.packages.default ];
            packages = [ pkgs.rerun ];
          };
          packages = {
            default = self'.packages.gepetto-viewer-rerun;
            gepetto-viewer-rerun = pkgs.python3Packages.callPackage ./. { };
          };
        };
    };
}
