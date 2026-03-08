# 🧠 Project Manas: Neuromorphic Cognitive AI Agent

Project Manas is a state-of-the-art autonomous AI agent designed with a neuromorphic cognitive architecture. It goes beyond simple chat interfaces, aiming to simulate a "mind" that can learn routines, manage its own goals, and interact with the world through a modular sensory system.

## 🚀 Key Features

- **Sovereign Autonomy**: A background autonomous loop allowing Manas to think, plan, and act independently.
- **Cognitive Architecture**: Modular components for working memory, long-term persistence, emotions, and motivation.
- **Sensory Integration**: Capabilities for vision, audio, and web-based environmental awareness.
- **Routine Learning**: Ability to learn and adapt to user routines and global events.
- **Dual Interfaces**: Access via a sleek Web Dashboard or a powerful Command Line Interface (CLI).
- **Security Auditing**: Built-in agents for autonomous security auditing and vulnerability research.

## 🏗️ Architecture

Manas is built on a highly modular core:
- `src/cognition`: The central processing unit handling the "Mind" logic, routine learning, and motivation.
- `src/memory`: Multi-tier memory system (Episodic, Semantic, Working).
- `src/senses`: Modules for environmental input (Vision, Audio, Web).
- `src/agents`: Specialized autonomous agents (Security, Nostr, Intelligence).
- `src/interface`: Web and CLI connection layers.

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) (for local LLM support)
- GitHub CLI (`gh`) (for repository management)

### Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/marketingsales-debug/manas-core.git
   cd manas-core
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**:
   Copy the example config and add your API keys (optional for cloud features):
   ```bash
   cp config/llm_config.json.example config/llm_config.json
   ```
   *Note: `config/llm_config.json` is git-ignored to protect your secrets.*

## ⚡ Usage

### CLI Interface
Launch a direct chat session with Manas:
```bash
python run.py
```

### Web Dashboard
Launch the visual interface on `http://localhost:8000`:
```bash
python run.py --web
```

### Sovereign Mode (Background Autonomy)
Run Manas in full autonomous mode where it manages its own thoughts and goals:
```bash
python sovereign_run.py
```

## 🛡️ Security & Privacy
Manas is designed with security in mind. Local models are prioritized via Ollama, and sensitive configuration files are automatically excluded from version control via `.gitignore`.

## 📄 License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---
**Abhinav Badesha Pattan** is the sole owner and creator of this project.

---
*Built with ❤️ for the future of Autonomous General Intelligence.*
