//! Snake HD online leaderboard.
//!
//! A small Axum service that stores high scores as a tamper-evident hash chain
//! (the same idea as the game's local `helpers/ledger.py`, enforced server-side).
//! Each submitted score becomes a block whose SHA-256 hash covers its fields
//! plus the previous block's hash, so the history can't be edited after the fact.
//!
//! Endpoints:
//!   GET  /health           -> "ok"
//!   POST /scores  {name, score}  -> the new block (or null if score <= 0)
//!   GET  /scores?n=10      -> top N blocks by score
//!   GET  /verify           -> { ok, first_bad_index }
//!
//! Run:  cargo run   (listens on 0.0.0.0:8080, persists to scores.json)

use std::sync::{Arc, Mutex};

use axum::{
    extract::{Query, State},
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tower_http::cors::{Any, CorsLayer};

const GENESIS_PREV: &str =
    "0000000000000000000000000000000000000000000000000000000000000000";
const LEDGER_PATH: &str = "scores.json";

#[derive(Clone, Serialize, Deserialize)]
struct Block {
    index: u64,
    timestamp: String,
    name: String,
    score: i64,
    prev_hash: String,
    hash: String,
}

/// SHA-256 over the block's canonical fields (must match the verify step).
fn hash_block(index: u64, timestamp: &str, name: &str, score: i64, prev_hash: &str) -> String {
    let payload = format!("{}|{}|{}|{}|{}", index, timestamp, name, score, prev_hash);
    let mut hasher = Sha256::new();
    hasher.update(payload.as_bytes());
    hex::encode(hasher.finalize())
}

type Db = Arc<Mutex<Vec<Block>>>;

fn load_chain() -> Vec<Block> {
    match std::fs::read_to_string(LEDGER_PATH) {
        Ok(text) => serde_json::from_str(&text).unwrap_or_default(),
        Err(_) => Vec::new(),
    }
}

fn save_chain(chain: &[Block]) {
    if let Ok(text) = serde_json::to_string_pretty(chain) {
        let _ = std::fs::write(LEDGER_PATH, text);
    }
}

#[derive(Deserialize)]
struct NewScore {
    name: String,
    score: i64,
}

#[derive(Deserialize)]
struct TopQuery {
    n: Option<usize>,
}

#[derive(Serialize)]
struct VerifyResult {
    ok: bool,
    first_bad_index: Option<u64>,
}

async fn health() -> &'static str {
    "ok"
}

async fn post_score(State(db): State<Db>, Json(input): Json<NewScore>) -> Json<Option<Block>> {
    if input.score <= 0 {
        return Json(None);
    }
    // Strip the '|' delimiter (keeps hashing canonical) and cap the length.
    let name: String = input.name.chars().filter(|c| *c != '|').take(12).collect();
    let name = if name.trim().is_empty() { "ANON".to_string() } else { name };

    let mut chain = db.lock().unwrap();
    let prev_hash = chain
        .last()
        .map(|b| b.hash.clone())
        .unwrap_or_else(|| GENESIS_PREV.to_string());
    let index = chain.len() as u64;
    let timestamp = chrono::Utc::now().to_rfc3339();
    let hash = hash_block(index, &timestamp, &name, input.score, &prev_hash);

    let block = Block { index, timestamp, name, score: input.score, prev_hash, hash };
    chain.push(block.clone());
    save_chain(&chain);
    Json(Some(block))
}

async fn get_scores(State(db): State<Db>, Query(q): Query<TopQuery>) -> Json<Vec<Block>> {
    let n = q.n.unwrap_or(10);
    let chain = db.lock().unwrap();
    let mut sorted: Vec<Block> = chain.clone();
    sorted.sort_by(|a, b| b.score.cmp(&a.score).then(a.index.cmp(&b.index)));
    sorted.truncate(n);
    Json(sorted)
}

async fn verify(State(db): State<Db>) -> Json<VerifyResult> {
    let chain = db.lock().unwrap();
    let mut prev = GENESIS_PREV.to_string();
    for b in chain.iter() {
        let recomputed = hash_block(b.index, &b.timestamp, &b.name, b.score, &b.prev_hash);
        if b.prev_hash != prev || b.hash != recomputed {
            return Json(VerifyResult { ok: false, first_bad_index: Some(b.index) });
        }
        prev = b.hash.clone();
    }
    Json(VerifyResult { ok: true, first_bad_index: None })
}

#[tokio::main]
async fn main() {
    let db: Db = Arc::new(Mutex::new(load_chain()));

    // Permissive CORS so the game / a web client can call it during development.
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    let app = Router::new()
        .route("/health", get(health))
        .route("/scores", post(post_score).get(get_scores))
        .route("/verify", get(verify))
        .with_state(db)
        .layer(cors);

    let addr = "0.0.0.0:8080";
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    println!("snake-leaderboard listening on http://{addr}");
    axum::serve(listener, app).await.unwrap();
}
