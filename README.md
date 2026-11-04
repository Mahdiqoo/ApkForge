<div align="center">

<!--  PLACEHOLDER 1: logo / banner (suggested size: 1200x300) -->
<img src="docs/images/banner.png" alt="APK Forge banner" width="100%">

#  APK Forge

**Turn ONE all-in-one Java file into a signed, installable Android APK — with a single click.**

![Version](https://img.shields.io/badge/version-3.8.1-44d62c)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![GUI](https://img.shields.io/badge/GUI-PyQt6-41cd52)
![License](https://img.shields.io/badge/license-PolyForm%20Strict%201.0.0-red)

</div>

---

##  What is APK Forge?

APK Forge is a desktop studio (Python + PyQt6) that builds Android apps **without Android Studio, Gradle or any project setup**. Paste your Java code — a full app, several classes in one file, or just a small snippet — pick an icon and press **BUILD**. APK Forge analyzes the code, splits it into proper files, compiles, dexes, packages, aligns and signs a ready-to-install APK.

Everything it needs (JDK, build-tools, android.jar) is downloaded into a single portable `Data` folder next to the script — nothing is installed system-wide.

<!--  PLACEHOLDER 2: main window / dashboard screenshot -->
<p align="center">
  <img src="docs/images/dashboard.png" alt="APK Forge dashboard" width="90%">
</p>

---

##  Features

- **One-file builds** — paste a full Activity, multiple classes in one file, or a bare snippet; APK Forge wraps and splits it automatically.
- **Auto-imports** — missing `import` lines for ~780 common Android/Java classes are added for you.
- **Auto-permissions** — required permissions are detected from your code and added to the manifest.
- **Auto min-SDK** — raises (or warns about) `minSdk` when your code needs a newer API.
- **Live diagnostics** — an analysis panel with one-click auto-fixes.
- **Assets manager** — add images, sounds and files; one-click auto-organize into `drawable` / `raw`.
- **Motion & sound automation** — per-element entrance animations and tap sounds.
- **Portable Data installer** — one-click download of JDK 17, Android build-tools 33.0.3, android.jar (API 33), Pillow and QtMultimedia, with several mirrors per item.
- ** AUTO paths** — every toolchain path points itself at the `Data` folder; on the **first launch** all paths are set automatically and saved to `Data/autopaths.json`, and again after every install.
- **Pinned toolchain** — exact versions are verified, so you get a clear message instead of cryptic javac/d8 errors.
- **SSL-resilient downloads** — works behind networks that break TLS (captive portals, proxies, antivirus).
- **Signing included** — auto-generated debug keystore, or use your own.

<!--  PLACEHOLDER 3: code editor + diagnostics screenshot -->
<p align="center">
  <img src="docs/images/editor.png" alt="Java editor with diagnostics" width="90%">
</p>

---

##  Requirements

| Requirement | Notes |
|---|---|
| **Python 3.9+** | Required |
| **PyQt6** | Installed automatically on first run (a console window asks first) |
| **Pillow** | Optional — icon resizing (installable from the app) |
| **QtMultimedia** | Optional — sound preview (installable from the app) |
| **JDK 17, build-tools 33.0.3, android.jar API 33** | Installed from inside the app into `./Data` |
| **Internet** | Only for the first-time downloads |

---

## 🚀 Getting started

1. **Download** `ApkForge_v3_8_1.py` (or clone this repository).
2. **Run it:**
   ```bash
   python ApkForge_v3_8_1.py
   ```
3. If a Python library is missing, a console window lists what is needed and asks **Install with pip? [Y/n]** — answer `Y` and the app restarts itself.
4. On the **first launch**, APK Forge runs ** AUTO for all paths** and creates `Data/autopaths.json`.
5. Open the **Dashboard**. Any missing tool shows a green **⬇ INSTALL** button — click it (or **Download & Install Missing**). The path fields fill themselves in when each install finishes.

<!--  PLACEHOLDER 4: "READY TO BUILD?" checklist + installer dialog -->
<p align="center">
  <img src="docs/images/installer.png" alt="Ready to build checklist and Data installer" width="80%">
</p>

---

##  How to build an APK

1. **Paste your Java code** into the editor (or load a `.java` file). Try one of the built-in templates if you want an example.
2. Open **Settings** and set the **app name**, **package**, **version**, **min/target SDK** (the package name can be generated automatically).
3. Choose an **icon** and add any **assets** (images, sounds, files).
4. Press **BUILD**.
5. When it finishes, your signed APK is in the output folder (default `Data/dist`). Copy it to your phone and install it.

<!--  PLACEHOLDER 5: settings page screenshot -->
<p align="center">
  <img src="docs/images/settings.png" alt="Settings page" width="80%">
</p>

<!--  PLACEHOLDER 6: build log / finished build screenshot -->
<p align="center">
  <img src="docs/images/build.png" alt="Build log" width="80%">
</p>

---

##  Folder layout

```
ApkForge_v3_8_1.py
Data/
├── python/                      pip packages (PyQt6, Pillow, …)
├── jdk-17…/                     JDK 17
├── android-build-tools-33.0.3/  aapt2 · d8 · zipalign · apksigner
├── androidjar/android.jar       Android platform library (API 33)
├── dist/                        built APKs
├── keystore/debug.keystore      auto-generated signing key
└── autopaths.json               first-run flag + detected paths
```

> Delete `Data/autopaths.json` to make the next launch behave like the first one.
> Delete the whole `Data` folder to remove everything APK Forge downloaded.

---

##  Troubleshooting

- **A path is empty or wrong** → Settings → Advanced → press ** Auto** beside it.
- **Wrong tool version** → the READY TO BUILD? checklist names the version found and the one required; use **⬇ INSTALL** to fetch the right one.
- **Download fails (SSL / blocked network)** → APK Forge retries other TLS modes, mirrors and OS-level download tools automatically; try again or switch networks.
- **Build error** → read the build log; the Diagnostics panel usually suggests a fix.

---

##  Roadmap

- [ ] HTML / WebView project support
- [ ] Your ideas — open an issue!

---

## 📜 License

Licensed under the **[PolyForm Strict License 1.0.0](LICENSE)**.

-  You may use APK Forge for **noncommercial** purposes (personal, hobby, study, education, research, nonprofit).
-  You may **not** distribute it, modify it, or create new works based on it.
-  You may **not** use it for commercial purposes.

APKs you build with APK Forge are yours. Copyright © 2026 **[YOUR NAME]**.

---

<div align="center">

Made with ⚒ by **[YOUR NAME]** · [Report a bug](../../issues) · [Request a feature](../../issues)

</div>
