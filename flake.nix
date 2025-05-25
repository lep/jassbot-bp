{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
  };

  outputs = { self, nixpkgs, systems }:
    let
      eachSystem = nixpkgs.lib.genAttrs (import systems);
      jassbot-bp = pkgs:
        pkgs.python3Packages.buildPythonPackage {
          pname = "jassbot";
          version = "1.0.0";
          src = self;
          doCheck = false;

          propagatedBuildInputs = [
            pkgs.python3.pkgs.markdown
            pkgs.python3.pkgs.flask
            pkgs.python3.pkgs.requests
          ];
        };

      devShell = pkgs: pkgs.mkShell { buildInputs = [ (jassbot-bp pkgs) ]; };
    in {
      packages = eachSystem (system: rec {
        jassbot_bp = jassbot-bp (import nixpkgs { inherit system; });
        default = jassbot_bp;
      });

      devShells = eachSystem
        (system: { default = devShell (import nixpkgs { inherit system; }); });

    };
}

