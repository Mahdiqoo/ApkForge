#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 APK FORGE — Android APK Builder Studio                          v4.1.0 "polish"
================================================================================
 The fastest way to turn ONE all-in-one Java file into a signed, installable
 Android APK. Paste Java (a full app, multiple classes, or a bare snippet),
 pick an icon, hit BUILD — APK Forge analyzes, splits, compiles, dexes,
 packages, aligns and signs a ready-to-install APK with a single click.

 v4.1.0 "POLISH" — THE PLAIN-TEXT PASS
 --------------------------------------------------------------------------------
 Every emoji removed from the codebase: log prefixes, buttons, nav tabs,
 toasts, diagnostics and banners now use plain ASCII markers ([ok], [warn],
 [error], [auto]) or no marker at all. Zero logic changes — an AST audit
 against v4.0.0 confirms every node matches and only string constants differ.

 v4.0.0 "CRUCIBLE" — THE STRUCTURED EDITION
 --------------------------------------------------------------------------------
 A ground-up reorganization of the v3.8.1 codebase: the same engine, the same
 behavior — now forged for readability and maintenance.
   • 11 numbered parts with uniform section banners and the TOC below.
   • Consistent flow: config → catalogs → engine → pipeline → GUI → boot.
   • Every class and function now carries a concise docstring.
   • Hot-loop regexes are pre-compiled (re.compile hoisted out of loops).
   • Uniform whitespace: 4-space indents, 2/1 blank-line rules, ≤100-col wrap.
   • Behavior locked against v3.8.1 by an automated headless regression
     harness (scanner, analyzer, splitter, injector, sound synthesis,
     toolchain probes) — byte-identical outputs on every check (v4.0.0;
     v4.1.0 then stripped the emoji decoration, nothing else).

 TABLE OF CONTENTS
 --------------------------------------------------------------------------------
   PART 1  Bootstrap            imports · feature flags · app identity ·
                                 toolchain pins · platform constants
   PART 2  Catalogs & templates auto-import catalog · permissions · min-SDK
                                 tokens · androidx map · Java templates ·
                                 AI coding guide · asset snippets
   PART 3  Java engine          structure scanner · analyzer · auto-import
                                 fixer · androidx migrator · splitter ·
                                 snippet wrapper · friendly javac errors
   PART 4  Elements & media     element model · 12-sound pure-Python synth ·
                                 resource manager · animation/media injector
   PART 5  Toolchain discovery  PATH search · build-tools extraction ·
                                 android.jar discovery · autopaths state
   PART 6  Data installer       multi-transport HTTP downloads · pip --target
                                 installs · JDK / build-tools / android.jar
                                 one-click installation into ./Data
   PART 7  Build pipeline       JDK probing & pinned toolchain · asset
                                 engine · asset⇄code cross-check · APK build
   PART 8  GUI · foundation     Quantum theme · Toast · animated widgets ·
                                 command palette · syntax highlighter ·
                                 code editor · element configurator
   PART 9  GUI · pages          Source · Design · Motion · Dashboard ·
                                 AI Guide · Settings · background workers
   PART 10 GUI · main window    BuilderThread · SplashOverlay · MainWindow
                                 (sidebar nav, build console, auto-paths)
   PART 11 Entry point          excepthook safety net · console bootstrap ·
                                 missing-library gate · main()
   (Parts 8–10 are one `if HAS_QT:` block: the Java engine in Parts 1–7 stays
    importable and testable without PyQt6.)

 REQUIREMENTS
 --------------------------------------------------------------------------------
   • Windows (runs elsewhere for engine testing), Python 3.9+
   • Nothing else is mandatory: on first run APK Forge detects every missing
     library or tool (PyQt6, Pillow, JDK, build-tools, android.jar) and can
     download & install ALL of it with one click into the portable ./Data
     folder beside this script. Delete that folder and the machine is exactly
     as it was — nothing is ever installed system-wide.
   • Manual alternative: pip install PyQt6 Pillow · JDK 17 · Android
     build-tools 33.0.3 · android.jar (API 33) next to this script — or press
     AUTO beside any path in Settings → Advanced.

 PINNED TOOLCHAIN (v3.8 "anvil" heritage)
 --------------------------------------------------------------------------------
   JDK 17 · build-tools 33.0.3 · android.jar API 33 are THE toolchain. A wrong
   version is never silently accepted: the READY TO BUILD? checklist names the
   version it found and the one it needs, and the build stops with the same
   clear message instead of failing later with cryptic javac/d8 errors.

 AUTO ON FIRST LAUNCH & ON EVERY INSTALL (v3.8.1 heritage)
 --------------------------------------------------------------------------------
   • First launch (no Data/autopaths.json yet): AUTO runs for ALL paths and
     writes Data/autopaths.json. Delete that file to replay first launch.
   • Every later launch: tools found in ./Data fill any empty or stale path
     (valid hand-set paths are never overridden).
   • Each Data install triggers AUTO for that item the moment it finishes.

 USAGE
 --------------------------------------------------------------------------------
   python ApkForge_v4_1_0.py        (answer Y to install anything missing)

 KEYBOARD
 --------------------------------------------------------------------------------
   Ctrl+K palette · Ctrl+B build · Ctrl+S save · Ctrl+O open ·
   Ctrl+1..6 pages · F5 rescan
================================================================================
"""


import os
import re
import io
import sys
import json
import math
import wave
import array
import random
import shutil
import signal
import zipfile
import weakref
import platform
import threading
import traceback
import subprocess
import tempfile
from html import escape as html_escape
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, FrozenSet, Callable
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# v3.6 The Data folder — one portable folder beside the script
# ---------------------------------------------------------------------------
# Everything the one-click installer downloads lives in ONE portable "Data"
# folder. Nothing is ever installed system-wide: delete the folder and the
# machine is exactly as it was.
#
#   Data/python/                      pip packages (PyQt6, Pillow, …)
#   Data/jdk-…/                       JDK 17 (Temurin / Microsoft / Corretto)
#   Data/android-build-tools-33.0.3/  aapt2 · d8 · zipalign · apksigner
#   Data/androidjar/android.jar       the Android platform library
#   Data/downloads/                   staging area for zips (cleaned up)
try:
    _SCRIPT_DIR_PATH = Path(__file__).parent
except Exception:                       # interactive / frozen edge cases
    _SCRIPT_DIR_PATH = Path.cwd()
DATA_DIR = _SCRIPT_DIR_PATH / "Data"
DATA_PY_DIR = DATA_DIR / "python"          # pip --target destination
DATA_DOWNLOADS_DIR = DATA_DIR / "downloads"

# Packages previously installed into Data take precedence over site-packages,
# so a PyQt6 repaired by the installer is used consistently on the next launch.
try:
    if DATA_PY_DIR.is_dir() and any(
            (DATA_PY_DIR / m).is_dir() for m in ("PyQt6", "PIL")):
        sys.path.insert(0, str(DATA_PY_DIR))
except Exception:
    pass


# ---------------------------------------------------------------------------
# Optional dependencies — feature-detected imports (never block startup)
# ---------------------------------------------------------------------------
# Optional: PIL for icon resizing (never blocks startup)
try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False

# PyQt6 is required for the GUI, but the pure "Java engine" below stays
# importable without it (used by the build pipeline and for headless testing).
try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    HAS_QT = True
except Exception:
    HAS_QT = False

# v3.5: in-tool sound preview (optional — QtMultimedia is not always shipped)
HAS_QTMULTIMEDIA = False
if HAS_QT:
    try:
        from PyQt6.QtMultimedia import QSoundEffect
        HAS_QTMULTIMEDIA = True
    except Exception:
        HAS_QTMULTIMEDIA = False


# ---------------------------------------------------------------------------
# App identity (also parsed by the APK Forge Workspace web API)
# ---------------------------------------------------------------------------
APP_NAME = "APK Forge"
APP_TAGLINE = "Android APK Builder Studio"
APP_VERSION = "4.1.0"
APP_BUILD_NAME = "polish"


# ---------------------------------------------------------------------------
# Defaults & toolchain constants
# ---------------------------------------------------------------------------
APP_DEFAULTS = {
    "app_name": "My App",
    "package": "com.example.myapp",
    "activity_name": "MainActivity",
    "version_code": 1,
    "version_name": "1.0",
    "min_sdk": 21,
    "target_sdk": 33,
    "permissions": [],
    "java_is_full": False,
}

# v3.6.1: platform-aware legacy zip name (for manual side-by-side installs)
BUILD_TOOLS_ZIP_NAME = ("build-tools_r33.0.3-windows.zip" if os.name == "nt"
                        else "build-tools_r33.0.3-macosx.zip"
                        if sys.platform == "darwin"
                        else "build-tools_r33.0.3-linux.zip")
BUILD_TOOLS_LOCAL_DIR = "android-build-tools-33.0.3"
ANDROID_JAR_NAME = "android.jar"

# v3.8 PINNED TOOLCHAIN — APK Forge builds with EXACTLY these versions.
# Wrong versions are called out by name (checklist + build errors) instead of
# being silently used, and the system is never scanned for substitutes.
REQUIRED_JDK_MAJOR = 17
REQUIRED_BUILD_TOOLS = "33.0.3"
REQUIRED_ANDROID_API = 33


# ---------------------------------------------------------------------------
# v3.8 Pin verification
# ---------------------------------------------------------------------------
# "Must be the version the app requires" is enforced from three sources of
# truth — NEVER from folder names:
#   • JDK         — the real version from `javac -version` (probe_java_level)
#   • build-tools — Pkg.Revision in the archive's own source.properties
#   • android.jar — the API level bracketed from its framework classes
# Every surface (discovery, AUTO, the READY TO BUILD? checklist, the
# installer and the build itself) asks these helpers, so a wrong version is
# always called out by name and never silently used.

# Marker classes that first appeared in a known API level (each verified
# against the platform docs' "Added in API level X"). Their presence and
# absence bracket the jar's real level from above and below.
_ANDROID_API_MARKERS: Tuple[Tuple[int, Tuple[str, ...]], ...] = (
    (34, ("android/credentials/CredentialManager.class",
          "android/credentials/CreateCredentialRequest.class")),
    (33, ("android/app/LocaleManager.class",
          "android/app/LocaleConfig.class")),
    (31, ("android/window/SplashScreen.class",)),
    (30, ("android/content/pm/InstallSourceInfo.class",
          "android/window/WindowMetrics.class")),
    (29, ("android/app/Notification$BubbleMetadata.class",)),
    (28, ("android/text/PrecomputedText.class",)),
    (26, ("android/app/NotificationChannel.class",)),
)

# path → (mtime, size, range) — the namelist of a 27 MB jar is read once.
_JAR_API_CACHE: Dict[str, Tuple[float, int, Optional[Tuple[int, int]]]] = {}


def android_jar_api_range(jar_path) -> Optional[Tuple[int, int]]:
    """Bracket an android.jar's API level from its framework classes.

    Returns (min_api, max_api): (33, 33) for an exact API 33 jar, (31, 32)
    when only the API 31 markers match, (34, 999) for API 34+ — or None
    when the file isn't recognizable as an android.jar at all (a captive
    portal page, a renamed zip, …). Cached per path + mtime + size.
    """
    if not jar_path:
        return None
    try:
        p = Path(jar_path)
        if not p.is_file():
            return None
        key = str(p)
        stat = p.stat()
        cached = _JAR_API_CACHE.get(key)
        if cached and cached[0] == stat.st_mtime and cached[1] == stat.st_size:
            return cached[2]
        with zipfile.ZipFile(str(p)) as zf:
            names = set(zf.namelist())
        if ("android/app/Activity.class" not in names
                or "java/lang/Object.class" not in names):
            rng = None                      # not an android.jar at all
        else:
            found = 0
            for level, markers in _ANDROID_API_MARKERS:
                if found >= level:
                    break                   # markers are sorted high → low
                if any(m in names for m in markers):
                    found = level
            if not found:
                rng = (1, _ANDROID_API_MARKERS[-1][0] - 1)   # API ≤ 25
            elif found == _ANDROID_API_MARKERS[0][0]:
                rng = (found, 999)                            # API 34+
            else:
                above = min(l for l, _ in _ANDROID_API_MARKERS if l > found)
                rng = (found, above - 1)
        _JAR_API_CACHE[key] = (stat.st_mtime, stat.st_size, rng)
        return rng
    except Exception:
        return None


def android_jar_api_label(rng: Optional[Tuple[int, int]]) -> str:
    """(33, 33) → 'API 33' · (31, 32) → 'API 31–32' · (34, 999) → 'API 34+'."""
    if rng is None:
        return "not a valid android.jar"
    lo, hi = rng
    if hi >= 999:
        return f"API {lo}+"
    if lo == hi:
        return f"API {lo}"
    if lo <= 1:
        return f"API {hi} or older"
    return f"API {lo}–{hi}"


def android_jar_pin_ok(jar_path) -> bool:
    """True when the jar's framework classes say it is exactly API 33."""
    rng = android_jar_api_range(jar_path)
    return rng is not None and rng[0] <= REQUIRED_ANDROID_API <= rng[1]


def build_tools_revision(folder) -> Optional[str]:
    """The build-tools revision from the archive's own source.properties
    (Pkg.Revision=33.0.3). The folder's NAME never decides (v3.8) — a
    renamed or hand-copied folder tells the truth about itself here."""
    if not folder or not os.path.isdir(str(folder)):
        return None
    props = search_for_file(str(folder), ["source.properties"])
    if not props:
        return None
    try:
        for line in Path(props).read_text(
                encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("Pkg.Revision="):
                return line.split("=", 1)[1].strip() or None
    except Exception:
        return None
    return None


def build_tools_pin_status(folder) -> Tuple[bool, Optional[str]]:
    """(is_the_pinned_toolchain, revision_found) for a build-tools folder.

    ok = all five tools present AND source.properties Pkg.Revision is
    exactly the required revision — unversioned or wrong-revision folders
    are never silently used.
    """
    if not folder or not os.path.isdir(str(folder)):
        return False, None
    rev = build_tools_revision(folder)
    if not _has_required_build_tools(str(folder)):
        return False, rev
    return (rev == REQUIRED_BUILD_TOOLS), rev


def jdk_pin_ok(bin_dir) -> Tuple[bool, Optional[int]]:
    """(is_the_pinned_jdk, level_found) for a JDK bin folder — the level
    comes from the real `javac -version`, cached per binary, so the UI
    thread only ever pays for one short subprocess per path."""
    javac = _bin_tool(bin_dir, "javac") if bin_dir else None
    if not javac:
        return False, None
    level = probe_java_level(javac)
    return (level == REQUIRED_JDK_MAJOR), level


def data_jdk_mismatches() -> List[str]:
    """JDK folders inside the portable Data folder whose real version is
    not the pinned one — surfaced by AUTO so a wrong copy is named
    instead of silently pointed at."""
    out: List[str] = []
    try:
        if not DATA_DIR.is_dir():
            return out
        javac = "javac.exe" if IS_WINDOWS else "javac"
        for c in sorted(DATA_DIR.glob("jdk*")):
            bin_javac = c / "bin" / javac
            if not bin_javac.exists():
                continue
            lvl = probe_java_level(bin_javac)
            if lvl == REQUIRED_JDK_MAJOR:
                continue
            out.append(f"JDK {lvl} ({c.name})" if lvl
                       else f"an unreadable JDK ({c.name})")
    except Exception:
        pass
    return out


def data_buildtools_mismatches() -> List[str]:
    """Build-tools folders inside Data whose own source.properties says a
    revision other than the pinned 33.0.3."""
    out: List[str] = []
    try:
        if not DATA_DIR.is_dir():
            return out
        for c in sorted(DATA_DIR.glob("android-build-tools*")):
            if not c.is_dir():
                continue
            ok, rev = build_tools_pin_status(c)
            if ok:
                continue
            if _has_required_build_tools(str(c)):
                out.append(f"build-tools {rev or 'unversioned'} ({c.name})")
            elif rev:
                out.append(f"build-tools {rev} ({c.name}, tools missing)")
    except Exception:
        pass
    return out


def data_androidjar_mismatch() -> Optional[str]:
    """'API 34' when Data/androidjar/android.jar exists but is not API 33."""
    try:
        jar = DATA_DIR / "androidjar" / ANDROID_JAR_NAME
        if not jar.exists() or android_jar_pin_ok(jar):
            return None
        return android_jar_api_label(android_jar_api_range(jar))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Platform constants & icon densities
# ---------------------------------------------------------------------------
IS_WINDOWS = (os.name == "nt")

# Executable suffixes: Windows toolchain uses .exe/.bat, other platforms
# (used for headless engine testing) fall back to extension-less names.
EXE_SUFFIXES = [".exe", ""] if IS_WINDOWS else ["", ".exe"]

# Android icon sizes for different densities
ICON_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}


# ---------------------------------------------------------------------------
# Animation & sound catalogs (v3.5 AUTO-MOTION / AUTO-SOUND)
# ---------------------------------------------------------------------------
# Animation types (id -> friendly label)
ANIMATIONS = {
    "fade_in": "Fade In",
    "fade_out": "Fade Out",
    "slide_in_left": "Slide In Left",
    "slide_in_right": "Slide In Right",
    "slide_in_top": "Slide In Top",
    "slide_in_bottom": "Slide In Bottom",
    "slide_out_left": "Slide Out Left",
    "slide_out_right": "Slide Out Right",
    "scale_in": "Scale In (Zoom In)",
    "scale_out": "Scale Out (Zoom Out)",
    "rotate": "Rotate 360°",
    "bounce": "Bounce",
    "shake": "Shake",
}

# One-click animation presets (Motion page → "Apply to all")
ANIM_PRESETS = {
    "Material Entrance": ["fade_in", "slide_in_bottom"],
    "Playful Pop": ["scale_in", "bounce"],
    "Subtle & Clean": ["fade_in"],
    "Cinematic Reveal": ["slide_in_right", "fade_in", "scale_in"],
}

# v3.5 AUTO-MOTION — tasteful per-element-type entrances applied by the
# "Auto-Motion All" button / the smart preset (never touches elements the
# user already configured by hand).
ANIM_AUTO_BY_TYPE: Dict[str, Tuple[List[str], int]] = {
    "Button": (["fade_in", "scale_in"], 250),
    "ImageButton": (["fade_in", "scale_in"], 250),
    "FloatingActionButton": (["scale_in", "bounce"], 350),
    "TextView": (["fade_in"], 350),
    "EditText": (["fade_in", "slide_in_bottom"], 300),
    "ImageView": (["scale_in", "fade_in"], 350),
    "CheckBox": (["fade_in"], 300),
    "RadioButton": (["fade_in"], 300),
    "Switch": (["fade_in"], 300),
    "ToggleButton": (["fade_in"], 300),
    "ProgressBar": (["fade_in"], 450),
    "SeekBar": (["fade_in"], 400),
    "RatingBar": (["fade_in"], 400),
    "ListView": (["slide_in_bottom", "fade_in"], 400),
    "GridView": (["slide_in_bottom", "fade_in"], 400),
    "RecyclerView": (["slide_in_bottom", "fade_in"], 400),
    "Spinner": (["slide_in_bottom", "fade_in"], 350),
    "CardView": (["slide_in_bottom", "fade_in"], 400),
    "LinearLayout": (["slide_in_bottom"], 450),
    "RelativeLayout": (["slide_in_bottom"], 450),
    "FrameLayout": (["fade_in"], 400),
    "Toolbar": (["slide_in_top", "fade_in"], 350),
    "WebView": (["fade_in"], 400),
}
ANIM_AUTO_DEFAULT = (["fade_in"], 350)
ANIM_AUTO_PRESET_NAME = "Auto (smart per element)"

# v3.5 AUTO-SOUND — tappable element types that get the gentle built-in tap
# sound from the "Auto-Sound" button (only if no sound is set).
SOUND_AUTO_TAPPABLE = {
    "Button", "ImageButton", "FloatingActionButton", "CheckBox",
    "RadioButton", "Switch", "ToggleButton",
}
SOUND_AUTO_DEFAULT = "builtin:tap"


def auto_motion_for(element_type: str) -> Tuple[List[str], int]:
    """Per-element-type motion default (v3.5 auto-motion)."""
    return ANIM_AUTO_BY_TYPE.get(element_type, ANIM_AUTO_DEFAULT)


# ---------------------------------------------------------------------------
# Permissions & SDK catalogs
# ---------------------------------------------------------------------------
# Common permissions catalog (label, android permission string)
PERMISSION_CATALOG = [
    ("Internet", "android.permission.INTERNET"),
    ("Camera", "android.permission.CAMERA"),
    ("Record Audio", "android.permission.RECORD_AUDIO"),
    ("Fine Location (GPS)", "android.permission.ACCESS_FINE_LOCATION"),
    ("Coarse Location", "android.permission.ACCESS_COARSE_LOCATION"),
    ("Read External Storage", "android.permission.READ_EXTERNAL_STORAGE"),
    ("Write External Storage", "android.permission.WRITE_EXTERNAL_STORAGE"),
    ("Vibrate", "android.permission.VIBRATE"),
    ("Flashlight", "android.permission.FLASHLIGHT"),
    ("Bluetooth", "android.permission.BLUETOOTH"),
    ("Bluetooth Connect (12+)", "android.permission.BLUETOOTH_CONNECT"),
    ("Wi-Fi State", "android.permission.ACCESS_WIFI_STATE"),
    ("Network State", "android.permission.ACCESS_NETWORK_STATE"),
    ("Read Contacts", "android.permission.READ_CONTACTS"),
    ("Write Contacts", "android.permission.WRITE_CONTACTS"),
    ("Call Phone", "android.permission.CALL_PHONE"),
    ("Send SMS", "android.permission.SEND_SMS"),
    ("Read SMS", "android.permission.READ_SMS"),
    ("Read Phone State", "android.permission.READ_PHONE_STATE"),
    ("Body Sensors", "android.permission.BODY_SENSORS"),
    ("Activity Recognition", "android.permission.ACTIVITY_RECOGNITION"),
    ("Post Notifications (13+)", "android.permission.POST_NOTIFICATIONS"),
    ("Foreground Service", "android.permission.FOREGROUND_SERVICE"),
    ("Wake Lock", "android.permission.WAKE_LOCK"),
    ("Request Install Packages", "android.permission.REQUEST_INSTALL_PACKAGES"),
]

# SDK levels shown in the friendly dropdowns
SDK_LABELS = {
    21: "Android 5.0 · Lollipop", 22: "Android 5.1", 23: "Android 6.0 · Marshmallow",
    24: "Android 7.0 · Nougat", 25: "Android 7.1", 26: "Android 8.0 · Oreo",
    27: "Android 8.1", 28: "Android 9.0 · Pie", 29: "Android 10",
    30: "Android 11", 31: "Android 12", 32: "Android 12L",
    33: "Android 13", 34: "Android 14", 35: "Android 15",
}

PACKAGE_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$')


def suggest_package(app_name: str) -> str:
    """AUTOMATION: derive a valid package name from the app name."""
    base = re.sub(r'[^a-z0-9]+', '', app_name.lower())
    if not base:
        return APP_DEFAULTS["package"]
    if base[0].isdigit():
        base = "app" + base
    return f"com.example.{base}"


def package_is_valid(pkg: str) -> bool:
    """True when pkg is a non-empty, well-formed Java package name."""
    return bool(pkg) and bool(PACKAGE_RE.match(pkg)) and ".." not in pkg


def sdk_label(api: int) -> str:
    """Friendly Android version label for an API level ('API <n>' fallback)."""
    return SDK_LABELS.get(api, f"API {api}")


# ---------------------------------------------------------------------------
# Auto-import catalog & compatibility data
# ---------------------------------------------------------------------------
# Simple class name → fully qualified name. The auto-import fixer adds any
# missing import whose simple name is used in the pasted code — this is what
# lets AI-generated Java "just compile". The permission-signature, min-SDK
# and androidx-migration tables that follow feed the compatibility engine.
IMPORT_CATALOG: Dict[str, str] = {
    # --- android.widget ---
    "Button": "android.widget.Button",
    "TextView": "android.widget.TextView",
    "EditText": "android.widget.EditText",
    "ImageView": "android.widget.ImageView",
    "ImageButton": "android.widget.ImageButton",
    "CheckBox": "android.widget.CheckBox",
    "RadioButton": "android.widget.RadioButton",
    "RadioGroup": "android.widget.RadioGroup",
    "Switch": "android.widget.Switch",
    "ToggleButton": "android.widget.ToggleButton",
    "ProgressBar": "android.widget.ProgressBar",
    "SeekBar": "android.widget.SeekBar",
    "RatingBar": "android.widget.RatingBar",
    "ListView": "android.widget.ListView",
    "GridView": "android.widget.GridView",
    "ScrollView": "android.widget.ScrollView",
    "HorizontalScrollView": "android.widget.HorizontalScrollView",
    "Spinner": "android.widget.Spinner",
    "WebView": "android.webkit.WebView",
    "Toast": "android.widget.Toast",
    "AlertDialog": "android.app.AlertDialog",
    "DatePicker": "android.widget.DatePicker",
    "TimePicker": "android.widget.TimePicker",
    "Chronometer": "android.widget.Chronometer",
    "TextClock": "android.widget.TextClock",
    "VideoView": "android.widget.VideoView",
    "SearchView": "android.widget.SearchView",
    "TabHost": "android.widget.TabHost",
    "TabWidget": "android.widget.TabWidget",
    "ZoomControls": "android.widget.ZoomControls",
    "AdapterView": "android.widget.AdapterView",
    "ArrayAdapter": "android.widget.ArrayAdapter",
    "BaseAdapter": "android.widget.BaseAdapter",
    "LinearLayout": "android.widget.LinearLayout",
    "RelativeLayout": "android.widget.RelativeLayout",
    "FrameLayout": "android.widget.FrameLayout",
    "GridLayout": "android.widget.GridLayout",
    "TableLayout": "android.widget.TableLayout",
    "TableRow": "android.widget.TableRow",
    "AbsoluteLayout": "android.widget.AbsoluteLayout",
    "Adapter": "android.widget.Adapter",
    "ListAdapter": "android.widget.ListAdapter",
    "SimpleAdapter": "android.widget.SimpleAdapter",
    "CompoundButton": "android.widget.CompoundButton",
    "PopupMenu": "android.widget.PopupMenu",
    "Space": "android.widget.Space",
    "TextSwitcher": "android.widget.TextSwitcher",
    "ImageSwitcher": "android.widget.ImageSwitcher",
    "ViewSwitcher": "android.widget.ViewSwitcher",
    "ViewFlipper": "android.widget.ViewFlipper",
    "ViewAnimator": "android.widget.ViewAnimator",
    # --- android.view ---
    "View": "android.view.View",
    "ViewGroup": "android.view.ViewGroup",
    "Gravity": "android.view.Gravity",
    "MotionEvent": "android.view.MotionEvent",
    "KeyEvent": "android.view.KeyEvent",
    "LayoutInflater": "android.view.LayoutInflater",
    "ViewTreeObserver": "android.view.ViewTreeObserver",
    "WindowManager": "android.view.WindowManager",
    "Window": "android.view.Window",
    "Display": "android.view.Display",
    "Menu": "android.view.Menu",
    "MenuItem": "android.view.MenuItem",
    "ContextMenu": "android.view.ContextMenu",
    "ActionMode": "android.view.ActionMode",
    "InputEvent": "android.view.InputEvent",
    "ScaleGestureDetector": "android.view.ScaleGestureDetector",
    "GestureDetector": "android.view.GestureDetector",
    "DragEvent": "android.view.DragEvent",
    "VelocityTracker": "android.view.VelocityTracker",
    "SurfaceView": "android.view.SurfaceView",
    "SurfaceHolder": "android.view.SurfaceHolder",
    "OrientationEventListener": "android.view.OrientationEventListener",
    "Choreographer": "android.view.Choreographer",
    "ViewStub": "android.view.ViewStub",
    "KeyCharacterMap": "android.view.KeyCharacterMap",
    # --- android.view.animation ---
    "Animation": "android.view.animation.Animation",
    "AnimationUtils": "android.view.animation.AnimationUtils",
    "AnimationSet": "android.view.animation.AnimationSet",
    "AlphaAnimation": "android.view.animation.AlphaAnimation",
    "TranslateAnimation": "android.view.animation.TranslateAnimation",
    "ScaleAnimation": "android.view.animation.ScaleAnimation",
    "RotateAnimation": "android.view.animation.RotateAnimation",
    "AccelerateInterpolator": "android.view.animation.AccelerateInterpolator",
    "DecelerateInterpolator": "android.view.animation.DecelerateInterpolator",
    "OvershootInterpolator": "android.view.animation.OvershootInterpolator",
    "BounceInterpolator": "android.view.animation.BounceInterpolator",
    "LinearInterpolator": "android.view.animation.LinearInterpolator",
    "CycleInterpolator": "android.view.animation.CycleInterpolator",
    "AnticipateInterpolator": "android.view.animation.AnticipateInterpolator",
    # --- android.graphics ---
    "Canvas": "android.graphics.Canvas",
    "Paint": "android.graphics.Paint",
    "Color": "android.graphics.Color",
    "Bitmap": "android.graphics.Bitmap",
    "BitmapFactory": "android.graphics.BitmapFactory",
    "Rect": "android.graphics.Rect",
    "RectF": "android.graphics.RectF",
    "Point": "android.graphics.Point",
    "PointF": "android.graphics.PointF",
    "Path": "android.graphics.Path",
    "Matrix": "android.graphics.Matrix",
    "Shader": "android.graphics.Shader",
    "LinearGradient": "android.graphics.LinearGradient",
    "RadialGradient": "android.graphics.RadialGradient",
    "SweepGradient": "android.graphics.SweepGradient",
    "PorterDuff": "android.graphics.PorterDuff",
    "PorterDuffXfermode": "android.graphics.PorterDuffXfermode",
    "BlurMaskFilter": "android.graphics.BlurMaskFilter",
    "EmbossMaskFilter": "android.graphics.EmbossMaskFilter",
    "Typeface": "android.graphics.Typeface",
    "Drawable": "android.graphics.drawable.Drawable",
    "ColorDrawable": "android.graphics.drawable.ColorDrawable",
    "BitmapDrawable": "android.graphics.drawable.BitmapDrawable",
    "GradientDrawable": "android.graphics.drawable.GradientDrawable",
    "ShapeDrawable": "android.graphics.drawable.ShapeDrawable",
    "AnimationDrawable": "android.graphics.drawable.AnimationDrawable",
    "LayerDrawable": "android.graphics.drawable.LayerDrawable",
    "StateListDrawable": "android.graphics.drawable.StateListDrawable",
    "NinePatchDrawable": "android.graphics.drawable.NinePatchDrawable",
    "InsetDrawable": "android.graphics.drawable.InsetDrawable",
    "ClipDrawable": "android.graphics.drawable.ClipDrawable",
    "LevelListDrawable": "android.graphics.drawable.LevelListDrawable",
    "RippleDrawable": "android.graphics.drawable.RippleDrawable",
    "VectorDrawable": "android.graphics.drawable.VectorDrawable",
    "CornerPathEffect": "android.graphics.CornerPathEffect",
    "DashPathEffect": "android.graphics.DashPathEffect",
    "PathEffect": "android.graphics.PathEffect",
    "PathMeasure": "android.graphics.PathMeasure",
    "Region": "android.graphics.Region",
    "ColorFilter": "android.graphics.ColorFilter",
    "PorterDuffColorFilter": "android.graphics.PorterDuffColorFilter",
    # NOTE: android.graphics.Camera is intentionally NOT in the catalog — the
    # "Camera" key maps to android.hardware.Camera (the overwhelmingly common
    # meaning). Use the fully-qualified android.graphics.Camera for 3D matrix
    # work if you need it.
    "YuvImage": "android.graphics.YuvImage",
    # --- android.os ---
    "Bundle": "android.os.Bundle",
    "Handler": "android.os.Handler",
    "Looper": "android.os.Looper",
    "Message": "android.os.Message",
    "AsyncTask": "android.os.AsyncTask",
    "Build": "android.os.Build",
    "Environment": "android.os.Environment",
    "BatteryManager": "android.os.BatteryManager",
    "PowerManager": "android.os.PowerManager",
    "WakeLock": "android.os.PowerManager.WakeLock",
    "Vibrator": "android.os.Vibrator",
    "VibrationEffect": "android.os.VibrationEffect",
    "SystemClock": "android.os.SystemClock",
    "CountDownTimer": "android.os.CountDownTimer",
    "Parcelable": "android.os.Parcelable",
    "StrictMode": "android.os.StrictMode",
    "Process": "android.os.Process",
    "UserManager": "android.os.UserManager",
    "FileObserver": "android.os.FileObserver",
    # --- android.app ---
    "Activity": "android.app.Activity",
    "ActivityGroup": "android.app.ActivityGroup",
    "ListActivity": "android.app.ListActivity",
    "Fragment": "android.app.Fragment",
    "Dialog": "android.app.Dialog",
    "DialogInterface": "android.content.DialogInterface",
    "Notification": "android.app.Notification",
    "NotificationManager": "android.app.NotificationManager",
    "NotificationChannel": "android.app.NotificationChannel",
    "PendingIntent": "android.app.PendingIntent",
    "AlarmManager": "android.app.AlarmManager",
    "Service": "android.app.Service",
    "IntentService": "android.app.IntentService",
    "Application": "android.app.Application",
    "ProgressDialog": "android.app.ProgressDialog",
    "KeyguardManager": "android.app.KeyguardManager",
    "WallpaperManager": "android.app.WallpaperManager",
    "ActionBar": "android.app.ActionBar",
    "LoaderManager": "android.app.LoaderManager",
    "TaskStackBuilder": "android.app.TaskStackBuilder",
    "DownloadManager": "android.app.DownloadManager",
    # --- android.content ---
    "Context": "android.content.Context",
    "Intent": "android.content.Intent",
    "IntentFilter": "android.content.IntentFilter",
    "SharedPreferences": "android.content.SharedPreferences",
    "ContentValues": "android.content.ContentValues",
    "ContentResolver": "android.content.ContentResolver",
    "BroadcastReceiver": "android.content.BroadcastReceiver",
    "ContentProvider": "android.content.ContentProvider",
    "ComponentName": "android.content.ComponentName",
    "Uri": "android.net.Uri",
    "ClipData": "android.content.ClipData",
    "ClipboardManager": "android.content.ClipboardManager",
    "Cursor": "android.database.Cursor",
    # --- android.media / audio / sound ---
    "MediaPlayer": "android.media.MediaPlayer",
    "SoundPool": "android.media.SoundPool",
    "AudioManager": "android.media.AudioManager",
    "Ringtone": "android.media.Ringtone",
    "RingtoneManager": "android.media.RingtoneManager",
    "MediaRecorder": "android.media.MediaRecorder",
    "AudioRecord": "android.media.AudioRecord",
    "AudioFormat": "android.media.AudioFormat",
    "AudioTrack": "android.media.AudioTrack",
    "ToneGenerator": "android.media.ToneGenerator",
    "MediaMetadataRetriever": "android.media.MediaMetadataRetriever",
    "ExifInterface": "android.media.ExifInterface",
    # --- android.hardware / camera / sensors ---
    "Camera": "android.hardware.Camera",
    "CameraManager": "android.hardware.camera2.CameraManager",
    "Sensor": "android.hardware.Sensor",
    "SensorManager": "android.hardware.SensorManager",
    "SensorEventListener": "android.hardware.SensorEventListener",
    "SensorEvent": "android.hardware.SensorEvent",
    "GeomagneticField": "android.hardware.GeomagneticField",
    "ConsumerIrManager": "android.hardware.ConsumerIrManager",
    "UsbManager": "android.hardware.usb.UsbManager",
    # --- android.location / bluetooth / net / telephony / wifi ---
    "LocationManager": "android.location.LocationManager",
    "Location": "android.location.Location",
    "LocationListener": "android.location.LocationListener",
    "Criteria": "android.location.Criteria",
    "Geocoder": "android.location.Geocoder",
    "Address": "android.location.Address",
    "BluetoothAdapter": "android.bluetooth.BluetoothAdapter",
    "BluetoothDevice": "android.bluetooth.BluetoothDevice",
    "BluetoothSocket": "android.bluetooth.BluetoothSocket",
    "BluetoothServerSocket": "android.bluetooth.BluetoothServerSocket",
    "HttpURLConnection": "java.net.HttpURLConnection",
    "HttpsURLConnection": "javax.net.ssl.HttpsURLConnection",
    "URLConnection": "java.net.URLConnection",
    "MalformedURLException": "java.net.MalformedURLException",
    "Socket": "java.net.Socket",
    "ServerSocket": "java.net.ServerSocket",
    "InetAddress": "java.net.InetAddress",
    "DatagramSocket": "java.net.DatagramSocket",
    "TelephonyManager": "android.telephony.TelephonyManager",
    "SmsManager": "android.telephony.SmsManager",
    "SmsMessage": "android.telephony.SmsMessage",
    "PhoneNumberUtils": "android.telephony.PhoneNumberUtils",
    "WifiManager": "android.net.wifi.WifiManager",
    "WifiInfo": "android.net.wifi.WifiInfo",
    "ConnectivityManager": "android.net.ConnectivityManager",
    "NetworkInfo": "android.net.NetworkInfo",
    "Network": "android.net.Network",
    # --- android.text / util / webkit / provider / prefs ---
    "TextUtils": "android.text.TextUtils",
    "TextWatcher": "android.text.TextWatcher",
    "Editable": "android.text.Editable",
    "SpannableString": "android.text.SpannableString",
    "Spannable": "android.text.Spannable",
    "Spanned": "android.text.Spanned",
    "ForegroundColorSpan": "android.text.style.ForegroundColorSpan",
    "StyleSpan": "android.text.style.StyleSpan",
    "Html": "android.text.Html",
    "InputType": "android.text.InputType",
    "InputFilter": "android.text.InputFilter",
    "Layout": "android.text.Layout",
    "Log": "android.util.Log",
    "Pair": "android.util.Pair",
    "SparseArray": "android.util.SparseArray",
    "SparseBooleanArray": "android.util.SparseBooleanArray",
    "Base64": "android.util.Base64",
    "DisplayMetrics": "android.util.DisplayMetrics",
    "TypedValue": "android.util.TypedValue",
    "JsonReader": "android.util.JsonReader",
    "JsonWriter": "android.util.JsonWriter",
    "WebViewClient": "android.webkit.WebViewClient",
    "WebSettings": "android.webkit.WebSettings",
    "WebChromeClient": "android.webkit.WebChromeClient",
    "JavascriptInterface": "android.webkit.JavascriptInterface",
    "CookieManager": "android.webkit.CookieManager",
    "ContactsContract": "android.provider.ContactsContract",
    "MediaStore": "android.provider.MediaStore",
    "Settings": "android.provider.Settings",
    "AlarmClock": "android.provider.AlarmClock",
    "CalendarContract": "android.provider.CalendarContract",
    "CallLog": "android.provider.CallLog",
    "Browser": "android.provider.Browser",
    "Telephony": "android.provider.Telephony",
    # --- android.view.inputmethod / accessibility ---
    "InputMethodManager": "android.view.inputmethod.InputMethodManager",
    "InputConnection": "android.view.inputmethod.InputConnection",
    "AccessibilityManager": "android.view.accessibility.AccessibilityManager",
    "AccessibilityEvent": "android.view.accessibility.AccessibilityEvent",
    # --- java.lang extras (auto-imported implicitly, kept for completeness) ---
    "Thread": "java.lang.Thread",
    "Runnable": "java.lang.Runnable",
    "Math": "java.lang.Math",
    "StringBuffer": "java.lang.StringBuffer",
    "StringBuilder": "java.lang.StringBuilder",
    "InterruptedException": "java.lang.InterruptedException",
    "Exception": "java.lang.Exception",
    "NumberFormatException": "java.lang.NumberFormatException",
    "IllegalArgumentException": "java.lang.IllegalArgumentException",
    "IllegalStateException": "java.lang.IllegalStateException",
    "UnsupportedOperationException": "java.lang.UnsupportedOperationException",
    "RuntimeException": "java.lang.RuntimeException",
    "IndexOutOfBoundsException": "java.lang.IndexOutOfBoundsException",
    "ClassCastException": "java.lang.ClassCastException",
    "NullPointerException": "java.lang.NullPointerException",
    "Character": "java.lang.Character",
    "Boolean": "java.lang.Boolean",
    "Integer": "java.lang.Integer",
    "Double": "java.lang.Double",
    "Float": "java.lang.Float",
    "Long": "java.lang.Long",
    "Byte": "java.lang.Byte",
    "Short": "java.lang.Short",
    # --- java.util / java.io / java.net / java.text ---
    "ArrayList": "java.util.ArrayList",
    "LinkedList": "java.util.LinkedList",
    "HashMap": "java.util.HashMap",
    "HashSet": "java.util.HashSet",
    "Hashtable": "java.util.Hashtable",
    "LinkedHashMap": "java.util.LinkedHashMap",
    "LinkedHashSet": "java.util.LinkedHashSet",
    "TreeMap": "java.util.TreeMap",
    "TreeSet": "java.util.TreeSet",
    "ArrayDeque": "java.util.ArrayDeque",
    "PriorityQueue": "java.util.PriorityQueue",
    "Vector": "java.util.Vector",
    "Stack": "java.util.Stack",
    "Properties": "java.util.Properties",
    "Arrays": "java.util.Arrays",
    "Collections": "java.util.Collections",
    "List": "java.util.List",
    "Map": "java.util.Map",
    "Set": "java.util.Set",
    "Queue": "java.util.Queue",
    "Deque": "java.util.Deque",
    "Iterator": "java.util.Iterator",
    "ListIterator": "java.util.ListIterator",
    "Comparator": "java.util.Comparator",
    "Random": "java.util.Random",
    "Scanner": "java.util.Scanner",
    "StringTokenizer": "java.util.StringTokenizer",
    "Locale": "java.util.Locale",
    "UUID": "java.util.UUID",
    "Optional": "java.util.Optional",
    "Objects": "java.util.Objects",
    "Calendar": "java.util.Calendar",
    "Date": "java.util.Date",
    "TimeZone": "java.util.TimeZone",
    "SimpleDateFormat": "java.text.SimpleDateFormat",
    "File": "java.io.File",
    "FileInputStream": "java.io.FileInputStream",
    "FileOutputStream": "java.io.FileOutputStream",
    "FileReader": "java.io.FileReader",
    "FileWriter": "java.io.FileWriter",
    "BufferedReader": "java.io.BufferedReader",
    "BufferedWriter": "java.io.BufferedWriter",
    "BufferedInputStream": "java.io.BufferedInputStream",
    "BufferedOutputStream": "java.io.BufferedOutputStream",
    "InputStreamReader": "java.io.InputStreamReader",
    "OutputStreamWriter": "java.io.OutputStreamWriter",
    "InputStream": "java.io.InputStream",
    "OutputStream": "java.io.OutputStream",
    "ByteArrayOutputStream": "java.io.ByteArrayOutputStream",
    "ByteArrayInputStream": "java.io.ByteArrayInputStream",
    "PrintStream": "java.io.PrintStream",
    "PrintWriter": "java.io.PrintWriter",
    "StringReader": "java.io.StringReader",
    "StringWriter": "java.io.StringWriter",
    "IOException": "java.io.IOException",
    "FileNotFoundException": "java.io.FileNotFoundException",
    "DataInputStream": "java.io.DataInputStream",
    "DataOutputStream": "java.io.DataOutputStream",
    "ObjectInputStream": "java.io.ObjectInputStream",
    "ObjectOutputStream": "java.io.ObjectOutputStream",
    "Serializable": "java.io.Serializable",
    "URL": "java.net.URL",
    "URLEncoder": "java.net.URLEncoder",
    "URLDecoder": "java.net.URLDecoder",
    "HttpCookie": "java.net.HttpCookie",
    "Timer": "java.util.Timer",
    "TimerTask": "java.util.TimerTask",
    "TimeUnit": "java.util.concurrent.TimeUnit",
    "ThreadLocalRandom": "java.util.concurrent.ThreadLocalRandom",
    "ConcurrentHashMap": "java.util.concurrent.ConcurrentHashMap",
    "Executors": "java.util.concurrent.Executors",
    "ExecutorService": "java.util.concurrent.ExecutorService",
    "AtomicInteger": "java.util.concurrent.atomic.AtomicInteger",
    "AtomicBoolean": "java.util.concurrent.atomic.AtomicBoolean",
    "AtomicLong": "java.util.concurrent.atomic.AtomicLong",
    "AtomicReference": "java.util.concurrent.atomic.AtomicReference",

    # --- v3.2 compatibility expansion (~130 more classes) ---
    # --- org.json (bundled with the Android framework — very common in
    #     AI-generated code) ---
    "JSONObject": "org.json.JSONObject",
    "JSONArray": "org.json.JSONArray",
    "JSONException": "org.json.JSONException",
    "JSONStringer": "org.json.JSONStringer",
    "JSONTokener": "org.json.JSONTokener",

    # --- java.util.regex / math / text / nio ---
    "Pattern": "java.util.regex.Pattern",
    "Matcher": "java.util.regex.Matcher",
    "PatternSyntaxException": "java.util.regex.PatternSyntaxException",
    "BigInteger": "java.math.BigInteger",
    "BigDecimal": "java.math.BigDecimal",
    "MathContext": "java.math.MathContext",
    "DecimalFormat": "java.text.DecimalFormat",
    "NumberFormat": "java.text.NumberFormat",
    "ParseException": "java.text.ParseException",
    "StandardCharsets": "java.nio.charset.StandardCharsets",
    "RandomAccessFile": "java.io.RandomAccessFile",
    "UnsupportedEncodingException": "java.io.UnsupportedEncodingException",

    # --- java.util.concurrent (expanded) ---
    "CountDownLatch": "java.util.concurrent.CountDownLatch",
    "Semaphore": "java.util.concurrent.Semaphore",
    "CyclicBarrier": "java.util.concurrent.CyclicBarrier",
    "LinkedBlockingQueue": "java.util.concurrent.LinkedBlockingQueue",
    "ArrayBlockingQueue": "java.util.concurrent.ArrayBlockingQueue",
    "BlockingQueue": "java.util.concurrent.BlockingQueue",
    "ScheduledExecutorService": "java.util.concurrent.ScheduledExecutorService",
    "Future": "java.util.concurrent.Future",
    "Callable": "java.util.concurrent.Callable",
    "ExecutionException": "java.util.concurrent.ExecutionException",
    "TimeoutException": "java.util.concurrent.TimeoutException",
    "RejectedExecutionException": "java.util.concurrent.RejectedExecutionException",
    "CopyOnWriteArrayList": "java.util.concurrent.CopyOnWriteArrayList",
    "ConcurrentLinkedQueue": "java.util.concurrent.ConcurrentLinkedQueue",
    "ThreadFactory": "java.util.concurrent.ThreadFactory",
    "ReentrantLock": "java.util.concurrent.locks.ReentrantLock",
    "EnumMap": "java.util.EnumMap",
    "EnumSet": "java.util.EnumSet",
    "BitSet": "java.util.BitSet",
    "StringJoiner": "java.util.StringJoiner",

    # --- java.lang (ref / annotations / common) ---
    "CharSequence": "java.lang.CharSequence",
    "Comparable": "java.lang.Comparable",
    "AutoCloseable": "java.lang.AutoCloseable",
    "Iterable": "java.lang.Iterable",
    "Number": "java.lang.Number",
    "Void": "java.lang.Void",
    "SuppressWarnings": "java.lang.SuppressWarnings",
    "FunctionalInterface": "java.lang.FunctionalInterface",
    "SafeVarargs": "java.lang.SafeVarargs",
    "WeakReference": "java.lang.ref.WeakReference",
    "SoftReference": "java.lang.ref.SoftReference",
    "ReferenceQueue": "java.lang.ref.ReferenceQueue",
    "ClassNotFoundException": "java.lang.ClassNotFoundException",
    "CloneNotSupportedException": "java.lang.CloneNotSupportedException",
    "ArithmeticException": "java.lang.ArithmeticException",
    "ArrayIndexOutOfBoundsException": "java.lang.ArrayIndexOutOfBoundsException",
    "StringIndexOutOfBoundsException": "java.lang.StringIndexOutOfBoundsException",
    "OutOfMemoryError": "java.lang.OutOfMemoryError",
    "AssertionError": "java.lang.AssertionError",

    # --- java.security / javax.crypto (crypto is everywhere in AI code) ---
    "MessageDigest": "java.security.MessageDigest",
    "NoSuchAlgorithmException": "java.security.NoSuchAlgorithmException",
    "SecureRandom": "java.security.SecureRandom",
    "KeyFactory": "java.security.KeyFactory",
    "KeyPair": "java.security.KeyPair",
    "KeyPairGenerator": "java.security.KeyPairGenerator",
    "KeyStore": "java.security.KeyStore",
    "PublicKey": "java.security.PublicKey",
    "PrivateKey": "java.security.PrivateKey",
    "GeneralSecurityException": "java.security.GeneralSecurityException",
    "InvalidKeyException": "java.security.InvalidKeyException",
    "SignatureException": "java.security.SignatureException",
    "X509EncodedKeySpec": "java.security.spec.X509EncodedKeySpec",
    "PKCS8EncodedKeySpec": "java.security.spec.PKCS8EncodedKeySpec",
    "Cipher": "javax.crypto.Cipher",
    "SecretKeySpec": "javax.crypto.SecretKeySpec",
    "IvParameterSpec": "javax.crypto.IvParameterSpec",
    "Mac": "javax.crypto.Mac",
    "KeyGenerator": "javax.crypto.KeyGenerator",
    "NoSuchPaddingException": "javax.crypto.NoSuchPaddingException",
    "BadPaddingException": "javax.crypto.BadPaddingException",
    "IllegalBlockSizeException": "javax.crypto.IllegalBlockSizeException",

    # --- java.net (expanded) ---
    "InetSocketAddress": "java.net.InetSocketAddress",
    "SocketTimeoutException": "java.net.SocketTimeoutException",
    "UnknownHostException": "java.net.UnknownHostException",
    "SocketException": "java.net.SocketException",
    "NetworkInterface": "java.net.NetworkInterface",
    "URISyntaxException": "java.net.URISyntaxException",
    # NOTE: java.net.Proxy is intentionally NOT keyed "Proxy" — that key maps
    # to java.lang.reflect.Proxy (Proxy.newProxyInstance is the dominant use in
    # generated code). Use the fully-qualified java.net.Proxy for sockets.

    # --- java.time (API 26+ — the MIN-SDK ADVISOR raises minSdk for these) ---
    "LocalDate": "java.time.LocalDate",
    "LocalTime": "java.time.LocalTime",
    "LocalDateTime": "java.time.LocalDateTime",
    "ZonedDateTime": "java.time.ZonedDateTime",
    "ZoneId": "java.time.ZoneId",
    "ZoneOffset": "java.time.ZoneOffset",
    "DateTimeFormatter": "java.time.format.DateTimeFormatter",
    "Duration": "java.time.Duration",
    "Instant": "java.time.Instant",
    "Period": "java.time.Period",

    # --- java.util.stream (API 24+ — advisor handles minSdk) ---
    "Collectors": "java.util.stream.Collectors",
    "Stream": "java.util.stream.Stream",

    # --- android.animation (property animation framework) ---
    "ObjectAnimator": "android.animation.ObjectAnimator",
    "ValueAnimator": "android.animation.ValueAnimator",
    "AnimatorSet": "android.animation.AnimatorSet",
    "Animator": "android.animation.Animator",
    "AnimatorListenerAdapter": "android.animation.AnimatorListenerAdapter",
    "TimeInterpolator": "android.animation.TimeInterpolator",
    "TypeEvaluator": "android.animation.TypeEvaluator",
    "FloatEvaluator": "android.animation.FloatEvaluator",
    "IntEvaluator": "android.animation.IntEvaluator",

    # --- android.transition (scene transitions, API 19+) ---
    "TransitionManager": "android.transition.TransitionManager",
    "Transition": "android.transition.Transition",
    "AutoTransition": "android.transition.AutoTransition",
    "Fade": "android.transition.Fade",
    "Slide": "android.transition.Slide",
    "ChangeBounds": "android.transition.ChangeBounds",

    # --- android.view (expanded) ---
    "TextureView": "android.view.TextureView",
    "ViewPropertyAnimator": "android.view.ViewPropertyAnimator",
    "ViewConfiguration": "android.view.ViewConfiguration",
    "ViewOutlineProvider": "android.view.ViewOutlineProvider",
    "Surface": "android.view.Surface",
    "ViewOverlay": "android.view.ViewOverlay",
    "View.OnLayoutChangeListener": "android.view.View",

    # --- android.widget (expanded) ---
    "Toolbar": "android.widget.Toolbar",
    "AutoCompleteTextView": "android.widget.AutoCompleteTextView",
    "MultiAutoCompleteTextView": "android.widget.MultiAutoCompleteTextView",
    "CheckedTextView": "android.widget.CheckedTextView",
    "AdapterViewFlipper": "android.widget.AdapterViewFlipper",
    "StackView": "android.widget.StackView",
    "AbsListView": "android.widget.AbsListView",
    "CursorAdapter": "android.widget.CursorAdapter",
    "SimpleCursorAdapter": "android.widget.SimpleCursorAdapter",

    # --- android.app (expanded) ---
    "ActivityManager": "android.app.ActivityManager",
    "ActivityOptions": "android.app.ActivityOptions",
    "ExpandableListActivity": "android.app.ExpandableListActivity",
    "DialogFragment": "android.app.DialogFragment",
    "ListFragment": "android.app.ListFragment",
    "FragmentManager": "android.app.FragmentManager",
    "FragmentTransaction": "android.app.FragmentTransaction",
    "SearchManager": "android.app.SearchManager",
    "UiModeManager": "android.app.UiModeManager",
    "JobInfo": "android.app.job.JobInfo",
    "JobParameters": "android.app.job.JobParameters",
    "JobScheduler": "android.app.job.JobScheduler",
    "JobService": "android.app.job.JobService",

    # --- android.content (expanded: pm / res / more) ---
    "PackageManager": "android.content.pm.PackageManager",
    "PackageInfo": "android.content.pm.PackageInfo",
    "ApplicationInfo": "android.content.pm.ApplicationInfo",
    "ActivityInfo": "android.content.pm.ActivityInfo",
    "ServiceInfo": "android.content.pm.ServiceInfo",
    "ProviderInfo": "android.content.pm.ProviderInfo",
    "ActivityNotFoundException": "android.content.ActivityNotFoundException",
    "IntentSender": "android.content.IntentSender",
    "ContentProviderOperation": "android.content.ContentProviderOperation",
    "ContentProviderResult": "android.content.ContentProviderResult",
    "ContentUris": "android.content.ContentUris",
    "Resources": "android.content.res.Resources",
    "ColorStateList": "android.content.res.ColorStateList",
    "Configuration": "android.content.res.Configuration",
    "TypedArray": "android.content.res.TypedArray",
    "AssetManager": "android.content.res.AssetManager",
    "AssetFileDescriptor": "android.content.res.AssetFileDescriptor",

    # --- android.media (expanded) ---
    "AudioAttributes": "android.media.AudioAttributes",
    "MediaCodec": "android.media.MediaCodec",
    "MediaFormat": "android.media.MediaFormat",
    "MediaExtractor": "android.media.MediaExtractor",
    "MediaMuxer": "android.media.MediaMuxer",
    "MediaSession": "android.media.session.MediaSession",

    # --- android.hardware (expanded: camera2 + biometrics) ---
    "CameraDevice": "android.hardware.camera2.CameraDevice",
    "CameraCaptureSession": "android.hardware.camera2.CameraCaptureSession",
    "CaptureRequest": "android.hardware.camera2.CaptureRequest",
    "CaptureResult": "android.hardware.camera2.CaptureResult",
    "CameraCharacteristics": "android.hardware.camera2.CameraCharacteristics",
    "FingerprintManager": "android.hardware.fingerprint.FingerprintManager",
    "BiometricPrompt": "android.hardware.biometrics.BiometricPrompt",

    # --- android.speech / tts ---
    "TextToSpeech": "android.speech.tts.TextToSpeech",
    "SpeechRecognizer": "android.speech.SpeechRecognizer",
    "RecognizerIntent": "android.speech.RecognizerIntent",
    "RecognitionListener": "android.speech.RecognitionListener",

    # --- android.opengl ---
    "GLSurfaceView": "android.opengl.GLSurfaceView",
    "GLES20": "android.opengl.GLES20",
    "GLES30": "android.opengl.GLES30",
    "GLUtils": "android.opengl.GLUtils",

    # --- android.graphics (expanded) ---
    "LightingColorFilter": "android.graphics.LightingColorFilter",
    "AnimatedVectorDrawable": "android.graphics.drawable.AnimatedVectorDrawable",
    "TransitionDrawable": "android.graphics.drawable.TransitionDrawable",
    "RotateDrawable": "android.graphics.drawable.RotateDrawable",
    "ScaleDrawable": "android.graphics.drawable.ScaleDrawable",
    "PictureDrawable": "android.graphics.drawable.PictureDrawable",

    # --- android.os (expanded) ---
    "Parcel": "android.os.Parcel",
    "ParcelFileDescriptor": "android.os.ParcelFileDescriptor",
    "RemoteException": "android.os.RemoteException",
    "DeadObjectException": "android.os.DeadObjectException",
    "Binder": "android.os.Binder",
    "IBinder": "android.os.IBinder",
    "Messenger": "android.os.Messenger",
    "HandlerThread": "android.os.HandlerThread",
    "ResultReceiver": "android.os.ResultReceiver",
    "UserHandle": "android.os.UserHandle",
    "PersistableBundle": "android.os.PersistableBundle",

    # --- android.text / net (expanded) ---
    "SpannableStringBuilder": "android.text.SpannableStringBuilder",
    "TextPaint": "android.text.TextPaint",
    "WifiConfiguration": "android.net.wifi.WifiConfiguration",
    "DownloadListener": "android.webkit.DownloadListener",

    # --- v3.3 compatibility expansion #2 (~210 more classes) ---
    # --- android.service.* + device admin ---
    "TileService": "android.service.quicksettings.TileService",
    "WallpaperService": "android.service.wallpaper.WallpaperService",
    "DreamService": "android.service.dreams.DreamService",
    "NotificationListenerService": "android.service.notification.NotificationListenerService",
    "VoiceInteractionService": "android.service.voice.VoiceInteractionService",
    "AccessibilityService": "android.accessibilityservice.AccessibilityService",
    "DeviceAdminReceiver": "android.app.admin.DeviceAdminReceiver",
    "DevicePolicyManager": "android.app.admin.DevicePolicyManager",

    # --- app widgets / usage stats / presentation ---
    "AppWidgetProvider": "android.appwidget.AppWidgetProvider",
    "AppWidgetManager": "android.appwidget.AppWidgetManager",
    "RemoteViews": "android.widget.RemoteViews",
    "UsageStatsManager": "android.app.usage.UsageStatsManager",
    "Presentation": "android.app.Presentation",

    # --- telecom / telephony (expanded) ---
    "TelecomManager": "android.telecom.TelecomManager",
    "PhoneStateListener": "android.telephony.PhoneStateListener",
    "ServiceState": "android.telephony.ServiceState",
    "SubscriptionManager": "android.telephony.SubscriptionManager",
    "SignalStrength": "android.telephony.SignalStrength",

    # --- android.text (spans, methods, format) ---
    "Linkify": "android.text.util.Linkify",
    "LinkMovementMethod": "android.text.method.LinkMovementMethod",
    "ScrollingMovementMethod": "android.text.method.ScrollingMovementMethod",
    "DateUtils": "android.text.format.DateUtils",
    "UnderlineSpan": "android.text.style.UnderlineSpan",
    "StrikethroughSpan": "android.text.style.StrikethroughSpan",
    "ClickableSpan": "android.text.style.ClickableSpan",
    "URLSpan": "android.text.style.URLSpan",
    "ImageSpan": "android.text.style.ImageSpan",
    "BackgroundColorSpan": "android.text.style.BackgroundColorSpan",
    "AbsoluteSizeSpan": "android.text.style.AbsoluteSizeSpan",
    "RelativeSizeSpan": "android.text.style.RelativeSizeSpan",
    "TypefaceSpan": "android.text.style.TypefaceSpan",
    "BulletSpan": "android.text.style.BulletSpan",
    "QuoteSpan": "android.text.style.QuoteSpan",

    # --- android.media (audiofx, projection, browse, router) ---
    "AudioEffect": "android.media.audiofx.AudioEffect",
    "Equalizer": "android.media.audiofx.Equalizer",
    "Visualizer": "android.media.audiofx.Visualizer",
    "BassBoost": "android.media.audiofx.BassBoost",
    "PresetReverb": "android.media.audiofx.PresetReverb",
    "Virtualizer": "android.media.audiofx.Virtualizer",
    "MediaProjectionManager": "android.media.projection.MediaProjectionManager",
    "MediaBrowser": "android.media.browse.MediaBrowser",
    "MediaRouter": "android.media.MediaRouter",
    "AudioDeviceInfo": "android.media.AudioDeviceInfo",
    "AudioFocusRequest": "android.media.AudioFocusRequest",
    "PlaybackState": "android.media.session.PlaybackState",
    "MediaMetadata": "android.media.session.MediaMetadata",

    # --- android.os (expanded #2) ---
    "CancellationSignal": "android.os.CancellationSignal",
    "StatFs": "android.os.StatFs",
    "StorageManager": "android.os.storage.StorageManager",
    "StorageVolume": "android.os.storage.StorageVolume",

    # --- android.view (expanded #2) ---
    "MenuInflater": "android.view.MenuInflater",
    "WindowInsets": "android.view.WindowInsets",
    "ContextThemeWrapper": "android.view.ContextThemeWrapper",
    "PathInterpolator": "android.view.animation.PathInterpolator",
    "AccelerateDecelerateInterpolator": "android.view.animation.AccelerateDecelerateInterpolator",
    "AnticipateOvershootInterpolator": "android.view.animation.AnticipateOvershootInterpolator",
    "AccessibilityNodeInfo": "android.view.accessibility.AccessibilityNodeInfo",
    "AutofillManager": "android.view.autofill.AutofillManager",

    # --- android.widget (expanded #2) ---
    "ExpandableListView": "android.widget.ExpandableListView",
    "ExpandableListAdapter": "android.widget.ExpandableListAdapter",
    "SimpleExpandableListAdapter": "android.widget.SimpleExpandableListAdapter",
    "NumberPicker": "android.widget.NumberPicker",
    "GestureOverlayView": "android.widget.GestureOverlayView",
    "SlidingDrawer": "android.widget.SlidingDrawer",
    "ListPopupWindow": "android.widget.ListPopupWindow",
    "PopupWindow": "android.widget.PopupWindow",

    # --- android.graphics (expanded #2: shapes, pdf, misc) ---
    "OvalShape": "android.graphics.drawable.shapes.OvalShape",
    "RectShape": "android.graphics.drawable.shapes.RectShape",
    "RoundRectShape": "android.graphics.drawable.shapes.RoundRectShape",
    "ArcShape": "android.graphics.drawable.shapes.ArcShape",
    "PdfDocument": "android.graphics.pdf.PdfDocument",
    "Icon": "android.graphics.drawable.Icon",
    "Picture": "android.graphics.Picture",
    "ColorSpace": "android.graphics.ColorSpace",
    "BlendModeColorFilter": "android.graphics.BlendModeColorFilter",

    # --- android.database (SQLite) ---
    "SQLiteDatabase": "android.database.sqlite.SQLiteDatabase",
    "SQLiteOpenHelper": "android.database.sqlite.SQLiteOpenHelper",
    "SQLiteException": "android.database.sqlite.SQLiteException",
    "SQLiteStatement": "android.database.sqlite.SQLiteStatement",
    "CursorWindow": "android.database.CursorWindow",
    "DatabaseUtils": "android.database.DatabaseUtils",

    # --- android.hardware (usb, display) ---
    "UsbDevice": "android.hardware.usb.UsbDevice",
    "UsbInterface": "android.hardware.usb.UsbInterface",
    "UsbEndpoint": "android.hardware.usb.UsbEndpoint",
    "UsbRequest": "android.hardware.usb.UsbRequest",
    "UsbDeviceConnection": "android.hardware.usb.UsbDeviceConnection",
    "UsbConstants": "android.hardware.usb.UsbConstants",
    "UsbAccessory": "android.hardware.usb.UsbAccessory",
    "DisplayManager": "android.hardware.display.DisplayManager",
    "VirtualDisplay": "android.hardware.display.VirtualDisplay",
    "TriggerEventListener": "android.hardware.TriggerEventListener",

    # --- android.net (expanded #2) ---
    "NsdManager": "android.net.nsd.NsdManager",
    "WifiP2pManager": "android.net.wifi.p2p.WifiP2pManager",
    "TrafficStats": "android.net.TrafficStats",
    "NetworkCallback": "android.net.ConnectivityManager.NetworkCallback",
    "LinkProperties": "android.net.LinkProperties",
    "NetworkCapabilities": "android.net.NetworkCapabilities",
    "NetworkRequest": "android.net.NetworkRequest",
    "LocalSocket": "android.net.LocalSocket",
    "LocalServerSocket": "android.net.LocalServerSocket",

    # --- android.nfc ---
    "NfcAdapter": "android.nfc.NfcAdapter",
    "NdefMessage": "android.nfc.NdefMessage",
    "NdefRecord": "android.nfc.NdefRecord",
    "Ndef": "android.nfc.tech.Ndef",
    "Tag": "android.nfc.Tag",

    # --- android.bluetooth.le (API 21+) ---
    "BluetoothLeScanner": "android.bluetooth.le.BluetoothLeScanner",
    "ScanFilter": "android.bluetooth.le.ScanFilter",
    "ScanSettings": "android.bluetooth.le.ScanSettings",
    "ScanResult": "android.bluetooth.le.ScanResult",
    "ScanCallback": "android.bluetooth.le.ScanCallback",

    # --- android.location / provider (expanded) ---
    "Geofence": "android.location.Geofence",
    "LocationRequest": "android.location.LocationRequest",
    "DocumentsContract": "android.provider.DocumentsContract",
    "UserDictionary": "android.provider.UserDictionary",

    # --- android.security.keystore ---
    "KeyGenParameterSpec": "android.security.keystore.KeyGenParameterSpec",
    "KeyProperties": "android.security.keystore.KeyProperties",

    # --- android.system / renderscript / preference ---
    "Os": "android.system.Os",
    "OsConstants": "android.system.OsConstants",
    "RenderScript": "android.renderscript.RenderScript",
    "PreferenceActivity": "android.preference.PreferenceActivity",
    "PreferenceFragment": "android.preference.PreferenceFragment",
    "PreferenceManager": "android.preference.PreferenceManager",

    # --- speech tts (expanded) ---
    "UtteranceProgressListener": "android.speech.tts.UtteranceProgressListener",

    # --- XML parsing (all bundled with Android) ---
    "Xml": "android.util.Xml",
    "XmlPullParser": "org.xmlpull.v1.XmlPullParser",
    "XmlSerializer": "org.xmlpull.v1.XmlSerializer",
    "DocumentBuilder": "javax.xml.parsers.DocumentBuilder",
    "DocumentBuilderFactory": "javax.xml.parsers.DocumentBuilderFactory",
    "SAXParser": "javax.xml.parsers.SAXParser",
    "SAXParserFactory": "javax.xml.parsers.SAXParserFactory",
    "Document": "org.w3c.dom.Document",
    "Element": "org.w3c.dom.Element",
    "Node": "org.w3c.dom.Node",
    "NodeList": "org.w3c.dom.NodeList",
    "SAXException": "org.xml.sax.SAXException",

    # --- java.security.cert / javax.net.ssl ---
    "Certificate": "java.security.cert.Certificate",
    "X509Certificate": "java.security.cert.X509Certificate",
    "CertificateException": "java.security.cert.CertificateException",
    "CertificateFactory": "java.security.cert.CertificateFactory",
    "SSLContext": "javax.net.ssl.SSLContext",
    "SSLSocketFactory": "javax.net.ssl.SSLSocketFactory",
    "TrustManager": "javax.net.ssl.TrustManager",
    "X509TrustManager": "javax.net.ssl.X509TrustManager",
    "HostnameVerifier": "javax.net.ssl.HostnameVerifier",
    "KeyManagerFactory": "javax.net.ssl.KeyManagerFactory",
    "TrustManagerFactory": "javax.net.ssl.TrustManagerFactory",

    # --- java.io (expanded #2) ---
    "FilenameFilter": "java.io.FilenameFilter",
    "FileFilter": "java.io.FileFilter",
    "EOFException": "java.io.EOFException",
    "CharArrayReader": "java.io.CharArrayReader",
    "CharArrayWriter": "java.io.CharArrayWriter",
    "SequenceInputStream": "java.io.SequenceInputStream",
    "LineNumberReader": "java.io.LineNumberReader",
    "PushbackInputStream": "java.io.PushbackInputStream",
    "PushbackReader": "java.io.PushbackReader",
    "StreamTokenizer": "java.io.StreamTokenizer",
    "NotSerializableException": "java.io.NotSerializableException",
    "InvalidClassException": "java.io.InvalidClassException",
    "ObjectStreamException": "java.io.ObjectStreamException",

    # --- java.lang (expanded #2: reflect & misc) ---
    "ThreadLocal": "java.lang.ThreadLocal",
    "InheritableThreadLocal": "java.lang.InheritableThreadLocal",
    "ProcessBuilder": "java.lang.ProcessBuilder",
    "StackTraceElement": "java.lang.StackTraceElement",
    "Appendable": "java.lang.Appendable",
    "Readable": "java.lang.Readable",
    "Method": "java.lang.reflect.Method",
    "Field": "java.lang.reflect.Field",
    "Constructor": "java.lang.reflect.Constructor",
    "Modifier": "java.lang.reflect.Modifier",
    "Proxy": "java.lang.reflect.Proxy",
    "InvocationTargetException": "java.lang.reflect.InvocationTargetException",
    "ReflectiveOperationException": "java.lang.ReflectiveOperationException",

    # --- java.util (expanded #2) ---
    "Currency": "java.util.Currency",
    "Formatter": "java.util.Formatter",
    "NoSuchElementException": "java.util.NoSuchElementException",
    "ConcurrentModificationException": "java.util.ConcurrentModificationException",
    "InputMismatchException": "java.util.InputMismatchException",
    "NavigableMap": "java.util.NavigableMap",
    "NavigableSet": "java.util.NavigableSet",
    "SortedMap": "java.util.SortedMap",
    "SortedSet": "java.util.SortedSet",
    "IntSummaryStatistics": "java.util.IntSummaryStatistics",
    "DoubleSummaryStatistics": "java.util.DoubleSummaryStatistics",
    "LongSummaryStatistics": "java.util.LongSummaryStatistics",
    "Spliterator": "java.util.Spliterator",
    "OptionalInt": "java.util.OptionalInt",
    "OptionalLong": "java.util.OptionalLong",
    "OptionalDouble": "java.util.OptionalDouble",

    # --- java.util.function (d8-desugared; advisor notes API 24) ---
    "Function": "java.util.function.Function",
    "BiFunction": "java.util.function.BiFunction",
    "Consumer": "java.util.function.Consumer",
    "BiConsumer": "java.util.function.BiConsumer",
    "Supplier": "java.util.function.Supplier",
    "Predicate": "java.util.function.Predicate",
    "BiPredicate": "java.util.function.BiPredicate",
    "UnaryOperator": "java.util.function.UnaryOperator",
    "BinaryOperator": "java.util.function.BinaryOperator",

    # --- java.util.stream / java.nio.file (API 24 / 26) ---
    "IntStream": "java.util.stream.IntStream",
    "LongStream": "java.util.stream.LongStream",
    "DoubleStream": "java.util.stream.DoubleStream",
    "Paths": "java.nio.file.Paths",
    "Files": "java.nio.file.Files",
}


# --- Usage signatures → permission strings (auto-permission detection) ---
# Order matters only for UI listing; each entry: (permission, [tokens...]).
PERMISSION_SIGNATURES: List[Tuple[str, List[str]]] = [
    ("android.permission.INTERNET",
     ["WebView", "HttpURLConnection", "HttpsURLConnection", "URLConnection", "Socket",
      "ServerSocket", "URL", "DownloadManager", "HttpCookie", "DatagramSocket"]),
    ("android.permission.CAMERA", ["Camera", "CameraManager", "CameraDevice",
                                   "CameraCaptureSession", "MediaStore.ACTION_IMAGE_CAPTURE"]),
    ("android.permission.RECORD_AUDIO", ["MediaRecorder", "AudioRecord", "SpeechRecognizer"]),
    ("android.permission.ACCESS_FINE_LOCATION",
     ["LocationManager", "getLastKnownLocation", "requestLocationUpdates", "Geocoder"]),
    ("android.permission.ACCESS_COARSE_LOCATION", ["LocationManager", "Geocoder"]),
    ("android.permission.ACCESS_NETWORK_STATE", ["ConnectivityManager", "NetworkInfo", "Network"]),
    ("android.permission.ACCESS_WIFI_STATE", ["WifiManager", "WifiInfo", "ScanResult"]),
    ("android.permission.VIBRATE", ["Vibrator", "VibrationEffect", "ToneGenerator"]),
    ("android.permission.BLUETOOTH", ["BluetoothAdapter", "BluetoothDevice", "BluetoothSocket"]),
    ("android.permission.BLUETOOTH_CONNECT", ["BluetoothAdapter", "BluetoothDevice"]),
    ("android.permission.READ_CONTACTS", ["ContactsContract", "CallLog"]),
    ("android.permission.WRITE_CONTACTS", ["ContactsContract"]),
    ("android.permission.CALL_PHONE", ["ACTION_CALL", "TelephonyManager"]),
    ("android.permission.SEND_SMS", ["SmsManager", "SmsMessage"]),
    ("android.permission.READ_SMS", ["SmsMessage", "Telephony.Sms"]),
    ("android.permission.READ_PHONE_STATE", ["TelephonyManager", "getDeviceId", "getSimSerialNumber"]),
    ("android.permission.READ_EXTERNAL_STORAGE", ["Environment.getExternalStorageDirectory", "MediaStore"]),
    ("android.permission.WRITE_EXTERNAL_STORAGE",
     ["Environment.getExternalStorageDirectory", "MediaStore", "DownloadManager"]),
    ("android.permission.BODY_SENSORS", ["SensorManager", "SensorEvent"]),
    ("android.permission.POST_NOTIFICATIONS", ["NotificationChannel", "NotificationManager"]),
    # v3.2 additions:
    ("android.permission.WAKE_LOCK", ["newWakeLock", "WakeLock"]),
    ("android.permission.FOREGROUND_SERVICE", ["startForeground"]),
    ("android.permission.ACTIVITY_RECOGNITION", ["TYPE_STEP_COUNTER", "TYPE_STEP_DETECTOR"]),
    # v3.3 additions:
    ("android.permission.READ_CALENDAR", ["CalendarContract"]),
    ("android.permission.WRITE_CALENDAR", ["CalendarContract"]),
    ("android.permission.NFC", ["NfcAdapter"]),
    ("android.permission.USE_BIOMETIC", ["BiometricPrompt"]),
    ("android.permission.USE_FINGERPRINT", ["FingerprintManager"]),
    ("android.permission.RECEIVE_BOOT_COMPLETED", ["BOOT_COMPLETED"]),
    ("android.permission.MODIFY_AUDIO_SETTINGS",
     ["AudioEffect", "Equalizer", "Visualizer", "BassBoost"]),
    ("android.permission.BLUETOOTH_SCAN", ["BluetoothLeScanner"]),
    ("android.permission.SCHEDULE_EXACT_ALARM", ["setExactAndAllowWhileIdle"]),
    ("android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
     ["ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS"]),
]


# --- API tokens that require a minimum SDK level (min-SDK advisor) ---
MIN_SDK_TOKENS: List[Tuple[int, List[str]]] = [
    (24, ["java.util.stream", "IntStream", "LongStream", "DoubleStream",
          "parallelStream()", "Collectors", "java.util.function.",
          "Optional", "StringJoiner", "Spliterator",
          "IntSummaryStatistics", "DoubleSummaryStatistics", "LongSummaryStatistics"]),
    (26, ["NotificationChannel", "java.time.", "LocalDate", "LocalTime", "LocalDateTime",
          "ZonedDateTime", "Duration.of", "Instant.now", "ZoneId", "DateTimeFormatter",
          "java.nio.file.", "Files.", "Paths.", "AudioFocusRequest", "AutofillManager",
          "ColorSpace"]),
    (23, ["FingerprintManager", "AudioDeviceInfo"]),
    (28, ["BiometricPrompt", "ImageDecoder"]),
    (29, ["BluetoothLeScanner", "ScanCallback", "BiometricManager", "WifiNetworkSuggestion",
          "BlendModeColorFilter"]),
    (30, ["InsetsController", "setSystemBarsBehavior"]),
    (31, ["BLUETOOTH_CONNECT", "LocationRequest"]),
]


# --- androidx → framework migration map (diagnostics "try auto-migrate") ---
# Conservative mapping; only entries that map cleanly are included.
ANDROIDX_MIGRATIONS: Dict[str, str] = {
    "androidx.appcompat.app.AppCompatActivity": "android.app.Activity",
    "androidx.appcompat.app.AlertDialog": "android.app.AlertDialog",
    "androidx.annotation.NonNull": "",
    "androidx.annotation.Nullable": "",
    "androidx.annotation.SuppressLint": "",
    "androidx.annotation.WorkerThread": "",
    "androidx.annotation.MainThread": "",
    "androidx.fragment.app.Fragment": "android.app.Fragment",
    # v3.2 additions:
    "androidx.fragment.app.DialogFragment": "android.app.DialogFragment",
    "androidx.fragment.app.ListFragment": "android.app.ListFragment",
    "androidx.core.util.Pair": "android.util.Pair",
    "androidx.annotation.AnyThread": "",
    "androidx.annotation.UiThread": "",
    "androidx.annotation.BinderThread": "",
    "androidx.annotation.CallSuper": "",
    "androidx.annotation.CheckResult": "",
    "androidx.annotation.ColorInt": "",
    "androidx.annotation.ColorRes": "",
    "androidx.annotation.Dimension": "",
    "androidx.annotation.DrawableRes": "",
    "androidx.annotation.IdRes": "",
    "androidx.annotation.IntDef": "",
    "androidx.annotation.IntRange": "",
    "androidx.annotation.LongDef": "",
    "androidx.annotation.LayoutRes": "",
    "androidx.annotation.StringRes": "",
    "androidx.annotation.StringDef": "",
    "androidx.annotation.VisibleForTesting": "",
    # v3.3 additions:
    "androidx.core.app.NotificationCompat": "android.app.Notification",
    "androidx.core.app.NotificationCompat.Builder": "android.app.Notification.Builder",
    "androidx.fragment.app.FragmentActivity": "android.app.Activity",
    "androidx.appcompat.widget.Toolbar": "android.widget.Toolbar",
    "androidx.core.app.JobIntentService": "android.app.IntentService",
}


# ---------------------------------------------------------------------------
# Smart Java templates — Source page "Insert template"
# ---------------------------------------------------------------------------
# Full-class templates are complete apps: multiple classes in one file are
# supported and split automatically — exactly what AI models produce.
TEMPLATES = {
    "Hello World (snippet)": '''TextView hello = new TextView(this);
hello.setText("Hello from APK Forge!");
hello.setTextSize(22);
hello.setPadding(32, 32, 32, 32);
setContentView(hello);''',

    "Tap Counter (snippet)": '''Button btn = new Button(this);
btn.setText("Tap me: 0");
final int[] count = {0};
btn.setOnClickListener(v -> {
    count[0]++;
    btn.setText("Tap me: " + count[0]);
});
setContentView(btn);''',

    "Full Class Skeleton (full class)": '''package com.example.myapp;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    private TextView status;
    private Button actionBtn;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(32, 32, 32, 32);

        status = new TextView(this);
        status.setText("Welcome to APK Forge");
        status.setTextSize(20);
        root.addView(status);

        actionBtn = new Button(this);
        actionBtn.setText("Click me");
        actionBtn.setOnClickListener(v -> status.setText("Forge complete!"));
        root.addView(actionBtn);

        setContentView(root);
    }
}''',

    "WebView App (full class)": '''package com.example.webview;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl("https://example.com");
        setContentView(webView);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}''',

    "Calculator (full class, multi-class demo)": '''package com.example.calculator;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private EditText inputA, inputB;
    private TextView result;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(24, 24, 24, 24);

        inputA = new EditText(this);
        inputA.setHint("First number");
        inputA.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        root.addView(inputA);

        inputB = new EditText(this);
        inputB.setHint("Second number");
        inputB.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        root.addView(inputB);

        result = new TextView(this);
        result.setTextSize(24);
        result.setPadding(0, 24, 0, 24);
        root.addView(result);

        LinearLayout ops = new LinearLayout(this);
        ops.setOrientation(LinearLayout.HORIZONTAL);
        for (final char op : new char[]{'+', '-', '*', '/'}) {
            Button b = new Button(this);
            b.setText(String.valueOf(op));
            b.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    try {
                        double a = Double.parseDouble(inputA.getText().toString());
                        double b = Double.parseDouble(inputB.getText().toString());
                        double r = MathOps.compute(a, b, op);
                        result.setText(a + " " + op + " " + b + " = " + MathOps.fmt(r));
                    } catch (Exception e) {
                        result.setText("Invalid input");
                    }
                }
            });
            ops.addView(b, new LinearLayout.LayoutParams(0,
                    LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        }
        root.addView(ops);

        setContentView(root);
    }
}

// Second top-level class in the SAME file — APK Forge splits it automatically.
class MathOps {
    static double compute(double a, double b, char op) {
        switch (op) {
            case '+': return a + b;
            case '-': return a - b;
            case '*': return a * b;
            case '/': return b == 0 ? Double.NaN : a / b;
            default:  throw new IllegalArgumentException("op " + op);
        }
    }

    static String fmt(double v) {
        if (Double.isNaN(v)) return "∞";
        if (v == Math.floor(v) && !Double.isInfinite(v)) return String.valueOf((long) v);
        return String.valueOf(v);
    }
}''',

    "Notes with SharedPreferences (full class)": '''package com.example.notes;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private EditText input;
    private TextView saved;
    private SharedPreferences prefs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("notes", Context.MODE_PRIVATE);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(24, 24, 24, 24);

        TextView title = new TextView(this);
        title.setText("Persistent Note");
        title.setTextSize(20);
        root.addView(title);

        input = new EditText(this);
        input.setHint("Type your note…");
        input.setText(prefs.getString("note", ""));
        root.addView(input);

        saved = new TextView(this);
        saved.setPadding(0, 16, 0, 16);
        root.addView(saved);

        Button save = new Button(this);
        save.setText("Save note");
        save.setOnClickListener(v -> {
            prefs.edit().putString("note", input.getText().toString()).apply();
            Toast.makeText(this, "Saved!", Toast.LENGTH_SHORT).show();
            refresh();
        });
        root.addView(save);

        setContentView(root);
        refresh();
    }

    private void refresh() {
        saved.setText("Stored: " + prefs.getString("note", "(empty)"));
    }
}''',

    "Canvas Drawing (full class, custom View)": '''package com.example.canvas;

import android.app.Activity;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.View;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(new DrawView(this));
    }
}

class DrawView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private float lastX = -1, lastY = -1;

    public DrawView(Context context) {
        super(context);
        paint.setColor(Color.rgb(68, 214, 44));
        paint.setStrokeWidth(8f);
        paint.setStyle(Paint.Style.STROKE);
        setBackgroundColor(Color.rgb(13, 13, 13));
    }

    @Override
    protected void onDraw(Canvas canvas) {
        canvas.drawColor(Color.rgb(13, 13, 13));
        if (lastX >= 0) canvas.drawCircle(lastX, lastY, 40f, paint);
    }

    @Override
    public boolean onTouchEvent(MotionEvent event) {
        if (event.getAction() == MotionEvent.ACTION_DOWN
                || event.getAction() == MotionEvent.ACTION_MOVE) {
            lastX = event.getX();
            lastY = event.getY();
            invalidate();
            return true;
        }
        return false;
    }
}''',

    "Sensor Dashboard (full class + service)": '''package com.example.sensors;

import android.app.Activity;
import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity implements SensorEventListener {
    private SensorManager sensorManager;
    private TextView accelText, lightText, stepText;
    private int steps = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(24, 24, 24, 24);

        accelText = big("Accelerometer: —");
        lightText = big("Light: —");
        stepText = big("Steps: 0");
        root.addView(accelText);
        root.addView(lightText);
        root.addView(stepText);
        setContentView(root);
    }

    private TextView big(String s) {
        TextView tv = new TextView(this);
        tv.setText(s);
        tv.setTextSize(22);
        tv.setPadding(0, 18, 0, 18);
        return tv;
    }

    @Override
    protected void onResume() {
        super.onResume();
        register(Sensor.TYPE_ACCELEROMETER);
        register(Sensor.TYPE_LIGHT);
        register(Sensor.TYPE_STEP_COUNTER);
    }

    private void register(int type) {
        Sensor s = sensorManager.getDefaultSensor(type);
        if (s != null) sensorManager.registerListener(this, s, SensorManager.SENSOR_DELAY_NORMAL);
    }

    @Override
    protected void onPause() {
        super.onPause();
        sensorManager.unregisterListener(this);
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
            accelText.setText(String.format("Accelerometer:%n%.2f %.2f %.2f",
                    event.values[0], event.values[1], event.values[2]));
        } else if (event.sensor.getType() == Sensor.TYPE_LIGHT) {
            lightText.setText("Light: " + event.values[0]);
        } else if (event.sensor.getType() == Sensor.TYPE_STEP_COUNTER) {
            steps = (int) event.values[0];
            stepText.setText("Steps: " + steps);
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) { }
}

// A background service in the same file — auto-registered in the manifest.
class SensorLogService extends android.app.Service {
    @Override
    public int onStartCommand(android.content.Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    @Override
    public android.os.IBinder onBind(android.content.Intent intent) {
        return null;
    }
}''',

    "List with Adapter (full class, 3 classes)": '''package com.example.listapp;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.BaseAdapter;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        List<Item> items = new ArrayList<>();
        for (int i = 1; i <= 40; i++) items.add(new Item("Row " + i, "Subtitle for row " + i));

        ListView list = new ListView(this);
        list.setAdapter(new ItemAdapter(this, items));
        list.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                Toast.makeText(MainActivity.this, "Clicked row " + (position + 1),
                        Toast.LENGTH_SHORT).show();
            }
        });
        setContentView(list);
    }
}

class Item {
    final String title, subtitle;
    Item(String title, String subtitle) { this.title = title; this.subtitle = subtitle; }
}

class ItemAdapter extends BaseAdapter {
    private final List<Item> data;
    private final android.content.Context ctx;

    ItemAdapter(android.content.Context ctx, List<Item> data) {
        this.ctx = ctx;
        this.data = data;
    }

    @Override public int getCount() { return data.size(); }
    @Override public Object getItem(int position) { return data.get(position); }
    @Override public long getItemId(int position) { return position; }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        LinearLayout row = (convertView instanceof LinearLayout)
                ? (LinearLayout) convertView : new LinearLayout(ctx);
        row.setOrientation(LinearLayout.VERTICAL);
        row.setPadding(28, 20, 28, 20);

        TextView title = new TextView(ctx);
        title.setText(data.get(position).title);
        title.setTextSize(17);
        title.setTextColor(0xFFE8E8E6);
        row.addView(title);

        TextView sub = new TextView(ctx);
        sub.setText(data.get(position).subtitle);
        sub.setTextSize(13);
        sub.setTextColor(0xFF9A9C98);
        row.addView(sub);
        return row;
    }
}''',

    "Notification + Alarm (full class, receiver)": '''package com.example.notifier;

import android.app.Activity;
import android.app.AlarmManager;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;

public class MainActivity extends Activity {
    private AlarmManager alarms;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        alarms = (AlarmManager) getSystemService(Context.ALARM_SERVICE);
        createChannel();

        LinearLayout root = new LinearLayout(this);
        root.setPadding(24, 24, 24, 24);

        Button notify = new Button(this);
        notify.setText("Notify me in 3 seconds");
        notify.setOnClickListener(v -> schedule(3000L));
        root.addView(notify);

        setContentView(root);
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationManager nm = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
            NotificationChannel ch = new NotificationChannel(
                    "forge", "Forge Channel", NotificationManager.IMPORTANCE_DEFAULT);
            ch.setDescription("APK Forge demo notifications");
            nm.createNotificationChannel(ch);
        }
    }

    private void schedule(long delayMs) {
        Intent intent = new Intent(this, AlarmReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(this, 42, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        alarms.set(AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + delayMs, pi);
    }
}

// BroadcastReceiver in the same file — auto-registered in the manifest.
class AlarmReceiver extends android.content.BroadcastReceiver {
    @Override
    public void onReceive(android.content.Context context, android.content.Intent intent) {
        android.app.NotificationManager nm = (android.app.NotificationManager)
                context.getSystemService(android.content.Context.NOTIFICATION_SERVICE);
        android.app.Notification.Builder b;
        if (android.os.Build.VERSION.SDK_INT >= 26) {
            b = new android.app.Notification.Builder(context, "forge");
        } else {
            b = new android.app.Notification.Builder(context);
        }
        b.setSmallIcon(android.R.drawable.ic_dialog_info)
         .setContentTitle("APK Forge")
         .setContentText("Your alarm fired!")
         .setAutoCancel(true);
        nm.notify(1, b.build());
    }
}''',

    "Threaded Progress (full class)": '''package com.example.progress;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

public class MainActivity extends Activity {
    private final Handler main = new Handler(Looper.getMainLooper());
    private ProgressBar bar;
    private TextView label;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(24, 24, 24, 24);

        label = new TextView(this);
        label.setText("Press start");
        label.setTextSize(18);
        root.addView(label);

        bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(100);
        root.addView(bar, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT));

        Button start = new Button(this);
        start.setText("Start work");
        start.setOnClickListener(v -> runWork());
        root.addView(start);

        setContentView(root);
    }

    private void runWork() {
        label.setText("Working…");
        new Thread(() -> {
            for (int p = 0; p <= 100; p += 5) {
                final int pct = p;
                main.post(() -> {
                    bar.setProgress(pct);
                    label.setText(pct + "%");
                });
                try { Thread.sleep(80); } catch (InterruptedException ignored) { }
            }
            main.post(() -> label.setText("Done"));
        }).start();
    }
}''',
}


# ---------------------------------------------------------------------------
# AI coding guide — clipboard text for the AI Guide page
# ---------------------------------------------------------------------------
# Copied to the clipboard from the AI Guide page so users can prime any AI
# model to emit APK-Forge-perfect Java on the very first try.
#
# v3.4 "AI GUIDE v2": rewritten as a PRECISION prompt — output contract,
# hard build-breaker list, required skeleton, px→dp helper, exact asset
# access patterns, threading rules, lifecycle rules, min-SDK table and a
# self-check list the model ticks before answering. Every rule maps to a
# real failure the forge has seen in AI-generated code.
AI_CODING_GUIDE = """\
APK FORGE — JAVA CODING GUIDE (v3.4) — for AI code generators
==============================================================
You are writing ONE self-contained Java file that the desktop tool "APK Forge"
compiles directly into a signed, installable Android APK — no Gradle, no
project folder, no XML files, no dependencies. Follow every rule below and
the code will build and run on the FIRST try.

------------------------------------------------------------------------------
0. OUTPUT CONTRACT
------------------------------------------------------------------------------
* Reply with EXACTLY ONE ```java code block containing the COMPLETE file.
  Nothing outside the block is needed — no project structure, no explanations
  after the code.
* ONE file, ONE paste. Multiple top-level classes/interfaces/enums ARE allowed
  and EXPECTED — they are auto-split into .java files at build time.
* No markdown inside the code, no TODOs, no pseudo-code, no "..." placeholders,
  no truncated methods — every line must compile.
* NEVER emit: XML, Gradle/build files, an AndroidManifest, proguard rules,
  Kotlin, .properties files, or more than one code block.

------------------------------------------------------------------------------
1. THE TWO ACCEPTED SHAPES
------------------------------------------------------------------------------
A) FULL CLASS (preferred for real apps):

    package com.example.appname;          // <- ALWAYS start with this
    import android.app.Activity;           // imports optional (~780 common
    import android.os.Bundle;              //    classes are auto-imported)

    public class MainActivity extends Activity {
        @Override
        protected void onCreate(Bundle savedInstanceState) {
            super.onCreate(savedInstanceState);
            setContentView(root);          // <- a View YOU built in code
        }
    }
    // extra top-level classes follow in the SAME file: helpers, adapters,
    // custom views, more activities, services, receivers, providers.

B) BARE SNIPPET (quick experiments only): statements without a class — they
   run inside an auto-generated Activity's onCreate(). Snippets MAY include
   their own import lines, helper methods and modifier-bearing fields (they
   are lifted into proper class members automatically).

------------------------------------------------------------------------------
2. HARD RULES — THESE BREAK THE BUILD (never do them)
------------------------------------------------------------------------------
[ ] NO androidx / android.support / appcompat / com.google.android.* — the
    plain framework ONLY. Use: AppCompatActivity -> Activity,
    NotificationCompat -> Notification, FragmentActivity -> Activity.
[ ] NO Kotlin. NO var, records, switch-expressions, sealed types, pattern
    matching for instanceof, text blocks. Java 8 syntax ONLY: lambdas,
    method references, anonymous classes, generics, enums, default methods,
    try-with-resources — all supported.
[ ] NO R.layout.*, setContentView(R.layout...), menu XML, DataBinding — there
    are NO xml layouts. Build every View programmatically and keep references
    in fields instead of findViewById.
[ ] NO third-party libraries of ANY kind (no Gson, Retrofit, Picasso, OkHttp,
    Firebase, Lombok). Use the framework: org.json, HttpURLConnection,
    BitmapFactory, SQLiteDatabase.
[ ] Do NOT emit an AndroidManifest or declare components in XML — activities,
    services, receivers and permissions are auto-registered by the tool.
[ ] NO java.util.stream or java.util.Optional when minSdk might be < 24;
    NO java.time when it might be < 26. (Default minSdk is 21. If your code
    needs 24/26+, say so in a comment — the tool auto-raises it.)

------------------------------------------------------------------------------
3. THE REQUIRED SKELETON (copy this shape exactly)
------------------------------------------------------------------------------
package com.example.myapp;

import android.app.Activity;
import android.os.Bundle;
import android.widget.*;

public class MainActivity extends Activity {
    private LinearLayout root;
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        status = new TextView(this);
        status.setText("Hello");
        root.addView(status);
        setContentView(root);
    }

    // helpers are normal private methods / inner classes
    private int dip(int px) { /* see section 4 */ return 0; }
}

// ---- optional extra top-level classes, SAME file ---------------------------
// class ItemAdapter extends BaseAdapter { ... }
// class DrawView extends View { @Override onDraw(Canvas c) { ... } }
// class DetailActivity extends Activity { ... }

------------------------------------------------------------------------------
4. PIXEL CORRECTNESS — AI models get this wrong constantly
------------------------------------------------------------------------------
NEVER pass raw px to layout params or margins. Include this helper and use it:

    private int dip(int px) {
        float d = getResources().getDisplayMetrics().density;
        return (int) (px * d + 0.5f);
    }

    LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, dip(48));
    lp.setMargins(dip(16), dip(8), dip(16), dip(8));
    button.setLayoutParams(lp);

Text sizes use sp automatically: status.setTextSize(18);  // correct as-is.

------------------------------------------------------------------------------
5. ASSETS & RESOURCES (v3.4 — read carefully, then copy the exact patterns)
------------------------------------------------------------------------------
Files the user bundles on the tool's Design page ship INSIDE the APK:

* ASSETS (default for any file): open EXACTLY by the name shown in the tool:

      // read a text/JSON asset
      InputStream in = getAssets().open("data.json");

      // load an image asset into an ImageView
      Bitmap bmp = BitmapFactory.decodeStream(getAssets().open("logo.png"));
      ImageView iv = new ImageView(this);
      iv.setImageBitmap(bmp);

      // list a bundled folder
      String[] names = getAssets().list("sounds");

      // local web page
      webView.loadUrl("file:///android_asset/page.html");

* Images the user tagged 'drawable' get a REAL id:  R.drawable.name
* Sounds the user tagged 'raw' get a REAL id:        R.raw.name

      MediaPlayer mp = MediaPlayer.create(this, R.raw.beep);
      mp.start();

  R.drawable./R.raw. names are ALWAYS lower_snake_case ("Holiday Photo.PNG"
  becomes R.drawable.holiday_photo). If unsure whether the user tagged a
  file, use getAssets() — it works for EVERY bundled file regardless of type.

* Generated ids that always exist: R.string.app_name, R.anim.* (user-
  configured entrance animations), R.drawable.* and R.raw.* (tagged assets).
* NEVER read /sdcard or getExternalStorageDirectory() for bundled files.
* When your app needs a file the user has NOT bundled yet, end your answer
  with: // ASSETS NEEDED: data.json, logo.png

------------------------------------------------------------------------------
6. THREADING — the #1 runtime crash source
------------------------------------------------------------------------------
* Network, file and database work NEVER on the UI thread.
* Touch views ONLY from the UI thread:

      new Thread(() -> {
          final String result = doNetworkCall();          // background
          runOnUiThread(() -> status.setText(result));    // UI thread
      }).start();

* Periodic UI updates: CountDownTimer, or a Handler created with
  Looper.getMainLooper(). Blocking onCreate for ~5 seconds = ANR crash.

------------------------------------------------------------------------------
7. PERMISSIONS & RUNTIME REQUESTS
------------------------------------------------------------------------------
* The tool AUTO-DETECTS common permissions from your code (INTERNET, CAMERA,
  RECORD_AUDIO, ACCESS_FINE_LOCATION, ...) and offers one-click enabling.
  Still, end your answer with a one-line reminder when you use them:

      // PERMISSIONS NEEDED: INTERNET, RECORD_AUDIO

* Dangerous permissions need a runtime grant on API 23+ — include the
  ActivityCompat.requestPermissions(...) pattern when using camera, mic,
  location, contacts or storage.

------------------------------------------------------------------------------
8. LIFECYCLE & MEMORY — avoid the classic leaks
------------------------------------------------------------------------------
* Release MediaPlayer, Camera, Cursor and Sensor listeners in onDestroy()/
  onPause(). Cancel Timer/Handler/CountDownTimer in onDestroy().
* In async callbacks guard with:  if (isFinishing()) return;  before touching
  views.
* Register receivers in onResume() -> unregister in onPause().
* Small persistent state -> SharedPreferences.

------------------------------------------------------------------------------
9. MULTI-COMPONENT APPS — zero configuration
------------------------------------------------------------------------------
* EVERY top-level class extending Activity / Service / BroadcastReceiver /
  ContentProvider is auto-registered in the generated manifest. MainActivity
  (or the first Activity) becomes the launcher:

      startActivity(new Intent(this, DetailActivity.class));

* A service is just another class in the same file:
      class SyncService extends Service { ... }

------------------------------------------------------------------------------
10. MIN-SDK QUICK TABLE
------------------------------------------------------------------------------
21 default | 23 runtime permissions | 24 streams/Optional
26 java.time & NotificationChannel | 29 scoped storage

------------------------------------------------------------------------------
11. SELF-CHECK BEFORE YOU ANSWER (tick every line silently)
------------------------------------------------------------------------------
[ ] exactly one ```java block, complete and final
[ ] package line present (full-class mode)
[ ] launcher class is: public class MainActivity extends Activity
[ ] UI built 100% programmatically; setContentView(myRoot) called
[ ] no androidx / Kotlin / var / records / XML / third-party libraries
[ ] no R.layout / findViewById(R.id.*) anywhere
[ ] assets read via getAssets().open("<exact name>") or R.drawable./R.raw.
[ ] background work off the UI thread; UI updates inside runOnUiThread
[ ] heavy objects released in onDestroy/onPause
[ ] "// PERMISSIONS NEEDED:" and "// ASSETS NEEDED:" comments at the end

Working mental model: "a plain framework Android app in ONE source file,
zero dependencies, Java 8, programmatic UI — compiled and signed automatically."
"""


# ---------------------------------------------------------------------------
# Asset snippets — Java patterns for Design-page bundled files
# ---------------------------------------------------------------------------
# Battle-tested Java patterns for the files bundled on the Design page.
# Shown on the AI Guide page with one-click copy buttons and referenced by
# the guide so AI-generated code uses the EXACT working shapes.
ASSET_SNIPPETS: List[Tuple[str, str]] = [
    ("Read a text asset (JSON/CSV/config)",
     'private String readAsset(String name) {\n'
     '    try (InputStream in = getAssets().open(name)) {\n'
     '        ByteArrayOutputStream bo = new ByteArrayOutputStream();\n'
     '        byte[] buf = new byte[8192];\n'
     '        int n;\n'
     '        while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);\n'
     '        return bo.toString("UTF-8");\n'
     '    } catch (IOException e) {\n'
     '        return "";\n'
     '    }\n'
     '}\n'
     '// usage: String json = readAsset("data.json");'),
    ("Load an image asset into an ImageView",
     'try {\n'
     '    Bitmap bmp = BitmapFactory.decodeStream(getAssets().open("logo.png"));\n'
     '    ImageView iv = new ImageView(this);\n'
     '    iv.setImageBitmap(bmp);\n'
     '    iv.setScaleType(ImageView.ScaleType.FIT_CENTER);\n'
     '    root.addView(iv);\n'
     '} catch (IOException e) {\n'
     '    Log.e("App", "asset missing", e);\n'
     '}'),
    ("Play a bundled sound (raw or asset)",
     '// sound tagged \'raw\' on the Design page:\n'
     'MediaPlayer mp = MediaPlayer.create(this, R.raw.beep);\n'
     'mp.setOnCompletionListener(MediaPlayer::release);\n'
     'mp.start();\n'
     '\n'
     '// sound living in assets/:\n'
     'try {\n'
     '    AssetFileDescriptor afd = getAssets().openFd("beep.mp3");\n'
     '    MediaPlayer mp2 = new MediaPlayer();\n'
     '    mp2.setDataSource(afd.getFileDescriptor(),\n'
     '            afd.getStartOffset(), afd.getLength());\n'
     '    afd.close();\n'
     '    mp2.prepare();\n'
     '    mp2.start();\n'
     '    mp2.setOnCompletionListener(MediaPlayer::release);\n'
     '} catch (IOException e) {\n'
     '    Log.e("App", "sound missing", e);\n'
     '}'),
    ("List a folder of assets",
     'try {\n'
     '    String[] names = getAssets().list("sounds");\n'
     '    if (names != null) {\n'
     '        for (String n : names) Log.i("App", "asset: " + n);\n'
     '    }\n'
     '} catch (IOException e) {\n'
     '    Log.e("App", "folder missing", e);\n'
     '}'),
    ("WebView showing a bundled page",
     'WebView webView = new WebView(this);\n'
     'webView.getSettings().setJavaScriptEnabled(true);\n'
     'webView.loadUrl("file:///android_asset/page.html");\n'
     'setContentView(webView);\n'
     '// needs INTERNET permission only for remote pages'),
    ("Use a tagged drawable / raw resource",
     '// image tagged \'drawable\' in the Design page -> real resource id:\n'
     'ImageView iv = new ImageView(this);\n'
     'iv.setImageResource(R.drawable.holiday_photo);\n'
     '\n'
     '// sound tagged \'raw\':\n'
     'MediaPlayer mp = MediaPlayer.create(this, R.raw.beep);\n'
     'mp.start();'),
]


# ---------------------------------------------------------------------------
# THE JAVA COMPATIBILITY ENGINE
# ---------------------------------------------------------------------------
# A comment/string-aware structural scanner + a set of transformers that make
# "one all-in-one Java file" written by a human OR an AI model compile:
#   • scan_java_structure  — braces, strings, comments, top-level types
#   • analyze_java         — package/imports/types/components/diagnostics
#   • auto_fix_imports     — adds missing imports for ~780 common classes
#   • migrate_androidx     — conservative androidx → framework rewrite
#   • split_java_units     — multi-class single file → multiple .java files
#   • wrap_snippet         — bare snippet → full Activity
#   • friendly_javac_errors — compiler output → plain-English hints


def log_time():
    """Current wall-clock time formatted as HH:MM:SS for log lines."""
    return datetime.now().strftime("%H:%M:%S")


_TYPE_KEYWORDS = ("class", "interface", "enum")
_STMT_KEYWORDS = ("if", "for", "while", "switch", "catch", "do", "else",
                  "try", "synchronized", "default", "finally")


def _blank(seg: str) -> str:
    """Blank out a text segment (for masking) while preserving newlines."""
    return "".join(c if c == "\n" else " " for c in seg)


# --- v3.5 FAST structure scanner ---
# One compiled regex blanks every comment / string / char literal at C speed;
# a token-stream walk (identifier | whitespace-run | single char) then drives
# the SAME state machine the reference character loop used. Output is
# verified identical (see _scan_reference) and the reference engine remains
# wired in as an automatic fallback safety net.
_LITERAL_RE = re.compile(
    r'//[^\n]*'                                   # line comment (excl. \n)
    r'|/\*(?:[\s\S]*?\*/|[\s\S]*\Z)'              # block comment (unterminated → EOF)
    r'|"(?:\\[\s\S]?|[^"\\\n])*(?:"|\n|\Z)'       # string literal
    r"|'(?:\\[\s\S]?|[^'\\\n])*(?:'|\n|\Z)"       # char literal
)
_TOKEN_SCAN_RE = re.compile(
    r'(?:[^\W\d_]|[_$])[\w$]*'                  # identifier run (unicode letters, 1 token)
    r'|\s+'                                       # whitespace run (1 token)
    r'|.'                                          # any other single char
)
_TYPE_NAME_AT_RE = re.compile(r'[ \t\r\n]*((?:[^\W\d_]|[_$])[\w$]*)')
# v3.5: brace-classification patterns precompiled once (they ran through the
# re-module cache with a rebuilt pattern string on every single brace).
_ANON_TAIL_C_RE = re.compile(r"new\s+[\w.$]+\s*\([^()]*\)\s*$")
_STMTKW_GROUP = "|".join(_STMT_KEYWORDS)
_STMTKW_PAREN_C_RE = re.compile(rf"\b(?:{_STMTKW_GROUP})\s*\([^()]*\)\s*$")
_STMTKW_END_C_RE = re.compile(rf"\b(?:{_STMTKW_GROUP})\s*$")
_STATIC_END_C_RE = re.compile(r"\bstatic\s*$")

# v3.5: memoise scan results per (light, text) — analysis, element parsing,
# motion safety checks and the build pipeline share ONE scan of the source.
_SCAN_CACHE: Dict[Tuple[bool, str], dict] = {}


def _scan_snapshot(struct: dict) -> dict:
    """Private-ish copy of a scan result (callers own their copy; the cached
    master stays pristine even if a caller ever mutates its result)."""
    return {"types": [dict(t) for t in struct["types"]],
            "stmt_spans": list(struct["stmt_spans"]),
            "masked": struct["masked"]}


def scan_java_structure(text: str, light: bool = False) -> dict:
    """
    Single-pass structural scan of Java source.

    Tracks string/char literals and comments, counts braces, and records:
      • types        — top-level class/interface/enum declarations
                      (name, kind, spans, is_public, extends, implements)
      • stmt_spans   — (open, close) ranges of brace bodies where plain Java
                      STATEMENTS are legal (method/constructor bodies, control
                      blocks, lambda bodies, static initializers). Used by the
                      safe code-injector. Class bodies / array initializers are
                      deliberately excluded.
      • masked       — text of identical length with comments and string/char
                      contents blanked (regex-safe: line numbers preserved).

    ``light=True`` skips type detection / statement spans (fast masking only).

    v3.5: literal masking is one compiled regex (C speed) and the state
    machine walks a token stream instead of single characters — with the
    reference engine kept as a fallback and results memoised per text.
    """
    key = (light, text)
    cached = _SCAN_CACHE.get(key)
    if cached is not None:
        return _scan_snapshot(cached)
    try:
        result = _scan_fast(text, light)
    except Exception:
        result = _scan_reference(text, light)
    if len(_SCAN_CACHE) >= 4:
        _SCAN_CACHE.clear()
    try:
        _SCAN_CACHE[key] = _scan_snapshot(result)
    except Exception:
        pass
    return result


_RE_PUBLIC_WORD = re.compile(r"\bpublic\b")


def _scan_fast(text: str, light: bool) -> dict:
    """Regex-mask + token-stream state machine (see scan_java_structure)."""
    masked = _LITERAL_RE.sub(lambda m: _blank(m.group(0)), text)
    if len(masked) != len(text):        # impossible in theory — fall back
        raise ValueError("mask length mismatch")

    if light:
        return {"types": [], "stmt_spans": [], "masked": masked}

    n = len(text)
    depth = 0
    types: List[dict] = []
    stmt_spans: List[Tuple[int, int]] = []
    ctx_stack: List[Tuple[int, str]] = []
    code_tail = ""
    last_top_boundary = 0
    pending_type: Optional[dict] = None

    for m in _TOKEN_SCAN_RE.finditer(masked):
        tok = m.group(0)

        # --- whitespace runs (blanked literals collapse to a single space) ---
        if tok[0].isspace():
            code_tail += " "
            if len(code_tail) > 400:
                code_tail = code_tail[-200:]
            continue

        # --- identifier runs & single code chars ---
        # (both simply append to code_tail — only exact type KEYWORDS can be
        # multi-char, and only braces/semicolons drive the state machine)
        code_tail += tok
        if len(code_tail) > 400:
            code_tail = code_tail[-200:]

        if tok in _TYPE_KEYWORDS:
            if depth == 0 and not code_tail[:-len(tok)].rstrip().endswith("."):
                kw_start = m.start()
                kind = tok
                if code_tail[:-len(tok)].rstrip().endswith("@"):
                    kw_start -= 1
                    kind = "@interface"
                m2 = _TYPE_NAME_AT_RE.match(masked, m.end())
                type_name = m2.group(1) if m2 else None
                if type_name:
                    pending_type = {
                        "name": type_name,
                        "kind": kind,
                        "region_start": last_top_boundary,
                        "decl_start": kw_start,
                        "body_open": -1,
                        "end": -1,
                    }

        elif tok == "{":
            if depth == 0 and pending_type is not None:
                pending_type["body_open"] = m.start()
                header = text[pending_type["decl_start"]:m.start()]
                is_public = bool(_RE_PUBLIC_WORD.search(header))
                extends, implements = _parse_extends_implements(header)
                pending_type.update({"is_public": is_public,
                                     "extends": extends, "implements": implements})
                types.append(pending_type)
                ctx_stack.append((m.start(), "type"))
                pending_type = None
                depth += 1
                continue
            # nested brace → classify by the code BEFORE this '{'
            tail = code_tail[:-1].rstrip()
            kind = "type"
            if tail.endswith("->"):
                kind = "stmt"
            elif _ANON_TAIL_C_RE.search(tail):
                kind = "anon"          # anonymous class body
            elif _STMTKW_PAREN_C_RE.search(tail) or _STMTKW_END_C_RE.search(tail):
                kind = "stmt"
            elif tail.endswith(")"):
                kind = "stmt"           # method / constructor body
            elif tail.endswith("=") or tail.endswith(",") or tail.endswith("{"):
                kind = "init"           # array initializer etc.
            elif _STATIC_END_C_RE.search(tail):
                kind = "stmt"           # static initializer block
            ctx_stack.append((m.start(), kind))
            depth += 1

        elif tok == "}":
            if ctx_stack:
                open_pos, kind = ctx_stack.pop()
                if kind == "stmt":
                    stmt_spans.append((open_pos, m.start() + 1))
                if kind == "type" and depth == 1 and types and types[-1]["end"] == -1 \
                        and types[-1]["body_open"] == open_pos:
                    types[-1]["end"] = m.start() + 1
            depth = max(0, depth - 1)
            if depth == 0:
                last_top_boundary = m.start() + 1

        elif tok == ";" and depth == 0:
            last_top_boundary = m.start() + 1

    # close any unterminated type (malformed input tolerance)
    for t in types:
        if t["end"] == -1:
            t["end"] = n
    return {"types": types, "stmt_spans": stmt_spans, "masked": masked}


def _scan_reference(text: str, light: bool) -> dict:
    """
    v3.1–v3.4 character-by-character scanner — kept verbatim as the fallback
    engine (and cross-check oracle) for _scan_fast.
    """
    n = len(text)
    i = 0
    depth = 0
    masked_parts: List[str] = []
    types: List[dict] = []
    stmt_spans: List[Tuple[int, int]] = []
    ctx_stack: List[Tuple[int, str]] = []
    code_tail = ""
    last_top_boundary = 0
    pending_type: Optional[dict] = None

    while i < n:
        c = text[i]

        # --- comments ---
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i)
            j = n if j == -1 else j
            masked_parts.append(_blank(text[i:j]))
            i = j
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            end = n if j == -1 else j + 2
            masked_parts.append(_blank(text[i:end]))
            i = end
            continue

        # --- string / char literals ---
        if c == '"' or c == "'":
            quote = c
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == quote or text[j] == "\n":
                    break
                j += 1
            end = min(n, j + 1)
            masked_parts.append(_blank(text[i:end]))
            code_tail += " "
            i = end
            continue

        # --- identifier runs ---
        if c.isalpha() or c == "_" or c == "$":
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] in "_$"):
                j += 1
            word = text[i:j]
            masked_parts.append(word)
            code_tail += word
            if len(code_tail) > 400:
                code_tail = code_tail[-200:]
            if (not light and depth == 0 and word in _TYPE_KEYWORDS
                    and (not code_tail[:-len(word)].rstrip().endswith("."))):
                kw_start = i
                kind = word
                if code_tail[: -len(word)].rstrip().endswith("@"):
                    kw_start -= 1
                    kind = "@interface"
                # parse the type name
                k = j
                while k < n and text[k] in " \t\r\n":
                    k += 1
                m = k
                while m < n and (text[m].isalnum() or text[m] in "_$"):
                    m += 1
                type_name = text[k:m] if m > k else None
                if type_name:
                    pending_type = {
                        "name": type_name,
                        "kind": kind,
                        "region_start": last_top_boundary,
                        "decl_start": kw_start,
                        "body_open": -1,
                        "end": -1,
                    }
            i = j
            continue

        # --- non-identifier code chars (braces, punctuation, …) ---
        masked_parts.append(c)
        code_tail += c
        if len(code_tail) > 400:
            code_tail = code_tail[-200:]

        if c == "{":
            if depth == 0 and pending_type is not None:
                pending_type["body_open"] = i
                header = text[pending_type["decl_start"]:i]
                is_public = bool(re.search(r"\bpublic\b", header))
                extends, implements = _parse_extends_implements(header)
                pending_type.update({"is_public": is_public,
                                     "extends": extends, "implements": implements})
                types.append(pending_type)
                ctx_stack.append((i, "type"))
                pending_type = None
                depth += 1
                i += 1
                continue
            # nested brace → classify by the code BEFORE this '{'
            tail = code_tail[:-1].rstrip()
            kind = "type"
            if tail.endswith("->"):
                kind = "stmt"
            elif re.search(r"new\s+[\w.$]+\s*\([^()]*\)\s*$", tail):
                kind = "anon"          # anonymous class body
            elif re.search(r"\b(?:%s)\s*\([^()]*\)\s*$" % "|".join(_STMT_KEYWORDS), tail) \
                    or re.search(r"\b(?:%s)\s*$" % "|".join(_STMT_KEYWORDS), tail):
                kind = "stmt"
            elif tail.endswith(")"):
                kind = "stmt"           # method / constructor body
            elif tail.endswith("=") or tail.endswith(",") or tail.endswith("{"):
                kind = "init"           # array initializer etc.
            elif re.search(r"\bstatic\s*$", tail):
                kind = "stmt"           # static initializer block
            ctx_stack.append((i, kind))
            depth += 1
            i += 1
            continue

        if c == "}":
            if ctx_stack:
                open_pos, kind = ctx_stack.pop()
                if kind == "stmt":
                    stmt_spans.append((open_pos, i + 1))
                if kind == "type" and depth == 1 and types and types[-1]["end"] == -1 \
                        and types[-1]["body_open"] == open_pos:
                    types[-1]["end"] = i + 1
            depth = max(0, depth - 1)
            if depth == 0:
                last_top_boundary = i + 1
            i += 1
            continue

        if c == ";" and depth == 0:
            last_top_boundary = i + 1
        i += 1

    # close any unterminated type (malformed input tolerance)
    for t in types:
        if t["end"] == -1:
            t["end"] = n
    masked = "".join(masked_parts)
    if len(masked) != n:  # safety: never happen, but keep positions aligned
        masked = text

    return {
        "types": types,
        "stmt_spans": stmt_spans,
        "masked": masked,
    }


def _parse_extends_implements(header: str) -> Tuple[List[str], List[str]]:
    """Extract simple extends/implements names from a type declaration header."""

    def simple_names(chunk: str) -> List[str]:
        """Split one comma-separated name chunk into simple names."""
        names = []
        for raw in chunk.split(","):
            raw = raw.strip()
            raw = re.sub(r"<.*>", "", raw, flags=re.DOTALL).strip()
            raw = re.sub(r"\b(?:public|private|protected|static|final|abstract|"
                         r"strictfp|sealed|non[ -]sealed)\b", "", raw).strip()
            if not raw:
                continue
            names.append(raw.split(".")[-1])
        return names

    header = re.sub(r"<[^<>]*>", "", header)  # one level of generics is enough
    extends: List[str] = []
    implements: List[str] = []
    m = re.search(r"\bextends\b([^({]*)", header)
    if m:
        rest = m.group(1)
        if "implements" in rest:
            rest = rest.split("implements")[0]
        extends = simple_names(rest)
    m = re.search(r"\bimplements\b([^({]*)", header)
    if m:
        implements = simple_names(m.group(1))
    return extends, implements


def mask_java(text: str) -> str:
    """Comments/strings blanked, length preserved — for safe regex scans."""
    return scan_java_structure(text, light=True)["masked"]


# ---------------------------------------------------------------------------
# Analysis model
# ---------------------------------------------------------------------------
@dataclass
class JavaIssue:
    """One diagnostic row: level, title, detail plus an optional fix hook."""
    level: str            # 'error' | 'warn' | 'info'
    title: str
    detail: str = ""
    fix_id: str = ""      # '', 'add_imports', 'enable_perms', 'raise_min_sdk',
                          # 'migrate_androidx', 'goto_settings', 'goto_source'
    fix_arg: str = ""


@dataclass
class JavaAnalysis:
    """Complete static-analysis result for one Java source text."""

    package: str = ""
    imports: List[str] = field(default_factory=list)
    import_simple: Set[str] = field(default_factory=set)
    type_names: List[str] = field(default_factory=list)
    activities: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    receivers: List[str] = field(default_factory=list)
    providers: List[str] = field(default_factory=list)
    fragments: List[str] = field(default_factory=list)
    launcher: str = ""
    is_full: bool = False
    has_setcontentview: bool = False
    uses_androidx: bool = False
    androidx_imports: List[str] = field(default_factory=list)
    uses_records: bool = False
    uses_var: bool = False
    missing_imports: List[Tuple[str, str]] = field(default_factory=list)
    suggested_permissions: List[str] = field(default_factory=list)
    required_min_sdk: int = 0
    issues: List[JavaIssue] = field(default_factory=list)
    loc: int = 0
    chars: int = 0

    def summary(self) -> str:
        """Short human-readable summary line for the diagnostics header."""
        bits = []
        if self.is_full:
            bits.append(f"{len(self.type_names)} class(es)")
            if self.activities:
                bits.append(f"launcher .{self.launcher}")
            if self.services:
                bits.append(f"{len(self.services)} service(s)")
            if self.receivers:
                bits.append(f"{len(self.receivers)} receiver(s)")
        else:
            bits.append("snippet")
        if self.missing_imports:
            bits.append(f"{len(self.missing_imports)} import(s) to add")
        if self.suggested_permissions:
            bits.append(f"{len(self.suggested_permissions)} permission(s) suggested")
        return " · ".join(bits) or "—"


_USAGE_RE_CACHE: Dict[str, re.Pattern] = {}


def _word_used(masked: str, token: str) -> bool:
    """Word-boundary usage test on masked code (handles dotted tokens too)."""
    if "." in token:
        return token in masked
    pat = _USAGE_RE_CACHE.get(token)
    if pat is None:
        pat = re.compile(r"(?<![\w.$])" + re.escape(token) + r"\b")
        _USAGE_RE_CACHE[token] = pat
    return bool(pat.search(masked))


# --- v3.1 fast path: ONE identifier set replaces hundreds of regex scans ---
_SIMPLE_IDENT_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_IDENT_FIND_RE = re.compile(r"(?<![\w.$])[A-Za-z_$][A-Za-z0-9_$]*")


def _identifier_set(masked: str) -> FrozenSet[str]:
    """All identifiers in the masked code that are NOT qualified suffixes
    (``foo.Bar`` contributes ``foo`` only). One pass, O(n) — membership tests
    against this set exactly reproduce the old per-token regex semantics
    while being ~6× faster on large files."""
    return frozenset(_IDENT_FIND_RE.findall(masked))


def _token_used(token: str, masked: str, idents: FrozenSet[str]) -> bool:
    """Fast usage test: set membership for plain identifiers, regex fallback
    for dotted / decorated tokens (``GridLayout.Spec``, ``parallelStream()``)."""
    if _SIMPLE_IDENT_RE.fullmatch(token):
        return token in idents
    return _word_used(masked, token)


_PY_DEF_RE = re.compile(r"^\s*def\s+\w+\s*\([^)]*\)\s*:\s*$", re.MULTILINE)
_PY_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+[\w.]+\s+import\s+[\w.,\s*]+|import\s+[\w.]+(?:\s+as\s+\w+)?)\s*$",
    re.MULTILINE)
_PY_SELF_RE = re.compile(r"\bself\.")
_PY_ELIF_RE = re.compile(r"^\s*elif\b|^\s*if\s+.*:\s*$", re.MULTILINE)


def looks_like_python(text: str) -> bool:
    """v3.2: heuristic detection of Python pasted into the Java editor (a
    surprisingly common AI/user mistake). Returns True when the code shows
    multiple unmistakable Python-only constructs."""
    if not text.strip():
        return False
    score = (len(_PY_DEF_RE.findall(text))
             + len(_PY_SELF_RE.findall(text)) // 3
             + len(_PY_ELIF_RE.findall(text)) // 2)
    imports = _PY_IMPORT_RE.findall(text)
    semicolon_imports = sum(1 for m in imports if m.strip().endswith(";"))
    score += len(imports) - semicolon_imports
    # Java never has 'def name(...):' at all — one is conclusive
    return score >= 3 or len(_PY_DEF_RE.findall(text)) >= 1


def analyze_java(java_text: str, current_min_sdk: int = 21,
                 enabled_permissions: Optional[List[str]] = None) -> JavaAnalysis:
    """Full static analysis of the pasted Java. Pure & fast — runs in workers."""
    a = JavaAnalysis()
    a.chars = len(java_text)
    a.loc = java_text.count("\n") + 1 if java_text.strip() else 0

    struct = scan_java_structure(java_text)
    masked = struct["masked"]
    types = struct["types"]
    idents = _identifier_set(masked)          # v3.1: one pass, cached set

    a.is_full = bool(types)
    a.type_names = [t["name"] for t in types]

    m = re.search(r"\bpackage\s+([\w.]+)\s*;", masked)
    if m:
        a.package = m.group(1)

    a.imports = re.findall(r"\bimport\s+(?:static\s+)?([\w.*]+)\s*;", masked)
    a.import_simple = {fq.split(".")[-1] for fq in a.imports if not fq.endswith(".*")}
    a.has_setcontentview = bool(re.search(r"\bsetContentView\s*\(", masked))

    # --- component classification (with in-file transitive supers) ---
    supers: Dict[str, List[str]] = {
        t["name"]: list(t["extends"]) + list(t["implements"]) for t in types}

    def resolves_component(name: str, targets: Set[str], seen: Optional[set] = None) -> bool:
        """True when any transitive super of name resolves into targets."""
        seen = seen or set()
        if name in seen:
            return False
        seen.add(name)
        for sup in supers.get(name, []):
            if sup in targets:
                return True
            if sup in supers and resolves_component(sup, targets, seen):
                return True
        return False

    activity_targets = {"Activity", "ListActivity", "ActivityGroup", "ExpandableListActivity"}
    service_targets = {"Service", "IntentService", "JobService", "LauncherActivity"}
    for t in types:
        name = t["name"]
        if resolves_component(name, activity_targets):
            a.activities.append(name)
        elif resolves_component(name, service_targets):
            a.services.append(name)
        elif resolves_component(name, {"BroadcastReceiver"}):
            a.receivers.append(name)
        elif resolves_component(name, {"ContentProvider"}):
            a.providers.append(name)
        elif resolves_component(name, {"Fragment", "DialogFragment", "ListFragment",
                                       "PreferenceFragment"}):
            a.fragments.append(name)

    if "MainActivity" in a.activities:
        a.launcher = "MainActivity"
    elif a.activities:
        a.launcher = a.activities[0]

    # --- library / syntax compatibility ---
    a.androidx_imports = [imp for imp in a.imports
                          if imp.startswith("androidx.") or imp.startswith("android.support.")]
    a.uses_androidx = bool(a.androidx_imports) or "androidx." in masked
    a.uses_records = bool(re.search(r"(?<![\w.$])record\s+\w+\s*\(", masked))
    a.uses_var = bool(re.search(r"(?<![\w.$])var\s+\w+\s*[=:;]", masked))

    # --- missing imports (auto-import fixer preview) ---
    local_names = set(a.type_names)
    for m2 in re.finditer(r"\b(?:class|interface|enum)\s+(\w+)", masked):
        local_names.add(m2.group(1))
    for key, fqcn in IMPORT_CATALOG.items():
        if key in local_names or key in a.import_simple:
            continue
        if _token_used(key, masked, idents):
            a.missing_imports.append((key, fqcn))

    # --- auto permissions ---
    enabled = set(enabled_permissions or [])
    suggested: List[str] = []
    for perm, tokens in PERMISSION_SIGNATURES:
        if perm in enabled:
            continue
        if any(_token_used(tok, masked, idents) for tok in tokens):
            if perm not in suggested:
                suggested.append(perm)
    a.suggested_permissions = suggested

    # --- min SDK advisor ---
    req = 0
    for api, tokens in MIN_SDK_TOKENS:
        if any(tok in masked or _token_used(tok, masked, idents) for tok in tokens):
            req = max(req, api)
    a.required_min_sdk = req

    # --- issues ---
    issues: List[JavaIssue] = []
    if not java_text.strip():
        issues.append(JavaIssue("info", "No Java code yet",
                                "Paste code on this page or insert a template.",
                                "goto_source"))
    elif not types and looks_like_python(java_text):
        # v3.5: files that already declare real Java classes can skip the
        # Python-paste heuristic — it only ever applied to bare snippets,
        # and raw-text regexes occasionally misfired on commented examples.
        issues.append(JavaIssue(
            "error", "This looks like PYTHON code, not Java",
            "APK Forge compiles Android JAVA. Python snippets (def/self/"
            "elif, colon-indentation) cannot be compiled into an APK — "
            "paste the Java equivalent instead.", ""))
        a.issues = issues
        return a
    if types:
        if len(types) > 1:
            issues.append(JavaIssue(
                "info", f"{len(types)} top-level types detected",
                "They will be automatically split into separate .java files "
                "at build time — write all your classes in ONE file.",
                ""))
        if not a.package:
            issues.append(JavaIssue(
                "info", "No package declaration",
                "One will be generated automatically from your Settings package "
                "name at build time."))
        if not a.activities:
            issues.append(JavaIssue(
                "error", "No Activity found",
                "Your main class must extend android.app.Activity "
                "(e.g. public class MainActivity extends Activity)."))
        else:
            issues.append(JavaIssue(
                "info", f"Launcher activity: {a.launcher}",
                f"{len(a.activities)} activit{'y' if len(a.activities) == 1 else 'ies'}, "
                f"{len(a.services)} service(s), {len(a.receivers)} receiver(s) will be "
                f"registered in the manifest.", ""))
    elif java_text.strip():
        issues.append(JavaIssue(
            "info", "Snippet mode",
            "Your code runs inside onCreate() of an auto-generated Activity."))
        if not a.has_setcontentview:
            issues.append(JavaIssue(
                "warn", "Snippet never calls setContentView(...)",
                "Without setContentView (or root.addView(...)) the screen will "
                "be blank. Call setContentView(yourView) at the end.", ""))

    if a.uses_androidx:
        migratable = [imp for imp in a.androidx_imports if imp in ANDROIDX_MIGRATIONS]
        issues.append(JavaIssue(
            "error", "androidx / support libraries are not available",
            "This forge builds against the plain Android framework. "
            + ("Click the fix to try an automatic migration of the common imports."
               if migratable else
               "Remove androidx imports and use framework classes "
               "(e.g. android.app.Activity instead of AppCompatActivity)."),
            "migrate_androidx" if migratable else ""))
    if a.uses_records:
        issues.append(JavaIssue(
            "error", "Records are not supported",
            "Java 'record' requires Java 14+; the build targets Java 8. "
            "Convert the record to a plain class."))
    if a.uses_var:
        issues.append(JavaIssue(
            "error", "'var' is not supported",
            "'var' requires Java 10+; the build targets Java 8. "
            "Use explicit types instead."))
    if a.missing_imports:
        names = ", ".join(k for k, _ in a.missing_imports[:6])
        more = "" if len(a.missing_imports) <= 6 else f" (+{len(a.missing_imports) - 6} more)"
        issues.append(JavaIssue(
            "warn", f"{len(a.missing_imports)} missing import(s)",
            f"Auto-detected: {names}{more}", "add_imports"))
    if suggested:
        pretty = ", ".join(p.split(".")[-1] for p in suggested[:5])
        issues.append(JavaIssue(
            "info", f"{len(suggested)} permission(s) suggested by your code",
            f"Your code appears to use: {pretty}", "enable_perms",
            ",".join(suggested)))
    if req and req > current_min_sdk:
        issues.append(JavaIssue(
            "warn", f"Code needs minSdk ≥ {req}",
            "Detected APIs (e.g. java.util.stream / NotificationChannel / java.time) "
            f"that only exist from API {req}. Current minimum is {current_min_sdk}.",
            "raise_min_sdk", str(req)))

    a.issues = issues
    return a


def auto_fix_imports(java_text: str) -> Tuple[str, List[str]]:
    """
    Add imports for every catalog class used but not imported.
    Returns (new_text, [added fully-qualified names]).
    """
    if not java_text.strip():
        return java_text, []
    masked = mask_java(java_text)
    idents = _identifier_set(masked)

    existing = re.findall(r"^\s*import\s+(?:static\s+)?([\w.*]+)\s*;", java_text, re.MULTILINE)
    existing_simple = {fq.split(".")[-1] for fq in existing if not fq.endswith(".*")}
    existing_fq = set(existing)

    local_names = set(m.group(1) for m in
                      re.finditer(r"\b(?:class|interface|enum)\s+(\w+)", masked))

    added: List[str] = []
    for key, fqcn in IMPORT_CATALOG.items():
        if key in existing_simple or fqcn in existing_fq or key in local_names:
            continue
        if _token_used(key, masked, idents):
            added.append(fqcn)

    if not added:
        return java_text, []

    # insert right after the last import, or after package, or at the very top
    insert_at = 0
    m_pkg = re.search(r"^\s*package\s+[\w.]+\s*;", java_text, re.MULTILINE)
    if m_pkg:
        insert_at = m_pkg.end()
    last_import = None
    for m in re.finditer(r"^\s*import\s+[\w.*\s]+;\s*$", java_text, re.MULTILINE):
        last_import = m
    if last_import:
        insert_at = max(insert_at, last_import.end())

    block = "".join(f"import {fq};\n" for fq in sorted(set(added)))
    sep = "\n" if insert_at > 0 else ""
    new_text = java_text[:insert_at] + sep + block + java_text[insert_at:]
    return new_text, sorted(set(added))


_RE_IMPORT_LINE = re.compile(r"^(\s*)import\s+([\w.]+)\s*;")


def migrate_androidx(java_text: str) -> Tuple[str, List[str], List[str]]:
    """
    Conservative androidx/support → framework rewrite for known-safe mappings.
    Returns (new_text, [migrated imports], [unmappable androidx imports]).
    """
    lines = java_text.splitlines(keepends=True)
    migrated: List[str] = []
    unmappable: List[str] = []
    out: List[str] = []
    strip_annotations = set()

    for line in lines:
        m = _RE_IMPORT_LINE.match(line)
        if m:
            fq = m.group(2)
            if fq in ANDROIDX_MIGRATIONS:
                target = ANDROIDX_MIGRATIONS[fq]
                migrated.append(fq)
                if target:
                    out.append(f"{m.group(1)}import {target};\n")
                else:
                    strip_annotations.add(fq.split(".")[-1])
                continue
            if fq.startswith("androidx.") or fq.startswith("android.support."):
                unmappable.append(fq)
                continue
        out.append(line)

    text = "".join(out)
    for ann in strip_annotations:
        text = re.sub(r"@\s*" + re.escape(ann) + r"\b\s*", "", text)
    # rewrite simple-name usages for mappings whose target has a DIFFERENT
    # simple name (e.g. AppCompatActivity → Activity)
    for fq in migrated:
        src_simple = fq.split(".")[-1]
        target = ANDROIDX_MIGRATIONS.get(fq, "")
        if target:
            tgt_simple = target.split(".")[-1]
            if tgt_simple != src_simple:
                text = re.sub(r"\b" + re.escape(src_simple) + r"\b", tgt_simple, text)
    return text, migrated, unmappable


# ---------------------------------------------------------------------------
# Splitter & snippet wrapper
# ---------------------------------------------------------------------------
def split_java_units(java_text: str, analysis: JavaAnalysis,
                     fallback_package: str,
                     activity_name: str = "MainActivity") -> List[Tuple[str, str]]:
    """
    Turn ONE all-in-one Java file into compilable (filename, content) units.

    • No types            → the snippet is wrapped into a full Activity.
    • Exactly one type    → written as-is (package line ensured).
    • Multiple types      → every top-level type becomes its own .java file
                            (public classes no longer collide with file names).
    """
    struct = scan_java_structure(java_text)
    types = struct["types"]

    import_block = "\n".join(
        m.group(0).strip() for m in
        re.finditer(r"^\s*import\s+[\w.*\s]+;\s*$", java_text, re.MULTILINE))

    if not types:
        wrapped = wrap_snippet(java_text, fallback_package, activity_name)
        return [(f"{activity_name}.java", wrapped)]

    pkg = analysis.package or fallback_package

    if len(types) == 1:
        content = java_text
        if not analysis.package:
            # prepend a package line so downstream parsing works
            content = f"package {pkg};\n\n" + content
        return [(f"{types[0]['name']}.java", content)]

    units: List[Tuple[str, str]] = []
    for t in types:
        unit_code = java_text[t["region_start"]:t["end"]].strip("\n")
        parts = [f"package {pkg};\n"]
        if import_block:
            parts.append("\n" + import_block + "\n")
        parts.append("\n" + unit_code + "\n")
        units.append((f"{t['name']}.java", "".join(parts)))
    return units


def wrap_snippet(snippet: str, package: str, activity: str) -> str:
    """
    v3.2 — MEMBER-AWARE snippet wrapper.

    Wrap a bare code snippet into a full Activity:

    • `package` / `import` lines the user pasted are LIFTED to the top of the
      generated file (v3.1 indented them INTO onCreate() — a guaranteed
      compile error whenever a snippet contained imports, which AI models
      paste all the time).
    • Top-level helper METHODS (e.g. `private void showToast(...) { … }`) are
      emitted as real class MEMBERS; the remaining statements still run
      inside onCreate().
    • Modifier-bearing single-line declarations (`private int counter = 0;`)
      become class FIELDS (usable from both onCreate and the members).
    • setContentView() detection keeps the wrapper from double-setting the
      content view; missing imports are auto-added from the catalog.
    """
    masked = mask_java(snippet)
    has_scv = bool(re.search(r"\bsetContentView\s*\(", masked))

    # --- 1) lift package / import lines out of the body ---
    import_lines: List[str] = []
    body_lines: List[str] = []
    directive_re = re.compile(
        r"^(?:import\s+(?:static\s+)?[\w.*]+\s*;|package\s+[\w.]+\s*;)\s*$")
    for line in snippet.splitlines():
        if directive_re.match(line.strip()):
            import_lines.append(line.strip())
        else:
            body_lines.append(line)
    body = "\n".join(body_lines).strip("\n")

    # --- 2) split top-level helper methods from statements ---
    members, stmt = split_snippet_members(body)

    # --- 3) modifier-bearing field lines → class fields ---
    field_lines: List[str] = []
    kept_lines: List[str] = []
    field_re = re.compile(
        r"^\s*(?:(?:public|private|protected|static|final|volatile|transient)\s+)+"
        r"[\w$][\w$.]*(?:\s*<[^<>]*>)?(?:\s*\[\s*\])*\s+[\w$]+\s*(?:=[^;]*)?;\s*$")
    annot_re = re.compile(r"^\s*@[\w$.]+(?:\([^;]*\))?\s*$")
    local_mod_re = re.compile(r"^(\s*)(?:(?:private|public|protected|static)\s+)+")

    for line in stmt.splitlines():
        s = line.strip()
        if s and "(" not in line and field_re.match(line):
            field_lines.append(line)
        elif s and annot_re.match(line):
            continue                      # dangling annotation — drop it
        else:
            # access/static modifiers are ILLEGAL on locals — strip them, but
            # ONLY on declaration-shaped lines: method headers inside
            # anonymous-class bodies legitimately start with "public void …("
            m = local_mod_re.match(line)
            if m:
                rest = line[m.end():]
                eq, sc, pa = rest.find("="), rest.find(";"), rest.find("(")
                limit = -1
                if eq >= 0 or sc >= 0:
                    limit = eq if sc < 0 else (sc if eq < 0 else min(eq, sc))
                if not (pa >= 0 and (limit < 0 or pa < limit)):
                    line = m.group(1) + rest
            kept_lines.append(line)
    stmt = "\n".join(kept_lines).strip("\n")

    # --- 3b) locals referenced by member methods → promoted to fields ---
    promoted, stmt = _promote_shared_locals("\n".join(members), stmt)
    field_lines = promoted + field_lines

    # --- 4) auto-imports over the whole program ---
    probe = "package p;\n" + "\n".join(import_lines) + "\n" + body
    fixed_probe, _added = auto_fix_imports(probe)
    for line in fixed_probe.splitlines():
        s = line.strip()
        if s.startswith("import ") and s not in import_lines:
            import_lines.append(s)

    base_imports = [
        "import android.app.Activity;",
        "import android.os.Bundle;",
        "import android.view.Gravity;",
        "import android.view.View;",
        "import android.view.ViewGroup;",
        "import android.widget.LinearLayout;",
    ]
    imports: List[str] = []
    for imp in base_imports + import_lines:
        if imp not in imports:
            imports.append(imp)

    # --- 5) assemble ---
    parts: List[str] = [f"package {package};", ""]
    parts += imports
    parts.append("")
    parts.append(f"public class {activity} extends Activity {{")
    if field_lines:
        parts.append("")
        parts.append(_indent_snippet("\n".join(field_lines), 4))
    if members:
        parts.append("")
        for chunk in members:
            parts.append(_indent_snippet(chunk, 4))
            parts.append("")
    parts.append("    @Override")
    parts.append("    protected void onCreate(Bundle savedInstanceState) {")
    parts.append("        super.onCreate(savedInstanceState);")
    if stmt.strip():
        if has_scv:
            parts.append("")
            parts.append("        // ---- your snippet ----")
            parts.append(_indent_snippet(stmt, 8))
            parts.append("        // ---- end snippet ----")
        else:
            parts.append("")
            parts.append("        LinearLayout root = new LinearLayout(this);")
            parts.append("        root.setOrientation(LinearLayout.VERTICAL);")
            parts.append("        root.setGravity(Gravity.CENTER);")
            parts.append("")
            parts.append("        // ---- your snippet ----")
            parts.append(_indent_snippet(stmt, 8))
            parts.append("        // ---- end snippet ----")
            parts.append("")
            parts.append("        setContentView(root);")
    else:
        parts.append("        LinearLayout root = new LinearLayout(this);")
        parts.append("        root.setOrientation(LinearLayout.VERTICAL);")
        parts.append("        root.setGravity(Gravity.CENTER);")
        parts.append("        setContentView(root);")
    parts.append("    }")
    parts.append("}")
    return "\n".join(parts) + "\n"


# --- snippet member extraction (v3.2) ---

_NON_METHOD_NAMES = {
    "if", "for", "while", "switch", "catch", "do", "try", "else", "finally",
    "return", "new", "throw", "synchronized", "assert", "case", "default",
}
_METHOD_TAIL_RE = re.compile(
    r"(?:^|[;{}])\s*(?:@\w+(?:\([^()]*\))?\s+)*"          # annotations
    r"(?:(?:public|private|protected|static|final|synchronized|abstract|native|default)\s+)*"
    r"(?:<[^<>]*>\s+)*"
    r"(?:[\w$][\w$.]*?(?:<[^()<>]*>)?(?:\s*\[\s*\])*\s+)?"  # optional return type
    r"([\w$]+)\s*\([^()]*\)\s*(?:throws\s+[\w$.,\s]+)?\s*$",
    re.DOTALL)
_ANON_TAIL_RE = re.compile(r"new\s+[\w.$]+\s*\([^()]*\)\s*$")


def _is_member_method_decl(header_tail: str) -> bool:
    """Does this top-level header look like a method/constructor declaration
    (and NOT a control statement, anonymous class, lambda or array init)?"""
    tail = header_tail.rstrip()
    if not tail.endswith(")"):
        return False
    if tail.endswith("->"):
        return False                       # lambda body
    if _ANON_TAIL_RE.search(tail[-120:]):
        return False                       # new Foo() { … } anonymous class
    m = _METHOD_TAIL_RE.search(tail)
    if not m:
        return False
    name = m.group(1)
    if name in _NON_METHOD_NAMES:
        return False
    return True


def split_snippet_members(text: str) -> Tuple[List[str], str]:
    """
    Split a bare snippet body into (member_chunks, statements).

    A member chunk is a top-level method/constructor declaration WITH its
    full brace-matched body (annotations and preceding comments included).
    Everything else — including control blocks, lambdas, anonymous classes
    and plain statements — is returned as the statements text so it can run
    inside onCreate().
    """
    if not text.strip():
        return [], ""
    masked = mask_java(text)
    n = len(text)
    members: List[str] = []
    member_spans: List[Tuple[int, int]] = []
    depth = 0
    boundary = 0            # start of a potential member header (top level)
    i = 0
    while i < n:
        c = masked[i]
        if c == "{":
            if depth == 0:
                header_tail = masked[max(boundary, i - 240):i]
                if _is_member_method_decl(header_tail):
                    # brace-match the method body in ONE pass
                    j = i + 1
                    d = 1
                    while j < n and d > 0:
                        cj = masked[j]
                        if cj == "{":
                            d += 1
                        elif cj == "}":
                            d -= 1
                        j += 1
                    member_spans.append((boundary, j))
                    members.append(text[boundary:j])
            depth += 1
        elif c == "}":
            depth = max(0, depth - 1)
            if depth == 0:
                boundary = i + 1
        elif c == ";" and depth == 0:
            boundary = i + 1
        i += 1

    if not member_spans:
        return [], text

    stmt_parts: List[str] = []
    prev = 0
    for s, e in member_spans:
        stmt_parts.append(text[prev:s])
        prev = e
    stmt_parts.append(text[prev:])
    stmt = "\n".join(stmt_parts)
    stmt = re.sub(r"\n{3,}", "\n\n", stmt).strip("\n")
    members = [m.strip("\n") for m in members if m.strip()]
    return members, stmt


def _promote_shared_locals(member_text: str, stmt: str) -> Tuple[List[str], str]:
    """v3.2: if a member method references a name that the statements declare
    as a LOCAL, the generated class would not compile. Promote such locals to
    FIELDS (declared at class level, still assigned inside onCreate()) — the
    standard Android pattern."""
    if not member_text.strip():
        return [], stmt
    decl_re = re.compile(
        r"^(\s*)(?:(?:final)\s+)?"
        r"([\w$][\w$.]*(?:\s*<[^=;]*?>)?(?:\s*\[\s*\])*)\s+([\w$]+)\s*=\s*")
    fields: List[str] = []
    out: List[str] = []
    for line in stmt.splitlines():
        m = decl_re.match(line)
        if m:
            indent, typ, name = m.group(1), m.group(2), m.group(3)
            used_in_members = re.search(
                r"(?<![\w.$])" + re.escape(name) + r"\b", member_text)
            redeclared_in_members = re.search(
                r"[\w$>\]]\s+" + re.escape(name) + r"\s*(?:=[^=]|[,;)])",
                member_text)
            if used_in_members and not redeclared_in_members:
                fields.append(f"private {typ} {name};")
                rhs = line[m.end():]
                # v3.2.1: a bare array initializer ({ 1, 2 }) is only legal in
                # a DECLARATION — as a plain assignment it must be rewritten:
                #     arr = { 1, 2 };          X  does not compile
                #     arr = new int[] { 1, 2 };  OK
                if rhs.lstrip().startswith("{"):
                    # typ already carries its own brackets ("int[]"), so the
                    # new-expression needs NO extra []:  new int[] { 1, 2 }
                    base_type = typ.split("<")[0].strip()
                    rhs = rhs.lstrip()
                    rhs = f"new {base_type} " + rhs
                out.append(f"{indent}{name} = " + rhs)
                continue
        out.append(line)
    return fields, "\n".join(out)


def _indent_snippet(text: str, spaces: int) -> str:
    """Indent every non-empty line by the given number of spaces."""
    pad = " " * spaces
    return "\n".join((pad + line if line.strip() else "") for line in text.rstrip().splitlines())


# ---------------------------------------------------------------------------
# Friendly javac error translation
# ---------------------------------------------------------------------------
_RE_JAVAC_ERROR_LINE = re.compile(r"([\w\\/:.-]+\.java):(\d+):\s*error:\s*(.*)")
_RE_JAVAC_POSITION = re.compile(r"\.java:\d+:")


def friendly_javac_errors(stdout: str) -> List[str]:
    """Translate raw javac output into plain-English, actionable hints."""
    hints: List[str] = []
    lines = stdout.splitlines()
    i = 0
    seen = set()

    def add(h: str):
        """Append a hint once (deduplicated by exact text)."""
        if h not in seen:
            seen.add(h)
            hints.append(h)

    # v3.3.1: whole-output patterns that don't follow the file:line:error shape
    if re.search(r"invalid (?:source|target) release", stdout):
        add("The located JDK is older than the requested -source/-target "
            "level (a JDK 6 compiler cannot do -source 1.8). Install JDK 8+ "
            "— e.g. Temurin from https://adoptium.net — or point Settings → "
            "JDK bin folder at a newer JDK. (v3.3.1+ auto-picks the right "
            "level and auto-switches to the newest JDK on the machine.)")
    if re.search(r"bad class file|class file has wrong version", stdout):
        add("android.jar (or another library) contains class files newer "
            "than this JDK can read — install a newer JDK (8+) or use an "
            "older android.jar.")

    while i < len(lines):
        line = lines[i]
        m = _RE_JAVAC_ERROR_LINE.search(line)
        if m:
            path, lineno, msg = m.group(1), m.group(2), m.group(3).strip()
            where = f"line {lineno}"
            # gather symbol/location continuation lines
            symbol = ""
            location = ""
            j = i + 1
            while j < len(lines) and not _RE_JAVAC_POSITION.search(lines[j]) \
                    and lines[j].strip() and not lines[j].startswith("Note:") \
                    and lines[j].strip()[0] in "symbollocation        ":
                if lines[j].strip().startswith("symbol:"):
                    symbol = lines[j].strip()
                elif lines[j].strip().startswith("location:"):
                    location = lines[j].strip()
                j += 1

            if "cannot find symbol" in msg and symbol:
                sym = symbol.replace("symbol:", "").strip()
                sym_name = sym.split()[-1] if sym else ""
                if sym.startswith("class"):
                    if sym_name == "R" or sym_name.startswith("R."):
                        add(f"[error] {where}: {sym_name} — R references need compiled XML "
                            f"resources. APK Forge generates R.anim/R.string automatically; "
                            f"images tagged 'drawable' and sounds tagged 'raw' on the "
                            f"Design page DO get real R.drawable/R.raw ids (check the "
                            f"'Access in code' column there). For layouts, build the UI "
                            f"programmatically (new LinearLayout(this)) instead of "
                            f"R.layout.")
                    elif sym_name == "var":
                        add(f"[error] {where}: 'var' is not a type here — this forge compiles "
                            f"with Java 8; spell out the type (Button b = …).")
                    elif sym_name in IMPORT_CATALOG:
                        add(f"[error] {where}: class '{sym_name}' is not imported → "
                            f"add `import {IMPORT_CATALOG[sym_name]};` "
                            f"(Source page → 'Fix Imports' does this automatically).")
                    else:
                        add(f"[error] {where}: unknown class '{sym_name}'. Check the spelling, "
                            f"or fully qualify it (e.g. android.widget.Button).")
                elif sym.startswith("variable") or sym.startswith("method") \
                        or sym.startswith("constructor"):
                    if sym_name == "R" or sym_name.startswith("R."):
                        add(f"[error] {where}: {sym_name} — R references need compiled XML "
                            f"resources; build the UI programmatically instead. Assets "
                            f"tagged 'drawable'/'raw' on the Design page get real "
                            f"R.drawable./R.raw. ids — copy the exact reference from "
                            f"its 'Access in code' column.")
                    else:
                        add(f"[error] {where}: {msg} — {sym}. "
                            f"Check the declaration, its scope and the exact name/arguments.")
                else:
                    add(f"[error] {where}: {msg} — {symbol}")
            elif "package androidx" in msg or "package android.support" in msg \
                    or "does not exist" in msg and "androidx" in msg:
                add("androidx/support libraries are not available in this forge. "
                    "Extend android.app.Activity and use framework classes "
                    "(diagnostics → 'Try migration' may fix common cases).")
            elif "package R does not exist" in msg:
                add("R references need compiled XML resources — build the UI "
                    "programmatically (new LinearLayout(this)) instead of "
                    "R.layout / R.id lookups.")
            elif "duplicate class" in msg:
                add(f"[error] {where}: duplicate class — the same class name is declared "
                    f"twice in the file; rename or remove one of them.")
            elif "class, interface, enum, or record expected" in msg:
                add(f"[error] {where}: statements outside of a class/method — wrap bare "
                    f"statements in a class, or paste them as a snippet (snippet "
                    f"mode places them inside onCreate() automatically).")
            elif "is public, should be declared in a file named" in msg:
                add(f"[error] {where}: class/file name mismatch — normally fixed "
                    f"automatically by the all-in-one splitter.")
            elif "method does not override" in msg:
                add(f"[error] {where}: @Override does not match a super method — "
                    f"remove @Override or match the exact signature.")
            elif "';' expected" in msg or "'(' expected" in msg or "')' expected" in msg \
                    or "'{' expected" in msg or "'}' expected" in msg:
                add(f"[error] {where}: syntax error ({msg}) — check brackets/semicolons "
                    f"around that line.")
            elif "incompatible types" in msg or "bad operand" in msg:
                add(f"[error] {where}: type mismatch — {msg}")
            elif "constructor" in msg and "cannot be applied" in msg:
                add(f"[error] {where}: constructor arguments do not match — {msg}")
            elif "is not abstract and does not override" in msg:
                add(f"[error] {where}: your class implements an interface but misses "
                    f"some of its methods — implement all of them.")
            elif "restricted local variable type" in msg or "'var' is not allowed" in msg:
                add(f"[error] {where}: 'var' requires Java 10+ — this forge compiles with "
                    f"Java 8; declare the explicit type instead (Button b = …).")
            else:
                add(f"[error] {where}: {msg}")
            i = j
            continue
        i += 1

    if not hints and stdout.strip():
        first_err = next((l for l in lines if "error:" in l), None)
        if first_err:
            add(first_err.strip())
    return hints[:8]


# ---------------------------------------------------------------------------
# ELEMENTS, MEDIA & ANIMATION INJECTION (brace-aware, compile-safe)
# ---------------------------------------------------------------------------

@dataclass
class ElementInfo:
    """Information about a UI element found in code."""
    name: str                 # Variable name (e.g., "myButton")
    type: str                 # Element type (e.g., "Button", "TextView")
    line_number: int = 0
    animations: List[str] = field(default_factory=list)
    animation_duration: int = 300   # Duration in milliseconds
    sound_path: str = ""
    image_path: str = ""
    auto_size: bool = True


@dataclass
class MediaResource:
    """Media resource (image/sound) to be included."""
    source_path: str
    resource_name: str
    resource_type: str        # 'drawable', 'raw'
    used_by: List[str] = field(default_factory=list)


UI_TYPES = [
    'Button', 'TextView', 'EditText', 'ImageView', 'ImageButton',
    'CheckBox', 'RadioButton', 'Switch', 'ToggleButton',
    'ProgressBar', 'SeekBar', 'RatingBar',
    'ListView', 'GridView', 'RecyclerView',
    'LinearLayout', 'RelativeLayout', 'FrameLayout', 'ConstraintLayout',
    'CardView', 'FloatingActionButton', 'Toolbar', 'ScrollView',
    'HorizontalScrollView', 'RadioGroup', 'Spinner', 'WebView', 'View',
    'SurfaceView', 'ViewFlipper', 'ViewSwitcher', 'TextSwitcher',
    'ImageSwitcher', 'VideoView', 'Chronometer', 'TextClock', 'SearchView',
    'DatePicker', 'TimePicker', 'TabHost', 'ZoomControls',
]


# ---------------------------------------------------------------------------
# v3.5 BUILT-IN SOUND LIBRARY — 12 beautiful sounds synthesized in pure Python
# ---------------------------------------------------------------------------
# 44.1 kHz mono 16-bit WAV: soft attacks, exponential decays, gentle harmonic
# content — no harsh beeps, no downloads, no licensing. Files materialize on
# demand into ~/.apkforge/builtin_sounds/ and are cached from then on.

BUILTIN_SOUNDS: Dict[str, str] = {
    "click":   "Click — soft UI tick",
    "tap":     "Tap — gentle pop",
    "pop":     "Pop — bubbly burst",
    "success": "Success — bright major chime",
    "levelup": "Level up — rising fanfare",
    "coin":    "Coin — classic two-tone",
    "chime":   "Chime — crystal ding",
    "sparkle": "Sparkle — rising shimmer",
    "notify":  "Notify — friendly two-note",
    "whoosh":  "Whoosh — airy sweep",
    "error":   "Error — soft low buzz",
    "drum":    "Drum — punchy thump",
}

_SOUND_SR = 44100
_BUILTIN_SOUND_DIR = Path.home() / ".apkforge" / "builtin_sounds"


# --- DSP synthesis helpers ---

def _snd_buffer(dur: float) -> List[float]:
    """Allocate a zeroed sample buffer lasting dur seconds."""
    return [0.0] * int(dur * _SOUND_SR)


def _snd_tone(buf: List[float], freq: float, start: float, dur: float,
              amp: float = 0.3, tau: float = 0.15,
              partials: Tuple[Tuple[float, float], ...] = ((1, 1.0), (2, 0.32), (3, 0.10)),
              attack: float = 0.012) -> None:
    """Additively add one tone (soft attack + exponential decay) to buf."""
    i0 = int(start * _SOUND_SR)
    n = min(int(dur * _SOUND_SR), len(buf) - i0)
    if n <= 0:
        return
    for i in range(n):
        t = i / _SOUND_SR
        env = min(1.0, t / attack) * math.exp(-t / tau)
        s = 0.0
        for mult, pa in partials:
            s += pa * math.sin(2.0 * math.pi * freq * mult * t)
        buf[i0 + i] += amp * env * s


def _snd_sweep(buf: List[float], f0: float, f1: float, start: float, dur: float,
               amp: float = 0.3, tau: float = 0.08, attack: float = 0.003) -> None:
    """Frequency sweep (geometric) with soft attack + decay."""
    i0 = int(start * _SOUND_SR)
    n = min(int(dur * _SOUND_SR), len(buf) - i0)
    if n <= 0:
        return
    phase = 0.0
    for i in range(n):
        t = i / n
        f = f0 * (f1 / f0) ** t
        phase += 2.0 * math.pi * f / _SOUND_SR
        ts = i / _SOUND_SR
        env = min(1.0, ts / attack) * math.exp(-ts / tau)
        buf[i0 + i] += amp * env * math.sin(phase)


def _snd_noise(buf: List[float], start: float, dur: float, amp: float = 0.2,
               highpass: bool = True, bell: bool = True, seed: int = 7) -> None:
    """Noise burst (optionally high-passed by differencing) with a bell
    amplitude envelope — for whooshes / transient clicks."""
    rng = random.Random(seed)
    i0 = int(start * _SOUND_SR)
    n = min(int(dur * _SOUND_SR), len(buf) - i0)
    if n <= 0:
        return
    prev = 0.0
    for i in range(n):
        x = rng.random() * 2.0 - 1.0
        y = (x - prev) if highpass else x
        prev = x
        e = math.sin(math.pi * (i / n)) if bell else math.exp(-(i / n) * 5.0)
        buf[i0 + i] += amp * e * y


# --- sound generators (one per BUILTIN_SOUNDS entry) ---

def _gen_click() -> List[float]:
    """Synthesize the built-in 'click' sound (soft UI tick)."""
    buf = _snd_buffer(0.05)
    _snd_tone(buf, 1900, 0.0, 0.035, amp=0.50, tau=0.008,
              partials=((1, 1.0), (2, 0.45)), attack=0.001)
    _snd_tone(buf, 2400, 0.0, 0.025, amp=0.20, tau=0.006,
              partials=((1, 1.0),), attack=0.001)
    _snd_tone(buf, 210, 0.0, 0.030, amp=0.25, tau=0.010,
              partials=((1, 1.0),), attack=0.001)
    return buf


def _gen_tap() -> List[float]:
    """Synthesize the built-in 'tap' sound (gentle pop)."""
    buf = _snd_buffer(0.08)
    _snd_sweep(buf, 720, 360, 0.0, 0.055, amp=0.42, tau=0.022, attack=0.003)
    _snd_tone(buf, 950, 0.0, 0.018, amp=0.12, tau=0.006,
              partials=((1, 1.0),), attack=0.001)
    return buf


def _gen_pop() -> List[float]:
    """Synthesize the built-in 'pop' sound (bubbly burst)."""
    buf = _snd_buffer(0.11)
    _snd_sweep(buf, 320, 880, 0.0, 0.05, amp=0.40, tau=0.030, attack=0.002)
    _snd_noise(buf, 0.0, 0.006, amp=0.12, highpass=True, bell=False)
    return buf


def _gen_success() -> List[float]:
    """Synthesize the built-in 'success' sound (bright major chime)."""
    buf = _snd_buffer(0.90)
    for freq, st, tau in ((523.25, 0.00, 0.20), (659.25, 0.13, 0.20),
                          (783.99, 0.26, 0.20), (1046.50, 0.40, 0.42)):
        _snd_tone(buf, freq, st, 0.5, amp=0.30, tau=tau,
                  partials=((1, 1.0), (2, 0.28), (3, 0.08)))
    return buf


def _gen_levelup() -> List[float]:
    """Synthesize the built-in 'levelup' sound (rising fanfare)."""
    buf = _snd_buffer(1.05)
    for freq, st, tau in ((392.00, 0.00, 0.12), (523.25, 0.11, 0.12),
                          (659.25, 0.22, 0.12), (783.99, 0.33, 0.14)):
        _snd_tone(buf, freq, st, 0.30, amp=0.28, tau=tau,
                  partials=((1, 1.0), (2, 0.25)))
    _snd_tone(buf, 1046.50, 0.47, 0.55, amp=0.30, tau=0.50,
              partials=((1, 1.0), (2, 0.30), (3, 0.10)))
    return buf


def _gen_coin() -> List[float]:
    """Synthesize the built-in 'coin' sound (classic two-tone)."""
    buf = _snd_buffer(0.45)
    _snd_tone(buf, 987.77, 0.00, 0.10, amp=0.30, tau=0.05,
              partials=((1, 1.0), (3, 0.22), (5, 0.06)), attack=0.002)
    _snd_tone(buf, 1318.51, 0.07, 0.35, amp=0.30, tau=0.13,
              partials=((1, 1.0), (3, 0.22), (5, 0.06)), attack=0.002)
    return buf


def _gen_chime() -> List[float]:
    """Synthesize the built-in 'chime' sound (crystal ding)."""
    buf = _snd_buffer(1.15)
    _snd_tone(buf, 987.77, 0.0, 1.0, amp=0.30, tau=0.40,
              partials=((1, 1.0), (2.756, 0.38), (5.40, 0.13)))
    _snd_noise(buf, 0.0, 0.004, amp=0.06, highpass=True, bell=False)
    return buf


def _gen_sparkle() -> List[float]:
    """Synthesize the built-in 'sparkle' sound (rising shimmer)."""
    buf = _snd_buffer(0.70)
    notes = (880.0, 1046.5, 1174.7, 1318.5, 1568.0, 1760.0)
    for k, freq in enumerate(notes):
        st = 0.055 * k
        _snd_tone(buf, freq, st, 0.18, amp=0.20, tau=0.07,
                  partials=((1, 1.0), (2, 0.20)), attack=0.004)
        _snd_tone(buf, freq * 1.012, st + 0.012, 0.14, amp=0.09, tau=0.06,
                  partials=((1, 1.0),), attack=0.004)
    return buf


def _gen_notify() -> List[float]:
    """Synthesize the built-in 'notify' sound (friendly two-note)."""
    buf = _snd_buffer(0.60)
    _snd_tone(buf, 587.33, 0.00, 0.16, amp=0.30, tau=0.08,
              partials=((1, 1.0), (3, 0.18)))
    _snd_tone(buf, 880.00, 0.13, 0.40, amp=0.30, tau=0.16,
              partials=((1, 1.0), (3, 0.18)))
    return buf


def _gen_whoosh() -> List[float]:
    """Synthesize the built-in 'whoosh' sound (airy sweep)."""
    buf = _snd_buffer(0.50)
    _snd_noise(buf, 0.02, 0.42, amp=0.30, highpass=True, bell=True, seed=11)
    _snd_sweep(buf, 220, 90, 0.02, 0.40, amp=0.14, tau=0.25, attack=0.05)
    return buf


def _gen_error() -> List[float]:
    """Synthesize the built-in 'error' sound (soft low buzz)."""
    buf = _snd_buffer(0.42)
    for st in (0.0, 0.17):
        _snd_tone(buf, 196, st, 0.13, amp=0.26, tau=0.05,
                  partials=((1, 1.0), (2, 0.30)), attack=0.004)
        _snd_tone(buf, 147, st, 0.13, amp=0.16, tau=0.05,
                  partials=((1, 1.0),), attack=0.004)
    # gentle low-pass smoothing so the buzz stays soft, never harsh
    out = buf[:]
    for i in range(2, len(buf)):
        buf[i] = (out[i] + out[i - 1] + out[i - 2]) / 3.0
    return buf


def _gen_drum() -> List[float]:
    """Synthesize the built-in 'drum' sound (punchy thump)."""
    buf = _snd_buffer(0.25)
    _snd_sweep(buf, 150, 48, 0.0, 0.16, amp=0.85, tau=0.09, attack=0.002)
    _snd_noise(buf, 0.0, 0.004, amp=0.18, highpass=True, bell=False, seed=3)
    return buf


_SOUND_GENERATORS: Dict[str, Callable[[], List[float]]] = {
    "click": _gen_click, "tap": _gen_tap, "pop": _gen_pop,
    "success": _gen_success, "levelup": _gen_levelup, "coin": _gen_coin,
    "chime": _gen_chime, "sparkle": _gen_sparkle, "notify": _gen_notify,
    "whoosh": _gen_whoosh, "error": _gen_error, "drum": _gen_drum,
}


def _render_wav(samples: List[float]) -> bytes:
    """Float samples → 16-bit mono WAV bytes (peak-normalised, 2 ms fades)."""
    n = len(samples)
    if n == 0:
        return b""
    peak = max((abs(s) for s in samples), default=0.0)
    scale = (0.88 / peak) if peak > 0.88 else 1.0
    fade = max(1, int(0.002 * _SOUND_SR))
    ints = array.array("h", (
        int(max(-1.0, min(1.0, samples[i] * scale)) * 32767.0
            * min(1.0, (i + 1) / fade)
            * min(1.0, (n - i) / fade))
        for i in range(n)))
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_SOUND_SR)
        w.writeframes(ints.tobytes())
    return out.getvalue()


def builtin_sound_path(sound_id: str) -> str:
    """Materialize (and cache) a built-in sound — returns the WAV path or ''."""
    if sound_id not in BUILTIN_SOUNDS:
        return ""
    try:
        _BUILTIN_SOUND_DIR.mkdir(parents=True, exist_ok=True)
        p = _BUILTIN_SOUND_DIR / f"{sound_id}.wav"
        if not p.exists() or p.stat().st_size == 0:
            gen = _SOUND_GENERATORS.get(sound_id)
            if gen is None:
                return ""
            data = _render_wav(gen())
            if not data:
                return ""
            tmp = p.with_name(f"{sound_id}.{os.getpid()}.{threading.get_ident()}.tmp")
            tmp.write_bytes(data)
            tmp.replace(p)
        return str(p)
    except Exception:
        return ""


def builtin_sound_label(sound_path: str) -> str:
    """Pretty label for a sound path ('builtin:success' → 'Success — bright major chime')."""
    if sound_path and sound_path.startswith("builtin:"):
        sid = sound_path[8:]
        return BUILTIN_SOUNDS.get(sid, sid)
    if sound_path:
        return Path(sound_path).name
    return ""


class ResourceManager:
    """Manages media resources (images, sounds) for the APK."""

    def __init__(self):
        """Create an empty resource table."""
        self.resources: Dict[str, MediaResource] = {}
        self.next_id = 1

    def add_resource(self, source_path: str, resource_type: str, element_name: str = "") -> str:
        """Add a resource and return its resource name."""
        # v3.5: built-in library sounds ("builtin:success") materialize into
        # ~/.apkforge/builtin_sounds/ on demand, then flow through the normal
        # raw-resource pipeline (R.raw.success).
        if source_path and source_path.startswith("builtin:"):
            source_path = builtin_sound_path(source_path[len("builtin:"):].strip())
        if not source_path or not Path(source_path).exists():
            return ""

        src = Path(source_path)
        base_name = src.stem.lower().replace(" ", "_").replace("-", "_")
        base_name = re.sub(r'[^a-z0-9_]', '', base_name)

        if not base_name or base_name[0].isdigit():
            base_name = f"res_{self.next_id}"
            self.next_id += 1

        # de-duplicate by source path
        for res_name, res in self.resources.items():
            if res.source_path == source_path:
                if element_name and element_name not in res.used_by:
                    res.used_by.append(element_name)
                return res_name

        # avoid collisions with different files mapping to the same name
        final_name = base_name
        n = 2
        while final_name in self.resources:
            final_name = f"{base_name}_{n}"
            n += 1

        resource = MediaResource(
            source_path=source_path,
            resource_name=final_name,
            resource_type=resource_type,
            used_by=[element_name] if element_name else []
        )
        self.resources[final_name] = resource
        return final_name

    def remove_resource(self, resource_name: str):
        """Drop one resource by name."""
        self.resources.pop(resource_name, None)

    def remove_element_resources(self, element_name: str):
        """Unlink an element and drop any resources left unused."""
        to_remove = []
        for res_name, res in self.resources.items():
            if element_name in res.used_by:
                res.used_by.remove(element_name)
            if not res.used_by:
                to_remove.append(res_name)
        for res_name in to_remove:
            del self.resources[res_name]

    def copy_resources(self, res_dir: Path, log_cb=None):
        """Copy every managed resource into res_dir/<resource_type>/."""
        for res_name, res in self.resources.items():
            target_dir = res_dir / res.resource_type
            target_dir.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(res.source_path,
                             target_dir / f"{res_name}{Path(res.source_path).suffix}")
                if log_cb:
                    log_cb(f"[{log_time()}] Copied {res.resource_type}: {res_name}")
            except Exception as e:
                if log_cb:
                    log_cb(f"[{log_time()}] [warn] Failed to copy {res.source_path}: {e}")


# --- META round-trip markers (injected comments → element config) ---

_RE_AUTOGEN_FOR = re.compile(r'//\s*Auto-generated for\s+(\w+)')
_RE_META_TYPE = re.compile(r'//\s*META:\s*type=(\w+)')
_RE_META_ANIMS = re.compile(r'//\s*META:\s*animations=([^\n]+)')
_RE_META_DURATION = re.compile(r'//\s*META:\s*duration=(\d+)')
_RE_META_SOUND = re.compile(r'//\s*META:\s*sound_path=([^\n]+)')
_RE_META_IMAGE = re.compile(r'//\s*META:\s*image_path=([^\n]+)')
_RE_META_AUTO_SIZE = re.compile(r'//\s*META:\s*auto_size=(True|False)')


def parse_animations_from_java(java_code: str) -> List[ElementInfo]:
    """Parse auto-generated animation code (// META comments) back into elements."""
    elements: List[ElementInfo] = []
    for match in _RE_AUTOGEN_FOR.finditer(java_code):
        element_name = match.group(1)
        start_pos = match.start()
        end_pos = java_code.find('} catch (Exception e)', start_pos)
        if end_pos == -1:
            end_pos = java_code.find('        });', start_pos)
        if end_pos == -1:
            end_pos = min(len(java_code), start_pos + 4000)
        code_block = java_code[start_pos:end_pos + 100]

        element_type = 'View'
        animations: List[str] = []
        duration = 300
        sound_path = ''
        image_path = ''
        auto_size = True

        meta_type = _RE_META_TYPE.search(code_block)
        if meta_type:
            element_type = meta_type.group(1)
        meta_anims = _RE_META_ANIMS.search(code_block)
        if meta_anims:
            animations = [a.strip() for a in meta_anims.group(1).split(',') if a.strip()]
        meta_duration = _RE_META_DURATION.search(code_block)
        if meta_duration:
            duration = int(meta_duration.group(1))
        meta_sound = _RE_META_SOUND.search(code_block)
        if meta_sound:
            sound_path = meta_sound.group(1).strip()
        meta_image = _RE_META_IMAGE.search(code_block)
        if meta_image:
            image_path = meta_image.group(1).strip()
        meta_auto_size = _RE_META_AUTO_SIZE.search(code_block)
        if meta_auto_size:
            auto_size = meta_auto_size.group(1) == 'True'

        if not any(e.name == element_name for e in elements):
            elements.append(ElementInfo(
                name=element_name, type=element_type,
                animations=animations, animation_duration=duration,
                sound_path=sound_path, image_path=image_path, auto_size=auto_size))
    return elements


# v3.5 SINGLE-PASS element scan: three compiled patterns replace the old
# 2 × 60 full-text scans PER VARIABLE (a 13 000-line file spent >1 s here).
_UI_TYPE_ALT = "|".join(sorted(UI_TYPES))
_UI_TYPE_SET = frozenset(UI_TYPES)
_UI_DECL_RE = re.compile(rf'\b({_UI_TYPE_ALT})\s+([a-zA-Z_]\w*)\s*[=;]')
_UI_NEW_RE = re.compile(rf'\b([a-zA-Z_]\w*)\s*=\s*new\s+({_UI_TYPE_ALT})\s*\(')
_UI_FID_RE = re.compile(r'\b([a-zA-Z_]\w*)\s*=\s*(?:\(([\w.<>\[\]]+)\)\s*)?findViewById')


def _ui_variable_types(java_code: str, masked: Optional[str] = None) -> Dict[str, str]:
    """UI variable name → element type — ONE regex pass per declaration style.

    v3.5: replaces thousands of per-variable full-text scans (~250× faster on
    large files) and detects variables the old scanner silently dropped:
    ``x = new TextView(...)`` and ``x = (TextView) findViewById(...)``.
    Insertion order = code order."""
    code = masked if masked is not None else mask_java(java_code)
    out: Dict[str, str] = {}
    for m in _UI_DECL_RE.finditer(code):          # Type name = … ;  (declaration)
        out[m.group(2)] = m.group(1)
    for m in _UI_NEW_RE.finditer(code):           # name = new Type(…
        out.setdefault(m.group(1), m.group(2))
    for m in _UI_FID_RE.finditer(code):           # name = (Type) findViewById(…
        var, cast = m.group(1), m.group(2)
        if cast:
            simple = cast.split(".")[-1].split("<")[0].rstrip("[]")
            if simple in _UI_TYPE_SET:
                out.setdefault(var, simple)
        else:
            out.setdefault(var, "View")           # untyped findViewById
    return out


def find_variables_in_scope(java_code: str) -> set:
    """Find UI variable names declared or assigned in the Java code."""
    return set(_ui_variable_types(java_code))


def parse_elements_from_java(java_code: str) -> List[ElementInfo]:
    """Parse UI elements from Java code (round-trips injected META config first)."""
    if not java_code:
        return []
    existing = parse_animations_from_java(java_code)
    if existing:
        return existing
    masked = mask_java(java_code)                 # v3.5: shared, memoised scan
    var_types = _ui_variable_types(java_code, masked)
    return [ElementInfo(name=n, type=t) for n, t in var_types.items()]


def generate_animation_xml(anim_type: str, duration: int = 300) -> str:
    """Generate XML for an animation resource."""
    animations_xml = {
        "fade_in": f'''<?xml version="1.0" encoding="utf-8"?>
<alpha xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromAlpha="0.0" android:toAlpha="1.0" android:duration="{duration}" />''',
        "fade_out": f'''<?xml version="1.0" encoding="utf-8"?>
<alpha xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromAlpha="1.0" android:toAlpha="0.0" android:duration="{duration}" />''',
        "slide_in_left": f'''<?xml version="1.0" encoding="utf-8"?>
<translate xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromXDelta="-100%" android:toXDelta="0%" android:duration="{duration}" />''',
        "slide_in_right": f'''<?xml version="1.0" encoding="utf-8"?>
<translate xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromXDelta="100%" android:toXDelta="0%" android:duration="{duration}" />''',
        "slide_in_top": f'''<?xml version="1.0" encoding="utf-8"?>
<translate xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromYDelta="-100%" android:toYDelta="0%" android:duration="{duration}" />''',
        "slide_in_bottom": f'''<?xml version="1.0" encoding="utf-8"?>
<translate xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromYDelta="100%" android:toYDelta="0%" android:duration="{duration}" />''',
        "slide_out_left": f'''<?xml version="1.0" encoding="utf-8"?>
<translate xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromXDelta="0%" android:toXDelta="-100%" android:duration="{duration}" />''',
        "slide_out_right": f'''<?xml version="1.0" encoding="utf-8"?>
<translate xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromXDelta="0%" android:toXDelta="100%" android:duration="{duration}" />''',
        "scale_in": f'''<?xml version="1.0" encoding="utf-8"?>
<scale xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromXScale="0.0" android:toXScale="1.0"
    android:fromYScale="0.0" android:toYScale="1.0"
    android:pivotX="50%" android:pivotY="50%" android:duration="{duration}" />''',
        "scale_out": f'''<?xml version="1.0" encoding="utf-8"?>
<scale xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromXScale="1.0" android:toXScale="0.0"
    android:fromYScale="1.0" android:toYScale="0.0"
    android:pivotX="50%" android:pivotY="50%" android:duration="{duration}" />''',
        "rotate": f'''<?xml version="1.0" encoding="utf-8"?>
<rotate xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromDegrees="0" android:toDegrees="360"
    android:pivotX="50%" android:pivotY="50%" android:duration="{duration}" />''',
        "bounce": f'''<?xml version="1.0" encoding="utf-8"?>
<set xmlns:android="http://schemas.android.com/apk/res/android"
    android:interpolator="@android:anim/bounce_interpolator">
    <translate android:fromYDelta="-50%" android:toYDelta="0%" android:duration="{duration}" />
</set>''',
        "shake": '''<?xml version="1.0" encoding="utf-8"?>
<translate xmlns:android="http://schemas.android.com/apk/res/android"
    android:fromXDelta="0%" android:toXDelta="2%" android:duration="50"
    android:repeatCount="5" android:repeatMode="reverse" />''',
    }
    return animations_xml.get(anim_type, "")


# ---------------------------------------------------------------------------
# SAFE animation & media injection (compile-safe via the structure scanner)
# ---------------------------------------------------------------------------

def _indent_block(text: str, indent: str) -> str:
    """Re-indent a code block one level deeper beneath the given indent."""
    pad = indent + "    "
    return "\n".join((pad + line if line.strip() else "") for line in text.strip("\n").splitlines())


def _element_code(element: ElementInfo, cls: str, resource_manager: ResourceManager) -> str:
    """Java statements configuring one element (round-trippable META included)."""
    e = []
    e.append(f"// Auto-generated for {element.name}")
    e.append(f"// META: type={element.type}")
    if element.animations:
        e.append(f"// META: animations={','.join(element.animations)}")
        e.append(f"// META: duration={element.animation_duration}")
    if element.sound_path:
        e.append(f"// META: sound_path={element.sound_path}")
    if element.image_path:
        e.append(f"// META: image_path={element.image_path}")
        e.append(f"// META: auto_size={element.auto_size}")

    e.append("try {")
    # v3.5 CONTEXT FIX: injections can land ANYWHERE the element is declared —
    # including inside anonymous inner classes (Runnable.run(), listeners,
    # adapters) where a bare `this` is the ANONYMOUS instance, not the
    # Activity ("incompatible types: <anonymous Runnable> cannot be converted
    # to Context" — 48 errors and a dead build). Every Context / Resources /
    # package reference now derives from the ELEMENT itself:
    #   element.getContext() · element.getResources()
    #   element.getContext().getPackageName()
    # which is legal in any scope where the element variable is visible.
    # v3.3 ANIMATION FUSION: a View runs ONE animation — separate
    # startAnimation() calls REPLACE each other, so a preset like "Material
    # Entrance" (fade_in + slide_in_bottom) silently played only its LAST
    # entry. All of the element's animations now compose into ONE
    # AnimationSet started exactly once; shareInterpolator=false keeps each
    # child's own interpolator (the bounce curve survives).
    anims = list(dict.fromkeys(element.animations))   # dedupe, keep order
    if anims:
        set_var = f"anim_set_{element.name}"
        e.append("    try {")
        e.append(f"        android.view.animation.AnimationSet {set_var} ="
                 " new android.view.animation.AnimationSet(false);")
        for idx, anim in enumerate(anims):
            idv = f"anim_id_{element.name}_{idx}"
            av = f"anim_a_{element.name}_{idx}"
            e.append("        try {")
            e.append(f"            int {idv} = {element.name}.getResources().getIdentifier("
                     f"\"{anim}\", \"anim\", "
                     f"{element.name}.getContext().getPackageName());")
            e.append(f"            if ({idv} != 0) {{")
            e.append(f"                android.view.animation.Animation {av} ="
                     f" android.view.animation.AnimationUtils.loadAnimation("
                     f"{element.name}.getContext(), {idv});")
            e.append(f"                if ({av} != null) {set_var}.addAnimation({av});")
            e.append("            }")
            e.append("        } catch (Exception ex) { }")
        e.append(f"        {element.name}.startAnimation({set_var});")
        e.append("    } catch (Exception ex) { }")

    if element.image_path:
        res_name = resource_manager.add_resource(element.image_path, 'drawable', element.name)
        if res_name:
            e.append("    try {")
            e.append(f"        int drawable_id_{element.name} ="
                     f" {element.name}.getResources().getIdentifier("
                     f"\"{res_name}\", \"drawable\", "
                     f"{element.name}.getContext().getPackageName());")
            e.append(f"        if (drawable_id_{element.name} != 0) {{")
            if element.type in ('ImageView', 'ImageButton'):
                e.append(f"            {element.name}.setImageResource("
                         f"drawable_id_{element.name});")
                if element.auto_size:
                    e.append(f"            {element.name}.setScaleType("
                             f"android.widget.ImageView.ScaleType.FIT_CENTER);")
                else:
                    e.append(f"            {element.name}.setScaleType("
                             f"android.widget.ImageView.ScaleType.CENTER_CROP);")
                e.append(f"            {element.name}.setAdjustViewBounds(true);")
            else:
                e.append(f"            android.graphics.drawable.Drawable drawable_{element.name}"
                         f" = {element.name}.getResources().getDrawable("
                         f"drawable_id_{element.name});")
                e.append(f"            if (drawable_{element.name} != null) {{")
                e.append(f"                drawable_{element.name}.setBounds(0, 0, "
                         f"{element.name}.getWidth(), {element.name}.getHeight());")
                e.append(f"                {element.name}.setBackground(drawable_{element.name});")
                e.append(f"            }}")
            e.append(f"        }}")
            e.append("    } catch (Exception ex) { }")

    if element.sound_path:
        res_name = resource_manager.add_resource(element.sound_path, 'raw', element.name)
        if res_name:
            # v3.5: the Context is captured into a FINAL local BEFORE the
            # listener, so the anonymous OnClickListener never captures the
            # (possibly reassigned) element variable — the Java-8
            # effectively-final rule can never break this block.
            e.append("    try {")
            e.append(f"        final int sound_id_{element.name} ="
                     f" {element.name}.getResources().getIdentifier("
                     f"\"{res_name}\", \"raw\", "
                     f"{element.name}.getContext().getPackageName());")
            e.append(f"        if (sound_id_{element.name} != 0) {{")
            e.append(f"            final android.content.Context snd_ctx_{element.name}"
                     f" = {element.name}.getContext();")
            e.append(f"            {element.name}.setOnClickListener("
                     f"new android.view.View.OnClickListener() {{")
            e.append(f"                @Override public void onClick(android.view.View v) {{")
            e.append(f"                    try {{")
            e.append(f"                        if (mediaPlayer != null) mediaPlayer.release();")
            e.append(f"                        mediaPlayer ="
                     f" android.media.MediaPlayer.create("
                     f"snd_ctx_{element.name}, sound_id_{element.name});")
            e.append(f"                        if (mediaPlayer != null) mediaPlayer.start();")
            e.append(f"                    }} catch (Exception ex) {{ }}")
            e.append(f"                }}")
            e.append(f"            }});")
            e.append(f"        }}")
            e.append("    } catch (Exception ex) { }")

    e.append("} catch (Exception ex) { }")
    return "\n".join(e)


# --- injection-point regexes (hoisted out of the injection loops) ---

_RE_EXTENDS_ACTIVITY = re.compile(
    r'\bextends\s+(?:[\w.]+\.)?(?:Activity|ListActivity|ActivityGroup)\b')
_RE_LEADING_WS = re.compile(r"[ \t]*")


def inject_animations_and_media(java_code: str, elements: List[ElementInfo],
                                resource_manager: ResourceManager, package_name: str,
                                log_cb=None) -> str:
    """
    Inject animation / media code AFTER the element's declaration statement.

    v3 uses the structure scanner so injections only ever land inside METHOD
    bodies (statement contexts) — injecting into class-level field
    initializers (a v2 bug that produced invalid Java) is now impossible.
    Field-only elements fall back to an injection at the end of onCreate(),
    where the field is in scope.
    """
    valid_elements = [e for e in elements if (e.animations or e.sound_path or e.image_path)]
    if not valid_elements:
        return java_code

    struct = scan_java_structure(java_code)
    types = struct["types"]
    stmt_spans = struct["stmt_spans"]
    masked = struct["masked"]
    if not types:
        if log_cb:
            log_cb(f"[{log_time()}] [warn] Injection skipped: no class found in code")
        return java_code

    # host type = first Activity, else first type
    host = None
    for t in types:
        header = java_code[t["decl_start"]:t["body_open"]]
        if _RE_EXTENDS_ACTIVITY.search(header):
            host = t
            break
    if host is None:
        host = types[0]
    host_cls = host["name"]

    def in_stmt_span(pos: int) -> bool:
        """True if pos lies inside any statement (method-body) span."""
        return any(o <= pos < c for (o, c) in stmt_spans)

    def enclosing_type(pos: int):
        """Innermost type whose body contains pos (falls back to host)."""
        for t in types:
            if t["body_open"] <= pos < t["end"]:
                return t
        return host

    injections: List[Tuple[int, str]] = []   # (position, code)

    has_sounds = any(e.sound_path for e in valid_elements)
    if has_sounds:
        injections.append((host["body_open"] + 1,
                           "\n    private android.media.MediaPlayer mediaPlayer;\n"))

    for element in valid_elements:
        name = re.escape(element.name)
        etype = re.escape(element.type)
        # v3.5: declaration patterns tolerate GENERIC types —
        # ``ArrayAdapter<String> view = new ArrayAdapter<String>(…)`` and
        # ``RecyclerView.Adapter<VH> a = …`` never matched before, so their
        # motion silently fell back to onCreate (or was skipped).
        patterns = [
            rf'\b{etype}(?:\s*<[^;=]*?>+)?\s+{name}\s*=[^;]*;',
            rf'(?<![\w.]){name}\s*=\s*[^;]*findViewById[^;]*;',
            rf'(?<![\w.]){name}\s*=\s*new\s+{etype}(?:\s*<[^;(]*?>+)?\s*\([^;]*;',
        ]
        best = None
        for pat in patterns:
            for m in re.finditer(pat, masked):
                if in_stmt_span(m.start()):
                    best = m          # keep the LAST statement-context match

        if best is not None:
            cls = enclosing_type(best.start())["name"]
            code = _element_code(element, cls, resource_manager)
            line_start = java_code.rfind("\n", 0, best.start()) + 1
            indent = _RE_LEADING_WS.match(java_code[line_start:]).group(0)
            injections.append((best.end(), "\n" + _indent_block(code, indent)))
            if log_cb:
                log_cb(f"[{log_time()}] [ok] Injected motion for {element.name} ({cls})")
        else:
            # field declaration fallback → inject at end of onCreate (in scope)
            is_field = False
            for m in re.finditer(rf'\b{etype}\s+{name}\s*[;=]', masked):
                if not in_stmt_span(m.start()):
                    is_field = True
                    break
            oncreate_span = _find_oncreate_span(java_code, masked, stmt_spans, host)
            if is_field and oncreate_span:
                code = _element_code(element, host_cls, resource_manager)
                injections.append((oncreate_span[1] - 1,
                                   "\n" + _indent_block(code, "        ") + "\n"))
                if log_cb:
                    log_cb(f"[{log_time()}] [ok] Injected motion for field "
                           f"{element.name} (onCreate)")
            elif log_cb:
                log_cb(f"[{log_time()}] [warn] No safe injection point for "
                       f"'{element.name}' — skipped (declare or assign it "
                       f"inside a method)")

    if has_sounds and not re.search(r'\bonDestroy\s*\(', masked[host["body_open"]:host["end"]]):
        ondestroy = (
            "\n    @Override\n"
            "    protected void onDestroy() {\n"
            "        super.onDestroy();\n"
            "        if (mediaPlayer != null) {\n"
            "            mediaPlayer.release();\n"
            "            mediaPlayer = null;\n"
            "        }\n"
            "    }\n"
        )
        injections.append((host["end"] - 1, ondestroy))

    # apply injections from the END of the file backwards so earlier
    # positions stay valid
    for pos, code in sorted(injections, key=lambda p: -p[0]):
        java_code = java_code[:pos] + code + java_code[pos:]

    return java_code


# onCreate locator for the field-declaration fallback injection.
_RE_ONCREATE = re.compile(r'\bonCreate\s*\(')


def _find_oncreate_span(java_code: str, masked: str,
                        stmt_spans: List[Tuple[int, int]], host: dict):
    """Locate the onCreate() method body span inside the host type."""
    region = masked[host["body_open"]:host["end"]]
    base = host["body_open"]
    m = _RE_ONCREATE.search(region)
    if not m:
        return None
    brace = masked.find("{", base + m.end())
    if brace == -1:
        return None
    for o, c in stmt_spans:
        if o == brace:
            return (o, c)
    return None


# ---------------------------------------------------------------------------
# TOOLCHAIN DISCOVERY & SUBPROCESS HELPERS
# ---------------------------------------------------------------------------

def find_in_path(executable_names, env_path=None):
    """Find an executable on PATH. Accepts a name or a list of candidate names."""
    if isinstance(executable_names, str):
        executable_names = [executable_names]
    paths = (env_path if env_path is not None else os.environ.get("PATH", "")).split(os.pathsep)
    for p in paths:
        if not p:
            continue
        for name in executable_names:
            exe = Path(p) / name
            if exe.exists():
                return str(exe)
    return None


def search_for_file(root_dir, names):
    """Recursively search for any of names under root_dir, return first found."""
    for base, dirs, files in os.walk(root_dir):
        # prune obviously irrelevant heavy dirs
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for n in names:
            if n in files:
                return os.path.join(base, n)
    return None


# --- build-tools detection & extraction ---
def _has_required_build_tools(out_dir):
    """Check if a build-tools directory has the main tools we need.

    v3.8 hardening: the tool names are platform-aware. A build-tools
    folder extracted from ANOTHER platform's archive (linux binaries under
    Windows, …) used to pass this check — its binaries could never run
    here, so the build failed later with cryptic errors. The right
    platform's names are required now."""
    if IS_WINDOWS:
        packager = ["aapt.exe", "aapt2.exe"]
        d8_names = ["d8.bat", "d8.cmd"]
        zipalign_names = ["zipalign.exe"]
        apksigner_names = ["apksigner.bat", "apksigner.cmd"]
    else:                               # linux & macos ship extensionless
        packager = ["aapt", "aapt2"]
        d8_names = ["d8"]
        zipalign_names = ["zipalign"]
        apksigner_names = ["apksigner"]
    aapt = search_for_file(out_dir, packager)
    d8 = search_for_file(out_dir, d8_names)
    zipalign = search_for_file(out_dir, zipalign_names)
    apksigner = search_for_file(out_dir, apksigner_names)
    return bool((aapt) and d8 and zipalign and apksigner)


def _ensure_build_tools_in(base_dir, log_cb=None):
    """Return a usable build-tools dir under base_dir, or None (dir first, zip second)."""
    out_dir = os.path.join(base_dir, BUILD_TOOLS_LOCAL_DIR)

    # 1) Prefer an already-present build-tools directory — the pinned
    #    revision, read from the archive's own source.properties (v3.8)
    if os.path.isdir(out_dir):
        ok, rev = build_tools_pin_status(out_dir)
        if ok:
            if log_cb:
                log_cb(f"[{log_time()}] Build-tools {rev} ready: {out_dir}")
            return out_dir
        if log_cb:
            if _has_required_build_tools(out_dir):
                log_cb(f"[{log_time()}] [warn] Build-tools at {out_dir} are "
                       f"{rev or 'unversioned'} — {REQUIRED_BUILD_TOOLS} is required")
            elif rev:
                log_cb(f"[{log_time()}] [warn] Build-tools at {out_dir} ({rev}) lack "
                       f"the required tools — {REQUIRED_BUILD_TOOLS} needed")

    # 2) Fall back to the zip (extracting happens OFF the UI thread)
    zip_path = os.path.join(base_dir, BUILD_TOOLS_ZIP_NAME)
    if not os.path.exists(zip_path):
        if log_cb:
            log_cb(
                f"[{log_time()}] Build-tools not found. Expected one of:\n"
                f"  • directory: {out_dir}\n"
                f"  • zip archive: {zip_path}")
        return None

    if log_cb:
        log_cb(f"[{log_time()}] Extracting build-tools from {Path(zip_path).name} …")
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)
    if log_cb:
        log_cb(f"[{log_time()}] Extracted to {out_dir}")
    ok, rev = build_tools_pin_status(out_dir)
    if not ok and log_cb:
        log_cb(f"[{log_time()}] [warn] Extracted build-tools are {rev or 'unversioned'} "
               f"— {REQUIRED_BUILD_TOOLS} is required (the Data installer "
               "fetches the right one)")
    return out_dir if ok else None


def ensure_build_tools_extracted(base_dir, log_cb=None):
    """Locate build-tools beside the script or in ./Data, extracting the zip if needed."""
    # v3.6: beside the script AND inside the Data folder (where the one-click
    # installer puts build-tools). The classic location wins when both exist.
    for base in (base_dir, os.path.join(base_dir, "Data")):
        result = _ensure_build_tools_in(base, log_cb)
        if result:
            return result
    return None


def _probe_direct(dirs, names):
    """Look for a file directly inside each of `dirs` (no recursion)."""
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for name in names:
            cand = Path(d) / name
            if cand.exists():
                return str(cand)
    return None


def locate_build_tools(extracted_dir, log_cb=None):
    """Locate the individual build tools FAST: direct probes first (the
    standard build-tools layout), a bounded one-level scan second, full walk
    last."""
    if not extracted_dir:
        return {}
    root = Path(extracted_dir)
    top_dirs = [str(root)] + [str(p) for p in root.iterdir() if p.is_dir()] \
        if root.is_dir() else []

    aapt = _probe_direct(top_dirs, ["aapt.exe", "aapt"])
    aapt2 = _probe_direct(top_dirs, ["aapt2.exe", "aapt2"])
    d8 = _probe_direct(top_dirs, ["d8.bat", "d8.cmd", "d8"])
    d8_jar = _probe_direct(top_dirs + [str(root / "lib")], ["d8.jar"])
    zipalign = _probe_direct(top_dirs, ["zipalign.exe", "zipalign"])
    apksigner_bat = _probe_direct(top_dirs, ["apksigner.bat", "apksigner"])
    apksigner_jar = _probe_direct([str(root / "lib")], ["apksigner.jar"])

    # fallback: bounded recursive search for anything still missing
    if not (aapt or aapt2):
        aapt = search_for_file(str(root), ["aapt.exe", "aapt"])
    if not aapt2:
        aapt2 = search_for_file(str(root), ["aapt2.exe", "aapt2"])
    if not d8:
        d8 = search_for_file(str(root), ["d8.bat", "d8.cmd", "d8"])
    if not d8_jar:
        d8_jar = search_for_file(str(root), ["d8.jar"])
    if not zipalign:
        zipalign = search_for_file(str(root), ["zipalign.exe", "zipalign"])
    if not apksigner_bat:
        apksigner_bat = search_for_file(str(root), ["apksigner.bat", "apksigner"])
    if not apksigner_jar:
        apksigner_jar = search_for_file(str(root), ["apksigner.jar"])

    lib_dir = None
    if d8:
        cand = Path(d8).parent / "lib"
        if cand.is_dir():
            lib_dir = str(cand)
    if not lib_dir and d8_jar:
        lib_dir = str(Path(d8_jar).parent)

    if log_cb:
        log_cb(f"[{log_time()}] Tools located — aapt: {bool(aapt)}, aapt2: {bool(aapt2)}, "
               f"d8: {bool(d8 or lib_dir)}, zipalign: {bool(zipalign)}, "
               f"apksigner: {bool(apksigner_bat or apksigner_jar)}")

    return {
        "aapt": aapt,
        "aapt2": aapt2,
        "d8": d8,
        "d8_lib_dir": lib_dir,
        "zipalign": zipalign,
        "apksigner_bat": apksigner_bat,
        "apksigner_jar": apksigner_jar,
        "root": extracted_dir,
    }


# --- android.jar discovery ---
def auto_find_android_jar(script_dir=None, log_cb=None):
    """AUTOMATION: look for android.jar in a folder named 'androidjar'.

    Search order: the caller's script dir (what the env scan passes) →
    EXE dir (frozen) → this file's dir → cwd, each with its classic
    ./androidjar home first, then its ./Data/androidjar home — every
    discovery surface looks beside the SAME script, never somewhere the
    system decides.

    v3.8: only the pinned API 33 is accepted — a jar of any other API level
    is named in the log and passed over, never silently used.
    """
    base_dirs: List[Path] = []
    if script_dir:
        base_dirs.append(Path(script_dir))
    if getattr(sys, "frozen", False):
        try:
            base_dirs.append(Path(sys.executable).parent)
        except Exception:
            pass
    try:
        base_dirs.append(Path(__file__).parent)
    except Exception:
        pass
    base_dirs.append(Path.cwd())

    seen = set()
    for base in base_dirs:
        s = str(base)
        if s in seen:
            continue
        seen.add(s)
        # v3.6: the Data installer drops android.jar into ./Data/androidjar/;
        #       the classic ./androidjar/ beside the script still wins first
        for cand in (base / "androidjar" / ANDROID_JAR_NAME,
                     base / "Data" / "androidjar" / ANDROID_JAR_NAME):
            if not cand.exists():
                continue
            if android_jar_pin_ok(cand):
                return str(cand)
            if log_cb:
                try:
                    log_cb(f"[{log_time()}] [warn] {cand} is "
                           f"{android_jar_api_label(android_jar_api_range(cand))} "
                           f"— API {REQUIRED_ANDROID_API} is required, skipping it")
                except Exception:
                    pass
    return None


# v3.7 AUTO PATHS — where every item lives inside the portable Data folder.
# Powers the AUTO buttons in Settings → Advanced and the self-writing path
# fields after a Data install: one resolver, one source of truth.
def data_path_for(kind: str) -> Optional[str]:
    """Resolve an item's home inside the portable Data folder (v3.7).

    Returns the absolute path (creating the folder for output/keystore when
    the Data folder exists), or None when the Data folder — or the item —
    isn't there yet. Never raises.
    """
    try:
        if not DATA_DIR.is_dir():
            return None

        if kind == "androidjar":
            jar = DATA_DIR / "androidjar" / ANDROID_JAR_NAME
            # v3.8: the pinned API level, read from the jar's own framework
            # classes — the file name alone never qualifies it
            return str(jar) if (jar.exists() and android_jar_pin_ok(jar)) else None

        if kind == "jdk":
            # v3.8: ONLY the pinned JDK 17 resolves — a wrong-version JDK
            # inside Data stays invisible to AUTO (it is named by
            # data_jdk_mismatches() instead of being silently pointed at).
            javac = "javac.exe" if IS_WINDOWS else "javac"
            for c in sorted(DATA_DIR.glob("jdk*")):
                if not (c / "bin" / javac).exists():
                    continue
                if probe_java_level(c / "bin" / javac) == REQUIRED_JDK_MAJOR:
                    return str(c / "bin")
            return None

        if kind == "buildtools":
            # v3.8: the pinned revision, decided by the folder's own
            # source.properties — the folder name alone never qualifies it
            bt = DATA_DIR / BUILD_TOOLS_LOCAL_DIR
            ok, _rev = build_tools_pin_status(bt)
            return str(bt) if ok else None

        if kind == "dist":
            dist = DATA_DIR / "dist"
            dist.mkdir(parents=True, exist_ok=True)
            return str(dist)

        if kind == "keystore":
            for cand in (DATA_DIR / "dist" / "debug.keystore",
                         DATA_DIR / "keystore" / "debug.keystore"):
                if cand.exists():
                    return str(cand)
            ks_dir = DATA_DIR / "keystore"     # generated on the first build
            ks_dir.mkdir(parents=True, exist_ok=True)
            return str(ks_dir / "debug.keystore")

        if kind == "manifest":
            m = DATA_DIR / "AndroidManifest.xml"
            return str(m) if m.exists() else None
    except Exception:
        return None
    return None


# v3.8.1 AUTO-ON-STARTUP — a small JSON file inside the Data folder remembers
# whether the AUTO pass for ALL paths has already run on this machine, plus
# what it resolved and which Data items were installed (and when).
#
#   Data/autopaths.json
#     {"schema": 1,
#      "first_run_done": true,          <- absent/false → first launch → AUTO all
#      "first_run_at": "...",
#      "last_auto_at": "...", "last_auto_reason": "...",
#      "paths":     {"jdk": "...", "buildtools": "...", "androidjar": "...", ...},
#      "installed": {"jdk": {"path": "...", "at": "..."}, ...}}
#
# Delete the file and the next launch behaves like the very first one again.
AUTOPATHS_JSON = DATA_DIR / "autopaths.json"
AUTOPATH_KINDS = ("androidjar", "jdk", "buildtools", "dist", "keystore", "manifest")
AUTOPATH_TOOLCHAIN_KINDS = ("androidjar", "jdk", "buildtools")


def load_autopaths_state() -> dict:
    """Read Data/autopaths.json — {} when missing or unreadable. Never raises."""
    try:
        if AUTOPATHS_JSON.is_file():
            d = json.loads(AUTOPATHS_JSON.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d
    except Exception:
        pass
    return {}


def save_autopaths_state(state: dict) -> bool:
    """Atomically write Data/autopaths.json (creates ./Data). Never raises."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = AUTOPATHS_JSON.with_name(AUTOPATHS_JSON.name + ".tmp")
        state["schema"] = 1
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        os.replace(tmp, AUTOPATHS_JSON)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# v3.6 DATA INSTALLER — one-click downloads into the portable Data folder
# ---------------------------------------------------------------------------
# A missing library or tool is no longer a dead end: the engine below can
# download and install every dependency into ./Data beside this script.
#   • zip items  (JDK, build-tools, android.jar) come from Adoptium / Google
#     and are extracted into their final Data sub-folder via a staging dir.
#   • pip items  (PyQt6, Pillow, QtMultimedia) are installed with
#     `pip install --target Data/python` — never touching site-packages.
# The GUI wraps this in InstallerThread + InstallDialog (beautiful progress,
# per-item statuses, cancel); the console bootstrap uses it before Qt exists.
#
# v3.6.1 — THE MIRROR CHAIN. Some networks block or hijack dl.google.com
# (and individual vendor CDNs), which used to kill an install with a bare
# "HTTP Error 404". Every zip item therefore carries a LIST of independent
# sources and the installer walks them in order until one delivers a real
# archive: Google's official repository → a byte-identical mirror → a live
# lookup in Google's own package index (self-heals renames) → (for the JDK)
# completely different vendors: Microsoft OpenJDK, Amazon Corretto, GitHub
# releases, or the Tsinghua University Adoptium mirror.
#
# v3.8 — SSL RESILIENCE (the UNEXPECTED_EOF killer). Networks that
# intercept TLS (captive portals, DPI boxes, antivirus MITM) used to kill
# every download with "SSL: UNEXPECTED_EOF_WHILE_READING" — every source,
# same error. Every request therefore walks a CHAIN OF TRANSPORTS until one
# gets through, and the first that works is remembered for the session:
#   1. urllib — the platform's default SSL
#   2. urllib — TLS 1.2 pinned (middleboxes that break TLS 1.3)
#   3. urllib — relaxed certificate checks (proxies that re-sign traffic)
#   4. curl — the OS's own schannel stack on Windows (immune to
#      OpenSSL-hooking antivirus); used on other platforms when present
#   5. PowerShell Invoke-WebRequest (Windows) — schannel again, through a
#      completely different HTTP client
# A server's answer (HTTP 404/403…) is never retried with another stack:
# that error means the SOURCE is gone, and the mirror chain moves on.

DATA_INSTALLER_UA = "ApkForge-Data-Installer/3.8.0 (+python)"
GOOGLE_REPO_BASE = "https://dl.google.com/android/repository/"
# Tencent mirrors dl.google.com/android/repository/ file-for-file.
TENCENT_REPO_BASE = "https://mirrors.cloud.tencent.com/AndroidSDK/"
ANDROID_REPO_XMLS = ("repository2-3.xml", "repository2-2.xml", "repository2-1.xml")
GITHUB_TEMURIN_API = ("https://api.github.com/repos/adoptium/"
                      "temurin17-binaries/releases/latest")
# v3.8 — Tsinghua University's Adoptium mirror: byte-identical archives,
# often the one host that still answers where Western CDNs are blocked.
TSINGHUA_ADOPTIUM_BASE = "https://mirrors.tuna.tsinghua.edu.cn/Adoptium/"

# v3.8 transport chain state
_DATA_SSL_MODES: Tuple[str, ...] = ("default", "tls12", "relaxed")
_DATA_TRANSPORTS: Tuple[str, ...] = ("default", "tls12", "relaxed",
                                     "curl", "powershell")
_DATA_TRANSPORT_WINNER: Optional[str] = None    # first transport that got through


# --- the transport chain ---
class _HttpAnswerError(RuntimeError):
    """The server ANSWERED with an HTTP error (404, 403…) — not a
    transport failure. Retrying another stack is pointless; the mirror
    chain moves to the next source instead."""


def _ssl_context_for(mode: Optional[str]):
    """SSLContext for one urllib attempt. None = the platform default."""
    import ssl

    if mode == "tls12":
        ctx = ssl.create_default_context()
        try:
            ctx.maximum_version = ssl.TLSVersion.TLSv1_2   # TLS 1.3 breakers
        except Exception:
            pass                    # exotic/old OpenSSL: keep the default
        return ctx
    if mode == "relaxed":
        ctx = ssl.create_default_context()
        ctx.check_hostname = False          # proxies that re-sign traffic
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return None


def _transport_order(python_only: bool = False) -> List[str]:
    """Transports to try, the remembered winner first. `python_only` keeps
    small metadata GETs (package index, release listings) on urllib — if
    even those fail, the plain mirror URLs still carry the download."""
    base = list(_DATA_SSL_MODES) if python_only else list(_DATA_TRANSPORTS)
    if not IS_WINDOWS:
        base = [t for t in base if t != "powershell"]
    if _DATA_TRANSPORT_WINNER and _DATA_TRANSPORT_WINNER in base:
        base = ([_DATA_TRANSPORT_WINNER]
                + [t for t in base if t != _DATA_TRANSPORT_WINNER])
    return base


def _remember_transport(mode: Optional[str]):
    """Remember the first transport that delivered — every later request
    in this session tries it before walking the chain again."""
    global _DATA_TRANSPORT_WINNER
    if mode and not _DATA_TRANSPORT_WINNER:
        _DATA_TRANSPORT_WINNER = mode


def _is_transport_error(exc: BaseException) -> bool:
    """True when the failure is at the TLS/transport layer — worth another
    transport. An HTTP status answer is the SERVER talking; the mirror
    chain handles that, not the SSL chain."""
    return not isinstance(exc, _HttpAnswerError)


# --- platform tags & size formatting ---
def _data_platform_tags() -> Tuple[str, str, str]:
    """(adoptium_os, adoptium_arch, google_build_tools_suffix) for this machine."""
    machine = (os.environ.get("PROCESSOR_ARCHITEW6432")
               or platform.machine() or "").lower()
    arch = "aarch64" if any(a in machine for a in ("arm64", "aarch64")) else "x64"
    if IS_WINDOWS:
        return "windows", arch, "windows"
    if sys.platform == "darwin":
        return "mac", arch, "macosx"
    return "linux", arch, "linux"


def _vendor_tags() -> Dict[str, str]:
    """v3.6.1 — per-vendor platform tokens for the mirror chain.

    Vendors spell the same machine slightly differently (macOS is 'mac' for
    Adoptium/GitHub but 'macos' for Microsoft/Corretto; Windows archives
    are .zip, everything else .tar.gz). One helper keeps every URL builder
    honest.
    """
    machine = (os.environ.get("PROCESSOR_ARCHITEW6432")
               or platform.machine() or "").lower()
    arch = "aarch64" if any(a in machine for a in ("arm64", "aarch64")) else "x64"
    if IS_WINDOWS:
        return {"arch": arch, "adoptium_os": "windows", "ms_os": "windows",
                "corretto_os": "windows", "github_os": "windows", "ext": "zip"}
    if sys.platform == "darwin":
        return {"arch": arch, "adoptium_os": "mac", "ms_os": "macos",
                "corretto_os": "macos", "github_os": "mac", "ext": "tar.gz"}
    return {"arch": arch, "adoptium_os": "linux", "ms_os": "linux",
            "corretto_os": "linux", "github_os": "linux", "ext": "tar.gz"}


def _human_bytes(n: float) -> str:
    """1234567 → '1.2 MB' (installer-friendly, one decimal)."""
    try:
        n = float(n)
    except Exception:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.1f} GB"


# --- metadata fetch & live URL resolvers ---
def _fetch_url_bytes(url: str, timeout: int = 25, limit: int = 8 << 20) -> bytes:
    """GET a small file (package index, release metadata) into memory —
    walking the SSL-mode chain (v3.8) so TLS interception can't kill the
    lookups that feed the mirror chain."""
    import urllib.request
    last: Optional[Exception] = None
    for mode in _transport_order(python_only=True):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": DATA_INSTALLER_UA,
                "Accept": "application/octet-stream, application/json, */*"})
            with urllib.request.urlopen(
                    req, timeout=timeout,
                    context=_ssl_context_for(mode)) as resp:
                data = resp.read(limit)
            _remember_transport(mode)
            return data
        except Exception as e:
            import urllib.error
            if isinstance(e, urllib.error.HTTPError):
                raise                      # the server answered — not ours to fix
            last = e
    raise (last if last is not None
           else RuntimeError(f"GET failed: {url}"))


_RE_URL_TAG = re.compile(r"<url>([^<]+)</url>")


def _resolve_android_repo_url(package_path: str, plat_suffix: str,
                              log_cb=None) -> Optional[str]:
    """v3.6.1 — resolve an SDK package's archive URL from Google's package
    index (repository2-*.xml), falling back to the index's Tencent mirror.

    The index — not a hardcoded filename — is the source of truth, so this
    self-heals whenever Google renames or re-revisions an archive. Returns
    None when every index is unreachable; the mirror chain then moves on.
    """
    for base in (GOOGLE_REPO_BASE, TENCENT_REPO_BASE):
        for xml_name in ANDROID_REPO_XMLS:
            try:
                xml = _fetch_url_bytes(base + xml_name).decode(
                    "utf-8", "replace")
            except Exception as e:
                if log_cb:
                    log_cb(f"[warn] package index {base}{xml_name}: {e}")
                continue
            m = re.search(
                r'<remotePackage path="%s"[^>]*>(.*?)</remotePackage>'
                % re.escape(package_path), xml, re.S)
            if not m:
                continue
            urls = _RE_URL_TAG.findall(m.group(1))
            if not urls:
                continue
            # multi-platform packages carry one archive per OS — take ours
            mine = [u for u in urls if u.endswith(f"-{plat_suffix}.zip")]
            chosen = mine[0] if mine else urls[0]
            if log_cb:
                log_cb(f"[ok] {package_path} → {chosen} (from {xml_name})")
            return base + chosen
    return None


def _resolve_github_temurin_url(log_cb=None) -> Optional[str]:
    """v3.6.1 — the newest Temurin 17 JDK asset, resolved live from GitHub
    releases. GitHub is reachable on many networks where vendor CDNs are
    blocked, which makes it the JDK chain's last (and most resilient) link.
    """
    try:
        data = json.loads(_fetch_url_bytes(GITHUB_TEMURIN_API).decode(
            "utf-8", "replace"))
    except Exception as e:
        if log_cb:
            log_cb(f"[warn] GitHub release lookup: {e}")
        return None
    t = _vendor_tags()
    prefix = f"OpenJDK17U-jdk_{t['arch']}_{t['github_os']}_hotspot_"
    suffix = ".zip" if t["ext"] == "zip" else ".tar.gz"
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.startswith(prefix) and name.endswith(suffix):
            url = asset.get("browser_download_url", "")
            if log_cb:
                log_cb(f"[ok] Temurin 17 asset on GitHub → {name}")
            return url or None
    return None


_RE_HOTSPOT_VERSION = re.compile(r"hotspot_([\d.]+)_(\d+)\.(?:zip|tar\.gz)$")


def _resolve_tsinghua_temurin_url(log_cb=None) -> Optional[str]:
    """v3.8 — JDK 17 from Tsinghua University's Adoptium mirror: archives
    byte-identical to Adoptium's own, resolved live from the mirror's
    directory listing. On many networks where Western CDNs are blocked or
    throttled, this is the one host that still answers at full speed.
    """
    t = _vendor_tags()
    listing = f"{TSINGHUA_ADOPTIUM_BASE}17/jdk/{t['arch']}/{t['adoptium_os']}/"
    try:
        html = _fetch_url_bytes(listing).decode("utf-8", "replace")
    except Exception as e:
        if log_cb:
            log_cb(f"[warn] Tsinghua mirror listing: {e}")
        return None
    prefix = f"OpenJDK17U-jdk_{t['arch']}_{t['github_os']}_hotspot_"
    suffix = ".zip" if t["ext"] == "zip" else ".tar.gz"
    best_key, best_name = None, None
    for name in set(re.findall(r'href="([^"<>=?]+)"', html)):
        if not (name.startswith(prefix) and name.endswith(suffix)):
            continue
        # OpenJDK17U-jdk_x64_windows_hotspot_17.0.21_9.zip → (17, 0, 21, 9);
        # 17.0.20.1_1 → (17, 0, 20, 1, 1) — tuples compare correctly even
        # across different part counts.
        m = _RE_HOTSPOT_VERSION.search(name)
        if not m:
            continue
        key = tuple(int(x) for x in m.group(1).split(".")) + (int(m.group(2)),)
        if best_key is None or key > best_key:
            best_key, best_name = key, name
    if best_name:
        if log_cb:
            log_cb(f"[ok] Tsinghua Adoptium mirror → {best_name}")
        return listing + best_name
    return None


# --- download chains & installable items ---
def _item_download_sources(item: Dict) -> List:
    """Flatten an item's download chain into [str | callable, …].

    Understands both the v3.6 single `url` field and the v3.6.1 `urls`
    chain (a list, or a zero-argument callable returning one — used for
    platform-dependent URLs). Callables stay lazy: they are resolved at
    attempt time, so a package-index lookup only ever runs when the plain
    mirror URLs before it have failed.
    """
    raw = item["urls"] if "urls" in item else item.get("url")
    if raw is None:
        return []
    if callable(raw):
        try:
            raw = raw()
        except Exception:
            return []
    if isinstance(raw, str):
        return [raw]
    if not isinstance(raw, (list, tuple)):
        return []
    return [s for s in raw if s]


# Every installable item, in canonical display order. `kind` decides how the
# item is fetched: "zip" streams + extracts an archive, "pip" shells out to
# `pip install --target Data/python`.
#
# v3.6.1 — `urls` (replacing the single `url`) is a chain of independent
# download sources: plain strings, or zero-argument callables that resolve
# lazily at attempt time (package-index / GitHub lookups). The installer
# tries them in order until one delivers a real archive.


def _jdk_urls():
    """JDK 17 from five independent sources — any one of them is enough."""
    t = _vendor_tags()
    return [
        # 1) Eclipse Temurin 17 GA — Adoptium's "latest" binary API
        f"https://api.adoptium.net/v3/binary/latest/17/ga/"
        f"{t['adoptium_os']}/{t['arch']}/jdk/hotspot/normal/eclipse",
        # 2) Microsoft Build of OpenJDK 17 — stable "latest" aka.ms links
        #    (and the only vendor with a Windows ARM64 zip)
        f"https://aka.ms/download-jdk/microsoft-jdk-17-"
        f"{t['ms_os']}-{t['arch']}.{t['ext']}",
        # 3) Amazon Corretto 17 — stable "latest" download links
        f"https://corretto.aws/downloads/latest/amazon-corretto-17-"
        f"{t['arch']}-{t['corretto_os']}-jdk.{t['ext']}",
        # 4) the newest Temurin 17 asset, resolved live from GitHub releases
        lambda: _resolve_github_temurin_url(),
        # 5) Tsinghua University's byte-identical Adoptium mirror, resolved
        #    live from its directory listing — on many networks where
        #    Western CDNs are blocked, it is the one host that still answers
        lambda: _resolve_tsinghua_temurin_url(),
    ]


def _build_tools_urls():
    """Android build-tools 33.0.3 — three sources, two vendors, one index.

    v3.8: every source is the EXACT pinned revision — a "compatible"
    33.0.2 is no longer an acceptable substitute (the pin is verified from
    the archive's own source.properties after extraction).
    """
    plat = _data_platform_tags()[2]
    return [
        # 1) Google's official repository (name verified against Google's own
        #    package index: build-tools_r33.0.3-<plat>.zip)
        f"{GOOGLE_REPO_BASE}build-tools_r33.0.3-{plat}.zip",
        # 2) Tencent's byte-identical mirror of the very same repository
        f"{TENCENT_REPO_BASE}build-tools_r33.0.3-{plat}.zip",
        # 3) self-healing: the exact archive name looked up LIVE in Google's
        #    package index (itself fetched from Google or its Tencent mirror)
        #    — survives any future rename on either side
        lambda: _resolve_android_repo_url("build-tools;33.0.3", plat),
    ]


def _android_jar_urls():
    """android.jar (API 33) — seven sources across three revisions."""
    return [
        # 1-2) the classic API 33 platform zip — Google, then the mirror
        f"{GOOGLE_REPO_BASE}platform-33_r02.zip",
        f"{TENCENT_REPO_BASE}platform-33_r02.zip",
        # 3) whatever revision Google's package index lists for android-33
        #    right now (kept current even when revisions are replaced)
        lambda: _resolve_android_repo_url("platforms;android-33", "linux"),
        # 4-5) the newer ext5 revision of the same platform
        f"{GOOGLE_REPO_BASE}platform-33-ext5_r01.zip",
        f"{TENCENT_REPO_BASE}platform-33-ext5_r01.zip",
        # 6-7) the original r01 revision
        f"{GOOGLE_REPO_BASE}platform-33_r01.zip",
        f"{TENCENT_REPO_BASE}platform-33_r01.zip",
    ]


INSTALL_ITEMS: Dict[str, Dict] = {
    "jdk": {
        "label": "JDK 17",
        "short": "JDK",
        "desc": "Java compiler & runtime — the pinned JDK 17, from five "
                "independent sources (Temurin, Microsoft, Corretto, GitHub, "
                "Tsinghua).",
        "size": "≈ 190 MB",
        "kind": "zip",
        "urls": _jdk_urls,
        "zip_name": "jdk-17-temurin.zip",
    },
    "buildtools": {
        "label": "Android build-tools 33.0.3",
        "short": "build-tools",
        "desc": "aapt2 · d8 · zipalign · apksigner — packaging & signing.",
        "size": "≈ 55 MB",
        "kind": "zip",
        "urls": _build_tools_urls,
        "zip_name": "build-tools_r33.0.3.zip",
    },
    "androidjar": {
        "label": "android.jar (API 33)",
        "short": "android.jar",
        "desc": "The Android platform library your Java compiles against.",
        "size": "≈ 65 MB",
        "kind": "zip",
        "urls": _android_jar_urls,
        "zip_name": "platform-33.zip",
    },
    "pillow": {
        "label": "Pillow",
        "short": "Pillow",
        "desc": "Icon resizing & image thumbnails (optional).",
        "size": "≈ 5 MB",
        "kind": "pip",
        "packages": ["Pillow"],
        "reload": "PIL",
    },
    "qtmultimedia": {
        "label": "QtMultimedia",
        "short": "QtMultimedia",
        "desc": "In-tool sound preview (optional). Needs a restart after install.",
        "size": "≈ 70 MB",
        "kind": "pip",
        "packages": ["PyQt6", "PyQt6-Addons"],
        "restart": True,
    },
}

INSTALL_ORDER = ["jdk", "buildtools", "androidjar", "pillow", "qtmultimedia"]


# --- cancellation ---
class _CancelRequested(Exception):
    """Raised by the installer loops when the user hits Stop."""


def _data_cancel_guard(cancel_check):
    """Throw _CancelRequested when the caller asked to stop."""
    if cancel_check is not None and cancel_check():
        raise _CancelRequested()


# --- download transports ---
def _urllib_stream(url: str, part: Path, mode: Optional[str],
                   progress_cb=None, cancel_check=None) -> None:
    """One urllib download attempt under a specific SSL mode.

    An HTTP status answer (404, 403…) is re-raised as _HttpAnswerError:
    the server DID talk, so retrying with another transport is pointless —
    the mirror chain moves to the next source instead."""
    import urllib.error
    import urllib.request
    req = urllib.request.Request(url, headers={
        "User-Agent": DATA_INSTALLER_UA})
    try:
        opener = urllib.request.urlopen(req, timeout=60,
                                        context=_ssl_context_for(mode))
    except urllib.error.HTTPError as e:
        raise _HttpAnswerError(str(e)) from None
    with opener as resp, open(part, "wb") as fh:
        total_raw = resp.headers.get("Content-Length")
        total = int(total_raw) if total_raw and total_raw.isdigit() else -1
        done = 0
        chunk = 1 << 16                      # 64 KB
        started = datetime.now()
        while True:
            _data_cancel_guard(cancel_check)
            block = resp.read(chunk)
            if not block:
                break
            fh.write(block)
            done += len(block)
            elapsed = max(0.001, (datetime.now() - started).total_seconds())
            speed = done / elapsed
            if total > 0:
                pct = int(done * 100 / total)
                detail = f"{_human_bytes(done)} / {_human_bytes(total)} · {_human_bytes(speed)}/s"
            else:
                pct, detail = -1, f"{_human_bytes(done)} · {_human_bytes(speed)}/s"
            if progress_cb:
                try:
                    progress_cb(pct, detail)
                except Exception:
                    pass


def _proc_download(cmd: List[str], part: Path, progress_cb=None,
                   cancel_check=None, tail: str = "") -> None:
    """Run an external download process (curl / PowerShell), reporting the
    growing file as indeterminate progress and honouring cancel."""
    import time as _time
    creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
        creationflags=creationflags)
    try:
        while proc.poll() is None:
            _data_cancel_guard(cancel_check)
            try:
                done = part.stat().st_size if part.exists() else 0
            except OSError:
                done = 0
            if progress_cb:
                try:
                    progress_cb(-1, f"{_human_bytes(done)}{tail}")
                except Exception:
                    pass
            _time.sleep(0.3)
        try:
            err = (proc.stderr.read() or "") if proc.stderr else ""
        except Exception:
            err = ""
        rc = proc.returncode
    except _CancelRequested:
        try:
            proc.kill()
            proc.wait()
        except Exception:
            pass
        raise
    finally:
        for stream in (proc.stdout, proc.stderr):
            try:
                if stream:
                    stream.close()
            except Exception:
                pass
    if rc != 0:
        tail_err = err.strip().splitlines()[-1][:300] if err.strip() \
            else f"exit code {rc}"
        if rc == 22:
            # curl --fail: the server answered with an HTTP error status —
            # a source problem, not a transport problem.
            raise _HttpAnswerError(tail_err)
        raise RuntimeError(tail_err)


def _curl_stream(url: str, part: Path, progress_cb=None,
                 cancel_check=None) -> None:
    """curl — on Windows it ships with the OS (10 1803+) and uses the OS's
    own schannel TLS stack, which is immune to the OpenSSL-hooking
    antivirus/proxy software that kills python.exe's downloads with
    UNEXPECTED_EOF. On Linux/macOS it is used when present too: a different
    HTTP client often survives what urllib's stack cannot."""
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("curl is not available on this machine")
    cmd = [curl, "-L", "--fail", "--silent", "--show-error",
           "--connect-timeout", "30", "--retry", "1",
           "-A", DATA_INSTALLER_UA, "-o", str(part), url]
    _proc_download(cmd, part, progress_cb, cancel_check, tail=" · curl")


def _powershell_stream(url: str, part: Path, progress_cb=None,
                       cancel_check=None) -> None:
    """PowerShell Invoke-WebRequest — .NET's schannel stack, the very TLS
    path Windows browsers use. TLS 1.2 is pinned (middleboxes that break
    TLS 1.3 choke on it)."""
    ps = shutil.which("powershell") or shutil.which("powershell.exe")
    if not ps:
        raise RuntimeError("PowerShell is not available on this machine")

    def _q(s: str) -> str:                  # single-quoted PS string
        """Quote a string as a single-quoted PowerShell literal."""
        return "'" + s.replace("'", "''") + "'"

    # exit 22 on an HTTP status answer mirrors curl's --fail convention:
    # _proc_download maps it to _HttpAnswerError, so the server's 404 moves
    # the mirror chain on instead of retrying the next transport.
    script = (
        "$ErrorActionPreference='Stop';"
        "[Net.ServicePointManager]::SecurityProtocol="
        "[Net.SecurityProtocolType]::Tls12;"
        "try { Invoke-WebRequest -Uri " + _q(url) +
        " -UserAgent " + _q(DATA_INSTALLER_UA) +
        " -OutFile " + _q(str(part)) +
        " -UseBasicParsing | Out-Null }"
        "catch {"
        "  $code = 0;"
        "  try { $code = [int]$_.Exception.Response.StatusCode } catch {};"
        "  if ($code -ge 400) {"
        "    [Console]::Error.WriteLine('HTTP ' + $code);"
        "    exit 22;"
        "  };"
        "  exit 1;"
        "};"
        "exit 0")
    cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass",
           "-Command", script]
    _proc_download(cmd, part, progress_cb, cancel_check, tail=" · PowerShell")


def _download_to_data(url: str, dest: Path, progress_cb=None,
                      cancel_check=None, log_cb=None) -> Path:
    """Stream `url` into `dest` with progress + cancel support.

    progress_cb(pct, detail) — pct is -1 when the server sends no length.
    The file is written to `<dest>.part` and atomically renamed on success.

    v3.8 SSL RESILIENCE: the download walks a chain of transports — urllib
    (default SSL → TLS 1.2 → relaxed) → curl → PowerShell — retrying only
    transport-level failures, and remembers the first transport that gets
    through for the rest of the session. See the transport chain notes at
    the top of the Data installer section.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")

    def _drop():
        """Remove the .part file of a failed download attempt."""
        try:
            if part.exists():
                part.unlink()
        except Exception:
            pass

    names = {"default": "the platform's default SSL", "tls12": "TLS 1.2",
             "relaxed": "relaxed certificate checks",
             "curl": "curl (schannel)", "powershell": "PowerShell (schannel)"}
    order = _transport_order()
    last_err: Optional[Exception] = None
    for i, transport in enumerate(order):
        try:
            if transport == "curl":
                _curl_stream(url, part, progress_cb, cancel_check)
            elif transport == "powershell":
                _powershell_stream(url, part, progress_cb, cancel_check)
            else:
                _urllib_stream(url, part, transport, progress_cb, cancel_check)
            _remember_transport(transport)
            part.replace(dest)
            return dest
        except _CancelRequested:
            _drop()
            raise
        except Exception as e:
            if not _is_transport_error(e):
                _drop()
                raise              # the server answered — the chain moves on
            last_err = e
            _drop()
            if log_cb:
                nxt = order[i + 1] if i + 1 < len(order) else None
                if nxt:
                    try:
                        log_cb(f"[warn] {e} — retrying over {names.get(nxt, nxt)}")
                    except Exception:
                        pass
    raise (last_err if last_err is not None
           else RuntimeError(f"download failed: {url}"))


# --- archive extraction ---
def _extract_zip(zip_path: Path, dest_dir: Path, progress_cb=None,
                 cancel_check=None) -> None:
    """Extract a zip with per-file progress + cancel between entries.

    v3.8: the Unix mode stored in each entry is restored after extraction —
    zipfile.extract silently drops it, which used to leave the build-tools
    binaries (aapt, aapt2, d8, zipalign, apksigner) non-executable on
    Linux/macOS after a Data install. (No-op on Windows.)"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        total = max(1, len(names))
        for i, name in enumerate(names):
            _data_cancel_guard(cancel_check)
            zf.extract(name, dest_dir)
            try:
                mode = (zf.getinfo(name).external_attr >> 16) & 0o7777
                if mode:
                    os.chmod(os.path.join(str(dest_dir), name), mode)
            except Exception:
                pass
            if progress_cb:
                try:
                    progress_cb(int((i + 1) * 100 / total), f"{i + 1}/{total} files")
                except Exception:
                    pass


def _extract_tar_gz(tar_path: Path, dest_dir: Path, progress_cb=None,
                    cancel_check=None) -> None:
    """Extract a .tar.gz (Adoptium ships JDK for Linux/macOS as tar.gz,
    Windows as zip) with per-member progress + cancel."""
    import tarfile
    dest_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tf:
        members = [m for m in tf.getmembers() if not m.issym() and not m.islnk()]
        total = max(1, len(members))
        for i, m in enumerate(members):
            _data_cancel_guard(cancel_check)
            try:
                tf.extract(m, dest_dir, filter="data")
            except TypeError:                    # Python < 3.12: no filter kwarg
                tf.extract(m, dest_dir)
            if progress_cb:
                try:
                    progress_cb(int((i + 1) * 100 / total), f"{i + 1}/{total} files")
                except Exception:
                    pass


def _archive_kind(path: Path) -> str:
    """Sniff the archive type from magic bytes (servers redirect Adoptium
    to .zip on Windows but .tar.gz on Linux/macOS)."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(4)
    except Exception:
        return "unknown"
    if head.startswith(b"PK\x03\x04"):
        return "zip"
    if head.startswith(b"\x1f\x8b"):
        return "targz"
    return "unknown"


# --- item installation ---
def _pip_install_to_data(packages: List[str], progress_cb=None, log_cb=None,
                         cancel_check=None) -> Tuple[bool, str]:
    """pip install --target Data/python <packages> — never site-packages.

    Returns (ok, message). pip's own output is streamed to log_cb line by
    line; progress_cb gets (-1, line) so the UI can show a busy bar + detail.
    """
    DATA_PY_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "pip", "install", "--no-input",
           "--progress-bar", "off", "--upgrade", "--target", str(DATA_PY_DIR)] \
        + list(packages)
    if log_cb:
        log_cb(f"$ {' '.join(cmd)}")
    creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
            creationflags=creationflags)
    except FileNotFoundError:
        return False, "pip is not available on this machine."
    try:
        for line in proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            _data_cancel_guard(cancel_check)
            if log_cb:
                log_cb(line)
            if progress_cb:
                try:
                    progress_cb(-1, line)
                except Exception:
                    pass
        rc = proc.wait()
    except _CancelRequested:
        try:
            proc.kill()
        except Exception:
            pass
        return False, "Cancelled."
    except Exception as e:
        return False, f"pip failed: {e}"
    if rc != 0:
        return False, f"pip exited with code {rc}."
    return True, "installed"


def _finish_zip_install(key: str, staging: Path, progress_cb=None,
                        cancel_check=None) -> Tuple[bool, str]:
    """Move an extracted archive from its staging dir into its final Data
    home. Each item knows where its payload belongs."""
    _data_cancel_guard(cancel_check)
    entries = [p for p in staging.iterdir()] if staging.is_dir() else []

    if key == "jdk":
        # v3.6.1: vendors ship different layouts — Temurin/Microsoft use a
        # top-level jdk-17.x+y folder, Amazon Corretto on macOS uses
        # amazon-corretto-17.jdk/Contents/Home. Find whichever directory
        # actually contains bin/javac, then install it under a jdk-* name
        # (the environment scan globs ./Data/jdk-*/bin).
        javac_name = "javac.exe" if IS_WINDOWS else "javac"
        home = None
        if staging.is_dir():
            for top in sorted(staging.iterdir()):
                if not top.is_dir():
                    continue
                if (top / "bin" / javac_name).exists():
                    home = top                        # flat layout
                    break
                # macOS bundles: <vendor>.jdk/Contents/Home/bin — and any
                # other one- or two-level wrapper the vendors come up with
                for nested in (sorted(top.glob("*/bin"))
                               + sorted(top.glob("*/*/bin"))):
                    if (nested / javac_name).exists():
                        home = nested.parent
                        break
                if home:
                    break
        if home is None or home == staging:
            return False, "javac missing after extraction"
        top = home
        while top.parent != staging:          # walk up to the archive's root
            top = top.parent
        name = top.name if top.name.lower().startswith("jdk") else f"jdk-{top.name}"
        final = DATA_DIR / name
        if final.exists():
            shutil.rmtree(final, ignore_errors=True)
        shutil.copytree(home, final)
        javac = final / "bin" / javac_name
        if not javac.exists():
            return False, "javac missing after extraction"
        # v3.8: the pin is verified from the real `javac -version` — a
        # mirror serving a different JDK is rejected here and the source
        # chain moves on
        lvl = probe_java_level(javac)
        if lvl != REQUIRED_JDK_MAJOR:
            return False, (f"JDK {lvl or 'unknown'} found — JDK "
                           f"{REQUIRED_JDK_MAJOR} is required")
        return True, str(final / "bin")

    if key == "buildtools":
        # build-tools zips contain one top folder (android-13) with all tools
        src = entries[0] if len(entries) == 1 and entries[0].is_dir() else staging
        final = DATA_DIR / BUILD_TOOLS_LOCAL_DIR
        if final.exists():
            shutil.rmtree(final, ignore_errors=True)
        shutil.copytree(src, final)
        # v3.8: the pin is verified from the archive's own source.properties
        # — a wrong or unversioned revision is never silently installed
        ok, rev = build_tools_pin_status(final)
        if not ok:
            return False, (f"build-tools {rev or 'unversioned'} found — "
                           f"{REQUIRED_BUILD_TOOLS} is required")
        return True, str(final)

    if key == "androidjar":
        jar = search_for_file(str(staging), [ANDROID_JAR_NAME])
        if not jar:
            return False, "android.jar not found inside the archive"
        # v3.8: the pin is verified from the jar's own framework classes —
        # a wrong API level is never silently installed
        rng = android_jar_api_range(jar)
        if rng is None or not (rng[0] <= REQUIRED_ANDROID_API <= rng[1]):
            return False, (f"the archive contains android.jar "
                           f"{android_jar_api_label(rng)} — API "
                           f"{REQUIRED_ANDROID_API} is required")
        final_dir = DATA_DIR / "androidjar"
        final_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(jar, final_dir / ANDROID_JAR_NAME)
        return True, str(final_dir / ANDROID_JAR_NAME)

    return False, f"unknown zip item '{key}'"


def install_data_item(key: str, progress_cb=None, log_cb=None,
                      cancel_check=None) -> Tuple[bool, str]:
    """Download & install ONE item into the Data folder.

    progress_cb(pct, detail): pct 0-100, or -1 for indeterminate (pip lines,
    unknown content length). Returns (ok, message) — message is a short
    human line for toasts and the install dialog.
    """
    item = INSTALL_ITEMS.get(key)
    if item is None:
        return False, f"Unknown item '{key}'."

    def _log(msg):
        """Forward one log line through log_cb, never raising."""
        if log_cb:
            try:
                log_cb(msg)
            except Exception:
                pass

    def _prog(pct, detail):
        """Forward one progress tick through progress_cb, never raising."""
        if progress_cb:
            try:
                progress_cb(pct, detail)
            except Exception:
                pass

    # ---- pip items ----------------------------------------------------------
    if item["kind"] == "pip":
        _log(f"Installing {item['label']} into {DATA_PY_DIR} …")
        _prog(5, "pip " + ", ".join(item["packages"]))
        ok, msg = _pip_install_to_data(item["packages"], progress_cb=_prog,
                                       log_cb=_log, cancel_check=cancel_check)
        if ok:
            _prog(100, "done")
            _log(f"[ok] {item['label']} installed into Data/python")
        return ok, msg

    # ---- zip items ----------------------------------------------------------
    sources = _item_download_sources(item)
    if not sources:
        return False, f"no download URL for '{key}' on this platform."
    staging = DATA_DOWNLOADS_DIR / f".{key}-extract"
    zip_path = DATA_DOWNLOADS_DIR / item["zip_name"]

    def _drop_partial():
        """v3.6.1 — remove a failed source's leftovers before the next try."""
        for p in (zip_path.with_suffix(zip_path.suffix + ".part"), zip_path):
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass

    try:
        DATA_DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        _prog(2, "starting download…")

        def dl_pct(p, detail):
            """Scale the download's 0-100 progress into the bar's first 70%."""
            # download occupies the first 70% of the item's bar
            _prog(-1 if p < 0 else max(2, int(p * 0.7)), f"{detail}")

        # v3.6.1 MIRROR CHAIN — walk the source list until one delivers a
        # real archive. A 404, a timeout, a network block or a captive
        # portal just advances to the next source.
        kind, last_err, tried = None, None, set()
        for src in sources:
            _data_cancel_guard(cancel_check)
            if callable(src):
                _log(f"· resolving a live source (package index / releases)…")
                url = src()
            else:
                url = src
            if not url or url in tried:
                continue
            tried.add(url)
            n_attempt = len(tried)
            src_label = ("primary source" if n_attempt == 1 else
                         f"backup source #{n_attempt - 1}")
            try:
                _log(f"Downloading {item['label']} — {url}  ·  {src_label}")
                _download_to_data(url, zip_path, progress_cb=dl_pct,
                                  cancel_check=cancel_check, log_cb=_log)
                kind = _archive_kind(zip_path)
                if kind not in ("zip", "targz"):
                    raise RuntimeError(
                        "the download is not a zip/tar.gz archive "
                        "(source blocked, renamed or hijacked?)")
                break
            except _CancelRequested:
                raise
            except Exception as e:
                last_err, kind = e, None
                _log(f"[error] {src_label} failed: {e}")
                _drop_partial()
        if kind is None:
            raise RuntimeError(
                f"all {len(sources)} download sources failed"
                + (f" — last error: {last_err}" if last_err else ""))

        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        _prog(72, "extracting…")
        _log(f"Extracting {item['label']} …")

        def ex_pct(p, detail):
            """Scale extraction progress into the bar's 70→95% slice."""
            # extraction occupies 70→95%
            _prog(72 + int(p * 0.23), f"extracting — {detail}")

        if kind == "targz":
            _extract_tar_gz(zip_path, staging, progress_cb=ex_pct,
                            cancel_check=cancel_check)
        elif kind == "zip":
            _extract_zip(zip_path, staging, progress_cb=ex_pct,
                         cancel_check=cancel_check)
        else:
            return False, "downloaded file is neither zip nor tar.gz"
        _prog(96, "finalizing…")
        ok, msg = _finish_zip_install(key, staging, progress_cb=_prog,
                                      cancel_check=cancel_check)
        if ok:
            _prog(100, "done")
            _log(f"[ok] {item['label']} ready → {msg}")
        return ok, msg
    except _CancelRequested:
        return False, "Cancelled."
    except Exception as e:
        _log(f"[error] {item['label']} failed: {e}")
        return False, str(e)
    finally:
        # staging always disappears; the zip stays for instant offline reinstall
        shutil.rmtree(staging, ignore_errors=True)
        try:
            if zip_path.exists():
                zip_path.unlink()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# JDK VERSION PROBING & THE PINNED TOOLCHAIN (v3.8 — forged to spec)
# ---------------------------------------------------------------------------
# APK Forge builds with JDK 17 — exactly 17, from the portable Data folder
# (one-click installer) or from a path set by hand in Settings → Advanced.
# The system is NEVER scanned: PATH javac, JAVA_HOME, Program Files vendors,
# IntelliJ ~/.jdks and Android Studio's runtime used to be silently picked
# up (v3.3.1's auto-selection), which built your app with whatever happened
# to be installed. A wrong version is now called out by name — in the READY
# TO BUILD? checklist and as a build-stopping error — instead of failing
# later with cryptic javac/d8 output.

_JDK_LEVEL_CACHE: Dict[str, Optional[int]] = {}

_RE_JAVA_VERSION = re.compile(r'(?:openjdk|javac|java)(?:\s+version)?\s+"?(\d+)(?:\.(\d+))?')


def parse_java_version(raw: str) -> Optional[int]:
    """
    'javac 1.6.0_21' → 6 ; 'java version "1.8.0_312"' → 8 ; 'javac 17.0.2' → 17
    Returns None when nothing parseable is found.
    """
    if not raw:
        return None
    m = _RE_JAVA_VERSION.search(raw)
    if not m:
        return None
    major, minor = int(m.group(1)), int(m.group(2) or 0)
    if major == 1:                                   # 1.6 / 1.7 / 1.8 naming
        return minor if minor >= 1 else None
    return major                                     # 9 … 21+ naming


def probe_java_level(binary_path) -> Optional[int]:
    """
    Run `<javac|java> -version` once and return the real Java level
    (6 / 7 / 8 / 11 / 17 / 21 …). Cached per binary path, so the env scan
    plus every build costs ONE subprocess call per installed JDK, ever.
    """
    if not binary_path:
        return None
    key = os.path.normcase(str(binary_path)) if IS_WINDOWS else str(binary_path)
    if key in _JDK_LEVEL_CACHE:
        return _JDK_LEVEL_CACHE[key]
    level = None
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
        proc = subprocess.run(
            [str(binary_path), "-version"], capture_output=True, text=True,
            timeout=25, creationflags=creationflags)
        raw = (proc.stdout or "") + "\n" + (proc.stderr or "")
        level = parse_java_version(raw)
    except Exception:
        level = None
    _JDK_LEVEL_CACHE[key] = level
    return level


def _bin_tool(bin_dir, name: str) -> Optional[str]:
    """javac.exe / javac / java.exe / java inside a bin directory."""
    if not bin_dir:
        return None
    for suffix in (".exe", "") if IS_WINDOWS else ("", ".exe"):
        cand = Path(bin_dir) / (name + suffix)
        if cand.exists():
            return str(cand)
    return None


@dataclass
class JdkDecision:
    """Chosen compiler + runtime for one build (see resolve_build_jdk)."""
    javac: Optional[str] = None
    javac_level: Optional[int] = None
    jdk_bin: str = ""
    java: Optional[str] = None
    java_level: Optional[int] = None

    def source_target(self) -> str:
        """-source/-target — Java 8 bytecode from the pinned JDK 17."""
        return "1.8"


# The pinned-JDK fix attached to every JDK pin failure (build + checklist).
PINNED_JDK_HINT = (
    "Use the one-click installer (Dashboard → READY TO BUILD? → Install) to "
    "download a portable JDK 17 into the Data folder, or set a JDK 17 bin "
    "folder by hand in Settings → Advanced.")


def resolve_build_jdk(cfg_jdk_bin, script_dir=None, log=None) -> JdkDecision:
    """
    v3.8 PINNED TOOLCHAIN — the build runs on JDK 17, exactly.

    Source: the explicit Settings path, else the portable Data folder. The
    system (PATH, JAVA_HOME, vendor folders, IDE runtimes) is never scanned
    — what builds your app is what you installed, where you installed it.
    A wrong version stops the build HERE, by name, instead of failing later
    with cryptic javac/d8 errors. d8 and apksigner run on the very same
    JDK 17: one coherent toolchain, no surprise runtimes.
    """
    def _log(msg):
        """Forward to the caller's log callback, never raising."""
        if log:
            try:
                log(msg)
            except Exception:
                pass

    bin_dir = (cfg_jdk_bin or "").strip() or auto_find_jdk_bin(script_dir)
    javac = _bin_tool(bin_dir, "javac") if bin_dir else None
    if not javac:
        raise RuntimeError(
            f"JDK {REQUIRED_JDK_MAJOR} not found. " + PINNED_JDK_HINT)
    level = probe_java_level(javac)
    if level != REQUIRED_JDK_MAJOR:
        raise RuntimeError(
            f"APK Forge builds with JDK {REQUIRED_JDK_MAJOR}, but the JDK at "
            f"{bin_dir} is Java {level or 'unknown'}. " + PINNED_JDK_HINT)
    if bin_dir != (cfg_jdk_bin or "").strip():
        _log(f"[{log_time()}] [ok] Using the pinned JDK {level} from {bin_dir}")
    return JdkDecision(javac=javac, javac_level=level, jdk_bin=bin_dir,
                       java=_bin_tool(bin_dir, "java"), java_level=level)


def friendly_tool_error(output: str, tool: str) -> Optional[str]:
    """Translate a d8 / apksigner crash into a plain-English cause + fix."""
    if not output:
        return None
    low = output.lower()
    if ("unsupportedclassversionerror" in low or "bad version number" in low
            or "class file has wrong version" in low):
        tail = [ln for ln in output.strip().splitlines() if ln.strip()]
        tail = tail[-1][:180] if tail else ""
        return (f"{tool} needs Java 8+ (its jar is Java 8 bytecode) but the "
                f"selected Java runtime is older. APK Forge builds with the "
                f"pinned JDK {REQUIRED_JDK_MAJOR} — one click in the READY TO "
                f"BUILD? card downloads it into ./Data (with automatic mirror "
                f"fallback).{('  Raw: ' + tail) if tail else ''}")
    if ("could not find or load main class" in low
            or "noclassdeffounderror" in low or "classnotfoundexception" in low):
        return (f"{tool} could not load its jar — the build-tools folder looks "
                f"incomplete. Re-extract android-build-tools-33.0.3 so it "
                f"contains lib/d8.jar and lib/apksigner.jar.")
    if "out of memory" in low or "heap space" in low:
        return (f"{tool} ran out of memory — close heavy applications and "
                f"retry the build.")
    return None


def auto_find_jdk_bin(script_dir=None, log_cb=None):
    """
    AUTOMATION (v3.8): locate the pinned JDK 17 — and ONLY inside the
    portable Data folder beside this script (Data/jdk-*/bin), which is
    where the one-click installer puts it. The system is never scanned:
    PATH javac, JAVA_HOME, Program Files vendors, IntelliJ ~/.jdks and
    Android Studio's runtime are deliberately ignored. A JDK of any other
    version inside Data is passed over — it is named by
    data_jdk_mismatches() instead of being silently used. A JDK outside
    the Data folder is used only when YOU point at it (Settings → Advanced).
    """
    try:
        # resolve() matches the env scanner's resolved script_dir, so a
        # symlinked launch looks in the REAL script folder on both paths
        base = Path(script_dir) if script_dir else Path(__file__).parent.resolve()
    except NameError:
        base = Path.cwd()

    data = base / "Data"
    if not data.is_dir():
        return None
    javac = "javac.exe" if IS_WINDOWS else "javac"
    for child in sorted(data.glob("jdk*")):
        bin_javac = child / "bin" / javac
        if not bin_javac.exists():
            continue
        if probe_java_level(bin_javac) == REQUIRED_JDK_MAJOR:
            return str(child / "bin")
        if log_cb:
            try:
                log_cb(f"[{log_time()}] [warn] JDK at {child} is not Java "
                       f"{REQUIRED_JDK_MAJOR} — skipping it")
            except Exception:
                pass
    return None


def is_full_java_class(java_text: str) -> bool:
    """True if the text declares at least one top-level type."""
    if not java_text or len(java_text.strip()) < 10:
        return False
    return bool(scan_java_structure(java_text)["types"])


# ---------------------------------------------------------------------------
# THE BUILD PIPELINE v3 (with R.java generation & friendly errors)
# ---------------------------------------------------------------------------

def resize_icon(source_path, output_path, size, log_cb=None):
    """Write one density's launcher icon; plain copy if Pillow is missing."""
    if not HAS_PIL:
        shutil.copy2(source_path, output_path)
        if log_cb:
            log_cb(f"[{log_time()}] [warn] Pillow not installed, using original icon size")
        return
    try:
        img = Image.open(source_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        img.resize((size, size), Image.Resampling.LANCZOS).save(output_path, 'PNG')
        if log_cb:
            log_cb(f"[{log_time()}] Created {size}x{size} icon")
    except Exception as e:
        if log_cb:
            log_cb(f"[{log_time()}] [warn] Icon resize failed: {e}")
        shutil.copy2(source_path, output_path)


def create_app_icons(icon_path, res_dir, log_cb=None):
    """Create every mipmap-density launcher icon from one source image."""
    if not icon_path or not Path(icon_path).exists():
        return False
    if log_cb:
        log_cb(f"[{log_time()}] Creating app icons from: {icon_path}")
    for density, size in ICON_SIZES.items():
        mipmap_dir = Path(res_dir) / density
        mipmap_dir.mkdir(parents=True, exist_ok=True)
        resize_icon(icon_path, str(mipmap_dir / "ic_launcher.png"), size, log_cb)
    return True


# ---------------------------------------------------------------------------
# v3.4 ASSET ENGINE — "handle assets massively better"
# ---------------------------------------------------------------------------
# The old system was a flat list of paths blindly copied into assets/. The
# new engine models every bundled file as a rich AssetEntry:
#   • three destinations — assets/ (getAssets().open("name")), res/drawable
#     (real R.drawable.<name> ids) and res/raw (real R.raw.<name> ids)
#   • junk filtering (Thumbs.db, desktop.ini, .DS_Store, ~$lock, .git …)
#   • collision-proof staging (duplicate destinations auto-renamed _2)
#   • Android resource-name sanitization ("Holiday Photo.PNG" → holiday_photo)
#   • size accounting + APK-bloat warnings
#   • code cross-checks: getAssets().open("x") / R.drawable.y references are
#     matched against what actually got staged, with plain-English hints

ASSET_TARGETS = ("assets", "drawable", "raw")
ASSET_DRAWABLE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
ASSET_RAW_EXTS = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac", ".mid", ".midi"}

_ASSET_JUNK_NAMES = {"thumbs.db", "desktop.ini", ".ds_store", "__macosx"}
_ASSET_JUNK_SUFFIXES = (".tmp", ".temp", ".bak", ".swp", ".lnk")
_ASSET_JUNK_PREFIXES = ("~$", ".git")


def _asset_is_junk(path: Path) -> bool:
    """True for desktop junk files (Thumbs.db, .DS_Store, ~$lock, .git…)."""
    n = path.name.lower()
    return (n in _ASSET_JUNK_NAMES
            or any(n.endswith(s) for s in _ASSET_JUNK_SUFFIXES)
            or any(n.startswith(p) for p in _ASSET_JUNK_PREFIXES))


_RE_RES_NAME_INVALID = re.compile(r"[^a-z0-9_]")
_RE_RES_NAME_RUNS = re.compile(r"_+")


def normalize_res_name(stem: str) -> str:
    """Android resource names: [a-z0-9_], must start with a letter."""
    s = _RE_RES_NAME_INVALID.sub("_", (stem or "").strip().lower())
    s = _RE_RES_NAME_RUNS.sub("_", s).strip("_")
    if not s:
        return "asset"
    if s[0].isdigit():
        s = "a" + s
    return s


def format_size(n) -> str:
    """Human-readable byte count ('1.5 MB', '512 KB', '42 B' …)."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "0 B"
    if n >= 1024 * 1024 * 1024:
        return f"{n / 1024 / 1024 / 1024:.2f} GB"
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n:.0f} B"


@dataclass
class AssetEntry:
    """One bundled file / folder / inline-text with its destination in the APK."""
    source: str = ""        # filesystem path ("" for inline text assets)
    text: str = ""          # inline content when source == ""
    name: str = ""          # destination name inside the APK
    target: str = "assets"  # 'assets' | 'drawable' | 'raw'
    enabled: bool = True

    # --- predicates ---
    @property
    def is_inline(self) -> bool:
        """True when the entry carries inline text instead of a file."""
        return not self.source

    @property
    def is_dir(self) -> bool:
        """True when the source path exists and is a folder."""
        try:
            return bool(self.source) and Path(self.source).is_dir()
        except Exception:
            return False

    @property
    def exists(self) -> bool:
        """True when the entry is inline or its source path exists."""
        return self.is_inline or Path(self.source).exists()

    @property
    def suffix(self) -> str:
        """Lowercased extension of the destination name."""
        return Path(self.name).suffix.lower() if self.name else ""

    # --- naming ---
    def res_name(self) -> str:
        """Validated Android resource name for drawable/raw targets."""
        return normalize_res_name(Path(self.name).stem)

    @classmethod
    def from_path(cls, path: str, target: str = "assets") -> "AssetEntry":
        """Build an entry from a filesystem path with a chosen target."""
        return cls(source=str(path), name=Path(path).name, target=target)

    @classmethod
    def guess_target(cls, path: str) -> str:
        """Guess the destination from the file extension alone."""
        ext = Path(path).suffix.lower()
        if ext in ASSET_DRAWABLE_EXTS:
            return "drawable"
        if ext in ASSET_RAW_EXTS:
            return "raw"
        return "assets"

    @classmethod
    def smart_target(cls, path: str, java_text: str = "") -> str:
        """Pick the destination for a NEW asset: files the code already opens
        via getAssets() MUST stay in assets/. Otherwise images become
        drawables and sounds become raw resources (R.drawable/R.raw access)."""
        name = Path(path).name
        if java_text and name and f'"{name}"' in java_text and "getAssets()" in java_text:
            return "assets"
        return cls.guess_target(path)

    # --- presentation ---
    def dest_display(self) -> str:
        """Human-readable destination path for the Design page."""
        if self.target == "drawable":
            return f"res/drawable/{self.res_name()}{self.suffix}"
        if self.target == "raw":
            return f"res/raw/{self.res_name()}{self.suffix}"
        if self.is_dir:
            return f"assets/{self.name}/…"
        return f"assets/{self.name}"

    def access_snippet(self) -> str:
        """The exact Java snippet that loads this asset."""
        if self.target == "drawable":
            return f"R.drawable.{self.res_name()}"
        if self.target == "raw":
            return f"R.raw.{self.res_name()}"
        if self.is_dir:
            return f'getAssets().list("{self.name}")'
        return f'getAssets().open("{self.name}")'

    def type_icon(self) -> str:
        """Short type tag for the Design page asset list."""
        if self.is_inline:
            return "txt"
        if not self.exists:
            return "n/a"
        if self.is_dir:
            return "dir"
        ext = self.suffix
        if ext in ASSET_DRAWABLE_EXTS:
            return "img"
        if ext in ASSET_RAW_EXTS:
            return "snd"
        if ext in (".mp4", ".mkv", ".3gp", ".webm"):
            return "vid"
        if ext in (".txt", ".json", ".xml", ".csv", ".html", ".htm", ".js", ".css"):
            return "txt"
        return "bin"

    def size_bytes(self) -> int:
        """Byte size on disk (recursive for folders); 0 when unknown."""
        try:
            if self.is_inline:
                return len((self.text or "").encode("utf-8"))
            p = Path(self.source)
            if p.is_file():
                return p.stat().st_size
            if p.is_dir():
                return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        except Exception:
            pass
        return 0

    # --- persistence ---
    def to_json(self) -> dict:
        """Serialize the entry for project-file persistence."""
        return {"source": self.source, "text": self.text, "name": self.name,
                "target": self.target, "enabled": self.enabled}

    @classmethod
    def from_json(cls, d: dict) -> "AssetEntry":
        """Rebuild an entry from its saved dict, validating the target."""
        e = cls(source=str(d.get("source", "")),
                text=str(d.get("text", "")),
                name=str(d.get("name", "")),
                target=str(d.get("target", "assets")))
        if e.target not in ASSET_TARGETS:
            e.target = "assets"
        if not e.name and e.source:
            e.name = Path(e.source).name
        e.enabled = bool(d.get("enabled", True))
        return e

    def copy(self) -> "AssetEntry":
        """Duplicate the entry (used when a list row is edited in place)."""
        return AssetEntry(source=self.source, text=self.text, name=self.name,
                          target=self.target, enabled=self.enabled)


@dataclass
class AssetStageResult:
    """What stage_assets() bundled into one build workspace."""
    files_staged: int = 0
    bytes_staged: int = 0
    junk_skipped: int = 0
    asset_names: Set[str] = field(default_factory=set)   # every file under assets/
    asset_folders: Set[str] = field(default_factory=set)  # every folder under assets/
    drawables: Set[str] = field(default_factory=set)      # available R.drawable.<name>
    raws: Set[str] = field(default_factory=set)           # available R.raw.<name>
    skipped: List[str] = field(default_factory=list)      # missing sources
    warnings: List[str] = field(default_factory=list)


def stage_assets(entries: List[AssetEntry], work_dir, res_dir, log_cb=None) -> AssetStageResult:
    """Copy every enabled AssetEntry into the build workspace: assets/ root,
    res/drawable (image → R.drawable.<name>) or res/raw (→ R.raw.<name>).
    Junk is filtered, collisions auto-renamed, and the exact code reference
    for each staged resource is logged."""
    result = AssetStageResult()
    assets_dir = Path(work_dir) / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    used_dests: Set[str] = set()
    used_res: Set[str] = set()

    def log(msg: str):
        """Timestamp a message and forward it to the build log."""
        if log_cb:
            log_cb(f"[{log_time()}] {msg}")

    def claim(dest_rel: str, label: str) -> str:
        """Reserve a destination path; auto-rename on collision (name_2.ext)."""
        if dest_rel in used_dests:
            folder, _, fname = dest_rel.rpartition("/")
            p = Path(fname)
            n = 2
            while True:
                cand = f"{folder}/{p.stem}_{n}{p.suffix}" if folder else f"{p.stem}_{n}{p.suffix}"
                if cand not in used_dests:
                    used_dests.add(cand)
                    result.warnings.append(
                        f"'{label}' clashed with another asset of the same name — "
                        f"staged as {cand} (rename one of them on the Design page)")
                    log(f"[warn] Name clash: '{label}' → {cand}")
                    return cand
                n += 1
        used_dests.add(dest_rel)
        return dest_rel

    def copy_tree_filtered(src: Path, dest_dir: Path, prefix: str) -> None:
        """Recursively copy a folder into assets/, skipping junk files."""
        for f in sorted(src.iterdir()):
            if _asset_is_junk(f):
                result.junk_skipped += 1
                continue
            if f.is_dir():
                sub = dest_dir / f.name
                sub.mkdir(parents=True, exist_ok=True)
                result.asset_folders.add(f"{prefix}{f.name}")
                copy_tree_filtered(f, sub, f"{prefix}{f.name}/")
            elif f.is_file():
                shutil.copy2(f, dest_dir / f.name)
                result.files_staged += 1
                result.bytes_staged += f.stat().st_size
                result.asset_names.add(f"{prefix}{f.name}")

    for entry in entries:
        if not entry.enabled or not entry.name:
            continue

        # --- inline text asset → always plain assets ---
        if entry.is_inline:
            dest_rel = claim(f"assets/{entry.name}", entry.name)
            fname = Path(dest_rel).name
            (assets_dir / fname).write_text(entry.text or "", encoding="utf-8")
            result.files_staged += 1
            result.bytes_staged += len((entry.text or "").encode("utf-8"))
            result.asset_names.add(fname)
            log(f"Inline asset written: assets/{fname}")
            continue

        src = Path(entry.source)
        if not src.exists():
            result.skipped.append(entry.name)
            result.warnings.append(
                f"'{entry.name}' no longer exists at {entry.source} — skipped "
                f"(remove it on the Design page)")
            log(f"[warn] Asset missing on disk: {entry.name}")
            continue

        # --- folder → always assets/<name>/ (recursive, junk-filtered) ---
        if src.is_dir():
            dest_rel = claim(f"assets/{entry.name}", entry.name)
            fname = Path(dest_rel).name
            dest = assets_dir / fname
            dest.mkdir(parents=True, exist_ok=True)
            result.asset_folders.add(fname)
            copy_tree_filtered(src, dest, f"{fname}/")
            log(f"Folder bundled: assets/{fname}/ …")
            continue

        # --- single file — route by target ---
        target = entry.target if entry.target in ASSET_TARGETS else "assets"
        if target == "drawable" and src.suffix.lower() not in ASSET_DRAWABLE_EXTS:
            log(f"[warn] '{entry.name}' is not an image — routed to assets/ instead of drawable")
            result.warnings.append(
                f"'{entry.name}' can't be a drawable (images only) — routed to assets/")
            target = "assets"

        if target == "assets":
            dest_rel = claim(f"assets/{entry.name}", entry.name)
            fname = Path(dest_rel).name
            shutil.copy2(src, assets_dir / fname)
            result.files_staged += 1
            result.bytes_staged += src.stat().st_size
            result.asset_names.add(fname)
            if src.stat().st_size > 8 * 1024 * 1024:
                result.warnings.append(
                    f"'{entry.name}' is {format_size(src.stat().st_size)} — consider "
                    f"compressing it; every byte ships inside the APK")
            log(f"Asset bundled: assets/{fname}")
        else:
            res = entry.res_name()
            base = res
            n = 2
            while res in used_res:
                res = f"{base}_{n}"
                n += 1
            used_res.add(res)
            if res != base:
                result.warnings.append(
                    f"'{entry.name}' clashes with another '{base}' resource — "
                    f"renamed to '{res}'")
            ext = src.suffix.lower()
            dest_dir = Path(res_dir) / ("drawable" if target == "drawable" else "raw")
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest_dir / f"{res}{ext}")
            result.files_staged += 1
            result.bytes_staged += src.stat().st_size
            if target == "drawable":
                result.drawables.add(res)
                log(f"Image resource: {entry.name} → R.drawable.{res}")
            else:
                result.raws.add(res)
                log(f"Raw resource: {entry.name} → R.raw.{res}")

    if result.bytes_staged > 60 * 1024 * 1024:
        result.warnings.append(
            f"Assets total {format_size(result.bytes_staged)} — very large APK; "
            f"trim heavy files if you can")
    return result


# ---------------------------------------------------------------------------
# v3.4 ASSET ⇄ CODE CROSS-CHECK
# ---------------------------------------------------------------------------
_ASSET_OPEN_RE = re.compile(r'getAssets\(\)\s*\.\s*(?:open|openFd|list)\s*\(\s*"([^"]+)"')
_ANDROID_ASSET_URL_RE = re.compile(r'file:///android_asset/([A-Za-z0-9_\-./]+)')
_R_DRAWABLE_RE = re.compile(r'\bR\s*\.\s*drawable\s*\.\s*([A-Za-z_]\w*)')
_R_RAW_RE = re.compile(r'\bR\s*\.\s*raw\s*\.\s*([A-Za-z_]\w*)')


@dataclass
class AssetUsage:
    """Asset/resource references extracted from the Java code."""
    asset_opens: Set[str] = field(default_factory=set)
    drawables: Set[str] = field(default_factory=set)
    raws: Set[str] = field(default_factory=set)


def scan_asset_usage(java_text: str) -> AssetUsage:
    """Extract every asset/resource reference the code makes."""
    usage = AssetUsage()
    if not java_text:
        return usage
    usage.asset_opens.update(m.group(1) for m in _ASSET_OPEN_RE.finditer(java_text))
    usage.asset_opens.update(m.group(1) for m in _ANDROID_ASSET_URL_RE.finditer(java_text))
    # R.* refs: scan with comments/strings masked so prose can't trigger
    try:
        masked = mask_java(java_text)
    except Exception:
        masked = java_text
    usage.drawables.update(m.group(1) for m in _R_DRAWABLE_RE.finditer(masked))
    usage.raws.update(m.group(1) for m in _R_RAW_RE.finditer(masked))
    return usage


def asset_reference_warnings(java_text: str, staged: AssetStageResult) -> List[str]:
    """Cross-check code references against what actually got staged."""
    if not java_text:
        return []
    usage = scan_asset_usage(java_text)
    warns: List[str] = []
    for name in sorted(usage.asset_opens):
        if name in staged.asset_names or name in staged.asset_folders:
            continue
        in_folder = [a for a in staged.asset_names if a.endswith("/" + name)]
        if in_folder:
            warns.append(f'getAssets().open("{name}") — that file is bundled inside '
                         f'"{in_folder[0]}" — open("{in_folder[0]}") is the correct path')
        elif staged.asset_names:
            warns.append(f'getAssets().open("{name}") — no bundled asset is named '
                         f'"{name}" (check the exact name & extension on the Design page)')
        else:
            warns.append(f'getAssets().open("{name}") — no assets are bundled; add '
                         f'the file on the Design page first')
    for r in sorted(usage.drawables - staged.drawables):
        warns.append(f"R.drawable.{r} — no image resource '{r}'. Tag an image asset as "
                     f"'drawable' on the Design page, or load it via getAssets()")
    for r in sorted(usage.raws - staged.raws):
        warns.append(f"R.raw.{r} — no raw resource '{r}'. Tag a sound/file asset as "
                     f"'raw' on the Design page, or load it via getAssets()")
    return warns


def asset_diagnostics(java_text: str, entries: List[AssetEntry]) -> List[JavaIssue]:
    """Diagnostics-panel cross-check (cheap — no folder walking): compares
    code references against the configured entries."""
    issues: List[JavaIssue] = []
    if not java_text:
        return issues
    usage = scan_asset_usage(java_text)
    file_names = {e.name for e in entries if e.enabled and not e.is_dir}
    folder_names = {e.name for e in entries if e.enabled and e.is_dir}
    folder_prefixes = {e.name + "/" for e in entries if e.enabled and e.is_dir}
    drawable_names = {e.res_name() for e in entries if e.enabled and e.target == "drawable"}
    raw_names = {e.res_name() for e in entries if e.enabled and e.target == "raw"}

    for name in sorted(usage.asset_opens):
        if (name in file_names or name in folder_names
                or any(name.startswith(p) for p in folder_prefixes)):
            continue
        hit = [f for f in file_names if f == Path(name).name]
        if hit:
            issues.append(JavaIssue(
                "warn", f'getAssets().open("{name}") — path mismatch',
                f'the bundled file is "{hit[0]}" (no folder part) — use '
                f'open("{hit[0]}").', "goto_design"))
        else:
            issues.append(JavaIssue(
                "warn", f'getAssets().open("{name}") — asset not bundled',
                "Add this file on the Design page (Assets & Resources), or remove "
                "the call.", "goto_design"))
    for r in sorted(usage.drawables - drawable_names):
        issues.append(JavaIssue(
            "warn", f"R.drawable.{r} is not bundled",
            "Tag an image asset as 'drawable' on the Design page so it gets a "
            "real R.drawable id, or load it via getAssets().open(…).", "goto_design"))
    for r in sorted(usage.raws - raw_names):
        issues.append(JavaIssue(
            "warn", f"R.raw.{r} is not bundled",
            "Tag a sound/file asset as 'raw' on the Design page so it gets a real "
            "R.raw id, or load it via getAssets().open(…).", "goto_design"))

    # bundled-but-never-referenced (info, capped)
    if file_names or folder_prefixes:
        referenced = set(usage.asset_opens) | usage.drawables | usage.raws
        unused = []
        for e in entries:
            if not e.enabled:
                continue
            base = e.res_name() if e.target in ("drawable", "raw") else Path(e.name).stem
            if base in referenced or e.name in usage.asset_opens:
                continue
            unused.append(e.name)
        if unused:
            issues.append(JavaIssue(
                "info", f"{len(unused)} bundled asset(s) never referenced in code",
                "They still ship inside the APK (fine for data drops): "
                + ", ".join(unused[:6]) + (" …" if len(unused) > 6 else "")))
    return issues[:8]


def motion_injection_warnings(java_text: str, elements: List[ElementInfo]) -> List[JavaIssue]:
    """
    v3.5 MOTION SAFETY — surface motion/sound/image configuration problems in
    the Diagnostics panel BEFORE the build (they used to be build-log-only):
      • element renamed away / never declared → injection skipped
      • element only declared as an unassigned field → falls back to onCreate
      • configured sound/image file missing on disk
    Cheap: reuses the memoised structure scan + 3 short regexes per element.
    """
    issues: List[JavaIssue] = []
    configured = [e for e in elements if (e.animations or e.sound_path or e.image_path)]
    if not configured or not java_text:
        return issues
    try:
        struct = scan_java_structure(java_text)
        masked = struct["masked"]
        spans = struct["stmt_spans"]

        def in_stmt_span(pos: int) -> bool:
            """True when pos lies inside an executable statement span."""
            return any(o <= pos < c for (o, c) in spans)

        for e in configured[:12]:
            name = re.escape(e.name)
            etype = re.escape(e.type)
            decl_any = re.search(rf'\b{etype}(?:\s*<[^;=]*?>+)?\s+{name}\s*[;=]', masked)
            stmt_hit = False
            for pat in (
                rf'\b{etype}(?:\s*<[^;=]*?>+)?\s+{name}\s*=[^;]*;',
                rf'(?<![\w.]){name}\s*=\s*[^;]*findViewById[^;]*;',
                rf'(?<![\w.]){name}\s*=\s*new\s+{etype}(?:\s*<[^;(]*?>+)?\s*\([^;]*;',
            ):
                if any(in_stmt_span(m.start()) for m in re.finditer(pat, masked)):
                    stmt_hit = True
                    break
            if stmt_hit:
                continue                       # will inject right after the statement
            if decl_any:
                issues.append(JavaIssue(
                    "warn", f"'{e.name}' is only declared as a field",
                    "Its motion/sound is injected at the END of onCreate() "
                    "(the field must be assigned there or earlier for the "
                    "animation to play). Declare or assign it inside a method "
                    "for an immediate entrance.", "goto_source"))
            else:
                issues.append(JavaIssue(
                    "error", f"Element '{e.name}' not found in the Java code",
                    "Motion/sound/image configured for it will be SKIPPED — "
                    "the variable no longer exists (renamed? typo?). Fix the "
                    "name or remove the element on the Motion page.", "goto_motion"))

        for e in configured:
            if e.sound_path and not e.sound_path.startswith("builtin:") \
                    and not Path(e.sound_path).exists():
                issues.append(JavaIssue(
                    "warn", f"Sound file missing: {Path(e.sound_path).name}",
                    f"'{e.sound_path}' does not exist anymore — the tap sound "
                    "for " + e.name + " will be skipped. Re-pick it on the "
                    "Motion page (or choose a built-in sound).", "goto_motion"))
            if e.image_path and not Path(e.image_path).exists():
                issues.append(JavaIssue(
                    "warn", f"Image file missing: {Path(e.image_path).name}",
                    f"'{e.image_path}' does not exist anymore — the image for "
                    + e.name + " will be skipped. Re-pick it on the Motion page.",
                    "goto_motion"))
    except Exception:
        pass          # diagnostics must never break the scan pipeline
    return issues[:8]


def write_manifest(manifest_path, cfg, analysis: JavaAnalysis):
    """
    v3: registers ALL activities/services/receivers found in the single file.
    The launcher activity is MainActivity (or the first Activity found).
    """
    package = cfg.get("package", APP_DEFAULTS["package"])
    app_name = cfg.get("app_name", APP_DEFAULTS["app_name"])
    version_code = int(cfg.get("version_code", APP_DEFAULTS["version_code"]))
    version_name = str(cfg.get("version_name", APP_DEFAULTS["version_name"]))
    min_sdk = int(cfg.get("min_sdk", APP_DEFAULTS["min_sdk"]))
    target_sdk = int(cfg.get("target_sdk", APP_DEFAULTS["target_sdk"]))
    permissions = cfg.get("permissions", [])
    has_icon = cfg.get("has_icon", False)

    launcher = cfg.get("activity_name") or analysis.launcher or APP_DEFAULTS["activity_name"]
    extra_activities = [a for a in analysis.activities if a != launcher]

    perm_xml = "".join(f'    <uses-permission android:name="{p}"/>\n' for p in permissions)
    icon_attr = ' android:icon="@mipmap/ic_launcher"' if has_icon else ''

    def activity_xml(name, exported, launcher_filter):
        """Render one <activity> element, launcher intent-filter optional."""
        s = f'        <activity android:name=".{name}"'
        if exported:
            s += ' android:exported="true"'
        s += '>\n'
        if launcher_filter:
            s += ('            <intent-filter>\n'
                  '                <action android:name="android.intent.action.MAIN"/>\n'
                  '                <category android:name="android.intent.category.LAUNCHER"/>\n'
                  '            </intent-filter>\n')
        s += '        </activity>\n'
        return s

    components = activity_xml(launcher, True, True)
    for a in extra_activities:
        components += activity_xml(a, False, False)
    for s in analysis.services:
        components += f'        <service android:name=".{s}"/>\n'
    for r in analysis.receivers:
        components += f'        <receiver android:name=".{r}"/>\n'
    for p in analysis.providers:
        components += f'        <provider android:name=".{p}" android:authorities="{package}.{p.lower()}"/>\n'

    manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{package}"
    android:versionCode="{version_code}"
    android:versionName="{version_name}">
{perm_xml}    <uses-sdk android:minSdkVersion="{min_sdk}" android:targetSdkVersion="{target_sdk}" />
    <application android:label="@string/app_name"{icon_attr}
        android:allowBackup="true" android:supportsRtl="true"
        android:theme="@android:style/Theme.Material.NoActionBar">
{components}    </application>
</manifest>
'''
    Path(manifest_path).write_text(manifest, encoding="utf-8")


def write_default_resources(res_dir, app_name):
    """Write res/values/strings.xml with the escaped app name."""
    values_dir = Path(res_dir) / "values"
    values_dir.mkdir(parents=True, exist_ok=True)
    strings = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{html_escape(app_name)}</string>
</resources>
'''
    (values_dir / "strings.xml").write_text(strings, encoding="utf-8")


def write_animation_resources(res_dir, elements: List[ElementInfo], log_cb=None):
    """Write res/anim/*.xml for every configured animation type."""
    anim_durations: Dict[str, int] = {}
    for element in elements:
        for anim_type in element.animations:
            # clamp at aggregation time (0 → default 300, negatives → 50)
            dur = max(50, min(10_000, int(element.animation_duration or 300)))
            anim_durations[anim_type] = max(anim_durations.get(anim_type, 0), dur)
    if not anim_durations:
        return                  # v3.3: no animations → no empty res/anim dir
    anim_dir = Path(res_dir) / "anim"
    anim_dir.mkdir(parents=True, exist_ok=True)
    for anim_type, duration in anim_durations.items():
        # v3.3: clamp to a sane range — a 0/blank duration made the animation
        # complete instantly (i.e. it never displayed at all).
        duration = max(50, min(10_000, int(duration or 300)))
        xml_content = generate_animation_xml(anim_type, duration)
        if xml_content:
            (anim_dir / f"{anim_type}.xml").write_text(xml_content, encoding="utf-8")
            if log_cb:
                log_cb(f"[{log_time()}] Created animation: {anim_type}.xml ({duration} ms)")


def _kill_process_tree(p: subprocess.Popen):
    """Kill a subprocess AND its children (d8.bat / apksigner.bat spawn java)."""
    try:
        if IS_WINDOWS:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                           capture_output=True, timeout=15,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            os.kill(p.pid, signal.SIGKILL)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def run_exe(args, cwd=None, env=None, log_cb=None, timeout: int = 600):
    """Run a subprocess, streaming its output to the log callback.

    Robustness (v3.1):
      • stdin is /dev/null — a tool can never hang waiting for console input.
      • a watchdog kills the whole process tree after `timeout` seconds, so a
        stuck tool can never freeze a build forever.
    """
    if log_cb:
        def q(a):
            """Quote a subprocess argument containing spaces/metacharacters."""
            return f'"{a}"' if (" " in a or "*" in a or ";" in a or ":" in a) else a
        log_cb(f"[{log_time()}] RUN: " + " ".join(q(a) for a in args))
    creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
    try:
        p = subprocess.Popen(
            args, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", shell=False,
            creationflags=creationflags)
    except FileNotFoundError as e:
        if log_cb:
            log_cb(f"[{log_time()}] [error] Tool not found: {e}")
        return 127, str(e)
    except Exception as e:
        if log_cb:
            log_cb(f"[{log_time()}] [error] Could not start: {e}")
        return 1, str(e)

    watchdog_fired = threading.Event()

    def _watchdog():
        """Fire after the timeout and kill the whole process tree."""
        watchdog_fired.set()
        if log_cb:
            log_cb(f"[{log_time()}] [warn] Watchdog: tool unresponsive for {timeout}s — "
                   f"killing process tree (pid {p.pid})…")
        _kill_process_tree(p)

    timer = threading.Timer(timeout, _watchdog)
    timer.daemon = True
    timer.start()

    out: List[str] = []
    try:
        for line in p.stdout:
            out.append(line)
            if log_cb:
                log_cb(line.rstrip())
        rc = p.wait()
    except Exception as e:                     # e.g. stream torn down by the kill
        rc = p.poll()
        rc = 1 if rc is None else rc
        out.append(f"\n[watchdog] {e}\n")
    finally:
        timer.cancel()

    if watchdog_fired.is_set() and rc == 0:
        rc = 1                                 # killed by watchdog ≠ success
        out.append(f"\n[{log_time()}] [error] Killed by the {timeout}s watchdog.\n")
    return rc, "".join(out)


def run_bat(bat_path, extra_args, cwd=None, env=None, log_cb=None):
    """Run a Windows .bat tool through cmd /c via run_exe()."""
    cmd = ["cmd", "/c", bat_path] + extra_args
    return run_exe(cmd, cwd=cwd, env=env, log_cb=log_cb)


class BuildConfig:
    """All inputs & tool paths for one APK build (v3.4 rich assets included)."""

    def __init__(self):
        """Reset every field to the APP_DEFAULTS baseline (no toolchain scan)."""
        self.app_name = APP_DEFAULTS["app_name"]
        self.package = APP_DEFAULTS["package"]
        self.activity_name = APP_DEFAULTS["activity_name"]
        self.version_code = APP_DEFAULTS["version_code"]
        self.version_name = APP_DEFAULTS["version_name"]
        self.min_sdk = APP_DEFAULTS["min_sdk"]
        self.target_sdk = APP_DEFAULTS["target_sdk"]
        self.permissions: List[str] = []
        self.java_text = ""
        self.java_is_full = False

        self.android_jar = ""
        # v3.1: no toolchain discovery here — this used to walk Program Files
        # on the UI thread and delay startup by seconds. The background
        # environment scan (EnvScannerThread) fills jdk_bin in instead.
        self.jdk_bin = ""

        self.keystore_path = ""
        self.keystore_pass = "android"
        self.key_alias = "androiddebugkey"
        self.key_pass = "android"

        self.use_aapt2 = False
        self.output_dir = ""
        self.build_tools_dir = ""
        self.tools: Dict = {}

        self.keep_temp = False

        # resources
        self.icon_path = ""
        self.assets: List[AssetEntry] = []   # v3.4 rich asset entries

        # motion & media
        self.elements: List[ElementInfo] = []
        self.resource_manager = ResourceManager()

        self.custom_manifest_path = ""

        # automations (v3)
        self.auto_imports = True
        self.auto_perms = True
        self.auto_min_sdk = True


def make_jar_from_dir(classes_dir: Path, jar_path: Path):
    """Zip every .class file under classes_dir into a jar."""
    with zipfile.ZipFile(jar_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in classes_dir.rglob("*"):
            if file.is_file() and file.suffix == ".class":
                arcname = str(file.relative_to(classes_dir)).replace("\\", "/")
                zf.write(str(file), arcname)


def build_apk(cfg: BuildConfig, log_cb=None, stage_cb=None):
    """
    Build the APK. `stage_cb(percent, stage_name)` reports progress.
    Runs entirely on a worker thread — heavy analysis included.
    """
    def stage(pct, name):
        """Report (percent, stage name) progress, never raising."""
        if stage_cb:
            try:
                stage_cb(pct, name)
            except Exception:
                pass

    base_temp = Path(tempfile.mkdtemp(prefix="apkbuild_"))
    try:
        stage(4, "Preparing workspace")

        # ---------------------------------------------------------------
        # v3.3.1 TOOLCHAIN RESOLUTION — probe the configured JDK's real
        # version BEFORE anything runs. A JDK 6/7-era compiler cannot
        # compile -source 1.8 AND cannot run the build-tools jars
        # (d8.jar / apksigner.jar are Java 8+ bytecode), so an old JDK
        # used to break the pipeline in three places at once. This picks
        # the best compiler/runtime available and adjusts the flags.
        jdk = resolve_build_jdk(cfg.jdk_bin, log=log_cb)
        if jdk.jdk_bin and jdk.jdk_bin != (cfg.jdk_bin or ""):
            cfg.jdk_bin = jdk.jdk_bin          # env + jdk_tool follow it
        runtime_java = jdk.java

        env = os.environ.copy()
        if cfg.jdk_bin:
            env["PATH"] = cfg.jdk_bin + os.pathsep + env.get("PATH", "")
            env["JAVA_HOME"] = str(Path(cfg.jdk_bin).parent)

        def jdk_tool(name):
            """Locate a JDK binary: the pinned bin dir first, then PATH."""
            if cfg.jdk_bin:
                for suffix in (".exe", ""):
                    cand = Path(cfg.jdk_bin) / (name + suffix)
                    if cand.exists():
                        return str(cand)
            return find_in_path([name + ".exe", name], env_path=env.get("PATH", ""))

        aapt = cfg.tools.get("aapt")
        aapt2 = cfg.tools.get("aapt2")
        d8 = cfg.tools.get("d8")
        d8_lib_dir = cfg.tools.get("d8_lib_dir")
        zipalign = cfg.tools.get("zipalign")
        apksigner_bat = cfg.tools.get("apksigner_bat")
        apksigner_jar = cfg.tools.get("apksigner_jar")

        if cfg.use_aapt2 and not aapt2:
            raise RuntimeError("aapt2 not found in build-tools")
        if not cfg.use_aapt2 and not aapt:
            if aapt2:
                cfg.use_aapt2 = True
            else:
                raise RuntimeError("Neither aapt nor aapt2 found in build-tools")
        if not d8 and not d8_lib_dir:
            raise RuntimeError("d8 not found in build-tools")
        if not zipalign:
            raise RuntimeError("zipalign not found in build-tools")
        if not (apksigner_bat or apksigner_jar):
            raise RuntimeError("apksigner not found in build-tools")
        if not cfg.android_jar or not Path(cfg.android_jar).exists():
            raise RuntimeError(
                "android.jar not found. Place it in ./androidjar/ next to this "
                "script or set the path in Settings → Advanced.")

        # ---------------------------------------------------------------
        # v3.8 PINNED TOOLCHAIN — android.jar must be API 33 and the
        # build-tools revision exactly 33.0.3, both verified from the
        # artifacts' own files (framework classes / source.properties),
        # never from folder names. A wrong version stops the build HERE,
        # by name, instead of failing later with cryptic tool errors.
        jar_rng = android_jar_api_range(cfg.android_jar)
        if jar_rng is None or not (jar_rng[0] <= REQUIRED_ANDROID_API
                                   <= jar_rng[1]):
            raise RuntimeError(
                f"APK Forge builds against android.jar API {REQUIRED_ANDROID_API}, "
                f"but {cfg.android_jar} is "
                f"{android_jar_api_label(jar_rng)}. Use the one-click installer "
                "(Dashboard → READY TO BUILD? → Install) or set the path in "
                "Settings → Advanced.")
        bt_root = cfg.tools.get("root") or cfg.build_tools_dir
        bt_rev = build_tools_revision(bt_root) if bt_root else None
        if bt_rev != REQUIRED_BUILD_TOOLS:
            raise RuntimeError(
                f"APK Forge builds with Android build-tools {REQUIRED_BUILD_TOOLS}, "
                f"but the build-tools at {bt_root} are "
                f"{bt_rev or 'unversioned'}. Use the one-click installer "
                "(Dashboard → READY TO BUILD? → Install) or set the folder in "
                "Settings → Advanced.")

        work = base_temp / "work"
        src = work / "src"
        res = work / "res"
        gen = work / "gen"
        assets = work / "assets"
        classes_dir = work / "classes"
        dex_out = work / "dex"
        compiled_res = work / "compiled_res"
        out_dir = Path(cfg.output_dir) if cfg.output_dir else (Path.cwd() / "dist")
        out_dir.mkdir(parents=True, exist_ok=True)
        for d in (work, src, res, gen, classes_dir, dex_out):
            d.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------------
        stage(10, "Analyzing Java")
        java_text = cfg.java_text or "// no-op"
        analysis = analyze_java(java_text, cfg.min_sdk, cfg.permissions)

        if cfg.auto_imports and analysis.missing_imports:
            java_text, added = auto_fix_imports(java_text)
            if added and log_cb:
                log_cb(f"[{log_time()}] [auto] Auto-imports added ({len(added)}): "
                        + ", ".join(a.split('.')[-1] for a in added[:8])
                        + (" …" if len(added) > 8 else ""))

        if analysis.required_min_sdk and analysis.required_min_sdk > cfg.min_sdk:
            if cfg.auto_min_sdk:
                cfg.min_sdk = analysis.required_min_sdk
                if log_cb:
                    log_cb(f"[{log_time()}] [auto] minSdk auto-raised to {cfg.min_sdk} "
                           f"(code uses APIs that require it)")
            elif log_cb:
                log_cb(f"[{log_time()}] [warn] Code needs minSdk ≥ {analysis.required_min_sdk} "
                       f"but current setting is {cfg.min_sdk} — the APK may crash on "
                       f"older devices")

        if cfg.auto_perms and analysis.suggested_permissions:
            for perm in analysis.suggested_permissions:
                if perm not in cfg.permissions:
                    cfg.permissions.append(perm)
            if log_cb:
                log_cb(f"[{log_time()}] [auto] Auto-permissions enabled: "
                        + ", ".join(p.split(".")[-1] for p in analysis.suggested_permissions))

        if analysis.package:
            cfg.package = analysis.package
        if analysis.launcher:
            cfg.activity_name = analysis.launcher

        stage(16, "Injecting motion & media")
        if cfg.elements or cfg.resource_manager.resources:
            java_text = inject_animations_and_media(
                java_text, cfg.elements, cfg.resource_manager, cfg.package, log_cb)

        stage(22, "Writing Java sources")
        units = split_java_units(java_text, analysis, cfg.package,
                                 cfg.activity_name)
        if len(units) > 1 and log_cb:
            log_cb(f"[{log_time()}] [auto] All-in-one splitter: {len(units)} .java files "
                   f"({', '.join(name for name, _ in units[:6])}"
                   f"{' …' if len(units) > 6 else ''})")
        for unit_name, unit_code in units:
            pkg_path = src / Path(cfg.package.replace(".", "/"))
            pkg_path.mkdir(parents=True, exist_ok=True)
            (pkg_path / unit_name).write_text(unit_code, encoding="utf-8")

        # ---------------------------------------------------------------
        stage(26, "Collecting resources")
        has_icon = False
        if cfg.icon_path and Path(cfg.icon_path).exists():
            has_icon = create_app_icons(cfg.icon_path, res, log_cb)
        # v3.4 — the full asset engine: assets/ + res/drawable + res/raw,
        # junk-filtered, collision-proof, size-accounted
        staged_assets = stage_assets(cfg.assets, work, res, log_cb)
        if staged_assets.files_staged and log_cb:
            parts = [f"{staged_assets.files_staged} file(s)",
                     format_size(staged_assets.bytes_staged)]
            if staged_assets.drawables:
                parts.append(f"{len(staged_assets.drawables)} drawable(s)")
            if staged_assets.raws:
                parts.append(f"{len(staged_assets.raws)} raw(s)")
            if staged_assets.junk_skipped:
                parts.append(f"{staged_assets.junk_skipped} junk filtered")
            log_cb(f"[{log_time()}] [auto] Assets staged: " + " · ".join(parts))
        # v3.4 — cross-check code references against what ACTUALLY got staged
        for w in asset_reference_warnings(java_text, staged_assets):
            if log_cb:
                log_cb(f"[{log_time()}] [warn] {w}")
        if cfg.elements:
            write_animation_resources(res, cfg.elements, log_cb)
            cfg.resource_manager.copy_resources(res, log_cb)
        write_default_resources(res, cfg.app_name)

        # manifest (custom import supported)
        manifest_path = work / "AndroidManifest.xml"
        if cfg.custom_manifest_path and Path(cfg.custom_manifest_path).exists():
            shutil.copy2(cfg.custom_manifest_path, manifest_path)
            if log_cb:
                log_cb(f"[{log_time()}] Using custom manifest: {cfg.custom_manifest_path}")
            try:
                tree = ET.parse(manifest_path)
                cfg.package = tree.getroot().get("package", cfg.package)
            except Exception:
                pass
        else:
            write_manifest(manifest_path, {
                "package": cfg.package,
                "app_name": cfg.app_name,
                "activity_name": cfg.activity_name,
                "version_code": cfg.version_code,
                "version_name": cfg.version_name,
                "min_sdk": cfg.min_sdk,
                "target_sdk": cfg.target_sdk,
                "permissions": cfg.permissions,
                "has_icon": has_icon,
            }, analysis)

        # ---------------------------------------------------------------
        # v3.2 CRITICAL ORDERING FIX: resources are built (and R.java emitted)
        # BEFORE javac in BOTH modes. With aapt2 the compile+link step used to
        # run at PACKAGING time — after the compiler — so every R.* reference
        # in the Java failed to compile. The linked APK is kept and reused.
        stage(32, "Building resources & R.java")
        unsigned_unaligned = work / "unsigned_unaligned.apk"
        aapt2_apk_ready = False
        if cfg.use_aapt2 and aapt2:
            compiled_res.mkdir(parents=True, exist_ok=True)
            rc, out = run_exe([aapt2, "compile", "-o", str(compiled_res),
                               "--dir", str(res)], cwd=str(work), env=env, log_cb=log_cb)
            if rc != 0:
                raise RuntimeError("aapt2 compile failed")
            res_flats = [str(p) for p in compiled_res.rglob("*.flat")]
            cmd = [aapt2, "link",
                   "-o", str(unsigned_unaligned),
                   "-I", str(cfg.android_jar),
                   "--java", str(gen),
                   "--min-sdk-version", str(cfg.min_sdk),
                   "--target-sdk-version", str(cfg.target_sdk),
                   "--version-code", str(cfg.version_code),
                   "--version-name", str(cfg.version_name),
                   "--manifest", str(manifest_path)]
            if assets.exists() and any(assets.iterdir()):
                cmd.extend(["-A", str(assets)])
            rc, out = run_exe(cmd + res_flats, cwd=str(work), env=env, log_cb=log_cb)
            if rc != 0:
                raise RuntimeError("aapt2 link failed")
            aapt2_apk_ready = True
            if log_cb:
                log_cb(f"[{log_time()}] [ok] Resources linked & R.java generated — "
                       f"R.drawable/R.raw/R.anim/R.string references now compile")
        elif aapt:
            rc, out = run_exe([aapt, "package", "-f",
                               "-M", str(manifest_path),
                               "-S", str(res),
                               "-I", str(cfg.android_jar),
                               "-J", str(gen)], cwd=str(work), env=env, log_cb=log_cb)
            if rc != 0:
                if log_cb:
                    log_cb(f"[{log_time()}] [warn] R.java generation failed (continuing)")
            else:
                if log_cb:
                    log_cb(f"[{log_time()}] [ok] R.java generated — R.drawable/R.raw/"
                           f"R.anim/R.string references now compile")

        # ---------------------------------------------------------------
        stage(38, "Compiling Java")
        javac = jdk.javac or jdk_tool("javac")
        if not javac:
            raise RuntimeError("javac not found. Install a JDK and/or set the JDK bin "
                               "path in Settings → Advanced.")

        source_files = [str(p) for p in src.rglob("*.java")]
        source_files += [str(p) for p in gen.rglob("*.java")]
        if not source_files:
            raise RuntimeError("No Java sources were produced")

        # v3.8: resolve_build_jdk already guarantees the pinned JDK 17 and
        # the pin checks above guarantee an API 33 android.jar — the class
        # file readability dance of v3.3.1 is unreachable by construction.

        javac_args = [
            javac,
            "-J-Duser.language=en",
            "-source", jdk.source_target(), "-target", jdk.source_target(),
            "-encoding", "UTF-8",
            "-nowarn", "-proc:none",
            "-classpath", str(cfg.android_jar),
            "-d", str(classes_dir),
        ]
        rc, out = run_exe(javac_args + source_files, cwd=str(work), env=env, log_cb=log_cb)
        if rc != 0:
            hints = friendly_javac_errors(out)
            if hints:
                raise RuntimeError("javac failed:\n" + "\n".join(hints))
            raise RuntimeError("javac failed — see the console for the raw output")

        classes_jar = work / "classes.jar"
        make_jar_from_dir(classes_dir, classes_jar)

        # ---------------------------------------------------------------
        stage(58, "Generating DEX")
        min_api_str = str(cfg.min_sdk)
        java = runtime_java or jdk_tool("java")

        d8_ok = False
        if java and d8_lib_dir and Path(d8_lib_dir).is_dir():
            cp = str(Path(d8_lib_dir) / "*")
            rc, out = run_exe([
                java, "-cp", cp, "com.android.tools.r8.D8",
                "--min-api", min_api_str,
                "--lib", str(cfg.android_jar),
                "--output", str(dex_out),
                str(classes_jar),
            ], cwd=str(work), env=env, log_cb=log_cb)
            d8_ok = (rc == 0)
            if not d8_ok and log_cb:
                log_cb(f"[{log_time()}] D8 via java -cp failed, falling back…")

        if not d8_ok:
            if not d8:
                raise RuntimeError("d8 not found and cannot call D8 main class.")
            d8_args = ["--min-api", min_api_str,
                       "--lib", str(cfg.android_jar),
                       "--output", str(dex_out),
                       str(classes_jar)]
            if d8.lower().endswith((".bat", ".cmd")):
                rc, out = run_bat(d8, d8_args, cwd=str(work), env=env, log_cb=log_cb)
            else:
                rc, out = run_exe([d8] + d8_args, cwd=str(work), env=env, log_cb=log_cb)
            if rc != 0:
                hint = friendly_tool_error(out, "d8")
                raise RuntimeError(hint or "d8 failed")

        dex_file = next(Path(dex_out).glob("classes.dex"), None)
        if not dex_file:
            raise RuntimeError("d8 did not produce classes.dex")

        # ---------------------------------------------------------------
        stage(74, "Packaging APK")
        if not aapt2_apk_ready:
            # aapt v1: package now (aapt2 already produced the linked APK above)
            cmd = [aapt, "package", "-f",
                   "-M", str(manifest_path),
                   "-I", str(cfg.android_jar),
                   "-S", str(res),
                   "-F", str(unsigned_unaligned)]
            if assets.exists() and any(assets.iterdir()):
                cmd.extend(["-A", str(assets)])
            rc, out = run_exe(cmd, cwd=str(work), env=env, log_cb=log_cb)
            if rc != 0:
                raise RuntimeError("aapt package failed")

        with zipfile.ZipFile(unsigned_unaligned, "a", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(dex_file, "classes.dex")

        stage(86, "Aligning APK")
        unsigned_aligned = work / "unsigned_aligned.apk"
        rc, out = run_exe([zipalign, "-f", "4", str(unsigned_unaligned), str(unsigned_aligned)],
                          cwd=str(work), env=env, log_cb=log_cb)
        if rc != 0:
            raise RuntimeError("zipalign failed")

        stage(92, "Signing APK")
        ks_path = cfg.keystore_path or str(out_dir / "debug.keystore")
        if not Path(ks_path).exists():
            keytool = jdk_tool("keytool")
            if not keytool:
                raise RuntimeError("keytool not found to generate a debug keystore. "
                                   "Install a JDK and/or set the JDK bin path.")
            rc, out = run_exe([
                keytool, "-genkey", "-v",
                "-keystore", ks_path,
                "-storepass", cfg.keystore_pass,
                "-alias", cfg.key_alias,
                "-keypass", cfg.key_pass,
                "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
                "-dname", "CN=Android Debug,O=Android,C=US",
            ], cwd=str(work), env=env, log_cb=log_cb)
            if rc != 0:
                raise RuntimeError("Failed to generate keystore")

        final_apk = out_dir / f"{cfg.activity_name}-{cfg.version_name}.apk"
        sign_args = ["sign",
                     "--ks", ks_path,
                     "--ks-key-alias", cfg.key_alias,
                     "--ks-pass", f"pass:{cfg.keystore_pass}",
                     "--key-pass", f"pass:{cfg.key_pass}",
                     "--out", str(final_apk),
                     str(unsigned_aligned)]
        if java and apksigner_jar and Path(apksigner_jar).exists():
            rc, out = run_exe([java, "-jar", apksigner_jar] + sign_args,
                              cwd=str(work), env=env, log_cb=log_cb)
        elif apksigner_bat and Path(apksigner_bat).exists():
            rc, out = run_bat(apksigner_bat, sign_args, cwd=str(work), env=env, log_cb=log_cb)
        else:
            raise RuntimeError("No suitable apksigner found (jar or bat)")
        if rc != 0:
            hint = friendly_tool_error(out, "apksigner")
            raise RuntimeError(hint or "apksigner failed")

        stage(100, "Complete")
        if log_cb:
            log_cb(f"[{log_time()}] [ok] Success! APK: {final_apk}")
            log_cb(f"[{log_time()}] Components — activities: {len(analysis.activities)}, "
                   f"services: {len(analysis.services)}, receivers: {len(analysis.receivers)}; "
                   f"minSdk {cfg.min_sdk}, permissions {len(cfg.permissions)}")

        return True, str(final_apk)
    except Exception as e:
        if log_cb:
            log_cb(f"[{log_time()}] ERROR: {e}")
        return False, str(e)
    finally:
        try:
            if not getattr(cfg, "keep_temp", False):
                shutil.rmtree(base_temp, ignore_errors=True)
        except Exception:
            pass


def export_java_code(java_code: str, output_path: str) -> bool:
    """Save Java source text to a file, returning success."""
    try:
        Path(output_path).write_text(java_code, encoding="utf-8")
        return True
    except Exception as e:
        print(f"Error saving Java code: {e}")
        return False


def parse_manifest(manifest_path):
    """Parse an AndroidManifest.xml and return a dictionary of important fields"""
    ns = "http://schemas.android.com/apk/res/android"
    ET.register_namespace("android", ns)
    tree = ET.parse(manifest_path)
    root = tree.getroot()
    package = root.get("package", "")
    vers_code = root.get(f"{{{ns}}}versionCode", "")
    vers_name = root.get(f"{{{ns}}}versionName", "")

    uses_sdk = root.find("uses-sdk")
    min_sdk = uses_sdk.get(f"{{{ns}}}minSdkVersion") if uses_sdk is not None else ""
    target_sdk = uses_sdk.get(f"{{{ns}}}targetSdkVersion") if uses_sdk is not None else ""

    permissions = [elem.get(f"{{{ns}}}name") for elem in root.findall("uses-permission")
                   if elem.get(f"{{{ns}}}name")]

    application = root.find("application")
    app_label = application.get(f"{{{ns}}}label") if application is not None else ""
    activity = application.find("activity") if application is not None else None
    activity_name = ""
    if activity is not None:
        activity_name = activity.get(f"{{{ns}}}name", "")
        if activity_name.startswith("."):
            activity_name = activity_name[1:]

    return {
        "package": package,
        "version_code": vers_code,
        "version_name": vers_name,
        "min_sdk": min_sdk,
        "target_sdk": target_sdk,
        "permissions": permissions,
        "app_name": app_label,
        "activity_name": activity_name,
    }


# ---------------------------------------------------------------------------
# GUI — THE QUANTUM INTERFACE
# ---------------------------------------------------------------------------
# Native-Qt animation stack (QPropertyAnimation / QVariantAnimation /
# QGraphicsEffect) delivers web-workspace-grade motion with zero extra
# dependencies: animated page transitions, toasts, glowing buttons,
# shimmer progress, ring gauges, count-up stats and a command palette.

if HAS_QT:

    # ---------------------------------------------------------------------------
    # The Quantum theme — Razer-inspired black + neon green
    # ---------------------------------------------------------------------------
    COLORS = {
        "bg": "#0c0d0c",
        "panel": "#141514",
        "panel2": "#101110",
        "line": "#232523",
        "green": "#44d62c",
        "green_bright": "#54e83c",
        "green_dim": "#1c2e18",
        "green_dark": "#12240f",
        "text": "#e8e8e6",
        "muted": "#9a9c98",
        "faint": "#6f736e",
        "danger": "#ff7a7a",
        "warn": "#ffb454",
    }

    THEME_QSS = """
    QWidget { background: #0c0d0c; color: #e8e8e6; font-family: "Segoe UI", "Arial", sans-serif; font-size: 13px; }
    QMainWindow, QDialog { background: #0c0d0c; }
    QToolTip { background-color: #141514; color: #e8e8e6; border: 1px solid #2a2c2a; padding: 6px; }

    /* ---------- Sidebar ---------- */
    QFrame#sidebar { background: #0e0f0d; border-right: 1px solid #1a1c1a; }
    QLabel#logo { background: transparent; }
    QPushButton#nav { background: transparent; border: none; border-radius: 9px; padding: 10px 14px;
                      color: #9a9c98; text-align: left; font-size: 13px; }
    QPushButton#nav:hover { background: #171917; color: #d8dad6; }
    QPushButton#nav:checked { background: #16210f; color: #44d62c; font-weight: 700; }

    /* ---------- Top bar & dock ---------- */
    QFrame#topbar { background: #0c0d0c; border-bottom: 1px solid #1a1c1a; }
    QLabel#crumb { color: #6f736e; font-size: 11px; letter-spacing: 1px; }
    QFrame#dock { background: #101110; border: 1px solid #1f211f; border-radius: 12px; }
    QLabel#dockTitle { color: #9a9c98; font-size: 11px; font-weight: 700; letter-spacing: 1px; background: transparent; }

    /* ---------- Cards & typography ---------- */
    QFrame#card { background: #141514; border: 1px solid #232523; border-radius: 12px; }
    QFrame#card:hover { border: 1px solid #2c312c; }
    QLabel#pageTitle { color: #f2f4ef; font-size: 23px; font-weight: 800; background: transparent; }
    QLabel#cardTitle { color: #e8e8e6; font-size: 15px; font-weight: 700; background: transparent; }
    QLabel#cardSection { color: #44d62c; font-size: 11px; font-weight: 700; letter-spacing: 1px; background: transparent; }
    QLabel#muted { color: #9a9c98; background: transparent; }
    QLabel#tiny { color: #6f736e; font-size: 11px; background: transparent; }
    QLabel#kvKey { color: #9a9c98; font-size: 12px; background: transparent; }
    QLabel#kvValue { color: #e8e8e6; font-size: 12px; font-weight: 600; background: transparent; }
    QLabel#kbd { background: #191a19; border: 1px solid #2a2c2a; border-radius: 5px; padding: 2px 7px;
                 color: #9a9c98; font-size: 11px; font-family: "Consolas", monospace; }
    QFrame#hline { color: #1f211f; background: #1f211f; max-height: 1px; border: none; }

    /* ---------- Status pills ---------- */
    QLabel#pill { border-radius: 9px; padding: 3px 10px; font-size: 11px; font-weight: 700; background: transparent; }
    QLabel#pill[state="ok"]    { background: #12240f; color: #44d62c; border: 1px solid #2c4a24; }
    QLabel#pill[state="warn"]  { background: #2a1f0d; color: #ffb454; border: 1px solid #4a3717; }
    QLabel#pill[state="bad"]   { background: #2a0f0f; color: #ff7a7a; border: 1px solid #4a2020; }
    QLabel#pill[state="muted"] { background: #1a1c1a; color: #9a9c98; border: 1px solid #262826; }
    QLabel#pill[state="green"] { background: #44d62c; color: #07230b; border: 1px solid #44d62c; }

    /* ---------- Buttons ---------- */
    QPushButton { background: #191a19; color: #d8dad6; border: 1px solid #2a2c2a; border-radius: 8px;
                  padding: 8px 14px; font-size: 12px; }
    QPushButton:hover { border-color: #3a3d3a; background: #1e201e; }
    QPushButton:pressed { background: #141514; }
    QPushButton:disabled { color: #5c6058; border-color: #222422; background: #141514; }
    QPushButton:focus { border: 1px solid #2f5427; }
    QPushButton#primary { background: #44d62c; color: #07230b; border: 1px solid #44d62c;
                          font-weight: 800; font-size: 13px; }
    QPushButton#primary:hover { background: #54e83c; border-color: #54e83c; }
    QPushButton#primary:pressed { background: #3bc226; }
    QPushButton#primary:disabled { background: #1e2f1a; color: #4e6a47; border-color: #243521; }
    QPushButton#danger { color: #ff7a7a; border-color: #3d2222; background: #171212; }
    QPushButton#danger:hover { background: #241414; border-color: #553030; }
    QPushButton#ghost { background: transparent; }
    QPushButton#ghost:hover { background: #191a19; }
    QPushButton#mini { padding: 4px 10px; font-size: 11px; border-radius: 6px; }
    QPushButton#buildBtn { background: #44d62c; color: #07230b; border: 1px solid #44d62c;
                           font-weight: 800; font-size: 14px; letter-spacing: 1px; border-radius: 10px; }
    QPushButton#buildBtn:hover { background: #54e83c; }
    QPushButton#buildBtn:pressed { background: #3bc226; }
    QPushButton#buildBtn:disabled { background: #1e2f1a; color: #4e6a47; border-color: #243521; }

    /* ---------- Animation gallery chips ---------- */
    QPushButton#chip { background: #101110; border: 1px solid #262826; border-radius: 16px;
                       padding: 8px 14px; color: #c9ccc6; font-size: 12px; }
    QPushButton#chip:hover { border-color: #3a3d3a; }
    QPushButton#chip:checked { background: #12240f; border: 1px solid #44d62c; color: #44d62c; font-weight: 700; }

    /* ---------- Inputs ---------- */
    QLineEdit, QPlainTextEdit, QTextEdit { background: #0f100f; border: 1px solid #2a2c2a; border-radius: 8px;
                                            padding: 8px 10px; color: #e8e8e6; selection-background-color: #44d62c;
                                            selection-color: #07230b; }
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus { border: 1px solid #44d62c; }
    QLineEdit:disabled { color: #5c6058; }
    QPlainTextEdit#codeEdit, QTextEdit#codeEdit { background: #0a0b0a; border: 1px solid #232523; border-radius: 10px;
            font-family: "Consolas", "Cascadia Mono", "Courier New", monospace; font-size: 13px; color: #dfe3dc; }
    QPlainTextEdit#console { background: #0a0b0a; border: 1px solid #232523; border-radius: 10px;
            font-family: "Consolas", "Cascadia Mono", monospace; font-size: 12px; color: #c9ccc6; }
    QWidget#linenumbers { background: #0a0b0a; border: 1px solid #232523; border-top-left-radius: 10px;
            border-bottom-left-radius: 10px; color: #4e524c; font-family: "Consolas", monospace; font-size: 12px; }

    QSpinBox, QDoubleSpinBox { background: #0f100f; border: 1px solid #2a2c2a; border-radius: 8px;
                                padding: 6px 10px; color: #e8e8e6; }
    QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #44d62c; }
    QSpinBox::up-button, QSpinBox::down-button { background: #191a19; border: none; width: 18px; }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #232523; }

    QComboBox { background: #0f100f; border: 1px solid #2a2c2a; border-radius: 8px; padding: 8px 12px;
                color: #e8e8e6; }
    QComboBox:hover { border-color: #3a3d3a; }
    QComboBox:focus { border-color: #44d62c; }
    QComboBox::drop-down { border: none; width: 26px; }
    QComboBox QAbstractItemView { background: #141514; border: 1px solid #2a2c2a; color: #e8e8e6;
                                  selection-background-color: #1c2e18; selection-color: #44d62c; outline: none; }

    QCheckBox { color: #c9ccc6; spacing: 10px; background: transparent; }
    QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 1px solid #2a2c2a; background: #0f100f; }
    QCheckBox::indicator:hover { border-color: #44d62c; }
    QCheckBox::indicator:checked { background: #44d62c; border-color: #44d62c; }
    QCheckBox:disabled { color: #5c6058; }

    QSlider::groove:horizontal { height: 6px; background: #232523; border-radius: 3px; }
    QSlider::sub-page:horizontal { background: #44d62c; border-radius: 3px; }
    QSlider::handle:horizontal { background: #44d62c; width: 14px; margin: -5px 0; border-radius: 7px; }
    QSlider::handle:horizontal:hover { background: #54e83c; }

    /* ---------- Lists & tables ---------- */
    QListWidget { background: #0f100f; border: 1px solid #232523; border-radius: 10px; color: #e8e8e6; outline: none; }
    QListWidget::item { padding: 8px; border-radius: 6px; }
    QListWidget::item:selected { background: #1c2e18; color: #e8ffe0; }
    QListWidget::item:hover { background: #161716; }

    QTableWidget { background: #0f100f; alternate-background-color: #121312; gridline-color: #1c1e1c;
                   border: 1px solid #232523; border-radius: 10px; color: #dfe3dc;
                   selection-background-color: #1c2e18; selection-color: #e8ffe0; outline: none; }
    QTableWidget::item { padding: 6px; }
    QTableWidget::item:selected { background: #1c2e18; color: #e8ffe0; }
    QHeaderView::section { background: #141514; color: #9a9c98; border: none; border-bottom: 1px solid #232523;
                           border-right: 1px solid #191b19; padding: 8px 10px; font-size: 11px; font-weight: 700; }
    QTableCornerButton::section { background: #141514; border: none; }

    /* ---------- Menus ---------- */
    QMenu { background: #141514; border: 1px solid #2a2c2a; border-radius: 10px; padding: 6px; }
    QMenu::item { padding: 8px 24px; border-radius: 6px; color: #d8dad6; }
    QMenu::item:selected { background: #1c2e18; color: #44d62c; }
    QMenu::separator { height: 1px; background: #232523; margin: 4px 8px; }

    /* ---------- Progress ---------- */
    QProgressBar { background: #0f100f; border: 1px solid #232523; border-radius: 5px; text-align: center;
                   color: #9a9c98; font-size: 10px; }
    QProgressBar::chunk { background: #44d62c; border-radius: 5px; }

    /* ---------- Scrollbars ---------- */
    QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
    QScrollBar::handle:vertical { background: #2a2c2a; border-radius: 5px; min-height: 30px; }
    QScrollBar::handle:vertical:hover { background: #3a3d3a; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
    QScrollBar::handle:horizontal { background: #2a2c2a; border-radius: 5px; min-width: 30px; }
    QScrollBar::handle:horizontal:hover { background: #3a3d3a; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
    QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

    /* ---------- Misc ---------- */
    QStatusBar { background: #0c0d0c; border-top: 1px solid #1f211f; color: #9a9c98; }
    QStatusBar QLabel { color: #6f736e; font-size: 11px; }
    QGroupBox { background: #141514; border: 1px solid #232523; border-radius: 12px; margin-top: 14px;
                padding: 14px; color: #e8e8e6; font-weight: 700; }
    QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: #44d62c; }
    QMessageBox { background: #141514; }
    QMessageBox QLabel { color: #e8e8e6; background: transparent; }
    QSplitter::handle { background: #1a1c1a; }

    /* ---------- v3.6 Data installer ---------- */
    QFrame#installRow { background: #101110; border: 1px solid #232523; border-radius: 10px; }
    QFrame#installRow:hover { border: 1px solid #2c312c; }
    QLabel#installName { color: #e8e8e6; font-size: 13px; font-weight: 700; background: transparent; }
    QLabel#installDesc { color: #9a9c98; font-size: 11px; background: transparent; }
    QLabel#installStatus { color: #6f736e; font-size: 11px; background: transparent; }
    QLabel#installPath { color: #44d62c; font-size: 11px;
                         font-family: "Consolas", monospace; background: transparent; }
    QProgressBar#installBar { background: #0f100f; border: 1px solid #2a2c2a; border-radius: 8px;
                              max-height: 14px; text-align: center; color: #e8e8e6; font-size: 10px; }
    QProgressBar#installBar::chunk { background: #44d62c; border-radius: 7px; }
    QPushButton#installMini { background: #12240f; color: #44d62c; border: 1px solid #2c4a24;
                              padding: 4px 10px; font-size: 11px; border-radius: 6px; font-weight: 700; }
    QPushButton#installMini:hover { background: #1a3512; border-color: #44d62c; }
    QPushButton#installMini:pressed { background: #142b0d; }
    QPushButton#installMini:disabled { color: #4e6a47; border-color: #243521; background: #141514; }
    QPushButton#autoPathBtn { background: #12240f; color: #44d62c; border: 1px solid #2c4a24;
                              padding: 4px 10px; font-size: 11px; border-radius: 6px; font-weight: 700; }
    QPushButton#autoPathBtn:hover { background: #1a3512; border-color: #44d62c; }
    QPushButton#autoPathBtn:pressed { background: #142b0d; }
    QPushButton#autoPathBtn:disabled { color: #4e6a47; border-color: #243521; background: #141514; }
    QPushButton#installBtn { background: #12240f; color: #44d62c; border: 1px solid #2c4a24;
                             border-radius: 9px; padding: 10px 14px; font-weight: 700; font-size: 12px; }
    QPushButton#installBtn:hover { background: #1a3512; border-color: #44d62c; }
    QPushButton#installBtn:pressed { background: #142b0d; }
    QPushButton#installBtn:disabled { color: #4e6a47; border-color: #243521; background: #141514; }
    QLabel#installBig { color: #f2f4ef; font-size: 20px; font-weight: 800; background: transparent; }
    """


    # ---------------------------------------------------------------------------
    # Toast notifications
    # ---------------------------------------------------------------------------
    class Toast(QtWidgets.QWidget):
        """Non-blocking toast that SLIDES IN from the right edge and glides
        out again (v3.2: real position animation + fade — the old version only
        faded, which read as "no animation at all")."""

        _by_parent: Dict[int, List["Toast"]] = {}

        KIND_STYLES = {
            "info":  ("#1a1c1a", "#9a9c98", "#262826"),
            "ok":    ("#12240f", "#44d62c", "#2c4a24"),
            "warn":  ("#2a1f0d", "#ffb454", "#4a3717"),
            "error": ("#2a0f0f", "#ff7a7a", "#4a2020"),
        }

        def __init__(self, parent: QtWidgets.QWidget, text: str, kind: str = "info",
                     timeout_ms: int = 3400):
            """Build the toast UI, its owned dismissal timer and fade effect."""
            super().__init__(parent)
            self._timeout = timeout_ms
            self._closing = False
            self._anim = None
            bg, fg, border = self.KIND_STYLES.get(kind, self.KIND_STYLES["info"])

            lay = QtWidgets.QHBoxLayout(self)
            lay.setContentsMargins(16, 10, 16, 10)
            label = QtWidgets.QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet(
                f"color:{fg}; background:transparent; font-size:12px; font-weight:600;")
            icon = {"ok": "OK", "warn": "!", "error": "X", "info": "i"}.get(kind, "i")
            ic = QtWidgets.QLabel(icon)
            ic.setStyleSheet(
                f"color:{fg}; background:transparent; font-size:14px; font-weight:800;")
            lay.addWidget(ic)
            lay.addWidget(label)
            self.setStyleSheet(
                f"background:{bg}; border:1px solid {border}; border-radius:10px;")
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.adjustSize()
            if self.width() > 420:
                self.setFixedWidth(420)
                self.adjustSize()

            # v3.1: the dismissal timer is OWNED by the toast — when the widget
            # (or its parent window) is destroyed, the timer dies with it, so
            # the callback can never fire on a deleted widget.
            self._timer = QtCore.QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(self._dismiss)

            # v3.2: opacity starts at ZERO — the slide+fade-in happens in
            # _slide_in() once the toast has been positioned by popup().
            self._fx = QtWidgets.QGraphicsOpacityEffect(self)
            self._fx.setOpacity(0.0)
            self.setGraphicsEffect(self._fx)
            self._timer.start(timeout_ms)

        def _slide_in(self):
            """v3.2: slide in from the right edge + fade in (250 ms)."""
            try:
                end = self.pos()
                pw = self.parentWidget()
                start = QtCore.QPoint((pw.width() if pw else end.x() + 260) + 16, end.y())
                self.move(start)
                slide = QtCore.QPropertyAnimation(self, b"pos", self)
                slide.setDuration(250)
                slide.setStartValue(start)
                slide.setEndValue(end)
                slide.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
                fade = QtCore.QPropertyAnimation(self._fx, b"opacity", self)
                fade.setDuration(250)
                fade.setStartValue(0.0)
                fade.setEndValue(1.0)
                fade.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
                grp = QtCore.QParallelAnimationGroup(self)
                grp.addAnimation(slide)
                grp.addAnimation(fade)
                grp.start()
                self._anim = grp
            except RuntimeError:
                pass

        def _dismiss(self):
            """Animate the toast out (210 ms) and clean up when finished."""
            if self._closing:
                return
            self._closing = True
            try:
                self._timer.stop()
            except RuntimeError:
                return
            try:
                if self._anim is not None:
                    self._anim.stop()
                    self._anim = None
                pw = self.parentWidget()
                off_x = (pw.width() if pw else self.x() + 260) + 16
                fade = QtCore.QPropertyAnimation(self._fx, b"opacity", self)
                fade.setDuration(210)
                fade.setStartValue(1.0)
                fade.setEndValue(0.0)
                slide = QtCore.QPropertyAnimation(self, b"pos", self)
                slide.setDuration(210)
                slide.setStartValue(self.pos())
                slide.setEndValue(QtCore.QPoint(off_x, self.y()))
                slide.setEasingCurve(QtCore.QEasingCurve.Type.InCubic)
                grp = QtCore.QParallelAnimationGroup(self)
                grp.addAnimation(fade)
                grp.addAnimation(slide)
                grp.finished.connect(self._cleanup)
                grp.start()
                self._anim = grp
            except RuntimeError:
                pass

        def _cleanup(self):
            """Unregister the toast, restack siblings and delete the widget."""
            try:
                parent = self.parent()
                lst = Toast._by_parent.get(id(parent), [])
                if self in lst:
                    lst.remove(self)
            except RuntimeError:
                pass                       # parent already gone — nothing to tidy
            try:
                self._relayout_siblings()
            except RuntimeError:
                return                     # the C++ object is already gone
            try:
                self.deleteLater()
            except RuntimeError:
                pass

        def _relayout_siblings(self):
            """Restack the parent's toasts bottom-up along the right edge."""
            parent = self.parent()
            if parent is None:
                return
            lst = Toast._by_parent.get(id(parent), [])
            margin, w_gap = 18, 10
            y = parent.height() - margin
            for t in reversed(lst):
                y -= t.height()
                t.move(parent.width() - t.width() - margin, y)
                y -= w_gap

        @staticmethod
        def popup(parent: QtWidgets.QWidget, text: str, kind: str = "info", timeout_ms: int = 3400):
            """Create, position and reveal a toast on `parent`. (Named `popup` so it
            never shadows QWidget.show().)"""
            if parent is None:
                return
            key = id(parent)
            lst = Toast._by_parent.setdefault(key, [])
            # hard cap of 4 stacked toasts
            while len(lst) >= 4:
                oldest = lst[0]
                lst.pop(0)
                try:
                    oldest._dismiss()
                except RuntimeError:
                    pass
            t = Toast(parent, text, kind, timeout_ms)
            lst.append(t)
            try:
                t._relayout_siblings()
                t.setVisible(True)
                t._slide_in()                 # v3.2: slide in from the right
                t.raise_()
            except RuntimeError:
                pass


    # ---------------------------------------------------------------------------
    # Animated stacked widget — v3.1: INSTANT page switching
    # ---------------------------------------------------------------------------
    class AnimatedStack(QtWidgets.QStackedWidget):
        """
        v3.1 performance note: the old transition rendered a full-page
        screenshot of the outgoing page (widget.grab()) and wrapped whole
        pages in QGraphicsOpacityEffect — both forced expensive full-page
        repaints on every switch. Pages now switch instantly; the motion
        budget lives in the small widgets (toasts, glows, gauges, counts).
        """

        def __init__(self, parent=None):
            """Create the stacked widget (no extra state)."""
            super().__init__(parent)

        def setCurrentIndexAnimated(self, index: int, direction: int = 1):
            """Switch to the given page index immediately."""
            # direction kept for API compatibility; switching is instant.
            if index == self.currentIndex() or not (0 <= index < self.count()):
                return
            self.setCurrentIndex(index)


    # ---------------------------------------------------------------------------
    # v3.2 — CONTROL-LEVEL ENTRANCE ANIMATION (cards fade + rise, staggered)
    # ---------------------------------------------------------------------------
    # Pages switch INSTANTLY (v3.1 perf decision — kept). The visible motion
    # now comes from the page's OWN cards: each fades in over 240 ms with a
    # 45 ms stagger, while the page's top margin animates 16 px → 0 (a
    # subtle "rise"). Effects are DETACHED when the animation finishes, so
    # an idle page paints at full native speed — zero steady-state cost.
    def _collect_cards(lay, out, depth: int = 0):
        """Direct + nested QFrame#card children of a layout (max depth 2)."""
        if lay is None or depth > 2:
            return
        try:
            count = lay.count()
        except RuntimeError:
            return
        for i in range(count):
            try:
                item = lay.itemAt(i)
            except RuntimeError:
                continue
            w = item.widget() if item is not None else None
            if w is not None:
                if isinstance(w, QtWidgets.QFrame) and w.objectName() == "card":
                    out.append(w)
            elif item is not None:
                _collect_cards(item.layout(), out, depth + 1)


    def animate_page_entrance(page) -> None:
        """Fade + rise a page's cards in, staggered. Debounced per page."""
        if page is None:
            return
        try:
            clock = QtCore.QElapsedTimer()
            clock.start()
            msecs = clock.msecsSinceReference()
            last = getattr(page, "_entrance_at", -10_000)
            if msecs - last < 400:
                return                      # debounce: nav spam / double clicks
            page._entrance_at = msecs

            # --- the cards ---
            cards: List[QtWidgets.QWidget] = []
            _collect_cards(getattr(page, "body", None), cards)
            root = page.layout()
            if not cards and root is not None:
                for i in range(root.count()):
                    item = root.itemAt(i)
                    w = item.widget() if item is not None else None
                    if w is not None:
                        cards.append(w)
            if not cards:
                return

            # --- the rise: animate the page's top margin 16 px → home ---
            try:
                root = page.layout()
                if root is not None:
                    lm, tm, rm, bm = root.getContentsMargins()
                    rise = QtCore.QVariantAnimation(page)
                    rise.setDuration(300)
                    rise.setStartValue(float(tm + 16))
                    rise.setEndValue(float(tm))
                    rise.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
                    rise.valueChanged.connect(
                        lambda v, L=lm, T=tm, R=rm, B=bm, lay=root:
                            lay.setContentsMargins(L, max(0, int(round(v))), R, B))
                    root.setContentsMargins(lm, tm + 16, rm, bm)
                    rise.start()
            except Exception:
                pass

            # --- cards fade in, staggered by 45 ms ---
            t0 = 0
            for w in cards[:8]:
                try:
                    fx = QtWidgets.QGraphicsOpacityEffect(w)
                    fx.setOpacity(0.0)
                    w.setGraphicsEffect(fx)
                    anim = QtCore.QPropertyAnimation(fx, b"opacity", w)
                    anim.setDuration(240)
                    anim.setStartValue(0.0)
                    anim.setEndValue(1.0)
                    anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)

                    def _done(target=w):
                        """Drop the effect from a finished card (zero idle cost)."""
                        try:
                            target.setGraphicsEffect(None)   # zero idle cost
                        except RuntimeError:
                            pass
                    anim.finished.connect(_done)
                    QtCore.QTimer.singleShot(t0, lambda a=anim: a.start())
                except RuntimeError:
                    pass
                t0 += 45
        except Exception:
            pass            # animation is ALWAYS best-effort — never break nav


    # ---------------------------------------------------------------------------
    # Count-up label (animated statistics) — v3.1: ONE reused animation
    # ---------------------------------------------------------------------------
    class CountUpLabel(QtWidgets.QLabel):
        """QLabel whose integer value counts up from old to new."""

        def __init__(self, text="", parent=None, suffix: str = ""):
            """Create the label and its single reused count-up animation."""
            super().__init__(text, parent)
            self._value = 0
            self._display = 0.0
            self._suffix = suffix
            # single persistent animation — restarting it never piles up new ones
            self._anim = QtCore.QVariantAnimation(self)
            self._anim.setDuration(550)
            self._anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
            self._anim.valueChanged.connect(self._on_tick)

        def setValue(self, v: int, animate: bool = True):
            """Move to a new integer value, animated unless disabled."""
            v = int(v)
            if v == self._value and int(round(self._display)) == v:
                return                      # nothing to do — don't restart the anim
            self._value = v
            if not animate:
                self._anim.stop()
                self._display = float(v)
                self._render()
                return
            self._anim.stop()
            self._anim.setStartValue(float(self._display))
            self._anim.setEndValue(float(v))
            self._anim.start()

        def _on_tick(self, val):
            """Record the animation tick and re-render."""
            self._display = float(val)
            self._render()

        def _render(self):
            """Show the rounded display value plus suffix."""
            self.setText(f"{int(round(self._display))}{self._suffix}")


    # ---------------------------------------------------------------------------
    # Spinner (rotating arc)
    # ---------------------------------------------------------------------------
    class Spinner(QtWidgets.QWidget):
        """Rotating-arc busy indicator driven by a QTimer."""

        def __init__(self, parent=None, size: int = 26, color: str = "#44d62c"):
            """Create the fixed-size spinner and its rotation timer."""
            super().__init__(parent)
            self.setFixedSize(size, size)
            self._angle = 0
            self._color = QtGui.QColor(color)
            self._timer = QtCore.QTimer(self)
            self._timer.setInterval(30)
            self._timer.timeout.connect(self._tick)

        def _tick(self):
            """Advance the arc angle and repaint."""
            self._angle = (self._angle + 14) % 360
            self.update()

        def start(self):
            """Show the spinner and start rotating."""
            self.show()
            self._timer.start()

        def stop(self):
            """Stop rotating and hide the spinner."""
            self._timer.stop()
            self.hide()

        def paintEvent(self, _e):
            """Paint the track ring and the rotating arc."""
            p = QtGui.QPainter(self)
            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            margin = 3
            rect = QtCore.QRectF(margin, margin, self.width() - 2 * margin,
                                 self.height() - 2 * margin)
            # track
            pen = QtGui.QPen(QtGui.QColor(40, 44, 40), 3)
            pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawArc(rect, 0, 360 * 16)
            # arc
            pen = QtGui.QPen(self._color, 3)
            pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            start = int(-self._angle * 16)
            p.drawArc(rect, start, 100 * 16)
            p.end()


    # ---------------------------------------------------------------------------
    # Shimmer progress bar (sweeping highlight during builds)
    # ---------------------------------------------------------------------------
    class ShimmerBar(QtWidgets.QProgressBar):
        """Progress bar with a looping highlight sweep while active."""

        def __init__(self, parent=None):
            """Create the looping shimmer animation (idle until started)."""
            super().__init__(parent)
            self.setTextVisible(False)
            self._shimmer = 0.0
            self._anim = QtCore.QVariantAnimation(self)
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.setDuration(1100)
            self._anim.setLoopCount(-1)
            self._anim.valueChanged.connect(self._on_shimmer)
            self._active = False

        def _on_shimmer(self, v):
            """Record the sweep phase and repaint."""
            self._shimmer = float(v)
            self.update()

        def start_shimmer(self):
            """Start the looping shimmer sweep."""
            if not self._active:
                self._active = True
                self._anim.start()

        def stop_shimmer(self):
            """Stop the sweep and reset the phase."""
            self._active = False
            self._anim.stop()
            self._shimmer = 0.0
            self.update()

        def paintEvent(self, _e):
            """Paint track, gradient chunk and shimmer sweep."""
            p = QtGui.QPainter(self)
            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            r = QtCore.QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
            # track
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(QtGui.QColor(21, 23, 21))
            p.drawRoundedRect(r, 4, 4)
            # chunk
            w = self.width() * (self.value() / max(1, self.maximum()))
            if w > 0:
                grad = QtGui.QLinearGradient(0, 0, max(1.0, w), 0)
                grad.setColorAt(0.0, QtGui.QColor("#2f9b1f"))
                grad.setColorAt(1.0, QtGui.QColor("#54e83c"))
                p.setBrush(QtGui.QBrush(grad))
                p.drawRoundedRect(QtCore.QRectF(0.5, 0.5, max(3.0, w - 1), self.height() - 1), 4, 4)
            # shimmer sweep
            if self._active and self.value() < self.maximum():
                x = self._shimmer * (self.width() + 60) - 60
                sg = QtGui.QLinearGradient(x, 0, x + 60, 0)
                sg.setColorAt(0.0, QtGui.QColor(255, 255, 255, 0))
                sg.setColorAt(0.5, QtGui.QColor(255, 255, 255, 70))
                sg.setColorAt(1.0, QtGui.QColor(255, 255, 255, 0))
                p.setBrush(QtGui.QBrush(sg))
                p.drawRoundedRect(r, 4, 4)
            p.end()


    # ---------------------------------------------------------------------------
    # Ring gauge (environment readiness) — v3.1: one animation, no label overlap
    # ---------------------------------------------------------------------------
    class RingGauge(QtWidgets.QWidget):
        """Circular readiness gauge. The widget is taller than wide on purpose:
        the sub-label lives in a dedicated strip BELOW the ring, so it can
        never overlap the arc (visible in v3.0 screenshots)."""

        def __init__(self, parent=None, diameter: int = 120, label: str = ""):
            """Create the gauge and its single value animation."""
            super().__init__(parent)
            self._d = diameter
            self.setFixedSize(diameter, diameter + 22)
            self._value = 0.0        # animated display value
            self._target = 0
            self._label = label
            self._sub = ""
            # single persistent animation — setTarget() just restarts it
            self._anim = QtCore.QVariantAnimation(self)
            self._anim.setDuration(700)
            self._anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
            self._anim.valueChanged.connect(self._tick)

        def setTarget(self, pct: int, sub: str = ""):
            """Animate the ring to a clamped percentage with a sub-label."""
            self._target = max(0, min(100, int(pct)))
            self._sub = sub
            self._anim.stop()
            self._anim.setStartValue(self._value)
            self._anim.setEndValue(float(self._target))
            self._anim.start()

        def _tick(self, v):
            """Record the animated value and repaint."""
            self._value = float(v)
            self.update()

        def paintEvent(self, _e):
            """Paint the ring, percentage, label and sub-label strip."""
            p = QtGui.QPainter(self)
            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            w = self._d                 # ring lives in the top square
            h = self.height()
            pen_w = 10
            rect = QtCore.QRectF(pen_w / 2 + 2, pen_w / 2 + 2, w - pen_w - 4, w - pen_w - 4)

            pen = QtGui.QPen(QtGui.QColor(30, 33, 30), pen_w)
            pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawArc(rect, 0, 360 * 16)

            if self._value > 0.5:
                grad = QtGui.QConicalGradient(w / 2, w / 2, 90)
                grad.setColorAt(0.0, QtGui.QColor("#54e83c"))
                grad.setColorAt(1.0, QtGui.QColor("#1e7a12"))
                pen = QtGui.QPen(QtGui.QBrush(grad), pen_w)
                pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
                p.setPen(pen)
                span = int(-self._value / 100.0 * 360 * 16)
                p.drawArc(rect, 90 * 16, span)

            # percentage + label — centered INSIDE the ring
            p.setPen(QtGui.QColor("#f2f4ef"))
            f = QtGui.QFont(self.font())
            f.setBold(True)
            f.setPixelSize(max(14, w // 6))
            p.setFont(f)
            p.drawText(QtCore.QRect(0, w // 2 - w // 5, w, w // 4),
                       QtCore.Qt.AlignmentFlag.AlignCenter,
                       f"{int(round(self._value))}%")

            if self._label:
                p.setPen(QtGui.QColor("#9a9c98"))
                f2 = QtGui.QFont(self.font())
                f2.setPixelSize(max(9, w // 12))
                f2.setBold(True)
                p.setFont(f2)
                p.drawText(QtCore.QRect(0, w // 2 + w // 9, w, w // 7),
                           QtCore.Qt.AlignmentFlag.AlignCenter, self._label.upper())

            # sub-label — dedicated strip BELOW the ring: zero overlap
            if self._sub:
                p.setPen(QtGui.QColor("#6f736e"))
                f3 = QtGui.QFont(self.font())
                f3.setPixelSize(max(8, w // 14))
                p.setFont(f3)
                sub = self._sub
                if len(sub) > 26:
                    sub = sub[:24] + "…"
                p.drawText(
                    QtCore.QRect(0, w + 2, w, h - w - 2),
                    QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter,
                    sub)
            p.end()


    # ---------------------------------------------------------------------------
    # Glow button — v3.2: hover glow + slow "breathing" idle loop
    # ---------------------------------------------------------------------------
    class GlowButton(QtWidgets.QPushButton):
        """Hover glow + optional slow Razer-style BREATHING loop (v3.2).

        The QGraphicsDropShadowEffect is disabled (bypassed by Qt entirely)
        whenever the glow reaches zero, so idle buttons repaint at full native
        speed. Breathing uses ONE looping animation group (two phase
        animations) that is paused while hovering / disabled and resumed on
        leave — never piles up."""

        def __init__(self, text: str = "", color: str = "#44d62c", parent=None,
                     idle_pulse: bool = False):
            """Create the button, its shadow effect and glow animation."""
            super().__init__(text, parent)
            self._color = QtGui.QColor(color)
            self._effect = QtWidgets.QGraphicsDropShadowEffect(self)
            self._effect.setOffset(0, 0)
            self._effect.setBlurRadius(0)
            c = QtGui.QColor(self._color)
            c.setAlpha(0)
            self._effect.setColor(c)
            self._effect.setEnabled(False)          # OFF while idle
            self.setGraphicsEffect(self._effect)
            self._glow = 0.0
            self._idle = idle_pulse
            self._breath = None                     # breathing group (v3.2)
            # single persistent animation — hover in/out just restart it
            self._anim = QtCore.QVariantAnimation(self)
            self._anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
            self._anim.valueChanged.connect(self._set_glow)

        def _set_glow(self, v: float):
            """Apply a glow level; zero disables the shadow effect."""
            self._glow = float(v)
            try:
                if v <= 0.001:
                    self._effect.setEnabled(False)   # idle → zero-cost repaints
                    return
                self._effect.setEnabled(True)
                c = QtGui.QColor(self._color)
                c.setAlpha(int(190 * v))
                self._effect.setColor(c)
                self._effect.setBlurRadius(28 * v)
            except RuntimeError:
                pass

        def _animate_to(self, target: float, duration: int = 260):
            """Animate the glow to target over duration ms."""
            try:
                self._pause_breathing()
                self._anim.stop()
                self._anim.setStartValue(self._glow)
                self._anim.setEndValue(float(target))
                self._anim.setDuration(duration)
                self._anim.start()
            except RuntimeError:
                pass

        # --- v3.2 breathing ---
        def _phase(self, start: float, end: float, ms: int):
            """Build one eased glow phase animation for the breathing loop."""
            a = QtCore.QVariantAnimation(self)
            a.setStartValue(start)
            a.setEndValue(end)
            a.setDuration(ms)
            a.setEasingCurve(QtCore.QEasingCurve.Type.InOutSine)
            a.valueChanged.connect(self._set_glow)
            return a

        def start_breathing(self, intensity: float = 0.34, period_ms: int = 2400):
            """Slow idle glow loop (0 → intensity → 0, forever). ONE group."""
            if self._breath is not None or not self.isEnabled():
                return
            try:
                grp = QtCore.QSequentialAnimationGroup(self)
                grp.setLoopCount(-1)
                grp.addAnimation(self._phase(0.0, intensity, period_ms // 2))
                grp.addAnimation(self._phase(intensity, 0.0, period_ms // 2))
                self._breath = grp
                grp.start()
            except RuntimeError:
                pass

        def _pause_breathing(self):
            """Pause the breathing loop; drop it if it already died."""
            if self._breath is not None:
                try:
                    self._breath.pause()
                except RuntimeError:
                    self._breath = None

        def _resume_breathing(self):
            """Resume breathing when enabled and not hovered."""
            grp = self._breath
            if grp is None or not self.isEnabled() or self.underMouse():
                return
            try:
                grp.resume()
            except RuntimeError:
                self._breath = None

        def stop_breathing(self):
            """Stop and discard the breathing group."""
            if self._breath is not None:
                try:
                    self._breath.stop()
                except RuntimeError:
                    pass
                self._breath = None

        def setEnabled(self, on: bool):
            """Enable/disable and keep glow and breathing consistent."""
            super().setEnabled(on)
            try:
                if on:
                    self._resume_breathing()
                else:
                    # building → glow fully off, breathing paused
                    self._pause_breathing()
                    self._anim.stop()
                    self._set_glow(0.0)
            except RuntimeError:
                pass

        def enterEvent(self, e):
            """Ramp the glow up while hovering."""
            self._animate_to(1.0, 200)      # also pauses breathing
            super().enterEvent(e)

        def leaveEvent(self, e):
            """Ramp the glow down, then resume breathing."""
            self._animate_to(0.0, 420)
            # hand control back to the breathing loop once the ramp finishes
            QtCore.QTimer.singleShot(500, self._resume_breathing)
            super().leaveEvent(e)

        def start_idle_pulse(self):
            """v3.2: the idle animation is now the continuous breathing loop."""
            if not self._idle or not self.isEnabled():
                return
            self.start_breathing()


    # ---------------------------------------------------------------------------
    # Small reusable widgets
    # ---------------------------------------------------------------------------
    class Pill(QtWidgets.QLabel):
        """Colored status pill: ok / warn / bad / muted / green."""

        def __init__(self, text="", state="muted", parent=None):
            """Create the pill with its initial state property."""
            super().__init__(text, parent)
            self.setObjectName("pill")
            self._state = state
            self.setProperty("state", state)

        def setState(self, state):
            """Switch the state property and re-polish the style."""
            self._state = state
            self.setProperty("state", state)
            self.style().unpolish(self)
            self.style().polish(self)


    def make_card(title: str = "", subtitle: str = ""):
        """Create a styled card frame. Returns (card, body_layout)."""
        card = QtWidgets.QFrame()
        card.setObjectName("card")
        lay = QtWidgets.QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)
        if title:
            t = QtWidgets.QLabel(title)
            t.setObjectName("cardTitle")
            lay.addWidget(t)
        if subtitle:
            s = QtWidgets.QLabel(subtitle)
            s.setObjectName("muted")
            s.setWordWrap(True)
            lay.addWidget(s)
        return card, lay


    def scroll_page(page: QtWidgets.QWidget) -> QtWidgets.QScrollArea:
        """Wrap ``page`` in a frameless, widget-resizable scroll area."""
        sc = QtWidgets.QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        sc.setWidget(page)
        return sc


    def kv_row(key: str, value: str = ""):
        """Build one key/value label row; returns (row, value_label)."""
        row = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        k = QtWidgets.QLabel(key)
        k.setObjectName("kvKey")
        v = QtWidgets.QLabel(value)
        v.setObjectName("kvValue")
        v.setWordWrap(True)
        h.addWidget(k)
        h.addWidget(v, 1)
        return row, v


    def clear_layout(lay):
        """Empty a layout: widgets are detached from the widget tree
        IMMEDIATELY (hidden + re-parented to None) and then deleted, so the
        next refresh never paints stale rows."""
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                w.deleteLater()


    def elide_path(p: str, maxlen: int = 46) -> str:
        """Truncate long paths to ``maxlen`` characters with a leading ellipsis."""
        if not p:
            return "—"
        if len(p) <= maxlen:
            return p
        return "…" + p[-(maxlen - 1):]


    def kbd(text: str) -> QtWidgets.QLabel:
        """Create a styled keyboard-key label."""
        l = QtWidgets.QLabel(text)
        l.setObjectName("kbd")
        l.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        return l


    # ---------------------------------------------------------------------------
    # Command palette (Ctrl+K) — v3.1: complete layout, keyboard nav, runs once
    # ---------------------------------------------------------------------------
    class CommandPalette(QtWidgets.QDialog):
        """Fuzzy-searchable command palette à la VS Code (Ctrl+K).

        v3.1 fixes:
          • the dialog now has a REAL top-level layout — the card frame fills
            the popup correctly (the old dialog left the frame unmanaged, so
            the palette rendered incomplete / cut off);
          • a command runs EXACTLY once (double-click / Enter / click could
            fire it twice);
          • ↑ ↓ PgUp PgDn Home End navigate, Tab completes, Esc closes;
          • the width adapts to the screen (no more overflow on laptops).
        """

        def __init__(self, parent, actions: List[dict]):
            """Build the palette UI and run the initial filter."""
            super().__init__(parent)
            self.setWindowFlags(QtCore.Qt.WindowType.Popup)
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setModal(True)
            self.actions = actions
            self.result_actions: List[dict] = []
            self._done = False            # single-run guard

            # --- top-level layout (the missing piece in v3.0) ---
            top = QtWidgets.QVBoxLayout(self)
            top.setContentsMargins(0, 0, 0, 0)

            frame = QtWidgets.QFrame(self)
            frame.setObjectName("card")
            top.addWidget(frame)

            lay = QtWidgets.QVBoxLayout(frame)
            lay.setContentsMargins(12, 12, 12, 12)
            lay.setSpacing(8)

            header = QtWidgets.QLabel("COMMAND PALETTE")
            header.setObjectName("cardSection")
            lay.addWidget(header)

            self.edit = QtWidgets.QLineEdit()
            self.edit.setPlaceholderText("Type a command… (Build, Insert, Go to, Fix…)")
            self.edit.setClearButtonEnabled(True)
            lay.addWidget(self.edit)

            self.list = QtWidgets.QListWidget()
            self.list.setMinimumHeight(180)
            self.list.setMaximumHeight(340)
            self.list.setItemDelegate(QtWidgets.QStyledItemDelegate(self.list))
            lay.addWidget(self.list, 1)

            hint = QtWidgets.QLabel("Up/Down navigate   Enter run   Tab complete   Esc close")
            hint.setObjectName("tiny")
            hint.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(hint)

            self.edit.textChanged.connect(self._filter)
            self.edit.returnPressed.connect(self._run_selected)
            self.list.itemActivated.connect(lambda _i: self._run_selected())
            # NOTE: itemClicked is intentionally NOT connected — together with
            # itemActivated (double-click) it caused commands to run TWICE.
            self.edit.installEventFilter(self)

            # responsive width: never wider than the parent / screen
            avail = 560
            try:
                screen = QtWidgets.QApplication.primaryScreen()
                if screen is not None:
                    avail = min(avail, screen.availableGeometry().width() - 80)
                if parent is not None and parent.width() > 0:
                    avail = min(avail, parent.width() - 60)
            except Exception:
                pass
            self.setMinimumWidth(max(360, avail))
            self.setMaximumWidth(max(420, avail))

            self._filter("")

        # --- keyboard navigation ---
        def eventFilter(self, obj, ev):
            """Route arrow, paging and Tab keys from the edit to the list."""
            if obj is self.edit and ev.type() == QtCore.QEvent.Type.KeyPress:
                key = ev.key()
                if key in (QtCore.Qt.Key.Key_Down, QtCore.Qt.Key.Key_Up,
                           QtCore.Qt.Key.Key_PageDown, QtCore.Qt.Key.Key_PageUp,
                           QtCore.Qt.Key.Key_Home, QtCore.Qt.Key.Key_End):
                    QtWidgets.QApplication.sendEvent(self.list, ev)
                    return True
                if key == QtCore.Qt.Key.Key_Tab:            # complete query
                    row = self.list.currentRow()
                    if 0 <= row < len(self.result_actions):
                        title = self.result_actions[row].get("title", "")
                        self.edit.setText(title.split("    ")[0])
                    return True
            return super().eventFilter(obj, ev)

        def keyPressEvent(self, e):
            """Close on Escape; otherwise default handling."""
            if e.key() == QtCore.Qt.Key.Key_Escape:
                self.reject()
                return
            super().keyPressEvent(e)

        # --- fuzzy scoring ---
        def _score(self, query: str, text: str) -> int:
            """Fuzzy subsequence score of query against text."""
            q, t = query.lower(), text.lower()
            if not q:
                return 1
            if q in t:
                return 100 - t.index(q)
            # subsequence score
            score, ti, streak = 0, 0, 0
            for ch in q:
                found = t.find(ch, ti)
                if found == -1:
                    return 0
                streak = streak + 1 if found == ti else 1
                score += 2 + streak
                ti = found + 1
            return score

        def _filter(self, text: str):
            """Rebuild the result list from the best-scoring actions."""
            self.list.clear()
            self.result_actions = []
            scored = []
            for act in self.actions:
                s = self._score(text, act.get("title", ""))
                if s <= 0 and act.get("detail"):
                    s = self._score(text, act.get("detail", "")) // 2
                if s > 0:
                    scored.append((s, act))
            scored.sort(key=lambda pair: -pair[0])
            for _s, act in scored[:20]:
                title = act.get("title", "")
                sc = act.get("shortcut", "")
                item = QtWidgets.QListWidgetItem(f"{title}    {sc}" if sc else title)
                item.setToolTip(act.get("detail", title))
                self.list.addItem(item)
                self.result_actions.append(act)
            if self.list.count():
                self.list.setCurrentRow(0)

        def _run_selected(self):
            """Accept the dialog and queue the selected command once."""
            if self._done:
                return                          # v3.1: never run a command twice
            row = self.list.currentRow()
            if 0 <= row < len(self.result_actions):
                act = self.result_actions[row]
                self._done = True
                self.accept()
                cb = act.get("run")
                if cb:
                    QtCore.QTimer.singleShot(0, cb)

        def run(self) -> int:
            """Size, position, focus and exec the palette."""
            geo = self.parentWidget().geometry() if self.parentWidget() else None
            self.adjustSize()
            if geo:
                self.move(max(0, geo.center().x() - self.width() // 2),
                          max(0, geo.y() + max(60, geo.height() // 6)))
            self.edit.setFocus()
            self.edit.selectAll()
            return self.exec()


    # ---------------------------------------------------------------------------
    # Java syntax highlighting
    # ---------------------------------------------------------------------------
    _JAVA_KEYWORDS = (
        "abstract assert boolean break byte case catch char class const "
        "continue default do double else enum extends final finally float "
        "for goto if implements import instanceof int interface long native "
        "new package private protected public return short static strictfp "
        "super switch synchronized this throw throws transient try void "
        "volatile while true false null"
    ).split()

    _JAVA_TYPES = sorted({
        "Activity", "Button", "TextView", "EditText", "ImageView", "ImageButton",
        "CheckBox", "RadioButton", "RadioGroup", "Switch", "ToggleButton",
        "LinearLayout", "RelativeLayout", "FrameLayout", "GridLayout", "TableLayout",
        "View", "ViewGroup", "ScrollView", "ListView", "GridView", "Spinner",
        "WebView", "Toast", "Intent", "Bundle", "Handler", "Looper", "Canvas",
        "Paint", "Color", "Bitmap", "BitmapFactory", "Rect", "RectF", "Path",
        "Matrix", "Typeface", "Drawable", "MediaPlayer", "SoundPool", "Sensor",
        "SensorManager", "SensorEvent", "Camera", "Location", "LocationManager",
        "BluetoothAdapter", "WifiManager", "TelephonyManager", "ConnectivityManager",
        "HttpURLConnection", "HttpsURLConnection", "URL", "Socket", "String",
        "Integer", "Double", "Float", "Long", "Boolean", "Character", "Byte",
        "Short", "Object", "System", "Math", "Thread", "Runnable", "Exception",
        "RuntimeException", "IOException", "ArrayList", "LinkedList", "HashMap",
        "HashSet", "TreeMap", "Arrays", "Collections", "List", "Map", "Set",
        "Queue", "Deque", "Iterator", "Comparator", "Random", "Scanner", "File",
        "InputStream", "OutputStream", "Reader", "Writer", "StringBuilder",
        "StringBuffer", "Date", "Calendar", "SimpleDateFormat", "Notification",
        "NotificationChannel", "NotificationManager", "PendingIntent",
        "AlarmManager", "Service", "BroadcastReceiver", "ContentProvider",
        "SharedPreferences", "ContentValues", "ContentResolver", "Uri",
        "Fragment", "Dialog", "AlertDialog", "ProgressDialog", "AsyncTask",
        "CountDownTimer", "MotionEvent", "KeyEvent", "Gravity", "InputType",
        "TextUtils", "Log", "Build", "Environment", "Vibrator", "BaseAdapter",
        "ArrayAdapter", "Adapter", "AdapterView", "VideoView", "ProgressBar",
        "SeekBar", "RatingBar", "R", "DisplayMetrics", "GestureDetector",
        "VelocityTracker", "Choreographer", "WindowManager", "LayoutInflater",
        "Animation", "AnimationUtils", "AlphaAnimation", "TranslateAnimation",
        "ScaleAnimation", "RotateAnimation", "AnimationSet", "TypedValue",
        "Pair", "SparseArray", "Base64", "Html", "Spannable", "Editable",
        "StringBuffer", "ThreadLocalRandom", "TimeUnit", "Executors",
        # v3.2 — the compatibility expansion's most commonly typed classes
        "JSONObject", "JSONArray", "JSONException", "Pattern", "Matcher",
        "BigDecimal", "BigInteger", "DecimalFormat", "StandardCharsets",
        "Cipher", "MessageDigest", "SecureRandom", "SecretKeySpec", "Mac",
        "ObjectAnimator", "ValueAnimator", "AnimatorSet", "TransitionManager",
        "GLSurfaceView", "GLES20", "TextToSpeech", "SpeechRecognizer",
        "CameraDevice", "CameraCaptureSession", "CaptureRequest",
        "FingerprintManager", "BiometricPrompt", "JobScheduler", "JobService",
        "PackageManager", "ApplicationInfo", "ColorStateList", "TypedArray",
        "Resources", "AssetManager", "Configuration", "AudioAttributes",
        "MediaCodec", "MediaExtractor", "Parcel", "IBinder", "Binder",
        "HandlerThread", "Messenger", "InetSocketAddress", "Proxy",
        "LocalDate", "LocalTime", "LocalDateTime", "DateTimeFormatter",
        "Duration", "Instant", "ZoneId", "Collectors", "Stream",
        "CountDownLatch", "Semaphore", "CyclicBarrier", "ReentrantLock",
        "Future", "Callable", "ScheduledExecutorService", "AtomicLong",
        "AtomicReference", "ConcurrentHashMap", "CopyOnWriteArrayList",
        "WeakReference", "SoftReference", "CharSequence", "Comparable",
        "StringJoiner", "EnumMap", "EnumSet", "BitSet", "Toolbar",
        "AutoCompleteTextView", "CheckedTextView", "TextureView",
        "ViewPropertyAnimator", "FragmentTransaction", "FragmentManager",
        "DialogFragment", "ListFragment", "Transition", "Fade", "Slide",
        "ChangeBounds", "Animator", "AnimatorListenerAdapter",
    })


    class JavaHighlighter(QtGui.QSyntaxHighlighter):
        """Fast, block-local Java highlighter (multi-line comments via states).

        v3.1: a real single-pass tokenizer. Strings and char literals are
        scanned FIRST, so "//" or "/*" inside a string literal is no longer
        painted as a comment (and nothing after it gets mis-highlighted).
        Extremely long lines (minified/generated code) skip the expensive
        keyword regexes while keeping the comment/string state accurate.
        """

        _HUGE_LINE = 2000          # chars — beyond this, cheap mode

        _STYLES = {
            "keyword":   QtGui.QTextCharFormat(),
            "control":   QtGui.QTextCharFormat(),
            "string":    QtGui.QTextCharFormat(),
            "number":    QtGui.QTextCharFormat(),
            "comment":   QtGui.QTextCharFormat(),
            "doc":       QtGui.QTextCharFormat(),
            "annotation": QtGui.QTextCharFormat(),
            "type":      QtGui.QTextCharFormat(),
            "meta":      QtGui.QTextCharFormat(),
        }

        def __init__(self, parent=None):
            """Configure the text formats and compile the rule regexes."""
            super().__init__(parent)
            s = self._STYLES
            s["keyword"].setForeground(QtGui.QColor("#54e83c"))
            f = QtGui.QFont()
            f.setBold(True)
            s["keyword"].setFont(f)
            s["control"].setForeground(QtGui.QColor("#44d62c"))
            s["string"].setForeground(QtGui.QColor("#d19a66"))
            s["number"].setForeground(QtGui.QColor("#b5cea8"))
            s["comment"].setForeground(QtGui.QColor("#6a7a67"))
            s["comment"].setFontItalic(True)
            s["doc"].setForeground(QtGui.QColor("#7fb069"))
            s["doc"].setFontItalic(True)
            s["annotation"].setForeground(QtGui.QColor("#ffb454"))
            s["type"].setForeground(QtGui.QColor("#7ec8a9"))
            s["meta"].setForeground(QtGui.QColor("#9a9c98"))

            self._rules = []
            kw = "|".join(re.escape(k) for k in _JAVA_KEYWORDS)
            self._rules.append((re.compile(rf"\b({kw})\b"), "keyword"))
            types = "|".join(re.escape(t) for t in _JAVA_TYPES)
            self._rules.append((re.compile(rf"(?<![\w.$])({types})\b"), "type"))
            self._rules.append((re.compile(r"@\s*\w+"), "annotation"))
            self._rules.append((re.compile(r"\b\d[\d_]*(\.[\d_]+)?[fLdD]?\b"), "number"))
            self._rules.append((re.compile(r"\b0x[0-9a-fA-F_]+\b"), "number"))

        # ---------------------------------------------------------------------------
        def _format_code(self, text: str, start: int, end: int):
            """Apply keyword/type/number rules to a pure-CODE slice only."""
            if end <= start:
                return
            for rx, style in self._rules:
                for m in rx.finditer(text, start, end):
                    self.setFormat(m.start(), m.end() - m.start(),
                                   self._STYLES[style])

        def highlightBlock(self, text: str):
            """Highlight one block, carrying comment state across blocks."""
            STATE_NORMAL, STATE_COMMENT = 0, 1
            state = self.previousBlockState()
            if state == -1:
                state = STATE_NORMAL

            n = len(text)
            huge = n > self._HUGE_LINE       # cheap mode keeps state accurate

            i = 0
            if state == STATE_COMMENT:
                end = text.find("*/")
                if end == -1:
                    self.setFormat(0, n, self._STYLES["comment"])
                    self.setCurrentBlockState(STATE_COMMENT)
                    return
                self.setFormat(0, end + 2, self._STYLES["comment"])
                i = end + 2
                state = STATE_NORMAL

            self.setCurrentBlockState(STATE_NORMAL)
            code_start = i

            while i < n:
                c = text[i]

                # --- comments (only when NOT inside a string) ---
                if c == "/" and i + 1 < n:
                    nxt = text[i + 1]
                    if nxt == "/":
                        if not huge:
                            self._format_code(text, code_start, i)
                        self.setFormat(i, n - i, self._STYLES["comment"])
                        return                              # rest of line
                    if nxt == "*":
                        if not huge:
                            self._format_code(text, code_start, i)
                        end = text.find("*/", i + 2)
                        if end == -1:
                            self.setFormat(i, n - i, self._STYLES["comment"])
                            self.setCurrentBlockState(STATE_COMMENT)
                            return
                        style = "doc" if text.startswith("/**", i) else "comment"
                        self.setFormat(i, end + 2 - i, self._STYLES[style])
                        i = end + 2
                        code_start = i
                        continue

                # --- string / char literals (scanned FIRST-class) ---
                if c == '"' or c == "'":
                    j = i + 1
                    while j < n:
                        if text[j] == "\\":
                            j += 2
                            continue
                        if text[j] == c or text[j] == "\n":
                            break
                        j += 1
                    end = min(n, j + 1)
                    self.setFormat(i, end - i, self._STYLES["string"])
                    i = end
                    code_start = i
                    continue

                i += 1

            # trailing code segment (no comment/string till EOL)
            if not huge:
                self._format_code(text, code_start, n)


    # ---------------------------------------------------------------------------
    # Code editor with line numbers, current-line highlight & auto-indent
    # ---------------------------------------------------------------------------
    class LineNumberArea(QtWidgets.QWidget):
        """Editor gutter that delegates sizing and painting to CodeEditor."""

        def __init__(self, editor: "CodeEditor"):
            """Bind the gutter to its editor."""
            super().__init__(editor)
            self._editor = editor

        def sizeHint(self):
            """Report the editor's current gutter width."""
            return QtCore.QSize(self._editor.line_number_width(), 0)

        def paintEvent(self, event):
            """Delegate gutter painting to the editor."""
            self._editor.line_number_paint(self, event)


    class CodeEditor(QtWidgets.QPlainTextEdit):
        """Java editor with gutter, current-line highlight and smart keys."""

        def __init__(self, parent=None):
            """Wire the gutter, signals and initial decorations."""
            super().__init__(parent)
            self.setObjectName("codeEdit")
            self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
            self.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
            self._ln_area = LineNumberArea(self)
            self.blockCountChanged.connect(self._update_ln_width)
            self.updateRequest.connect(self._update_ln_area)
            self.cursorPositionChanged.connect(self._highlight_current_line)
            self._update_ln_width(0)
            self._highlight_current_line()

        # --- line numbers ---
        def line_number_width(self) -> int:
            """Compute the pixel width the gutter needs."""
            digits = max(3, len(str(max(1, self.blockCount()))))
            return 14 + self.fontMetrics().horizontalAdvance("9") * digits

        def _update_ln_width(self, _n):
            """Set the viewport margins to the gutter width."""
            self.setViewportMargins(self.line_number_width(), 0, 0, 0)

        def _update_ln_area(self, rect, dy):
            """Scroll or repaint the gutter on viewport updates."""
            if dy:
                self._ln_area.scroll(0, dy)
            else:
                self._ln_area.update(0, rect.y(), self._ln_area.width(), rect.height())
            if rect.contains(self.viewport().rect()):
                self._update_ln_width(0)

        def resizeEvent(self, e):
            """Keep the gutter glued to the viewport edge on resize."""
            super().resizeEvent(e)
            cr = self.contentsRect()
            self._ln_area.setGeometry(QtCore.QRect(cr.left(), cr.top(),
                                                   self.line_number_width(), cr.height()))

        def line_number_paint(self, area, event):
            """Paint the gutter's line numbers."""
            p = QtGui.QPainter(area)
            p.fillRect(event.rect(), QtGui.QColor(10, 11, 10))
            block = self.firstVisibleBlock()
            n = block.blockNumber()
            top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
            bottom = top + round(self.blockBoundingRect(block).height())
            current = self.textCursor().blockNumber()
            while block.isValid() and top <= event.rect().bottom():
                if block.isVisible() and bottom >= event.rect().top():
                    color = QtGui.QColor("#44d62c") if n == current else QtGui.QColor("#4e524c")
                    p.setPen(color)
                    p.drawText(0, top, area.width() - 6,
                               self.fontMetrics().height(),
                               QtCore.Qt.AlignmentFlag.AlignRight, str(n + 1))
                block = block.next()
                top = bottom
                bottom = top + round(self.blockBoundingRect(block).height())
                n += 1
            p.end()

        # --- current line highlight ---
        def _highlight_current_line(self):
            """Apply the full-width selection for the current line."""
            selection = QtWidgets.QTextEdit.ExtraSelection()
            selection.format.setBackground(QtGui.QColor(18, 19, 18))
            selection.format.setProperty(QtGui.QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            self.setExtraSelections([selection])

        # --- auto-indent & smart tab — v3.1: the REAL caret moves ---
        def keyPressEvent(self, e):
            """Handle auto-indenting Enter and plain Tab inserts."""
            if e.key() == QtCore.Qt.Key.Key_Return or e.key() == QtCore.Qt.Key.Key_Enter:
                cursor = self.textCursor()
                if cursor.hasSelection():
                    cursor.removeSelectedText()
                line = cursor.block().text()
                indent = re.match(r"[ \t]*", line).group(0)
                # extra indent when '{' was typed before the caret on this line
                before = line[:cursor.positionInBlock()]
                if before.rstrip().endswith("{"):
                    indent += "    "
                # dedent when the line opens a bare '}' block
                if before.strip() == "" and line.strip().startswith("}"):
                    indent = indent[:-4] if indent.endswith("    ") else indent
                cursor.insertText("\n" + indent)
                self.setTextCursor(cursor)      # ← the actual caret moves now
                e.accept()
                return
            if e.key() == QtCore.Qt.Key.Key_Tab and not self.textCursor().hasSelection():
                cursor = self.textCursor()
                cursor.insertText("    ")
                self.setTextCursor(cursor)      # ← the actual caret moves now
                e.accept()
                return
            super().keyPressEvent(e)

        # --- drag & drop .java files ---
        def dragEnterEvent(self, event):
            """Accept drags that carry .java/.txt files."""
            urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
            if any(u.toLocalFile().lower().endswith((".java", ".txt")) for u in urls):
                event.acceptProposedAction()
            else:
                super().dragEnterEvent(event)

        def dropEvent(self, event):
            """Load the first dropped .java/.txt file into the editor."""
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path.lower().endswith((".java", ".txt")):
                    try:
                        text = Path(path).read_text(encoding="utf-8", errors="replace")
                        self.setPlainText(text)
                        if hasattr(self, "_on_file_dropped") and callable(self._on_file_dropped):
                            self._on_file_dropped(path)
                        event.acceptProposedAction()
                        return
                    except Exception:
                        pass
            super().dropEvent(event)


    # ---------------------------------------------------------------------------
    # Element configurator — animation gallery dialog
    # ---------------------------------------------------------------------------
    class ElementConfigDialog(QtWidgets.QDialog):
        """Configure animations / sounds / images for one or many elements."""

        def __init__(self, elements: List[ElementInfo], parent=None):
            """Build the animation, sound and image cards plus footer."""
            super().__init__(parent)
            self.elements = elements if isinstance(elements, list) else [elements]
            single = len(self.elements) == 1

            if single:
                self.setWindowTitle(f"Configure {self.elements[0].name} · {self.elements[0].type}")
            else:
                self.setWindowTitle(f"Configure {len(self.elements)} Elements")

            self.resize(640, 660)
            root = QtWidgets.QVBoxLayout(self)
            root.setSpacing(14)

            if single:
                info = QtWidgets.QLabel(
                    f"<b style='color:#44d62c'>{html_escape(self.elements[0].name)}</b>"
                    f"<span style='color:#9a9c98'> · {html_escape(self.elements[0].type)}</span>")
            else:
                names = ", ".join(e.name for e in self.elements[:5])
                if len(self.elements) > 5:
                    names += f" and {len(self.elements) - 5} more"
                info = QtWidgets.QLabel(
                    f"<b style='color:#44d62c'>{len(self.elements)} elements</b>"
                    f"<span style='color:#9a9c98'> — {html_escape(names)}</span>")
            info.setWordWrap(True)
            root.addWidget(info)

            # --- Animations card ---
            anim_card, anim_lay = make_card("ANIMATION GALLERY", "Toggle any animations to apply.")
            self.chips: Dict[str, QtWidgets.QPushButton] = {}
            chip_grid = QtWidgets.QGridLayout()
            chip_grid.setSpacing(8)
            for idx, (anim_id, label) in enumerate(ANIMATIONS.items()):
                chip = QtWidgets.QPushButton(f"{ANIM_ICONS.get(anim_id, '•')}  {label}")
                chip.setObjectName("chip")
                chip.setCheckable(True)
                chip.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
                if any(anim_id in e.animations for e in self.elements):
                    chip.setChecked(True)
                chip.clicked.connect(self._update_summary)
                self.chips[anim_id] = chip
                chip_grid.addWidget(chip, idx // 3, idx % 3)
            anim_lay.addLayout(chip_grid)

            dur_row = QtWidgets.QHBoxLayout()
            dur_row.addWidget(QtWidgets.QLabel("Duration"))
            self.duration_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            self.duration_slider.setRange(50, 2000)
            self.duration_slider.setSingleStep(25)
            self.duration_slider.setValue(self.elements[0].animation_duration)
            self.duration_spin = QtWidgets.QSpinBox()
            self.duration_spin.setRange(50, 5000)
            self.duration_spin.setSingleStep(50)
            self.duration_spin.setValue(self.elements[0].animation_duration)
            self.duration_slider.valueChanged.connect(self.duration_spin.setValue)
            self.duration_spin.valueChanged.connect(self.duration_slider.setValue)
            dur_row.addWidget(self.duration_slider, 1)
            dur_row.addWidget(self.duration_spin)
            for label, val in (("Fast", 150), ("Normal", 300), ("Slow", 700)):
                b = QtWidgets.QPushButton(label)
                b.setObjectName("mini")
                b.clicked.connect(lambda _=False, v=val: self.duration_spin.setValue(v))
                dur_row.addWidget(b)
            anim_lay.addLayout(dur_row)
            root.addWidget(anim_card)

            # --- Sound card (v3.5: built-in library picker + preview) ---
            sound_card, sound_lay = make_card(
                "TAP SOUND", "Built-in library or your own file — played when the user taps this element.")
            self.sound_combo = QtWidgets.QComboBox()
            self.sound_combo.addItem("No sound", "")
            for sid, slabel in BUILTIN_SOUNDS.items():
                self.sound_combo.addItem(slabel, f"builtin:{sid}")
            self.sound_combo.addItem("Browse for a sound file…", "__browse__")
            self._select_sound_value(self.elements[0].sound_path if single else "")
            self.sound_combo.setEnabled(single)
            self.sound_combo.currentIndexChanged.connect(
                lambda _=0: self._sound_combo_changed())
            self.preview_btn = QtWidgets.QPushButton("Preview")
            self.preview_btn.setObjectName("mini")
            self.preview_btn.setEnabled(single and HAS_QTMULTIMEDIA)
            if not HAS_QTMULTIMEDIA:
                self.preview_btn.setToolTip("Sound preview needs QtMultimedia (not available)")
            else:
                self.preview_btn.setToolTip("Play the selected sound right now")
            self.preview_btn.clicked.connect(self._preview_sound)
            self._snd_effect = None
            sh = QtWidgets.QHBoxLayout()
            sh.addWidget(self.sound_combo, 1)
            sh.addWidget(self.preview_btn)
            sound_lay.addLayout(sh)
            if not single:
                hint = QtWidgets.QLabel(
                    "Sound applies to a single element only — select one element to edit it.")
                hint.setObjectName("tiny")
                sound_lay.addWidget(hint)
            root.addWidget(sound_card)

            # --- Image card ---
            img_card, img_lay = make_card(
                "IMAGE / BACKGROUND", "Applied to ImageView/ImageButton or used as background.")
            self.image_path_edit = QtWidgets.QLineEdit(
                self.elements[0].image_path if single else "")
            self.image_path_edit.setEnabled(single)
            self.image_path_edit.setPlaceholderText("No image selected")
            self.image_browse_btn = QtWidgets.QPushButton("Browse…")
            self.image_clear_btn = QtWidgets.QPushButton("Clear")
            for b in (self.image_browse_btn, self.image_clear_btn):
                b.setEnabled(single)
            self.image_browse_btn.clicked.connect(self.browse_image)
            self.image_clear_btn.clicked.connect(
                lambda: (self.image_path_edit.clear(), self._update_summary()))
            self.image_path_edit.textChanged.connect(self._update_summary)
            ih = QtWidgets.QHBoxLayout()
            ih.addWidget(self.image_path_edit, 1)
            ih.addWidget(self.image_browse_btn)
            ih.addWidget(self.image_clear_btn)
            img_lay.addLayout(ih)

            img_bottom = QtWidgets.QHBoxLayout()
            self.image_preview = QtWidgets.QLabel()
            self.image_preview.setFixedSize(64, 64)
            self.image_preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.image_preview.setStyleSheet(
                "border:1px solid #262826; border-radius:10px; background:#0f100f; color:#6f736e;")
            self.image_preview.setText("No img")
            self.auto_size_cb = QtWidgets.QCheckBox("Auto-fit image size")
            self.auto_size_cb.setChecked(self.elements[0].auto_size if single else True)
            self.auto_size_cb.setEnabled(single)
            img_bottom.addWidget(self.image_preview)
            img_bottom.addWidget(self.auto_size_cb)
            img_bottom.addStretch(1)
            img_lay.addLayout(img_bottom)
            root.addWidget(img_card)

            # --- Footer ---
            self.summary = QtWidgets.QLabel()
            self.summary.setObjectName("muted")
            root.addWidget(self.summary)

            btns = QtWidgets.QHBoxLayout()
            btns.addStretch(1)
            cancel = QtWidgets.QPushButton("Cancel")
            ok = QtWidgets.QPushButton("Apply")
            ok.setObjectName("primary")
            cancel.clicked.connect(self.reject)
            ok.clicked.connect(self.accept)
            btns.addWidget(cancel)
            btns.addWidget(ok)
            root.addLayout(btns)

            self._update_summary()

        def _select_sound_value(self, value: str):
            """Point the sound combo at a stored value ('' / builtin:x / file path)."""
            idx = self.sound_combo.findData(value)
            if idx < 0 and value:
                # a custom file → give it its own item right before Browse
                browse_idx = self.sound_combo.findData("__browse__")
                insert_at = browse_idx if browse_idx >= 0 else self.sound_combo.count()
                self.sound_combo.insertItem(insert_at, f"{Path(value).name}", value)
                idx = self.sound_combo.findData(value)
            if idx >= 0:
                self.sound_combo.setCurrentIndex(idx)
            else:
                self.sound_combo.setCurrentIndex(0)

        def _sound_combo_changed(self):
            """Open the file picker when Browse is selected."""
            data = self.sound_combo.currentData()
            if data == "__browse__":
                p, _ = QtWidgets.QFileDialog.getOpenFileName(
                    self, "Select Sound File", "",
                    "Audio Files (*.mp3 *.wav *.ogg *.m4a *.aac);;All Files (*)")
                self._select_sound_value(p if p else "")
            self._update_summary()

        def _preview_sound(self):
            """Play the selected sound through a shared QSoundEffect."""
            if not HAS_QTMULTIMEDIA:
                return
            value = self.sound_combo.currentData() or ""
            path = builtin_sound_path(value[8:]) if value.startswith("builtin:") else value
            if not path or not Path(path).exists():
                return
            try:
                from PyQt6.QtCore import QUrl
                if self._snd_effect is None:
                    self._snd_effect = QSoundEffect(self)
                self._snd_effect.setSource(QUrl.fromLocalFile(path))
                self._snd_effect.setVolume(0.7)
                self._snd_effect.play()
            except Exception:
                pass

        def browse_image(self):
            """Pick an image file and show its thumbnail."""
            p, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Select Image File", "",
                "Images (*.png *.jpg *.jpeg);;All Files (*)")
            if p:
                self.image_path_edit.setText(p)
                pm = QtGui.QPixmap(p)
                if not pm.isNull():
                    self.image_preview.setPixmap(
                        pm.scaled(56, 56, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                 QtCore.Qt.TransformationMode.SmoothTransformation))

        def _update_summary(self):
            """Refresh the footer summary from the current choices."""
            n = sum(1 for c in self.chips.values() if c.isChecked())
            parts = [f"{n} animation{'s' if n != 1 else ''} · {self.duration_spin.value()} ms"]
            snd = self.sound_combo.currentData() or ""
            if snd and snd != "__browse__":
                parts.append("sound OK")
            if self.image_path_edit.text().strip():
                parts.append("image OK")
            self.summary.setText("  ".join(parts))

        def get_config(self) -> List[ElementInfo]:
            """Write the dialog's choices back onto the elements."""
            selected = [aid for aid, chip in self.chips.items() if chip.isChecked()]
            duration = self.duration_spin.value()
            single = len(self.elements) == 1
            snd = (self.sound_combo.currentData() or "") if single else ""
            if snd == "__browse__":
                snd = ""
            for element in self.elements:
                element.animations = selected.copy()
                element.animation_duration = duration
                if single:
                    element.sound_path = snd
                    element.image_path = self.image_path_edit.text().strip()
                    element.auto_size = self.auto_size_cb.isChecked()
            return self.elements


    # ---------------------------------------------------------------------------
    # Page base
    # ---------------------------------------------------------------------------


    class Page(QtWidgets.QWidget):
        """Base page: title + subtitle header and a body layout."""

        def __init__(self, win, title: str, subtitle: str = ""):
            """Build the page header and the vertical body layout."""
            super().__init__()
            self.win = win
            root = QtWidgets.QVBoxLayout(self)
            root.setContentsMargins(26, 22, 26, 22)
            root.setSpacing(16)

            head = QtWidgets.QWidget()
            hl = QtWidgets.QVBoxLayout(head)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(4)
            t = QtWidgets.QLabel(title)
            t.setObjectName("pageTitle")
            s = QtWidgets.QLabel(subtitle)
            s.setObjectName("muted")
            s.setWordWrap(True)
            hl.addWidget(t)
            hl.addWidget(s)
            root.addWidget(head)

            self.body = QtWidgets.QVBoxLayout()
            self.body.setSpacing(16)
            root.addLayout(self.body, 1)


    # ---------------------------------------------------------------------------
    # SOURCE page — Java editor + live diagnostics with one-click fixes
    # ---------------------------------------------------------------------------
    class SourcePage(Page):
        """Source page: Java editor with live diagnostics and one-click fixes."""

        def __init__(self, win):
            """Build status strip, editor, diagnostics panel and toolbar."""
            super().__init__(win, "Source",
                             "Paste ONE all-in-one Java file — full app, multiple classes or a "
                             "bare snippet. Everything is analyzed live as you type.")

            # --- status strip ---
            strip = QtWidgets.QHBoxLayout()
            self.mode_pill = Pill("SNIPPET MODE", "muted")
            self.elements_pill = Pill("0 elements", "muted")
            self.diag_pill = Pill("0 diagnostics", "muted")
            self.loc_lbl = QtWidgets.QLabel("0 lines")
            self.loc_lbl.setObjectName("tiny")
            self.goto_motion_btn = QtWidgets.QPushButton("Configure in Motion →")
            self.goto_motion_btn.setObjectName("ghost")
            self.goto_motion_btn.clicked.connect(lambda: win.goto_page("motion"))
            strip.addWidget(self.mode_pill)
            strip.addWidget(self.elements_pill)
            strip.addWidget(self.diag_pill)
            strip.addWidget(self.loc_lbl)
            strip.addStretch(1)
            strip.addWidget(self.goto_motion_btn)
            self.body.addLayout(strip)

            # --- editor with syntax highlighting ---
            self.java_edit = CodeEditor()
            self.java_edit.setPlaceholderText(
                "Paste your Java here — a full app with multiple classes in ONE file, "
                "or a bare snippet.\n"
                "Tip: drag & drop a .java file, insert a template below, or open the "
                "AI Guide to make AI models write APK-Forge-perfect code.")
            self.java_edit._on_file_dropped = self._file_dropped
            self.body.addWidget(self.java_edit, 1)

            # --- diagnostics panel ---
            diag_card, diag_lay = make_card()
            self.diag_card = diag_card
            head = QtWidgets.QHBoxLayout()
            self.diag_title = QtWidgets.QLabel("DIAGNOSTICS")
            self.diag_title.setObjectName("cardSection")
            head.addWidget(self.diag_title)
            self.scan_spinner = Spinner(self, 20)
            self.scan_spinner.stop()
            head.addWidget(self.scan_spinner)
            head.addStretch(1)
            self.rescan_btn = QtWidgets.QPushButton("Rescan (F5)")
            self.rescan_btn.setObjectName("mini")
            self.rescan_btn.clicked.connect(lambda: win.trigger_scan(force=True))
            head.addWidget(self.rescan_btn)
            diag_lay.addLayout(head)
            self.diag_list = QtWidgets.QVBoxLayout()
            self.diag_list.setSpacing(6)
            diag_lay.addLayout(self.diag_list)
            self.body.addWidget(diag_card)

            # --- toolbar ---
            bar = QtWidgets.QHBoxLayout()
            self.open_btn = QtWidgets.QPushButton("Open File")
            self.save_btn = QtWidgets.QPushButton("Save")
            self.fiximports_btn = QtWidgets.QPushButton("Fix Imports")
            self.fiximports_btn.setToolTip(
                "Add imports for every known class used but not imported.")
            self.fiximports_btn.clicked.connect(lambda: win.fix_imports())
            self.clear_btn = QtWidgets.QPushButton("Clear")
            self.clear_btn.setObjectName("danger")

            lbl = QtWidgets.QLabel("Template:")
            lbl.setObjectName("muted")
            self.template_combo = QtWidgets.QComboBox()
            for name in TEMPLATES:
                self.template_combo.addItem(name)
            self.insert_btn = QtWidgets.QPushButton("Insert")
            self.insert_btn.setObjectName("primary")

            bar.addWidget(self.open_btn)
            bar.addWidget(self.save_btn)
            bar.addWidget(self.fiximports_btn)
            bar.addWidget(self.clear_btn)
            bar.addStretch(1)
            bar.addWidget(lbl)
            bar.addWidget(self.template_combo, 1)
            bar.addWidget(self.insert_btn)
            self.body.addLayout(bar)

            # --- wiring ---
            self.open_btn.clicked.connect(win.on_load_java)
            self.save_btn.clicked.connect(win.on_save_java)
            self.clear_btn.clicked.connect(self._clear_editor)
            self.insert_btn.clicked.connect(self._insert_template)

            win.java_edit = self.java_edit

        # --- helpers ---
        def _file_dropped(self, path: str):
            """Log and rescan after a Java file is dropped on the editor."""
            self.win.log(f"[{log_time()}] Loaded Java from drop: {path}")
            self.win.trigger_scan()

        def _clear_editor(self):
            """Clear the editor after asking for confirmation."""
            if self.java_edit.toPlainText().strip():
                confirm = QtWidgets.QMessageBox.question(
                    self, "Clear source",
                    "Clear the Java editor? Your code cannot be recovered (unless auto-saved).",
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No)
                if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
                    return
            self.java_edit.clear()

        def _insert_template(self):
            """Insert the selected template into the editor."""
            name = self.template_combo.currentText()
            code = TEMPLATES.get(name, "")
            if not code:
                return
            if self.java_edit.toPlainText().strip():
                confirm = QtWidgets.QMessageBox.question(
                    self, "Insert template",
                    f"Replace the current code with the '{name}' template?",
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No)
                if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
                    return
            self.java_edit.setPlainText(code)
            self.win.toast(f"Template inserted: {name}", "ok")
            self.win.log(f"[{log_time()}] Template inserted: {name}")
            self.win.trigger_scan()

        # --- refresh (called after each background scan) ---
        def refresh_status(self, payload: dict):
            """Refresh the status pills from a scan payload."""
            analysis: "JavaAnalysis" = payload.get("analysis")
            if analysis is None:
                return
            if analysis.is_full:
                self.mode_pill.setText(
                    f"FULL APP · {len(analysis.type_names)} class(es)")
                self.mode_pill.setState("ok")
            else:
                self.mode_pill.setText("SNIPPET MODE")
                self.mode_pill.setState("muted")

            total = len(payload.get("elements", []))
            configured = sum(1 for e in payload.get("elements", [])
                             if e.animations or e.sound_path or e.image_path)
            if total:
                self.elements_pill.setText(f"{total} elements · {configured} configured")
                self.elements_pill.setState("ok" if configured else "muted")
            else:
                self.elements_pill.setText("0 elements")
                self.elements_pill.setState("muted")

            errors = sum(1 for i in analysis.issues if i.level == "error")
            warns = sum(1 for i in analysis.issues if i.level == "warn")
            self.diag_pill.setText(
                f"{len(analysis.issues)} diagnostics"
                + (f" ({errors} err, {warns} warn" + ")" if errors or warns else ")"))
            if errors:
                self.diag_pill.setState("bad")
            elif warns:
                self.diag_pill.setState("warn")
            else:
                self.diag_pill.setState("ok" if analysis.issues else "muted")
            self.loc_lbl.setText(f"{analysis.loc} lines · {analysis.chars // 1024} KB")

        def refresh_diagnostics(self, issues: List[JavaIssue]):
            """Rebuild the diagnostics list from the given issues."""
            clear_layout(self.diag_list)
            if not issues:
                ok = QtWidgets.QLabel("No issues detected — your code looks forgeable.")
                ok.setStyleSheet("color:#44d62c; background:transparent; font-weight:600;")
                self.diag_list.addWidget(ok)
                return
            ICONS = {"error": ("X", "#ff7a7a"), "warn": ("!", "#ffb454"), "info": ("i", "#44d62c")}
            for issue in issues[:12]:
                icon, color = ICONS.get(issue.level, ("•", "#9a9c98"))
                row = QtWidgets.QWidget()
                h = QtWidgets.QHBoxLayout(row)
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(10)
                ic = QtWidgets.QLabel(icon)
                ic.setFixedWidth(18)
                ic.setStyleSheet(f"color:{color}; background:transparent; font-weight:800;")
                col = QtWidgets.QVBoxLayout()
                col.setSpacing(1)
                title = QtWidgets.QLabel(issue.title)
                title.setStyleSheet(
                    f"color:{color if issue.level != 'info' else '#e8e8e6'};"
                    "background:transparent; font-weight:700;")
                title.setWordWrap(True)
                col.addWidget(title)
                if issue.detail:
                    detail = QtWidgets.QLabel(issue.detail)
                    detail.setObjectName("tiny")
                    detail.setWordWrap(True)
                    col.addWidget(detail)
                h.addWidget(ic)
                h.addLayout(col, 1)
                if issue.fix_id:
                    fix = QtWidgets.QPushButton("FIX →")
                    fix.setObjectName("mini")
                    fix.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
                    fix.clicked.connect(lambda _=False, iid=issue.fix_id, arg=issue.fix_arg:
                                         self.win.apply_fix(iid, arg))
                    h.addWidget(fix)
                self.diag_list.addWidget(row)
            if len(issues) > 12:
                more = QtWidgets.QLabel(f"… and {len(issues) - 12} more")
                more.setObjectName("tiny")
                self.diag_list.addWidget(more)


    # ---------------------------------------------------------------------------
    # DESIGN page — icon & the v3.4 asset manager
    # ---------------------------------------------------------------------------
    class _IconDropLabel(QtWidgets.QLabel):
        """Icon preview slot that accepts dropped image files directly
        (v3.4: page-level drops now go to the ASSET list instead of the icon,
        so dropping five images no longer silently overwrites the icon)."""

        _ICON_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")

        def __init__(self, owner):
            """Keep a weak reference to the owning page."""
            super().__init__()
            self._owner = weakref.ref(owner)
            self.setAcceptDrops(True)
            self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        def dragEnterEvent(self, event):
            """Accept drags that carry an image file."""
            urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
            if urls and Path(urls[0].toLocalFile()).suffix.lower() in self._ICON_EXTS:
                event.acceptProposedAction()

        def dropEvent(self, event):
            """Hand the first dropped image file to the owner's set_icon()."""
            owner = self._owner()
            if owner is None:
                return
            for url in event.mimeData().urls():
                p = url.toLocalFile()
                if p and Path(p).suffix.lower() in self._ICON_EXTS:
                    owner.set_icon(p)
                    break
            event.acceptProposedAction()


    class DesignPage(Page):
        """Design page: app icon plus the v3.4 asset manager."""

        def __init__(self, win):
            """Build the icon and asset-manager cards side by side."""
            super().__init__(win, "Design",
                             "Your app's icon and the asset manager — drop anything "
                             "anywhere on this page to bundle it.")

            self._updating_assets = False
            self._shown: List[AssetEntry] = []

            row = QtWidgets.QHBoxLayout()
            row.addWidget(self._make_icon_card())
            row.addWidget(self._make_assets_card(), 1)
            self.body.addLayout(row)

            self.setAcceptDrops(True)

        # --- icon ---
        def _make_icon_card(self):
            """Create the icon preview card with browse and remove buttons."""
            card, lay = make_card(
                "APP ICON", "512×512 recommended — resized to every density automatically.")

            self.icon_preview = _IconDropLabel(self)
            self.icon_preview.setFixedSize(132, 132)
            self.icon_preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.icon_preview.setStyleSheet(
                "border:1px dashed #2a2c2a; border-radius:14px; background:#0f100f; color:#6f736e; font-size:11px;")
            self.icon_preview.setText("Drop icon\nor browse")
            lay.addWidget(self.icon_preview, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)

            self.icon_hint = QtWidgets.QLabel(
                "No icon selected — default Android icon will be used.")
            self.icon_hint.setObjectName("tiny")
            self.icon_hint.setWordWrap(True)
            self.icon_hint.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            lay.addWidget(self.icon_hint)

            btns = QtWidgets.QHBoxLayout()
            self.icon_browse_btn = QtWidgets.QPushButton("Browse…")
            self.icon_clear_btn = QtWidgets.QPushButton("Remove")
            self.icon_clear_btn.setObjectName("danger")
            self.icon_browse_btn.clicked.connect(self._browse_icon)
            self.icon_clear_btn.clicked.connect(self._clear_icon)
            btns.addWidget(self.icon_browse_btn)
            btns.addWidget(self.icon_clear_btn)
            lay.addLayout(btns)
            return card

        def _browse_icon(self):
            """Pick an icon file via dialog and apply it."""
            p, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Select App Icon", "", "Images (*.png *.jpg *.jpeg);;All Files (*)")
            if p:
                self.set_icon(p)

        def set_icon(self, path: str):
            """Apply the chosen icon path to preview and config."""
            if not Path(path).exists():
                return
            self.win.cfg.icon_path = path
            pm = QtGui.QPixmap(path)
            if not pm.isNull():
                self.icon_preview.setPixmap(
                    pm.scaled(116, 116, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                             QtCore.Qt.TransformationMode.SmoothTransformation))
                self.icon_preview.setStyleSheet(
                    "border:1px solid #2c4a24; border-radius:14px; background:#0f100f;")
            self.icon_hint.setText(Path(path).name)
            self.win._save_settings_soon()
            self.win.log(f"[{log_time()}] Icon set: {path}")

        def _clear_icon(self):
            """Remove the icon and reset the preview slot."""
            self.win.cfg.icon_path = ""
            self.icon_preview.clear()
            self.icon_preview.setText("Drop icon\nor browse")
            self.icon_preview.setStyleSheet(
                "border:1px dashed #2a2c2a; border-radius:14px; background:#0f100f; color:#6f736e; font-size:11px;")
            self.icon_hint.setText("No icon selected — default Android icon will be used.")
            self.win._save_settings_soon()

        # --- assets (v3.4 — the full asset manager) ---
        def _make_assets_card(self):
            """Create the asset manager card: filter, table, preview, actions."""
            card, lay = make_card(
                "ASSETS & RESOURCES",
                "Images → drawable (R.drawable.name) · sounds → raw (R.raw.name) · "
                "everything else → assets (getAssets().open(\"name\")). "
                "Auto-Organize picks the right target for you.")

            # toolbar: filter + add actions
            top = QtWidgets.QHBoxLayout()
            self.asset_search = QtWidgets.QLineEdit()
            self.asset_search.setPlaceholderText("Filter assets by name…")
            self.asset_search.setClearButtonEnabled(True)
            self.asset_search.textChanged.connect(lambda _t: self.refresh_assets())
            top.addWidget(self.asset_search, 1)
            add_file = QtWidgets.QPushButton("Add Files")
            add_folder = QtWidgets.QPushButton("Add Folder")
            add_text = QtWidgets.QPushButton("Add Text")
            add_text.setToolTip(
                "Create a JSON / config / notes asset right here — no external file needed.")
            add_file.clicked.connect(self._add_files)
            add_folder.clicked.connect(self._add_folder)
            add_text.clicked.connect(self._new_text_asset)
            for b in (add_file, add_folder, add_text):
                top.addWidget(b)
            lay.addLayout(top)

            # the table
            self.assets_table = QtWidgets.QTableWidget(0, 4)
            self.assets_table.setHorizontalHeaderLabels(
                ["Name", "Destination", "Size", "Access in code"])
            self.assets_table.verticalHeader().setVisible(False)
            self.assets_table.setSelectionBehavior(
                QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.assets_table.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
            self.assets_table.setEditTriggers(
                QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.assets_table.setShowGrid(False)
            self.assets_table.setAlternatingRowColors(True)
            self.assets_table.setContextMenuPolicy(
                QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            self.assets_table.customContextMenuRequested.connect(self._asset_context_menu)
            self.assets_table.itemChanged.connect(self._on_asset_item_changed)
            self.assets_table.itemSelectionChanged.connect(self._update_asset_preview)
            self.assets_table.itemDoubleClicked.connect(
                lambda item: self._rename_asset() if item.column() == 0 else None)
            hdr = self.assets_table.horizontalHeader()
            hdr.setStretchLastSection(True)
            hdr.resizeSection(0, 230)
            hdr.resizeSection(1, 150)
            hdr.resizeSection(2, 70)
            lay.addWidget(self.assets_table, 1)

            # preview strip
            self.asset_thumb = QtWidgets.QLabel()
            self.asset_thumb.setFixedSize(48, 48)
            self.asset_thumb.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.asset_thumb.setStyleSheet(
                "border:1px dashed #2a2c2a; border-radius:8px; background:#0f100f;")
            self.asset_info = QtWidgets.QLabel("Select an asset to preview it.")
            self.asset_info.setObjectName("tiny")
            self.asset_info.setWordWrap(True)
            self.asset_copy_btn = QtWidgets.QPushButton("Copy access")
            self.asset_copy_btn.setObjectName("mini")
            self.asset_copy_btn.setEnabled(False)
            self.asset_copy_btn.clicked.connect(self._copy_asset_snippet)
            prev = QtWidgets.QHBoxLayout()
            prev.addWidget(self.asset_thumb)
            prev.addWidget(self.asset_info, 1)
            prev.addWidget(self.asset_copy_btn)
            lay.addLayout(prev)

            self.assets_size_lbl = QtWidgets.QLabel("0 items · 0 B")
            self.assets_size_lbl.setObjectName("tiny")
            lay.addWidget(self.assets_size_lbl)

            # actions
            btns = QtWidgets.QHBoxLayout()
            organize = QtWidgets.QPushButton("Auto-Organize")
            organize.setObjectName("primary")
            organize.setToolTip(
                "Images → drawable, sounds → raw — but assets your code already "
                "opens via getAssets() stay put, and anything referenced as "
                "R.drawable.x / R.raw.x is routed there exactly.")
            organize.clicked.connect(self._auto_organize)
            self.asset_target_combo = QtWidgets.QComboBox()
            self.asset_target_combo.addItem("→ assets")
            self.asset_target_combo.addItem("→ drawable")
            self.asset_target_combo.addItem("→ raw")
            self.asset_target_combo.setToolTip(
                "Move the selected asset(s) to another destination inside the APK.")
            move_btn = QtWidgets.QPushButton("Move")
            move_btn.clicked.connect(
                lambda: self._apply_target(ASSET_TARGETS[self.asset_target_combo.currentIndex()]))
            rename_btn = QtWidgets.QPushButton("Rename…")
            rename_btn.clicked.connect(self._rename_asset)
            remove = QtWidgets.QPushButton("Remove")
            remove.setObjectName("danger")
            remove.clicked.connect(self._remove_selected)
            clear = QtWidgets.QPushButton("Clear All")
            clear.setObjectName("danger")
            clear.clicked.connect(self._clear_files)
            for b in (organize, self.asset_target_combo, move_btn, rename_btn,
                      remove, clear):
                btns.addWidget(b)
            lay.addLayout(btns)
            return card

        # --- asset helpers ---
        def _entries(self) -> List[AssetEntry]:
            """Return the asset list held by the project config."""
            return self.win.cfg.assets

        def _selected_entries(self) -> List[AssetEntry]:
            """Return the assets currently selected in the table."""
            rows = sorted({i.row() for i in self.assets_table.selectedItems()})
            return [self._shown[r] for r in rows if 0 <= r < len(self._shown)]

        def _add_files(self):
            """Add files picked through a file dialog."""
            paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
                self, "Add Files", "", "All Files (*)")
            added = sum(self._add_asset(p) for p in paths)
            if added:
                self.win.toast(
                    f"{added} asset(s) added — check the 'Access in code' column", "ok")

        def _add_folder(self):
            """Add a folder picked through a directory dialog."""
            p = QtWidgets.QFileDialog.getExistingDirectory(
                self, "Add Folder",
                "", QtWidgets.QFileDialog.Option.ShowDirsOnly)
            if p and self._add_asset(p):
                self.win.toast("Folder added — junk files will be filtered automatically", "ok")

        def _add_asset(self, path: str) -> int:
            """Add a file/folder. The target is picked SMARTLY: files the code
            already opens via getAssets() stay in assets/; otherwise images →
            drawable and sounds → raw. Returns 1 when added."""
            if not path:
                return 0
            if any(e.source == path for e in self._entries()):
                self.win.toast(f"{Path(path).name} is already bundled", "info")
                return 0
            java = self.win.java_edit.toPlainText() if hasattr(self.win, "java_edit") else ""
            entry = AssetEntry.from_path(path, AssetEntry.smart_target(path, java))
            self.win.cfg.assets.append(entry)
            self.refresh_assets()
            self.win._save_settings_soon()
            self.win.log(f"[{log_time()}] Asset: {entry.name} → {entry.dest_display()} "
                         f"· {entry.access_snippet()}")
            return 1

        def _new_text_asset(self):
            """Create an inline text asset through a small dialog."""
            box = QtWidgets.QDialog(self)
            box.setWindowTitle("New Text Asset")
            box.resize(500, 400)
            v = QtWidgets.QVBoxLayout(box)
            v.addWidget(QtWidgets.QLabel("Asset name (exactly as opened from Java):"))
            name_edit = QtWidgets.QLineEdit("notes.txt")
            v.addWidget(name_edit)
            v.addWidget(QtWidgets.QLabel("Content (bundled into the APK verbatim):"))
            edit = QtWidgets.QPlainTextEdit()
            edit.setPlaceholderText('{\n  "greeting": "hello"\n}\n… or any text / JSON / CSV your app reads')
            v.addWidget(edit, 1)
            btns = QtWidgets.QHBoxLayout()
            ok = QtWidgets.QPushButton("Add Asset")
            ok.setObjectName("primary")
            cancel = QtWidgets.QPushButton("Cancel")
            ok.clicked.connect(box.accept)
            cancel.clicked.connect(box.reject)
            btns.addWidget(ok)
            btns.addWidget(cancel)
            v.addLayout(btns)
            if box.exec() != QtWidgets.QDialog.DialogCode.Accepted:
                return
            name = name_edit.text().strip()
            if not name or "/" in name or "\\" in name:
                self.win.toast("Pick a simple file name (no folders, no slashes)", "warn")
                return
            if any(e.name == name for e in self._entries()):
                self.win.toast(f"An asset named '{name}' already exists", "warn")
                return
            self.win.cfg.assets.append(
                AssetEntry(source="", text=edit.toPlainText(), name=name, target="assets"))
            self.refresh_assets()
            self.win._save_settings_soon()
            self.win.log(f"[{log_time()}] Text asset created: {name} "
                         f'(getAssets().open("{name}"))')
            self.win.toast(f"Text asset '{name}' created", "ok")

        def _remove_selected(self):
            """Remove the selected assets from the project."""
            sel = self._selected_entries()
            if not sel:
                return
            for e in sel:
                try:
                    self.win.cfg.assets.remove(e)
                except ValueError:
                    pass
            self.refresh_assets()
            self.win._save_settings_soon()
            self.win.log(f"[{log_time()}] Removed {len(sel)} asset(s)")

        def _clear_files(self):
            """Remove every bundled asset after confirmation."""
            if not self.win.cfg.assets:
                return
            confirm = QtWidgets.QMessageBox.question(
                self, "Clear assets",
                f"Remove all {len(self.win.cfg.assets)} bundled asset(s)?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
                return
            self.win.cfg.assets.clear()
            self.refresh_assets()
            self.win._save_settings_soon()

        def _rename_asset(self):
            """Rename the one selected asset."""
            sel = self._selected_entries()
            if len(sel) != 1:
                self.win.toast("Select exactly one asset to rename", "info")
                return
            e = sel[0]
            new, ok = QtWidgets.QInputDialog.getText(
                self, "Rename asset", "New name (as used from Java):",
                QtWidgets.QLineEdit.EchoMode.Normal, e.name)
            if not ok:
                return
            new = new.strip()
            if not new or new == e.name:
                return
            if "/" in new or "\\" in new:
                self.win.toast("No slashes in the name", "warn")
                return
            if any(other.name == new and other is not e for other in self._entries()):
                self.win.toast(f"'{new}' is already used by another asset", "warn")
                return
            e.name = new
            self.refresh_assets()
            self.win._save_settings_soon()
            self.win.log(f"[{log_time()}] Asset renamed → {e.name} ({e.access_snippet()})")
            self.win.toast(f"Renamed to {new}", "ok")

        def _apply_target(self, target: str):
            """Move the selected assets to a new destination target."""
            moved, skipped = 0, []
            for e in self._selected_entries():
                if e.is_dir or e.is_inline:
                    skipped.append(e.name)
                    continue
                if target == "drawable" and Path(e.source).suffix.lower() not in ASSET_DRAWABLE_EXTS:
                    skipped.append(e.name)
                    continue
                if e.target != target:
                    e.target = target
                    moved += 1
            if moved:
                self.refresh_assets()
                self.win._save_settings_soon()
                self.win.log(f"[{log_time()}] {moved} asset(s) → {target}")
                self.win.toast(f"{moved} asset(s) → {target}", "ok")
            if skipped:
                self.win.toast(
                    "Folders & text stay in assets/ · drawables must be image files", "warn")

        def _auto_organize(self):
            """v3.4 automation: route every asset to the destination the CODE
            actually implies (R.drawable.x → drawable, R.raw.x → raw,
            getAssets().open("x") → assets) and use smart defaults for the rest
            (images → drawable, sounds → raw)."""
            java = self.win.java_edit.toPlainText() if hasattr(self.win, "java_edit") else ""
            usage = scan_asset_usage(java)
            moved = []
            for e in self.win.cfg.assets:
                if e.is_dir or e.is_inline or not e.enabled:
                    continue
                res = e.res_name()
                if res in usage.drawables:
                    want = "drawable"
                elif res in usage.raws:
                    want = "raw"
                elif any(name == e.name or name.endswith("/" + e.name)
                         for name in usage.asset_opens):
                    want = "assets"
                else:
                    want = AssetEntry.guess_target(e.source)
                if want != e.target:
                    e.target = want
                    moved.append(f"{e.name} → {want}")
            if moved:
                self.refresh_assets()
                self.win._save_settings_soon()
                for m in moved:
                    self.win.log(f"[{log_time()}] Auto-organize: {m}")
                self.win.toast(f"{len(moved)} asset(s) re-routed (images→drawable, "
                               f"sounds→raw)", "ok")
            else:
                self.win.toast("Assets are already optimally organized", "info")

        def _copy_asset_snippet(self):
            """Copy the selected asset's access snippet to the clipboard."""
            sel = self._selected_entries()
            if not sel:
                return
            snippet = sel[0].access_snippet()
            QtGui.QGuiApplication.clipboard().setText(snippet)
            self.win.toast(f"Copied: {snippet}", "ok")

        def _asset_context_menu(self, pos: QtCore.QPoint):
            """Show the table context menu and run the chosen action."""
            item = self.assets_table.itemAt(pos)
            if item is None:
                return
            if item not in self.assets_table.selectedItems():
                self.assets_table.selectRow(item.row())
            menu = QtWidgets.QMenu(self)
            a_copy = menu.addAction("Copy access snippet")
            a_rename = menu.addAction("Rename…")
            menu.addSeparator()
            a_assets = menu.addAction("→  assets  (getAssets().open)")
            a_draw = menu.addAction("→  drawable  (R.drawable)")
            a_raw = menu.addAction("→  raw  (R.raw)")
            menu.addSeparator()
            sel = self._selected_entries()
            e = sel[0] if sel else None
            a_open = menu.addAction("Open file location")
            a_open.setEnabled(bool(e and not e.is_inline and e.exists))
            menu.addSeparator()
            a_remove = menu.addAction("Remove")
            act = menu.exec(self.assets_table.viewport().mapToGlobal(pos))
            if act is None:
                return
            if act == a_copy:
                self._copy_asset_snippet()
            elif act == a_rename:
                self._rename_asset()
            elif act == a_assets:
                self._apply_target("assets")
            elif act == a_draw:
                self._apply_target("drawable")
            elif act == a_raw:
                self._apply_target("raw")
            elif act == a_open and e is not None:
                try:
                    QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(
                        str(Path(e.source).parent)))
                except Exception:
                    pass
            elif act == a_remove:
                self._remove_selected()

        def _on_asset_item_changed(self, item):
            """Toggle an asset's bundled flag from its checkbox."""
            if self._updating_assets:
                return
            if item.column() != 0:
                return
            row = item.row()
            if not (0 <= row < len(self._shown)):
                return
            e = self._shown[row]
            new_enabled = item.checkState() == QtCore.Qt.CheckState.Checked
            if new_enabled != e.enabled:
                e.enabled = new_enabled
                self._update_assets_summary()
                self.win._save_settings_soon()
                self.win.log(f"[{log_time()}] {e.name}: {'bundled' if new_enabled else 'excluded from build'}")

        def refresh_assets(self):
            """Rebuild the asset table, honoring the name filter."""
            self._updating_assets = True
            try:
                filt = self.asset_search.text().strip().lower() \
                    if hasattr(self, "asset_search") else ""
                self.assets_table.setRowCount(0)
                self._shown = []
                for e in self.win.cfg.assets:
                    if filt and filt not in e.name.lower():
                        continue
                    self._shown.append(e)
                for row, e in enumerate(self._shown):
                    self.assets_table.insertRow(row)
                    name_item = QtWidgets.QTableWidgetItem(f"{e.type_icon()}  {e.name}")
                    name_item.setFlags(QtCore.Qt.ItemFlag.ItemIsUserCheckable |
                                       QtCore.Qt.ItemFlag.ItemIsEnabled |
                                       QtCore.Qt.ItemFlag.ItemIsSelectable)
                    name_item.setCheckState(
                        QtCore.Qt.CheckState.Checked if e.enabled
                        else QtCore.Qt.CheckState.Unchecked)
                    name_item.setToolTip(e.source or "(inline text asset)")
                    if not e.exists:
                        name_item.setForeground(QtGui.QColor("#ff7a7a"))
                        name_item.setToolTip(f"MISSING on disk: {e.source}")
                    self.assets_table.setItem(row, 0, name_item)
                    self.assets_table.setItem(row, 1, QtWidgets.QTableWidgetItem(e.dest_display()))
                    self.assets_table.setItem(row, 2, QtWidgets.QTableWidgetItem(
                        format_size(e.size_bytes())))
                    access = QtWidgets.QTableWidgetItem(e.access_snippet())
                    access.setToolTip("Right-click → Copy access snippet")
                    self.assets_table.setItem(row, 3, access)
                self._update_assets_summary()
                self._update_asset_preview()
            finally:
                self._updating_assets = False

        def _update_assets_summary(self):
            """Refresh the totals line under the asset table."""
            entries = self.win.cfg.assets
            total = sum(e.size_bytes() for e in entries)
            enabled = [e for e in entries if e.enabled]
            n_a = sum(1 for e in enabled if e.target == "assets")
            n_d = sum(1 for e in enabled if e.target == "drawable")
            n_r = sum(1 for e in enabled if e.target == "raw")
            disabled = len(entries) - len(enabled)
            txt = (f"{len(entries)} item(s) · {format_size(total)} · "
                   f"{n_a} assets · {n_d} drawable · {n_r} raw")
            if disabled:
                txt += f" · {disabled} off"
            self.assets_size_lbl.setText(txt)

        def _update_asset_preview(self):
            """Preview the selected asset's thumbnail and details."""
            sel = self._selected_entries()
            if not sel:
                self.asset_thumb.clear()
                self.asset_thumb.setText("—")
                self.asset_info.setText("Select an asset to preview it.")
                self.asset_copy_btn.setEnabled(False)
                return
            e = sel[0]
            self.asset_copy_btn.setEnabled(True)
            pm = QtGui.QPixmap()
            if not e.is_inline and e.exists and e.suffix in ASSET_DRAWABLE_EXTS:
                pm = QtGui.QPixmap(e.source)
            if not pm.isNull():
                self.asset_thumb.setPixmap(pm.scaled(
                    44, 44, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation))
            else:
                self.asset_thumb.clear()
                self.asset_thumb.setText(e.type_icon())
            info = e.access_snippet()
            if e.is_inline:
                preview = (e.text[:90] + "…") if len(e.text) > 90 else e.text
                info += f"\nInline text asset · {format_size(e.size_bytes())}\n{preview}"
            elif e.exists:
                info += f"\n{e.source}\n{format_size(e.size_bytes())}"
                if e.is_dir:
                    info += " (whole folder, junk-filtered)"
            else:
                info += f"\nMISSING on disk: {e.source}"
            self.asset_info.setText(info)

        # --- page-level drag & drop ---
        def dragEnterEvent(self, event):
            """Accept any drag that carries URLs."""
            urls = event.mimeData().urls() if event.mimeData().hasUrls() else []
            if urls:
                event.acceptProposedAction()

        def dropEvent(self, event):
            """Add every dropped file to the asset list."""
            # v3.4: everything dropped on the page goes to the ASSET list —
            # icon drops land on the icon slot itself (no more surprise
            # icon overwrites when dropping a bundle of images).
            for url in event.mimeData().urls():
                self._add_asset(url.toLocalFile())
            event.acceptProposedAction()

        def load_persisted(self):
            """Restore icon and assets from the saved config."""
            if self.win.cfg.icon_path:
                self.set_icon(self.win.cfg.icon_path)
            self.refresh_assets()


    # ---------------------------------------------------------------------------
    # MOTION page — elements, animations & media
    # ---------------------------------------------------------------------------
    class MotionPage(Page):
        """Motion page: element table with animation, sound and image config."""

        def __init__(self, win):
            """Build the action bar, elements table and row buttons."""
            super().__init__(win, "Motion",
                             "Elements are auto-detected from your Java code. Double-click a row "
                             "to configure animations, click sounds and images.")

            bar = QtWidgets.QHBoxLayout()
            self.rescan_btn = QtWidgets.QPushButton("Rescan")
            self.auto_motion_btn = QtWidgets.QPushButton("Auto-Motion All")
            self.auto_motion_btn.setObjectName("primary")
            self.auto_motion_btn.setToolTip(
                "Apply a tasteful entrance animation to every element that has "
                "none yet — matched to each element's type (buttons pop in, "
                "lists slide up, images zoom-fade…). Elements you configured "
                "by hand are never touched.")
            self.auto_sound_btn = QtWidgets.QPushButton("Auto-Sound")
            self.auto_sound_btn.setToolTip(
                "Give every tappable element (buttons, switches, checkboxes…) "
                "a gentle built-in tap sound — only those without a sound.")
            bar.addWidget(self.rescan_btn)
            bar.addWidget(self.auto_motion_btn)
            bar.addWidget(self.auto_sound_btn)

            preset_lbl = QtWidgets.QLabel("Apply to all:")
            preset_lbl.setObjectName("muted")
            self.preset_combo = QtWidgets.QComboBox()
            self.preset_combo.addItem(ANIM_AUTO_PRESET_NAME)
            for name in ANIM_PRESETS:
                self.preset_combo.addItem(name)
            self.apply_preset_btn = QtWidgets.QPushButton("Apply Preset")
            self.apply_preset_btn.setObjectName("primary")
            bar.addStretch(1)
            bar.addWidget(preset_lbl)
            bar.addWidget(self.preset_combo)
            bar.addWidget(self.apply_preset_btn)
            self.body.addLayout(bar)

            self.elements_table = QtWidgets.QTableWidget()
            self.elements_table.setColumnCount(6)
            self.elements_table.setHorizontalHeaderLabels([
                "Element", "Type", "Animations", "Duration (ms)", "Sound", "Image"
            ])
            header = self.elements_table.horizontalHeader()
            header.setStretchLastSection(True)
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            self.elements_table.setSelectionBehavior(
                QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            self.elements_table.setSelectionMode(
                QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
            self.elements_table.setEditTriggers(
                QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            self.elements_table.setAlternatingRowColors(True)
            self.elements_table.verticalHeader().setVisible(False)
            self.elements_table.doubleClicked.connect(lambda _: self.configure_selected())
            self.body.addWidget(self.elements_table, 1)

            btns = QtWidgets.QHBoxLayout()
            self.configure_btn = QtWidgets.QPushButton("Configure Selected")
            self.configure_btn.setObjectName("primary")
            self.remove_btn = QtWidgets.QPushButton("Remove")
            self.remove_btn.setObjectName("danger")
            self.clear_btn = QtWidgets.QPushButton("Clear All")
            self.clear_btn.setObjectName("danger")
            self.hint = QtWidgets.QLabel("Hold Ctrl to multi-select")
            self.hint.setObjectName("tiny")
            btns.addWidget(self.configure_btn)
            btns.addWidget(self.remove_btn)
            btns.addWidget(self.clear_btn)
            btns.addStretch(1)
            btns.addWidget(self.hint)
            self.body.addLayout(btns)

            self.rescan_btn.clicked.connect(lambda: win.trigger_scan(force=True))
            self.apply_preset_btn.clicked.connect(self._apply_preset)
            self.auto_motion_btn.clicked.connect(
                lambda: self._auto_motion_all(only_unconfigured=True))
            self.auto_sound_btn.clicked.connect(self._auto_sound_tappables)
            self.configure_btn.clicked.connect(self.configure_selected)
            self.remove_btn.clicked.connect(self._remove_selected)
            self.clear_btn.clicked.connect(self._clear_elements)

        def selected_elements(self) -> List[ElementInfo]:
            """Return the elements selected in the table."""
            rows = sorted({i.row() for i in self.elements_table.selectedIndexes()})
            elems = []
            for r in rows:
                if 0 <= r < len(self.win.cfg.elements):
                    elems.append(self.win.cfg.elements[r])
            return elems

        def configure_selected(self):
            """Configure the selected elements via ElementConfigDialog."""
            elems = self.selected_elements()
            if not elems:
                self.win.toast(
                    "Select one or more element rows first (double-click works too).", "info")
                return
            dlg = ElementConfigDialog(elems, self)
            if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                dlg.get_config()
                self.win._after_elements_changed()
                self.win._save_settings_soon()
                self.win.toast(f"Configured {len(elems)} element(s)", "ok")

        def _apply_preset(self):
            """Apply the chosen animation preset to every element."""
            if not self.win.cfg.elements:
                self.win.toast(
                    "No elements detected yet — add some Java code on the Source page.", "info")
                return
            name = self.preset_combo.currentText()
            if name == ANIM_AUTO_PRESET_NAME:
                # v3.5 smart preset: per-type defaults for EVERY element
                for e in self.win.cfg.elements:
                    anims, dur = auto_motion_for(e.type)
                    e.animations = list(anims)
                    e.animation_duration = dur
                self.win._after_elements_changed()
                self.win._save_settings_soon()
                self.win.toast("Smart auto-motion applied to every element", "ok")
                return
            preset = ANIM_PRESETS.get(name, [])
            for e in self.win.cfg.elements:
                e.animations = preset.copy()
            self.win._after_elements_changed()
            self.win._save_settings_soon()
            self.win.toast(f"Preset applied: {name}", "ok")

        def _auto_motion_all(self, only_unconfigured: bool = True):
            """v3.5 AUTO-MOTION: per-element-type entrances for elements that
            have no animation configured yet (hand-made configs are sacred)."""
            elements = self.win.cfg.elements
            if not elements:
                self.win.toast(
                    "No elements detected yet — add some Java code on the Source page.", "info")
                return
            changed = 0
            for e in elements:
                if only_unconfigured and e.animations:
                    continue
                anims, dur = auto_motion_for(e.type)
                e.animations = list(anims)
                e.animation_duration = dur
                changed += 1
            if changed:
                self.win._after_elements_changed()
                self.win._save_settings_soon()
                self.win.toast(f"Auto-motion applied to {changed} element(s)", "ok")
            else:
                self.win.toast("Every element already has animations configured.", "info")

        def _auto_sound_tappables(self):
            """v3.5 AUTO-SOUND: gentle built-in tap for tappable elements."""
            elements = self.win.cfg.elements
            targets = [e for e in elements
                       if e.type in SOUND_AUTO_TAPPABLE and not e.sound_path]
            if not targets:
                self.win.toast("No tappable element without a sound — nothing to do.", "info")
                return
            for e in targets:
                e.sound_path = SOUND_AUTO_DEFAULT
            self.win._after_elements_changed()
            self.win._save_settings_soon()
            self.win.toast(f"Built-in tap sound → {len(targets)} element(s)", "ok")

        def _remove_selected(self):
            """Remove the selected elements and their persisted config."""
            for e in self.selected_elements():
                if e in self.win.cfg.elements:
                    self.win.cfg.elements.remove(e)
                # v3.5: also forget any persisted configuration so a removed
                # element can not resurrect on the next scan
                self.win._restored_elements.pop(e.name, None)
            self.win._after_elements_changed()
            self.win._save_settings_soon()

        def _clear_elements(self):
            """Drop every element and any persisted configuration."""
            self.win.cfg.elements.clear()
            self.win._restored_elements.clear()
            self.win._after_elements_changed()
            self.win._save_settings_soon()

        def refresh(self):
            """Rebuild the elements table from the config."""
            t = self.elements_table
            t.setRowCount(0)
            for e in self.win.cfg.elements:
                row = t.rowCount()
                t.insertRow(row)
                anims = ", ".join(ANIMATIONS.get(a, a) for a in e.animations) or "—"
                t.setItem(row, 0, QtWidgets.QTableWidgetItem(e.name))
                t.setItem(row, 1, QtWidgets.QTableWidgetItem(e.type))
                t.setItem(row, 2, QtWidgets.QTableWidgetItem(anims))
                t.setItem(row, 3, QtWidgets.QTableWidgetItem(str(e.animation_duration)))
                t.setItem(row, 4, QtWidgets.QTableWidgetItem(
                    builtin_sound_label(e.sound_path) or "—"))
                t.setItem(row, 5, QtWidgets.QTableWidgetItem(
                    Path(e.image_path).name if e.image_path else "—"))


    # ---------------------------------------------------------------------------
    # DASHBOARD page — readiness gauge, checks, automation, stats, history
    # ---------------------------------------------------------------------------
    class DashboardPage(Page):
        """Dashboard page: readiness gauge, checks, stats and history."""

        def __init__(self, win):
            """Lay out hero, project, checks, automation, stats and history cards."""
            super().__init__(win, "Dashboard",
                             "Everything you need before hitting the big green button.")

            # --- Row 1: hero + project ---
            row1 = QtWidgets.QHBoxLayout()
            row1.addWidget(self._make_hero_card())
            row1.addWidget(self._make_project_card(), 1)
            self.body.addLayout(row1)

            # --- Row 2: checks + automation ---
            row2 = QtWidgets.QHBoxLayout()
            row2.addWidget(self._make_checks_card(), 1)
            row2.addWidget(self._make_automation_card(), 1)
            self.body.addLayout(row2)

            # --- Row 3: stats + history ---
            row3 = QtWidgets.QHBoxLayout()
            row3.addWidget(self._make_stats_card(), 1)
            row3.addWidget(self._make_history_card(), 1)
            self.body.addLayout(row3)

        # --- hero ---
        def _make_hero_card(self):
            """Create the readiness gauge with install and build buttons."""
            card, lay = make_card()
            lay.setContentsMargins(24, 22, 24, 22)

            self.env_gauge = RingGauge(self, 128, "READY")
            lay.addWidget(self.env_gauge, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)

            self.env_summary = QtWidgets.QLabel("Scanning environment…")
            self.env_summary.setObjectName("muted")
            self.env_summary.setWordWrap(True)
            self.env_summary.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
            lay.addWidget(self.env_summary)

            # v3.6: one-click download & install for everything missing
            self.install_missing_btn = QtWidgets.QPushButton("Download & Install Missing")
            self.install_missing_btn.setObjectName("installBtn")
            self.install_missing_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            self.install_missing_btn.setToolTip(
                "Downloads every missing library & tool into the portable Data "
                "folder beside APK Forge — your system is never touched.")
            self.install_missing_btn.clicked.connect(lambda: self.win.open_installer())
            self.install_missing_btn.hide()  # shown when something is missing
            lay.addWidget(self.install_missing_btn)

            self.build_now_btn = GlowButton("BUILD APK NOW", idle_pulse=True)
            self.build_now_btn.setObjectName("buildBtn")
            self.build_now_btn.setMinimumHeight(48)
            self.build_now_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            self.build_now_btn.clicked.connect(self.win.on_build)
            lay.addWidget(self.build_now_btn)

            open_out = QtWidgets.QPushButton("Open Output Folder")
            open_out.clicked.connect(self.win.on_open_output)
            lay.addWidget(open_out)
            return card

        # --- project ---
        def _make_project_card(self):
            """Create the project summary rows and quick actions."""
            card, lay = make_card("PROJECT")

            rows = {}
            for key in ("App name", "Package", "Version", "Mode", "Elements",
                        "Components", "Icon", "Assets"):
                row, lbl = kv_row(key)
                rows[key] = lbl
                lay.addWidget(row)
            self.lbl_app = rows["App name"]
            self.lbl_pkg = rows["Package"]
            self.lbl_ver = rows["Version"]
            self.lbl_mode = rows["Mode"]
            self.lbl_elems = rows["Elements"]
            self.lbl_comp = rows["Components"]
            self.lbl_icon = rows["Icon"]
            self.lbl_assets = rows["Assets"]

            btns = QtWidgets.QHBoxLayout()
            load_btn = QtWidgets.QPushButton("Load Java…")
            new_btn = QtWidgets.QPushButton("New Project")
            guide_btn = QtWidgets.QPushButton("AI Guide")
            load_btn.clicked.connect(self.win.on_load_java)
            new_btn.clicked.connect(self.win.on_new_project)
            guide_btn.clicked.connect(lambda: self.win.goto_page("aiguide"))
            btns.addWidget(load_btn)
            btns.addWidget(new_btn)
            btns.addWidget(guide_btn)
            lay.addLayout(btns)
            return card

        # --- checks ---
        def _make_checks_card(self):
            """Create the readiness checks list card."""
            card, lay = make_card("READY TO BUILD?")
            self.checks_header = QtWidgets.QLabel("—")
            self.checks_header.setObjectName("muted")
            lay.addWidget(self.checks_header)
            self.checks_list = QtWidgets.QVBoxLayout()
            self.checks_list.setSpacing(6)
            lay.addLayout(self.checks_list)
            return card

        # --- automation ---
        def _make_automation_card(self):
            """Create the automation toggles card."""
            card, lay = make_card("AUTOMATION CENTER", "Everything APK Forge does for you.")

            self.auto_cbs = {}
            for key, label in AUTO_AUTOMATIONS:
                cb = QtWidgets.QCheckBox(label)
                cb.setChecked(self.win.auto.get(key, True))
                cb.toggled.connect(lambda on, k=key: self.win.set_auto(k, on))
                self.auto_cbs[key] = cb
                lay.addWidget(cb)
            return card

        # --- stats ---
        def _make_stats_card(self):
            """Create the animated workspace statistics grid."""
            card, lay = make_card("WORKSPACE STATS")

            grid = QtWidgets.QGridLayout()
            grid.setSpacing(14)
            self.stat_elements = CountUpLabel("0")
            self.stat_perms = CountUpLabel("0")
            self.stat_assets = CountUpLabel("0")
            self.stat_loc = CountUpLabel("0")
            stats = [
                ("UI elements", self.stat_elements, "#44d62c"),
                ("Permissions", self.stat_perms, "#ffb454"),
                ("Assets", self.stat_assets, "#9a9c98"),
                ("Java lines", self.stat_loc, "#7ec8a9"),
            ]
            for i, (label, w, color) in enumerate(stats):
                w.setStyleSheet(f"color:{color}; font-size:26px; font-weight:800;"
                                "background:transparent;")
                cap = QtWidgets.QLabel(label.upper())
                cap.setObjectName("cardSection")
                cell = QtWidgets.QVBoxLayout()
                cell.setSpacing(2)
                cell.addWidget(w)
                cell.addWidget(cap)
                grid.addLayout(cell, i // 2, i % 2)
            lay.addLayout(grid)
            return card

        # --- history ---
        def _make_history_card(self):
            """Create the build history list card."""
            card, lay = make_card("BUILD HISTORY", "Your last builds — double-click to open.")

            self.history_list = QtWidgets.QListWidget()
            self.history_list.setMaximumHeight(160)
            self.history_list.itemDoubleClicked.connect(self._open_history_item)
            lay.addWidget(self.history_list, 1)
            return card

        def _open_history_item(self, item):
            """Open the folder of a double-clicked history entry."""
            apk = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if apk and Path(apk).exists():
                QtGui.QDesktopServices.openUrl(
                    QtCore.QUrl.fromLocalFile(str(Path(apk).parent)))

        # --- refresh ---
        def refresh(self):
            """Refresh every dashboard card from the current state."""
            win = self.win
            cfg = win.cfg

            self.lbl_app.setText(cfg.app_name or "—")
            self.lbl_pkg.setText(cfg.package or "—")
            self.lbl_ver.setText(f"{cfg.version_name} (code {cfg.version_code})")

            payload = win.last_scan or {}
            analysis: "JavaAnalysis" = payload.get("analysis")
            if analysis is not None and analysis.is_full:
                self.lbl_mode.setText(f"Full app · {len(analysis.type_names)} class(es)")
                comps = [f"{len(analysis.activities)} activit{'y' if len(analysis.activities) == 1 else 'ies'}"]
                if analysis.services:
                    comps.append(f"{len(analysis.services)} service(s)")
                if analysis.receivers:
                    comps.append(f"{len(analysis.receivers)} receiver(s)")
                self.lbl_comp.setText(" · ".join(comps))
            elif analysis is not None:
                self.lbl_mode.setText("Snippet (auto-wrapped)")
                self.lbl_comp.setText("1 auto-generated activity")
            else:
                self.lbl_mode.setText("—")
                self.lbl_comp.setText("—")

            total = len(cfg.elements)
            configured = sum(1 for e in cfg.elements
                             if e.animations or e.sound_path or e.image_path)
            self.lbl_elems.setText(f"{total} detected · {configured} configured")
            self.lbl_icon.setText(Path(cfg.icon_path).name if cfg.icon_path else "Default")
            n_assets = len(cfg.assets)
            if n_assets:
                n_a = sum(1 for e in cfg.assets if e.target == "assets")
                n_d = sum(1 for e in cfg.assets if e.target == "drawable")
                n_r = sum(1 for e in cfg.assets if e.target == "raw")
                bits = [f"{n_a} asset(s)"]
                if n_d:
                    bits.append(f"{n_d} drawable")
                if n_r:
                    bits.append(f"{n_r} raw")
                self.lbl_assets.setText(" · ".join(bits))
            else:
                self.lbl_assets.setText("0 items")

            # stats (animated count-up)
            perms = (win.checked_permissions() if hasattr(win, "checked_permissions")
                     else cfg.permissions)
            self.stat_elements.setValue(total)
            self.stat_perms.setValue(len(perms))
            self.stat_assets.setValue(len(cfg.assets))
            self.stat_loc.setValue(analysis.loc if analysis else 0)

            # checks
            checks = win.collect_checks()
            ok_count = sum(1 for c in checks if c["ok"])
            self.checks_header.setText(f"{ok_count}/{len(checks)} checks passed")
            clear_layout(self.checks_list)
            for c in checks:
                row = QtWidgets.QWidget()
                h = QtWidgets.QHBoxLayout(row)
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(10)
                dot = QtWidgets.QLabel("●")
                color = "#44d62c" if c["ok"] else ("#ffb454" if c.get("warn") else "#ff7a7a")
                dot.setStyleSheet(f"color:{color}; font-size:14px; background:transparent;")
                lbl = QtWidgets.QLabel(c["label"])
                lbl.setObjectName("kvValue")
                h.addWidget(dot)
                h.addWidget(lbl, 1)
                # v3.6: a missing library or tool gets a green download button
                # right beside its name — one click installs it into ./Data
                if not c["ok"] and c.get("install"):
                    inst = QtWidgets.QPushButton("Install")
                    inst.setObjectName("installMini")
                    inst.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
                    inst.setToolTip(f"Download & install "
                                    f"{INSTALL_ITEMS[c['install']]['label']} "
                                    f"({INSTALL_ITEMS[c['install']]['size']}) into the "
                                    f"Data folder")
                    inst.clicked.connect(
                        lambda _=False, k=c["install"]: win.open_installer([k]))
                    h.addWidget(inst)
                if not c["ok"] and c.get("page"):
                    fix = QtWidgets.QPushButton("Go →")
                    fix.setObjectName("mini")
                    fix.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
                    fix.clicked.connect(lambda _=False, p=c["page"]: win.goto_page(p))
                    h.addWidget(fix)
                self.checks_list.addWidget(row)

            # v3.6: the hero's big install button mirrors the missing set
            if hasattr(self, "install_missing_btn"):
                missing = win.missing_installables()
                self.install_missing_btn.setVisible(bool(missing))
                if missing:
                    self.install_missing_btn.setText(
                        f"Download & Install Missing ({len(missing)})")

            # history
            self.history_list.clear()
            for entry in win.build_history[:10]:
                apk = entry.get("apk", "")
                size_mb = entry.get("size", 0) / 1024 / 1024
                item = QtWidgets.QListWidgetItem(
                    f"{Path(apk).name}   ·   {size_mb:.1f} MB   ·   {entry.get('time', '')}")
                item.setToolTip(apk)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, apk)
                self.history_list.addItem(item)


    # ---------------------------------------------------------------------------
    # AI GUIDE page — make AI models write APK-Forge-perfect Java
    # ---------------------------------------------------------------------------
    class AiGuidePage(Page):
        """AI Guide page: copy the coding guide, snippets and templates."""

        def __init__(self, win):
            """Build the guide hero plus capabilities, shortcuts, template cards."""
            super().__init__(win, "AI Guide",
                             "Give AI models the coding rules of this forge — they will produce "
                             "working Android Java on the first try.")

            # --- copy guide hero ---
            card, lay = make_card()
            title = QtWidgets.QLabel("AI CODING GUIDE v2")
            title.setObjectName("cardTitle")
            lay.addWidget(title)
            desc = QtWidgets.QLabel(
                "Copy this precision guide into your AI chat (as a system prompt or "
                "first message) BEFORE asking for an app. It teaches the model the "
                "exact contract: one all-in-one Java file, plain framework classes, "
                "programmatic UI, correct asset access, no build-breakers — plus a "
                "self-check list it ticks before answering.")
            desc.setObjectName("muted")
            desc.setWordWrap(True)
            lay.addWidget(desc)

            btns = QtWidgets.QHBoxLayout()
            self.copy_guide_btn = GlowButton("COPY AI CODING GUIDE", idle_pulse=True)
            self.copy_guide_btn.setObjectName("primary")
            self.copy_guide_btn.setMinimumHeight(44)
            self.copy_guide_btn.clicked.connect(self._copy_guide)
            btns.addWidget(self.copy_guide_btn, 1)
            self.view_guide_btn = QtWidgets.QPushButton("View Guide")
            self.view_guide_btn.clicked.connect(self._view_guide)
            btns.addWidget(self.view_guide_btn)
            lay.addLayout(btns)
            self.body.addWidget(card)

            # --- capabilities + shortcuts ---
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self._make_capabilities_card(), 1)
            row.addWidget(self._make_shortcuts_card(), 1)
            self.body.addLayout(row)

            # --- template quick insert ---
            self.body.addWidget(self._make_templates_card())

            # --- v3.4: asset access snippets ---
            self.body.addWidget(self._make_asset_snippets_card())

        def _copy_guide(self):
            """Copy the AI coding guide to the clipboard."""
            QtGui.QGuiApplication.clipboard().setText(AI_CODING_GUIDE)
            self.win.toast("AI coding guide v2 copied — paste it into any AI chat "
                           "as the first message.", "ok")
            self.win.log(f"[{log_time()}] AI coding guide v2 copied to clipboard")

        def _view_guide(self):
            """Show the full guide in a read-only dialog."""
            box = QtWidgets.QDialog(self)
            box.setWindowTitle("AI Coding Guide")
            box.resize(720, 640)
            v = QtWidgets.QVBoxLayout(box)
            text = QtWidgets.QPlainTextEdit(AI_CODING_GUIDE)
            text.setReadOnly(True)
            v.addWidget(text)
            close = QtWidgets.QPushButton("Close")
            close.clicked.connect(box.accept)
            v.addWidget(close)
            box.exec()

        def _make_capabilities_card(self):
            """Create the supported-features checklist card."""
            card, lay = make_card("WHAT THE FORGE SUPPORTS")
            caps = [
                ("Multiple classes in ONE file", "auto-split into .java files at build"),
                ("All framework APIs", "Activity, Service, BroadcastReceiver, sensors…"),
                ("Java 8 syntax", "lambdas, method refs, anonymous classes, generics"),
                ("R.* references", "R.drawable / R.raw / R.anim / R.string compile"),
                ("Assets & resources (v3.4)", "getAssets() + drawable/raw with real ids"),
                ("Auto-permissions", "detected from your code usage"),
                ("Multi-activity apps", "startActivity() — all activities registered"),
                ("Custom views", "extend View, override onDraw(Canvas)"),
            ]
            for title, sub in caps:
                r = QtWidgets.QWidget()
                h = QtWidgets.QHBoxLayout(r)
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(10)
                dot = QtWidgets.QLabel("•")
                dot.setStyleSheet("color:#44d62c; font-weight:800; background:transparent;")
                col = QtWidgets.QVBoxLayout()
                col.setSpacing(0)
                t = QtWidgets.QLabel(title)
                t.setObjectName("kvValue")
                s = QtWidgets.QLabel(sub)
                s.setObjectName("tiny")
                col.addWidget(t)
                col.addWidget(s)
                h.addWidget(dot)
                h.addLayout(col, 1)
                lay.addWidget(r)
            return card

        def _make_shortcuts_card(self):
            """Create the keyboard shortcuts card."""
            card, lay = make_card("KEYBOARD SHORTCUTS")
            shortcuts = [
                ("Ctrl+K", "Command palette"),
                ("Ctrl+B", "Build APK"),
                ("Ctrl+S", "Save Java code"),
                ("Ctrl+O", "Open a .java file"),
                ("F5", "Re-analyze code"),
                ("Ctrl+1 … 6", "Go to page"),
                ("Ctrl+`", "Toggle console"),
                ("Esc", "Close palette / dialog"),
            ]
            for keys, what in shortcuts:
                r = QtWidgets.QWidget()
                h = QtWidgets.QHBoxLayout(r)
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(10)
                h.addWidget(kbd(keys))
                w = QtWidgets.QLabel(what)
                w.setObjectName("kvValue")
                h.addWidget(w, 1)
                lay.addWidget(r)
            return card

        def _make_templates_card(self):
            """Create the one-click demo app grid."""
            card, lay = make_card(
                "ONE-CLICK DEMO APPS",
                "Insert a complete, buildable app to see the patterns in action.")
            grid = QtWidgets.QGridLayout()
            grid.setSpacing(8)
            quick = [
                ("Full Class Skeleton", "Full Class Skeleton (full class)"),
                ("Tap Counter", "Tap Counter (snippet)"),
                ("WebView App", "WebView App (full class)"),
                ("Calculator (3 classes)", "Calculator (full class, multi-class demo)"),
                ("Notes (SharedPreferences)", "Notes with SharedPreferences (full class)"),
                ("Canvas Drawing", "Canvas Drawing (full class, custom View)"),
                ("Sensor Dashboard (+Service)", "Sensor Dashboard (full class + service)"),
                ("List + Adapter (3 classes)", "List with Adapter (full class, 3 classes)"),
                ("Notifications + Alarm", "Notification + Alarm (full class, receiver)"),
                ("Threaded Progress", "Threaded Progress (full class)"),
            ]
            for i, (label, key) in enumerate(quick):
                b = QtWidgets.QPushButton(f"{label}")
                b.setObjectName("mini")
                b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
                b.clicked.connect(lambda _=False, k=key: self.win.insert_template(k))
                grid.addWidget(b, i // 2, i % 2)
            lay.addLayout(grid)
            return card

        def _make_asset_snippets_card(self):
            """v3.4: battle-tested asset access patterns with one-click copy —
            paste them into your code (or into the AI prompt) so asset loading
            works on the first try."""
            card, lay = make_card(
                "ASSET ACCESS SNIPPETS",
                "Copy-paste patterns for files bundled on the Design page — "
                "images, sounds, JSON and web pages.")
            grid = QtWidgets.QGridLayout()
            grid.setSpacing(8)
            for i, (label, code) in enumerate(ASSET_SNIPPETS):
                b = QtWidgets.QPushButton(f"{label}")
                b.setObjectName("mini")
                b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
                b.setToolTip(code[:220] + ("…" if len(code) > 220 else ""))
                b.clicked.connect(lambda _=False, c=code: self._copy_snippet(c))
                grid.addWidget(b, i // 2, i % 2)
            lay.addLayout(grid)
            return card

        def _copy_snippet(self, code: str):
            """Copy an asset access snippet to the clipboard."""
            QtGui.QGuiApplication.clipboard().setText(code)
            self.win.toast("Snippet copied — paste it into your Java code.", "ok")
            self.win.log(f"[{log_time()}] Asset snippet copied")


    # ---------------------------------------------------------------------------
    # SETTINGS page — identity, versions, compatibility, permissions, advanced
    # ---------------------------------------------------------------------------
    class SettingsPage(Page):
        """Settings page: identity, versions, compatibility, permissions, advanced."""

        def __init__(self, win):
            """Build the identity, version, compat, permissions and advanced cards."""
            super().__init__(win, "Settings",
                             "Your app's identity and build options — every change is auto-saved.")

            row = QtWidgets.QHBoxLayout()
            row.addWidget(self._make_identity_card())
            right = QtWidgets.QVBoxLayout()
            right.addWidget(self._make_version_card())
            right.addWidget(self._make_compat_card())
            row.addLayout(right, 1)
            self.body.addLayout(row)

            self.body.addWidget(self._make_permissions_card())
            self.body.addWidget(self._make_advanced_card())

        # --- identity ---
        def _make_identity_card(self):
            """Create the app identity fields card."""
            card, lay = make_card("APP IDENTITY")

            lay.addWidget(QtWidgets.QLabel("App name"))
            self.app_name_edit = QtWidgets.QLineEdit(APP_DEFAULTS["app_name"])
            lay.addWidget(self.app_name_edit)

            lay.addWidget(QtWidgets.QLabel("Package name"))
            pkg_row = QtWidgets.QHBoxLayout()
            self.package_edit = QtWidgets.QLineEdit(APP_DEFAULTS["package"])
            self.pkg_auto_btn = QtWidgets.QPushButton("AUTO")
            self.pkg_auto_btn.setObjectName("mini")
            self.pkg_auto_btn.setCheckable(True)
            self.pkg_auto_btn.setChecked(True)
            self.pkg_auto_btn.setToolTip(
                "When ON, the package name is generated automatically from the app name.")
            pkg_row.addWidget(self.package_edit, 1)
            pkg_row.addWidget(self.pkg_auto_btn)
            lay.addLayout(pkg_row)
            self.pkg_valid_lbl = QtWidgets.QLabel("")
            self.pkg_valid_lbl.setObjectName("tiny")
            lay.addWidget(self.pkg_valid_lbl)

            lay.addWidget(QtWidgets.QLabel("Activity name"))
            self.activity_edit = QtWidgets.QLineEdit(APP_DEFAULTS["activity_name"])
            lay.addWidget(self.activity_edit)
            hint = QtWidgets.QLabel(
                "Auto-detected for full classes (MainActivity or your first Activity). "
                "Used as the class name for snippets.")
            hint.setObjectName("tiny")
            hint.setWordWrap(True)
            lay.addWidget(hint)

            self.app_name_edit.textEdited.connect(self._on_app_name_edited)
            self.package_edit.textEdited.connect(self._pkg_edited_manually)
            return card

        def _pkg_edited_manually(self, _text):
            """Turn AUTO package derivation off on manual edits."""
            # v3.1: typing a package by hand turns AUTO derivation OFF — it
            # used to silently overwrite the manual value on the next rename.
            if self.pkg_auto_btn.isChecked():
                self.pkg_auto_btn.setChecked(False)
            self._validate_package()

        def _on_app_name_edited(self, _text):
            """Derive the package from the app name while typing."""
            if self.pkg_auto_btn.isChecked():
                self.package_edit.setText(suggest_package(self.app_name_edit.text()))
            self._validate_package()
            self.win._save_settings_soon()
            self.win.refresh_dashboard_soon()

        def _validate_package(self):
            """Show whether the current package name is valid."""
            pkg = self.package_edit.text().strip()
            if not pkg:
                self.pkg_valid_lbl.setText("")
                return
            if package_is_valid(pkg):
                self.pkg_valid_lbl.setText("valid package")
                self.pkg_valid_lbl.setStyleSheet("color:#44d62c; background:transparent;")
            else:
                self.pkg_valid_lbl.setText("invalid — expected com.example.app style")
                self.pkg_valid_lbl.setStyleSheet("color:#ff7a7a; background:transparent;")
            self.win._save_settings_soon()

        # --- version ---
        def _make_version_card(self):
            """Create the version name and version code card."""
            card, lay = make_card("VERSION")
            h = QtWidgets.QHBoxLayout()
            col1 = QtWidgets.QVBoxLayout()
            col1.addWidget(QtWidgets.QLabel("Version name"))
            self.vname_edit = QtWidgets.QLineEdit(APP_DEFAULTS["version_name"])
            col1.addWidget(self.vname_edit)
            col2 = QtWidgets.QVBoxLayout()
            col2.addWidget(QtWidgets.QLabel("Version code"))
            self.vcode_spin = QtWidgets.QSpinBox()
            self.vcode_spin.setRange(1, 2_000_000_000)
            self.vcode_spin.setValue(APP_DEFAULTS["version_code"])
            col2.addWidget(self.vcode_spin)
            h.addLayout(col1, 1)
            h.addLayout(col2)
            lay.addLayout(h)
            tip = QtWidgets.QLabel("Tip: enable 'Auto version bump' on the Dashboard.")
            tip.setObjectName("tiny")
            lay.addWidget(tip)
            return card

        # --- compatibility ---
        def _make_compat_card(self):
            """Create the minimum and target SDK pickers."""
            card, lay = make_card("COMPATIBILITY")
            h = QtWidgets.QHBoxLayout()
            col1 = QtWidgets.QVBoxLayout()
            col1.addWidget(QtWidgets.QLabel("Minimum SDK"))
            self.min_sdk_combo = QtWidgets.QComboBox()
            for api in sorted(SDK_LABELS):
                self.min_sdk_combo.addItem(sdk_label(api), api)
            col1.addWidget(self.min_sdk_combo)
            col2 = QtWidgets.QVBoxLayout()
            col2.addWidget(QtWidgets.QLabel("Target SDK"))
            self.target_sdk_combo = QtWidgets.QComboBox()
            for api in sorted(SDK_LABELS):
                self.target_sdk_combo.addItem(sdk_label(api), api)
            col2.addWidget(self.target_sdk_combo)
            h.addLayout(col1, 1)
            h.addLayout(col2)
            lay.addLayout(h)
            self.minsdk_hint = QtWidgets.QLabel("")
            self.minsdk_hint.setObjectName("tiny")
            self.minsdk_hint.setWordWrap(True)
            lay.addWidget(self.minsdk_hint)
            return card

        def set_minsdk_hint(self, required: int):
            """Warn when the code needs a higher API than selected."""
            if required and required > (self.min_sdk_combo.currentData() or 21):
                self.minsdk_hint.setText(
                    f"Your code needs API {required}+ — raise the minimum (the build "
                    f"does it automatically when Auto min SDK is on).")
                self.minsdk_hint.setStyleSheet("color:#ffb454; background:transparent;")
            else:
                self.minsdk_hint.setText("")
                self.minsdk_hint.setStyleSheet("")

        # --- permissions ---
        def _make_permissions_card(self):
            """Create the permissions checklist card."""
            card, lay = make_card("PERMISSIONS",
                                  "Tick what your app needs — or let code analysis suggest them "
                                  "from the Source page diagnostics.")

            self.perm_list = QtWidgets.QListWidget()
            self.perm_list.setMaximumHeight(240)
            lay.addWidget(self.perm_list, 1)

            bottom = QtWidgets.QHBoxLayout()
            self.perm_count_lbl = QtWidgets.QLabel("0 selected")
            self.perm_count_lbl.setObjectName("tiny")
            add_custom = QtWidgets.QPushButton("Add Custom")
            add_custom.clicked.connect(self._add_custom_permission)
            bottom.addWidget(self.perm_count_lbl)
            bottom.addStretch(1)
            bottom.addWidget(add_custom)
            lay.addLayout(bottom)

            self.perm_list.itemChanged.connect(lambda _item: self._on_perm_changed())
            return card

        def _add_permission_item(self, label: str, perm: str, custom: bool = False):
            """Append one checkable permission row to the list."""
            item = QtWidgets.QListWidgetItem(("*  " if custom else "") + f"{label}  —  {perm}")
            item.setToolTip(perm)
            item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.CheckState.Unchecked)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, perm)
            self.perm_list.addItem(item)
            return item

        def _add_custom_permission(self):
            """Ask for and add a custom permission."""
            text, ok = QtWidgets.QInputDialog.getText(
                self, "Add custom permission",
                "Permission (android.permission. prefix is added automatically):",
                text="android.permission.")
            if not ok or not text.strip():
                return
            perm = text.strip()
            if not perm.startswith("android.permission."):
                perm = "android.permission." + perm.split(".")[-1]
            if any(self.perm_list.item(i).data(QtCore.Qt.ItemDataRole.UserRole) == perm
                   for i in range(self.perm_list.count())):
                self.win.toast(f"{perm} is already in the list.", "info")
                return
            item = self._add_permission_item(perm.split(".")[-1], perm, custom=True)
            item.setCheckState(QtCore.Qt.CheckState.Checked)
            self._on_perm_changed()

        def _on_perm_changed(self):
            """Update the selected count and schedule a save."""
            checked = self.checked_permissions()
            self.perm_count_lbl.setText(f"{len(checked)} selected")
            self.win._save_settings_soon()

        def checked_permissions(self) -> List[str]:
            """Return the currently checked permission strings."""
            perms = []
            for i in range(self.perm_list.count()):
                item = self.perm_list.item(i)
                if item.checkState() == QtCore.Qt.CheckState.Checked:
                    perms.append(item.data(QtCore.Qt.ItemDataRole.UserRole))
            return perms

        def set_permissions(self, perms: List[str]):
            """Check exactly the given permissions in the list."""
            for i in range(self.perm_list.count()):
                item = self.perm_list.item(i)
                item.setCheckState(
                    QtCore.Qt.CheckState.Checked
                    if item.data(QtCore.Qt.ItemDataRole.UserRole) in perms
                    else QtCore.Qt.CheckState.Unchecked)
            self._on_perm_changed()

        def ensure_permission_items(self, perms: List[str]):
            """Create list items for permissions not present yet (used by one-click fix)."""
            known = {self.perm_list.item(i).data(QtCore.Qt.ItemDataRole.UserRole)
                     for i in range(self.perm_list.count())}
            for perm in perms:
                if perm not in known:
                    self._add_permission_item(perm.split(".")[-1], perm, custom=True)

        # --- advanced ---
        def _make_advanced_card(self):
            """Create toolchain paths, signing fields and build options."""
            card, lay = make_card("ADVANCED", "Toolchain paths & signing — every path has an AUTO button that points it at the portable Data folder.")

            def path_row(label, placeholder="", auto_kind=None):
                """One labeled path row: edit + AUTO button for auto_kind."""
                row = QtWidgets.QHBoxLayout()
                edit = QtWidgets.QLineEdit()
                edit.setPlaceholderText(placeholder)
                if auto_kind:
                    auto = QtWidgets.QPushButton("Auto")
                    auto.setObjectName("autoPathBtn")
                    auto.setToolTip(
                        "Set this path to where the item lives in the portable "
                        "Data folder beside the code (or create it there).")
                    auto.clicked.connect(
                        lambda _=False, k=auto_kind, e=edit: self._auto_path(k, e))
                browse = QtWidgets.QPushButton("Browse…")
                row.addWidget(edit, 1)
                if auto_kind:
                    row.addWidget(auto)
                row.addWidget(browse)
                lay.addWidget(QtWidgets.QLabel(label))
                lay.addLayout(row)
                return edit, browse

            self.android_jar_edit, b1 = path_row(
                "android.jar (Android platform)", "auto-detected from ./androidjar/",
                auto_kind="androidjar")
            self.jdk_bin_edit, b2 = path_row(
                "JDK bin folder",
                "JDK 17 from the Data folder — or a JDK 17 bin folder set by hand",
                auto_kind="jdk")
            self.buildtools_edit, b6 = path_row(
                "Build-tools folder", "auto-detected from ./Data or beside the script",
                auto_kind="buildtools")
            self.out_dir_edit, b3 = path_row(
                "Output folder (empty = ./dist)", auto_kind="dist")
            self.ks_path_edit, b4 = path_row(
                "Keystore (empty = auto-generated debug keystore)", auto_kind="keystore")
            self.manifest_edit, b5 = path_row(
                "Custom AndroidManifest.xml (optional)", auto_kind="manifest")

            b1.clicked.connect(lambda: self._browse_file(
                self.android_jar_edit, "android.jar (android.jar)",
                "android.jar (android.jar);;All Files (*)"))
            b2.clicked.connect(lambda: self._browse_dir(self.jdk_bin_edit))
            b6.clicked.connect(lambda: self._browse_dir(self.buildtools_edit))
            b3.clicked.connect(lambda: self._browse_dir(self.out_dir_edit))
            b4.clicked.connect(lambda: self._browse_file(
                self.ks_path_edit, "Keystore (*.keystore *.jks)",
                "Keystore (*.keystore *.jks);;All Files (*)"))
            b5.clicked.connect(lambda: self._browse_file(
                self.manifest_edit, "AndroidManifest.xml",
                "AndroidManifest.xml (*.xml);;All Files (*)"))

            sign_row = QtWidgets.QHBoxLayout()

            def small_field(label):
                """One labeled single-line settings field."""
                col = QtWidgets.QVBoxLayout()
                col.addWidget(QtWidgets.QLabel(label))
                edit = QtWidgets.QLineEdit()
                col.addWidget(edit)
                return col, edit

            c1, self.ks_pass_edit = small_field("Keystore password")
            self.ks_pass_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.ks_pass_edit.setText("android")
            c2, self.key_alias_edit = small_field("Key alias")
            self.key_alias_edit.setText("androiddebugkey")
            c3, self.key_pass_edit = small_field("Key password")
            self.key_pass_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            self.key_pass_edit.setText("android")
            for c in (c1, c2, c3):
                sign_row.addLayout(c, 1)
            lay.addLayout(sign_row)

            opts = QtWidgets.QHBoxLayout()
            self.aapt2_cb = QtWidgets.QCheckBox("Use aapt2 (default: aapt)")
            self.keep_temp_cb = QtWidgets.QCheckBox("Keep temp build folders (debug)")
            opts.addWidget(self.aapt2_cb)
            opts.addWidget(self.keep_temp_cb)
            opts.addStretch(1)
            import_manifest_btn = QtWidgets.QPushButton("Import settings from manifest")
            import_manifest_btn.clicked.connect(self._import_manifest)
            opts.addWidget(import_manifest_btn)
            lay.addLayout(opts)
            return card

        def _browse_file(self, edit, title, filt):
            """Browse for a file and store it in the given edit."""
            p, _ = QtWidgets.QFileDialog.getOpenFileName(self, title, "", filt)
            if p:
                edit.setText(p)
                self.win._save_settings_soon()
                self.win.refresh_environment()

        def _browse_dir(self, edit):
            """Browse for a folder and store it in the given edit."""
            p = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
            if p:
                edit.setText(p)
                self.win._save_settings_soon()
                self.win.refresh_environment()

        def _auto_path(self, kind: str, edit):
            """AUTO — point a path row at its home inside the portable Data
            folder beside the code.

            When the item isn't there yet the button explains what's missing
            and (for installable toolchain items) offers the one-click Data
            installer instead of failing silently.
            """
            win = self.win
            names = {
                "androidjar": "android.jar (API 33)",
                "jdk": "the JDK",
                "buildtools": "Android build-tools 33.0.3",
                "dist": "the output folder",
                "keystore": "the debug keystore",
                "manifest": "a custom AndroidManifest.xml",
            }
            what = names.get(kind, "This item")
            resolved = data_path_for(kind)

            if resolved:
                edit.setText(resolved)
                win._save_settings_soon()
                note = ""
                if kind == "keystore" and not Path(resolved).exists():
                    note = " (generated automatically on the first build)"
                win.log(f"[{log_time()}] Auto path — {what} → {resolved}{note}")
                win.toast(f"Auto path set{note}", "ok")
                if kind in ("buildtools", "jdk", "androidjar"):
                    win.refresh_environment()
                return

            # --- nothing to point at — explain & offer the installer ---
            install_keys = {"androidjar": "androidjar", "jdk": "jdk",
                            "buildtools": "buildtools"}
            key = install_keys.get(kind)
            if key and key in win.missing_installables():
                # v3.8: a WRONG-VERSION copy inside Data is named, never
                # silently pointed at
                if kind == "jdk":
                    wrong = data_jdk_mismatches()
                elif kind == "buildtools":
                    wrong = data_buildtools_mismatches()
                elif kind == "androidjar":
                    m = data_androidjar_mismatch()
                    wrong = [f"android.jar {m}"] if m else []
                else:
                    wrong = []
                pin_names = {
                    "jdk": f"JDK {REQUIRED_JDK_MAJOR}",
                    "buildtools": f"build-tools {REQUIRED_BUILD_TOOLS}",
                    "androidjar": f"android.jar (API {REQUIRED_ANDROID_API})"}
                if wrong:
                    detail = (f"The Data folder contains {', '.join(wrong)}, but "
                              f"APK Forge builds with {pin_names[kind]}.")
                    title = "Wrong version in the Data folder"
                else:
                    detail = (f"{what[0].upper() + what[1:]} is not installed in "
                              "the portable Data folder beside the code.")
                    title = "Not in the Data folder yet"
                btn = QtWidgets.QMessageBox.question(
                    self, title,
                    detail + "\n\nDownload & install the right version now?",
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No)
                if btn == QtWidgets.QMessageBox.StandardButton.Yes:
                    win.open_installer([key])
                return
            if key:
                QtWidgets.QMessageBox.information(
                    self, "Not in the Data folder",
                    f"{what[0].upper() + what[1:]} is not inside the portable "
                    "Data folder.\n\n"
                    "A copy elsewhere on this machine is being used — the "
                    "Dashboard's installer can still fetch a portable copy "
                    "into:\n" + str(DATA_DIR))
                return
            QtWidgets.QMessageBox.information(
                self, "The Data folder isn't there yet",
                "The portable Data folder beside the code doesn't exist or has "
                f"no home for {what}.\n\n"
                "Install a library first (Dashboard → Download & Install "
                "Missing), then AUTO can point at it.")

        def _import_manifest(self):
            """Read an AndroidManifest.xml into the settings fields."""
            p, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Import AndroidManifest.xml", "",
                "AndroidManifest.xml (*.xml);;All Files (*)")
            if not p:
                return
            try:
                data = parse_manifest(p)
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Import failed", f"Could not parse manifest:\n{e}")
                return
            if data.get("package"):
                self.package_edit.setText(data["package"])
            if data.get("version_name"):
                self.vname_edit.setText(data["version_name"])
            if data.get("version_code", "").isdigit():
                self.vcode_spin.setValue(int(data["version_code"]))
            if data.get("min_sdk", "").isdigit():
                self._select_combo(self.min_sdk_combo, int(data["min_sdk"]))
            if data.get("target_sdk", "").isdigit():
                self._select_combo(self.target_sdk_combo, int(data["target_sdk"]))
            if data.get("activity_name"):
                self.activity_edit.setText(data["activity_name"])
            if data.get("permissions"):
                self.ensure_permission_items(data["permissions"])
                self.set_permissions(data["permissions"])
            self._validate_package()
            self.win._save_settings_soon()
            self.win.log(f"[{log_time()}] Manifest imported: {p}")
            self.win.toast("Settings updated from manifest.", "ok")

        def _select_combo(self, combo: QtWidgets.QComboBox, value: int):
            """Select the combo item whose data equals the value."""
            for i in range(combo.count()):
                if combo.itemData(i) == value:
                    combo.setCurrentIndex(i)
                    return


    # ---------------------------------------------------------------------------
    # Background workers — the UI NEVER freezes
    # ---------------------------------------------------------------------------
    class EnvScannerThread(QtCore.QThread):
        """Scans the toolchain (build-tools, android.jar, JDK) off the UI thread.

        v3.1: run() is fully guarded — a scan failure can no longer abort the
        process OR leave the splash overlay blocking the window forever.
        """
        logLine = QtCore.pyqtSignal(str)
        result = QtCore.pyqtSignal(dict)
        failed = QtCore.pyqtSignal(str)

        def __init__(self, script_dir: str, tools_dir_override: str = ""):
            """Store the script dir and the optional build-tools override."""
            super().__init__()
            self.script_dir = script_dir
            # v3.7: an explicit "Build-tools folder" from Settings → Advanced
            # (filled by AUTO or by hand) wins over auto-discovery.
            self.tools_dir_override = (tools_dir_override or "").strip()

        def run(self):
            """Scan the toolchain off-thread and emit the result."""
            try:
                tools_dir = None
                if self.tools_dir_override:
                    ok, rev = build_tools_pin_status(self.tools_dir_override)
                    if ok:
                        tools_dir = self.tools_dir_override
                        self.logLine.emit(
                            f"[{log_time()}] Build-tools {rev} (Settings → Advanced): {tools_dir}")
                    else:
                        self.logLine.emit(
                            f"[{log_time()}] [warn] Build-tools folder from Settings is "
                            f"{rev or 'unversioned'} — {REQUIRED_BUILD_TOOLS} is "
                            "required. Falling back to the portable Data folder.")
                if not tools_dir:
                    tools_dir = ensure_build_tools_extracted(self.script_dir, self.logLine.emit)
                tools = locate_build_tools(tools_dir, self.logLine.emit) if tools_dir else {}
                # v3.8: android.jar is only accepted when its own framework
                # classes say API 33 — wrong versions are named and passed over
                jar = auto_find_android_jar(self.script_dir, self.logLine.emit)
                # v3.8: the pinned JDK 17 from the Data folder ONLY — the
                # system (PATH, JAVA_HOME, Program Files, IDE runtimes) is
                # never scanned for substitutes.
                jdk = auto_find_jdk_bin(self.script_dir, self.logLine.emit)
                jdk_level = probe_java_level(_bin_tool(jdk, "javac")) if jdk else None
                self.result.emit({"tools_dir": tools_dir, "tools": tools,
                                  "jar": jar, "jdk": jdk, "jdk_level": jdk_level})
            except Exception as e:
                # SAFETY NET: log, report, keep the app alive & usable.
                try:
                    self.logLine.emit(
                        f"[{log_time()}] [error] Environment scan failed: {e}\n"
                        + "\n".join(traceback.format_exc(limit=4).splitlines()[1:6]))
                except Exception:
                    pass
                self.failed.emit(str(e))


    # ---------------------------------------------------------------------------
    # Installer thread — item installs off the UI thread, progress via signals
    # ---------------------------------------------------------------------------
    class InstallerThread(QtCore.QThread):
        """v3.6 — runs the Data installer for a list of items, off the UI
        thread. Every signal is safe to connect straight to InstallDialog."""
        itemStarted = QtCore.pyqtSignal(str)
        itemProgress = QtCore.pyqtSignal(str, int, str)  # key, pct (-1 busy), detail
        itemFinished = QtCore.pyqtSignal(str, bool, str)  # key, ok, message
        logLine = QtCore.pyqtSignal(str)
        allDone = QtCore.pyqtSignal(bool, str)

        def __init__(self, keys: List[str]):
            """Order the requested install keys; reset the cancel flag."""
            super().__init__()
            self.keys = [k for k in INSTALL_ORDER if k in keys]
            self._cancelled = False

        def cancel(self):
            """Request a cooperative cancel of the running install."""
            self._cancelled = True

        def run(self):
            """Install each requested key, emitting progress signals."""
            ok_all, done_labels = True, []
            try:
                for key in self.keys:
                    if self._cancelled:
                        break
                    self.itemStarted.emit(key)
                    ok, msg = install_data_item(
                        key,
                        progress_cb=lambda pct, detail, k=key:
                            self.itemProgress.emit(k, pct, detail),
                        log_cb=self.logLine.emit,
                        cancel_check=lambda: self._cancelled)
                    self.itemFinished.emit(key, ok, msg)
                    ok_all = ok_all and ok
                    if ok:
                        done_labels.append(INSTALL_ITEMS[key]["label"])
            except Exception as e:
                self.logLine.emit(f"[{log_time()}] [error] Installer error: {e}")
                ok_all = False
            if self._cancelled:
                self.allDone.emit(False, "Cancelled — finished items stay installed.")
            elif ok_all:
                self.allDone.emit(True, "Installed: " + ", ".join(done_labels))
            else:
                self.allDone.emit(False, "Some items failed — see the console log.")


    # ---------------------------------------------------------------------------
    # Install dialog — the Data installer's UI: pick, watch, cancel
    # ---------------------------------------------------------------------------
    class InstallDialog(QtWidgets.QDialog):
        """v3.6 DATA INSTALLER — the beautiful face of install_data_item().

        Shows every installable item with size + description, runs the chosen
        ones with a live progress bar, per-item statuses, download speed and
        cancel — all in the same Razer-black-and-neon style as the studio.
        """

        def __init__(self, parent, win, preselect: List[str]):
            """Build the item rows, progress bar and action buttons."""
            super().__init__(parent)
            self.win = win
            self.missing = set(win.missing_installables())
            self.thread: Optional[InstallerThread] = None
            self.finished_keys: List[str] = []

            self.setWindowTitle(f"{APP_NAME} — Data Installer")
            self.setModal(True)
            self.setMinimumWidth(620)

            root = QtWidgets.QVBoxLayout(self)
            root.setContentsMargins(18, 18, 18, 18)
            root.setSpacing(12)

            header = QtWidgets.QLabel("DATA INSTALLER")
            header.setObjectName("cardSection")
            root.addWidget(header)
            big = QtWidgets.QLabel("Download & Install")
            big.setObjectName("installBig")
            root.addWidget(big)
            desc = QtWidgets.QLabel(
                "Everything installs into the portable Data folder beside APK Forge — "
                "your system is never touched. Every download tries several mirrors "
                "automatically, so one blocked or dead link is never a dead end. "
                "Delete the folder and it's as if nothing ever happened.")
            desc.setObjectName("muted")
            desc.setWordWrap(True)
            root.addWidget(desc)

            path_lbl = QtWidgets.QLabel(str(DATA_DIR))
            path_lbl.setObjectName("installPath")
            root.addWidget(path_lbl)

            # --- item rows ---
            self.rows: Dict[str, dict] = {}
            for key in INSTALL_ORDER:
                item = INSTALL_ITEMS[key]
                row = QtWidgets.QFrame()
                row.setObjectName("installRow")
                v = QtWidgets.QVBoxLayout(row)
                v.setContentsMargins(14, 10, 14, 10)
                v.setSpacing(2)

                top = QtWidgets.QHBoxLayout()
                cb = QtWidgets.QCheckBox(item["label"])
                cb.setObjectName("installCheck")
                cb.setChecked(key in preselect and key in self.missing)
                cb.setEnabled(key in self.missing)
                top.addWidget(cb, 1)
                size = QtWidgets.QLabel(item["size"])
                size.setObjectName("pill")
                size.setProperty("state", "muted")
                top.addWidget(size)
                v.addLayout(top)

                mid = QtWidgets.QHBoxLayout()
                d = QtWidgets.QLabel(item["desc"])
                d.setObjectName("installDesc")
                d.setWordWrap(True)
                mid.addWidget(d, 1)
                status = QtWidgets.QLabel("" if key in self.missing
                                          else "already installed")
                status.setObjectName("installStatus")
                mid.addWidget(status, 0, QtCore.Qt.AlignmentFlag.AlignBottom)
                v.addLayout(mid)

                root.addWidget(row)
                self.rows[key] = {"check": cb, "status": status, "frame": row}

            # --- progress ---
            self.bar = QtWidgets.QProgressBar()
            self.bar.setObjectName("installBar")
            self.bar.setRange(0, 100)
            self.bar.setValue(0)
            self.bar.hide()
            root.addWidget(self.bar)
            self.status_lbl = QtWidgets.QLabel("")
            self.status_lbl.setObjectName("installStatus")
            self.status_lbl.setWordWrap(True)
            root.addWidget(self.status_lbl)

            root.addStretch(1)

            # --- buttons ---
            btns = QtWidgets.QHBoxLayout()
            self.open_data_btn = QtWidgets.QPushButton("Open Data Folder")
            self.open_data_btn.setObjectName("ghost")
            self.open_data_btn.clicked.connect(self._open_data_folder)
            btns.addWidget(self.open_data_btn)
            btns.addStretch(1)
            self.cancel_btn = QtWidgets.QPushButton("Cancel")
            self.cancel_btn.clicked.connect(self._on_cancel)
            btns.addWidget(self.cancel_btn)
            self.install_btn = GlowButton("DOWNLOAD & INSTALL", idle_pulse=True)
            self.install_btn.setObjectName("primary")
            self.install_btn.setMinimumHeight(44)
            self.install_btn.clicked.connect(self._start)
            btns.addWidget(self.install_btn)
            root.addLayout(btns)

        # --- handlers ---
        def _open_data_folder(self):
            """Open the portable Data folder in the file manager."""
            try:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                QtGui.QDesktopServices.openUrl(
                    QtCore.QUrl.fromLocalFile(str(DATA_DIR)))
            except Exception as e:
                self.win.log(f"[{log_time()}] [warn] open Data folder: {e}")

        def _selected(self) -> List[str]:
            """Return the checked and enabled install keys."""
            return [k for k in INSTALL_ORDER
                    if self.rows[k]["check"].isEnabled()
                    and self.rows[k]["check"].isChecked()]

        def _start(self):
            """Run InstallerThread for the selected items."""
            keys = self._selected()
            if not keys:
                self.status_lbl.setText("Select at least one item to install.")
                self.status_lbl.setStyleSheet("color:#ffb454; background:transparent;")
                return
            self.thread = InstallerThread(keys)
            self.thread.itemStarted.connect(self._on_item_started)
            self.thread.itemProgress.connect(self._on_item_progress)
            self.thread.itemFinished.connect(self._on_item_finished)
            self.thread.logLine.connect(self.win.log)
            self.thread.allDone.connect(self._on_all_done)

            for k in INSTALL_ORDER:
                self.rows[k]["check"].setEnabled(False)
            self.install_btn.setEnabled(False)
            self.open_data_btn.setEnabled(False)
            self.cancel_btn.setText("Stop")
            self.bar.setRange(0, 100)
            self.bar.setValue(0)
            self.bar.show()
            self.status_lbl.setStyleSheet("color:#9a9c98; background:transparent;")
            self.status_lbl.setText("Preparing…")
            self.win.log(f"[{log_time()}] Data installer started — "
                         f"{', '.join(INSTALL_ITEMS[k]['label'] for k in keys)}")
            self.thread.start()

        def _on_item_started(self, key: str):
            """Mark an item row as starting."""
            st = self.rows[key]["status"]
            st.setText("starting…")
            st.setStyleSheet("color:#44d62c; background:transparent;")

        def _on_item_progress(self, key: str, pct: int, detail: str):
            """Update bar and status text while an item installs."""
            label = INSTALL_ITEMS[key]["label"]
            self.rows[key]["status"].setText(detail)
            if pct < 0:
                self.bar.setRange(0, 0)  # busy bar
            else:
                if self.bar.maximum() == 0:
                    self.bar.setRange(0, 100)
                self.bar.setValue(pct)
            self.status_lbl.setText(f"{label} — {detail}")

        def _on_item_finished(self, key: str, ok: bool, msg: str):
            """Record the item result, auto-fill paths, hot-load Pillow."""
            st = self.rows[key]["status"]
            if ok:
                st.setText("installed")
                st.setStyleSheet("color:#44d62c; background:transparent;")
                self.finished_keys.append(key)
            else:
                st.setText(f"{msg}")
                st.setStyleSheet("color:#ff7a7a; background:transparent;")
            if self.bar.maximum() == 0:
                self.bar.setRange(0, 100)

            # Pillow can go live immediately — pick it up in-process.
            if ok and key == "pillow" and not HAS_PIL:
                try:
                    from PIL import Image as _PilImage  # noqa: F401
                    globals()["Image"] = _PilImage
                    globals()["HAS_PIL"] = True
                    self.win.log(f"[{log_time()}] [ok] Pillow active — icon resizing enabled.")
                except Exception:
                    pass

            # v3.7 AUTO-PATH: a finished install instantly fills the matching
            # path field with the item's final location inside ./Data — the
            # settings literally write themselves (msg IS the final path for
            # the zip items: jdk → …/bin, buildtools → folder, androidjar → jar).
            if ok and key in ("jdk", "buildtools", "androidjar") and msg:
                try:
                    sp = self.win.page("settings")
                    field = {"jdk": sp.jdk_bin_edit,
                             "buildtools": sp.buildtools_edit,
                             "androidjar": sp.android_jar_edit}[key]
                    field.setText(msg)
                    self.win._save_settings_soon()
                    # v3.8.1: run the AUTO routine for this item too — it
                    # re-resolves the path from ./Data, saves settings and
                    # records the install in Data/autopaths.json
                    self.win.on_data_item_installed(key, msg)
                    self.win.log(
                        f"[{log_time()}] {INSTALL_ITEMS[key]['label']} path set "
                        f"automatically → {msg}")
                except Exception as e:
                    self.win.log(f"[{log_time()}] [warn] auto path update: {e}")

        def _on_all_done(self, ok: bool, msg: str):
            """Re-enable buttons, toast the result and rescan."""
            self.bar.setRange(0, 100)
            self.bar.setValue(100 if ok else 0)
            self.install_btn.setEnabled(True)
            self.open_data_btn.setEnabled(True)
            self.cancel_btn.setText("Close")
            for k in INSTALL_ORDER:
                if k not in self.finished_keys:
                    self.rows[k]["check"].setEnabled(k in self.missing)
            color = "#44d62c" if ok else "#ffb454"
            self.status_lbl.setStyleSheet(f"color:{color}; background:transparent;")
            self.status_lbl.setText(msg)
            self.win.log(f"[{log_time()}] Data installer finished — {msg}")
            if self.finished_keys:
                self.win.toast(msg, "ok" if ok else "warn")
                if "qtmultimedia" in self.finished_keys:
                    self.win.toast("Restart APK Forge to activate QtMultimedia.", "info")
                # rescan so installed tools light up everywhere instantly
                QtCore.QTimer.singleShot(300, self.win.refresh_environment)
                self.win._refresh_dashboard_safe()
            self.thread = None

        def _on_cancel(self):
            """Cancel a running install or close the dialog."""
            if self.thread is not None and self.thread.isRunning():
                self.thread.cancel()
                self.status_lbl.setText("Stopping… (safe — finished items stay installed)")
                return
            self.reject()

        def closeEvent(self, event):
            """Confirm, cancel and reap the thread before closing."""
            if self.thread is not None and self.thread.isRunning():
                confirm = QtWidgets.QMessageBox.question(
                    self, "Install in progress",
                    "A download is still running.\n\nStop it and close?",
                    QtWidgets.QMessageBox.StandardButton.Yes |
                    QtWidgets.QMessageBox.StandardButton.No)
                if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
                self.thread.cancel()
            # give the thread a moment to unwind its cancel
            if self.thread is not None:
                self.thread.wait(4000)
            event.accept()


    # ---------------------------------------------------------------------------
    # Background scan — pooled Java analysis with main-thread signals
    # ---------------------------------------------------------------------------
    class _ScanSignals(QtCore.QObject):
        """Signal bundle for ScanJob, created on the main thread."""

        done = QtCore.pyqtSignal(int, dict)


    class ScanJob(QtCore.QRunnable):
        """
        Heavy Java analysis (structure scan, diagnostics, permissions, elements)
        executed on the global thread pool — the editor never blocks.

        v3.1 ownership fix: autoDelete is OFF and MainWindow holds a reference
        per generation. The signals QObject is created on the MAIN thread and
        deleted via deleteLater() from the main thread — it is never destroyed
        on a worker thread anymore.
        """
        def __init__(self, generation: int, text: str, min_sdk: int, enabled_perms: List[str]):
            """Keep the scan payload; the window owns the lifetime."""
            super().__init__()
            self.setAutoDelete(False)  # lifetime managed by MainWindow
            self.signals = _ScanSignals()
            self.gen = generation
            self.text = text
            self.min_sdk = min_sdk
            self.perms = enabled_perms

        def run(self):
            """Analyze the Java text, autosave it, and emit the result."""
            try:
                analysis = analyze_java(self.text, self.min_sdk, self.perms)
                elements = parse_elements_from_java(self.text)
                # autosave the draft off the UI thread
                try:
                    AUTOSAVE_JAVA.parent.mkdir(parents=True, exist_ok=True)
                    AUTOSAVE_JAVA.write_text(self.text, encoding="utf-8")
                except Exception:
                    pass
                self.signals.done.emit(self.gen, {"elements": elements, "analysis": analysis})
            except Exception as e:
                try:
                    self.signals.done.emit(
                        self.gen, {"elements": [], "analysis": None, "error": str(e)})
                except Exception:
                    pass  # window already closed — nothing to report


    # ---------------------------------------------------------------------------
    # Background build thread
    # ---------------------------------------------------------------------------
    class BuilderThread(QtCore.QThread):
        """Runs the APK build in a background thread (on a CONFIG SNAPSHOT)."""
        logLine = QtCore.pyqtSignal(str)
        stage = QtCore.pyqtSignal(int, str)
        done = QtCore.pyqtSignal(bool, str)

        def __init__(self, cfg: BuildConfig):
            """Store the config snapshot that this thread builds."""
            super().__init__()
            self.cfg = cfg

        def run(self):
            """Run the build to completion and emit done, crash-safe."""
            try:
                ok, out = build_apk(self.cfg, log_cb=self.logLine.emit, stage_cb=self._stage)
            except Exception as e:
                # SAFETY NET: a crashing build must never abort the process.
                try:
                    self.logLine.emit(f"[{log_time()}] [error] Build crashed: {e}")
                    self.logLine.emit("\n".join(traceback.format_exc(limit=6).splitlines()[:8]))
                except Exception:
                    pass
                ok, out = False, f"internal error: {e}"
            self.done.emit(ok, out)

        def _stage(self, pct, name):
            """Forward a stage callback to the stage signal."""
            self.stage.emit(pct, name)


    # ---------------------------------------------------------------------------
    # Splash overlay — the window appears INSTANTLY with animated feedback
    # ---------------------------------------------------------------------------
    class SplashOverlay(QtWidgets.QWidget):
        """v3.2 CENTERING FIX.

        The overlay is parented to the window's CENTRAL widget (it covers the
        sidebar too, like a real splash) and keeps itself EXACTLY covering its
        parent via an event filter — so its content is always perfectly
        centered no matter how the window is resized / maximized / fullscreened.

        (v3.1 bug: the splash lived on the inner `content` widget but sized
        itself from `centralWidget().rect()` — a rect in the WRONG coordinate
        space, which shifted everything right by the sidebar width.)
        """

        def __init__(self, parent: QtWidgets.QWidget):
            """Build the centered splash UI and track the parent geometry."""
            super().__init__(parent)
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            lay = QtWidgets.QVBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addStretch(1)                  # EQUAL stretches → true centering

            logo = QtWidgets.QLabel(
                "<span style='color:#44d62c; font-weight:800; font-size:34px'>APK</span>"
                "<span style='color:#e8e8e6; font-weight:800; font-size:34px'> FORGE</span>")
            logo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(logo)
            tag = QtWidgets.QLabel(APP_TAGLINE.upper() + f"  ·  v{APP_VERSION} '{APP_BUILD_NAME}'")
            tag.setStyleSheet("color:#6f736e; font-size:11px; letter-spacing:2px; background:transparent;")
            tag.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(tag)
            lay.addSpacing(18)

            self.spinner = Spinner(self, 34)
            lay.addWidget(self.spinner, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
            self.status = QtWidgets.QLabel("Scanning build environment…")
            self.status.setStyleSheet("color:#9a9c98; background:transparent;")
            self.status.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(self.status)
            lay.addStretch(1)                  # EQUAL stretches → true centering
            self.spinner.start()

            # self-managed geometry: follow the parent everywhere, forever
            try:
                parent.installEventFilter(self)
            except Exception:
                pass
            self.setGeometry(parent.rect())
            self.raise_()

        def eventFilter(self, obj, ev):
            """Keep the overlay exactly covering its parent widget."""
            if obj is self.parentWidget() and ev.type() in (
                    QtCore.QEvent.Type.Resize, QtCore.QEvent.Type.Show,
                    QtCore.QEvent.Type.Polish, QtCore.QEvent.Type.LayoutRequest):
                try:
                    self.setGeometry(obj.rect())
                    self.raise_()
                except RuntimeError:
                    pass
            return super().eventFilter(obj, ev)

        def paintEvent(self, _e):
            """Paint the translucent splash backdrop."""
            p = QtGui.QPainter(self)
            p.fillRect(self.rect(), QtGui.QColor(12, 13, 12, 235))
            p.end()

        def fade_out(self, on_gone=None):
            """Fade the splash away. `on_gone` is invoked AFTER the widget is
            deleted so the owner can drop its reference safely (v3.1 fix for
            the RuntimeError-on-resize crash)."""
            try:
                self.spinner.stop()
                try:
                    self.parentWidget().removeEventFilter(self)
                except Exception:
                    pass
                fx = QtWidgets.QGraphicsOpacityEffect(self)
                self.setGraphicsEffect(fx)
                anim = QtCore.QPropertyAnimation(fx, b"opacity", self)
                anim.setDuration(380)
                anim.setStartValue(1.0)
                anim.setEndValue(0.0)
                anim.setEasingCurve(QtCore.QEasingCurve.Type.InCubic)
                anim.finished.connect(self.hide)
                anim.finished.connect(self.deleteLater)
                if on_gone is not None:
                    anim.finished.connect(on_gone)
                anim.start()
            except RuntimeError:
                # already gone — just notify the owner
                if on_gone is not None:
                    on_gone()


    # ---------------------------------------------------------------------------
    # MAIN WINDOW — sidebar navigation + animated pages + build console
    # ---------------------------------------------------------------------------
    NAV_ITEMS = [
        ("dashboard", "Dashboard"),
        ("source", "Source"),
        ("design", "Design"),
        ("motion", "Motion"),
        ("aiguide", "AI Guide"),
        ("settings", "Settings"),
    ]

    # v3.2: single source of truth for the automation toggles — shared by the
    # Dashboard card AND the command palette (Ctrl+K).
    AUTO_AUTOMATIONS = [
        ("auto_pkg", "Auto package name — derived from your app name"),
        ("auto_scan", "Live element scan — analyze code while you type"),
        ("auto_bump", "Auto version bump — versionCode +1 after each build"),
        ("auto_open", "Auto-open output folder — reveal the APK when done"),
        ("auto_imports", "Auto-fix imports — missing imports added at build"),
        ("auto_perms", "Auto-permissions — enable permissions your code uses"),
        ("auto_min_sdk", "Auto min SDK — raise minSdk when code needs newer APIs"),
    ]

    AUTOSAVE_JAVA = Path.home() / ".apkforge" / "autosave.java"


    class MainWindow(QtWidgets.QMainWindow):
        """Main window: sidebar navigation, pages, console and build flow."""
        def __init__(self):
            """Initialize state, build the UI and start the background work."""
            super().__init__()
            self.setWindowTitle(f"{APP_NAME} — {APP_TAGLINE}  ·  v{APP_VERSION}")
            self.resize(1320, 860)
            self.setMinimumSize(960, 600)     # v3.1: fits smaller laptops too

            self.cfg = BuildConfig()
            self.auto = {"auto_pkg": True, "auto_scan": True, "auto_bump": True,
                         "auto_open": True, "auto_imports": True, "auto_perms": True,
                         "auto_min_sdk": True}
            self.script_dir = str(Path(__file__).parent.resolve())
            self.tools_dir: Optional[str] = None
            self.tools: Dict = {}
            self._thread: Optional[BuilderThread] = None
            self._env_thread: Optional[EnvScannerThread] = None
            self._restored_elements: Dict[str, ElementInfo] = {}
            self._scan_gen = 0
            self._scan_jobs: Dict[int, ScanJob] = {}       # v3.1: job lifetime
            self._build_cfg: Optional[BuildConfig] = None   # v3.1: build snapshot
            self.last_scan: Optional[dict] = None
            self.build_history: List[dict] = []
            self._closing = False        # v3.1: window is on its way out
            self._really_close = False   # v3.1: final close pass is allowed

            self._build_ui()
            self._load_settings()

            # welcome banner
            self.log(f"[{log_time()}] {APP_NAME} v{APP_VERSION} '{APP_BUILD_NAME}' — {APP_TAGLINE}")
            self.log(f"[{log_time()}] Automations active: package naming, live scan, auto-save, "
                     f"auto-imports, auto-permissions, auto min-SDK, version bump")
            self.log(f"[{log_time()}] Data installer ready — missing libraries & tools "
                     f"download into ./Data (one click, never system-wide)")

            # v3.8.1: first launch → AUTO for all paths (JSON-detected);
            # later launches → fill empty/stale toolchain rows from ./Data.
            # Runs BEFORE the scan so the scan already sees the filled paths.
            self._auto_paths_startup()

            # environment scan in the BACKGROUND (splash covers it)
            self.refresh_environment()

            # restore last java draft (fast — pure text set)
            if not self.java_edit.toPlainText().strip() and AUTOSAVE_JAVA.exists():
                try:
                    text = AUTOSAVE_JAVA.read_text(encoding="utf-8", errors="replace")
                    if text.startswith("\ufeff"):   # v3.2: strip a UTF-8 BOM
                        text = text.lstrip("\ufeff")
                    self.java_edit.setPlainText(text)
                    self.log(f"[{log_time()}] Session restored from {AUTOSAVE_JAVA}")
                except Exception:
                    pass

            self._start_build_pulse()
            self.trigger_scan()
            self.refresh_dashboard_soon()

        # --- UI construction ---
        def _build_ui(self):
            """Assemble the central layout, pages, console and timers."""
            central = QtWidgets.QWidget()
            self.setCentralWidget(central)
            root = QtWidgets.QHBoxLayout(central)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            root.addWidget(self._build_sidebar())

            content = QtWidgets.QWidget()
            cv = QtWidgets.QVBoxLayout(content)
            cv.setContentsMargins(0, 0, 0, 0)
            cv.setSpacing(0)
            cv.addWidget(self._build_topbar())

            self.stack = AnimatedStack()
            cv.addWidget(self.stack, 1)
            cv.addWidget(self._build_console_dock())
            root.addWidget(content, 1)

            self._build_statusbar()
            self._build_shortcuts()

            # lazy page registry — pages are constructed on first visit
            self._pages: Dict[str, Page] = {}
            self._stack_index: Dict[str, int] = {}
            self.PAGE_FACTORIES = {
                "dashboard": DashboardPage,
                "source": SourcePage,
                "design": DesignPage,
                "motion": MotionPage,
                "aiguide": AiGuidePage,
                "settings": SettingsPage,
            }
            # dashboard + source + settings are needed immediately
            self.page("dashboard")
            self.page("source")
            self.page("settings")

            # syntax highlighter attaches to the editor's document
            self.highlighter = JavaHighlighter(self.java_edit.document())

            # splash overlay over the WHOLE central widget, perfectly centered
            # (v3.2: parented to `central` and self-syncing via event filter —
            # see SplashOverlay; see also _splash_visible / _dismiss_splash)
            self.splash = SplashOverlay(central)
            self.splash.setGeometry(central.rect())
            self.splash.raise_()

            # default page
            self.goto_page("dashboard")

            # debounced live scan (AUTOMATION)
            self._scan_timer = QtCore.QTimer(self)
            self._scan_timer.setSingleShot(True)
            self._scan_timer.setInterval(350)
            self._scan_timer.timeout.connect(lambda: self._run_scan_job())
            self.java_edit.textChanged.connect(
                lambda: self._scan_timer.start() if self.auto.get("auto_scan") else None)

            # debounced settings persistence
            self._save_timer = QtCore.QTimer(self)
            self._save_timer.setSingleShot(True)
            self._save_timer.setInterval(700)
            self._save_timer.timeout.connect(self._save_settings_now)

            # debounced dashboard refresh
            self._dash_timer = QtCore.QTimer(self)
            self._dash_timer.setSingleShot(True)
            self._dash_timer.setInterval(450)
            self._dash_timer.timeout.connect(self._refresh_dashboard_safe)

        def page(self, key: str) -> Page:
            """Lazily construct (or return the cached) page for a nav key."""
            if key not in self._pages:
                factory = self.PAGE_FACTORIES.get(key)
                if factory is None:
                    raise KeyError(f"unknown page: {key}")
                w = factory(self)
                sc = scroll_page(w)
                idx = self.stack.addWidget(sc)
                self._stack_index[key] = idx
                self._pages[key] = w
                # initialize lazily-built pages with the CURRENT state
                try:
                    if key == "motion":
                        w.refresh()
                    elif key == "design":
                        w.load_persisted()
                except Exception as e:
                    self.log(f"[{log_time()}] [warn] page init '{key}': {e}")
            return self._pages[key]

        def _build_sidebar(self) -> QtWidgets.QWidget:
            """Create the navigation rail and the build controls."""
            side = QtWidgets.QFrame()
            side.setObjectName("sidebar")
            side.setFixedWidth(236)
            v = QtWidgets.QVBoxLayout(side)
            v.setContentsMargins(14, 18, 14, 16)
            v.setSpacing(6)

            logo = QtWidgets.QLabel(
                "<span style='color:#44d62c; font-weight:800'>APK</span>"
                "<span style='color:#e8e8e6; font-weight:800'> FORGE</span>")
            logo.setObjectName("logo")
            logo.setStyleSheet("font-size:20px; background:transparent;")
            v.addWidget(logo)
            tag = QtWidgets.QLabel(APP_TAGLINE.upper())
            tag.setObjectName("tiny")
            v.addWidget(tag)
            v.addSpacing(14)

            self.nav_buttons = {}
            for key, title in NAV_ITEMS:
                btn = QtWidgets.QPushButton(title)
                btn.setObjectName("nav")
                btn.setCheckable(True)
                btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda _=False, k=key: self.goto_page(k))
                self.nav_buttons[key] = btn
                v.addWidget(btn)

            v.addStretch(1)

            # v3.2: animated neon accent bar that GLIDES to the active page
            self.nav_indicator = QtWidgets.QWidget(side)
            self.nav_indicator.setFixedSize(3, 26)
            self.nav_indicator.setStyleSheet(
                "background:#44d62c; border-radius:1px;")
            self.nav_indicator.hide()
            self._nav_anim = None

            self.build_btn = GlowButton("BUILD APK", idle_pulse=True)
            self.build_btn.setObjectName("buildBtn")
            self.build_btn.setMinimumHeight(48)
            self.build_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            self.build_btn.clicked.connect(self.on_build)
            v.addWidget(self.build_btn)

            self.build_progress = ShimmerBar()
            self.build_progress.setRange(0, 100)
            self.build_progress.setValue(0)
            self.build_progress.setFixedHeight(7)
            v.addWidget(self.build_progress)

            self.build_status = QtWidgets.QLabel("Idle — waiting for orders")
            self.build_status.setObjectName("tiny")
            v.addWidget(self.build_status)
            return side

        def _build_topbar(self) -> QtWidgets.QWidget:
            """Create the breadcrumb bar with palette and console buttons."""
            bar = QtWidgets.QFrame()
            bar.setObjectName("topbar")
            bar.setFixedHeight(46)
            h = QtWidgets.QHBoxLayout(bar)
            h.setContentsMargins(20, 0, 20, 0)
            self.crumb = QtWidgets.QLabel("APK FORGE / DASHBOARD")
            self.crumb.setObjectName("crumb")
            h.addWidget(self.crumb)
            h.addStretch(1)

            palette_btn = QtWidgets.QPushButton("Commands")
            palette_btn.setObjectName("mini")
            palette_btn.setToolTip("Open the command palette (Ctrl+K)")
            palette_btn.clicked.connect(self.open_palette)
            h.addWidget(palette_btn)

            self.console_btn = QtWidgets.QPushButton("▤  Console")
            self.console_btn.setObjectName("mini")
            self.console_btn.setCheckable(True)
            self.console_btn.toggled.connect(lambda on: self.show_console(on))
            h.addWidget(self.console_btn)
            return bar

        def _build_console_dock(self) -> QtWidgets.QWidget:
            """Create the collapsible build console dock."""
            dock = QtWidgets.QFrame()
            dock.setObjectName("dock")
            v = QtWidgets.QVBoxLayout(dock)
            v.setContentsMargins(14, 10, 14, 12)
            v.setSpacing(8)

            head = QtWidgets.QHBoxLayout()
            title = QtWidgets.QLabel("BUILD CONSOLE")
            title.setObjectName("dockTitle")
            head.addWidget(title)
            head.addStretch(1)
            copy_btn = QtWidgets.QPushButton("Copy")
            copy_btn.setObjectName("mini")
            copy_btn.clicked.connect(self._copy_log)
            clear_btn = QtWidgets.QPushButton("Clear")
            clear_btn.setObjectName("mini")
            clear_btn.clicked.connect(lambda: self.log_view.clear())
            hide_btn = QtWidgets.QPushButton("Hide ▾")
            hide_btn.setObjectName("mini")
            hide_btn.clicked.connect(lambda: self.show_console(False))
            for b in (copy_btn, clear_btn, hide_btn):
                head.addWidget(b)
            v.addLayout(head)

            self.log_view = QtWidgets.QPlainTextEdit()
            self.log_view.setObjectName("console")
            self.log_view.setReadOnly(True)
            self.log_view.setMaximumBlockCount(3000)
            self.log_view.setFixedHeight(200)
            v.addWidget(self.log_view)

            dock.setVisible(False)
            self.console_dock = dock
            return dock

        def _build_statusbar(self):
            """Add the toolchain status widgets to the status bar."""
            sb = self.statusBar()
            self.sb_jdk = QtWidgets.QLabel()
            self.sb_jar = QtWidgets.QLabel()
            self.sb_tools = QtWidgets.QLabel()
            for w in (self.sb_jdk, self.sb_jar, self.sb_tools):
                sb.addWidget(w)
            sb.addPermanentWidget(QtWidgets.QLabel(f"v{APP_VERSION} · {APP_BUILD_NAME}"))

        def _build_shortcuts(self):
            """Register the global shortcuts and Ctrl+N page jumps."""
            from PyQt6.QtGui import QShortcut, QKeySequence
            QShortcut(QKeySequence("Ctrl+K"), self, self.open_palette)
            QShortcut(QKeySequence("Ctrl+B"), self, self.on_build)
            QShortcut(QKeySequence("Ctrl+S"), self, self.on_save_java)
            QShortcut(QKeySequence("Ctrl+O"), self, self.on_load_java)
            QShortcut(QKeySequence("F5"), self, lambda: self.trigger_scan(force=True))
            QShortcut(QKeySequence("Ctrl+`"), self, lambda: self.show_console(not self.console_dock.isVisible()))
            for i, (key, _title) in enumerate(NAV_ITEMS, start=1):
                QShortcut(QKeySequence(f"Ctrl+{i}"), self, lambda k=key: self.goto_page(k))

        def _start_build_pulse(self):
            """Start the BUILD button idle breathing pulse."""
            # v3.2: the BUILD button now BREATHES continuously while idle
            # (paused on hover & while building) instead of one welcome pulse.
            if hasattr(self, "build_btn"):
                QtCore.QTimer.singleShot(900, self.build_btn.start_idle_pulse)

        # --- Navigation & console ---
        def goto_page(self, key: str):
            """Switch to a page, animating the stack and the nav indicator."""
            if key not in self.PAGE_FACTORIES:
                return
            prev_key = getattr(self, "_current_page_key", None)
            self.page(key)  # lazy-build on first visit
            for k, btn in self.nav_buttons.items():
                btn.setChecked(k == key)
            old = self.stack.currentIndex()
            new = self._stack_index.get(key, old)
            direction = 1 if new >= old else -1
            self.stack.setCurrentIndexAnimated(new, direction)
            self._current_page_key = key
            self._update_nav_indicator(animate=(prev_key is not None))
            title = dict(NAV_ITEMS).get(key, key)
            self.crumb.setText(f"APK FORGE / {title.upper()}")
            if key == "dashboard":
                self._refresh_dashboard_safe()
            # v3.2: control-level entrance motion — the page itself switches
            # INSTANTLY (v3.1 perf choice) while its cards fade & rise in.
            if key != prev_key:
                animate_page_entrance(self._pages.get(key))

        def _update_nav_indicator(self, animate: bool = True):
            """v3.2: glide the neon accent bar to the active nav button."""
            indicator = getattr(self, "nav_indicator", None)
            if indicator is None:
                return
            btn = self.nav_buttons.get(getattr(self, "_current_page_key", None))
            if btn is None:
                return
            try:
                bar_h = min(26, max(10, btn.height() - 12))
                target = QtCore.QRect(6, btn.y() + max(0, (btn.height() - bar_h) // 2),
                                      3, bar_h)
                if not indicator.isVisible():
                    indicator.setGeometry(target)
                    indicator.show()
                    indicator.raise_()
                    return
                if animate:
                    if self._nav_anim is not None:
                        try:
                            self._nav_anim.stop()
                        except RuntimeError:
                            pass
                    anim = QtCore.QPropertyAnimation(indicator, b"geometry", self)
                    anim.setDuration(220)
                    anim.setStartValue(QtCore.QRect(indicator.geometry()))
                    anim.setEndValue(target)
                    anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
                    anim.start()
                    self._nav_anim = anim
                else:
                    indicator.setGeometry(target)
                indicator.raise_()
            except RuntimeError:
                pass

        def show_console(self, on: bool):
            """Show or hide the console dock and sync its toggle button."""
            self.console_dock.setVisible(on)
            self.console_btn.setChecked(on)

        # --- Logging & toasts ---
        def log(self, text: str):
            """Append a color-coded line to the build console."""
            safe = html_escape(text).replace("\n", "<br>")
            if "ERROR" in text or "[error]" in text:
                color = "#ff7a7a"
            elif "[warn]" in text:
                color = "#ffb454"
            elif "[ok]" in text or "Success" in text or "[auto]" in text or "Build started" in text:
                color = "#44d62c"
            elif text.startswith("[") and "RUN:" in text:
                color = "#7c807a"
            else:
                color = "#c9ccc6"
            self.log_view.appendHtml(f"<span style='color:{color}'>{safe}</span>")
            sb = self.log_view.verticalScrollBar()
            sb.setValue(sb.maximum())

        def toast(self, text: str, kind: str = "info"):
            """Pop up a transient toast notification."""
            Toast.popup(self, text, kind)

        def _copy_log(self):
            """Copy the console log to the clipboard."""
            QtGui.QGuiApplication.clipboard().setText(self.log_view.toPlainText())
            self.toast("Console copied to clipboard.", "ok")

        # --- Live scan (async) — no UI freeze even on huge files ---
        def trigger_scan(self, force: bool = False):
            """Request a scan now (force) or after the short debounce."""
            if force:
                self._run_scan_job()
            else:
                self._scan_timer.start()

        def _run_scan_job(self):
            """Submit the current editor text to the pool as a ScanJob."""
            text = self.java_edit.toPlainText()
            sp = self.page("settings")
            min_sdk = sp.min_sdk_combo.currentData() or 21
            perms = sp.checked_permissions()
            self._scan_gen += 1
            sp_widget = self._pages.get("source")
            if sp_widget is not None and hasattr(sp_widget, "scan_spinner"):
                sp_widget.scan_spinner.start()
            job = ScanJob(self._scan_gen, text, min_sdk, perms)
            job.signals.done.connect(self._on_scan_done)
            self._scan_jobs[self._scan_gen] = job      # v3.1: we own the job
            QtCore.QThreadPool.globalInstance().start(job)

        def _on_scan_done(self, generation: int, payload: dict):
            """Apply the newest scan payload; drop stale generations."""
            # v3.1: ALWAYS reclaim the job (even stale ones), deleting its
            # signals QObject on the MAIN thread — never on a worker thread.
            job = self._scan_jobs.pop(generation, None)
            if job is not None:
                try:
                    job.signals.deleteLater()
                except RuntimeError:
                    pass
            if generation != self._scan_gen:
                return  # stale result — a newer scan is in flight
            sp_widget = self._pages.get("source")
            if sp_widget is not None and hasattr(sp_widget, "scan_spinner"):
                sp_widget.scan_spinner.stop()
            if payload.get("error"):
                self.log(f"[{log_time()}] [warn] Scan error: {payload['error']}")
                return

            self.last_scan = payload

            # merge previous element configurations by name
            found: List[ElementInfo] = payload.get("elements", [])
            prev = {e.name: e for e in self.cfg.elements}
            merged = []
            for f in found:
                src = self._restored_elements.pop(f.name, None) or prev.get(f.name)
                if src is not None:
                    f.animations = list(src.animations)
                    f.animation_duration = src.animation_duration
                    f.sound_path = src.sound_path
                    f.image_path = src.image_path
                    f.auto_size = src.auto_size
                merged.append(f)
            # v3.5: CONFIGURED elements that vanished from the code (renamed /
            # deleted) are RETAINED — the Motion page keeps showing them and
            # the Diagnostics panel explains exactly what will be skipped,
            # instead of the configuration silently disappearing. Bare
            # detections (no animation/sound/image) still vanish as before.
            seen = {e.name for e in merged}
            for src in list(self._restored_elements.values()) + list(prev.values()):
                if src.name in seen:
                    continue
                if src.animations or src.sound_path or src.image_path:
                    merged.append(src)
                    seen.add(src.name)
            self.cfg.elements = merged

            self._after_elements_changed()

            analysis: JavaAnalysis = payload.get("analysis")
            if analysis is not None:
                java_now = self.java_edit.toPlainText() if hasattr(self, "java_edit") else ""
                # v3.4: asset ⇄ code cross-check joins the diagnostics panel
                try:
                    analysis.issues = analysis.issues + asset_diagnostics(java_now, self.cfg.assets)
                except Exception:
                    pass
                # v3.5: motion / sound / image safety joins the diagnostics panel
                try:
                    analysis.issues = analysis.issues + motion_injection_warnings(java_now, self.cfg.elements)
                except Exception:
                    pass
                if "source" in self._pages:
                    self._pages["source"].refresh_diagnostics(analysis.issues)
                    self._pages["source"].refresh_status(payload)
                if "settings" in self._pages:
                    self._pages["settings"].set_minsdk_hint(analysis.required_min_sdk)

        def _after_elements_changed(self):
            """Refresh the pages that depend on the element configuration."""
            if "motion" in self._pages:
                self._pages["motion"].refresh()
            if "source" in self._pages:
                if self.last_scan:
                    self._pages["source"].refresh_status(self.last_scan)
            self.refresh_dashboard_soon()

        def refresh_dashboard_soon(self):
            """Debounce a dashboard refresh."""
            self._dash_timer.start()

        def _refresh_dashboard_safe(self):
            """Refresh the dashboard, logging errors instead of raising."""
            try:
                if "dashboard" in self._pages:
                    self._pages["dashboard"].refresh()
            except Exception as e:
                self.log(f"[{log_time()}] [warn] dashboard refresh: {e}")

        # --- Diagnostics one-click fixes ---
        def fix_imports(self):
            """Insert any missing imports into the Java editor."""
            text = self.java_edit.toPlainText()
            new_text, added = auto_fix_imports(text)
            if added:
                self.java_edit.setPlainText(new_text)
                self.toast(f"{len(added)} import(s) added.", "ok")
                self.log(f"[{log_time()}] Auto-imports: {', '.join(a.split('.')[-1] for a in added[:10])}")
                self.trigger_scan()
            else:
                self.toast("No missing imports detected.", "info")

        def fix_perms(self, csv_perms: str):
            """Enable the listed permissions on the Settings page."""
            perms = [p for p in csv_perms.split(",") if p]
            if not perms:
                return
            sp = self.page("settings")
            sp.ensure_permission_items(perms)
            sp.set_permissions(perms)
            self.toast(f"{len(perms)} permission(s) enabled.", "ok")
            self.log(f"[{log_time()}] Permissions enabled: "
                     + ", ".join(p.split(".")[-1] for p in perms))

        def fix_min_sdk(self, api_str: str):
            """Raise the minimum SDK combo to the given API level."""
            try:
                api = int(api_str)
            except (TypeError, ValueError):
                return
            sp = self.page("settings")
            sp._select_combo(sp.min_sdk_combo, api)
            self.toast(f"Minimum SDK raised to {sdk_label(api)}.", "ok")
            self.log(f"[{log_time()}] [auto] minSdk raised to {api}")

        def fix_androidx(self):
            """Migrate androidx imports to framework equivalents."""
            text = self.java_edit.toPlainText()
            new_text, migrated, unmappable = migrate_androidx(text)
            if migrated:
                self.java_edit.setPlainText(new_text)
                self.toast(f"Migrated {len(migrated)} androidx import(s).", "ok")
                self.log(f"[{log_time()}] androidx migrated: {', '.join(migrated)}")
                if unmappable:
                    self.toast(f"{len(unmappable)} androidx import(s) have no framework "
                               f"equivalent — rewrite them manually.", "warn")
                self.trigger_scan()
            else:
                self.toast("Nothing migratable found.", "info")

        def apply_fix(self, fix_id: str, arg: str = ""):
            """Dispatch a one-click diagnostics fix by its id."""
            if fix_id == "add_imports":
                self.fix_imports()
            elif fix_id == "enable_perms":
                self.fix_perms(arg)
            elif fix_id == "raise_min_sdk":
                self.fix_min_sdk(arg)
            elif fix_id == "migrate_androidx":
                self.fix_androidx()
            elif fix_id == "goto_settings":
                self.goto_page("settings")
            elif fix_id == "goto_source":
                self.goto_page("source")
            elif fix_id == "goto_design":
                self.goto_page("design")
            elif fix_id == "goto_motion":
                self.goto_page("motion")

        def insert_template(self, key: str):
            """Replace the editor content with a code template."""
            code = TEMPLATES.get(key, "")
            if not code:
                return
            if self.java_edit.toPlainText().strip():
                confirm = QtWidgets.QMessageBox.question(
                    self, "Insert template",
                    f"Replace the current code with '{key}'?",
                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
                    return
            self.java_edit.setPlainText(code)
            self.goto_page("source")
            self.toast(f"Template inserted: {key}", "ok")
            self.trigger_scan()

        # --- Command palette ---
        def _palette_actions(self) -> List[dict]:
            """Assemble the command palette action list."""
            actions: List[dict] = []
            for idx, (key, title) in enumerate(NAV_ITEMS):
                actions.append({"title": f"Go to {title}", "shortcut": f"Ctrl+{idx + 1}",
                                "run": lambda k=key: self.goto_page(k)})
            actions += [
                {"title": "Build APK", "shortcut": "Ctrl+B", "run": self.on_build},
                {"title": "Save Java code", "shortcut": "Ctrl+S", "run": self.on_save_java},
                {"title": "Open a .java file", "shortcut": "Ctrl+O", "run": self.on_load_java},
                {"title": "Re-analyze code", "shortcut": "F5",
                 "run": lambda: self.trigger_scan(force=True)},
                {"title": "Toggle console", "shortcut": "Ctrl+`",
                 "run": lambda: self.show_console(not self.console_dock.isVisible())},
                {"title": "Show console", "run": lambda: self.show_console(True)},
                {"title": "Hide console", "run": lambda: self.show_console(False)},
                {"title": "Clear console", "run": lambda: self.log_view.clear()},
                {"title": "Copy console log", "run": self._copy_log},
                {"title": "Fix missing imports", "run": self.fix_imports},
                {"title": "Migrate androidx imports", "run": self.fix_androidx},
                {"title": "Copy AI coding guide", "run": lambda: self.page("aiguide")._copy_guide()},
                {"title": "Open output folder", "run": self.on_open_output},
                {"title": "Open autosave folder", "run": self._open_autosave_folder},
                {"title": "New project", "run": self.on_new_project},
                {"title": "Rescan environment", "run": self.refresh_environment},
                {"title": "Install missing libraries & tools (Data folder)", "run": self.open_installer},
                {"title": "Reset window size", "run": self._reset_window_size},
            ]
            # v3.2: automation toggles — the Commands interface is now complete
            for key, label in AUTO_AUTOMATIONS:
                short = label.split(" — ")[0]
                actions.append({"title": f"Toggle automation: {short}",
                                "detail": label,
                                "run": lambda k=key: self._toggle_auto_command(k)})
            for name in TEMPLATES:
                actions.append({"title": f"Insert template: {name}",
                                "run": lambda n=name: self.insert_template(n)})
            return actions

        def _toggle_auto_command(self, key: str):
            """Flip an automation and sync the Dashboard checkbox."""
            on = not self.auto.get(key, True)
            self.set_auto(key, on)
            if key in getattr(self._pages.get("dashboard"), "auto_cbs", {}):
                self._pages["dashboard"].auto_cbs[key].setChecked(on)
            self.toast(f"{key} → {'ON' if on else 'OFF'}", "ok")

        def _open_autosave_folder(self):
            """Open the autosave folder in the desktop file manager."""
            try:
                AUTOSAVE_JAVA.parent.mkdir(parents=True, exist_ok=True)
                QtGui.QDesktopServices.openUrl(
                    QtCore.QUrl.fromLocalFile(str(AUTOSAVE_JAVA.parent)))
            except Exception as e:
                self.log(f"[{log_time()}] [warn] autosave folder: {e}")

        def _reset_window_size(self):
            """Restore the default window size, centered on screen."""
            self.showNormal()
            self.resize(1320, 860)
            try:
                screen = QtWidgets.QApplication.primaryScreen()
                if screen is not None:
                    scr = screen.availableGeometry()
                    self.move(max(0, scr.center().x() - self.width() // 2),
                              max(0, scr.center().y() - self.height() // 2))
            except Exception:
                pass
            self.toast("Window size reset.", "info")

        def open_palette(self):
            """Open the command palette dialog."""
            palette = CommandPalette(self, self._palette_actions())
            palette.run()

        # --- Environment (background thread + splash) ---
        # --- v3.1 splash lifecycle helpers ---
        def _splash_visible(self) -> bool:
            """Safe splash check — never raises on a deleted C++ object."""
            sp = getattr(self, "splash", None)
            if sp is None:
                return False
            try:
                return sp.isVisible()
            except RuntimeError:
                self.splash = None            # wrapper is dead — drop it
                return False

        def _splash_gone(self):
            """Drop the splash reference once the widget is gone."""
            self.splash = None

        def _dismiss_splash(self):
            """Guaranteed one-shot splash dismissal (idempotent, crash-proof)."""
            sp = getattr(self, "splash", None)
            if sp is None:
                return
            try:
                if sp.isVisible():
                    sp.fade_out(on_gone=self._splash_gone)
                    return
            except RuntimeError:
                pass
            self.splash = None

        # --- v3.8.1 AUTO-ON-STARTUP / AUTO-ON-INSTALL ---
        def _autopath_fields(self) -> dict:
            """Map the autopath kinds to their Settings line edits."""
            sp = self.page("settings")
            return {"androidjar": sp.android_jar_edit, "jdk": sp.jdk_bin_edit,
                    "buildtools": sp.buildtools_edit, "dist": sp.out_dir_edit,
                    "keystore": sp.ks_path_edit, "manifest": sp.manifest_edit}

        def auto_all_paths(self, reason: str, kinds=None, only_missing: bool = False,
                           refresh: bool = True, installed_fallback: Optional[str] = None
                           ) -> Tuple[List[str], List[str]]:
            """Run the AUTO resolver for several path rows at once, silently
            (no dialogs), and record the outcome in Data/autopaths.json.

            kinds           which rows (default: all of them)
            only_missing    only fill rows that are empty or point at something
                            that no longer exists — never overrides a valid
                            hand-set path (used for the every-launch sync)
            installed_fallback  path reported by the Data installer; used when
                            the resolver can't verify the item itself
            Returns (changed_kinds, unresolved_kinds). Never raises.
            """
            changed: List[str] = []
            unresolved: List[str] = []
            try:
                labels = {"androidjar": "android.jar", "jdk": "JDK bin",
                          "buildtools": "build-tools", "dist": "output folder",
                          "keystore": "keystore", "manifest": "custom manifest"}
                fields = self._autopath_fields()
                state = load_autopaths_state()
                paths = state.setdefault("paths", {})
                for kind in (kinds or AUTOPATH_KINDS):
                    edit = fields.get(kind)
                    if edit is None:
                        continue
                    resolved = data_path_for(kind)
                    if not resolved and installed_fallback and kind in AUTOPATH_TOOLCHAIN_KINDS:
                        resolved = installed_fallback
                    if not resolved:
                        if kind != "manifest":
                            unresolved.append(kind)
                        continue
                    cur = edit.text().strip()
                    if only_missing and cur:
                        # keep a valid existing path; replace only dead ones
                        if kind not in AUTOPATH_TOOLCHAIN_KINDS or Path(cur).exists():
                            paths[kind] = cur
                            continue
                    paths[kind] = resolved
                    if cur != resolved:
                        edit.setText(resolved)
                        changed.append(kind)
                        self.log(f"[{log_time()}] Auto path — {labels[kind]} → {resolved}")
                state["last_auto_at"] = datetime.now().isoformat(timespec="seconds")
                state["last_auto_reason"] = reason
                state["unresolved"] = unresolved
                if installed_fallback is not None and kinds:
                    inst = state.setdefault("installed", {})
                    for kind in kinds:
                        if kind in paths:
                            inst[kind] = {"path": paths[kind],
                                          "at": state["last_auto_at"]}
                save_autopaths_state(state)
                if changed:
                    self._save_settings_now()
                    if refresh:
                        QtCore.QTimer.singleShot(200, self.refresh_environment)
            except Exception as e:
                self.log(f"[{log_time()}] [warn] Auto paths ({reason}): {e}")
            return changed, unresolved

        def _auto_paths_startup(self):
            """First launch (no Data/autopaths.json yet, or it lacks
            first_run_done) → AUTO for EVERY path. Every later launch → a
            light sync that fills only the toolchain rows that are empty or
            stale, so tools dropped into ./Data are picked up too."""
            try:
                state = load_autopaths_state()
                if not state.get("first_run_done"):
                    self.log(f"[{log_time()}] First launch detected — running AUTO "
                             f"for all paths")
                    try:
                        DATA_DIR.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        pass
                    changed, unresolved = self.auto_all_paths(
                        "first launch", refresh=False)
                    state = load_autopaths_state()
                    state["first_run_done"] = True
                    state["first_run_at"] = datetime.now().isoformat(timespec="seconds")
                    save_autopaths_state(state)
                    if unresolved:
                        names = {"androidjar": "android.jar", "jdk": "JDK 17",
                                 "buildtools": "build-tools 33.0.3"}
                        miss = [names[k] for k in unresolved if k in names]
                        if miss:
                            self.log(f"[{log_time()}] Not in ./Data yet: {', '.join(miss)} — "
                                     f"install them from the Dashboard (); their paths "
                                     f"fill in automatically right after each install.")
                    self.log(f"[{log_time()}] Auto paths saved to {AUTOPATHS_JSON}")
                else:
                    self.auto_all_paths("startup sync", kinds=AUTOPATH_TOOLCHAIN_KINDS,
                                        only_missing=True, refresh=False)
            except Exception as e:
                self.log(f"[{log_time()}] [warn] Auto paths startup: {e}")

        def on_data_item_installed(self, key: str, final_path: str):
            """The Data installer just finished jdk / buildtools / androidjar —
            run AUTO for that item right away (path field, settings, JSON)."""
            if key not in AUTOPATH_TOOLCHAIN_KINDS:
                return
            self.auto_all_paths(f"{key} installed", kinds=[key],
                                installed_fallback=final_path or None, refresh=False)
            # the matching field is set even if it already held the same path
            # (a reinstall) — make sure it is saved and visible in the log
            self._save_settings_soon()

        def refresh_environment(self):
            """Launch the background environment scan thread."""
            if self._closing:
                return
            if self._env_thread is not None and self._env_thread.isRunning():
                return
            # v3.7: the explicit "Build-tools folder" path (AUTO or manual)
            # from Settings → Advanced wins over auto-discovery.
            tools_override = ""
            try:
                tools_override = self.page("settings").buildtools_edit.text().strip()
            except Exception:
                pass
            self._env_thread = EnvScannerThread(self.script_dir, tools_override)
            self._env_thread.logLine.connect(self.log)
            self._env_thread.result.connect(self._on_env_result)
            self._env_thread.failed.connect(self._on_env_failed)
            self._env_thread.start()
            # v3.1 WATCHDOG: whatever happens (hang, crash, disk stall), the
            # splash can never block the window for more than 60 seconds.
            QtCore.QTimer.singleShot(60_000, self._env_watchdog)

        def _env_watchdog(self):
            """Dismiss the splash if the scan runs past 60 seconds."""
            if self._env_thread is not None and self._env_thread.isRunning():
                self.log(f"[{log_time()}] [warn] Environment scan is taking unusually long — "
                         "continuing without it for now (it will finish in the background).")
                self._dismiss_splash()

        def _on_env_failed(self, msg: str):
            """Handle a crashed scan: log, toast and unblock the UI."""
            # SAFETY NET path: scan crashed — log, toast, and ALWAYS unblock UI.
            self.log(f"[{log_time()}] [error] Environment scan failed: {msg}")
            self.toast("Environment scan failed — set tool paths in Settings → Advanced.", "error")
            self._dismiss_splash()

        def _on_env_result(self, res: dict):
            """Guard the inner env-result handler against errors."""
            try:
                self._on_env_result_inner(res)
            except Exception as e:
                self.log(f"[{log_time()}] [warn] env result: {e}")
                self._dismiss_splash()

        def _on_env_result_inner(self, res: dict):
            """Apply the scan results to the Settings fields and env UI."""
            self.tools_dir = res.get("tools_dir")
            self.tools = res.get("tools", {})

            sp = self.page("settings")
            jar_field = sp.android_jar_edit.text().strip()
            if not jar_field and res.get("jar"):
                sp.android_jar_edit.setText(res["jar"])
                self.log(f"[{log_time()}] [ok] android.jar auto-detected: {res['jar']}")
            jdk_field = sp.jdk_bin_edit.text().strip()
            if not jdk_field and res.get("jdk"):
                sp.jdk_bin_edit.setText(res["jdk"])
                _lv = res.get("jdk_level")
                self.log(f"[{log_time()}] [ok] JDK auto-detected: {res['jdk']}"
                         + (f" (Java {_lv})" if _lv else ""))
            # v3.7: when the scan found build-tools inside the portable Data
            # folder, show that location in the Advanced card too.
            bt_field = sp.buildtools_edit.text().strip()
            scanned_dir = res.get("tools_dir") or ""
            if not bt_field and scanned_dir:
                try:
                    if DATA_DIR.resolve() in Path(scanned_dir).resolve().parents:
                        sp.buildtools_edit.setText(scanned_dir)
                        self.log(f"[{log_time()}] [ok] build-tools auto-detected: {scanned_dir}")
                except Exception:
                    pass

            self._apply_env_ui()

            # v3.1: dismissal is guaranteed on EVERY path (result, failure,
            # watchdog) — the splash can never linger and block clicks.
            self._dismiss_splash()
            QtCore.QTimer.singleShot(420, self._env_toast)

        def _toolchain_pins(self) -> dict:
            """v3.8 — pinned-toolchain status for the JDK / android.jar /
            build-tools currently configured in Settings. One source of
            truth for the checklist, the status dots, the env toast and the
            install buttons. Probes are cached (per binary / per jar
            mtime), so this stays cheap on the UI thread."""
            sp = self.page("settings")
            jdk_path = sp.jdk_bin_edit.text().strip()
            jdk_ok, jdk_lvl = jdk_pin_ok(jdk_path)

            jar_path = sp.android_jar_edit.text().strip()
            jar_rng = (android_jar_api_range(jar_path)
                       if jar_path and Path(jar_path).exists() else None)
            jar_ok = jar_rng is not None and \
                jar_rng[0] <= REQUIRED_ANDROID_API <= jar_rng[1]

            tools_ok = bool(self.tools.get("aapt") or self.tools.get("aapt2")) and \
                bool(self.tools.get("zipalign")) and \
                bool(self.tools.get("apksigner_bat") or self.tools.get("apksigner_jar"))
            bt_root = self.tools.get("root") or ""
            bt_rev = build_tools_revision(bt_root) if bt_root else None
            bt_ok = tools_ok and bt_rev == REQUIRED_BUILD_TOOLS

            return {"jdk_ok": jdk_ok, "jdk_level": jdk_lvl, "jdk_path": jdk_path,
                    "jar_ok": jar_ok, "jar_range": jar_rng, "jar_path": jar_path,
                    "tools_ok": tools_ok, "bt_rev": bt_rev, "bt_ok": bt_ok}

        def _env_toast(self):
            """Toast the toolchain readiness summary after the scan."""
            pins = self._toolchain_pins()
            if pins["jdk_ok"] and pins["jar_ok"] and pins["bt_ok"]:
                self.toast("Environment ready — you can build.", "ok")
            else:
                missing = []
                if not pins["jdk_ok"]:
                    missing.append(f"JDK {REQUIRED_JDK_MAJOR}")
                if not pins["jar_ok"]:
                    missing.append(f"android.jar (API {REQUIRED_ANDROID_API})")
                if not pins["bt_ok"]:
                    missing.append(f"build-tools {REQUIRED_BUILD_TOOLS}")
                # v3.6: point at the one-click Data installer
                if self.missing_installables():
                    self.toast("Missing: " + ", ".join(missing)
                               + " — one click installs them (Dashboard button).",
                               "warn")
                else:
                    self.toast(f"Missing: {', '.join(missing)} — see Dashboard.", "warn")

        def _apply_env_ui(self):
            """Update the status dots, the gauge and the install button."""
            pins = self._toolchain_pins()
            jdk_ok, jar_ok, tools_ok = pins["jdk_ok"], pins["jar_ok"], pins["bt_ok"]

            def mini(ok):
                """Return the colored status-dot span for a flag."""
                return ("<span style='color:#44d62c'>●</span>" if ok
                        else "<span style='color:#ff7a7a'>●</span>")
            self.sb_jdk.setText(f"{mini(jdk_ok)} JDK&nbsp;&nbsp;&nbsp;")
            self.sb_jar.setText(f"{mini(jar_ok)} android.jar&nbsp;&nbsp;&nbsp;")
            self.sb_tools.setText(f"{mini(tools_ok)} build-tools")

            # ring gauge + summary
            if "dashboard" in self._pages:
                dash = self._pages["dashboard"]
                pct = (30 * jdk_ok + 30 * jar_ok + 30 * tools_ok + 10 * HAS_PIL)
                dash.env_gauge.setTarget(pct, "JDK · JAR · TOOLS")
                missing = []
                if not jdk_ok: missing.append(f"JDK {REQUIRED_JDK_MAJOR}")
                if not jar_ok: missing.append(f"android.jar (API {REQUIRED_ANDROID_API})")
                if not tools_ok: missing.append(f"build-tools {REQUIRED_BUILD_TOOLS}")
                if not HAS_PIL: missing.append("Pillow (optional)")
                if missing:
                    dash.env_summary.setText("Missing: " + ", ".join(missing))
                    dash.env_summary.setStyleSheet("color:#ffb454; background:transparent;")
                else:
                    dash.env_summary.setText("All systems operational.")
                    dash.env_summary.setStyleSheet("color:#44d62c; background:transparent;")
                # v3.6: the hero's one-click install button follows the missing set
                if hasattr(dash, "install_missing_btn"):
                    miss_keys = self.missing_installables()
                    dash.install_missing_btn.setVisible(bool(miss_keys))
                    if miss_keys:
                        dash.install_missing_btn.setText(
                            f"Download & Install Missing ({len(miss_keys)})")

            self._refresh_dashboard_safe()

        # --- Checks & pre-flight ---
        def checked_permissions(self) -> List[str]:
            """Return the permissions checked on the Settings page."""
            return self.page("settings").checked_permissions()

        def collect_checks(self) -> List[dict]:
            """Build the pre-flight readiness checklist rows."""
            sp = self.page("settings")
            java = self.java_edit.toPlainText() if hasattr(self, "java_edit") else ""
            pkg = sp.package_edit.text().strip()
            pins = self._toolchain_pins()

            # v3.8: the checklist NAMES the version it found and the one it
            # needs — a wrong version is never silently accepted
            if pins["jdk_ok"]:
                jdk_label = f"JDK {REQUIRED_JDK_MAJOR} available"
            elif pins["jdk_path"]:
                jdk_label = (f"JDK {REQUIRED_JDK_MAJOR} required — found "
                             f"JDK {pins['jdk_level'] or '?'}")
            else:
                jdk_label = f"JDK {REQUIRED_JDK_MAJOR} not found"

            if pins["jar_ok"]:
                jar_label = f"android.jar (API {REQUIRED_ANDROID_API}) found"
            elif pins["jar_path"]:
                jar_label = (f"android.jar API {REQUIRED_ANDROID_API} required — "
                             f"found {android_jar_api_label(pins['jar_range'])}")
            else:
                jar_label = f"android.jar (API {REQUIRED_ANDROID_API}) not found"

            if pins["bt_ok"]:
                bt_label = f"Build-tools {REQUIRED_BUILD_TOOLS} ready"
            elif pins["tools_ok"]:
                bt_label = (f"Build-tools {REQUIRED_BUILD_TOOLS} required — found "
                            f"{pins['bt_rev'] or 'unversioned'}")
            else:
                bt_label = f"Build-tools {REQUIRED_BUILD_TOOLS} not found"

            return [
                {"ok": bool(java.strip()), "label": "Java code present", "page": "source"},
                {"ok": bool(sp.app_name_edit.text().strip()), "label": "App name set", "page": "settings"},
                {"ok": package_is_valid(pkg), "label": "Package name valid", "page": "settings"},
                {"ok": pins["jdk_ok"], "label": jdk_label, "page": "settings",
                 "install": "jdk"},
                {"ok": pins["jar_ok"], "label": jar_label, "page": "settings",
                 "install": "androidjar"},
                {"ok": pins["bt_ok"], "label": bt_label, "page": "settings",
                 "install": "buildtools"},
                {"ok": bool(self.cfg.icon_path), "warn": True,
                 "label": "Icon selected (optional)", "page": "design"},
                # v3.6: missing Python libraries are installable too — one
                # click downloads them into the Data folder (never site-packages)
                {"ok": HAS_PIL, "warn": True,
                 "label": "Pillow — icon resizing (optional)", "install": "pillow"},
                {"ok": HAS_QTMULTIMEDIA, "warn": True,
                 "label": "QtMultimedia — sound preview (optional)",
                 "install": "qtmultimedia"},
            ]

        def missing_installables(self) -> List[str]:
            """v3.6 — installable items that are currently missing, in
            canonical INSTALL_ORDER. Drives the buttons everywhere.
            v3.8: a WRONG VERSION counts as missing — the one-click install
            replaces it with the pinned one."""
            pins = self._toolchain_pins()
            missing: List[str] = []
            if not pins["jdk_ok"]:
                missing.append("jdk")
            if not pins["jar_ok"]:
                missing.append("androidjar")
            if not pins["bt_ok"]:
                missing.append("buildtools")

            if not HAS_PIL:
                missing.append("pillow")
            if HAS_QT and not HAS_QTMULTIMEDIA:
                missing.append("qtmultimedia")

            return [k for k in INSTALL_ORDER if k in missing]

        def open_installer(self, preselect: Optional[List[str]] = None):
            """v3.6 — open the Data Installer dialog. Without arguments every
            currently-missing item is preselected; pass keys to preselect just
            those (used by the button beside a single check row)."""
            missing = self.missing_installables()
            if preselect is None:
                preselect = missing
            else:
                preselect = [k for k in INSTALL_ORDER if k in preselect]
                if not preselect:
                    preselect = missing
            if not missing and not preselect:
                self.toast("Nothing to install — everything is already here.", "ok")
                return
            dlg = InstallDialog(self, self, preselect)
            dlg.exec()

        def _collect_config(self):
            """Pull every UI field into the live BuildConfig."""
            sp = self.page("settings")
            self.cfg.app_name = sp.app_name_edit.text().strip() or APP_DEFAULTS["app_name"]
            self.cfg.package = sp.package_edit.text().strip() or APP_DEFAULTS["package"]
            self.cfg.activity_name = sp.activity_edit.text().strip() or APP_DEFAULTS["activity_name"]
            self.cfg.version_name = sp.vname_edit.text().strip() or "1.0"
            self.cfg.version_code = sp.vcode_spin.value()
            self.cfg.min_sdk = sp.min_sdk_combo.currentData() or APP_DEFAULTS["min_sdk"]
            self.cfg.target_sdk = sp.target_sdk_combo.currentData() or APP_DEFAULTS["target_sdk"]
            self.cfg.permissions = sp.checked_permissions()
            self.cfg.java_text = self.java_edit.toPlainText()
            # v3.1: reuse the last background scan when it's fresh — avoids a
            # UI-thread structure scan of a huge file right before building.
            if self.last_scan and self.last_scan.get("analysis") is not None \
                    and self.last_scan["analysis"].chars == len(self.cfg.java_text):
                self.cfg.java_is_full = self.last_scan["analysis"].is_full
            else:
                self.cfg.java_is_full = is_full_java_class(self.cfg.java_text)
            self.cfg.android_jar = sp.android_jar_edit.text().strip()
            self.cfg.jdk_bin = sp.jdk_bin_edit.text().strip()
            self.cfg.output_dir = sp.out_dir_edit.text().strip()
            self.cfg.keystore_path = sp.ks_path_edit.text().strip()
            self.cfg.keystore_pass = sp.ks_pass_edit.text() or "android"
            self.cfg.key_alias = sp.key_alias_edit.text() or "androiddebugkey"
            self.cfg.key_pass = sp.key_pass_edit.text() or "android"
            self.cfg.use_aapt2 = sp.aapt2_cb.isChecked()
            self.cfg.keep_temp = sp.keep_temp_cb.isChecked()
            self.cfg.custom_manifest_path = sp.manifest_edit.text().strip()
            self.cfg.tools = self.tools
            self.cfg.auto_imports = self.auto.get("auto_imports", True)
            self.cfg.auto_perms = self.auto.get("auto_perms", True)
            self.cfg.auto_min_sdk = self.auto.get("auto_min_sdk", True)

        def _snapshot_config(self) -> BuildConfig:
            """v3.1: deep-ish copy of cfg for the build thread. The UI keeps
            mutating the live cfg while a build runs — the thread now reads
            this immutable snapshot instead (lists copied, scalars frozen)."""
            snap = BuildConfig()
            src = self.cfg
            for f in ("app_name", "package", "activity_name", "version_name",
                      "version_code", "min_sdk", "target_sdk", "java_text",
                      "java_is_full", "android_jar", "jdk_bin", "keystore_path",
                      "keystore_pass", "key_alias", "key_pass", "use_aapt2",
                      "output_dir", "build_tools_dir", "keep_temp", "icon_path",
                      "custom_manifest_path", "auto_imports", "auto_perms",
                      "auto_min_sdk"):
                setattr(snap, f, getattr(src, f))
            snap.permissions = list(src.permissions)
            snap.assets = [e.copy() for e in src.assets]   # v3.4 rich asset entries
            snap.elements = list(src.elements)
            snap.tools = dict(src.tools)
            snap.resource_manager = src.resource_manager
            return snap

        # --- Build flow ---
        def on_build(self):
            """Validate readiness and launch the background build thread."""
            if self._thread is not None and self._thread.isRunning():
                self.toast("A build is already running.", "info")
                return

            self._collect_config()
            problems = [c for c in self.collect_checks() if not c["ok"] and not c.get("warn")]
            if problems:
                listing = "\n".join(f"•  {c['label']}" for c in problems)
                # v3.6: missing tools & libraries can be downloaded right here
                installable = [c["install"] for c in problems if c.get("install")]
                if installable:
                    mb = QtWidgets.QMessageBox(self)
                    mb.setWindowTitle("Not ready to build")
                    mb.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                    mb.setText(f"Resolve these items first:\n\n{listing}")
                    mb.setInformativeText(
                        "Missing libraries & tools download automatically into the\n"
                        "portable Data folder beside APK Forge — your system is\n"
                        "never touched.")
                    btn_install = mb.addButton(
                        "Download & Install",
                        QtWidgets.QMessageBox.ButtonRole.AcceptRole)
                    mb.addButton("Go to Dashboard",
                                 QtWidgets.QMessageBox.ButtonRole.RejectRole)
                    mb.exec()
                    if mb.clickedButton() is btn_install:
                        self.open_installer(installable)
                        return
                    self.goto_page("dashboard")
                    return
                QtWidgets.QMessageBox.warning(
                    self, "Not ready to build",
                    f"Resolve these items first (the Dashboard shows one-click fixes):\n\n{listing}")
                self.goto_page("dashboard")
                return

            # fresh resource manager per build
            self.cfg.resource_manager = ResourceManager()

            # v3.1: the thread builds from a SNAPSHOT — the UI's live cfg can
            # keep changing while the build runs without any race.
            self._build_cfg = self._snapshot_config()
            self._thread = BuilderThread(self._build_cfg)
            self._thread.logLine.connect(self.log)
            self._thread.stage.connect(self._on_stage)
            self._thread.done.connect(self._on_build_done)

            self.build_progress.setValue(0)
            self.build_progress.start_shimmer()
            self.build_status.setText("Building…")
            self.build_btn.setEnabled(False)
            self.build_btn.setText("BUILDING…")
            self.show_console(True)
            self.log(f"[{log_time()}] Build started — {self.cfg.app_name} v{self.cfg.version_name} "
                     f"({self.cfg.activity_name})")
            self._thread.start()

        def _on_stage(self, pct: int, name: str):
            """Update the progress bar and status for a build stage."""
            self.build_progress.setValue(pct)
            self.build_status.setText(f"{pct}% — {name}")

        def _on_build_done(self, ok: bool, msg: str):
            """Finalize the build UI, apply automations, record history."""
            self.build_btn.setEnabled(True)
            self.build_btn.setText("BUILD APK")
            self.build_progress.stop_shimmer()

            if ok:
                self.build_progress.setValue(100)
                self.build_status.setText("Success")
                self.log(f"[{log_time()}] APK ready: {msg}")
                if not self._closing:
                    self.toast(f"APK built: {Path(msg).name}", "ok")

                # v3.1: sync build-time automations (auto min-SDK, auto perms)
                # back from the snapshot into the live UI settings.
                snap = self._build_cfg
                if snap is not None:
                    try:
                        sp = self.page("settings")
                        if snap.min_sdk != (sp.min_sdk_combo.currentData() or 21):
                            sp._select_combo(sp.min_sdk_combo, snap.min_sdk)
                            self.cfg.min_sdk = snap.min_sdk
                            self.log(f"[{log_time()}] [auto] minSdk synced to {snap.min_sdk} "
                                     f"(raised automatically at build time)")
                        if snap.permissions:
                            sp.ensure_permission_items(snap.permissions)
                            sp.set_permissions(snap.permissions)
                            self.cfg.permissions = list(snap.permissions)
                    except Exception as e:
                        self.log(f"[{log_time()}] [warn] config sync: {e}")

                # record build history
                try:
                    size = Path(msg).stat().st_size
                except Exception:
                    size = 0
                self.build_history.insert(0, {"apk": msg, "size": size,
                                               "time": datetime.now().strftime("%Y-%m-%d %H:%M")})
                self.build_history = self.build_history[:12]
                self._save_settings_soon()

                if self.auto.get("auto_open") and not self._closing:
                    out_dir = Path(msg).parent
                    QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(out_dir)))
                if self.auto.get("auto_bump"):
                    sp = self.page("settings")
                    sp.vcode_spin.setValue(sp.vcode_spin.value() + 1)
                    self.log(f"[{log_time()}] [auto] Version code bumped "
                             f"to {sp.vcode_spin.value()}")
                    self._save_settings_soon()
                self._refresh_dashboard_safe()
            else:
                self.build_progress.setValue(0)
                self.build_status.setText("Failed")
                self.log(f"[{log_time()}] [error] Build failed: {msg}")
                if not self._closing:
                    self.toast("Build failed — check the console.", "error")
                    QtWidgets.QMessageBox.warning(
                        self, "Build failed",
                        f"The build did not complete:\n\n{msg}\n\nCheck the console for the full log.")

            # v3.1: the user asked to exit mid-build — now it's safe.
            if self._closing:
                self._save_settings_now()
                self._really_close = True
                self.close()

        # --- Actions ---
        def on_load_java(self):
            """Open a .java file into the editor."""
            p, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open Java File", "", "Java Files (*.java);;Text Files (*.txt);;All Files (*)")
            if not p:
                return
            try:
                text = Path(p).read_text(encoding="utf-8", errors="replace")
                if text.startswith("\ufeff"):      # v3.2: strip a UTF-8 BOM
                    text = text.lstrip("\ufeff")
                self.java_edit.setPlainText(text)
                self.log(f"[{log_time()}] Loaded: {p}")
                self.toast(f"Loaded {Path(p).name}", "ok")
                self.trigger_scan(force=True)
                self.goto_page("source")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Load failed", f"Could not read file:\n{e}")

        def on_save_java(self):
            """Save the editor text to a .java file."""
            p, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Java Code", f"{self.cfg.activity_name}.java",
                "Java Files (*.java);;All Files (*)")
            if not p:
                return
            if export_java_code(self.java_edit.toPlainText(), p):
                self.log(f"[{log_time()}] Saved: {p}")
                self.toast(f"Saved {Path(p).name}", "ok")
            else:
                QtWidgets.QMessageBox.critical(self, "Save failed", "Could not write the file.")

        def on_new_project(self):
            """Clear code, icon, assets and elements after confirmation."""
            confirm = QtWidgets.QMessageBox.question(
                self, "New project",
                "Clear the Java code, icon, assets and element configuration?\n"
                "(App settings are kept.)",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
                return
            self.java_edit.clear()
            self.cfg.elements.clear()
            self.page("design")._clear_icon()
            self.cfg.assets.clear()
            self.page("design").refresh_assets()
            self._after_elements_changed()
            self._save_settings_soon()
            self.log(f"[{log_time()}] [auto] New project started")
            self.goto_page("source")

        def on_open_output(self):
            """Open the output folder in the desktop file manager."""
            out = self.page("settings").out_dir_edit.text().strip()
            out_dir = Path(out) if out else (Path.cwd() / "dist")
            out_dir.mkdir(parents=True, exist_ok=True)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(out_dir)))

        # --- Automation toggles ---
        def set_auto(self, key: str, on: bool):
            """Set an automation toggle and persist it soon."""
            self.auto[key] = on
            self._save_settings_soon()
            self.log(f"[{log_time()}] Automation '{key}' → {'ON' if on else 'OFF'}")

        # --- Persistence (debounced) ---
        def _save_settings_soon(self):
            """Debounce a settings save (skipped while loading)."""
            if getattr(self, "_loading", False):
                return
            self._save_timer.start()

        def _save_settings_now(self):
            """Persist all project settings to QSettings now."""
            if getattr(self, "_loading", False):
                return
            try:
                s = QtCore.QSettings("ApkForge", "Studio")
                sp = self.page("settings")
                s.setValue("app_name", sp.app_name_edit.text())
                s.setValue("package", sp.package_edit.text())
                s.setValue("activity_name", sp.activity_edit.text())
                s.setValue("version_name", sp.vname_edit.text())
                s.setValue("version_code", sp.vcode_spin.value())
                s.setValue("min_sdk", sp.min_sdk_combo.currentData() or 21)
                s.setValue("target_sdk", sp.target_sdk_combo.currentData() or 33)
                s.setValue("permissions", ",".join(sp.checked_permissions()))
                s.setValue("android_jar", sp.android_jar_edit.text())
                s.setValue("jdk_bin", sp.jdk_bin_edit.text())
                s.setValue("buildtools_dir", sp.buildtools_edit.text())
                s.setValue("out_dir", sp.out_dir_edit.text())
                s.setValue("keystore_path", sp.ks_path_edit.text())
                s.setValue("keystore_pass", sp.ks_pass_edit.text())
                s.setValue("key_alias", sp.key_alias_edit.text())
                s.setValue("key_pass", sp.key_pass_edit.text())
                s.setValue("use_aapt2", sp.aapt2_cb.isChecked())
                s.setValue("keep_temp", sp.keep_temp_cb.isChecked())
                s.setValue("custom_manifest", sp.manifest_edit.text())
                s.setValue("icon_path", self.cfg.icon_path)
                # v3.4: rich asset entries (JSON — inline text assets included)
                s.setValue("assets_json", json.dumps(
                    [e.to_json() for e in self.cfg.assets]))
                s.setValue("pkg_auto", sp.pkg_auto_btn.isChecked())
                for k, v in self.auto.items():
                    s.setValue(k, v)
                elems = [{"name": e.name, "type": e.type, "animations": e.animations,
                          "duration": e.animation_duration, "sound": e.sound_path,
                          "image": e.image_path, "auto_size": e.auto_size}
                         for e in self.cfg.elements]
                s.setValue("elements_json", json.dumps(elems))
                s.setValue("build_history_json", json.dumps(self.build_history))
            except Exception as e:
                self.log(f"[{log_time()}] [warn] Settings save failed: {e}")

        def _load_settings(self):
            """Load the persisted settings into the Settings page."""
            s = QtCore.QSettings("ApkForge", "Studio")
            sp = self.page("settings")
            self._loading = True
            try:
                self._load_settings_inner(s, sp)
            finally:
                self._loading = False

        def _load_settings_inner(self, s, sp):
            """Apply the stored settings values to the UI and config."""
            for label, perm in PERMISSION_CATALOG:
                sp._add_permission_item(label, perm)

            if s.contains("app_name"):
                sp.app_name_edit.setText(s.value("app_name", "", type=str))
            if s.contains("package"):
                sp.package_edit.setText(s.value("package", "", type=str))
            if s.contains("activity_name"):
                sp.activity_edit.setText(s.value("activity_name", "", type=str))
            sp.vname_edit.setText(s.value("version_name", "1.0", type=str))
            sp.vcode_spin.setValue(s.value("version_code", 1, type=int))
            sp._select_combo(sp.min_sdk_combo, s.value("min_sdk", 21, type=int))
            sp._select_combo(sp.target_sdk_combo, s.value("target_sdk", 33, type=int))

            if s.contains("permissions"):
                perms = [p for p in str(s.value("permissions", "", type=str)).split(",") if p]
                sp.ensure_permission_items(perms)
                sp.set_permissions(perms)

            for key, edit in (("android_jar", sp.android_jar_edit), ("jdk_bin", sp.jdk_bin_edit),
                              ("buildtools_dir", sp.buildtools_edit),
                              ("out_dir", sp.out_dir_edit), ("keystore_path", sp.ks_path_edit),
                              ("custom_manifest", sp.manifest_edit)):
                if s.contains(key):
                    edit.setText(s.value(key, "", type=str))
            sp.ks_pass_edit.setText(s.value("keystore_pass", "android", type=str))
            sp.key_alias_edit.setText(s.value("key_alias", "androiddebugkey", type=str))
            sp.key_pass_edit.setText(s.value("key_pass", "android", type=str))
            sp.aapt2_cb.setChecked(s.value("use_aapt2", False, type=bool))
            sp.keep_temp_cb.setChecked(s.value("keep_temp", False, type=bool))
            sp.pkg_auto_btn.setChecked(s.value("pkg_auto", True, type=bool))

            if s.contains("icon_path"):
                self.cfg.icon_path = s.value("icon_path", "", type=str)
            # v3.4 assets: new rich entries, with automatic migration from the
            # old flat "||"-joined path list
            try:
                if s.contains("assets_json"):
                    data = json.loads(str(s.value("assets_json", "[]", type=str)))
                    self.cfg.assets = [AssetEntry.from_json(d) for d in data
                                       if isinstance(d, dict)]
                elif s.contains("additional_files"):
                    files = [f for f in str(s.value("additional_files", "", type=str)).split("||") if f]
                    self.cfg.assets = [AssetEntry.from_path(f)
                                       for f in files if Path(f).exists()]
            except Exception as e:
                self.log(f"[{log_time()}] [warn] Asset settings load failed: {e}")
                self.cfg.assets = []

            for k in list(self.auto.keys()):
                self.auto[k] = s.value(k, True, type=bool)
            if "dashboard" in self._pages:
                for key, cb in self._pages["dashboard"].auto_cbs.items():
                    cb.setChecked(self.auto.get(key, True))

            # restore element configurations (merged at scan time)
            try:
                data = s.value("elements_json", "", type=str)
                if data:
                    for item in json.loads(data):
                        self._restored_elements[item["name"]] = ElementInfo(
                            name=item.get("name", ""),
                            type=item.get("type", "View"),
                            animations=list(item.get("animations", [])),
                            animation_duration=int(item.get("duration", 300)),
                            sound_path=item.get("sound", ""),
                            image_path=item.get("image", ""),
                            auto_size=bool(item.get("auto_size", True)))
            except Exception:
                pass

            # build history
            try:
                h = s.value("build_history_json", "", type=str)
                if h:
                    self.build_history = [e for e in json.loads(h) if isinstance(e, dict)]
            except Exception:
                pass

            sp._validate_package()
            sp._on_perm_changed()

        # --- Misc — v3.1: all size/close paths are crash-proof ---
        def showEvent(self, e):
            """Center once, sync the splash, snap the nav indicator."""
            super().showEvent(e)
            # v3.2: center the window on the screen the first time it appears
            if not getattr(self, "_centered_once", False):
                self._centered_once = True
                try:
                    screen = QtWidgets.QApplication.primaryScreen()
                    if screen is not None:
                        scr = screen.availableGeometry()
                        self.move(max(0, scr.center().x() - self.width() // 2),
                                  max(0, scr.center().y() - self.height() // 2))
                except Exception:
                    pass
            # position the splash correctly once the layout is real
            # (v3.2: geometry comes from the splash's OWN parent — using
            # centralWidget().rect() while the splash lived on `content` was
            # the off-center-welcome bug.)
            self._splash_sync()
            # first layout pass is final now — snap the nav indicator (no anim)
            QtCore.QTimer.singleShot(0, lambda: self._update_nav_indicator(animate=False))

        def resizeEvent(self, e):
            """Re-sync splash, nav indicator and toasts on resize."""
            super().resizeEvent(e)
            # v3.1 CRASH FIX + v3.2 CENTERING FIX: the splash syncs itself via
            # its parent event filter; this is a belt-and-suspenders pass that
            # also clears a dead wrapper instead of raising RuntimeError.
            self._splash_sync()
            # nav indicator follows the (possibly re-flowed) sidebar instantly
            self._update_nav_indicator(animate=False)
            # toasts: iterate over a COPY and drop dead wrappers defensively
            lst = Toast._by_parent.get(id(self), [])
            for t in list(lst):
                try:
                    t._relayout_siblings()
                except RuntimeError:
                    try:
                        lst.remove(t)
                    except Exception:
                        pass

        def _splash_sync(self):
            """Keep the splash exactly covering ITS OWN parent (v3.2)."""
            sp = getattr(self, "splash", None)
            if sp is None:
                return
            try:
                pw = sp.parentWidget()
                if pw is not None:
                    sp.setGeometry(pw.rect())
                    sp.raise_()
            except RuntimeError:
                self.splash = None

        def closeEvent(self, event):
            """Close safely even while a build thread is running."""
            # v3.1 CRASH FIX: closing while a build runs used to destroy a
            # running QThread (hard abort). Now we hide the window, let the
            # build finish in the background (its 600s watchdog guarantees it
            # ends), and close for real from _on_build_done().
            if self._thread is not None and self._thread.isRunning() \
                    and not self._really_close:
                if not self._closing:
                    confirm = QtWidgets.QMessageBox.question(
                        self, "Build in progress",
                        "A build is still running.\n\n"
                        "Exit now and let it finish in the background?\n"
                        "(APK Forge closes automatically when the build ends.)",
                        QtWidgets.QMessageBox.StandardButton.Yes |
                        QtWidgets.QMessageBox.StandardButton.No)
                    if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
                        event.ignore()
                        return
                    self._closing = True
                    self.log(f"[{log_time()}] Waiting for the running build to finish — "
                             "the window will close itself automatically.")
                    self._save_settings_now()
                    try:
                        AUTOSAVE_JAVA.parent.mkdir(parents=True, exist_ok=True)
                        AUTOSAVE_JAVA.write_text(self.java_edit.toPlainText(),
                                                 encoding="utf-8")
                    except Exception:
                        pass
                    self.hide()
                event.ignore()
                return

            # env thread: it's short-lived — a brief wait is safe & clean
            if self._env_thread is not None and self._env_thread.isRunning():
                self._env_thread.wait(3000)

            self._save_settings_now()
            try:
                AUTOSAVE_JAVA.parent.mkdir(parents=True, exist_ok=True)
                AUTOSAVE_JAVA.write_text(self.java_edit.toPlainText(), encoding="utf-8")
            except Exception:
                pass
            event.accept()


# ---------------------------------------------------------------------------
# Entry point — instant window, everything heavy in the background
# ---------------------------------------------------------------------------
_WINDOW_REF: Optional[weakref.ref] = None      # for the global excepthook


def _make_excepthook():
    """v3.1 SAFETY NET.

    With a custom sys.excepthook installed, PyQt no longer qFatal-aborts the
    process when a slot raises — the error is logged and the app keeps
    running. threading.excepthook covers plain Python threads (watchdog etc).
    """
    def hook(exc_type, exc_value, exc_tb):
        """Report one unhandled exception without killing the app."""
        try:
            # keep the stderr print for developers
            sys.__excepthook__(exc_type, exc_value, exc_tb)
        except Exception:
            pass
        try:
            msg = "".join(traceback.format_exception_only(exc_type, exc_value)).strip()
            win = _WINDOW_REF() if _WINDOW_REF is not None else None
            if win is not None:
                try:
                    win.log(f"[{log_time()}] [error] Internal error "
                             f"(recovered, app continues): {msg}")
                except Exception:
                    pass
        except Exception:
            pass
    return hook


# ---------------------------------------------------------------------------
# v3.6 CONSOLE BOOTSTRAP — "which libraries are needed?" answered before Qt
# ---------------------------------------------------------------------------
# When the code runs and a library is missing, a beautiful console banner
# lists EXACTLY what is needed and why, then offers a one-question install:
# answer Y (or press Enter) and everything downloads into ./Data — the app
# even restarts itself when PyQt6 was just installed.

_CON_GREEN = "\033[92m"
_CON_AMBER = "\033[93m"
_CON_RED = "\033[91m"
_CON_DIM = "\033[2m"
_CON_BOLD = "\033[1m"
_CON_RESET = "\033[0m"
_CON_ANSI_OK = False


def _console_init():
    """UTF-8-safe stdout + ANSI colors on Windows 10+ consoles."""
    global _CON_ANSI_OK
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    _CON_ANSI_OK = False
    if IS_WINDOWS:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                _CON_ANSI_OK = bool(kernel32.SetConsoleMode(
                    handle, mode.value | 0x0004))
        except Exception:
            _CON_ANSI_OK = False
    else:
        _CON_ANSI_OK = True


def _c(code: str, text: str) -> str:
    """ANSI-color-wrap text when console colors are on, else return as-is."""
    return f"{code}{text}{_CON_RESET}" if _CON_ANSI_OK else text


def _console_banner(lines: List[str], width: int = 62):
    """Print a framed box that survives every Windows code page."""
    bar = "═" * width
    print(_c(_CON_GREEN, "╔" + bar + "╗"))
    for ln in lines:
        pad = width - len(ln)
        # len() counts chars; emojis are 1 for print but may render wider —
        # conservative padding keeps the right border aligned.
        print(_c(_CON_GREEN, "║") + " " + ln + " " * max(0, pad - 2) +
              " " + _c(_CON_GREEN, "║"))
    print(_c(_CON_GREEN, "╚" + bar + "╝"))


# --- v3.7 console gate — helper script & new-console install flow ---
# v3.7 CONSOLE GATE — when APK Forge starts WITHOUT a console of its own
# (double-clicked, launched with pythonw.exe, or from a GUI shortcut) and a
# Python library is missing, a REAL console window must open and ask the
# user. This tiny helper script runs INSIDE that fresh window: it shows the
# missing-library banner, asks the one Y/n question and — on Y — runs the
# pip install right there with live output, then reports back via a file.
_CONSOLE_BOOTSTRAP_SCRIPT = r'''#!/usr/bin/env python3
# APK Forge console bootstrap (runs inside a freshly opened console window)
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
try:
    import ctypes
    ctypes.windll.kernel32.SetConsoleTitleW("APK Forge - install libraries?")
except Exception:
    pass

BANNER, QUESTION, RESULT, TARGET, PACKAGES = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]


def _finish(state):
    try:
        with open(RESULT, "w", encoding="utf-8") as fh:
            fh.write(state)
    except Exception:
        pass
    try:
        input("\nPress Enter to close this window... ")
    except BaseException:
        pass
    sys.exit(0)


try:
    with open(BANNER, "r", encoding="utf-8") as fh:
        print(fh.read(), end="")
except Exception:
    pass

try:
    answer = input(QUESTION)
except BaseException:
    answer = "n"

if (answer or "").strip().lower() in ("n", "no"):
    print("")
    print("Noted - nothing was installed. APK Forge needs PyQt6 to start;")
    print("re-run it and answer Y, or install manually:  pip install PyQt6")
    _finish("declined")

print("")
rc = subprocess.call(
    [sys.executable, "-m", "pip", "install", "--no-input", "--upgrade",
     "--target", TARGET] + [p for p in PACKAGES.split(",") if p])
if rc == 0:
    print("")
    print("Done - libraries installed into the portable Data folder.")
    _finish("installed")
print("")
print("pip exited with code %s - see the messages above." % rc)
_finish("failed")
'''


def _console_python_exe() -> Optional[str]:
    """A console-capable python.exe for this interpreter.

    pythonw.exe is a GUI-subsystem binary — a child launched from it never
    gets a console, even with CREATE_NEW_CONSOLE. When running under
    pythonw, use its sibling python.exe instead.
    """
    exe = sys.executable
    if not exe:
        return None
    if IS_WINDOWS and exe.lower().endswith("pythonw.exe"):
        cand = exe[:-len("pythonw.exe")] + "python.exe"
        return cand if Path(cand).exists() else None
    return exe


def _ask_install_in_new_console(banner_lines: List[str], question: str,
                                packages: List[str]) -> Optional[str]:
    """Open a REAL console window, ask the Y/n question there and — on Y —
    run the pip install inside it with live output.

    Used when APK Forge was started WITHOUT a console of its own (pythonw /
    double-click): the user literally gets "a console window that opens and
    asks". Returns "installed" | "declined" | "failed", or None when no
    console window could be opened at all.
    """
    py = _console_python_exe()
    if not py:
        return None
    tmp: Optional[Path] = None
    try:
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="apkforge-console-"))
        helper = tmp / "console_ask.py"
        banner = tmp / "banner.txt"
        result = tmp / "answer.txt"
        helper.write_text(_CONSOLE_BOOTSTRAP_SCRIPT, encoding="utf-8")
        banner.write_text("\n".join(banner_lines) + "\n\n", encoding="utf-8")
        # CREATE_NEW_CONSOLE: the child gets its very own console window,
        # even though THIS process has none.
        flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        subprocess.run(
            [py, str(helper), str(banner), question, str(result),
             str(DATA_PY_DIR), ",".join(packages)],
            creationflags=flags)
        if result.exists():
            state = result.read_text(encoding="utf-8").strip()
            if state in ("installed", "declined", "failed"):
                return state
        return None
    except Exception:
        return None
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)


# --- missing-library check & one-click install into ./Data ---

_RE_ANSI_STRIP = re.compile(r"\x1b\[[0-9;]*m")   # ANSI color escapes


def ensure_runtime_libraries() -> bool:
    """Detect missing Python libraries at run time and offer a one-click
    install into the Data folder. Returns True when the app may start.

    Required : PyQt6            (the whole user interface)
    Optional : Pillow           (icon resizing)
               QtMultimedia     (in-tool sound preview)
    """
    global HAS_PIL

    _console_init()

    required_missing = [] if HAS_QT else ["PyQt6"]
    optional_missing = []
    if HAS_QT and not HAS_PIL:
        optional_missing.append("Pillow")
    if HAS_QT and not HAS_QTMULTIMEDIA:
        optional_missing.append("PyQt6 (QtMultimedia module)")

    if not required_missing and not optional_missing:
        return True

    why = {
        "PyQt6": "the user interface — required",
        "Pillow": "icon resizing & thumbnails — optional",
        "PyQt6 (QtMultimedia module)": "in-tool sound preview — optional",
    }
    sizes = {"PyQt6": "≈ 70 MB", "Pillow": "≈ 5 MB",
             "PyQt6 (QtMultimedia module)": "≈ 70 MB"}

    def _pad(text: str, width: int) -> str:
        """Pad the RAW text (ANSI codes must not count toward the width)."""
        return text + " " * max(0, width - len(text))

    lines = [f"{_c(_CON_BOLD, 'APK FORGE v' + APP_VERSION)} — {_c(_CON_RED, 'missing libraries detected')}",
             ""]
    for name in required_missing:
        lines.append(f"  {_c(_CON_RED, 'X')} {_c(_CON_BOLD, _pad(name, 32))}"
                     f"{_c(_CON_DIM, why.get(name, ''))}")
        lines.append(f"     {_c(_CON_DIM, sizes.get(name, ''))}")
    for name in optional_missing:
        lines.append(f"  {_c(_CON_AMBER, '•')} {_c(_CON_BOLD, _pad(name, 32))}"
                     f"{_c(_CON_DIM, why.get(name, ''))}")
        lines.append(f"     {_c(_CON_DIM, sizes.get(name, ''))}")
    lines += ["",
              f"  Everything installs into the portable folder:",
              f"  {_c(_CON_BOLD, str(DATA_PY_DIR))}",
              "  (nothing touches your system — delete the folder to undo)"]
    _console_banner(lines)

    # exact pip set: PyQt6 (+QtMultimedia support) and Pillow when missing
    pip_set = ["PyQt6", "PyQt6-Addons"] if required_missing else []
    if "Pillow" in optional_missing or "Pillow" in required_missing:
        pip_set.append("Pillow")
    if not pip_set:
        pip_set = ["PyQt6", "PyQt6-Addons"]

    want = os.environ.get("APKFORGE_AUTO_INSTALL", "").strip().lower()
    window_state: Optional[str] = None      # console-window flow result (v3.7)
    if want not in ("1", "y", "yes"):
        try:
            answer = input(_c(_CON_BOLD,
                              "Download & install these into ./Data now? [Y/n] "))
        except (EOFError, KeyboardInterrupt):
            answer = "n"
            print()
        except (RuntimeError, OSError, AttributeError):
            answer = None          # no console attached at all (pythonw…)
        if answer is None:
            # v3.7 CONSOLE GATE: “a console window must open” — literally.
            # Started without a console (double-click / pythonw.exe)? Open
            # one, ask there, and on Y install right inside that window.
            if IS_WINDOWS:
                # plain text only — the fresh console may not render ANSI
                plain = [_RE_ANSI_STRIP.sub("", ln) for ln in lines]
                window_state = _ask_install_in_new_console(
                    plain, "Download & install these into ./Data now? [Y/n] ",
                    pip_set)
                if window_state == "declined":
                    answer = "n"
                elif window_state in ("installed", "failed"):
                    answer = "y"
                else:
                    answer = "n"   # no window possible — safe default
            else:
                answer = "n"
        if answer.strip().lower() in ("n", "no"):
            if required_missing:
                print(_c(_CON_RED,
                         "\nAPK Forge cannot start without PyQt6. Install it manually:\n"))
                print(_c(_CON_BOLD, "    pip install PyQt6\n")
                      + _c(_CON_DIM, "    (or re-run and answer Y to install into ./Data)\n"))
                return False
            if optional_missing:
                print(_c(_CON_AMBER,
                         "\nContinuing without the optional libraries "
                         "(icon resizing / sound preview will be limited).\n"))
            return True

    if window_state == "installed":
        # the console window already ran the pip install — live, with output
        ok, msg = True, "installed"
    elif window_state == "failed":
        ok, msg = False, "pip failed — see the console window."
    else:
        print(_c(_CON_DIM, f"Installing: {', '.join(pip_set)} → {DATA_PY_DIR}\n"))

        def _pip_line(line: str):
            """Print one pip output line, dimmed."""
            # one callback, one print — _pip_install_to_data reports every pip
            # line through BOTH progress_cb and log_cb, so only log_cb prints.
            print("    " + _c(_CON_DIM, line))

        ok, msg = _pip_install_to_data(
            pip_set, log_cb=_pip_line, cancel_check=lambda: False)
        if not ok and "PyQt6-Addons" in pip_set and "PyQt6" in pip_set:
            # Hardening: some platforms/mirrors ship no PyQt6-Addons wheel
            # (it only powers the optional in-tool sound preview).
            # The GUI's core must still make it in — retry without it.
            print(_c(_CON_AMBER,
                     "\n· no PyQt6-Addons wheel here — retrying without it "
                     "(sound preview stays disabled)…\n"))
            core = [p for p in pip_set if p != "PyQt6-Addons"]
            ok, msg = _pip_install_to_data(
                core, log_cb=_pip_line, cancel_check=lambda: False)
            if ok:
                print(_c(_CON_AMBER,
                         "Installed the core set — QtMultimedia (sound "
                         "preview) can be added later from the Dashboard."))

    if not ok:
        print(_c(_CON_RED, f"\nInstallation failed: {msg}"))
        if required_missing:
            print(_c(_CON_BOLD, "\n    pip install PyQt6\n"))
            return False
        print(_c(_CON_AMBER, "Continuing without the optional libraries.\n"))
        return True

    print(_c(_CON_GREEN, "\nLibraries installed into ./Data — no system files touched."))

    if required_missing:
        # PyQt6 just arrived: restart so the module-level `if HAS_QT:` block
        # (all GUI classes) is defined with the fresh interpreter state.
        print(_c(_CON_BOLD, "Restarting APK Forge…\n"))
        try:
            sys.stdout.flush()
            os.execv(sys.executable,
                     [sys.executable, os.path.abspath(__file__)])
        except Exception as e:
            print(_c(_CON_RED, f"Restart failed ({e}) — start it again with:"))
            print(_c(_CON_BOLD, f"    python \"{os.path.abspath(__file__)}\"\n"))
            return False

    # Optional-only installs can be picked up in-process.
    if not HAS_PIL:
        try:
            from PIL import Image as _PILImage          # noqa: F401
            globals()["Image"] = _PILImage
            HAS_PIL = True
            print(_c(_CON_GREEN, "Pillow active — icon resizing enabled."))
        except Exception:
            print(_c(_CON_AMBER, "Pillow becomes active on the next start."))
    if not HAS_QTMULTIMEDIA:
        print(_c(_CON_AMBER, "QtMultimedia becomes active on the next start."))
    return True


# --- application start ---


def main():
    """Start APK Forge: library gate, safety nets, then the Qt application."""
    global _WINDOW_REF
    # v3.6: tell the user WHICH libraries are needed and offer the one-click
    # Data install BEFORE anything else happens.
    if not ensure_runtime_libraries():
        sys.exit(1)
    if not HAS_QT:
        print("APK Forge requires PyQt6.  Install it with:\n\n    pip install PyQt6\n")
        sys.exit(1)

    # v3.1: install the global safety nets BEFORE any widget exists.
    sys.excepthook = _make_excepthook()
    _th_hook = _make_excepthook()
    threading.excepthook = lambda args: _th_hook(args.exc_type, args.exc_value,
                                                 args.exc_traceback)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("ApkForge")
    app.setStyle("Fusion")
    app.setStyleSheet(THEME_QSS)

    win = MainWindow()
    _WINDOW_REF = weakref.ref(win)
    win.show()

    # v3.2: soft window fade-in (windowOpacity is cheap & native; a fallback
    # timer guarantees full opacity even where the platform ignores it).
    try:
        win.setWindowOpacity(0.0)
        fade = QtCore.QPropertyAnimation(win, b"windowOpacity", win)
        fade.setDuration(240)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        fade.start()
        QtCore.QTimer.singleShot(420, lambda: win.setWindowOpacity(1.0))
    except Exception:
        try:
            win.setWindowOpacity(1.0)
        except Exception:
            pass

    rc = app.exec()
    sys.exit(rc)


if __name__ == "__main__":
    main()
