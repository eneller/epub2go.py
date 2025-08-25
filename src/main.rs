use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use clap::Parser;
use indicatif::ProgressIterator;

const ALLBOOKS_URL: &str = "https://www.projekt-gutenberg.org/info/texte/allworka.html";

/// A book from Projekt Gutenberg.
#[derive(Debug)]
struct Book {
    author: String,
    title: String,
    url: String,
}

/// Represents the converter for Projekt Gutenberg books.
/// It holds configuration and handles the conversion process.
#[derive(Debug)]
struct GBConvert {
    download_dir: PathBuf,
    blocklist: Vec<String>,
    drama_css: &'static str,
}

impl GBConvert {
    pub fn new(download_dir: PathBuf) -> Self {
        let blocklist_content = include_str!("epub2go/blocklist.txt");
        let blocklist: Vec<String> = blocklist_content.lines().map(String::from).collect();

        let drama_css = include_str!("epub2go/drama.css");

        Self {
            download_dir,
            blocklist,
            drama_css,
        }
    }
}

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
    //TODO logging
    let mut books: Vec<String>;
    if !cli.args.is_empty() {
        books = cli.args;
    } else {
        //TODO interactive mode using fzf or nucleo
        books = cli.args;
    }

    // Create an instance of the converter
    let converter = GBConvert::new(cli.path.clone());

    //download book(s)
    if books.len() == 1 {
        //TODO download single book with optional progress
        //let get = Command::new("touch").arg("a b c").status();
    } else {
        //TODO disable progress on silent
        for book in books.into_iter().progress() {}
    }
}
