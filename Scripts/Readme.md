It is for utility / operational scripts that:

Help developers
Automate tasks
Are not part of the main program logic
Think of Scripts/ as:

“Tools that operate on the project, not the project itself.”
Model download scripts
Setup helpers
Database migration scripts
One‑off automation
CI helpers

🔧 3. Scripts/ is currently empty in meaning
Right now it only has a README.md.

That’s okay, but eventually it should contain things like:

text
Scripts/
├── download_vosk_model.sh
├── setup_local_env.sh
└── run_dev.sh
If not needed yet → fine to keep minimal.