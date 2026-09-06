# DistroHub

**Find the operating system that fits.** A clean, searchable directory of Linux
distributions and Windows — how to download each one, how to make the USB, how to
install it, how to keep it updated, and real user reviews and star ratings, all in
one place.

A one-person project by **Opperman Cybernetix**.

---

## Why

Existing distro sites are cluttered and dated, and none really combine practical
**install + update guides** with **community reviews** in one modern, fast interface.
DistroHub is built around one idea: someone lands, finds the right OS in seconds,
learns how to get it running, and never feels lost.

## Features

- **Fast search** — by name, category, use-case, or package manager (`gaming`,
  `security`, `lightweight`, `arch`, `tor`…)
- **Category filters** — Beginner, Mainstream, Gaming, Arch, Security, Privacy,
  Advanced, Servers & Devices, Windows
- **Per-distro guides** — Make USB → Install → Update → Get working, each in a
  clean slide-in panel
- **Star ratings & reviews** — real, shared, stored server-side
- **Downloadable PDF** — a branded one-page install guide generated on the fly for
  any distro
- **USB tool walkthroughs** — full step-by-step for Ventoy, Rufus, balenaEtcher and dd
- **Contact form** — saved to the database and optionally emailed to the maintainer
- **27 systems** seeded and ready, easy to extend

## Tech stack

Flask · SQLite · vanilla JS (no build step) · ReportLab (PDF generation). No
frameworks to learn, nothing to compile — it runs on a Raspberry Pi.

## Quick start

```bash
git clone https://github.com/<your-username>/distrohub.git
cd distrohub
pip install -r requirements.txt
python3 app.py
```

Open **http://localhost:5000** — or from another device, `http://<host-ip>:5000`
(the app listens on `0.0.0.0`). The database is created and seeded on first run.

## Configuration

**Contact-form email (optional).** Messages are always saved to the `contacts`
table; set these to also have them emailed:

```bash
export SMTP_HOST=smtp.yourprovider.com
export SMTP_PORT=587
export SMTP_USER=you@yourprovider.com
export SMTP_PASS=your-app-password
export CONTACT_TO=you@yourprovider.com
```

Any SMTP server works (a Gmail app-password is the easiest free option).

**Donations.** Set `DONATE_URL` near the top of the `<script>` in
`templates/index.html` to your Ko-fi / PayPal / Buy Me a Coffee link.

## Project structure

```
distrohub/
├── app.py              # Flask app, database, API, PDF + contact routes
├── pdfgen.py           # on-the-fly per-distro PDF guide
├── distros.json        # the distro data (edit to add/change distros)
├── tools.json          # USB-tool walkthroughs (Ventoy/Rufus/Etcher/dd)
├── templates/
│   └── index.html      # the whole front-end (talks to the API)
├── requirements.txt
└── LICENSE
```

## Contributing

Additions and fixes are welcome — especially new distros and corrections to install
or update commands as versions change.

**Add a distro:** copy an object in `distros.json`, fill in the fields
(`id, name, cat, g, tags, pm, based, diff, url, blurb, usb, install[], update,
after, note?`), delete `distrohub.db`, and restart to reseed.

**Add a USB tool:** add an object to `tools.json` (`name, for, platforms, url,
install[], code?, use[], tips[], warn?`).

Open an issue or a pull request. If you're reporting something out of date, the
distro `id` and what changed is all I need.

## Roadmap

- Sort by rating / most-reviewed
- Admin page to read contact messages and moderate reviews in the browser
- "Download the full handbook" (all distros in one PDF)
- Community Discord

## Support

DistroHub is free and ad-free, built and maintained by one person in his own time.
If it saved you time, a coffee helps keep it going:

☕ **[Buy me a coffee](https://buymeacoffee.com/cybernetix88)**

## License

MIT — see [LICENSE](LICENSE). Built and maintained by Opperman Cybernetix.
