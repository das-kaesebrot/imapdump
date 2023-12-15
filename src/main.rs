use crate::args::args::ImapDumpArgs;
use clap::Parser;
use simple_logger::SimpleLogger;

mod imapclient;
mod args;


fn main() {
    SimpleLogger::new().init().unwrap();

    let args = ImapDumpArgs::parse();

    let mut session = imapclient::get_client(args.host, args.port, args.username, args.password).unwrap();
    let result = imapclient::fetch_all_messages(&mut session);
    _ = imapclient::logout_client(session).expect("Logout should succeed")
}
