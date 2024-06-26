

# CK3-Family-Tree-Exporter-To-Gramps
Neat GUI program to create CK3 Family Trees in Gramps.

## Introduction
I remade the original CK3 Family Tree Exporter with a nice user interface. Now using [rakaly cli](https://github.com/rakaly/cli) 
conversions and [jq](https://jqlang.github.io/jq/) for JSON processing. 

## Installation
Windows users can use the binaries on the [release]() page.
### Python
You will need to download the latest [rakaly cli](https://github.com/rakaly/cli) and [jq](https://jqlang.github.io/jq/) 
binary which is used for the JSON conversion step. After that install from requirements.txt.

## Usage
1. Download the CK3 Family Tree Exporter.
2. Download [Gramps](https://gramps-project.org/blog/download/).
3. Open the program. Set your CK3 Game path ( C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III)
4. and save data. JSON path should be set AFTER generating it (it will be automatically added after generation as well).
4. Convert your save file to JSON.
4. Convert to CSV. Requires you to provide the path to your JSON and a character ID from a dynasty you want the tree from. 
5. Find it from debug mode or directly from the save file.
5. The exporter will initially convert the localization files from the game folder into a processed format created in the resources folder. 
6. This file will be used for subsequent conversion.
6. Import the created CSV file to Gramps using the instructions found [here](https://gramps-project.org/wiki/index.php/Gramps_5.1_Wiki_Manual_-_Manage_Family_Trees:_CSV_Import_and_Export#Import).
7. All path configurations will be saved to config.ini.

## Community
Join the [Discord Server]()

