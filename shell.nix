{ pkgs ? import <nixpkgs> { } }:
let

  # set your python version here
  pythonPkg = pkgs.python310;
  pythonEnv = pythonPkg.withPackages (pythonPkgs:
    with pythonPkgs; [
      pip
      virtualenv
      # add nix python packages to install with python
    ]);
  lib-path = with pkgs; lib.makeLibraryPath [ libffi openssl stdenv.cc.cc ];

in pkgs.mkShell {
  packages = [ pkgs.bashInteractive ];
  buildInputs = with pkgs; [ pythonEnv ];
  shellHook = ''

    # Allow the use of wheels.
    SOURCE_DATE_EPOCH=$(date +%s)

    # Augment the dynamic linker path
    export "LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${lib-path}"

    # Create local venv
    VENV=$PWD/.venv
    if test ! -d $VENV; then
      virtualenv $VENV
    fi
    source $VENV/bin/activate
    export PYTHONPATH=$VENV/${pythonEnv.sitePackages}/:$PYTHONPATH
    export PATH=$VENV/bin:$PATH
  '';
}
