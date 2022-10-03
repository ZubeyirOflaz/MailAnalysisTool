# Mail Analysis Tool
<table>
<tr>
<td>
  Python project for the extraction, processing and analysis of a mail database
</td>
</tr>
</table>
<p align="center">
<img src="https://img.shields.io/github/license/ZubeyirOflaz/Deep-Learning-Uncertainty-Quantification-Methods" alt="plot" width="75">       <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="plot" width="85">
</p>

## Introduction
This project enables the analysis of an email database with the following features:
- Data and metadata extraction: The script goes through all the email files in the given zip folder and arranges all the data and relevant metadata fields in a Pandas dataframe.
- Increased security: Any attachments or additional files in the database other than the .eml email files are never unzipped to prevent contamination from potentially malicious files.
- Transliteration: The names from non-Latin alphabets associated with the email addresses are transliterated to the Latin Alphabet
- Online and Offline Translation: The project includes both an offline translator using transformers, and an online translator via the REST APIs of multiple online translation services. The default translation configuration in this project enables Russian to English translation.
- Network visualization: The email dataframe created can be used to visualize the connections between different people using the additional functions provided.


## Usage

Pandas dataframe can be created using the functions in mail_analysis_master.py script. The translation_module.py includes offline and online translation functionalities and network_visualizer can be used to visualize all or part of the correspondence.

## Todo
- Add more comments to the code
- Increase the speed of the code, remove some of the inefficiencies
- Add more advanced analysis functions
 