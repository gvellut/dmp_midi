# MIDI files for 200 Drum Machine Patterns

See https://github.com/montoyamoraga/drum-machine-patterns for the input (README.md file).

The code builds MIDI versions of the drum machine patterns from the book 200 Drum Machine Patterns by René-Pierre Bardet.

## Install

The tool needs Python >= 3.7.

- Clone the project locally
- Run `pip install -r requirements.txt`

## Run

- `mkdir input`
- `mkdir output`
- Download the file https://raw.githubusercontent.com/montoyamoraga/drum-machine-patterns/main/README.md and copy it to the `input` folder
- Run with : `python -m dmpmid.cli -i input -o output`
- The MIDI files will be generated in the `output` folder

The generated MIDI follows the *General MIDI* convention: All instruments are on channel 10 and the notes used for the drum instruments are the ones listed on https://github.com/montoyamoraga/drum-machine-patterns

You may have to shift the notes around if your drum instrument does not follow this convention.

## Downloads

Pre-generated MIDI files can be downloaded in the release section of this project.
