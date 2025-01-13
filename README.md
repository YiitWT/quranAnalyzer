---

# Quran Word Analyzer 🕋

Welcome to the **Quran Word Analyzer**! This is a fun and educational project designed to help you explore the Quran by searching for specific words in its verses. It’s important to note that this tool is **not a serious religious resource** but rather a fun way to interact with the text programmatically. Always refer to official sources like [Diyanet İşleri Başkanlığı](https://www.diyanet.gov.tr) for accurate and authoritative Quranic studies.

---

## 📜 About the Project

This project is a web application that allows users to search for specific words in the Quran and see how many times they appear and in which verses. It uses the [Quran.com API](https://quran.com/api) to fetch Quranic verses and provides a simple interface for searching and analyzing the text.

### Key Features:
- **Search for words** in the Quran in **Arabic** or **Turkish**.
- See the **total number of occurrences** of the word.
- View the **verses** where the word appears.
- Paginated results for easy navigation.
- Normalized Arabic text for better search accuracy.

---

## 🚀 How to Use

### Prerequisites
1. **Python 3.x** installed on your machine.
2. **Flask** and other dependencies installed (see below).

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/YiitWT/quranAnalyzer.git
   cd quran-word-analyzer
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask server:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Using the Web Interface
1. **Select Language**: Choose whether you want to search in **Arabic** or **Turkish**.
2. **Enter a Word**: Type the word you want to search for in the input field.
3. **Toggle Word Matching**: Use the checkbox to decide whether the word should be treated as a separate word (e.g., "Allah" vs. "Allah'ın").
4. **Set Page Size**: Choose how many results you want to see per page.
5. **Click "Kelimeyi Analiz Et"**: The tool will display the results, including:
   - The **total number of verses** where the word appears.
   - The **total number of occurrences** of the word.
   - A list of verses with the word highlighted.

---

## 🛠️ Technical Details

### Backend
- Built with **Flask** (Python).
- Uses the **Quran.com API** to fetch Quranic verses.
- Normalizes Arabic text for better search results.
- Caches the Quran dataset in a CSV file (`quran_dataset.csv`) for faster access.

### Frontend
- Simple and responsive HTML/CSS interface.
- Uses **Bootstrap** for styling.
- Dynamic pagination for navigating through search results.

---

## ⚠️ Important Notes
- This tool is **not a substitute for serious Quranic study**. It is intended for **educational and fun purposes only**.
- The data used in this project was fetched from [Quran.com](https://quran.com) and [Diyanet İşleri Başkanlığı](https://www.diyanet.gov.tr) as of **14.01.2025**.
- Always refer to official and authoritative sources for accurate Quranic interpretation and understanding.

---

## 📝 License

This project is licensed under the **MIT License**. Feel free to use, modify, and distribute it as you see fit. If you find it useful, consider giving it a ⭐ on GitHub!

---

## 🙏 Acknowledgments
- Thanks to [Quran.com](https://quran.com) for providing the API.
- Thanks to [Diyanet İşleri Başkanlığı](https://www.diyanet.gov.tr) for their translations and resources.

---

Enjoy exploring the Quran with this fun tool! If you have any questions or suggestions, feel free to open an issue or contribute to the project. 😊

---
