"""MT2009_PLUS_ENV_EDITOR_V1: python3 -m unittest test_env_schema

env_schema.py has to describe every variable of linux-port/docker/.env.example
and every ${VAR} docker-compose.yml reads, and its "services" have to cover
each service compose passes the variable to (otherwise a change would be
written to .env and never reach the container). Pure standard library: no
YAML parser, the compose file is read by indentation and its anchors
(&migrate-env, &seban-env) are followed by hand."""
import os
import re
import unittest

import env_schema

HERE = os.path.dirname(os.path.abspath(__file__))
DOCKER = os.path.dirname(HERE)
EXAMPLE = os.path.join(DOCKER, ".env.example")
COMPOSE = os.path.join(DOCKER, "docker-compose.yml")
VAR = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")


def example_keys():
    with open(EXAMPLE, encoding="utf-8") as handle:
        return re.findall(r"^([A-Z][A-Z0-9_]*)=", handle.read(), re.M)


def _block(lines, start):
    """Lines indented deeper than lines[start], after it."""
    indent = len(lines[start]) - len(lines[start].lstrip())
    out = []
    for line in lines[start + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        out.append(line)
    return out


def compose_services():
    """{service: {"run": set(vars), "build": set(vars)}}"""
    with open(COMPOSE, encoding="utf-8") as handle:
        lines = [l.split(" #")[0] if not l.lstrip().startswith("#") else "" for l in handle.read().splitlines()]
    anchors = {}
    for i, line in enumerate(lines):
        match = re.search(r"&([A-Za-z0-9_-]+)\s*$", line)
        if match:
            anchors[match.group(1)] = "\n".join(_block(lines, i))
    start = lines.index("services:")
    services = {}
    for i in range(start + 1, len(lines)):
        match = re.fullmatch(r"  ([a-z][a-z0-9-]*):\s*", lines[i])
        if not match:
            if re.match(r"[a-z]", lines[i]):
                break
            continue
        body = _block(lines, i)
        text = "\n".join(body)
        for name in re.findall(r"\*([A-Za-z0-9_-]+)", text):
            text += "\n" + anchors.get(name, "")
        build = ""
        for j, line in enumerate(body):
            if line.strip() == "build:":
                build = "\n".join(_block(body, j))
        run = text.replace(build, "") if build else text
        services[match.group(1)] = {"run": set(VAR.findall(run)), "build": set(VAR.findall(build))}
    return services


class SchemaCoverage(unittest.TestCase):
    def test_every_env_example_key_is_described(self):
        missing = [key for key in example_keys() if key not in env_schema.BY_KEY]
        self.assertEqual(missing, [], ".env.example has variables the panel's .env editor does not know - "
                                      "describe them in seban-panel/env_schema.py")

    def test_every_compose_variable_is_described(self):
        used = set()
        for found in compose_services().values():
            used |= found["run"] | found["build"]
        missing = sorted(key for key in used if key not in env_schema.BY_KEY)
        self.assertEqual(missing, [], "docker-compose.yml reads variables env_schema.py does not describe")

    def test_services_cover_compose(self):
        problems = []
        for service, found in compose_services().items():
            for key in found["run"]:
                entry = env_schema.BY_KEY.get(key)
                if entry and service not in entry["services"]:
                    problems.append("%s -> %s" % (key, service))
            for key in found["build"]:
                entry = env_schema.BY_KEY.get(key)
                if entry and not (entry.get("build") or entry.get("readonly")) and service not in entry["services"]:
                    problems.append("%s -> %s (build)" % (key, service))
        self.assertEqual(sorted(problems), [], "a change would not reach these services")

    def test_entries_are_complete(self):
        sections = {s["id"] for s in env_schema.SECTIONS}
        kinds = {"int", "number", "bool", "enum", "string", "port", "portrange", "address", "host", "url", "path"}
        seen = set()
        for entry in env_schema.SCHEMA:
            key = entry["key"]
            self.assertNotIn(key, seen, key)
            seen.add(key)
            self.assertIn(entry["section"], sections, key)
            self.assertIn(entry["type"], kinds, key)
            self.assertTrue(entry["label"] and entry["desc"], key)
            for service in entry["services"]:
                self.assertIn(service, env_schema.SERVICE_LABELS, key)
            if entry.get("readonly"):
                self.assertTrue(entry.get("readonly_reason"), key + " is read-only without a reason")
            if entry["type"] == "enum":
                self.assertTrue(entry["options"], key)
            # Every shipped default passes its own rule (read-only ones are refused by design).
            if not entry.get("readonly") and not entry.get("secret") and entry["default"] != "":
                self.assertIsNone(env_schema.validate(key, entry["default"]), key + "=" + entry["default"])

    def test_example_values_are_valid(self):
        with open(EXAMPLE, encoding="utf-8") as handle:
            for key, value in re.findall(r"^([A-Z][A-Z0-9_]*)=(.*)$", handle.read(), re.M):
                entry = env_schema.BY_KEY[key]
                if entry.get("readonly") or entry.get("secret") or value == "":
                    continue
                self.assertIsNone(env_schema.validate(key, value), "%s=%s from .env.example" % (key, value))

    def test_secrets_and_paths_are_guarded(self):
        for key in ("M2_DB_ROOT_PASSWORD", "M2_DB_PASSWORD", "M2_DB_USER", "M2_COMPOSE_PROJECT_NAME",
                    "M2_CONTAINER_PREFIX", "M2_UPDATE_STACK_DIR", "M2_BACKUP_HOST_DIR"):
            self.assertTrue(env_schema.BY_KEY[key].get("readonly"), key)
            self.assertIsNotNone(env_schema.validate(key, "x"), key)
        for entry in env_schema.SCHEMA:
            if re.search(r"PASSWORD|SECRET|_KEY$", entry["key"]):
                self.assertTrue(entry.get("secret"), entry["key"] + " looks secret")

    def test_validate(self):
        v = env_schema.validate
        self.assertIsNone(v("PLAYERBOT_AUTOSPAWN_COUNT", "1200"))
        self.assertIsNotNone(v("PLAYERBOT_AUTOSPAWN_COUNT", "2501"))
        self.assertIsNotNone(v("PLAYERBOT_AUTOSPAWN_COUNT", "12a"))
        self.assertIsNone(v("M2_AREZZO", "1"))
        self.assertIsNotNone(v("M2_AREZZO", "yes"))
        self.assertIsNone(v("M2_DIFFICULTY", "custom"))
        self.assertIsNotNone(v("M2_DIFFICULTY", "insane"))
        self.assertIsNone(v("M2_BOOK_WAIT_HOURS", "1.5"))
        self.assertIsNone(v("M2_MONSTER_HP", "250"))
        self.assertIsNotNone(v("M2_MONSTER_HP", "301"))
        self.assertIsNone(v("M2_GAME_PORT_RANGE", "13000-13012"))
        self.assertIsNotNone(v("M2_GAME_PORT_RANGE", "13012-13000"))
        self.assertIsNone(v("M2_PUBLIC_ADDRESS", ""))
        self.assertIsNone(v("M2_PUBLIC_ADDRESS", "gra.example.org"))
        self.assertIsNotNone(v("M2_PUBLIC_ADDRESS", "http://x"))
        self.assertIsNone(v("M2_BRAND", "Mój Serwer"))
        self.assertIsNotNone(v("M2_BRAND", "a$b"))
        self.assertIsNotNone(v("M2_BRAND", "a\nB=1"))
        self.assertIsNotNone(v("M2_TZ", "Europe/Warsaw #x"))
        self.assertIsNone(v("M2_SEBAN_SESSION_SECRET", "abc_DEF-12.x"))
        self.assertIsNotNone(v("M2_SEBAN_SESSION_SECRET", "spaces not ok"))
        self.assertIsNotNone(v("NOT_A_KEY", "1"))
        self.assertEqual(env_schema.services_for(["M2_AREZZO", "M2_SEBAN_PANEL_PORT"]), ["game", "playerbot-migrate", "seban-panel"])
        self.assertEqual(env_schema.services_for(["M2_MAKE_JOBS"]), [])


if __name__ == "__main__":
    unittest.main()
