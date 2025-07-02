"""Main CLI entrypoint for SnapTransact."""

from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from snap_transact import __version__
from snap_transact.core import process_images

app = typer.Typer(
    name="snap-transact",
    help="Extract transaction data from screenshots using OCR",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"SnapTransact CLI v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging",
    ),
) -> None:
    """SnapTransact CLI - Extract transaction data from screenshots."""
    if verbose:
        logger.configure(
            handlers=[
                {
                    "sink": "sys.stderr",
                    "level": "DEBUG",
                    "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                }
            ]
        )
    else:
        logger.configure(
            handlers=[
                {
                    "sink": "sys.stderr",
                    "level": "INFO",
                    "format": "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
                }
            ]
        )


@app.command()
def process(
    input_path: Path = typer.Argument(
        ...,
        help="Path to image file or directory containing images",
        exists=True,
    ),
    output: Path = typer.Option(
        Path("transactions.csv"),
        "--output",
        "-o",
        help="Output CSV file path",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
    ),
) -> None:
    """Process images and extract transaction data to CSV."""
    logger.info(f"Processing images from: {input_path}")
    logger.info(f"Output will be saved to: {output}")
    
    try:
        result = process_images(input_path, output, config)
        logger.success(f"Successfully processed {result.processed_count} images")
        logger.success(f"Extracted {result.transaction_count} transactions")
        logger.success(f"Results saved to: {output}")
    except Exception as e:
        logger.error(f"Failed to process images: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app() 