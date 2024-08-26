{
  description = "arcade visuals";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachSystem
      [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ]
      (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in
        {
          devShells.default = pkgs.mkShell rec {
            nativeBuildInputs = with pkgs; [
              rustc
              cargo
              rustfmt
              clippy
              crate2nix
              pkg-config
            ];
            buildInputs = with pkgs; [
              libglvnd
              xorg.libX11
              xorg.libXcursor
              xorg.libXi
              xorg.libxcb
              libxkbcommon
              wayland
            ];
            LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath buildInputs;
          };
        });
}
