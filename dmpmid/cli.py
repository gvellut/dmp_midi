from dataclasses import dataclass
from io import StringIO
import json
from pathlib import Path
import re
from typing import Dict, List
import unicodedata

from addict import Dict as Addict
import click
from cmarkgfm import github_flavored_markdown_to_html as gfm
from lxml import etree
from mido import Message, MidiFile, MidiTrack


class UnrecognizedDocumentError(Exception):
    pass


@click.command()
@click.option(
    "-i",
    "--input",
    "input_file",
    help="Path to local README.md from montoyamoraga/drum-machine-patterns",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    help="Directory where to save the midi files",
    required=True,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option(
    "-b",
    "--base-velocity",
    "base_velocity",
    help="Base velocity",
    type=click.IntRange(0, 127),
    default=64,
)
@click.option(
    "-a",
    "--accent-velocity",
    "accent_velocity",
    help="Accent velocity",
    type=click.IntRange(0, 127),
    default=127,
)
def main(input_file, output_dir, base_velocity, accent_velocity):
    # 2 types of input : markdown or json depending on where it was downloaded
    if input_file.endswith(".md"):
        document = parse_gfm_document(input_file)
        patterns = list_patterns(document)
    elif input_file.endswith(".json"):
        patterns = extract_patterns_from_json(input_file)

    print(f"Found {len(patterns)} patterns")

    for pattern in patterns:
        to_midi(pattern, base_velocity, accent_velocity, output_dir)


@dataclass
class Event:
    absolute_time: int
    params: Dict


DRUM_CHANNEL = 10

# mapping of the Roland TR-09
NOTE_MAPPING = {
    "BD": 36,
    "RS": 37,
    "SD": 38,
    "CP": 39,
    "CH": 42,
    "LT": 43,
    "OH": 46,
    "MT": 47,
    "CY": 49,
    "HT": 50,
    "TM": 54,
    "CB": 56,
}

ACCENT_TRACK = "AC"

TICKS_PER_BEAT = 480


def to_midi(pattern: "Pattern", basic_velocity, accent_velocity, output_dir):
    time = 0
    # each note is a 1/16th
    delta = TICKS_PER_BEAT // 4

    events = []

    for i in range(pattern.length):
        if pattern.accent and pattern.accent.pattern[i]:
            velocity = accent_velocity
        else:
            velocity = basic_velocity

        for part in pattern.parts:
            if not part.pattern[i]:
                continue

            instrument = part.instrument
            # assume always a value
            note = NOTE_MAPPING[instrument]
            events.append(
                Event(time, {"type": "note_on", "note": note, "velocity": velocity})
            )
            # TODO time value ? will it be cut off ? check
            events.append(
                Event(
                    time + delta,
                    {"type": "note_off", "note": note, "velocity": velocity},
                )
            )

        time += delta

    events = sorted(events, key=lambda e: e.absolute_time)

    # single track midi file
    # TICKS_PER_BEAT same as  the default 480 so parameter not really necessary
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    track = MidiTrack()
    mid.tracks.append(track)

    time = 0
    for event in events:
        delta = event.absolute_time - time
        track.append(Message(**event.params, time=delta))
        time = event.absolute_time

    file_name = pattern.main
    if pattern.sub:
        file_name += f"_{pattern.sub}"
    file_name = to_safe_filename(file_name) + ".mid"
    file_path = Path(output_dir) / file_name

    mid.save(str(file_path))


@dataclass
class Pattern:
    main: str
    sub: str
    length: int
    accent: "Part"
    parts: List["Part"]


@dataclass
class Part:
    instrument: str
    pattern: List[bool]


def list_patterns(document):
    patterns = []

    main_part_title = "Patterns from the book"

    root = document.getroot()
    main_part_title_element = root.xpath(
        f".//h2[contains(text(), '{main_part_title}')]"
    )
    if len(main_part_title_element) == 0:
        raise UnrecognizedDocumentError(
            f"Could not find title with text '{main_part_title}' in input document"
        )

    main_part = main_part_title_element[0].getparent()
    for table in main_part.findall(".//table"):
        h3 = table.xpath("./preceding-sibling::h3")[-1]
        h4 = table.xpath("./preceding-sibling::h4")[-1]

        parts = parse_html_table(table)
        accent, instrument_tracks, length = analyze(parts)

        pattern = Pattern(h3.text, h4.text, length, accent, instrument_tracks)
        patterns.append(pattern)

    return patterns


def analyze(parts):
    accent = None
    instrument_tracks = []
    for i, part in enumerate(parts):
        # special case : not an instrument but change the velocity
        if part.instrument == ACCENT_TRACK:
            accent = part
        else:
            instrument_tracks.append(part)

    length = len(instrument_tracks[0].pattern)
    return accent, instrument_tracks, length


def parse_html_table(table):
    parts = []

    # ignore thead => always the numbers from 01 to 16  or 12
    table_rows = table.xpath(".//tbody/tr")
    for row in table_rows:
        part = []

        cells = row.xpath(".//td")
        for i, cell in enumerate(cells):
            if i == 0:
                # assume always a value
                instrument = cell.text.strip()
            else:
                is_beat = cell.text is not None and cell.text.strip() == "X"
                part.append(is_beat)

        parts.append(Part(instrument, part))

    return parts


def parse_gfm_document(text):
    with open(text, "r", encoding="utf-8") as f:
        html = gfm(f.read())
        rooted_xml = f"<doc>{html}</doc>"
        parser = etree.XMLParser(remove_blank_text=True)
        buffer = StringIO(rooted_xml)
        parsed_xml = etree.parse(buffer, parser)
        return parsed_xml


JSON_INSTRUMENT_MAPPING = {
    "BassDrum": "BD",
    "RimShot": "RS",
    "SnareDrum": "SD",
    "Clap": "CP",
    "ClosedHiHat": "CH",
    "LowTom": "LT",
    "OpenHiHat": "OH",
    "MediumTom": "MT",
    "Cymbal": "CY",
    "HighTom": "HT",
    "Tambourine": "TM",
    "Cowbell": "CB",
    "accent": "AC",
}

# X to refer to the convention in the README.md input file
JSON_NOTE_X = "Note"
JSON_ACCENT_X = "Accent"


def extract_patterns_from_json(input_file_path):
    with open(input_file_path, "r", encoding="utf-8") as f:
        data = [Addict(p) for p in json.load(f)]

    patterns = []
    for pattern in data:
        title = pattern.title

        accent = None
        instrument_tracks = []
        for instrument, track in pattern.tracks.items():
            instrument_code = JSON_INSTRUMENT_MAPPING[instrument]
            if instrument_code == ACCENT_TRACK:
                accent = Part(ACCENT_TRACK, [beat == JSON_ACCENT_X for beat in track])
            else:
                part = [beat == JSON_NOTE_X for beat in track]
                instrument_tracks.append(Part(instrument_code, part))

        length = len(instrument_tracks[0].pattern)

        # just a single level name for the JSON file
        pattern = Pattern(title, None, length, accent, instrument_tracks)
        patterns.append(pattern)

    return patterns


def to_safe_filename(name):
    name = "".join(
        c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn"
    )
    safe = re.sub(r"[^0-9a-zA-Z_]+", "_", name)
    safe = safe.strip("_")
    return safe


if __name__ == "__main__":
    main()
