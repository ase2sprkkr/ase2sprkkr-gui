# ASE2SPRKKR GUI

A PyQt6 desktop interface for creating and editing ASE structures, configuring
SPR-KKR calculations, and exploring calculation results through ASE2SPRKKR.

## Install

Install this beta alongside the matching released ASE2SPRKKR and KKRunner packages:

```bash
python -m pip install --pre ase2sprkkr-gui
```

## Run

```bash
ase2sprkkr-gui
ase2sprkkr-gui Fe.cif             # open a structure or potential file
ase2sprkkr-gui calculation.out    # open a SPR-KKR calculation result
ase2sprkkr-gui results/           # import output files from a directory
ase2sprkkr-gui --open-last        # open the latest existing recent structure
ase2sprkkr-gui --output data.txt  # disambiguate a nonstandard file extension
```

The same options work with `ase2sprkkr gui`. A positional filename is
interpreted as an output for `.out`/`.log`, input parameters for
`.inp`/`.in`, and otherwise as a structure. Use `--structure FILE`,
`--input FILE`, or `--output PATH` to choose explicitly. `--open-last`
uses the recent **structure** history (skipping files that no longer exist),
even when a calculation output was opened more recently.

The GUI requires the ASE2SPRKKR Python backend. Running actual SPR-KKR
calculations also requires a separately installed SPR-KKR executable.

## Development

Source: https://github.com/ase2sprkkr/ase2sprkkr-gui
