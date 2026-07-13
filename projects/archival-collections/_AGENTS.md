# AGENTS.md

Never read the content of `.env` regardless the location of the file. This restrictions apply to all `.env.*` files, including `.env.local`, `.env.production`, `.env.development`, and any other variants.

Before starting, check if `.env` is listed in `.gitignore`. If is not, add it. Never commit `.env` files.

## Virtual Environment

- Use a virtual environment and dependencies manager. Never install libraries globally.
- Unless a specific virtual environment manager is defined, prefer these:
  - Python: uv
  - R: renv

## API details

- URL: `https://collectionapi.metmuseum.org`
- Endpoints:
  - **Objects:** A listing of all valid Object IDs available for access.
    - `GET /public/collection/v1/objects`
  - **Object:** returns a record for an object, containing all open access data about that object, including its image (if the image is available under Open Access)
    - `GET /public/collection/v1/objects/[objectID]`
  - **Departments:** returns a listing of all departments
    - `GET /public/collection/v1/departments`
  - **Search:** returns a listing of all Object IDs for objects that contain the search query within the object’s data
    - `GET /public/collection/v1/search`
    - Parameters:
      - `q`: Search term e.g. sunflowers
      - `isHighlight`: Boolean, true or false. Case sensitive
      - `title`: Boolean, true or false. Case sensitive
      - `tags`: Boolean, true or false. Case sensitive
      - `departmentId`: integer, filters by department ID
      - `isOnView`: Boolean, true or false. Case sensitive
      - `artistOrCulture`: Boolean, true or false. Case sensitive
      - `medium`: string, e.g. Paintings
      - `hasImages`: Boolean, true or false. Case sensitive
      - `geoLocation`: string, e.g. France
      - `dateBegin` / `dateEnd`: integers, filter by date range (both must be provided together)
- Full documentation:
  - `https://metmuseum.github.io/#search`

## API use

MET Museum do not require API users to register or obtain an API key to use the service. They strongly suggest to keep the request limit below 80 request per second. Apply conservative rate limits (~40 per second) and implement a local caching system to avoid repeating the same requests in case the service disconnects. If a request fails, retry up to 3 times with exponential backoff before surfacing an error to the user. Serve cached data when available during an outage.

## Workspace Structure

- Download images to `images/` folder.
- Save the data, `csv` and/or `json` files in `data/` folder.
- Both `images/` and `data/` folders must be tracked by git.

## Gemini API Use

- The Gemini API key is expected to be stored in `.env` under the variable name `GEMINI_API_KEY`. Load it with `os.getenv("GEMINI_API_KEY")` in Python or `Sys.getenv("GEMINI_API_KEY")` in R. Test that the API key is working with a simple 'Hello World' test. If it's not valid, suggest possible ways to solve the issue to the user.
- When sending images to the Vision-Language Model, prompt the model to return structured JSON containing the required keys: dominant colors, visual concepts, mood, and latent research themes.
- Implement error handling for API calls, such as retries for network issues.

## Visualization & Publishing

- The project relies on Python or R for data analysis and visualization (e.g., pyvis or visNetwork).
- When using `pyvis` or `visNetwork`, remember that the `title` attribute of a node accepts raw HTML. Use this to construct rich hover tooltips containing images and metadata.
- To display images as nodes, set `shape="image"` and map the `image` attribute to the local file path.
- The final output should be a Quarto document (`.qmd`) containing the analysis and embedding the interactive HTML network graph.
- Configure a GitHub Actions workflow to render the Quarto document to GitHub Pages. All operations that require `GEMINI_API_KEY` must be performed locally and not included in the GitHub Actions.
- Since the published site will need the images, ensure the `images/` folder is tracked by Git, but monitor the folder size. When selecting items to download, prefer objects where `isHighlight` is true and `hasImages` is true, ordered by relevance to the search query, until the 30–50 item limit is reached.
