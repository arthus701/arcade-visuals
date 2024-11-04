{
  description = "Audio Process Component of Arcade-Visuals";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs?ref=nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
    in
    {
      devShells.x86_64-linux.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          rustup
          rustfmt
          crate2nix
          pkg-config
          alsa-lib
          cmake
          openssl
          xorg.libxcb
          reuse
          udev
        ];
      };

    };
}
