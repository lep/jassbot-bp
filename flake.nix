{
    inputs = {
	nixpkgs.url = "github:NixOS/nixpkgs";
	flake-utils.url = "github:numtide/flake-utils";
	jassdoc.url = "github:lep/jassdoc";
	jassdoc.inputs.nixpkgs.follows = "nixpkgs";
	jassdoc.inputs.flake-utils.follows = "flake-utils";
    };

    outputs = { self, nixpkgs, flake-utils, jassdoc }:
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
		appWrapper = {
		    type = "app";
		    program = toString (pkgs.writeScript "run-jassbot" ''
			export FLASK_JASSDB="${jassdoc.packages.${system}.jassdoc}/jass.db";
			${mypython}/bin/python3 -m ${module.pname}
		    '');
		};

	    in {
		apps.jassbot = appWrapper;
		apps.default = appWrapper;

		packages.jassbot = module;
		defaultPackage = module;

		devShell = pkgs.mkShell {
		    buildInputs = [
			pkgs.python3
			module
		    ];
		    FLASK_JASSDB="${jassdoc.packages.${system}.jassdoc}/jass.db";
		};
	    }
	);
}

