import { invoke } from "@tauri-apps/api/core";

export async function getNewsSummary(): Promise<string> {
    return await invoke("get_news_summary", {});
}
