# MIDI files for 200 Drum Machine Patterns + 260 Drum Machine Patterns

The code builds MIDI versions of the drum machine patterns from the books *200 Drum Machine Patterns* and *260 Drum Machine Patterns* by __René-Pierre Bardet__.

It uses as input digital versions of the patterns taken from:
- https://github.com/montoyamoraga/drum-machine-patterns (*200 Drum Machine Patterns* only)
- https://github.com/stephenhandley/DrumMachinePatterns (patterns from both books)

## Install

The tool needs Python >= 3.7.

- Clone the project locally
- Run `pip install -r requirements.txt`

## Run

- `mkdir input`
- `mkdir output`
- Download one of the following file:
  - https://raw.githubusercontent.com/montoyamoraga/drum-machine-patterns/main/README.md 
  - https://raw.githubusercontent.com/stephenhandley/DrumMachinePatterns/master/Sources/DrumMachinePatterns200/Patterns.json 
  - https://raw.githubusercontent.com/stephenhandley/DrumMachinePatterns/master/Sources/DrumMachinePatterns260/Patterns.json 
- Copy the file to the input folder
- Run with : `python -m dmpmid.cli -i input/README.md -o output`
    - Or use `input/Patterns.json` depending on the downloaded files
- The MIDI files will be generated in the `output` folder

The generated MIDI follows the *General MIDI* convention: All instruments are on channel 10 and the notes used for the drum instruments are the ones listed on https://github.com/montoyamoraga/drum-machine-patterns

You may have to shift the notes to a different drum pad in your DAW if your drum kit does not follow this convention. Alternatively, you could edit the code in this project to map the instrument to a different MIDI note that fits your kit (by changing the numeric values in the `NOTE_MAPPING` global variable), then relaunch the tool to generate the custom MIDI files.

## Downloads

Pre-generated MIDI files can be downloaded in the release section of this project.
