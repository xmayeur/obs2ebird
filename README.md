# Bird's observation list conversion from Observation.org to eBird.org format

This program enables the conversion from [Observation.org](http://observation.org) to [eBird.org](http://eBird.org)
observation lists.

## Export from observation.org

- Lists from Observation.org need first to be downloaded in .CSV format.
- All lists are imported into a local database by executing the command:

        $ python -i "<path_to_observations_files/*.csv>

- The local database path is defined by default in the config.yml file as `observations.sqlite`

## Import file for eBird.org

- The import file for eBird.org observation is created by executing the command:

      $ python -o <path_to_ebird_file.csv> [--from start_date] [--to end_date] 

- Date are expressed in the ISO format "yyyy-mm-dd"

- The file can now be imported to [eBird import form](https://ebird.org/import/upload.form?theme=ebird),selecting the observation list option

- Note that a mapping is sometime needed between the provided species names and/or location names and the one accepted by eBird. This mapping is saved between sessions.
