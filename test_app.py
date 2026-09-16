"""Automated UI smoke test via Streamlit's AppTest -- catches exceptions on
load and on a real repo lookup without needing a human to click through it."""

from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=30)
at.run()
assert not at.exception, f"Exception on initial load: {at.exception}"
print("Initial load: OK, no exceptions")

at.text_input[0].set_value("JustVugg/colibri").run()
at.button[0].click().run()
assert not at.exception, f"Exception after repo lookup: {at.exception}"
print("Repo lookup (JustVugg/colibri): OK, no exceptions")

# a bad/nonexistent repo should show a clean error, not crash
at2 = AppTest.from_file("app.py", default_timeout=30)
at2.run()
at2.text_input[0].set_value("this-owner-does-not-exist-xyz/nope").run()
at2.button[0].click().run()
assert not at2.exception, f"Exception on 404 case: {at2.exception}"
print("404 handling: OK, no exceptions (should show a clean error message)")

print("\nAll AppTest checks passed.")
