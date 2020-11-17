# Premise Plumbing Modeling Tools

PPMtools is a Python package being developed to model premise plumbing systems. PPMtools contains classes and associated functions to support an Agent-Based Modeling Framework with asssociated Monte Carlo pattern generation functions to simulate pseudo-realistic usage patterns in homes. 

PPMtools consists of the following general files:

1 file contains general functions and acts as the main interface:
* PPMtools.py

Typical use will involve 'import PPMtools'


3 files manage Python class objects, and associated functions:
* house.py
* person.py
* fixtures.py

An example file is provided that demonstrates a water age use case study example:
* example_water_age.py (coming soon)

Additionally, the ["INP_Files" folder](INP_Files) includes example premise plumbing systems' INP files.


# Status
All code in this repository is being provided in a "draft" state and has not been reviewed or cleared by US EPA. This status will be updated as models are reviewed.

# Dependencies

* PPMtools depends on WNTR (Water Network Tool for Reslience). More information on WNTR can be found [here](https://github.com/USEPA/WNTR). WNTR can be installed using 'pip install wntr', or see [link](https://github.com/USEPA/WNTR) for more information.
* PPMtools also depends on EPANET (version 2.2 or newer). A version for Windows and Linux is distributed with PPMtools. The latest official release of EPANET can be found [here](https://github.com/USEPA/EPANET2.2) (Managed by USEPA) or an ongoing development codebase can be found [here](https://github.com/OpenWaterAnalytics/EPANET) (Managed by Open Water Analytics). 


# License

This repository is released under the [MIT License](../LICENSE.md).

EPA Disclaimer
==============
The United States Environmental Protection Agency (EPA) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use. EPA has relinquished control of the information and no longer has responsibility to protect the integrity , confidentiality, or availability of the information. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recomendation or favoring by EPA. The EPA seal and logo shall not be used in any manner to imply endorsement of any commercial product or activity by EPA or the United States Government.

By submitting a pull request, you make an agreement with EPA that you will not submit a claim of compensation for services rendered to EPA or any other federal agency. Further, you agree not to charge the time you spend developing software code related to this project to any federal grant or cooperative agreement.

# Contributors
* Jonathan Burkhardt
* Levi Haupert
* William Platten
* James Mason
* John Minor