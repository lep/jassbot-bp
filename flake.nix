{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
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

          nativeBuildInputs = [
            pkgs.minify
            pkgs.closurecompiler
            pkgs.moreutils
            pkgs.python3Packages.htmlmin
          ];

          postUnpack = ''
            minify --recursive -o source/jassbot/static/ source/jassbot/static/jassbot
            for template in source/jassbot/templates/jassbot/*.html.j2; do
              htmlmin --remove-comments --remove-empty-space "$template" "$template"
            done

            for js in source/jassbot/static/jassbot/*.js; do
              closure-compiler --js "$js" | sponge "$js"
            done
          '';

          pyproject = true;
          build-system = [ pkgs.python3.pkgs.setuptools ];

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

