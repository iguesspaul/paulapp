import { invoke } from "@tauri-apps/api/core";

export interface UVIndexResponse {
    max_uv_index: number;
    max_uv_time: string;
}

export async function getUVIndex(): Promise<UVIndexResponse> {
    return await invoke("get_uv_index");
}
