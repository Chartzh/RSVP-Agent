# Hello, world!

"Hello, world!" projects are a common starting point for developers learning new languages or platforms, as it provides a simple demonstration of how a programming language can be written for an application.

This application's logic is written in [Motoko](https://internetcomputer.org/docs/motoko/main/getting-started/motoko-introduction), a programming language designed specifically for developing canisters on ICP.

## Deploying from ICP Ninja

When viewing this project in ICP Ninja, you can deploy it directly to the mainnet for free by clicking "Run" in the upper right corner. Open this project in ICP Ninja:

[![](https://icp.ninja/assets/open.svg)](https://icp.ninja/i?g=https://github.com/dfinity/examples/motoko/hello_world)

## Project structure

The `/backend` folder contains the Motoko canister, `app.mo`. The `/frontend` folder contains web assets for the application's user interface. The user interface is written with plain JavaScript, but any frontend framework can be used.

Edit the `mops.toml` file to add [Motoko dependencies](https://mops.one/) to the project.

## Build and deploy from the command-line

To migrate your ICP Ninja project off of the web browser and develop it locally, follow these steps. These steps are necessary if you want to deploy this project for long-term, production use on the mainnet.

### 1. Download your project from ICP Ninja using the 'Download files' button on the upper left corner under the pink ninja star icon.

### 2. Open the `BUILD.md` file for further instructions.

Tentu. Berikut adalah ringkasan lengkap dan final untuk men-deploy backend dan frontend Anda secara lokal di VS Code.

Kuncinya adalah menggunakan **dua terminal** secara bersamaan.

-----

### \#\# Terminal 1: WSL (Untuk Backend ICP)

1.  **Buka terminal WSL (Ubuntu)** di VS Code.
2.  **Pindah ke direktori proyek** Anda:
    ```bash
    cd ~/projects/"RSVP Agent"
    ```
3.  **Jalankan jaringan `dfx` lokal**. (Pastikan Anda menggunakan `dfx` versi stabil seperti `0.26.1`):
    ```bash
    dfx start --background
    ```
4.  **Deploy backend Anda** (hanya jika ada perubahan pada `main.mo`):
    ```bash
    dfx deploy backend
    ```
5.  **Salin Canister ID lokal** yang muncul di terminal.

-----

### \#\# Terminal 2: PowerShell (Untuk Frontend Python)

1.  Buka terminal **baru** di VS Code (pastikan ini adalah **PowerShell**).
2.  **PENTING:** Buka file `frontend/rsvp_service.py` dan **update variabel `CANISTER_ID`** dengan ID yang Anda salin dari Terminal 1.
3.  **Aktifkan *virtual environment***:
    ```powershell
    .\venv\Scripts\activate
    ```
4.  **Jalankan agen Python** Anda:
    ```powershell
    py frontend\agent.py
    ```

Selesai\! Sekarang backend dan frontend Anda keduanya berjalan secara lokal di komputer Anda dan saling terhubung.
