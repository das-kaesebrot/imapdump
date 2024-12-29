use std::collections::{HashMap, HashSet};

use imap::Session;
use sha2::{Digest, Sha256};

extern crate imap;
extern crate native_tls;

pub async fn get_client(
    host: String,
    port: u16,
    username: String,
    password: String,
) -> Result<
    Session<native_tls::TlsStream<std::net::TcpStream>>,
    (
        imap::Error,
        imap::Client<native_tls::TlsStream<std::net::TcpStream>>,
    ),
> {
    let tls = native_tls::TlsConnector::builder().build().unwrap();
    let domain = host.clone();
    let client = imap::connect((host, port), domain, &tls).unwrap();
    client.login(username, password)
}

pub async fn logout_client(
    mut session: imap::Session<native_tls::TlsStream<std::net::TcpStream>>,
) -> Result<(), imap::Error> {
    session.logout()
}

pub async fn fetch_all_messages(
    session: &mut imap::Session<native_tls::TlsStream<std::net::TcpStream>>,
) -> imap::error::Result<Option<String>> {
    // Fetch all folders first
    let folders = session.list(Some(""), Some("*"))?;

    let mut message_ids_per_folder: HashMap<&str, HashSet<u32>> = HashMap::new();

    // Iterate over the folders and print their names
    for folder in folders.iter() {
        log::debug!(
            "delim='{}', name='{}'",
            folder.delimiter().unwrap_or_default(),
            folder.name()
        );

        session.select(folder.name()).unwrap();
        let messages = session.uid_search("ALL").unwrap();

        if messages.is_empty() {
            log::info!("Skipping empty directory '{}'", folder.name());
            continue;
        }

        message_ids_per_folder.insert(folder.name(), messages);
    }

    let mut hash_per_message_id: HashMap<Vec<u8>, Vec<u8>> = HashMap::new();

    for (folder_name, messages) in message_ids_per_folder.iter() {
        log::info!(
            "Processing {} message(s) in directory '{}'",
            messages.len(),
            folder_name
        );

        session.select(folder_name).unwrap();

        let result = session
            .uid_fetch(
                messages
                    .iter()
                    .map(|f| f.to_string())
                    .collect::<Vec<String>>()
                    .join(","),
                "FAST",
            )
            .unwrap();

        for fetch_result in &result[..] {
            let result = fetch_result.clone().envelope().unwrap();
            let date = result.date.unwrap();
            let message_id = result.message_id.unwrap();

            let hasher = Sha256::new();
            let generated_hash = hasher
                .chain_update(date)
                .chain_update(message_id)
                .finalize()
                .to_vec();

            hash_per_message_id.insert(message_id.to_vec(), generated_hash);
        }
    }

    Ok(None)
}
