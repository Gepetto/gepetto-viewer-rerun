{
  description = "Provide a `Client` class to visualize data with Rerun";

  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    rerun-update = {
      url = "https://github.com/NixOS/nixpkgs/pull/358093.patch";
      flake = false;
    };
  };

  outputs =
    inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      systems = inputs.nixpkgs.lib.systems.flakeExposed;
      perSystem =
        { pkgs, self', system, ... }:
        {
          _module.args.pkgs = import ./patched-nixpkgs.nix {
            inherit (inputs) nixpkgs;
            inherit system;
            patches = [ inputs.rerun-update ];
          };
          apps.default = {
            type = "app";
            program = pkgs.python3.withPackages (_: [ self'.packages.default ]);
          };
          devShells.default = pkgs.mkShell { inputsFrom = [ self'.packages.default ]; };
          packages = {
            default = self'.packages.gepetto-viewer-rerun;
            gepetto-viewer-rerun = pkgs.python3Packages.callPackage ./. { };
          };
        };
    };
}
