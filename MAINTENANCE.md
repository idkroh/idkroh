# Maintaining this profile

The public `idkroh/idkroh` repository supplies the README on the GitHub profile.

Edit `README.md` for wording and links. The original supplied portrait is in `assets/portrait.jpg`; the account avatar is managed separately in GitHub profile settings.

`python scripts/generate_profile.py` regenerates the local SVG assets using Python's standard library. The daily GitHub Actions workflow runs around 02:17 UTC (06:17 in Dubai); GitHub may delay scheduled jobs. Use **Actions → Refresh profile graphics → Run workflow** for an immediate refresh. GitHub may disable scheduled workflows after 60 days without repository activity; re-enable it from the Actions tab if needed.

The contribution calendar comes from the anonymous public GitHub contribution page, including whatever aggregate private activity you have chosen to show publicly. Repository counts and language totals come only from public repositories. Language shares exclude forks and this profile repository and reflect source bytes, not skill ratings. The calendar covers GitHub's displayed rolling year; the bar chart shows the 12 latest calendar months, with partial first and current months.

All graphics are committed locally. There are no third-party stats widgets, external fonts, API keys, or personal access tokens in this repository. The workflow's built-in token only needs write access to this repository to commit assets. Network or parsing failures stop the job and leave the last successful graphics in place.

Change the design in `scripts/generate_profile.py`. The SVG animations are decorative; all numbers and labels remain readable without animation. GitHub and browser caching may delay display of a refreshed asset.
