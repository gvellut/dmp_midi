# MIDI files for 200 Drum Machine Patterns + 260 Drum Machine Patterns

The code builds MIDI versions of the drum machine patterns from the book *200 Drum Machine Patterns* and *260 Drum Machine Patterns* by __René-Pierre Bardet__.

See https://github.com/montoyamoraga/drum-machine-patterns for the input (README.md file) and https://github.com/stephenhandley/DrumMachinePatterns (.JSON file)

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

You may have to shift the notes to different notes in your DAW if your drum instrument does not follow this convention.

## Downloads

Pre-generated MIDI files can be downloaded in the release section of this project.

## TODO

Add patterns from https://github.com/stephenhandley/DrumMachinePatterns and the book 260 Drum Patterns