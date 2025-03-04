# GHPython Componentizer

> A github action to make Grasshopper development 164% <sup><small>[1]</small></sup> version-control friendlier and 82% more pleasant.

Imagine if you could write your grasshopper components in Python code in an actual text file with a powerful editor?
Git wouldn't hate you and life would be so much beautiful. 🐵

Well, here's an action for you then! 🦸‍♀️

---

## Usage

### Usage from Github Actions

The recommended way to use this tool is as a Github Action.
It needs to be run on a windows runner and IronPython/NuGet need to be pre-installed.

Copy the following workflow code into a `.github/workflows/main.yml` file in your repository.
Make sure you have the components definition (see below for details) stored in a source folder.
Replace the `source` and `target` to match your folder structure.

```yaml
on: [push]

jobs:
  build_ghuser_components:
    runs-on: windows-latest
    name: Build components
    steps:
      - uses: actions/checkout@v2
      - uses: NuGet/setup-nuget@v1.0.5
      - name: Install IronPython
        run: |
          choco install ironpython --version=2.7.8.1
      - uses: compas-dev/compas-actions.ghpython_components@v1
        with:
          source: examples
          target: build
```

Commit, push and enjoy! 🍿

### Usage on the command line

Alternatively, you can also use this tool directly from the command line.
Make sure to have IronPython installed and the `GH_IO.dll` assembly available.
Then start the script pointing it to a source and target folder, e.g.:

    ipy componentize.py examples build

Optionally, tag it with a version:

    ipy componentize.py examples build --version 0.1.2

## How to create components

1. Create a folder to contain your components
1. Each component goes into its own folder
1. The name of the folder determines the name of the `.ghuser` file created
1. Inside the component folder:
   1. Create a `metadata.json` file containing all required details of the component
   1. Add a lovely icon named `icon.png` (24x24)
   1. Add a `code.py` file with the Python script of the component
1. Use this action setting `source` and `target` folder inputs
1. Be happy 🎈

## Specification

### Icon

* Icon name should be `icon.png`
* Icon dimensions should be `24x24`

## Python code

* Supports both procedural and GH_Component SDK modes (see `isAdvancedMode` in metadata)
* Supports a small set of templated variables that can be used in code:
  * `{{version}}`: Gets replaced with the version, if specified in the command-line.
  * `{{name}}`: Gets replaced with the name of the component as defined in the metadata file.
  * `{{ghuser_name}}`: Gets replaced with the name of the `.ghuser` file being generated.

## Metadata

* `name`: Name of the component. Keep it short, single words are best.
* `nickname`: Abbreviation of the component. Keep it short, 1~5 character words are best.
* `category`: Category of the component. The category controls in which tab the component will end up.
* `subcategory`: Subcategory for this component. The subcategory controls in which panel the component will end up.
* `description`: **(optional)** Description of the component. Be succinct but clear.
* `exposure`: **(optional)** Controls where the component will be exposed. Defaults to `2` (primary). Accepts one of the following integer values:
  * `-1`:  Hidden. Do not expose the object anywhere.
  * `2`: Primary. Expose the object in the first section on the toolbar.
  * `4`: Secondary. Expose the object in the second section on the toolbar.
  * `8`: Expose the object in the third section on the toolbar.
  * `16`: Expose the object in the fourth section on the toolbar.
  * `32`: Expose the object in the fifth section on the toolbar.
  * `64`: Expose the object in the sixth section on the toolbar.
  * `128`: Expose the object in the seventh section on the toolbar.
* `instanceGuid`: **(optional)** Statically define a GUID for this instance. Defaults to a new Guid.
* `ghpython`
  * `hideOutput`: **(optional)** Defines whether to hide or not `out` output parameter. Defaults to `True`.
  * `hideInput`: **(optional)** Defines whether to hide or not the `code` input parameter. Defaults to `True`.
  * `isAdvancedMode`: **(optional)** Defines whether the script is in advanced mode (aka GH_Component SDK mode) or procedural mode. Defaults to `False`.
  * `marshalOutGuids`: **(optional)** Defines whether output Guids will be looked up or not. Defaults to `True`. Change to `False` to preserve output Guids.
  * `iconDisplay`: **(optional)** Defines whether to display the icon or not. Defaults to `0`.
    * `0` : Application setting
    * `1` : Text display
    * `2` : Icon display
  * `inputParameters`: List of input parameters.
    * `name`: Name of the input parameter.
    * `nickname`: **(optional)** Abbreviation of the input parameter. Defaults to the same as `name`.
    * `description`: **(optional)** Description of the input parameter.
    * `optional`: **(optional)** Defines whether the input parameter is optional or not. Defaults to `True`.
    * `allowTreeAccess`: **(optional)** Defines whether to allow tree access for this input parameter. Defaults to `True`.
    * `showTypeHints`: **(optional)** Defines whether to show type hints for this input parameter. Defaults to `True`.
    * `scriptParamAccess`: **(optional)** Defines access type of the parameter. Defaults to `item`. Accepts either integer value or string value.
      * `0` / `item`: item access
      * `1` / `list`: list access
      * `2` / `tree`: tree access
    * `wireDisplay`: **(optional)** Defines wire display type. Accepts either integer value or string value.
      * `0` / `default`: Wire display is controlled by the application settings.
      * `1` / `faint`: Wires are displayed faintly (thin and transparent) while the parameter is not selected.
      * `2` / `hidden`: Wires are not displayed at all while the parameter is not selected.
    * `typeHintID`: **(optional)** Defines the type hint of the input parameter. Defaults to `ghdoc`.
      Accepts either a Guid value or a string value. The following are the valid
      string values (their respective Guids are not listed here for readability):
      `none`, `ghdoc`, `float`, `bool`, `int`, `complex`, `str`, `datetime`, `guid`,
      `color`, `point`, `vector`, `plane`, `interval`, `uvinterval`, `box`, `transform`,
      `line`, `circle`, `arc`, `polyline`, `rectangle`, `curve`, `mesh`, `surface`, `subd`, `brep`.
  * `outputParameters`: List of output parameters.
    * `name`: Name of the output parameter.
    * `nickname`: **(optional)** Abbreviation of the output parameter. Defaults to the same as `name`.
    * `description`: **(optional)** Description of the output parameter.
    * `optional`: **(optional)** Defines whether the output parameter is optional or not. Defaults to `False`.

## Caveats

GHUser components have one important limitation: once used in a document, they forget who they are.
The don't know they were created out of a `ghuser` component, they will be simple GHPython components.
This has an important consequence: **if you update the `ghuser` components,
those already in use will NOT be automatically updated**.

## License

This package is maintained by Gramazio Kohler Research [@gramaziokohler](https://github.com/gramaziokohler)
and it is published under an [MIT License](LICENSE).

---
> <sup>[1] Like, totally scientifically proven. word.</sup>
