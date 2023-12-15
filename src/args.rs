pub(crate) mod args {
    pub use clap::Parser;

    #[derive(Parser, Debug)]
    #[command(author, version, about, long_about = None)]
    pub struct ImapDumpArgs {
        // Host to use
        #[arg(short = 'H', long)]
        pub host: String,
    
        // IMAP port to use
        #[arg(short, long, default_value_t = 993)]
        pub port: u16,

        // Username for logging into the IMAP server
        #[arg(short, long)]
        pub username: String,
        
        // Password for logging into the IMAP server
        #[arg(short = 'P', long)]
        pub password: String,
    }
}
