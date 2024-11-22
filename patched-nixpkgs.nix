{ nixpkgs, patches, system, ...  }:
let
  super = import nixpkgs { inherit system; };
in
import (super.applyPatches {
  inherit patches;
  name = "patched nixpkgs";
  src = nixpkgs;
}) { inherit system; }
