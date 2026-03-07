# Google Colab Setup Guide for Manas

This guide explains how to host your Manas dashboard and train the "Manus" model on Google Colab, even without a local Ollama instance.

## 1. Uploading to Colab

You have three ways to get your code into Colab:

*   **Option A: GitHub (Fastest)** - Push your local changes to a GitHub repo and clone it in the notebook.
*   **Option B: Google Drive** - Upload your project folder to your Google Drive and mount it in the notebook.
*   **Option C: Manual Upload** - Zip your project and drag it into the Colab file browser (left sidebar).

## 2. Running without Ollama


## 3. Training "Manus"

Training does **NOT** require Ollama. It uses the `unsloth` library to fine-tune the model weights directly on the Colab GPU.
1.  **GPU Runtime**: Go to `Runtime > Change runtime type` and select **T4 GPU**.
2.  **Start Training**: Run the "Start Training" cell in the notebook. it will harvest memories and begin the fine-tuning process.

## Steps

1.  Open the [Manas Colab Notebook Template](file:///Users/avipattan/.gemini/antigravity/brain/95a63919-2177-4ec6-bc91-f999e578aca8/manas_colab_notebook.md).
2.  Copy its content into a new Google Colab notebook.
3.  Run the cells sequentially, choosing your preferred upload method.
4.  Enter your Ngrok token and Cloud API keys when prompted.
