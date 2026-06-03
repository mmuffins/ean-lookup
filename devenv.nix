{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  env.GREET = "EAN Lookup";

  packages = with pkgs; [ ];
  cachix.pull = [ "nix-linter" ];

  languages.python = {
    enable = true;
    version = "3.14";

    venv.enable = true;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  enterShell = ''
    git --version
    python --version
    uv --version
  '';

}
