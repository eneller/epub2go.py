use std::path::PathBuf;

use clap::Parser;

/// Download ePUBs from https://www.projekt-gutenberg.org/
#[derive(Parser, Debug)]
#[command(version)]
struct Cli {
    /// Set the log level to DEBUG
    #[arg(short, long)]
    debug: bool,

    /// Disable the progress bar
    #[arg(short, long)]
    silent: bool,

    /// The path to which files are saved
    #[arg(short, long, default_value = ".")]
    path: PathBuf,

    /// Do not parse html files with blocklist
    #[arg(long)]
    no_clean: bool,

    /// Number of concurrent download workers
    #[arg(short = 'w', long, default_value_t = 10)]
    max_workers: u8,

    /// URLs to download from. If none are provided, enters interactive mode.
    args: Vec<String>,
}

fn main() {
    let cli = Cli::parse();
}