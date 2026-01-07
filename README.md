# ❤️ Date Logger & AI Dating Coach

A personal relationship companion app built with Streamlit and Google Gemini. Log your dates, track "vibes", and get personalized AI advice based on your history and dating goals.

## Features

- **📝 Date Logging**: Record dates with photos, videos, audio, and notes.
- **🏷️ Vibe Check**: Tag dates with customizable attributes (e.g., "Good Food", "Red Flag", "Chemisty").
- **👤 User Profile**: Set your identity and dating goals (e.g., "Long-term relationship") for tailored advice.
- **💬 AI Companion**: Chat with a "Dating Coach" that remembers your past dates and gives insights using Google Gemini.
- **🔒 Privacy First**: Your data stays local in a SQLite database. Your API key is not stored permanently.
- **📊 History & Export**: View your dating history and analyze it or download as CSV.

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pankajberkeleyhaas/Date_Logger_app.git
   cd Date_Logger_app
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the App**:
   ```bash
   streamlit run app.py
   ```

4. **Get an AI Key**:
   - Go to [Google AI Studio](https://aistudio.google.com/).
   - Create a free API Key.
   - Enter it in the App's **Settings** sidebar to enable smart features.

## Customization

You can customize the "Tags" in the **Settings** tab to fit your dating style. Add specific interests or deal-breakers to track them over time.

## Technologies

- Python
- Streamlit
- SQLite
- Pandas
- Google Generative AI (Gemini)
