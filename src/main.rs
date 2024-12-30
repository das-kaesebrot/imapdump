use crate::args::args::ImapDumpArgs;
use clap::Parser;
use simple_logger::SimpleLogger;

mod args;
mod imapclient;

#[tokio::main]
async fn main() {
    SimpleLogger::new().init().unwrap();

    let args = ImapDumpArgs::parse();

    let mut session = imapclient::get_client(args.host, args.port, args.username, args.password)
        .await
        .unwrap();
    let result = imapclient::get_message_hashes(&mut session);
    _ = imapclient::logout_client(session).await.unwrap()
}
