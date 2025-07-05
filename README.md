# UA Energy News Analytics
Collecting and analysing energy news in Ukraine

> [!NOTE]  
> 🚧 Work in Progress. This project is currently being updated.

## 📝 Overview

This project is designed to collect and analyse publications from UA-Energy, a leading Ukrainian energy news portal. It includes a Python CLI for web-scraing and processing news data and a Quarto dashboard for presenting the results of the analysis, which uses topic modelling and OpenAI API to gain insights into the texts. The dashboard is deployed on GitHub Pages and served using Shinylive as a serverless Shiny application running entirely in a web browser. It also reads data from a Parquet file stored in Azure Blob Storage.

## 📂 Repository Structure

```
ua-energy-news-analytics/
│
├── uaenergy/        # Python modules, including a CLI, for scraping and processing data
├── _quarto.yml      # a Quarto project configuration file
├── app.qmd          # a Quarto dashboard
├── requirements.txt # Python dependencies
└── README.md        # Project documentation
```

## ⚙️ Installation

1. Clone the repository:
```sh
git clone https://github.com/alinacherkas/ua-energy-news-analytics
cd ua-energy-news-analytics
```
2. Create a virtual environment and install dependencies:
```sh
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 🚀 Usage

You can run the CLI to collect and process data locally:

```sh
# print CLI documentation
python -m uaenergy --help
# scrape news articles published within specific dates
python -m uaenergy scrape --date-start 2025-01-01 --date-end 2025-06-30
# process the raw file
python -m uaenergy process ua-energy-news-2025-01-01-2025-06-30-raw.parquet.brotli
```

Running the processing pipeline requires that you have `OPENAI_API_KEY` set as an environment variable. You will also need to install [Quarto](https://quarto.org/docs/get-started/) for running the application locally. Once Quarto is installed, run `quarto preview app.qmd` to launch the app.

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

## 📄 License

This project is licensed under the MIT License.
