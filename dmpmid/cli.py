from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import re
from typing import Dict, List
import unicodedata

import click
from cmarkgfm import github_flavored_markdown_to_html as gfm
from lxml import etree
from mido import Message, MidiFile, MidiTrack


class UnrecognizedDocumentError(Exception):
    pass


DRUM_CHANNEL = 10

ACCENT_TRACK = "AC"

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
    "CB": 56,
}

TICKS_PER_BEAT = 480


@click.command()
@click.option(
    "-i",
    "--input",
    "input_readme",
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
def main(input_readme, output_dir, base_velocity, accent_velocity):
    document = parse_document(input_readme)
    patterns = list_patterns(document)
    for pattern in patterns:
        to_midi(pattern, base_velocity, accent_velocity, output_dir)


@dataclass
class Event:
    absolute_time: int
    params: Dict


def to_midi(pattern: "Pattern", basic_velocity, accent_velocity, output_dir):
    time = 0
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
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    time = 0
    for event in events:
        delta = event.absolute_time - time
        track.append(Message(**event.params, time=delta))
        time = event.absolute_time

    file_name = to_safe_filename(f"{pattern.main}_{pattern.sub}") + ".mid"
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


def parse_document(text):
    with open(text, "r", encoding="utf-8") as f:
        html = gfm(f.read())
        rooted_xml = f"<doc>{html}</doc>"
        parser = etree.XMLParser(remove_blank_text=True)
        buffer = StringIO(rooted_xml)
        parsed_xml = etree.parse(buffer, parser)
        return parsed_xml


def to_safe_filename(name):
    name = "".join(
        c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn"
    )
    safe = re.sub(r"[^0-9a-zA-Z_]+", "_", name)
    safe = safe.strip("_")
    return safe


if __name__ == "__main__":
    main()
