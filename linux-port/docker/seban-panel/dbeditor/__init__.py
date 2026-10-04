"""MT2009_PLUS_DB_EDITOR_V1: "Edytor bazy danych" - the database editor of the
Seban panel, for an operator who is not a programmer: items, skills, monster
drops (with their groups) and chests, plus the client data the game's clients
download after a change.

Each part is a module of this package with an install(bp, ctx) function that
adds its routes to the one blueprint (url prefix /db). ctx carries the panel's
helpers (db, rows, one, login_required, game_text, ...), so no module imports
app.py. The hub page lists the parts that are installed.
"""
from flask import Blueprint, render_template

bp = Blueprint("dbeditor", __name__, url_prefix="/db")

# (endpoint, icon, title, description) - filled by the parts' install().
SECTIONS = []


def add_section(endpoint, icon, title, description):
    SECTIONS.append((endpoint, icon, title, description))


def install(app, ctx):
    login_required = ctx["login_required"]

    @bp.route("/")
    @login_required
    def index():
        return render_template("dbeditor/index.html", sections=SECTIONS)

    # The parts, in the order the hub shows them. A part that is missing (an
    # older image) is skipped.
    for name in ("items", "skills", "drops", "chests", "mobs", "spawns", "regen", "shops", "refine", "attrs", "exptable", "fishing", "clientdata"):
        try:
            module = __import__("dbeditor." + name, fromlist=["install"])
        except ImportError:
            continue
        module.install(bp, ctx)
    app.register_blueprint(bp)
