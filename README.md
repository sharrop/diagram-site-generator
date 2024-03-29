# A Navigable TMF Class Diagram Website

This project generates navigable class diagrams of all TMF APIs as a single website. Each diagram is in Scalable Vector Graphics (SVG) format that is browsable and can contain hyperlinks to other SVG pages.

The idea is that (say) a **Customer** class diagram page would have a link to an **AccountRef**. Clicking on the **AccountRef** will take you to the **Account** class diagram. Any references in that diagram will take you to those diagrams etc.

**NOTE**: To regenerate this website, you will need access to the TMForum `github.com/tmforum-rand` repository - which is by application to the TMForum API project, and typically reserved for active TMF API authors.

## Status

- **This only works in the TMForum v4 repository at the moment**, as the v5 repo does not store the generated PlantUML files.
- There are quite a few broken links in the class diagrams, as I try to detect which schema references have valid class diagrams behind them. For example: AgreementItemRef does not have its own AgreementItem diagram - this is inside the Agreement schema.
- Note that this website is generated from the tmf-rand repo, and so may create APIs/schemas that are yet to be released, or are a work-in-progress.

## Installation

You can use the website as-is, but if you need to regenerate it from scratch:

1. Clone/Download *this* repo into a local directory (as {_tool_} below)
2. Clone/Download the `github.com/tmforum-rand` repository under a root dirctory, as {_root_} below (you will need TMForum-granted access to this repo as an "API Author"). This would be either:
   - **The TMF v4 API repo ([Open_API-And_Data_Model](https://github.com/tmforum-rand/Open_API_And_Data_Model)).** Note this ZIP is ~1Gb
   - The TMF v5 API repo ([OAS_Open_API_And_Data_Model](https://github.com/tmforum-rand/OAS_Open_API_And_Data_Model))
  
    Do this by going to the green "**<> Code**" button and selecting "**Download ZIP**" then unpacking this into a directory as {_root_}

This will run through the files of the repo picking out all the PlantUML files, and:
1. Modify the PlantUML to inject schema descriptions and hyperlinks to referenced diagrams 
2. Use these PlantUML files as source to generate a collection of SVG files that contain these links
3. Create a new "API Diagram" with its API name, version, basePath, description - and a description of each of its exposed resources, with its operations and notifications.
4. Generate an `index.htm` file as a starter page, with links into the API diagrams.

## Usage

```bash
cd {tool}/src
python main.py {root}
```
- Let this run. 
- It will generate a directories called `{tool}/plantUML` (the modified PlantUML files) and `{tool}/website` (the generated SVG files). 
- In a web browser open the `{tool}/webiste/index.htm` page to navigate around. 
- The `{tool}/webiste` directory is self-contained with no further dependencies, so it is ZIP-able and can be unpacked elsewhere.

## Contributing

Issues are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)