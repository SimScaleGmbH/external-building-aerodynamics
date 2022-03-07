
# SimScale External Building Aerodynamics

> :warning: **This code is not production-ready** and should only be used for demo/testing purposes.

simscale-eba is a wrapper package that wraps the SimScale API in an easy to set of objects for External Building Aerodynamics

## Installation

You can use pip:

```bash
pip install git+https://github.com/SimScaleGmbH/external-building-aerodynamics.git
```

### Development branch installation

Development branches can be created and used. To install a branch in your environment please use:

```bash
pip install git+https://github.com/SimScaleGmbH/external-building-aerodynamics.git@branch-name
```

### Version installation

Versions released for backward compatibility. Two current versions exist:

 1. v0.1.0 The old UTCI workflow
 2. v0.2.0 The new UTCI workflow and many improvements

See Installation section for taking the latest.

```bash
pip install git+https://github.com/SimScaleGmbH/external-building-aerodynamics.git@version-name
```

## Usage

To import the entire module:

    import simscale_eba

Alternatively, you can use components independently:

    import simscale_eba.PedestrianWindComfort as pwc

## Modules

| Module | Description |
|--|--|
| BoundaryLayer | Classes to create, analyze and visualize atmospheric boundary layers, with different standards and roughnesses, reference speeds, and heights |
| AblProfileFunctions | Functions used to define the many standards used in Atmospheric Boundary Layer classes withing BoundaryLayer |
| PedestrianWindComfort | Currently, this module contains classes that receive the setup of a Pedestrian Wind Comfort analysis type from the SimScale platform, including wind engineering standards and exposure categories and surface roughnesses |
| ResultProcessing | Perhaps the most important module for custom workflows such as the UTCI (Outdoor thermal comfort) and VDI (Custom comfort criteria) workflows. Here we give the ability to download results from LBM and PWC simulations, and process them into readable data or produce comfort plots |
| ExternalBuildingAssessment | Allows the user to create multidirectional CFD runs similar in usability ad setup to Pedestrian Wind Comfort, however with the ability to add customisation for more niche workflows not supported by the PWC analysis type out of the box |
| HourlyContinuous | This is another important module for weather data, although the SimScale platform uses .stat files for its PWC analysis type, this file type is not as common as others, nor does it hold enough information for us to analyze by period, or to perform UTCI calculations. This module, therefore, gives many utilities to read EPW files, process them into statistical data, and export if needed as .stat files. |
| TestConditions | This should be seen as the class that is equivalent to a PWC analysis **Wind conditions** section, holding the statistical wind data, and the atmospheric boundary layer object for each direction |
| WindTunnel | This module should also be seen as an equivalent in the PWC workflow, this time it's equivalent to the **Region of interest** in PWC. The region of interest takes the usual parameters of a region of interest and calculates the wind tunnel size position and orientation that can also be used to set up a **Latice Bolzmann Method** simulation directly|
| SimulationCore | This module contains most of the API-related class methods, since we actually reuse the methods across many different objects in this collection of modules, they will in the future be updated to pull the methods in this module to make the package more maintainable. This should be considered an **internal module** unless you wish to develop your own classes |
| SpectralAnalysis | Spectral analysis contains classes and functions useful for analysing signals produce from probe point result controls. Currently this is mainly used for internal testing and validation but can be used to analyse any signal if needed |

## Contact

This package is maintained by app-eng@simscale.com