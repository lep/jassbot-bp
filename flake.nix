{
    inputs = {
	nixpkgs.url = "github:NixOS/nixpkgs";
	flake-utils.url = "github:numtide/flake-utils";
    };

    outputs = { self, nixpkgs, flake-utils }:
	flake-utils.lib.eachDefaultSystem (system:
	    let pkgs = import nixpkgs { inherit system; };
		py = pkgs.python3Packages;

		module = py.buildPythonPackage {
		    pname = "jassbot";
		    version = "1.0.0";
		    src = self;

		    doCheck = false;

		    propagatedBuildInputs = [
			py.markdown
			py.flask
		    ];
		};
		mypython = pkgs.python3.withPackages(_: [ module ]);
	    in {
		packages.jassbot-bp = module;
		defaultPackage = module;
		devShell = pkgs.mkShell {
		    buildInputs = [
			pkgs.python3
			module
		    ];
		};
	    }
	);
}

