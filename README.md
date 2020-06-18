# UA Energy Mini Project
 UA Energy: Web Scraping and Text Mining of Energy News in Ukraine


## Repository Structure

- `UA Energy Mini-Project.ipynb` - a Python notebook demonstrating web scraping and exploratory analysis of [ua-energy.org](https://ua-energy.org). It is **strongly** recommended to view the notebook in nbviewer to see **interactive plots**.
- `uaenergy.py` - a script with custom scraping functions for ua-energy.org.
- `UAEnergy_Out*.xlsx` - data files created as part of the scraping. The full set of scraped articles with metadata can be found in `UAEnergy_Out3_MergedArticles.xlsx`.

- Click to view [UA Energy Mini-Project.ipynb](https://nbviewer.jupyter.org/github/alinacherkas/UA-Energy-Mini-Project/blob/master/UA%20Energy%20Mini-Project.ipynb)

## Abstract

The mini-project sets out to collect text data from a leading Ukrainian energy news portal. In so doing, I web scrape more than 6 thousand articles with basic metadata and conduct exploratory analysis of energy news. The analysis focuses on (1) the use of tags, (2) mentions of organisations and countries and (3) mentions of persons. I use **regular expressions** to extract relevant information and interactive visualisations to present the results. The five most common tags are:
- "газ" (gas)
- "Нафтогаз" (Naftogaz)
- "НКРЕПК" (National Commission for State Regulation of Energy)
- "нафта" (oil)
- "транзит" (transit)

The most frequently mentioned people are:
- [Andriy Kobolyev](https://en.wikipedia.org/wiki/Andriy_Kobolyev) (CEO of Naftogaz)
- [Oleksiy Orzhel](https://en.wikipedia.org/wiki/Oleksiy_Orzhel) (former Minister of Energy and Environmental Protection of Ukraine)
- [Volodymyr Groysman](https://en.wikipedia.org/wiki/Volodymyr_Groysman) (former Prime Minister of Ukraine)
- [Yuriy Vitrenko](https://en.wikipedia.org/wiki/Vitrenko_Yuriy_Yuriyovytch) (Director for Business Development at Naftogaz)
- Olha Buslavets (acting Minister of Energy and Environmental Protection of Ukraine as of April 2020)
- [Oleksiy Honcharuk](https://en.wikipedia.org/wiki/Oleksiy_Honcharuk) (former Prime Minister of Ukraine)

The share of articles mentioning these people show clear spikes for politicians but a more stable trend for business figures.

## Анотація

Даний міні-проект спрямований на збір текстових даних з провідного українського інформаційно-аналітичного ресурсу у галузі енергетики. Використовуючи веб-скрейпінг, я збираю понад 6 тисяч новин з метаданимии та досліджую їх. Зокрема, я аналізую (1) використання тегів, (2) використання назв організацій та країн, (3) використання імен. Я застосовую **регулярні вирази** для пошуку релевантної інформації та інтерактивні візуалізації для представлення результатів. Аналіз демонструє п'ять найпоширеніших тегів:
- "газ"
- "Нафтогаз"
- "НКРЕПК" (Національна комісія, що здійснює державне регулювання у сферах енергетики та комунальних послуг)
- "нафта"
- "транзит"

Найчастіше згадуваними особами є:
- [Андрій Коболєв](https://uk.wikipedia.org/wiki/Коболєв_Андрій_Володимирович) (голова правління НАК «Нафтогаз України»)
- [Олексій Оржель](https://uk.wikipedia.org/wiki/Оржель_Олексій_Анатолійович) (колишній міністр енергетики та захисту довкілля України)
- [Володимир Гройсман](https://uk.wikipedia.org/wiki/Гройсман_Володимир_Борисович) (колишній Прем'єр-міністр України)
- [Юрій Вітренко](https://uk.wikipedia.org/wiki/Вітренко_Юрій_Юрійович) (виконавчий директор НАК «Нафтогаз України»)
- [Ольга Буславець](https://uk.wikipedia.org/wiki/Буславець_Ольга_Анатоліївна) (в.о. міністр енергетики та захисту довкілля України з квітня 2020)
- [Олексій Гончарук](https://uk.wikipedia.org/wiki/Гончарук_Олексій_Валерійович) (колишній Прем'єр-міністр України)

Частка статей, у яких названі дані особи, зростає у період політичної активності для політиків, але є більш стабільною для представників бізнесу.