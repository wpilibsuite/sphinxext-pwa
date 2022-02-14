# sphinxext-pwa

## 🛑 **STOP** 🛑

This technology is highly experimental and volatile. Individuals using this extension should expect the following:

- completely random breakage
- excessive data usage
- excessive battery life drain
- completely breaking your sphinx website

## Introduction
[Progressive Web Applications](https://developers.google.com/web/updates/2015/12/getting-started-pwa), also known as PWAs, are a fantastic technology that enables seemless integration between websites and mobile devices. It empowers websites with the ability to present itself as a native-style application; complete with notifications and offline support. This extension's goal is to provide a "close as possible" integration between Sphinx and PWAs.

## Installation

Installation is pretty easy but has a couple major points.

First, you need to add this dependency to your `extensions` list in `conf.py`.

```python
extensions = [
    "sphinxext.pwa",
]
```

The extension will automatically prepopulate data for the `manifest` that is required for PWAs. However, setting the icons is mandatory. `pwa_icons` is a configuration variable that accepts a list of arrays. The nested array must have index `0` be the directory of the icon. The second `1` index must be string list of sizes of that icon. 

**IMPORTANT:** Icons must be placed at the *root* of the `_static` directory. Subdirectories *will not work*.

```python
pwa_icons = [["_static/myicon.webp", "48x48"]]
```

This should be all that is necessary to get your PWA functional. There is some extra customizability listed below.

## Configuration

PWAs have *a lot* of configuration. For details on accepted inputs, see [the Mozilla documentation](https://developer.mozilla.org/en-US/docs/Web/Manifest). Only a limited subset of options are exposed. Below are a list of exposed manifest options.

**Note:** Invalid inputs to these options can break the PWA and be extremely difficult to debug.

| Configuration     | Default                         | Type                             |
|-------------------|---------------------------------|----------------------------------|
| `pwa_name`        | `project` variable in `conf.py` | String                           |
| `pwa_short_name`  | None                            | String                           |
| `pwa_theme_color` | None                            | String containing HEX color code |
| `pwa_display`     | "standalone"                    | String                           |
| `pwa_icons`       | MANDATORY                       | [["image location", "sizes"]]    |

## Caveats

**Supported Browsers:** Chrome (Desktop & Mobile), Firefox (Mobile), Safari (iOS). Only the standard, non-beta, non-light versions of these browsers are supported.

**Supported OSes:** iOS >= 15, Safari versions 10-14.4 (excluding 14.5-14.8 due to a indexedDB bug) should also work. Android >= 6.

**Installation Time for Offline to Work**: It depends on the website, but a 160MB application takes on average 15 minutes to enable offline support. This also changes depending on the device specific implementation.

**Push Updates**: Because the cache is unique with every deploy, this initializes a redeploy of the entire cache.

**Cache Timeouts**: Whenever the user clears their browser cache, it will purge the assets. It is undetermined at this time if it will retrigger the download of the entire cache. Some users have space saving applications that may interfere with this.
