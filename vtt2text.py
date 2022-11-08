# @Author: anh-tuan.vu
# @Date:   2021-01-27 07:02:40
# @Last Modified by: rachmadani haryono
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


def clean_format2(src):
    pass


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
    if format_ == "1" and not output:
        print(clean(src))
    elif format_ == "2":
        content = clean_format2(src)
        if output:
            # write to output
            pass
        else:
            print(content)
    else:
        raise ValueError(f"Unknown error: {format_}")
