use crate::models::{OllamaGenerateRequest, OllamaGenerateResponse};
use chrono::Local;
use reqwest::Client;
use std::fs;
use std::path::PathBuf;
use std::time::Duration;

const OLLAMA_BASE: &str = "http://localhost:11434/api/generate";

pub async fn generate_news_summary() -> Result<String, String> {
    let base_path = if std::path::Path::new("src-tauri").exists() {
        PathBuf::from("src-tauri/static")
    } else {
        PathBuf::from("static")
    };

    if !base_path.exists() {
        fs::create_dir_all(&base_path)
            .map_err(|e| format!("Failed to create static dir: {}", e))?;
    }

    let today = Local::now().format("%Y-%m-%d").to_string();
    let cache_file = base_path.join(format!("news_{}.txt", today));

    if cache_file.exists() {
        if let Ok(content) = fs::read_to_string(&cache_file) {
            eprintln!("[ai] Loaded summary from cache: {}", cache_file.display());
            return Ok(content);
        }
    }

    let client = Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| format!("Client build error: {}", e))?;

    let urls = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    ];

    let mut headlines = String::new();

    for url in urls {
        if let Ok(res) = client.get(url).send().await {
            if let Ok(xml) = res.text().await {
                let mut count = 0;
                for line in xml.split("<title>") {
                    if count > 0 && count <= 5 {
                        if let Some(title) = line.split("</title>").next() {
                            let t = title.replace("<![CDATA[", "").replace("]]>", "");
                            if !t.contains("BBC")
                                && !t.contains("NYT")
                                && !t.contains("NYTimes.com")
                            {
                                headlines.push_str(&format!("- {}\n", t.trim()));
                            }
                        }
                    }
                    count += 1;
                }
            }
        }
    }

    if headlines.is_empty() {
        headlines = "- Global markets fluctuate amid economic uncertainty.\n- Technological advances in AI reported by major companies.".to_string();
    }

    eprintln!("[ai] Scraped headlines:\n{}", headlines);

    let model_name = "gemma4:e2b".to_string();

    eprintln!("[ai] Using model: {}", model_name);

    let prompt = format!(
        "You are an AI news aggregator. I will provide you with the top headlines from major global news sources today.\n\nHere are the headlines:\n{}\n\nTask: Please write a compelling, concise, and professional single-paragraph daily AI summary of these major events. Only return the summary text itself.",
        headlines
    );

    let req_body = OllamaGenerateRequest {
        model: model_name,
        prompt,
        stream: false,
    };

    let res = client
        .post(OLLAMA_BASE)
        .json(&req_body)
        .send()
        .await
        .map_err(|e| format!("Failed to connect to local Ollama API: {}", e))?;

    let ollama_res: OllamaGenerateResponse = res
        .json()
        .await
        .map_err(|e| format!("Failed to parse Ollama response: {}", e))?;

    eprintln!("[ai] Generated summary successfully");

    let _ = fs::write(&cache_file, &ollama_res.response);

    Ok(ollama_res.response)
}
