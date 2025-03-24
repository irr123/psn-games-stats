# PSN Games Stats

1.  **Obtain your PSN API token:**
    * Go to http://ca.account.sony.com/api/v1/ssocookie to get your token.

1.  **Set the token as an environment variable (recommended):**
    * ```bash
        export PSN_TOKEN="your_token_here"
        ```
        * (Replace `"your_token_here"` with your actual token)
1.  **Setup env and Install deps:**
    * `python3 -m venv ./venv && source ./venv/bin/activate`
    * `pip install -r requirements.txt`

1.  **Run the script:**
    * ```bash
        make fmt lint && python ./games.py ${PSN_TOKEN} && make srv
        ```

1.  **Open the web interface:**
    * Open [http://localhost:8000/](http://localhost:8000/) in your web browser.

