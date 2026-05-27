#![cfg_attr(all(not(debug_assertions), target_os = "windows"), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::path::PathBuf;

fn main() {
  tauri::Builder::default()
    .setup(|app| {
      // Start backend sidecar
      let backend_path = if cfg!(debug_assertions) {
        // In development, try to find backend binary in project root
        PathBuf::from("../backend/bin/backend")
      } else {
        // In production, look in resources
        app.path_resolver()
          .resolve_resource("../backend/bin/backend")
          .expect("failed to resolve backend binary")
      };

      if backend_path.exists() {
        let _backend_process: Child = Command::new(backend_path)
          .spawn()
          .expect("failed to start backend process");
        
        // Note: In production, you'd want to manage this process lifecycle
        // For now, it runs until the app closes
      }

      Ok(())
    })
    .invoke_handler(tauri::generate_handler![])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
