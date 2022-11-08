# @Author: anh-tuan.vu
# @Date:   2021-01-27 07:02:40
# @Last Modified by: rachmadani haryono
import dataclasses
import enum
import pathlib
import re
from os.path import exists, splitext

import click


def clean(filepath: str) -> str:
    """Clean up the content of a subtitle file (vtt) to a string

    Args:
        filepath (str): path to vtt file

    Returns:
        str: clean content
    """
    # read file content
    with open(filepath, encoding="utf-8") as fp:
        content = fp.read()

    # remove header & empty lines
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    lines = lines[1:] if lines[0].upper() == "WEBVTT" else lines

    # remove indexes
    lines = [lines[i] for i in range(len(lines)) if not lines[i].isdigit()]

    # remove timestamps
    pattern = r"^\d{2}:\d{2}:\d{2}.\d{3}.*\d{2}:\d{2}:\d{2}.\d{3}$"
    lines = [lines[i] for i in range(len(lines)) if not re.match(pattern, lines[i])]

    content = " ".join(lines)
    # remove duplicate spaces
    pattern = r"\s+"
    content = re.sub(pattern, r" ", content)

    # add space after punctuation marks if it doesn't exist
    pattern = r"([\.!?])(\w)"
    content = re.sub(pattern, r"\1 \2", content)

    return content


def to_file(file_in: str, file_out=None, **kwargs) -> str:
    """Save clean content of a subtitle file to text file

    Args:
        file_in (str): path to vtt file
        file_out (None, optional): path to text file
        **kwargs (optional): arguments for other parameters
            - no_message (bool): do not show message of result.
                                 Default is False

    Returns:
        str: path to text file
    """
    # set default values
    no_message = kwargs.get("no_message", False)
    if not file_out:
        filename = splitext(file_in)[0]
        file_out = "%s.txt" % filename
        i = 0
        while exists(file_out):
            i += 1
            file_out = "{}_{}.txt".format(filename, i)

    content = clean(file_in)
    with open(file_out, "w+", encoding="utf-8") as fp:
        fp.write(content)
    if not no_message:
        print("clean content is written to file: %s" % file_out)

    return file_out


class LineType(enum.Enum):
    TEXT = 1
    EMPTY_LINE = 2
    TIME = 3
    TEXT_WITH_TIME = 4


@dataclasses.dataclass
class LineData:
    """LineData class.

    Attributes:
        time_start: first time match integer rounded in second

    """

    line: str
    format_: LineType = LineType.TEXT
    line_clean: str = None
    time_start: int = None

    def __post_init__(self):
        if not self.line:
            self.format_ = LineType.EMPTY_LINE
        if match := re.match(r"^(\d*):(\d*):(\d*)(\.\d*)?", self.line):
            self.format_ = LineType.TIME
            self.time_start = (
                (int(match.groups()[0]) * 3600)
                + int(match.groups()[1]) * 60
                + int(match.groups()[2])
            )
        patt1 = r"<(\d*:\d*:\d*(\.\d*)?|/?c)>"
        if re.search(patt1, self.line):
            self.format_ = LineType.TEXT_WITH_TIME
            self.line_clean = re.sub(
                r"\s{2,}", " ", re.sub(patt1, " ", self.line)
            ).strip()
            if match := re.match(r".*<(\d*):(\d*):(\d*)(\.\d*)?>", self.line):
                self.time_start = (
                    (int(match.groups()[0]) * 3600)
                    + int(match.groups()[1]) * 60
                    + int(match.groups()[2])
                )
        if self.format_ == LineType.TEXT:
            self.line_clean = self.line.strip()


def clean_format2(src: str):
    """clean with format2 for logseq."""
    data_list = []
    first_time_found = False
    for line in pathlib.Path(src).read_text().splitlines():
        entry = LineData(line=line.strip())
        if not first_time_found:
            if entry.format_ not in (LineType.TEXT_WITH_TIME, LineType.TIME):
                # skip text until first time match line
                continue
            else:
                first_time_found = True
                data_list.append((LineType.TIME, entry.time_start))
        else:
            if entry.format_ == LineType.TEXT:
                data_list.append((LineType.TEXT, entry.line_clean))
            elif entry.format_ == LineType.EMPTY_LINE:
                pass
            elif entry.format_ == LineType.TIME:
                data_list.append((LineType.TIME, entry.time_start))
            elif entry.format_ == LineType.TEXT_WITH_TIME:
                data_list.append((LineType.TIME, entry.time_start))
                data_list.append((LineType.TEXT, entry.line_clean))
            else:
                raise ValueError(f"Unknown line format: {entry.format_}")
    last_time = None
    last_item = None
    line_list = []
    for idx, item in enumerate(data_list):
        if idx != 0:
            last_item = data_list[idx - 1]
        if item[0] == LineType.TIME:
            #  skip if next item is also time
            #  or last time is the same as current time
            if (data_list[idx + 1][0] == LineType.TIME) or (
                last_time is not None and last_time == item[1]
            ):
                continue
            else:
                line_list.append("")
                line_list.append("".join(("{{youtube-timestamp ", str(item[1]), "}}")))
                last_time = item[1]
        elif (
            idx == 0
            or last_item != LineType.TEXT
            or (last_item[0] == LineType.TEXT and last_item[1] != item[1])
        ) and item[1] != line_list[-1].strip():
            #  only print if it is first time on element
            # last item is not text
            #  or item is not the same as the last one
            line_list.append(item[1].strip())
    return "\n".join(line_list)


@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug):
    pass


@cli.command(name="clean")  # @cli, not @click!
@click.argument("src", nargs=1, type=click.Path(exists=True))
@click.option(
    "--format",
    "format_",
    type=click.Choice(["1", "2"]),
    default="1",
    help="Output format type.",
)
@click.option("--output", type=click.File("wb"), help="Output filename")
def run_clean(src, format_, output):
    content = None
    if format_ == "1":
        if not output:
            content = clean(src)
        else:
            raise NotImplementedError
    elif format_ == "2":
        content = clean_format2(src).strip()
        if output:
            # write to output
            raise NotImplementedError
    else:
        raise ValueError(f"Unknown format: {format_}")
    if not output:
        print(content)
