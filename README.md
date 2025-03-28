# kicad_delay_tuner
Python script to coax KiCad into doing delay instead of length matching. This uses the [latest KiCad API](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/index.html) through the [kicad-python](https://docs.kicad.org/kicad-python-main/index.html) library (kypy).

## How to use
1. Make sure KiCad PCB Editor is open to the board you are doing delay tuning/analysis on. This is a requirement of the new API, as it talks to the KiCad application instead of looking at the files directly.
2. Go to Preferences --> Preferences in the top bar, then under Plugins, tick the "Enable KiCad API" box. This will allow the script to use the API and connect to your running KiCad instance.
3. Go to File --> Board Setup in the top bar, then in the left menu go to Design Rules --> Custom Rules and add `# DELAY TUNER RULES` as the LAST LINE of your existing custom rules (if you have them, if you don't and need to use them later, add yours ABOVE this line)
4. Change the board parameters to match your board (global variables at the top of the script)   
5. Specify a netclass, rules file, and if applicable, a vivado IO report in csv format. An example vivado IO report is included in this repo. (**TODO**: make these command line args, for now change the lines in the code)
6. Run the script and observe the table for raw length values taken from kicad, calculated delay values, equivalent length values, and suggested rule values to get KiCad to target the longest delay in the netclass
7. Choose if you want to write the new rules to your rules file when prompted
8. Use the KiCad length matching tools as usual and rerun script to taste
