use std::collections::{HashMap, HashSet};

use imap::Session;
use sha2::{Digest, Sha256};

extern crate imap;
extern crate native_tls;

// https://www.atmail.com/blog/imap-commands/

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

pub fn get_message_hashes(
    session: &mut imap::Session<native_tls::TlsStream<std::net::TcpStream>>,
) -> Option<HashMap<String, Vec<u8>>> {
    let mut hash_per_message_id: HashMap<String, Vec<u8>> = HashMap::new();

    // Fetch all folders
    match session.list(Some(""), Some("*")) {
        Ok(folders) => {
            // Iterate over the folders and retrieve the message ids inside
            for folder in folders.iter() {
                log::debug!(
                    "delim='{}', name='{}'",
                    folder.delimiter().unwrap_or_default(),
                    folder.name()
                );                

                match session.select(folder.name()) {
                    Ok(_) => log::debug!("Selected folder '{}'", folder.name()),
                    Err(e) => {
                        log::error!("Error selecting folder: {}", e);
                        continue;
                    }
                }

                let messages = session.uid_search("ALL").unwrap();

                if messages.is_empty() {
                    log::info!("Skipping empty directory '{}'", folder.name());
                    continue;
                }

                log::info!(
                    "Processing {} message(s) in folder '{}'",
                    messages.len(),
                    folder.name()
                );

                let message_envelopes = session
                    .uid_fetch(
                        messages
                            .iter()
                            .map(|f| f.to_string())
                            .collect::<Vec<String>>()
                            .join(","),
                        "ENVELOPE",
                    )
                    .unwrap();

                // get the messages in each folder and generate a hash value from them
                for fetch_result in message_envelopes.iter() {
                    let result = fetch_result.envelope();

                    if result.is_none() {
                        log::warn!("Message envelope is None!");
                        continue;
                    }

                    let message = result.unwrap();

                    let date = message.date.unwrap();
                    let message_id = String::from_utf8(message.message_id.unwrap_or_default().to_vec()).unwrap();

                    let hasher =    Sha256::new();
                    let generated_hash = hasher
                        .chain_update(date)
                        .chain_update(message_id.clone())
                        .finalize()
                        .to_vec();

                    hash_per_message_id.insert(message_id, generated_hash);
                }
            }
        }
        Err(e) => {
            log::error!("Error fetching folders: {}", e);
            return None;
        }
    };

    Some(hash_per_message_id)
}
