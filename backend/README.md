# Polytrader Backend

This directory hosts the Polytrader AI agent code, which leverages:

- Python 3.11+
- LangGraph for agent orchestration
- LangChain libraries and various LLM integrations

## Installation

Navigate to the backend directory:

```bash
cd backend
```

Install Dependencies:

Option A (Using Pip):

```bash
pip install -e ".[dev]"
```

Option B (Using PDM if you prefer):

```bash
pdm install
```

Copy environment variables:

Duplicate .env.example to .env, fill in needed values (like LLM API keys or Polymarket private key).
The environment variables are read in configuration.py or other relevant files. 2. Usage
Local Development
Run the LangGraph dev server:

```bash
make lg-server
```

This calls langgraph dev, starting a local server where you can interact with the Polymarket agent’s graph.

Alternatively, you can directly invoke:

```bash
langgraph dev
```

if you have langgraph installed globally or in your virtual environment.

## Configuring Polymarket

- To be able to get out of positions that your agent gets in, you will need to have to sign into Polymarket with your Agent's wallet and create the Proxy Contract.

  - Ideally, this will all be done programmatically, but for now, you can do it manually

- Then, add the `POLYMARKET_PROXY_ADDRESS` to the `.env` file in both the `backend/` and `frontend/` directories.

  - This is the address you will be depositing the funds to, since the agent will be the one creating the orders. Ultimately, Poly

- Go to [Polymarket](https://polymarket.com/) and connect your wallet. You will be prompted to create a proxy contract.

- Then back in the repo, inside of [polymarket.py](backend/src/polytrader/polymarket.py), you change the value based into `self._init_approvals(False)` to `self._init_approvals(True)`.
  - This only needs to be done once, and will start the first time your run `make lg-server`.
    - notice the print logs in the terminal, and you will see the API keys that are being used.

## Tests (incomplete)

We use pytest (and pytest-asyncio) for testing. To run tests:

```bash
make test
```

Or directly:

```bash
pytest
```

This will run the test suite in tests/.

Additional Scripts
In `src/scripts/`, you will find Python scripts that interact with Polymarket or fetch data:

- `fetch_active_markets.py`
- `fetch_all_events.py`
- `fetch_all_markets.py`
- `fetch_all_tags.py`
- `fetch_current_markets.py`

They can be run like:

```bash
python src/scripts/fetch_all_markets.py --limit 50
```

Each script supports various flags, see their --help for details.

3. Project Structure

```
backend/
├── src/
│ └── polytrader/
│ ├── **init**.py
│ ├── configuration.py
│ ├── gamma.py
│ ├── graph.py
│ ├── objects.py
│ ├── polymarket.py
│ ├── prompts.py
│ ├── state.py
│ ├── tools.py
│ └── utils.py
├── tests/
│ ├── **init**.py
│ ├── test_gamma.py
│ └── test_polymarket.py
├── Makefile
├── langgraph.json
├── pyproject.toml
└── README.md (this file)
```

4. Environment Variables
   Add them to .env. For example:

```
FIRECRAWL_API_KEY=your_firecrawl_key
POLYMARKET_PRIVATE_KEY=0x123abc...
CLOB_API_KEY=...
CLOB_SECRET=...
CLOB_PASS_PHRASE=...
```

For local dev, typically no further secrets are needed unless you want to do real trades on Polymarket.
